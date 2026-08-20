"""Procore -> bronze extraction engine.

Pure Python. No Spark, no Fabric imports, no global state. This module is imported
by BOTH the Fabric notebook (`notebooks/01_extract_bronze.py`) and the local runner
(`run_local.py`), so the auth / pagination / retry / watermark logic exists exactly
once. That is the whole point: the defects recorded in
`deliverables/02-procore-etl-validation.md` are one bug duplicated per notebook.

Everything here is driven by `config/endpoints.yml`. Adding a Procore endpoint is a
YAML entry, not a new notebook.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterator

# Procore caps per_page at 1000 on most v1.0 list endpoints.
# resources/procore/endpoints-cheatsheet.md:17
MAX_PER_PAGE = 1000

# Stop a runaway pagination loop rather than hammering the API forever.
MAX_PAGES = 1000

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


# --------------------------------------------------------------------------
# Settings & secrets
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    """Connection settings. Never holds a token - tokens are fetched, not stored."""

    base_url: str
    client_id: str
    client_secret: str
    company_id: str

    @property
    def token_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/oauth/token"


def get_secret(name: str, vault_env: str = "AFFECT_KEYVAULT_URL") -> str:
    """Read a secret from Key Vault inside Fabric, from the environment locally.

    Fixes defect #1 (credentials hard-coded in a notebook cell). There is exactly one
    function that produces a credential, so there is no second place for one to hide.

    Two things the first version got wrong, both of which meant this could never have
    worked against a real vault:

    - It passed `name` straight to Key Vault. Secret names cannot contain underscores,
      so `PROCORE_CLIENT_ID` is not a legal secret name; `setup_keyvault.py` writes
      `procore-client-id`. The translation lives in fabric_common.kv_secret_name.
    - It fell through to os.environ when the vault lookup did not fire, so a
      misconfigured vault read a credential from somewhere else and reported success.
      Inside Fabric this now fails closed.

    fabric_common is imported inside the Fabric branch, not at module scope: it ships to
    the same Files/lib directory in the lakehouse, but src/procore/run_local.py puts only
    src/procore on sys.path. Locally that branch never runs, so the import never happens.
    """
    try:
        import notebookutils  # type: ignore[import-not-found]
    except ImportError:
        notebookutils = None  # not running inside Fabric

    if notebookutils is not None:
        from fabric_common import KEYVAULT_URL, kv_secret_name

        vault = os.environ.get(vault_env) or KEYVAULT_URL
        return notebookutils.credentials.getSecret(vault, kv_secret_name(name))

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Secret {name!r} not found. Export it locally (see "
            f"config/settings.example.env), or run inside Fabric where it is read from "
            f"Key Vault. See charley-dev/_docs/keyvault-runbook.md."
        )
    return value


def load_settings() -> Settings:
    return Settings(
        base_url=os.environ.get("PROCORE_BASE_URL", "https://sandbox.procore.com"),
        client_id=get_secret("PROCORE_CLIENT_ID"),
        client_secret=get_secret("PROCORE_CLIENT_SECRET"),
        company_id=get_secret("PROCORE_COMPANY_ID"),
    )


# --------------------------------------------------------------------------
# Endpoint registry
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str
    scope: str  # "company" | "project"
    api_version: str
    bronze_table: str
    incremental: str | None = None  # e.g. "filters[updated_at]"; None = full reload
    key: str = "id"  # natural key used for the merge

    @property
    def major_version(self) -> int:
        return int(self.api_version.split(".")[0])

    @property
    def needs_company_header(self) -> bool:
        """v2.0+ requires the Procore-Company-Id header; v1.x takes it in path/query.

        Mixing the two is the most common cause of an unexplained 403.
        resources/procore/endpoints-cheatsheet.md:18-19
        """
        return self.major_version >= 2


def load_endpoints(path: str) -> list[Endpoint]:
    import yaml

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return [Endpoint(**entry) for entry in raw["endpoints"]]


# --------------------------------------------------------------------------
# Watermark (defect #2 - incremental instead of full reload)
# --------------------------------------------------------------------------


def updated_at_filter(since: datetime, until: datetime | None = None) -> str:
    """Build Procore's ISO-8601 range filter value.

    Format: 2026-07-01T00:00:00Z...2026-07-31T23:59:59Z
    resources/procore/endpoints-cheatsheet.md:220-221
    """
    until = until or datetime.now(timezone.utc)
    return f"{_iso(since)}...{_iso(until)}"


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def watermark_params(endpoint: Endpoint, last_ingested: datetime | None) -> dict[str, str]:
    """Params that limit the pull to rows changed since the last successful run.

    A full reload happens only when the endpoint declares no incremental filter, or
    when the bronze table is empty (first run).
    """
    if not endpoint.incremental or last_ingested is None:
        return {}
    # Overlap by an hour: Procore's updated_at has second granularity and clock skew
    # is real. Re-pulling an hour of rows is free because the load is a merge, not an
    # append - see write_bronze() in the callers.
    since = last_ingested - timedelta(hours=1)
    return {endpoint.incremental: updated_at_filter(since)}


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def fetch_token(settings: Settings, session: Any) -> str:
    """Client-credentials grant.

    This is the grant that survives unattended runs. A user-based (authorization_code)
    token expires and breaks the pipeline at the worst moment - flagged in
    resources/procore/endpoints-cheatsheet.md:196-200 as the most common Procore ETL
    failure mode.
    """
    response = session.post(
        settings.token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def build_headers(token: str, company_id: str, endpoint: Endpoint) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if endpoint.needs_company_header:
        headers["Procore-Company-Id"] = str(company_id)
    return headers


def request_with_retry(
    session: Any,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    max_attempts: int = 5,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """GET with rate-limit and transient-failure handling.

    Honours Retry-After on 429 and backs off exponentially otherwise. A single
    throttled call without this fails an entire nightly run.
    """
    last_response = None
    for attempt in range(max_attempts):
        response = session.get(url, headers=headers, params=params, timeout=60)
        if response.status_code not in RETRYABLE_STATUS:
            response.raise_for_status()
            return response

        last_response = response
        if attempt == max_attempts - 1:
            break

        retry_after = response.headers.get("Retry-After")
        delay = float(retry_after) if retry_after else 2.0**attempt
        sleep(delay)

    last_response.raise_for_status()  # type: ignore[union-attr]
    raise RuntimeError(f"Exhausted {max_attempts} attempts for {url}")


def iter_records(
    session: Any,
    base_url: str,
    path: str,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    per_page: int = MAX_PER_PAGE,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[dict[str, Any]]:
    """Yield every record from a paginated Procore list endpoint.

    Termination is driven by the response itself - a short page, an empty page, or the
    Total header being reached. Never by an assumed page count.
    resources/procore/endpoints-cheatsheet.md:213-217
    """
    url = f"{base_url.rstrip('/')}{path}"
    seen = 0
    total: int | None = None

    for page in range(1, MAX_PAGES + 1):
        page_params = dict(params or {})
        page_params.update({"page": page, "per_page": per_page})

        response = request_with_retry(session, url, headers, page_params, sleep=sleep)
        payload = response.json()

        # Most list endpoints return a bare array; a few wrap it in an object.
        rows = payload if isinstance(payload, list) else _unwrap(payload)
        if not rows:
            return

        for row in rows:
            yield row
        seen += len(rows)

        if total is None:
            total = _int_or_none(response.headers.get("Total"))
        if total is not None and seen >= total:
            return
        if len(rows) < per_page:
            return


def _unwrap(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull the record list out of an object-wrapped response."""
    for key in ("data", "items", "results"):
        if isinstance(payload.get(key), list):
            return payload[key]
    # A single-object response (e.g. /schedule metadata) is one record.
    return [payload] if payload else []


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Project scoping (defect #3 - stop looping every project every run)
# --------------------------------------------------------------------------


def iter_active_projects(
    session: Any, settings: Settings, token: str, sleep: Callable[[float], None] = time.sleep
) -> Iterator[dict[str, Any]]:
    """Company projects filtered to active.

    Rebecca's notebooks loop every project regardless of status. Procore's limits are
    high but real, and most of those projects are closed.
    resources/procore/endpoints-cheatsheet.md:29
    """
    projects_ep = Endpoint(
        name="projects",
        path="/rest/v1.0/projects",
        scope="company",
        api_version="1.0",
        bronze_table="bronze_procore_projects",
    )
    headers = build_headers(token, settings.company_id, projects_ep)
    yield from iter_records(
        session,
        settings.base_url,
        projects_ep.path,
        headers,
        params={"company_id": settings.company_id, "filters[by_status]": "Active"},
        sleep=sleep,
    )


def resolve_paths(endpoint: Endpoint, company_id: str, project_ids: list[int]) -> list[tuple[str, int | None]]:
    """Expand an endpoint template into the concrete paths to call.

    Returns (path, project_id) pairs so the caller can stamp project_id onto bronze
    rows - project-scoped endpoints do not always echo it back in the payload.
    """
    if endpoint.scope == "company":
        return [(endpoint.path.format(company_id=company_id), None)]
    return [
        (endpoint.path.format(company_id=company_id, project_id=pid), pid)
        for pid in project_ids
    ]


# --------------------------------------------------------------------------
# Bronze rows
# --------------------------------------------------------------------------


def to_bronze_row(
    record: dict[str, Any], endpoint: Endpoint, project_id: int | None, ingested_at: datetime
) -> dict[str, Any]:
    """Wrap a raw Procore record for the bronze layer.

    The full payload is kept as an unparsed JSON string. This is the structural fix for
    defect #5 (transformations dropping the vendor / cost-code IDs the model needs):
    bronze physically cannot drop a column it never parsed, so a transform bug is a
    re-run rather than a re-extract.
    """
    import json

    return {
        "_key": str(record.get(endpoint.key, "")),
        "_project_id": project_id,
        "_source_endpoint": endpoint.name,
        "_ingested_at": ingested_at,
        "payload": json.dumps(record, default=str),
    }


def split_sql_statements(sql: str) -> list[str]:
    """Split a .sql file into individual statements.

    Lives here because it is the one module both the Fabric notebook and run_local.py
    already import. Spark's spark.sql() executes a single statement at a time, so the
    split has to happen identically in both runners or the two diverge.

    Comments are stripped BEFORE splitting - a `;` inside a `--` comment is otherwise
    read as a statement boundary and tears the statement in half.

    ponytail: line-wise comment strip, then split on `;`. Breaks if a string literal ever
    contains `--` or `;`. None do today. Reach for sqlglot if that changes.
    """
    body = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return [statement.strip() for statement in body.split(";") if statement.strip()]


def extract_endpoint(
    session: Any,
    settings: Settings,
    token: str,
    endpoint: Endpoint,
    project_ids: list[int],
    last_ingested: datetime | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Pull one endpoint across all in-scope projects into bronze rows."""
    headers = build_headers(token, settings.company_id, endpoint)
    params = watermark_params(endpoint, last_ingested)
    if endpoint.scope == "company":
        params = {**params, "company_id": settings.company_id}

    ingested_at = datetime.now(timezone.utc)
    rows: list[dict[str, Any]] = []
    for path, project_id in resolve_paths(endpoint, settings.company_id, project_ids):
        for record in iter_records(
            session, settings.base_url, path, headers, params=params, sleep=sleep
        ):
            rows.append(to_bronze_row(record, endpoint, project_id, ingested_at))
    return rows
