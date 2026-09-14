"""Offline checks for reconcile_live.py comparison functions: synthetic inputs at the
pass/fail boundaries. No network, no Fabric."""
import json
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reconcile_live as rl  # noqa: E402

CHECKS = []


def check(name, cond):
    assert cond, name
    CHECKS.append(name)


def test_ar_conservation():
    layer = dict(rows=149, billed=26153291.94, paid=18713981.77, balance=7439310.17)
    ok = rl.cmp_ar_conservation({"bronze": layer, "silver": dict(layer), "model": dict(layer, billed=26153291.944)})
    check("1 sub-cent difference passes", ok["status"] == "PASS")
    bad = rl.cmp_ar_conservation({"bronze": layer, "silver": dict(layer, paid=18713981.76), "model": layer})
    check("1 one cent off fails", bad["status"] == "FAIL" and "paid" in bad["summary"])
    check("1 row count off fails", rl.cmp_ar_conservation({"a": layer, "b": dict(layer, rows=148)})["status"] == "FAIL")
    check("1 missing value fails", rl.cmp_ar_conservation({"a": layer, "b": dict(layer, balance=None)})["status"] == "FAIL")


def test_unmatched_ar():
    rows = [dict(job="2", invoice_id="98", amount=50.0), dict(job="2", invoice_id="105", amount=63078.0)]
    first = rl.cmp_unmatched_ar(rows, None)
    check("2 first run lists everything as new", first["status"] == "WARN" and first["detail"]["new_jobs"] == ["2"])
    same = rl.cmp_unmatched_ar(rows, first["detail"])
    check("2 unchanged since previous passes", same["status"] == "PASS" and same["detail"]["total_amount"] == 63128.0)
    more = rl.cmp_unmatched_ar(rows + [dict(job="28", invoice_id="149", amount=539632.28)], first["detail"])
    check("2 new job and invoice warn", more["status"] == "WARN" and more["detail"]["new_jobs"] == ["28"]
          and more["detail"]["new_invoice_ids"] == ["149"])


def test_ar_receipts():
    documented = {20: 113716.90, 21: 9190.68}
    excused = [dict(recnum=20, paid=113716.90, receipts=0), dict(recnum=21, paid=9190.68, receipts=0)]
    check("3 documented opening balances pass", rl.cmp_ar_receipts(excused, documented, 0)["status"] == "PASS")
    drift = rl.cmp_ar_receipts([dict(recnum=20, paid=113716.91, receipts=0)], documented, 0)
    check("3 documented exception that changed fails", drift["status"] == "FAIL")
    check("3 orphan receipts fail", rl.cmp_ar_receipts([], documented, 1)["status"] == "FAIL")
    new = rl.cmp_ar_receipts(excused + [dict(recnum=127, paid=25966.02, receipts=14964.62)], documented, 0)
    check("3 undocumented mismatch warns with amount", new["status"] == "WARN"
          and new["detail"]["new_mismatches"][0]["difference"] == 11001.40)


def test_ap_cost():
    check("4 tolerance floor is 25k", rl.ap_tolerance(1000, 2000) == 25000)
    check("4 tolerance is 10% of the larger side", rl.ap_tolerance(3_000_000, 2_000_000) == 300_000)
    at_edge = rl.cmp_ap_cost([dict(job="1", ap=100000, spent=125000)], [])
    check("4 exactly 25k variance passes", at_edge["status"] == "PASS")
    over = rl.cmp_ap_cost([dict(job="1", ap=100000, spent=125000.01)], [])
    check("4 just over 25k warns", over["status"] == "WARN" and over["detail"]["over_tolerance"][0]["job"] == "1")
    check("4 null spent counts as zero", rl.cmp_ap_cost([dict(job="18", ap=43422.5, spent=None)], [])["status"] == "WARN")
    check("4 ERP-only at 5k passes", rl.cmp_ap_cost([], [dict(job="9", vendor="7", ap=5000)])["status"] == "PASS")
    check("4 ERP-only over 5k warns", rl.cmp_ap_cost([], [dict(job="9", vendor="7", ap=5000.01)])["status"] == "WARN")


def test_submittals():
    check("5 clean passes", rl.cmp_submittals(0, 0, 32)["status"] == "PASS")
    check("5 one closed counted open fails", rl.cmp_submittals(1, 0, 32)["status"] == "FAIL")
    check("5 negative turnaround warns", rl.cmp_submittals(0, 1, 32)["status"] == "WARN")
    check("5 median 0 warns", rl.cmp_submittals(0, 0, 0)["status"] == "WARN")
    check("5 median 1 and 365 pass", rl.cmp_submittals(0, 0, 1)["status"] == "PASS"
          and rl.cmp_submittals(0, 0, 365)["status"] == "PASS")
    check("5 median 366 or blank warns", rl.cmp_submittals(0, 0, 366)["status"] == "WARN"
          and rl.cmp_submittals(0, 0, None)["status"] == "WARN")


