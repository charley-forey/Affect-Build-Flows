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

SCOPE_COMPANY = "company"
SCOPE_PROJECT = "project"
SCOPE_PARENT = "parent"
VALID_SCOPES = (SCOPE_COMPANY, SCOPE_PROJECT, SCOPE_PARENT)


@dataclass(frozen=True)
class ParentRef:
    endpoint: str  # logical name of the endpoint supplying the ids
    field: str = "id"  # which field on those records holds the id


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

    def __post_init__(self) -> None:
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
        path = endpoint.path.format(company_id=company_id, parent_id=parent_id)
        if project_id is not None and "project_id=" not in path:
            path += ("&" if "?" in path else "?") + f"project_id={project_id}"
        out.append((path, project_id))
    return out


def collect_parent_ids(records: list[dict[str, Any]], ref: ParentRef,
                       with_project: bool = False) -> list[Any]:
    """Distinct, order-preserving ids from a parent endpoint's records.

    with_project=True returns (parent_id, project_id) pairs instead of bare ids, for the
    nested endpoints that 400 without a project (see expand_paths). The project is read
    from the parent record itself - `project_id`, or `project.id` when Procore nests it -
    so it never has to be guessed downstream.

    Kept as a flag rather than a second function because the two differ only in what they
    carry, and callers pass the result straight into expand_paths either way.
    """
    seen: dict[Any, Any] = {}
    for record in records:
        value = record.get(ref.field)
        if value is None:
            continue
        if not with_project:
            seen.setdefault(value, None)
            continue
        project = record.get("project_id")
        if project is None and isinstance(record.get("project"), dict):
            project = record["project"].get("id")
        seen.setdefault(value, project)
    if not with_project:
        return list(seen)
    return [(parent, project) for parent, project in seen.items()]


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

    assert collect_parent_ids([{"id": 1}, {"id": 2}, {"id": 1}, {}], ParentRef("x", "id")) == [1, 2]

    # Pair form: the project travels WITH the parent id, read from either shape Procore
    # uses. Without it, /prime_contracts/{id}/line_items and budget_views/{id}/detail_rows
    # both 400 - and an empty budget_detail_rows means an empty fct_BudgetLine.
    pairs = collect_parent_ids(
        [{"id": 1, "project_id": 7}, {"id": 2, "project": {"id": 8}}, {"id": 3}],
        ParentRef("x", "id"), with_project=True)
    assert pairs == [(1, 7), (2, 8), (3, None)], pairs

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
