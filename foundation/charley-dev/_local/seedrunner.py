"""Run the gold seed SQL through DuckDB so it can be verified without Fabric.

The .sql files are written in Spark SQL because Fabric is the production target. DuckDB
executes them unchanged given the compatibility macros below - the same trick
src/procore/run_local.py already uses for get_json_object and datediff.

That means the local run verifies the actual production SQL, not a re-implementation of
it. What it does NOT verify is Spark dialect edge cases; those get checked on the first
Fabric run.

Usage:
    python seedrunner.py           # build the seeds and print row counts
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPO = CHARLEY_DEV.parent.parent

# Seeds live in two places, deliberately:
#   src/procore/sql  - dim_Trade / dim_Status, already written and tested for slice 1.
#                      Reused rather than duplicated; two copies of a seed is two seeds
#                      that drift.
#   charley-dev      - the five the earlier work did not cover.
#
# SEEDS ONLY - files starting with 0. The 1*/2*/3* files in the same folder build the
# dimensions and facts, and those need the `sv_*` source views. Globbing the whole folder
# here pulled them into the SEED notebook, which has no source views, and the run failed
# with no obvious cause. Prefixes carry meaning (see 00-platform/naming-standards.md), so
# they are what selects.
SEED_DIRS = (
    (REPO / "src" / "procore" / "sql", ("20_gold_dim_trade.sql", "21_gold_dim_status.sql")),
    (CHARLEY_DEV / "02-transformation" / "sql" / "gold", "0*.sql"),
)

# Dimensions and facts, built after the seeds and over the sv_* fixtures.
GOLD_GLOB = "[1234]*.sql"

# Spark -> DuckDB. Both are exact 1:1 mappings, which is why one .sql serves both.
MACROS = (
    # Spark builds a date range with explode(sequence(...)); DuckDB spells the same two
    # operations unnest(generate_series(...)).
    "CREATE OR REPLACE MACRO sequence(a, b, c) AS generate_series(a, b, c)",
    "CREATE OR REPLACE MACRO explode(l) AS unnest(l)",
    # Used by dim_Status to read Procore's raw payloads. Same macro src/procore uses.
    "CREATE OR REPLACE MACRO get_json_object(j, p) AS json_extract_string(j, p)",
    # Spark spells regex matching as an infix operator (x RLIKE 'p'); DuckDB has only the
    # function regexp_matches(x, p) and cannot macro an operator. The SQL uses a function
    # form both engines understand, defined here for DuckDB and as a Spark UDF in the gold
    # notebook. Used by dim_CostCodeCrosswalk to find codes that start with a CSI division.
    "CREATE OR REPLACE MACRO rlike_(s, p) AS regexp_matches(COALESCE(s, ''), p)",
    # json_field(payload, 'KEY') - look a key up by NAME rather than by JSON path.
    #
    # Spark's get_json_object uses a simplified JSONPath that silently returns NULL for
    # bracket keys containing '(', ')' or '='. Affect's budget view names its columns
    # "UPDATED PRIME CONTRACT BUDGET (D = A+B+C)", so every money column parsed to NULL and
    # silver produced 0 rows - a failure that looks like "Procore has no budget data".
    #
    # In Fabric this is a map lookup: from_json(payload,'map<string,string>')['KEY'].
    # There is no path grammar involved, so no key name can break it.
    "CREATE OR REPLACE MACRO json_field(j, k) AS json_extract_string(j, '$.\"' || k || '\"')",
    # Spark's datediff(end, start) is 2-arg; DuckDB ships only the 3-arg date_diff(part,
    # start, end). Overloading by arity is allowed, so the Spark spelling works here too.
    "CREATE OR REPLACE MACRO datediff(e, s) AS date_diff('day', CAST(s AS DATE), CAST(e AS DATE))",
)

# Fixtures standing in for sql/silver/00_source_views.sql.
#
# That file is Spark-only (backticks + abfss paths), so offline runs recreate the same
# `sv_*` views from literals instead. The COLUMN NAMES here must match the view definitions
# exactly - that is the contract the gold SQL is written against, and the reason the gold
# files are quote-free and run unchanged on both engines.
#
# Values deliberately exercise the edge cases the gold SQL handles: a project with no prime
# contract, a vendor with no Sage match, a cost code that does not parse into a division,
# an AR invoice whose job does not resolve, a responded vs still-open submittal, a
# non-critical activity that must be excluded, and a milestone with inverted dates.
SOURCE_FIXTURES = (
    """CREATE OR REPLACE VIEW sv_projects AS SELECT * FROM (VALUES
        ('P1', 'Tower A', 'S100', 'PROCORE'),
        ('P2', 'Depot B', NULL,   'PROCORE')
    ) AS t(project_id, project_name, sage_project_id, origin_code)""",

    # 8,800,000 is FINANCIALS!C3 verbatim. Combined with the approved change order below,
    # this reproduces the workbook's own Current Contract (9,116,960.48) and Contract
    # Growth (3.60%) - two values from the reconciliation gate in
    # powerbi/build-plan.md:142-158. The fixture is faithful to the real project so the
    # offline suite checks the numbers Affect will actually look at.
    """CREATE OR REPLACE VIEW sv_prime_contracts AS SELECT * FROM (VALUES
        ('C1', 'P1', 8800000.0, 0.10, DATE '2025-01-01', DATE '2026-06-30', 'Approved')
    ) AS t(prime_contract_id, project_id, contract_value, retainage_pct,
           start_date, estimated_completion_date, status)""",

    """CREATE OR REPLACE VIEW sv_vendors AS SELECT * FROM (VALUES
        ('V1', 'SV1', '  Acme Concrete  '),
        ('V2', NULL,  'Bright Electric')
    ) AS t(procore_vendor_id, sage_vendor_id, vendor_name)""",

    # The REAL Procore shape, verified against Affect's tenant: "01-00-00 - GENERAL
    # REQUIREMENTS". CC2 deliberately does not follow it, so the unparseable path is
    # exercised rather than assumed.
    # Procore returns the CODE and the NAME as separate fields. Parsing a division out of
    # the name is meaningless - "Concrete" has no division in it - so the code is carried
    # separately. CC2 has no parseable code, exercising that path.
    """CREATE OR REPLACE VIEW sv_cost_codes AS SELECT * FROM (VALUES
        ('CC1', '03-100', 'Concrete'),
        ('CC2', 'General', 'General')
    ) AS t(cost_code_id, cost_code, cost_code_name)""",

    """CREATE OR REPLACE VIEW sv_budgets AS SELECT * FROM (VALUES
        ('P1','CC1','03-100','Materials', DATE '2025-05-01',
         1000000.0, 50000.0, 1050000.0, 1100000.0, 900000.0, 400000.0, 350000.0, 550000.0),
        ('P1','CC2','General','Labor',    DATE '2025-05-01',
          500000.0,      0.0,  500000.0,  500000.0, 480000.0, 200000.0, 150000.0, 330000.0)
    ) AS t(project_id, cost_code_id, cost_code, category, snapshot_date,
           original_budget, budget_modifications, updated_budget, forecast_budget,
           committed_to_date, direct_costs, invoiced_to_date, cost_to_complete)""",

    # The approved CO is the workbook's own contract growth (9,116,960.48 - 8,800,000).
    # The two unapproved ones are real addends from FINANCIALS!C5, which the workbook
    # stores as the formula "=65000+3158.46+11550+4620" typed into a value cell - the
    # components exist nowhere else once someone edits it. Here each is a row.
    """CREATE OR REPLACE VIEW sv_prime_change_orders AS SELECT * FROM (VALUES
        ('P1','CO1','C1', DATE '2025-05-02', 316960.48, '1', 'Approved'),
        ('P1','CO2','C1', DATE '2025-05-10',   3158.46, '2', 'Pending'),
        ('P1','CO3','C1', DATE '2025-05-20',  11550.0,  '3', 'Draft')
    ) AS t(project_id, change_order_id, contract_id, created_date, amount, co_number, status)""",

    """CREATE OR REPLACE VIEW sv_ar_invoices AS SELECT * FROM (VALUES
        ('S100', DATE '2025-05-05', DATE '2025-06-04', 'App 1', 500000.0, 500000.0,      0.0, '5'),
        ('S100', DATE '2025-05-25', DATE '2025-06-24', 'App 2', 300000.0,      0.0, 300000.0, '5'),
        ('S999', DATE '2025-05-05', DATE '2025-06-04', 'Orphan', 1000.0,       0.0,   1000.0, '5')
    ) AS t(sage_project_id, invoice_date, due_date, description,
           invoice_total, amount_paid, invoice_balance, billing_period)""",

    """CREATE OR REPLACE VIEW sv_submittals AS SELECT * FROM (VALUES
        ('P1','SB1','001','Rebar shop drawings','Open',    'CC1', DATE '2025-05-01', DATE '2025-05-20', NULL),
        ('P1','SB2','002','Concrete mix design','Approved','CC1', DATE '2025-04-01', DATE '2025-04-20', DATE '2025-04-15'),
        ('P1','SB3','003','No cost code',        'Open',    NULL,  DATE '2025-05-03', DATE '2099-01-01', NULL)
    ) AS t(project_id, item_id, item_number, subject, status_label, cost_code_id,
           created_date, due_date, responded_date)""",

    # RFIs are the second arm of fct_RfiSubmittal. Fixtures mirror the submittal shapes -
    # one open, one answered - plus the priority column that only RFIs carry, so the union
    # is exercised on both arms rather than only on the one that existed first.
    """CREATE OR REPLACE VIEW sv_rfis AS SELECT * FROM (VALUES
        ('P1','R1','RFI-1','Slab edge detail','Open',  'High',  'CC1', DATE '2025-05-03', DATE '2025-05-17', NULL),
        ('P1','R2','RFI-2','Closed one',      'Closed','Normal', NULL, DATE '2025-04-01', DATE '2025-04-20', DATE '2025-04-10')
    ) AS t(project_id, item_id, item_number, subject, status_label, priority, cost_code_id,
           created_date, due_date, responded_date)""",

    # Crosswalk fixtures. P1 is in all three systems, P2 is Procore-only (the dangerous
    # case - it reads as zero revenue everywhere without erroring), P3 maps to TWO Sage
    # projects, which is a data problem the crosswalk must surface rather than resolve.
    """CREATE OR REPLACE VIEW sv_project_crosswalk AS SELECT * FROM (VALUES
        ('P1', 'S100', 'Tower A'),
        ('P3', 'S300', 'Ambiguous'),
        ('P3', 'S301', 'Ambiguous')
    ) AS t(procore_project_id, sage_project_id, project_name)""",

    """CREATE OR REPLACE VIEW sv_outbuild_projects AS SELECT * FROM (VALUES
        ('OB1', 'P1'),
        ('OB9', NULL)
    ) AS t(outbuild_project_id, procore_project_id)""",

    """CREATE OR REPLACE VIEW sv_sage_vendors AS SELECT * FROM (VALUES
        ('SV1', 'ACME CONCRETE LLC')
    ) AS t(sage_vendor_id, sage_vendor_name)""",

    # Field ops. Values exercise the paths that matter: one open and past due, one closed
    # (so IsPastDue must be FALSE even though its due date has gone), and a punch item with
    # no cost code.
    """CREATE OR REPLACE VIEW sv_observations AS SELECT * FROM (VALUES
        ('P1','OB1','1','Site walk finding','Safety','OPEN','High','Concrete','Alex R',
         DATE '2025-05-01', DATE '2025-05-10', NULL),
        ('P1','OB2','2','Closed finding',    'Quality','CLOSED','Normal','Metals','Sam T',
         DATE '2025-04-01', DATE '2025-04-05', DATE '2025-04-04')
    ) AS t(project_id, observation_id, observation_number, title, observation_type,
           status_label, priority, trade, assignee_name, created_date, due_date, closed_date)""",

    """CREATE OR REPLACE VIEW sv_punch_items AS SELECT * FROM (VALUES
        ('P1','PI1','1','Fix grid','Punch','OPEN','High','Concrete','Pat M','CC1',
         DATE '2025-05-02', DATE '2025-05-09', NULL),
        ('P1','PI2','2','No cost code','Punch','CLOSED','Low','Metals','Pat M',NULL,
         DATE '2025-04-02', DATE '2025-04-08', DATE '2025-04-07')
    ) AS t(project_id, punch_item_id, punch_item_number, title, punch_item_type,
           status_label, priority, trade, manager_name, cost_code_id,
           created_date, due_date, closed_date)""",

    """CREATE OR REPLACE VIEW sv_manpower_daily AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 800.0, 100.0),
        ('P1', DATE '2025-05-02', 200.0,  25.0)
    ) AS t(project_id, log_date, total_hours, total_workers)""",

    # P2 has an incident and NO manpower log - the case the FULL OUTER JOIN preserves and
    # an inner join would silently drop.
    """CREATE OR REPLACE VIEW sv_incidents AS SELECT * FROM (VALUES
        ('P1','I1','Cut hand','CLOSED', TRUE,  DATE '2025-05-10'),
        ('P1','I2','Near miss','CLOSED', FALSE, DATE '2025-05-12'),
        ('P2','I3','Orphan month','OPEN', TRUE, DATE '2025-05-20')
    ) AS t(project_id, incident_id, title, status_label, is_recordable, event_date)""",

    """CREATE OR REPLACE VIEW sv_outbuild_activities AS SELECT * FROM (VALUES
        ('P1','A1','Foundation complete', DATE '2025-05-01', DATE '2025-06-30', 0.5, 60.0, TRUE,  'Task','In Progress'),
        ('P1','A2','Non-critical task',   DATE '2025-05-01', DATE '2025-06-30', 0.2, 60.0, FALSE, 'Task','In Progress'),
        ('P1','A3','Inverted dates',      DATE '2025-07-01', DATE '2025-06-01', 0.0, 10.0, TRUE,  'Task','Not Started')
    ) AS t(project_id, activity_id, activity_name, start_date, end_date,
           progress, duration, is_critical, activity_type, status)""",
)

# dim_Status is not a pure seed: it unions its 32 static rows with Procore's OWN status
# vocabulary, read from bronze. Empty stubs let the static block be verified standalone -
# which is also exactly the shape of a first run, before any Procore data has landed.
#
# The populated path is already covered by src/procore/tests/test_pipeline.py against
# fixtures; duplicating that here would test the same SQL twice.
UPSTREAM_STUBS = (
    "CREATE OR REPLACE TABLE bronze_procore_rfi_statuses (payload VARCHAR)",
    "CREATE OR REPLACE TABLE silver_rfi_submittal (ItemType VARCHAR, StatusLabel VARCHAR)",
)


def seed_files() -> list[Path]:
    """Every seed file, in the order the pipeline runs them."""
    files: list[Path] = []
    for directory, selector in SEED_DIRS:
        if isinstance(selector, str):
            found = sorted(directory.glob(selector))
        else:
            found = [p for p in sorted(directory.glob("*.sql")) if p.name in selector]
            missing = set(selector) - {p.name for p in found}
            if missing:
                raise FileNotFoundError(
                    f"expected seed(s) not found in {directory}: {sorted(missing)}"
                )
        if not found:
            raise FileNotFoundError(f"no files matched {selector!r} in {directory}")
        files.extend(found)
    return files


def gold_files() -> list[Path]:
    """Dimension and fact files, which depend on the sv_* source views."""
    return sorted((CHARLEY_DEV / "02-transformation" / "sql" / "gold").glob(GOLD_GLOB))


def split_statements(sql: str) -> list[str]:
    """Split a .sql file into statements, stripping comments first.

    A `;` inside a `--` comment is otherwise read as a statement boundary and tears the
    statement in half. Same approach as procore_extract.split_sql_statements.
    """
    body = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return [s.strip() for s in body.split(";") if s.strip()]


def build(verbose: bool = False) -> Any:
    """Create an in-memory database with every seed table built."""
    import duckdb

    con = duckdb.connect()
    for statement in (*MACROS, *UPSTREAM_STUBS, *SOURCE_FIXTURES):
        con.execute(statement)

    # Seeds first, then dimensions and facts - the same order the pipeline runs, and the
    # order the facts' foreign keys require.
    for path in [*seed_files(), *gold_files()]:
        for statement in split_statements(path.read_text(encoding="utf-8")):
            try:
                con.execute(statement)
            except Exception as exc:  # noqa: BLE001 - which file failed is the useful part
                raise RuntimeError(f"{path.name}: {exc}") from exc
        if verbose:
            print(f"  ran {path.name}")
    return con


def table_names(con: Any) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()]


def main() -> int:
    con = build(verbose=True)
    print()
    for name in table_names(con):
        count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        print(f"  {name:<26} {count:>6} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
