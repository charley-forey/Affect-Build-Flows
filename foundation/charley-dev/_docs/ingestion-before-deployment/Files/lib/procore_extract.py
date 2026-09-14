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

# 100, not 1000. The cheatsheet's 1000 holds for top-level v1.0 collections, and the live
# tenant rejected it on 7 of 44 endpoints on 2026-08-25 with an explicit
# "Invalid per_page of 1000, exceeding max per_page of 100": every REST v2.0 path, every
# nested sub-resource (prime_contracts/{id}/line_items, payment_applications,
# work_order_contracts/{id}/line_items, purchase_order_contracts/{id}/line_items,
# budget_views/{id}/detail_rows) and daily_logs.
#
# Those seven had never succeeded, on the laptop bridge or in Fabric, since the day they
# were registered - the bronze tables behind budget detail and every contract line item
# have been empty the whole time. A per-version cap was tried first and was wrong: the
# split is not v1.0 vs v2.0, it is top-level vs nested, which is not a property the
# registry records.
#
# ponytail: one global cap, ~10x the requests on the few large collections (cost_codes is
# 5,433 rows = 55 pages). Well inside Procore's rate limit and the nightly window. If the
# request count ever matters, raise it per endpoint in endpoints.yml rather than guessing
# a rule from the path shape.
MAX_PER_PAGE = 100

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
        # Production is the default, and sandbox is what you opt INTO. The other way round
        # cost a live run on 2026-08-24: the local script set PROCORE_BASE_URL and the
        # Fabric notebook did not, so the notebook silently authenticated against
        # sandbox.procore.com with production credentials and got a 401. Had those
        # credentials happened to be valid in both, it would have landed convincingly
        # empty tables instead - a wrong answer that looks healthy. One caller setting an
        # override the other forgets is not a default worth keeping.
        base_url=os.environ.get("PROCORE_BASE_URL", "https://api.procore.com"),
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


def build_params(endpoint, company_id, since=None) -> dict[str, Any]:
    """Every query parameter an endpoint needs, in one place.

    Three rules used to live in extract_procore_local.pull() and nowhere else, so the
    generated Fabric notebook shipped without them. `daily_log_headers` is what that cost:
    it 400s with "The Start Date and End Date parameters are required", which reads as a
    broken endpoint rather than a missing parameter.

    A declared window matters beyond this one failure. Without it several daily-log
    endpoints return 200 and no rows - "this project has no daily logs" - which is the
    most expensive kind of wrong, because nothing errors and the absence looks like data.
    """
    from datetime import timedelta

    params = dict(watermark_params(endpoint, since))
    if endpoint.scope == "company":
        params["company_id"] = company_id

    days = getattr(endpoint, "date_range_days", None)
    if days:
        # Yesterday, not today. Procore validates the window against ITS current day in the
        # company's own timezone (Affect: US/Eastern), and rejects an end date beyond it
        # with "The End Date parameter cannot exceed the current day."
        #
        # UTC is ahead of Eastern by 4-5 hours, so any run between 20:00 and midnight local
        # sends tomorrow's date and gets a 400 - while a run at 09:00 works perfectly. That
        # is a bug that hides from every daytime test and only ever fires in the unattended
        # overnight window, which is the only time this pipeline actually runs. It surfaced
        # at 03:06 UTC on 2026-08-25.
        #
        # ponytail: stepping back a day is timezone-proof for any offset and costs the
        # current day's logs, which are incomplete anyway. Read the company's timezone from
        # Procore and use its real local date if same-day logs ever matter.
        end = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        start = end - timedelta(days=days)
        prefix = getattr(endpoint, "date_param_prefix", "") or ""
        lo = f"{prefix}start_date" if not prefix else f"{prefix}[start_date]"
        hi = f"{prefix}end_date" if not prefix else f"{prefix}[end_date]"
        params[lo] = start.isoformat()
        params[hi] = end.isoformat()
    return params


