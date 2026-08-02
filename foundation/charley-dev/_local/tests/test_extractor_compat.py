"""The extraction notebook passes procore_scope.Endpoint objects into procore_extract
functions that were written against procore_extract.Endpoint.

That works by duck typing, which is fine right up until someone renames a field on one
of the two classes and the break surfaces as a 403 or an empty table in production
rather than as an import error. These tests pin the contract.

Run:  python test_extractor_compat.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

CHARLEY_DEV = Path(__file__).resolve().parent.parent.parent
REPO = CHARLEY_DEV.parent.parent

sys.path.insert(0, str(CHARLEY_DEV / "00-platform" / "lib"))
sys.path.insert(0, str(REPO / "src" / "procore"))

import procore_extract as px  # noqa: E402
import procore_scope as ps  # noqa: E402

CHECKS: list[str] = []


def check(label: str) -> None:
    CHECKS.append(label)


def make(scope: str = "project", **kw) -> ps.Endpoint:
    return ps.Endpoint(
        name=kw.pop("name", "rfis"),
        path=kw.pop("path", "/rest/v1.0/projects/{project_id}/rfis"),
        scope=scope,
        api_version=kw.pop("api_version", "1.0"),
        bronze_table=kw.pop("bronze_table", "cd_bronze_procore_rfis"),
        **kw,
    )


def test_attribute_contract() -> None:
    """Every attribute procore_extract touches must exist on procore_scope.Endpoint."""
    required = ("name", "path", "scope", "api_version", "bronze_table", "incremental", "key")
    ep = make()
    for attr in required:
        assert hasattr(ep, attr), f"procore_scope.Endpoint is missing {attr!r}"
    assert hasattr(ep, "needs_company_header") and hasattr(ep, "major_version")
    check("procore_scope.Endpoint exposes every field procore_extract reads")

    # DELIBERATE DIVERGENCE, measured against Affect's tenant on 2026-08-02.
    #
    # procore_extract follows the documented rule: only v2.0+ sends Procore-Company-Id.
    # Affect's tenant 404s v1.x PROJECT endpoints without it - same token, same project,
    # header alone flips 404 -> 200 on v1.0 rfis, v1.1 submittals, v1.0 incidents and
    # v1.0 manpower_logs. On the first full run that cost 28 of 36 endpoints, and it looked
    # like missing project tools rather than a missing header, because the failure is a 404.
    #
    # procore_scope.Endpoint therefore always returns True, and since build_headers reads
    # the property off whichever Endpoint it is handed, our loader drives the behaviour.
    # This test now pins the divergence in place rather than forbidding it: agreement on
    # v2.0+, and OUR rule winning below that.
    for version in ("2.0", "2.1"):
        mine = make(api_version=version).needs_company_header
        theirs = px.Endpoint(
            name="x", path="/x", scope="company", api_version=version, bronze_table="t"
        ).needs_company_header
        assert mine == theirs is True, f"v{version} should send the header in both"

    for version in ("1.0", "1.1"):
        assert make(api_version=version).needs_company_header, (
            f"v{version} must send the company header - without it Affect's tenant 404s"
        )
    check("company header is sent at every API version (measured, not documented)")


def test_build_headers() -> None:
    """build_headers is procore_extract's, but the RULE is ours - it reads the property off
    whichever Endpoint it is handed. This is what makes the divergence above take effect in
    Fabric as well as locally, without forking the shared extractor."""
    for version in ("1.0", "1.1", "2.0"):
        headers = px.build_headers("tok", "562949953444705", make(api_version=version))
        assert headers["Authorization"] == "Bearer tok"
        assert headers["Procore-Company-Id"] == "562949953444705", (
            f"v{version} lost the company header - Affect's tenant 404s without it"
        )
    check("build_headers applies OUR header rule at every version, via duck typing")


def test_watermark_params() -> None:
    since = datetime(2026, 7, 1, tzinfo=timezone.utc)

    # No incremental filter declared -> full reload, whatever the watermark says.
    assert px.watermark_params(make(), since) == {}

    ep = make(incremental="filters[updated_at]")
    # First run (no watermark) is a full reload.
    assert px.watermark_params(ep, None) == {}

    params = px.watermark_params(ep, since)
    assert "filters[updated_at]" in params
    # The one-hour backward overlap is what makes clock skew harmless. It is only safe
    # because the load MERGEs on the natural key rather than appending.
    assert params["filters[updated_at]"].startswith("2026-06-30T23:00:00Z...")
    check("watermark_params accepts procore_scope.Endpoint and applies the 1h overlap")


def test_to_bronze_row() -> None:
    ingested = datetime(2026, 8, 1, tzinfo=timezone.utc)
    row = px.to_bronze_row({"id": 42, "subject": "RFI"}, make(), 7, ingested)
    assert row["_key"] == "42"
    assert row["_project_id"] == 7 and row["_source_endpoint"] == "rfis"
    # Bronze keeps the payload unparsed - it cannot drop a column it never read.
    assert '"subject": "RFI"' in row["payload"]

    # A non-default key column must be honoured (rfi_statuses keys on `value`).
    keyed = px.to_bronze_row({"value": "open"}, make(name="rfi_statuses", key="value"), None, ingested)
    assert keyed["_key"] == "open"
    check("to_bronze_row honours the registry's key column")


def test_real_registry_round_trips() -> None:
    """The shipped registry must survive every procore_extract call path."""
    endpoints = ps.load_registry(str(CHARLEY_DEV / "01-ingestion" / "Procore" / "config" / "endpoints.yml"))
    assert len(endpoints) >= 30

    for ep in endpoints:
        px.build_headers("tok", "1", ep)
        px.watermark_params(ep, datetime(2026, 7, 1, tzinfo=timezone.utc))
        px.to_bronze_row({ep.key: "x"}, ep, None, datetime.now(timezone.utc))
        ps.expand_paths(ep, "1", [7], parent_ids=[3])
    check(f"all {len(endpoints)} registry endpoints round-trip through procore_extract")

    # Only endpoints the cheatsheet confirms may declare filters[updated_at]. Incrementing
    # RFIs on created_at would miss status changes, and "open critical RFIs" is a status
    # question - so this guards against a well-meaning future edit.
    incremental = {e.name for e in endpoints if e.incremental}
    assert "rfis" not in incremental and "submittals" not in incremental
    assert all(e.incremental == "filters[updated_at]" for e in endpoints if e.incremental)
    check("no endpoint claims an unverified incremental filter")


def main() -> int:
    for fn in (
        test_attribute_contract, test_build_headers, test_watermark_params,
        test_to_bronze_row, test_real_registry_round_trips,
    ):
        fn()
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_extractor_compat: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
