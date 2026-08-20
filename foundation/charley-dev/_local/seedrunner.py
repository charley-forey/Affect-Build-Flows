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
    # NO trunc() MACRO, deliberately. Spark spells month-flooring trunc(date, 'MM') and the
    # obvious bridge is a 2-arg macro - but unlike datediff, DuckDB does NOT overload it by
    # arity: the macro REPLACES the builtin trunc(), which DuckDB's own date functions call
    # internally, and 00_dim_date.sql stops building with a binder error pointing at a
    # statement that never mentions trunc.
    #
    # The manual parsers use date_trunc('MONTH', d) instead, which both engines have with
    # the same argument order, so no macro is needed. Some Spark spellings are cheaper to
    # avoid than to bridge.
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
    # sage_project_id is NULL on BOTH rows because that is what production does:
    # 01_source_views_cd.sql:43 hardcodes CAST(NULL AS STRING) - the Procore project record
    # carries no Sage id. This fixture used to supply 'S100' here, which made the offline
    # suite exercise a path that cannot exist live and hid a dead Sage join for weeks.
    # The Sage id must reach dim_Project via sv_project_crosswalk. Do not repopulate this.
    """CREATE OR REPLACE VIEW sv_projects AS SELECT * FROM (VALUES
        ('P1', 'Tower A', NULL, 'PROCORE'),
        ('P2', 'Depot B', NULL, 'PROCORE')
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
        ('P1','CO3','C1', DATE '2025-05-20',  11550.0,  '3', 'Draft'),
        -- A SECOND MONTH, deliberately. Every CO used to sit in May, which made per-month
        -- and cumulative roll-ups identical and let a $4.85M understatement pass the gate
        -- (see 30_fct_financialperiod.sql). June's row must carry May's approved CO too.
        ('P1','CO4','C1', DATE '2025-06-11', 100000.0,  '4', 'Approved')
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

    # Commitments. V1 has BOTH a direct cost and a subcontract against CC1 - the case
    # that must produce two rows (actual, committed) and never one summed row.
    """CREATE OR REPLACE VIEW sv_commitments AS SELECT * FROM (VALUES
        ('Subcontract','P1','SC1','SC-1','HVAC','APPROVED','V1','Demar Plumbing',
         390000.0, 30485.0, 30485.0, TRUE),
        ('Purchase Order','P1','PO1','PO-1','Equipment','APPROVED','V3','Daikin',
         28000.0, 0.0, 0.0, TRUE)
    ) AS t(commitment_type, project_id, commitment_id, commitment_number, title,
           status_label, vendor_id, vendor_name, grand_total, total_payments,
           total_requisitioned, is_executed)""",

    """CREATE OR REPLACE VIEW sv_commitment_lines AS SELECT * FROM (VALUES
        ('P1','CL1','SC1','WorkOrderContract','WorkOrderContract','CC1','03-100',
         '03-100 - CONCRETE','HVAC','Material', 390000.0, 390000.0, 0.0, 0.0),
        ('P1','CL2','PO1','PurchaseOrderContract','PurchaseOrderContract','CC2','06-100',
         '06-100 - CARPENTRY','Equipment','Material', 28000.0, 28000.0, 1.0, 28000.0),
        -- A work order LINE pointing at a purchase order id. Different id spaces can
        -- collide, and joining without checking holder_type attaches this to the wrong
        -- contract - and so to the wrong vendor.
        ('P1','CL3','PO1','WorkOrderContract','WorkOrderContract','CC1','03-100',
         '03-100 - CONCRETE','Mismatched','Material', 7777.0, 7777.0, 0.0, 0.0)
    ) AS t(project_id, line_item_id, commitment_id, holder_type, source_endpoint,
           cost_code_id, cost_code, cost_code_name, description, line_item_type,
           amount, total_amount, quantity, unit_cost)""",

    # The vendor <-> cost-code bridge. D1 belongs to vendor V1 (see sv_direct_costs), so
    # two lines against CC1 must roll into ONE bridge row, and the Commitment::Item line
    # must not be attributed to V1 at all.
    """CREATE OR REPLACE VIEW sv_direct_cost_lines AS SELECT * FROM (VALUES
        ('P1','L1','D1','DirectCost::Item','CC1','03-100','03-100 - CONCRETE',
         'Slab pour','Material', 1000.0, 1100.0, 1.0, 1000.0, 'ls'),
        ('P1','L2','D1','DirectCost::Item','CC1','03-100','03-100 - CONCRETE',
         'Slab pour 2','Material', 500.0, 500.0, 1.0, 500.0, 'ls'),
        ('P1','L4','D2','DirectCost::Item','CC2','06-100','06-100 - CARPENTRY',
         'Lumber','Material', 2000.0, 2100.0, 1.0, 2000.0, 'ls'),
        ('P1','L3','D1','Commitment::Item','CC1','03-100','03-100 - CONCRETE',
         'Not a direct cost','Material', 9999.0, 9999.0, 1.0, 9999.0, 'ls')
    ) AS t(project_id, line_item_id, direct_cost_id, holder_type, cost_code_id, cost_code,
           cost_code_name, description, line_item_type, amount, total_amount, quantity,
           unit_cost, unit_of_measure)""",

    # Insurance: one lapsed, one current, one exempt. The three states that must not
    # collapse into a single "compliant" flag.
    """CREATE OR REPLACE VIEW sv_vendor_insurance AS SELECT * FROM (VALUES
        ('I1','V1','GL','Farm Family','PN-1','NON_COMPLIANT',
         DATE '2022-08-26', DATE '2023-08-26', 24.0, FALSE, TRUE, TRUE, NULL),
        ('I2','V2','Auto','Acme Ins','PN-2','COMPLIANT',
         DATE '2024-01-01', DATE '2032-01-01', 1000000.0, FALSE, TRUE, TRUE, NULL),
        ('I3','V2','Umbrella','Acme Ins',NULL,'COMPLIANT',
         DATE '2024-01-01', DATE '2032-01-01', 5000000.0, TRUE, TRUE, FALSE, NULL)
    ) AS t(insurance_id, vendor_id, insurance_type, provider, policy_number, status_label,
           effective_date, expiration_date, coverage_limit_raw, is_exempt, info_received,
           additional_insured, notes)""",

    # Billing. Built to exercise the cumulative trap: B1..B3 are one owner contract whose
    # retainage BALANCE grows each period, so summing the column multiplies the money. B2
    # and B3 deliberately share a period_end - real data has three periods ending
    # 2026-07-31 - so the tie must break on period_number or the winner is arbitrary.
    """CREATE OR REPLACE VIEW sv_billing AS SELECT * FROM (VALUES
        ('Owner','P1','B1','1',1,'APPROVED',NULL,'Client','C1','Prime','PrimeContract',
         DATE '2025-05-31', DATE '2025-05-01', DATE '2025-05-31', NULL, 25.0,
         1000000.0, 0.0, 1000000.0, 250000.0, 0.0, 12500.0, 5.0, 0.0, 12500.0,
         237500.0, 237500.0, 762500.0),
        ('Owner','P1','B2','2',2,'APPROVED',NULL,'Client','C1','Prime','PrimeContract',
         DATE '2025-06-30', DATE '2025-06-01', DATE '2025-06-30', NULL, 50.0,
         1000000.0, 0.0, 1000000.0, 500000.0, 237500.0, 25000.0, 5.0, 0.0, 25000.0,
         475000.0, 237500.0, 525000.0),
        ('Owner','P1','B3','3',3,'APPROVED',NULL,'Client','C1','Prime','PrimeContract',
         DATE '2025-06-30', DATE '2025-06-01', DATE '2025-06-30', NULL, 60.0,
         1000000.0, 0.0, 1000000.0, 600000.0, 475000.0, 30000.0, 5.0, 0.0, 30000.0,
         570000.0, 95000.0, 430000.0),
        ('Owner','P1','B4','4',4,'DRAFT',NULL,'Client','C1','Prime','PrimeContract',
         DATE '2025-07-31', DATE '2025-07-01', DATE '2025-07-31', NULL, 70.0,
         1000000.0, 0.0, 1000000.0, 700000.0, 570000.0, 99999.0, 5.0, 0.0, 99999.0,
         600001.0, 30001.0, 300000.0),
        ('Subcontractor','P1','B5','1',1,'APPROVED','V1','Demar','C1','SC-1',
         'WorkOrderContract', DATE '2025-05-31', DATE '2025-05-01', DATE '2025-05-31',
         NULL, 10.0, 390000.0, 0.0, 390000.0, 36185.0, 0.0, 4000.0, 5.0, 0.0, 4000.0,
         32185.0, 32185.0, 353815.0),
        ('Subcontractor','P2','B6','1',1,'DRAFT','V2','Orphan','C9','SC-9',
         'WorkOrderContract', DATE '2025-05-31', DATE '2025-05-01', DATE '2025-05-31',
         NULL, 5.0, 100000.0, 0.0, 100000.0, 5000.0, 0.0, 7777.0, 5.0, 0.0, 7777.0,
         0.0, 0.0, 95000.0)
    ) AS t(billing_type, project_id, billing_id, invoice_number, period_number,
           status_label, vendor_id, counterparty_name, contract_id, contract_name,
           contract_type, billing_date, period_start, period_end, payment_date,
           percent_complete, original_contract_sum, net_change_by_change_orders,
           contract_sum_to_date, completed_to_date, previous_certificates,
           retainage_amount, retainage_percent, stored_retainage_amount, total_retainage,
           earned_less_retainage, current_payment_due, balance_to_finish)""",

    """CREATE OR REPLACE VIEW sv_direct_costs AS SELECT * FROM (VALUES
        ('P1','D1','PM Payroll','payroll','APPROVED','V1','Affect','A Foreman',
         DATE '2025-05-31', 11275.5, 11400.0),
        ('P1','D2','Lumber','expense','APPROVED','V2','Supplier',NULL,
         DATE '2025-05-15', 2000.0, 2100.0),
        ('P1','D3','Unapproved spend','expense','PENDING','V2','Supplier',NULL,
         DATE '2025-05-20', 500.0, 500.0)
    ) AS t(project_id, direct_cost_id, description, cost_type, status_label,
           vendor_id, vendor_name, employee_name, cost_date, amount, grand_total)""",

    """CREATE OR REPLACE VIEW sv_project_vendors AS SELECT * FROM (VALUES
        ('P1','V1','Demar Plumbing','Demar LLC','New York','NY','212','a@b.com',
         TRUE, TRUE, FALSE, NULL, NULL, TRUE),
        ('P1','V2','Supplier Co',NULL,'Queens','NY',NULL,NULL,
         FALSE, TRUE, FALSE, NULL, NULL, FALSE)
    ) AS t(project_id, vendor_id, vendor_name, trade_name, city, state_code,
           business_phone, email_address, is_prequalified, is_active, is_union_member,
           license_number, labor_union, synced_to_erp)""",

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

    # ----------------------------------------------------------------------
    # MANUAL INPUT. One row each, and that is the point: before these existed the gold
    # man_* tables had no source at all, so "the manual pipeline works" was a claim with
    # nothing behind it. A single row per table is enough to prove the join exists, which
    # is the thing that was broken.
    #
    # P9 appears in sv_man_wins and NOWHERE in dim_Project. Silver is what rejects unknown
    # projects, and silver is not exercised here - so this row is the one that would reach
    # gold if that rejection were ever removed, and test_gold's referential check is what
    # notices.
    # ----------------------------------------------------------------------
    """CREATE OR REPLACE VIEW sv_man_wins AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 1, 'Topped out two weeks early', 'REALIZED'),
        ('P1', DATE '2025-05-01', 2, 'Zero recordables this quarter', 'FOCUSAREA')
    ) AS t(project_id, month_start, win_number, description, win_type)""",

    """CREATE OR REPLACE VIEW sv_man_risks AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 1, 'Curtain wall lead time', 'HIGH',
         'Expedite fabrication; weekly vendor call', 'PM', 'IN_PROGRESS')
    ) AS t(project_id, month_start, risk_number, description, impact_code, mitigation,
           owner_role, status_code)""",

    """CREATE OR REPLACE VIEW sv_man_priority_items AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 1, 'Level 3 slab pour', 'AT_RISK',
         'Concrete delivery delayed 3 days', 'Saturday pour', 'No impact to SC',
         CAST(NULL AS VARCHAR))
    ) AS t(project_id, month_start, item_number, schedule_item, status_code,
           critical_delays, recovery_plan, forecast_impact, notes)""",

    # ProfitabilityCode is a LABEL, not a code - it matches dim_ScorecardBand[MatchValue].
    # The fixture carries the label so a regression that upper-cases it fails here.
    """CREATE OR REPLACE VIEW sv_man_flags AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 'Within Range', 125000.0, TRUE, 'Rev 3',
         TRUE, TRUE, FALSE)
    ) AS t(project_id, month_start, profitability_code, contingency_remaining,
           baseline_approved, baseline_revision, month_end_closed_out,
           forecasting_in_line, resources_updated)""",

    """CREATE OR REPLACE VIEW sv_man_survey AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 1, 'How satisfied are you with communication?', 4,
         'ANONYMOUS')
    ) AS t(project_id, month_start, question_number, question_text, score,
           surveyed_party)""",

    """CREATE OR REPLACE VIEW sv_man_safety_monthly AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 12500.0, 0, 18, 310.5)
    ) AS t(project_id, month_start, hours_worked, recordable_incidents, orientations,
           ot_hours)""",

    """CREATE OR REPLACE VIEW sv_man_quality_monthly AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 42, 17, 3.5, 9.2)
    ) AS t(project_id, month_start, observations, punchlist_items, avg_days_past_due,
           avg_days_to_close)""",

    # A SPAN, not a date. The parser used to produce four single dates, which gold could
    # not fill - the fixture is the pair so a regression to the old shape fails here.
    """CREATE OR REPLACE VIEW sv_man_milestones AS SELECT * FROM (VALUES
        ('P1', 'A1', 'Substantial Completion', DATE '2026-03-01', DATE '2026-03-31',
         DATE '2026-03-01', DATE '2026-03-31', TRUE)
    ) AS t(project_id, activity_key, milestone_name, contract_start, contract_finish,
           baseline_start, baseline_finish, is_substantial_completion)""",

    """CREATE OR REPLACE VIEW sv_man_daily_log_compliance AS SELECT * FROM (VALUES
        ('P1', DATE '2025-05-01', 22, 3)
    ) AS t(project_id, month_start, logs_expected, logs_missed_same_day)""",

    # The job register, off the BUILD site. No project_id: a job is registered before
    # anybody knows whether it will be won, and most never become Procore projects.
    #
    # Rows 2 and 3 are two different jobs both issued 26-002 - the collision a race between
    # two Power Automate runs produces. They are here deliberately so dim_Job carries a
    # duplicate and the DQ expectation over it has something real to be exercised against.
    """CREATE OR REPLACE VIEW sv_man_job_register AS SELECT * FROM (VALUES
        (1, 'Fulton Street Fit-Out', 26, 1, '26-001', 'ESTIMATING',
         '/sites/BUILD/01 ESTIMATING/E-26-001-Fulton Street Fit-Out',
         CAST(NULL AS VARCHAR), 'pm@example.com', TIMESTAMP '2026-07-01 09:00:00',
         TIMESTAMP '2026-07-01 09:01:00', 'Copied 12 item(s)', CAST(NULL AS VARCHAR),
         TIMESTAMP '2026-07-01 09:01:00', 'flow:EstimatingSetup'),
        (2, 'Bergen Street Retail', 26, 2, '26-002', 'BIDDING',
         '/sites/BUILD/01 ESTIMATING/E-26-002-Bergen Street Retail',
         '/sites/BUILD/00 PROJECTS/26-002-Bergen Street Retail', 'pm@example.com',
         TIMESTAMP '2026-07-02 09:00:00', TIMESTAMP '2026-07-02 09:02:00',
         'Copied 31 item(s)', NULL, TIMESTAMP '2026-07-02 09:02:00', 'flow:ConvertToBidding'),
        (3, 'Court Square Lobby', 26, 2, '26-002', 'ESTIMATING',
         '/sites/BUILD/01 ESTIMATING/E-26-002-Court Square Lobby', NULL, 'pm2@example.com',
         TIMESTAMP '2026-07-02 09:00:01', TIMESTAMP '2026-07-02 09:00:09',
         'Copied 12 item(s)', NULL, TIMESTAMP '2026-07-02 09:00:09', 'flow:EstimatingSetup')
    ) AS t(register_id, project_name, job_year, job_seq, job_number, stage,
           estimating_folder_url, project_folder_url, requested_by, requested_at,
           completed_at, copy_job_status, error_detail, last_modified, last_modified_by)""",

    # ----------------------------------------------------------------------
    # PQP - Procore half. Values exercise the mapping, not the happy path: OB1's trade
    # 'Concrete Formwork' resolves to a qc_seed_Trade key, OB2's 'Metals' does not (there
    # is no METALS trade in the 26), so HasUnmappedTrade must be TRUE on exactly one row.
    # ----------------------------------------------------------------------
    """CREATE OR REPLACE VIEW sv_qc_ncr AS SELECT * FROM (VALUES
        ('P1','OB1','1','Rebar cover short','Cover below spec at grid C4',
         'Non-Conformance','Structural','Concrete Formwork','Alex R','High',
         'OPEN','OPEN','NCR', DATE '2025-05-01', DATE '2025-05-10', CAST(NULL AS DATE)),
        ('P1','OB2','2','Closed finding','Corrected on the day','Corrective Action',
         'Quality','Metals','Sam T','Normal','CLOSED','CLOSED','COR',
         DATE '2025-04-01', DATE '2025-04-05', DATE '2025-04-04'),
        -- OB3 resolves ONLY through qc_seed_TradeAlias: Procore says 'HVAC', the workbook
        -- key is HVAC_DUCTWORK, and no amount of normalising the label gets from one to
        -- the other. Without this row the suite passes whether the alias join works or
        -- not, which is exactly how a broken alias reached the lakehouse once already.
        ('P1','OB3','3','Duct hanger spacing','Hangers over-spaced in corridor',
         'Non-Conformance','Mechanical','HVAC','Jo N','Normal',
         'OPEN','OPEN','NCR', DATE '2025-05-03', DATE '2025-05-12', CAST(NULL AS DATE))
    ) AS t(project_id, ncr_id, ncr_number, title, description, observation_type, category,
           trade, assignee_name, priority, source_status, status_code, item_class_code,
           created_date, due_date, closed_date)""",

    """CREATE OR REPLACE VIEW sv_qc_punch AS SELECT * FROM (VALUES
        ('P1','PI1','1','Fix grid','Punch','Concrete Formwork','Pat M','CC1','High',
         'INITIATED','OPEN','PUNCH_ITEM', DATE '2025-05-02', DATE '2025-05-09',
         CAST(NULL AS DATE)),
        ('P1','PI2','2','Day 2 work','Day 2 Work','Metals','Pat M',CAST(NULL AS VARCHAR),
         'Low','CLOSED','CLOSED','DAY_2_WORK', DATE '2025-04-02', DATE '2025-04-08',
         DATE '2025-04-07')
    ) AS t(project_id, punch_id, punch_number, title, punch_item_type, trade,
           manager_name, cost_code_id, priority, source_status, status_code,
           item_class_code, created_date, due_date, closed_date)""",

    # SB3 is UNMAPPED on purpose: 'Under Review' is not a value 24_qc_procore_silver.sql
    # maps, so status_code is NULL. The DQ suite counts those rather than the pipeline
    # bucketing them into whatever an ELSE branch said.
    """CREATE OR REPLACE VIEW sv_qc_submittal AS SELECT * FROM (VALUES
        ('P1','SB1','001','Rebar shop drawings','CC1','Open','OPEN','SHOP_DRAWING',
         DATE '2025-05-01', DATE '2025-05-20', CAST(NULL AS DATE)),
        ('P1','SB2','002','Lobby stone mockup','CC1','Approved','APPROVED','MOCK_UP',
         DATE '2025-04-01', DATE '2025-04-20', DATE '2025-04-15'),
        ('P1','SB3','003','Unmapped status',CAST(NULL AS VARCHAR),'Under Review',
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR),
         DATE '2025-05-03', DATE '2025-05-17', CAST(NULL AS DATE))
    ) AS t(project_id, submittal_id, submittal_number, subject, cost_code_id,
           source_status, status_code, submittal_type_code, created_date, due_date,
           responded_date)""",

    # Not read by any gold file yet - landed and typed so the "could Procore Inspections
    # replace the 26 checklist sheets" question can be answered against real data rather
    # than argued about. Declared here so the view contract is verified either way.
    """CREATE OR REPLACE VIEW sv_qc_inspection AS SELECT * FROM (VALUES
        ('P1','IN1','1','Slab pour pre-check','Quality','Concrete Pre-Pour',
         'Concrete Formwork','J. Alvarez','CLOSED', DATE '2025-05-08',
         DATE '2025-05-08', 100.0)
    ) AS t(project_id, inspection_id, inspection_number, name, inspection_type,
           template_name, trade, inspector_name, source_status, inspection_date,
           due_date, percent_complete)""",

    # ----------------------------------------------------------------------
    # PQP - SharePoint half. Keys are REAL values from the seed CSVs (EXCAVATION-001,
    # TCO-A2, H-01, D-07), so the referential checks in test_qc.py test the join rather
    # than testing that two invented strings match each other.
    # ----------------------------------------------------------------------
    """CREATE OR REPLACE VIEW sv_man_qc_dfow AS SELECT * FROM (VALUES
        ('P1','D-07','Cast-in-place concrete frame','CONCRETE_FORMWORK',3,
         'Pre-pour checklist and third-party survey','Superintendent','IN_PROGRESS',
         CAST(NULL AS VARCHAR)),
        ('P1','D-08','Bulk excavation','EXCAVATION',3,'Daily survey','Superintendent',
         'COMPLETE', CAST(NULL AS VARCHAR))
    ) AS t(project_id, dfow_ref, dfow_description, trade_key, risk_tier, control_measure,
           owner_role, status_code, notes)""",

    """CREATE OR REPLACE VIEW sv_man_qc_itp AS SELECT * FROM (VALUES
        ('P1','ITP-014','CONCRETE_FORMWORK','Slab on grade pour',
         'Compressive strength test','28-day break >= 4000 psi','Hold','QA Manager',
         DATE '2025-05-14', DATE '2025-05-14','PASS','COMPLETE', CAST(NULL AS VARCHAR))
    ) AS t(project_id, itp_ref, trade_key, activity, inspection_type, acceptance_criteria,
           hold_point_type, responsible, planned_date, actual_date, result_code,
           status_code, notes)""",

    # One gate of each type, which is the collapse under test: three sheets, one table.
    # STAT-1 has a target date AFTER its completed date - workbook defect #6's shape, and
    # what the date_order expectation is there to catch.
    """CREATE OR REPLACE VIEW sv_man_qc_gate AS SELECT * FROM (VALUES
        ('P1','TCO-A2','TCO','SUBMITTED','I. Aguire (PM)', DATE '2025-09-01',
         DATE '2025-08-20', CAST(NULL AS DATE), CAST(NULL AS VARCHAR),
         'Awaiting DOB NOW acceptance'),
        ('P1','FA-01','FIRE_ALARM','NOT_STARTED','MEP Manager', DATE '2025-10-01',
         CAST(NULL AS DATE), CAST(NULL AS DATE), CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR)),
        ('P1','S-01','STATUTORY','CLOSED','QA Manager', DATE '2025-06-01',
         DATE '2025-05-02', DATE '2025-05-20', 'sp://evidence/S-01',
         CAST(NULL AS VARCHAR))
    ) AS t(project_id, gate_key, gate_type, status_code, responsible, target_date,
           submitted_date, completed_date, evidence_link, blocker_note)""",

    """CREATE OR REPLACE VIEW sv_man_qc_special_inspection AS SELECT * FROM (VALUES
        ('P1','SI-006','Structural steel welding','SIA','R. Patel','YES','YES',
         DATE '2025-07-02', DATE '2025-07-02', DATE '2025-07-09','CLOSED',
         CAST(NULL AS VARCHAR))
    ) AS t(project_id, inspection_ref, category, agency, inspector_name, required_code,
           performed_code, scheduled_date, performed_date, report_received_date,
           status_code, notes)""",

    """CREATE OR REPLACE VIEW sv_man_qc_commissioning AS SELECT * FROM (VALUES
        ('P1','CX-003','Smoke purge fans','HVAC_DUCTWORK','MEP Manager',
         DATE '2025-10-01', CAST(NULL AS DATE),'NOT_STARTED', CAST(NULL AS VARCHAR))
    ) AS t(project_id, system_ref, system_name, trade_key, responsible, planned_date,
           actual_date, status_code, notes)""",

    """CREATE OR REPLACE VIEW sv_man_qc_inspector_sign_in AS SELECT * FROM (VALUES
        ('P1','SI-2025-041', DATE '2025-07-16','T. Nguyen','NYC_DOB',
         'Facade progress inspection','Levels 4-6','OBSERVATION_ONLY', FALSE,
         CAST(NULL AS VARCHAR))
    ) AS t(project_id, sign_in_ref, visit_date, inspector_name, agency_code, purpose,
           area_inspected, outcome_code, follow_up_required, notes)""",

    # Two trades, three items, one FAIL. Enough to prove the 26-sheets-into-one collapse
    # holds: two different TradeKeys land in the same table and both resolve.
    """CREATE OR REPLACE VIEW sv_man_qc_checklist_result AS SELECT * FROM (VALUES
        ('P1','EXCAVATION','EXCAVATION-001','1_PREPARATORY','PASS', DATE '2025-05-08',
         'J. Alvarez', CAST(NULL AS VARCHAR)),
        ('P1','EXCAVATION','EXCAVATION-002','1_PREPARATORY','FAIL', DATE '2025-05-08',
         'J. Alvarez','Water table not noted'),
        ('P1','CONCRETE_FORMWORK','CONCRETE_FORMWORK-001','2_WORK_READINESS','PASS',
         DATE '2025-05-14','J. Alvarez', CAST(NULL AS VARCHAR))
    ) AS t(project_id, trade_key, item_key, stage_code, result_code, inspected_date,
           inspected_by, notes)""",

    """CREATE OR REPLACE VIEW sv_man_qc_doh_result AS SELECT * FROM (VALUES
        ('P1','H-01','OWNER_DOH_CONSULTANT','VERIFIED', DATE '2025-07-20','QA Manager',
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR)),
        ('P1','H-02','AFFECT_BUILD','OPEN', CAST(NULL AS DATE), CAST(NULL AS VARCHAR),
         CAST(NULL AS VARCHAR), CAST(NULL AS VARCHAR))
    ) AS t(project_id, item_key, responsibility_code, status_code, verified_date,
           verified_by, evidence_link, notes)""",
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
    """Split a .sql file into statements, stripping `--` comments first.

    QUOTE AWARE, and it has to be. The first version split on every `;` and stripped from
    every `--`, which is fine while the SQL contains only identifiers - and silently
    catastrophic the moment a string LITERAL contains one. 08_qc_seeds.sql inlines 943 rows
    of workbook prose; 43 of them contain a semicolon ("Verify anchor bolt layout; check
    template"). Splitting there tears one CREATE TABLE into two invalid halves, and the
    error you get back is a parse failure hundreds of lines from the actual cause.

    THE ONE PLACE THIS LIVES. deploy_seeds / deploy_silver / deploy_gold each had their own
    copy of the naive version; they now import this one, so the seeds that run offline and
    the seeds that run in Fabric are split identically. Three copies of a parser is three
    parsers that drift.

    `''` inside a literal needs no special case: it closes and immediately reopens the
    quote, which leaves the in-quote state exactly where it should be.
    """
    out: list[str] = []
    buf: list[str] = []
    in_quote = False
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        if in_quote:
            buf.append(ch)
            if ch == "'":
                in_quote = False
            i += 1
        elif ch == "'":
            in_quote = True
            buf.append(ch)
            i += 1
        elif ch == "-" and sql.startswith("--", i):
            i = sql.find("\n", i)
            if i == -1:
                break
            buf.append("\n")
            i += 1
        elif ch == ";":
            out.append("".join(buf).strip())
            buf = []
            i += 1
        else:
            buf.append(ch)
            i += 1
    out.append("".join(buf).strip())
    return [s for s in out if s]


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