def stamp_project(record: dict[str, Any], project_id) -> dict[str, Any]:
    """Record the project this was FETCHED under, when the payload does not say.

    Procore's project-scoped list endpoints do not reliably echo `project_id` back, and the
    caller is the only one who knows it. Skipping this does not break the record itself -
    it breaks the CHILD endpoint, one step later and somewhere else entirely:
    `collect_parent_ids` reads the project off the parent record, finds nothing, and builds
    `/prime_contracts/{id}/line_items` with no project, which Procore answers with
    "Missing Project or Company ID".

    That is what happened on 2026-08-25: `work_order_contract_line_items` and
    `purchase_order_contract_line_items` succeeded while `prime_contract_line_items`,
    `payment_applications` and `budget_detail_rows` failed, purely on whether their parent
    payload happened to include a project. The local bridge stamped it and the notebook did
    not, so it worked on a laptop and 400'd in Fabric.
    """
    if project_id is not None and record.get("project_id") is None:
        return {**record, "project_id": project_id}
    return record


def is_tool_not_enabled(exc: Exception) -> bool:
    """True for the 403/404 that means "this scope does not have this tool turned on".

    Normal across a 19-project portfolio, and across a company that has not licensed every
    Procore module - `standard_cost_codes` 404s at company level on Affect's tenant. Not a
    reason to lose the other 43 endpoints.

    The rule lived only in extract_procore_local.pull(), so the laptop bridge shrugged such
    a response off while the Fabric notebook died on it - which is a large part of why the
    local path "worked" and the scheduled one never had. Shared so the two cannot diverge
    again. Anything that is not 403/404 is a real failure and must still propagate.
    """
    status = getattr(getattr(exc, "response", None), "status_code", None)
    return status in (403, 404)


def bronze_merge_keys(endpoint) -> list[str]:
    """The natural key of a bronze row, which is not always the endpoint key alone.

    A project-scoped endpoint is fetched once per project, and its records are only
    unique WITHIN a project. `project_vendors` is the proof: measured against the live
    tenant on 2026-08-25 it returns 409 rows carrying 58 duplicate vendor ids - the same
    vendor legitimately working on several projects - and zero duplicates once the project
    is part of the key. Merging those on `_key` alone made Delta raise
    DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE, which is Delta refusing to
    guess which of the two rows wins. It was right to refuse.

    Company-scoped endpoints carry a NULL `_project_id`, which is why `merge_sql` joins
    with `<=>` rather than `=`. With plain `=` the predicate is NULL rather than true, no
    source row ever matches, and every nightly run appends a fresh copy of every record
    while nothing raises. Crashing on the project endpoints was the good outcome; that
    would have been the silent one.

    `endpoint` is unused today and kept so a future endpoint whose identity needs a third
    column has one place to say so. This is the same predicate the reference notebook
    `01_extract_bronze.py` already used - it was right, and the generated Fabric notebook
    was the one that had drifted.
    """
    return ["_key", "_project_id"]


def bronze_schema():
    """The Spark schema for `to_bronze_row` output, declared rather than inferred.

    Inference cannot type a column that is None in every row, and `_project_id` is None
    for all 8 company-level endpoints - so `spark.createDataFrame(rows)` died with
    CANNOT_DETERMINE_TYPE on the very first endpoint of the 2026-08-25 run, after
    authenticating and resolving 19 projects. Sampling was never going to work here: the
    failure depends on which endpoint runs first.

    Declaring it also keeps bronze's schema identical across runs, which the Delta MERGE
    downstream depends on - an inferred `_project_id` is long on a project endpoint and
    unresolvable on a company one, and a column whose type moves between runs turns a
    merge into a schema-evolution error later, somewhere less obvious than here.

    pyspark is imported inside the function on purpose: this module is exercised offline
    by the test suites, which have no Spark.
    """
    from pyspark.sql.types import (StringType, StructField, StructType, LongType,
                                   TimestampType)

    return StructType([
        StructField("_key", StringType(), True),
        StructField("_project_id", LongType(), True),
        StructField("_source_endpoint", StringType(), True),
        StructField("_ingested_at", TimestampType(), True),
        StructField("payload", StringType(), True),
        StructField("_batch_id", StringType(), True),
        StructField("_row_hash", StringType(), True),
    ])


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
