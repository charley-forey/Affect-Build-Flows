"""Checks for the non-trivial extractor logic. Run: python src/procore/tests/test_extract.py

Plain asserts, no framework, no network - a fake session stands in for requests. These
cover the four behaviours that are easy to get wrong and expensive to get wrong:
pagination termination, rate-limit retry, the v2.0 company header, and the watermark.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from procore_extract import (  # noqa: E402
    Endpoint,
    Settings,
    build_headers,
    extract_endpoint,
    iter_records,
    request_with_retry,
    resolve_paths,
    updated_at_filter,
    watermark_params,
)

BASE = "https://sandbox.procore.example"

RFIS = Endpoint(
    name="rfis",
    path="/rest/v1.0/projects/{project_id}/rfis",
    scope="project",
    api_version="1.0",
    bronze_table="bronze_procore_rfis",
)
COMMITMENTS_V2 = Endpoint(
    name="commitment_contracts",
    path="/rest/v2.0/companies/{company_id}/projects/{project_id}/commitment_contracts",
    scope="project",
    api_version="2.0",
    bronze_table="bronze_procore_commitment_contracts",
)
PROJECTS = Endpoint(
    name="projects",
    path="/rest/v1.0/projects",
    scope="company",
    api_version="1.0",
    bronze_table="bronze_procore_projects",
    incremental="filters[updated_at]",
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else []
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Replays a queue of responses and records every request made."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        if not self._responses:
            return FakeResponse(200, [])
        return self._responses.pop(0)


def _page(n, start=0):
    return [{"id": start + i, "number": f"RFI-{start + i}"} for i in range(n)]


# --------------------------------------------------------------------------


def test_pagination_stops_on_short_page():
    """A page shorter than per_page is the last page."""
    session = FakeSession([FakeResponse(200, _page(3))])
    rows = list(iter_records(session, BASE, "/rest/v1.0/x", {}, per_page=10))
    assert len(rows) == 3, rows
    assert len(session.calls) == 1, "should not have asked for a second page"


def test_pagination_stops_on_total_header():
    """Full pages keep going until the Total header is satisfied."""
    session = FakeSession(
        [
            FakeResponse(200, _page(2, 0), headers={"Total": "4"}),
            FakeResponse(200, _page(2, 2), headers={"Total": "4"}),
            FakeResponse(200, _page(2, 4), headers={"Total": "4"}),  # must never be used
        ]
    )
    rows = list(iter_records(session, BASE, "/rest/v1.0/x", {}, per_page=2))
    assert len(rows) == 4, f"expected 4 rows, got {len(rows)}"
    assert len(session.calls) == 2, f"expected 2 requests, got {len(session.calls)}"
    assert [r["id"] for r in rows] == [0, 1, 2, 3]


def test_pagination_stops_on_empty_page():
    session = FakeSession([FakeResponse(200, _page(2), headers={}), FakeResponse(200, [])])
    rows = list(iter_records(session, BASE, "/rest/v1.0/x", {}, per_page=2))
    assert len(rows) == 2, rows


def test_pagination_increments_page_param():
    session = FakeSession(
        [
            FakeResponse(200, _page(2, 0), headers={"Total": "4"}),
            FakeResponse(200, _page(2, 2), headers={"Total": "4"}),
        ]
    )
    list(iter_records(session, BASE, "/rest/v1.0/x", {}, per_page=2))
    assert [c["params"]["page"] for c in session.calls] == [1, 2]
    assert all(c["params"]["per_page"] == 2 for c in session.calls)


def test_object_wrapped_response_is_unwrapped():
    session = FakeSession([FakeResponse(200, {"data": _page(2)})])
    rows = list(iter_records(session, BASE, "/rest/v1.0/x", {}, per_page=10))
    assert len(rows) == 2, rows


# --------------------------------------------------------------------------


def test_429_retries_and_honours_retry_after():
    """A throttled call must back off by exactly what Procore asks for, then succeed."""
    slept = []
    session = FakeSession(
        [
            FakeResponse(429, [], headers={"Retry-After": "7"}),
            FakeResponse(200, _page(1)),
        ]
    )
    response = request_with_retry(
        session, f"{BASE}/x", {}, {}, sleep=lambda s: slept.append(s)
    )
    assert response.status_code == 200
    assert slept == [7.0], f"expected a single 7s sleep, got {slept}"


def test_retry_backs_off_exponentially_without_retry_after():
    slept = []
    session = FakeSession(
        [FakeResponse(503), FakeResponse(503), FakeResponse(200, _page(1))]
    )
    request_with_retry(session, f"{BASE}/x", {}, {}, sleep=lambda s: slept.append(s))
    assert slept == [1.0, 2.0], f"expected exponential backoff, got {slept}"


def test_retry_gives_up_and_raises():
    session = FakeSession([FakeResponse(429) for _ in range(5)])
    try:
        request_with_retry(session, f"{BASE}/x", {}, {}, max_attempts=5, sleep=lambda s: None)
    except RuntimeError:
        pass
    else:
        raise AssertionError("should have raised after exhausting attempts")


def test_non_retryable_error_raises_immediately():
    session = FakeSession([FakeResponse(403)])
    try:
        request_with_retry(session, f"{BASE}/x", {}, {}, sleep=lambda s: None)
    except RuntimeError:
        pass
    else:
        raise AssertionError("403 should raise, not retry")
    assert len(session.calls) == 1, "403 must not be retried"


# --------------------------------------------------------------------------


def test_v2_endpoint_gets_company_header():
    """Missing this header on v2.0 is the top cause of unexplained 403s."""
    headers = build_headers("tok", "12345", COMMITMENTS_V2)
    assert headers["Procore-Company-Id"] == "12345"
    assert headers["Authorization"] == "Bearer tok"


def test_v1_endpoint_does_not_get_company_header():
    """And sending it to v1.0 is the other half of the same trap."""
    headers = build_headers("tok", "12345", RFIS)
    assert "Procore-Company-Id" not in headers, headers


def test_v11_is_treated_as_v1():
    submittals = Endpoint(
        name="submittals",
        path="/rest/v1.1/projects/{project_id}/submittals",
        scope="project",
        api_version="1.1",
        bronze_table="b",
    )
    assert "Procore-Company-Id" not in build_headers("tok", "1", submittals)


# --------------------------------------------------------------------------


def test_updated_at_filter_format():
    since = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 7, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert updated_at_filter(since, until) == "2026-07-01T00:00:00Z...2026-07-31T23:59:59Z"


def test_watermark_overlaps_by_an_hour():
    """Clock skew is real; the merge makes the overlap free."""
    last = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)
    params = watermark_params(PROJECTS, last)
    assert params["filters[updated_at]"].startswith("2026-07-20T11:00:00Z...")


def test_first_run_is_a_full_pull():
    assert watermark_params(PROJECTS, None) == {}


def test_endpoint_without_incremental_never_watermarks():
    last = datetime(2026, 7, 20, tzinfo=timezone.utc)
    assert watermark_params(RFIS, last) == {}, "rfis declares no incremental filter"


# --------------------------------------------------------------------------


def test_project_scope_expands_per_project():
    paths = resolve_paths(RFIS, "999", [11, 22])
    assert paths == [
        ("/rest/v1.0/projects/11/rfis", 11),
        ("/rest/v1.0/projects/22/rfis", 22),
    ], paths


def test_company_scope_is_called_once():
    assert resolve_paths(PROJECTS, "999", [11, 22]) == [("/rest/v1.0/projects", None)]


def test_v2_path_gets_both_ids():
    paths = resolve_paths(COMMITMENTS_V2, "999", [11])
    assert paths[0][0] == "/rest/v2.0/companies/999/projects/11/commitment_contracts"


# --------------------------------------------------------------------------


def test_bronze_rows_keep_the_raw_payload_and_stamp_project():
    """Bronze cannot drop a column it never parsed - the fix for the dropped-ID defect."""
    session = FakeSession(
        [
            FakeResponse(200, [{"id": 1, "number": "RFI-1", "cost_code_id": 77}]),
            FakeResponse(200, [{"id": 2, "number": "RFI-2", "cost_code_id": 88}]),
        ]
    )
    settings = Settings(BASE, "cid", "secret", "999")
    rows = extract_endpoint(session, settings, "tok", RFIS, [11, 22], sleep=lambda s: None)

    assert len(rows) == 2, rows
    assert [r["_project_id"] for r in rows] == [11, 22]
    assert [r["_key"] for r in rows] == ["1", "2"]
    assert all(r["_source_endpoint"] == "rfis" for r in rows)
    # The ID the semantic model needs survives into bronze untouched.
    assert '"cost_code_id": 77' in rows[0]["payload"]
    assert all(r["_ingested_at"].tzinfo is not None for r in rows), "must be tz-aware"


def test_company_scoped_extract_sends_company_id_param():
    session = FakeSession([FakeResponse(200, [{"id": 5}])])
    settings = Settings(BASE, "cid", "secret", "999")
    extract_endpoint(session, settings, "tok", PROJECTS, [], sleep=lambda s: None)
    assert session.calls[0]["params"]["company_id"] == "999"


# --------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, exc))
            print(f"  FAIL {name}: {exc}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