def test_carry_forward():
    check("6 equal balances pass", rl.cmp_carry_forward("2026-08", {"Current Contract": (35301887.38, 35301887.38)})["status"] == "PASS")
    bad = rl.cmp_carry_forward("2026-08", {"Current Contract": (35301887.38, 35301887.38),
                                           "Pending Change Orders": (251.0, 49463.97)})
    check("6 sparse month balance fails", bad["status"] == "FAIL" and "Pending" in bad["summary"])
    check("6 blank month fails", rl.cmp_carry_forward("2026-08", {"x": (None, 5.0)})["status"] == "FAIL")
    check("6 latest complete month", rl.latest_complete_month(date(2026, 9, 14)) == date(2026, 8, 1)
          and rl.latest_complete_month(date(2026, 1, 1)) == date(2025, 12, 1))


def test_insurance():
    today = date(2026, 9, 14)
    check("7 future expiry, few expired passes", rl.cmp_insurance(date(2027, 1, 1), today, 49, 100)["status"] == "PASS")
    check("7 half expired warns", rl.cmp_insurance(date(2027, 1, 1), today, 50, 100)["status"] == "WARN")
    check("7 latest expiry in the past warns", rl.cmp_insurance(date(2025, 4, 1), today, 0, 105)["status"] == "WARN")
    check("7 expiring today is not past", rl.cmp_insurance(today, today, 0, 1)["status"] == "PASS")


def test_freshness():
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    run = lambda **kw: dict(dict(run_id="R1", status="ok", run_at=now - timedelta(hours=30)), **kw)
    check("8 same run, 30h old passes", rl.cmp_freshness({"a": run(), "b": run()}, now)["status"] == "PASS")
    check("8 older than 30h warns", rl.cmp_freshness({"a": run(), "b": run(run_at=now - timedelta(hours=30, seconds=1))}, now)["status"] == "WARN")
    check("8 different run ids fail", rl.cmp_freshness({"a": run(), "b": run(run_id="R2")}, now)["status"] == "FAIL")
    check("8 blocked status fails", rl.cmp_freshness({"a": run(), "b": run(status="blocked")}, now)["status"] == "FAIL")
    check("8 missing run fails", rl.cmp_freshness({"a": run(run_id=None), "b": run(run_id=None)}, now)["status"] == "FAIL")


def test_division():
    check("9 two digits and blank pass", rl.cmp_division({"01": 983, "28": 55, None: 114})["status"] == "PASS")
    bad = rl.cmp_division({"01": 983, "1": 736, "123": 1, "A1": 2})
    check("9 unpadded and malformed fail", bad["status"] == "FAIL" and bad["detail"]["nonconforming_codes"] == 739)


def test_blank_members():
    check("10 none passes", rl.cmp_blank_members({"fct_Invoice": 0}, {"t": (0, 10)})["status"] == "PASS")
    check("10 orphan project rows warn", rl.cmp_blank_members({"fct_Invoice": 38}, {"t": (0, 10)})["status"] == "WARN")
    blank = rl.cmp_blank_members({}, {"t": (700, 2583), "empty": (0, 0)})
    check("10 blank trade warns with share", blank["status"] == "WARN" and blank["detail"]["trade"]["t"]["share"] == 0.271)


def test_blank_member_query_failure():
    live = rl.Live.__new__(rl.Live)
    live.apr, live.qc = "monthly", "qc"
    calls = []
    def unavailable(model, query):
        calls.append(query)
        if len(calls) == 1:
            raise RuntimeError("query unavailable")
        return [{"n": 0, "b": 0}]
    live.dax = unavailable
    try:
        live.c10()
    except RuntimeError as exc:
        check("10 query failure propagates instead of silently skipping", str(exc) == "query unavailable")
    else:
        raise AssertionError("failed query was treated as a completed check")


def test_previous_detail_matches_model():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write = lambda name, model, detail, status="WARN": (d / name).write_text(json.dumps(
            dict(target=dict(model_id=model), checks=[dict(id="2", status=status, detail=detail)])))
        write("20260913T000000Z.json", "m1", {"v": 1})
        write("20260914T000000Z.json", "other", {"v": 2})
        write("20260914T010000Z.json", "m1", {"v": 3}, status="ERROR")
        check("previous run: newest same-model, skips errored runs", rl.previous_detail("2", "m1", d) == {"v": 1})
        check("previous run: none for unknown model", rl.previous_detail("2", "m9", d) is None)


def test_sql_guard():
    live = rl.Live.__new__(rl.Live)
    for bad in ("DROP TABLE x", "SELECT 1; DELETE FROM x", "UPDATE x SET a=1"):
        try:
            live.sql(bad)
        except ValueError:
            continue
        raise AssertionError(bad)
    CHECKS.append("sql guard refuses writes")


def main():
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    for c in CHECKS:
        print(f"  ok  {c}")
    print(f"\ntest_reconcile_live: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
