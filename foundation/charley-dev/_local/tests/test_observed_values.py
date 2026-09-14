"""Production-observed categorical values vs the SQL that branches on them, and vs fixtures.

Why: the offline suite once passed while the live candidate BLOCKED, because no fixture
carried a real status value (void change orders) - and a later review found Procore
'Pending - ...' labels nobody had mapped. Offline SQL tests only prove the values someone
thought to write down. This checks the values production actually holds.

  (a) every string-literal comparison in silver/gold/snapshot SQL (CASE x WHEN '..', = '..',
      IN ('..'), LIKE '..') is accounted for below - a new branch forces a decision here;
  (b) every observed value in observed_values.json is handled explicitly by its SQL block,
      or listed as intentionally falling to that block's documented default (or as a known
      defect, printed loudly);
  (c) the seedrunner fixtures carry a row for every observed value of the key status columns.

Run alone:  python test_observed_values.py      (also run from test_gold.py)
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import seedrunner  # noqa: E402

HERE = Path(__file__).resolve().parent
SQL = seedrunner.CHARLEY_DEV / "02-transformation" / "sql"
SEED = seedrunner.CHARLEY_DEV / "02-transformation" / "seed"
CATALOGUE = json.loads((HERE / "observed_values.json").read_text(encoding="utf-8"))["fields"]
UNKNOWN = "unknown - capture next time capacity allows"

upper = lambda v: v.strip().upper()  # noqa: E731
lower = lambda v: v.strip().lower()  # noqa: E731
exact = lambda v: v.strip()  # noqa: E731

# ---------------------------------------------------------------------------------------
# The maintained mapping: catalogue field -> the SQL block that branches on it.
#   start/end   regexes bounding the block inside `file` (comments stripped; the block
#               is the text after `start` up to and including `end`)
#   norm        what silver+gold do to the raw value before comparing
#   default     what a value NOT named in the block gets - quoted from the SQL
#   default_ok  observed values deliberately left to that default, with the reason
#   defects     observed values that fall to the default and should not - printed as
#               POTENTIAL LIVE DEFECTS, kept here so the suite stays green while they are open
# ---------------------------------------------------------------------------------------
MAPPINGS = {
    "prime_change_order.status": dict(
        file="gold/21_fct_changeorder.sql", start=r"CASE WHEN LOWER\(TRIM\(status\)\) IN", end=r"AS IsPending",
        norm=lower, default="IsPending = TRUE (anything not approved/closed/void is outstanding)",
        default_ok={"pending": "outstanding by definition",
                    "draft": "counted pending today; open question to Affect (definitions-evidence section 3)"},
        defects={}),
    # Same vocabulary Procore uses on CO packages; not on prime COs yet, but nothing stops it.
    "potential_change_order.status": dict(
        file="gold/21_fct_changeorder.sql", start=r"CASE WHEN LOWER\(TRIM\(status\)\) IN", end=r"AS IsPending",
        norm=lower, default="IsPending = TRUE",
        default_ok={"pending": "outstanding", "draft": "as prime CO draft",
                    "pricing": "Procore Pending variant", "proceeding": "Procore Pending variant"},
        defects={"rejected": "Procore: not reflected in budget - would count as pending",
                 "no_charge": "Procore: no financial charge - would count as pending",
                 "not_proceeding": "Procore: dead, like void - would count as pending"}),
    "submittal.status_name": dict(
        file="silver/24_qc_procore_silver.sql", start=r"TABLE cd_silver_qc_submittal.*?AS source_status", end=r"AS status_code",
        norm=upper, default="status_code NULL (unmapped stays visible)", default_ok={}, defects={}),
    "submittal.status_category": dict(
        file="gold/23_fct_rfisubmittal.sql", start=r"SELECT \*,", end=r"FROM sv_submittals",
        norm=upper, default="neither closed nor draft -> open",
        default_ok={"OPEN": "open is the default by design"}, defects={}),
    "billing.status_label": dict(
        file="gold/27_fct_billing.sql", start=r"CREATE OR REPLACE TABLE fct_Billing", end=r"FROM ranked",
        norm=upper, default="issued, not approved: may win IsLatestPeriod, never IsLatestApprovedPeriod",
        default_ok={"UNDER_REVIEW": "issued, awaiting approval (documented at _approved_rank)",
                    "PENDING_OWNER_APPROVAL": "issued, awaiting approval (documented at _approved_rank)",
                    "REVISE_AND_RESUBMIT": "issued, sent back - not approved"},
        defects={}),
    "commitment_line.holder_type": dict(
        file="gold/31_bridge_vendorcostcode.sql", start=r"AND \(\(l\.holder_type", end=r"\'Purchase Order\'\)\)",
        norm=exact, default="line dropped from the Committed bridge", default_ok={}, defects={}),
    "direct_cost_line.holder_type": dict(
        file="gold/31_bridge_vendorcostcode.sql", start=r"WHERE l\.holder_type", end=r"\'DirectCost::Item\'",
        norm=exact, default="line dropped from the Actual bridge", default_ok={}, defects={}),
    "direct_cost.cost_type": dict(
        file="gold/28_fct_directcost.sql", start=r"CASE cost_type", end=r"AS CostCategory",
        norm=lower, default="raw cost_type passed through", default_ok={}, defects={}),
    "direct_cost.status_label": dict(
        file="gold/28_fct_directcost.sql", start=r"UPPER\(COALESCE\(status_label", end=r"AS IsApproved",
        norm=upper, default="IsApproved = FALSE", default_ok={}, defects={}),
    "observation.status_label": dict(
        file="silver/24_qc_procore_silver.sql", start=r"TABLE cd_silver_qc_ncr.*?AS source_status", end=r"AS status_code",
        norm=upper, default="status_code NULL", default_ok={}, defects={}),
    "observation.observation_type": dict(
        file="silver/24_qc_procore_silver.sql", start=r"TABLE cd_silver_qc_ncr.*?AS status_code", end=r"AS item_class_code",
        norm=upper, default="item_class_code NULL", default_ok={}, defects={}),
    "punch_item.status_label": dict(
        file="silver/24_qc_procore_silver.sql", start=r"TABLE cd_silver_qc_punch.*?AS source_status", end=r"AS status_code",
        norm=upper, default="status_code NULL",
        default_ok={},
        defects={"OVERDUE": "77 live punch items get status_code NULL - the CASE lists workflow_status "
                            "values but reads status_label (display status Open/Overdue/Closed)"}),
    "punch_item.punch_item_type": dict(
        file="silver/24_qc_procore_silver.sql", start=r"TABLE cd_silver_qc_punch.*?AS status_code", end=r"AS item_class_code",
        norm=upper, default="PUNCH_ITEM (WHEN punch_item_type IS NOT NULL)",
        default_ok={v: "an ordinary punch item" for v in (
            "PUNCH LIST", "AFFECT GROUP", "ARCHITECTURAL", "OWNER/ENGINEER/ARCHITECT - PUNCH LIST",
            "ENGINEER", "ROLLING (PUNCH AS YOU GO)", "NEW SCOPE", "PRE-CON", "DEFECTS")},
        defects={}),
    "vendor_insurance.insurance_type": dict(
        file="gold/32_fct_vendorinsurance.sql", start=r"CASE WHEN UPPER\(insurance_type\)", end=r"AS InsuranceCategory",
        norm=upper, default="InsuranceCategory 'Other'",
        default_ok={"CERTIFICATE OF LIABILITY INSURANCE": "document title, not a coverage type"}, defects={}),
    "manual.win_type": dict(
        file="silver/30_manual_silver.sql", start=r"UPPER\(TRIM\(b\.WinType\)\)", end=r"FROM cd_bronze_man_wins",
        norm=upper, default="row rejected ('invalid WinType')", default_ok={}, defects={}),
    "manual.impact_code": dict(
        file="silver/30_manual_silver.sql", start=r"COALESCE\(b\.ImpactCode", end=r"FROM cd_bronze_man_risks",
        norm=upper, default="row rejected ('invalid ImpactCode')", default_ok={}, defects={}),
    "manual.stage": dict(
        file="silver/30_manual_silver.sql", start=r"FROM cd_bronze_man_job_register\s+WHERE UPPER", end=r"JobNumber IS NULL",
        norm=upper, default="not reported as a half-run flow", default_ok={}, defects={}),
    "manual.gate_type": dict(
        file="silver/31_qc_manual_silver.sql", start=r"COALESCE\(b\.GateType", end=r"FROM cd_bronze_man_qc_gate",
        norm=upper, default="row rejected ('invalid GateType')", default_ok={}, defects={}),
}

# Trade labels resolve through seed CSVs, not literals: exact TradeKey, then alias.
TRADE_FIELDS = {
    "punch_item.trade": dict(
        default="TradeLabel 'Unmapped trade: <raw>', HasUnmappedTrade = TRUE (33_fct_qc.sql)",
        default_ok={v: "deliberately unaliased - needs Affect to pick a trade (33_fct_qc.sql)" for v in (
            "Drywall/Carpentry", "Concrete Superstructure", "Concrete")}
        | {v: "no equivalent in the 26-sheet trade library (33_fct_qc.sql)" for v in (
            "Glazing", "Roofing", "Windows", "Demolition", "Window Treatments", "WINDOW TREATMENT",
            "Low Voltage", "Trash Chute/Compactors", "Specalties")},
        defects={}),
    "observation.trade": dict(default="as punch_item.trade", default_ok={}, defects={}),
}

# Observed fields no SQL branches on today - catalogued for the next person who adds one.
NO_BRANCH = {
    "rfi.status": "IsOpen comes from responded_date; RFI drafts not split (ponytail note in 23_fct_rfisubmittal.sql)",
    "commitment.status_label": "not branched: VOID/DRAFT commitments are summed as Committed in bridge_VendorCostCode",
    "punch_item.workflow_status": "carried in silver, not branched",
    "vendor_insurance.status_label": "passed through as StatusLabel",
    "manpower_log.status": "not carried into silver",
    "manpower_log.trade": "not carried into silver",
    "outbuild_activity.activity_type": "passed through as ActivityType",
    "outbuild_activity.status": "no such field - NULL",
    "sage.status_code": "passed through as StatusCode",
}

# (a) Every (file, column) the scanner finds comparing to a string literal.
ACCOUNTED = {
    ("gold/21_fct_changeorder.sql", "status"): ["prime_change_order.status", "potential_change_order.status"],
    ("gold/30_fct_financialperiod.sql", "StatusLabel"): ["prime_change_order.status"],
    ("snapshot/fct_dailysnapshot.sql", "StatusLabel"): ["prime_change_order.status"],
    ("gold/23_fct_rfisubmittal.sql", "status_category"): ["submittal.status_category"],
    ("gold/23_fct_rfisubmittal.sql", "status_label"): ["submittal.status_name"],
    ("gold/33_fct_qc.sql", "status_category"): ["submittal.status_category"],
    ("gold/33_fct_qc.sql", "source_status"): ["submittal.status_name"],
    ("gold/27_fct_billing.sql", "status_label"): ["billing.status_label"],
    ("gold/28_fct_directcost.sql", "cost_type"): ["direct_cost.cost_type"],
    ("gold/28_fct_directcost.sql", "status_label"): ["direct_cost.status_label"],
    ("gold/31_bridge_vendorcostcode.sql", "holder_type"): ["commitment_line.holder_type", "direct_cost_line.holder_type"],
    ("gold/32_fct_vendorinsurance.sql", "insurance_type"): ["vendor_insurance.insurance_type"],
    ("silver/24_qc_procore_silver.sql", "status_label"): ["observation.status_label", "punch_item.status_label", "submittal.status_name"],
    ("silver/24_qc_procore_silver.sql", "observation_type"): ["observation.observation_type"],
    ("silver/24_qc_procore_silver.sql", "punch_item_type"): ["punch_item.punch_item_type"],
    ("silver/30_manual_silver.sql", "WinType"): ["manual.win_type"],
    ("silver/30_manual_silver.sql", "ImpactCode"): ["manual.impact_code"],
    ("silver/30_manual_silver.sql", "Stage"): ["manual.stage"],
    ("silver/31_qc_manual_silver.sql", "GateType"): ["manual.gate_type"],
    # Not source vocabularies - constants this codebase writes itself, or free text.
    ("silver/24_qc_procore_silver.sql", "subject"): "free-text subject keywords, not a status vocabulary",
    ("silver/24_qc_procore_silver.sql", "target_table"): "internal reject table names",
    ("silver/25_outbuild_silver.sql", "target_table"): "internal reject table names",
    ("silver/27_sage_rejects.sql", "target_table"): "internal reject table names",
    ("gold/45_dq_datagap.sql", "target_table"): "internal reject table names",
    ("silver/01_source_views_cd.sql", "Relationship"): "committed seed CSV vocabulary (project_crosswalk.csv)",
    ("gold/12_dim_costcode.sql", "cost_code"): "code-format parsing, not a category",
    ("gold/17_dim_costcodecrosswalk.sql", "cost_code_raw"): "code-format parsing, not a category",
    ("gold/31_bridge_vendorcostcode.sql", "commitment_type"): "constant written by 23_commitment_silver.sql",
    ("gold/31_bridge_vendorcostcode.sql", "amount_type"): "constant written in the same file",
    ("gold/33_fct_qc.sql", "submittal_type_code"): "code derived in 24_qc_procore_silver.sql",
    ("snapshot/fct_dailysnapshot.sql", "ItemType"): "constant written by the gold facts",
}

KEYWORDS = {
    "CASE", "WHEN", "THEN", "ELSE", "END", "AND", "OR", "NOT", "IN", "IS", "NULL", "LIKE", "UPPER",
    "LOWER", "TRIM", "COALESCE", "REPLACE", "CAST", "AS", "WHERE", "ON", "SELECT", "FROM", "BY",
    "ORDER", "NULLIF", "CONCAT", "SUM", "COUNT", "MAX", "MIN", "IF", "TRUE", "FALSE", "STRING",
}


def strip_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def discover() -> set[tuple[str, str]]:
    """Best-effort: the last column identifier before each comparison with a non-empty literal."""
    found = set()
    for path in sorted(SQL.glob("*/*.sql")):
        rel = f"{path.parent.name}/{path.name}"
        sql = strip_comments(path.read_text(encoding="utf-8"))
        hits = [(m.start(), sql[max(0, m.start() - 120):m.start()])
                for m in re.finditer(r"(?:<>|!=|=|\bIN\s*\(|\bLIKE)\s*'(?=[^'])", sql)]
        hits += [(m.start(), m.group(1)) for m in re.finditer(r"\bCASE\s+([^\n]+?)\s+WHEN\s+'", sql)]
        for _, before in hits:
            before = re.sub(r"'[^']*'", "", before.split("\n")[-1])
            idents = [i.split(".")[-1] for i in re.findall(r"[A-Za-z_][\w.]*", before)]
            idents = [i for i in idents if i.upper() not in KEYWORDS]
            if idents:
                found.add((rel, idents[-1]))
    return found


def block(m: dict) -> str:
    sql = strip_comments((SQL / m["file"]).read_text(encoding="utf-8"))
    start = re.search(m["start"], sql, re.S)
    assert start, f"{m['file']}: block start {m['start']!r} not found - update MAPPINGS"
    end = re.compile(m["end"]).search(sql, start.end())
    assert end, f"{m['file']}: block end {m['end']!r} not found after start - update MAPPINGS"
    return sql[start.end():end.end()]


def handled_by(m: dict):
    # Only what is compared against counts - never what a branch outputs (THEN/ELSE ...),
    # or an output code like 'CORRECTED' would pass for an input nobody mapped.
    text = re.sub(r"\b(?:THEN|ELSE)\b[^\n]*", "", block(m))
    likes = re.findall(r"LIKE\s+'([^']*)'", text)
    literals = set(re.findall(r"'([^']*)'", text)) - set(likes) - {""}
    patterns = [re.compile("^" + ".*".join(map(re.escape, p.split("%"))) + "$", re.S) for p in likes]
    assert literals or patterns, f"{m['file']}: no literals in block {m['start']!r}"
    return lambda v: v in literals or any(p.match(v) for p in patterns)


def trade_resolver():
    with open(SEED / "qc_trades.csv", encoding="utf-8") as f:
        keys = {r["TradeKey"] for r in csv.DictReader(f)}
    with open(SEED / "qc_trade_alias.csv", encoding="utf-8") as f:
        aliases = {r["ProcoreTrade"].strip().upper() for r in csv.DictReader(f)}
    return lambda v: v.strip().upper().replace(" ", "_") in keys or v.strip().upper() in aliases


def classify(field: str, m: dict, is_handled, norm) -> list[str]:
    """Return defect lines; raise on any value neither handled nor documented."""
    entry = CATALOGUE[field]
    defects, unexplained = [], []
    for raw, count in entry["values"].items():
        v = norm(raw)
        if is_handled(v):
            assert v not in m["default_ok"] and v not in m["defects"], \
                f"{field}: {raw!r} is now handled by the SQL - remove it from default_ok/defects"
        elif v in m["defects"]:
            defects.append(f"{field} = {raw!r} ({count} rows) -> {m['default']}: {m['defects'][v]}")
        elif v not in m["default_ok"]:
            unexplained.append(raw)
    assert not unexplained, (
        f"{field}: production values {unexplained} fall to the default ({m['default']}) and nobody "
        f"said that was intended. Map them in the SQL, or add them to default_ok/defects in "
        f"test_observed_values.py with the reason.")
    return defects


def test_catalogue_shape(check) -> None:
    for field, entry in CATALOGUE.items():
        assert entry["status"] in ("observed", UNKNOWN), (field, entry["status"])
        assert entry["status"] == "observed" or not entry["values"], f"{field}: unknown but has values"
        assert entry["status"] != "observed" or entry["provenance"], f"{field}: observed with no provenance"
        for p in entry["provenance"]:
            assert p.get("file") and p.get("captured"), (field, p)
        assigned = (field in MAPPINGS) + (field in TRADE_FIELDS) + (field in NO_BRANCH)
        assert assigned == 1, f"{field}: must be in exactly one of MAPPINGS / TRADE_FIELDS / NO_BRANCH"
    for field in (*MAPPINGS, *TRADE_FIELDS, *NO_BRANCH):
        assert field in CATALOGUE, f"{field}: mapped but missing from observed_values.json"
    known = sum(e["status"] == "observed" for e in CATALOGUE.values())
    check(f"observed_values.json: {len(CATALOGUE)} fields, {known} with production evidence, "
          f"{len(CATALOGUE) - known} marked unknown rather than guessed")


def test_sql_branches_accounted(check) -> None:
    found = discover()
    missing = sorted(found - ACCOUNTED.keys())
    assert not missing, (
        f"New string-literal branches in SQL {missing}: add each to ACCOUNTED (and its values to "
        f"observed_values.json) or say why it is not a source vocabulary.")
    stale = sorted(ACCOUNTED.keys() - found)
    assert not stale, f"ACCOUNTED entries the SQL no longer has: {stale}"
    for key, fields in ACCOUNTED.items():
        if isinstance(fields, list):
            for field in fields:
                assert field in CATALOGUE, (key, field)
    check(f"every string-literal branch in silver/gold/snapshot SQL ({len(found)} file-columns) "
          f"is catalogued or explained")


def test_observed_values_handled(check) -> list[str]:
    defects = []
    for field, m in MAPPINGS.items():
        defects += classify(field, m, handled_by(m), m["norm"])
    resolve = trade_resolver()
    for field, m in TRADE_FIELDS.items():
        defects += classify(field, m, resolve, exact)
    for line in defects:
        print(f"  !!  POTENTIAL LIVE DEFECT: {line}")
    check(f"every production value is mapped by its SQL block or documented as defaulting "
          f"({len(defects)} known defects printed above)")
    return defects


# (c) key status columns: fixture view, column, normalisation the SQL applies.
KEY_FIXTURES = {
    "prime_change_order.status": ("sv_prime_change_orders", "status", lower),
    "submittal.status_name": ("sv_submittals", "status_label", upper),
    "submittal.status_category": ("sv_submittals", "status_category", upper),
    "rfi.status": ("sv_rfis", "status_label", lower),
    "billing.status_label": ("sv_billing", "status_label", upper),
}


def test_fixtures_cover_observed(check) -> None:
    import duckdb
    con = duckdb.connect()
    for sql in seedrunner.SOURCE_FIXTURES:
        con.execute(sql)
    for field, (view, column, norm) in KEY_FIXTURES.items():
        present = {norm(r[0]) for r in con.execute(f"SELECT DISTINCT {column} FROM {view}").fetchall()
                   if r[0] is not None}
        missing = sorted(v for v in CATALOGUE[field]["values"] if norm(v) not in present)
        assert not missing, f"{view}.{column} has no fixture row for production values {missing}"
        check(f"{view}.{column} fixtures include every production value of {field}")


def main() -> int:
    checks: list[str] = []
    test_catalogue_shape(checks.append)
    test_sql_branches_accounted(checks.append)
    test_observed_values_handled(checks.append)
    test_fixtures_cover_observed(checks.append)
    for label in checks:
        print(f"  ok  {label}")
    print(f"\ntest_observed_values: {len(checks)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
