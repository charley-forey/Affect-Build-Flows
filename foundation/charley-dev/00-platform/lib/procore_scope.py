"""Registry loading and path expansion for the Procore extractor.

`src/procore/procore_extract.py` handles auth, pagination, retry and watermarks, and its
`resolve_paths` fills {company_id} and {project_id}. Three endpoints we need are
sub-resources of a record we have to fetch first:

    /rest/v1.0/prime_contracts/{parent_id}/line_items
    /rest/v1.0/prime_contracts/{parent_id}/payment_applications
    /rest/v1.0/budget_views/{parent_id}/detail_rows

Rather than fork the extractor, this module adds the parent concept alongside it: it
resolves the concrete path list, and the extractor's existing `iter_records` does the
fetching unchanged. One engine, one place for the auth and pagination bugs to be fixed.

Self-check: python procore_scope.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlsplit

SCOPE_COMPANY = "company"
SCOPE_PROJECT = "project"
SCOPE_PARENT = "parent"
VALID_SCOPES = (SCOPE_COMPANY, SCOPE_PROJECT, SCOPE_PARENT)


@dataclass(frozen=True)
class ParentRef:
    endpoint: str  # logical name of the endpoint supplying the ids
    field: str = "id"  # which field on those records holds the id

    # Only spawn children for parents whose `where_field` equals `where_value`.
    #
    # This exists for budget_detail_rows. Procore returns a DIFFERENT COLUMN SET per budget
    # view - "Procore Standard Forecast" carries 2 money columns, Affect's own "STANDARD
    # BUDGET VIEW - CM" carries 16 with their lettered scheme (COMMITTED COSTS (G),
    # INVOICED TO DATE (P), ...). Pulling every view mixes incompatible shapes into one
    # bronze table and the parser silently produces NULLs from whichever it did not expect.
    #
    # Filtering also cuts the request count from ~100 to ~19, which matters against a
    # 600/hour quota.
    where_field: str | None = None
    where_value: str | None = None


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str
    scope: str
    api_version: str
    bronze_table: str
    incremental: str | None = None
    key: str = "id"
    parent: ParentRef | None = None

    # Some endpoints require start_date/end_date and return 200 WITH ZERO ROWS without
    # them - see the module docstring on manpower_logs. A number here means "always send a
    # window this many days back from today".
    date_range_days: int | None = None

    # What the window parameters are CALLED. Procore is inconsistent even within one
    # family: manpower_logs wants start_date/end_date, daily_logs wants
    # filters[start_date]/filters[end_date] and returns 400 "parameters are required"
    # while you are sending the other spelling.
    date_param_prefix: str = ""

    # Declared per-project exclusions: {project_id: reason}. A 403/404 on one of these
    # scopes is recorded as `excluded_declared` instead of blocking the run. An undeclared
    # 403/404 still blocks - the declaration is the justification the gate asks for.
    unavailable_projects: dict = field(default_factory=dict, hash=False)

    # Page size. 100 is safe everywhere; 1000 cuts requests ~10x on large collections but
    # the tenant 400s it ("exceeding max per_page of 100") on every nested sub-resource,
    # every v2.0 path and daily_logs (measured 2026-08-25), so those are refused here.
    per_page: int = 100

    def __post_init__(self) -> None:
        if not 1 <= self.per_page <= 1000:
            raise ValueError(f"{self.name}: per_page must be 1..1000")
        if self.per_page > 100 and (self.scope == SCOPE_PARENT or self.major_version >= 2
                                    or "daily_logs" in self.path):
            raise ValueError(f"{self.name}: per_page > 100 is rejected by Procore on this path shape")
        if any(not str(r).strip() for r in self.unavailable_projects.values()):
            raise ValueError(f"{self.name}: every unavailable_projects entry needs a reason")
        if self.unavailable_projects and self.scope == SCOPE_COMPANY:
            raise ValueError(f"{self.name}: unavailable_projects needs a project or parent scope")
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"{self.name}: unknown scope {self.scope!r}")
        if self.scope == SCOPE_PARENT and self.parent is None:
            raise ValueError(f"{self.name}: scope 'parent' requires a parent: block")
        if self.scope != SCOPE_PARENT and self.parent is not None:
            raise ValueError(f"{self.name}: parent: is only valid with scope 'parent'")
        if ("{parent_id}" in self.path) != (self.scope == SCOPE_PARENT):
            raise ValueError(f"{self.name}: {{parent_id}} and scope 'parent' must agree")

    @property
    def major_version(self) -> int:
        return int(self.api_version.split(".")[0])

    @property
    def needs_company_header(self) -> bool:
        """ALWAYS send Procore-Company-Id. Verified against Affect's tenant 2026-08-02.

        The documented rule - and what the cheatsheet says at line 41 - is that only v2.0+
        needs this header, because v1.x takes the company in the path or query. That is not
        what Affect's tenant does. Measured, same token, same project, v1.0 RFIs:

            header + per_page=1000   -> 200, 32 rows
            header, no params        -> 200, 32 rows
            NO header + per_page     -> 404
            NO header, no params     -> 404

        Same pattern on v1.1 submittals, v1.0 incidents and v1.0 manpower_logs. The failure
        is a 404, not a 403 - it reads as "this project has no RFI tool", not "you forgot a
        header", which is why 28 of 36 endpoints looked like a permissions problem on the
        first full run and were not.

        Sending the header on a v1.x endpoint that does not need it is harmless; omitting it
        where it is needed costs a day of chasing the wrong cause. So it always goes.
        """
        return True


def load_registry(path: str) -> list[Endpoint]:
    """Parse endpoints.yml into validated Endpoint objects."""
    import yaml

    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    endpoints = []
    for entry in raw["endpoints"]:
        entry = dict(entry)
        parent = entry.pop("parent", None)
        endpoints.append(Endpoint(**entry, parent=ParentRef(**parent) if parent else None))

    validate_registry(endpoints)
    return endpoints


def validate_registry(endpoints: list[Endpoint]) -> None:
    """Catch registry mistakes at load time rather than mid-run.

    A typo in a parent reference otherwise surfaces as an empty table hours later, which
    reads as "no data in Procore" instead of "the config is wrong".
    """
    names = [e.name for e in endpoints]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise ValueError(f"duplicate endpoint name(s): {sorted(duplicates)}")

    tables = [e.bronze_table for e in endpoints]
    dup_tables = {t for t in tables if tables.count(t) > 1}
    if dup_tables:
        raise ValueError(f"duplicate bronze_table(s): {sorted(dup_tables)}")

    known = set(names)
    for e in endpoints:
        if e.parent and e.parent.endpoint not in known:
            raise ValueError(f"{e.name}: parent endpoint {e.parent.endpoint!r} not in registry")

    resolution_order(endpoints)  # raises on a cycle


def resolution_order(endpoints: list[Endpoint]) -> list[Endpoint]:
    """Order endpoints so a parent is always fetched before its children.

    Kahn's algorithm, and it doubles as the cycle check: if anything is left unemitted,
    the remaining nodes form a cycle.
    """
    by_name = {e.name: e for e in endpoints}
    pending = list(endpoints)
    emitted: list[Endpoint] = []
    done: set[str] = set()

    while pending:
        ready = [e for e in pending if not e.parent or e.parent.endpoint in done]
        if not ready:
            raise ValueError(
                f"parent cycle among: {sorted(e.name for e in pending)}"
            )
        for e in ready:
            emitted.append(e)
            done.add(e.name)
        pending = [e for e in pending if e.name not in done]

    assert len(emitted) == len(by_name)
    return emitted


def expand_paths(
    endpoint: Endpoint,
    company_id: str,
    project_ids: list[int] | None = None,
    parent_ids: list[Any] | None = None,
) -> list[tuple[str, int | None]]:
    """Expand a path template into the concrete paths to call.

    Returns (path, project_id) pairs. The project_id travels alongside because
    project-scoped endpoints do not reliably echo it back in the payload, and bronze rows
    need it to be joinable.
    """
    if endpoint.scope == SCOPE_COMPANY:
        return [(endpoint.path.format(company_id=company_id), None)]

    if endpoint.scope == SCOPE_PROJECT:
        return [
            (endpoint.path.format(company_id=company_id, project_id=pid), pid)
            for pid in (project_ids or [])
        ]

    # scope == parent. No parent ids means the parent pull returned nothing - an empty
    # list, not an error: a company with no prime contracts has no line items either.
    #
    # Parent ids may arrive as bare ids or as (parent_id, project_id) pairs. The pair form
    # exists because Procore's nested endpoints need the project as well as the parent:
    #
    #     /prime_contracts/{id}/line_items                 -> 400
    #     /prime_contracts/{id}/line_items?project_id=N    -> 200, 15 rows
    #
    # Same for budget_views/{id}/detail_rows and prime_contracts/{id}/payment_applications
    # (verified 2026-08-02). Without the pair, budget_detail_rows returns nothing and
    # fct_BudgetLine is empty - so the project has to travel with the parent id, not be
    # rediscovered later.
    out = []
    for entry in (parent_ids or []):
        parent_id, project_id = entry if isinstance(entry, tuple) else (entry, None)
        if "{project_id}" in endpoint.path and project_id is None:
            raise ValueError(f"{endpoint.name}: parent record is missing its project id")
        path = endpoint.path.format(company_id=company_id, parent_id=parent_id, project_id=project_id)
        if project_id is not None and "project_id=" not in path and "{project_id}" not in endpoint.path:
            path += ("&" if "?" in path else "?") + f"project_id={project_id}"
        out.append((path, project_id))
    return out


def declared_unavailable(endpoint: Endpoint, project_id: Any) -> str | None:
    """The declared reason this (endpoint, project) scope may 403/404, or None."""
    if project_id is None:
        return None
    return {str(k): v for k, v in endpoint.unavailable_projects.items()}.get(str(project_id))


def tombstone_scopes(endpoint: Endpoint, audit: dict[str, Any]) -> list[Any]:
    """Project ids (None = company) whose bronze rows may be tombstoned by this endpoint run.

    A key missing from a pull is only evidence of deletion when the pull held the COMPLETE
    key set of that scope, so every doubt resolves to "do not tombstone":
    - incremental pulls (`mode` != full) and date-windowed pulls list only a slice;
    - a project is eligible only if EVERY one of its scopes (one per parent, for parent
      endpoints) ended `complete` - failed, unavailable_* and excluded_declared never do;
    - a scope that returned zero rows is not trusted: this tenant has answered wrong
      parameters with 200 and an empty list (see endpoints.yml, prime_change_orders).
      ponytail: a project whose last record is deleted keeps it; add a recycle-bin read
      if that case matters.
    Projects outside the run's scope (inactive) have no scopes here, so never tombstone.
    """
    if audit.get("mode") != "full" or getattr(endpoint, "date_range_days", None):
        return []
    projects: dict[Any, list[dict]] = {}
    for scope in audit.get("scopes", []):
        projects.setdefault(scope.get("project_id"), []).append(scope)
    return [pid for pid, scopes in projects.items()
            if all(s.get("status") == "complete" for s in scopes)
            and sum(s.get("received_rows", 0) for s in scopes) > 0]


def normalize_records(endpoint: Endpoint, record: dict[str, Any], path: str = "") -> list[dict[str, Any]]:
    """Checklist responses group inspection instances under templates; retain that context."""
    if endpoint.name == "checklist_list_items":
        requested = parse_qs(urlsplit(path).query).get("filters[list_id][]", [])
        if len(requested) != 1 or str(record.get("list_id")) != requested[0]:
            raise ValueError("inspection item does not match the requested inspection filter")
    if endpoint.name != "checklist_lists" or "lists" not in record:
        if endpoint.name == "checklist_lists" and not record.get("id"):
            raise ValueError("checklist response has neither inspection id nor lists")
        return [record]
    inspections = record["lists"]
    if not isinstance(inspections, list) or any(not isinstance(r, dict) or not r.get("id") for r in inspections):
        raise ValueError("checklist template contains invalid inspection records")
    context = {key: value for key, value in record.items() if key != "lists"}
    return [dict(inspection, _source_group=context) for inspection in inspections]


def collect_parent_ids(records: list[dict[str, Any]], ref: ParentRef,
                       with_project: bool = True) -> list[Any]:
    """Distinct, order-preserving ids from a parent endpoint's records.

    with_project=True returns (parent_id, project_id) pairs instead of bare ids, for the
    nested endpoints that 400 without a project (see expand_paths). The project is read
    from the parent record itself - `project_id`, or `project.id` when Procore nests it -
    so it never has to be guessed downstream.

    Kept as a flag rather than a second function because the two differ only in what they
    carry, and callers pass the result straight into expand_paths either way.

    It defaults to True because False is a trap: the generated Fabric notebook took the
    default and every parent-scoped endpoint 400'd with "Missing Project or Company ID",
    or - worse, once a project id was supplied - 404'd because a parent from project A had
    been paired with project B. Both read as a broken endpoint rather than a missing flag.
    Nothing in production wants bare ids; the self-check asks for them explicitly.
    """
    seen: dict[Any, Any] = {}
    for record in records:
        # Skip parents that do not match the filter, when one is declared. Compared as
        # strings so a YAML value does not have to match the payload's JSON type.
        if ref.where_field is not None:
            if str(record.get(ref.where_field)) != str(ref.where_value):
                continue
        value = record.get(ref.field)
        if value is None:
            continue
        if not with_project:
            seen.setdefault(value, None)
            continue
        project = record.get("project_id")
        if project is None and isinstance(record.get("project"), dict):
            project = record["project"].get("id")
        # DEDUP ON THE PAIR, not on the parent id. Some Procore parents are COMPANY-level
        # definitions applied to every project, so the same id comes back once per project:
        # budget view "STANDARD BUDGET VIEW - CM" is one id shared across all 19 projects.
        # Keying on the id alone collapsed 19 (view, project) pairs into 1 and returned one
        # project's budget instead of the portfolio's - 19 rows where 361 were expected.
        seen.setdefault((value, project), None)
    if not with_project:
        return list(seen)
    return list(seen)


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------


def _ep(name: str, path: str, scope: str, parent: ParentRef | None = None, **kw: Any) -> Endpoint:
    return Endpoint(
        name=name, path=path, scope=scope, api_version=kw.pop("api_version", "1.0"),
        bronze_table=kw.pop("bronze_table", f"cd_bronze_{name}"), parent=parent, **kw
    )


def _selftest() -> None:
    company = _ep("vendors", "/rest/v1.0/vendors", SCOPE_COMPANY)
    project = _ep("rfis", "/rest/v1.0/projects/{project_id}/rfis", SCOPE_PROJECT)
    child = _ep(
        "lines", "/rest/v1.0/prime_contracts/{parent_id}/line_items", SCOPE_PARENT,
        parent=ParentRef("contracts", "id"),
    )
    contracts = _ep("contracts", "/rest/v1.0/prime_contracts", SCOPE_PROJECT)

    assert expand_paths(company, "42") == [("/rest/v1.0/vendors", None)]
    assert expand_paths(project, "42", [7, 9]) == [
        ("/rest/v1.0/projects/7/rfis", 7),
        ("/rest/v1.0/projects/9/rfis", 9),
    ]
    assert expand_paths(child, "42", parent_ids=[3, 4]) == [
        ("/rest/v1.0/prime_contracts/3/line_items", None),
        ("/rest/v1.0/prime_contracts/4/line_items", None),
    ]
    # No projects / no parents yields no calls rather than a malformed URL.
    assert expand_paths(project, "42", []) == []
    assert expand_paths(child, "42", parent_ids=[]) == []

    # EVERY version sends the company header. Affect's tenant 404s v1.x project endpoints
    # without it - measured 2026-08-02, see the property docstring. This assertion is the
    # regression guard: reverting to the documented "v2.0+ only" rule silently loses 28 of
    # 36 endpoints, and loses them as 404s that look like missing project tools.
    assert _ep("c", "/rest/v2.0/x", SCOPE_COMPANY, api_version="2.0").needs_company_header
    assert project.needs_company_header
    assert _ep("s", "/rest/v1.1/x", SCOPE_COMPANY, api_version="1.1").needs_company_header
    assert _ep("t", "/rest/v1.0/x", SCOPE_COMPANY, api_version="1.0").needs_company_header

    # Parents are always emitted before their children.
    order = [e.name for e in resolution_order([child, contracts, project])]
    assert order.index("contracts") < order.index("lines"), order

    assert collect_parent_ids([{"id": 1}, {"id": 2}, {"id": 1}, {}], ParentRef("x", "id"),
                          with_project=False) == [1, 2]

    # Pair form: the project travels WITH the parent id, read from either shape Procore
    # uses. Without it, /prime_contracts/{id}/line_items and budget_views/{id}/detail_rows
    # both 400 - and an empty budget_detail_rows means an empty fct_BudgetLine.
    pairs = collect_parent_ids(
        [{"id": 1, "project_id": 7}, {"id": 2, "project": {"id": 8}}, {"id": 3}],
        ParentRef("x", "id"), with_project=True)
    assert pairs == [(1, 7), (2, 8), (3, None)], pairs

    # where_field/where_value: only matching parents spawn children. Budget views are the
    # reason - each view exposes a different column set, and mixing them into one bronze
    # table makes the parser produce NULLs from whichever shape it did not expect.
    views = [{"id": 1, "name": "Procore Standard Forecast", "project_id": 7},
             {"id": 2, "name": "STANDARD BUDGET VIEW - CM", "project_id": 7},
             {"id": 3, "name": "MTM COMPARISON", "project_id": 8}]
    only_cm = ParentRef("budget_views", "id",
                        where_field="name", where_value="STANDARD BUDGET VIEW - CM")
    assert collect_parent_ids(views, only_cm, with_project=True) == [(2, 7)]

    # A company-level parent appears once per project under the SAME id. Deduping on the id
    # alone returns one project's data and looks like a small portfolio rather than a bug.
    shared = [{"id": 99, "name": "CM", "project_id": p} for p in (7, 8, 9)]
    ref = ParentRef("budget_views", "id", where_field="name", where_value="CM")
    assert collect_parent_ids(shared, ref, with_project=True) == [(99, 7), (99, 8), (99, 9)]
    # No filter means every parent, as before.
    assert len(collect_parent_ids(views, ParentRef("budget_views", "id"),
                              with_project=False)) == 3

    paired = _ep("li", "/rest/v1.0/prime_contracts/{parent_id}/line_items",
                 SCOPE_PARENT, ParentRef("contracts", "id"))
    assert expand_paths(paired, "42", parent_ids=[(1, 7), (3, None)]) == [
        ("/rest/v1.0/prime_contracts/1/line_items?project_id=7", 7),
        ("/rest/v1.0/prime_contracts/3/line_items", None),
    ]

    # A path that already carries the project must not gain a second copy of it.
    dup = _ep("d", "/rest/v1.0/x/{parent_id}/y?project_id={company_id}",
              SCOPE_PARENT, ParentRef("p", "id"))
    assert expand_paths(dup, "42", parent_ids=[(1, 7)])[0][0].count("project_id=") == 1

    # -- registry mistakes must fail loudly at load time, not silently at run time --
    def expect_error(fn: Any, label: str) -> None:
        try:
            fn()
        except ValueError:
            return
        raise AssertionError(f"{label} should raise")

    declared = _ep("pc", "/rest/v1.0/prime_contracts?project_id={project_id}", SCOPE_PROJECT,
                   unavailable_projects={562949955173068: "tool not enabled"})
    assert declared_unavailable(declared, "562949955173068") == "tool not enabled"
    assert declared_unavailable(declared, 7) is None and declared_unavailable(declared, None) is None
    expect_error(lambda: _ep("x", "/a", SCOPE_PROJECT, unavailable_projects={1: " "}),
                 "exclusion without a reason")
    expect_error(lambda: _ep("x", "/a", SCOPE_COMPANY, unavailable_projects={1: "r"}),
                 "project exclusion on a company endpoint")

    # Tombstone eligibility: complete, full, non-empty scopes only.
    def done(pid: Any, n: int = 1, status: str = "complete") -> dict:
        return {"project_id": pid, "status": status, "received_rows": n}
    full = {"mode": "full", "scopes": [done(7), done(8, status="failed"), done(9, 0),
                                       done(10, 0, "excluded_declared"), done(None),
                                       done(11), done(11, 0, "unavailable_403")]}
    assert tombstone_scopes(project, full) == [7, None]
    assert tombstone_scopes(project, dict(full, mode="incremental")) == []
    assert tombstone_scopes(_ep("m", "/m", SCOPE_PROJECT, date_range_days=30), full) == []

    assert _ep("big", "/rest/v1.0/cost_codes", SCOPE_PROJECT, per_page=1000).per_page == 1000
    expect_error(lambda: _ep("x", "/a/{parent_id}", SCOPE_PARENT, parent=ParentRef("y"), per_page=1000),
                 "per_page 1000 on a nested path")
    expect_error(lambda: _ep("x", "/rest/v2.0/a", SCOPE_PROJECT, api_version="2.0", per_page=1000),
                 "per_page 1000 on v2.0")
    expect_error(lambda: _ep("x", "/a", SCOPE_PROJECT, per_page=0), "per_page 0")

    expect_error(lambda: _ep("x", "/a", "galaxy"), "unknown scope")
    expect_error(
        lambda: _ep("x", "/a/{parent_id}/b", SCOPE_PARENT), "parent scope without parent block"
    )
    expect_error(
        lambda: _ep("x", "/a", SCOPE_PROJECT, parent=ParentRef("y")), "parent block on non-parent scope"
    )
    expect_error(
        lambda: _ep("x", "/a/b", SCOPE_PARENT, parent=ParentRef("y")), "parent scope without {parent_id}"
    )
    expect_error(lambda: validate_registry([project, project]), "duplicate name")
    expect_error(
        lambda: validate_registry([child, project]), "parent referencing a missing endpoint"
    )
    expect_error(
        lambda: validate_registry([
            _ep("a", "/x/{parent_id}", SCOPE_PARENT, parent=ParentRef("b")),
            _ep("b", "/y/{parent_id}", SCOPE_PARENT, parent=ParentRef("a")),
        ]),
        "parent cycle",
    )
    expect_error(
        lambda: validate_registry([
            _ep("a", "/x", SCOPE_COMPANY, bronze_table="t"),
            _ep("b", "/y", SCOPE_COMPANY, bronze_table="t"),
        ]),
        "duplicate bronze_table",
    )

    print("procore_scope: all checks passed")


if __name__ == "__main__":
    _selftest()
