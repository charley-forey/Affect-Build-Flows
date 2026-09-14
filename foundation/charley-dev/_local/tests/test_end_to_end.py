"""Connect raw fixtures to the real silver views, gold SQL and model column contracts.

External warehouse crosswalks/lookups stay explicit fixtures. This does not emulate Spark or DAX.
"""
from pathlib import Path
import re
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seedrunner
import test_silver

ROOT = Path(__file__).resolve().parents[2]


def main():
    con = test_silver.build()
    # The production CD source views below replace every fixture with the parsed bronze
    # output - no view reads the external warehouse any more.
    for sql in (*seedrunner.UPSTREAM_STUBS, *seedrunner.SOURCE_FIXTURES):
        con.execute(sql)
    # Seeds first: sv_project_crosswalk reads seed_ProjectCrosswalk. The real 15 rows key to
    # production ids, so the seed TABLE (not the view) is re-pointed at the bronze fixture's
    # Procore project 7 / Sage job 11 - the real view SQL still runs over it.
    for path in seedrunner.seed_files():
        for sql in seedrunner.split_statements(path.read_text(encoding="utf-8")):
            con.execute(sql)
    con.execute("CREATE OR REPLACE TABLE seed_ProjectCrosswalk AS SELECT '7' AS ProcoreProjectId, "
                "'11' AS SageJobNumber, 'primary' AS Relationship, 'fixture' AS Source")
    # Procore's project cost-code list carries every code a commitment line can reference;
    # test_silver's bronze holds only CC1 while PO line CL2 books to CC2.
    con.execute("INSERT INTO cd_bronze_procore_cost_codes VALUES " + test_silver.bronze_row(
        "CC2", {"id": "CC2", "full_code": "06-100", "name": "  Carpentry  ", "parent": {"id": "CC0"}}))
    for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/silver/10_procore_silver.sql").read_text()):
        con.execute(sql)
    count = 0
    for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/silver/01_source_views_cd.sql").read_text()):
        if "{CD_SILVER_ABFSS}" in sql:
            sql = re.sub(r"delta\.`\{CD_SILVER_ABFSS\}/(\w+)`", r"\1", sql)
            con.execute(sql)
            count += 1
    assert count == 55, "source-view contract changed; review the linked integration scope"
    assert con.execute("SELECT * FROM sv_project_crosswalk").fetchall() == [("7", "11", "Tower A")]
    assert con.execute("SELECT procore_vendor_id, sage_vendor_id FROM sv_vendors").fetchall() == [("V1", "55")]
    for path in seedrunner.gold_files():
        for sql in seedrunner.split_statements(path.read_text(encoding="utf-8")):
            con.execute(sql)

    # Revenue conservation across the actual Sage parser -> source view -> gold fact.
    source = con.execute("SELECT COUNT(*), SUM(invoice_total), SUM(amount_paid), SUM(invoice_balance) FROM sv_ar_invoices").fetchone()
    target = con.execute("SELECT COUNT(*), SUM(Amount), SUM(AmountPaid), SUM(Balance) FROM fct_Invoice").fetchone()
    assert source[0] == target[0], (source, target)
    assert con.execute("SELECT _idnum, CAST(recnum AS VARCHAR), TRIM(invnum) FROM cd_bronze_sage_acrinv ORDER BY _idnum").fetchall() == con.execute(
        "SELECT InvoiceKey, InvoiceID, InvoiceNumber FROM fct_Invoice ORDER BY InvoiceKey").fetchall()
    for a, b in zip(source[1:], target[1:]):
        assert a is not None and b is not None and abs(a - b) < 0.01, (source, target)
    # Receipt conservation: bronze acrpmt -> silver -> sv_ar_payments -> fct_Invoice.
    receipts = [con.execute(sql).fetchone()[0] for sql in (
        "SELECT SUM(amount) FROM cd_bronze_sage_acrpmt",
        "SELECT SUM(amount) FROM cd_silver_sage_ar_payments",
        "SELECT SUM(amount) FROM sv_ar_payments",
        "SELECT SUM(PaymentsReceived) FROM fct_Invoice")]
    assert len(set(receipts)) == 1 and receipts[0] == 9000.0, receipts
    from datetime import date
    assert con.execute("SELECT InvoiceID, PaidDate, DaysToPayment FROM fct_Invoice ORDER BY InvoiceID").fetchall() == [
        ("901", None, None), ("902", date(2026, 5, 20), 20)], "receipt-derived paid dates"

    sys.path.insert(0, str(ROOT / "02-transformation/dq"))
    from expectations import build_suite
    expectations = build_suite().expectations
    assert len({e.name for e in expectations}) == len(expectations)

    # cd_40_dq_checks is its own Spark session: gold's temp views are gone. Every sv_* a rule
    # reads must be created in that notebook before the cell that evaluates the suite.
    import deploy_dq
    sources = ["".join(c["source"]) for c in deploy_dq.build_notebook()["cells"]]
    evaluate = next(i for i, s in enumerate(sources) if "suite.run(" in s)
    created = set(re.findall(r"CREATE OR REPLACE TEMPORARY VIEW (sv_\w+)", "".join(sources[:evaluate])))
    referenced = {v for e in expectations for v in re.findall(r"\bsv_\w+", e.failing_sql)}
    assert referenced, "no rule reads sv_* - regex or suite changed"
    assert referenced <= created, f"DQ notebook never creates {sorted(referenced - created)}"
    assert "spark.sql(_sql)" in "".join(sources[:evaluate])
    def blocking_failures():
        failed = []
        for rule in expectations:
            try:
                rows = con.execute(rule.failing_sql.replace("`", '"')).fetchall()
            except Exception as exc:
                raise AssertionError(f"DQ rule cannot run: {rule.name}") from exc
            if rows and rule.severity == "error":
                failed.append(rule.name)
        return failed

    # test_silver's register deliberately issues 26-002 twice (the flow-concurrency race).
    # It must be the ONLY blocking failure, and it must be caught.
    assert blocking_failures() == ["dim_Job.JobNumber.unique"], blocking_failures()
    con.execute("UPDATE cd_bronze_man_job_register SET JobSeq = 3, JobNumber = '26-003' WHERE Id = 4")
    for name in ("silver/30_manual_silver.sql", "gold/13_dim_job.sql"):
        for sql in seedrunner.split_statements((ROOT / "02-transformation/sql" / name).read_text(encoding="utf-8")):
            con.execute(sql)
    # The clean integrated fixture passes the production gate: every ERROR rule, zero rows.
    assert blocking_failures() == [], blocking_failures()

    # Separate budget categories on one cost code must survive; duplicate copies must not inflate totals.
    con.execute("BEGIN")
    try:
        original = json.loads(con.execute("SELECT payload FROM cd_bronze_procore_budget_detail_rows").fetchone()[0])
        other = dict(original, category="Labor")
        other["UPDATED PRIME CONTRACT BUDGET (D = A+B+C)"] = 3780.13
        con.execute("INSERT INTO cd_bronze_procore_budget_detail_rows VALUES "
                    + test_silver.BRONZE["cd_bronze_procore_budget_detail_rows"][0] + ", "
                    + test_silver.bronze_row("B2", other, "7"))
        def rebuild_budget():
            for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/silver/10_procore_silver.sql").read_text()):
                con.execute(sql)
            for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/gold/20_fct_budgetline.sql").read_text()):
                con.execute(sql)
        rebuild_budget()
        assert con.execute("SELECT BudgetLineID, Category FROM fct_BudgetLine ORDER BY BudgetLineID").fetchall() == [("B1", "Hard Costs"), ("B2", "Labor")]
        assert abs(con.execute("SELECT SUM(BudgetAmount) FROM fct_BudgetLine").fetchone()[0] - 1053780.13) < .001
        key_rule = next(e for e in expectations if e.name.startswith("fct_BudgetLine.") and "unique" in e.name)
        assert not con.execute(key_rule.failing_sql.replace("`", '"')).fetchall()
        conflict = dict(original, original_budget_amount=999999)
        con.execute("INSERT INTO cd_bronze_procore_budget_detail_rows VALUES " + test_silver.bronze_row("B1", conflict, "7"))
        rebuild_budget()
        assert len(con.execute(key_rule.failing_sql.replace("`", '"')).fetchall()) == 1
        assert key_rule.severity == "error"
    finally:
        con.execute("ROLLBACK")

    # Missing accounting inputs are unknown, never a zero-value, fully paid invoice.
    con.execute("UPDATE cd_bronze_sage_acrinv SET invamt=0, amtpad=NULL, invbal=NULL")
    for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/silver/26_sage_silver.sql").read_text()):
        con.execute(sql)
    for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/gold/22_fct_invoice.sql").read_text()):
        con.execute(sql)
    assert con.execute("SELECT COUNT(*) FROM fct_Invoice").fetchone()[0] == source[0]
    assert con.execute("SELECT COUNT(*) FROM fct_Invoice WHERE Amount IS NOT NULL OR IsPaid IS NOT NULL").fetchone()[0] == 0
    for column in ("Amount", "AmountPaid", "Balance"):
        rule = next(e for e in expectations if e.name == f"fct_Invoice.{column}.not_null")
        assert rule.severity == "error"
        assert len(con.execute(rule.failing_sql.replace("`", '"')).fetchall()) == source[0]

    # A conflicting crosswalk may not choose the lexically greatest ID as if verified.
    con.execute("CREATE OR REPLACE TABLE seed_ProjectCrosswalk AS SELECT * FROM (VALUES ('P1','S1','primary','t'),('P1','S2','primary','t')) AS t(ProcoreProjectId,SageJobNumber,Relationship,Source)")
    con.execute("CREATE OR REPLACE TEMPORARY VIEW sv_projects AS SELECT 'P1' AS project_id, 'Test' AS project_name, 'PROCORE' AS origin_code")
    for name in ("10_dim_project.sql", "15_dim_projectcrosswalk.sql"):
        for sql in seedrunner.split_statements((ROOT / "02-transformation/sql/gold" / name).read_text()):
            con.execute(sql)
    assert con.execute("SELECT SageJobNumber, IsInCrosswalk FROM dim_Project WHERE ProjectKey='P1'").fetchone() == (None, False)
    assert con.execute("SELECT SageProjectId, HasAmbiguousSageMatch, SageMatchMethod FROM dim_ProjectCrosswalk WHERE ProjectKey='P1'").fetchone() == (None, True, "AMBIGUOUS")

    # No model column can silently disappear between the parsers and report binding.
    checked = 0
    # fct_DailySnapshot is written by the DQ gate, not the gold build: run its real capture
    # SQL (same substitution as test_report.py) so its model columns are checked too.
    import deploy_dq
    for statement in deploy_dq.snapshot_statements():
        con.execute(statement.replace("{SNAPSHOT_DATE}", "2026-01-31").replace("{RUN_ID}", "test")
                    .replace(") USING DELTA", ")"))
    for directory in (ROOT / "04-semantic_models").glob("*.SemanticModel"):
        for path in (directory / "definition/tables").glob("*.tmdl"):
            text = path.read_text(encoding="utf-8")
            match = re.search(r"^table\s+(.+)$", text, re.M)
            if not match:
                continue
            table = match[1].strip("'")
            if table == "meta_PipelineRun":
                continue  # The notebook writes this runtime table, not the SQL transforms.
            source_table = re.search(r"entityName:\s*(\w+)", text)
            physical = source_table[1] if source_table else table
            columns = {r[0] for r in con.execute(f'DESCRIBE "{physical}"').fetchall()}
            declared = {c.strip("'") for c in re.findall(r"^\tcolumn\s+(.+)$", text, re.M)}
            assert declared <= columns, f"{directory.name}: {table} missing {declared - columns}"
            checked += 1
    con.close()
    print(f"end-to-end: {count} own-source views, Sage revenue conservation, {checked} model table contracts, {len(expectations)} DQ rules executable, zero blocking on the clean fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
