# Role: SQL

You own `foundation/charley-dev/02-transformation/sql/**` and the offline suites that prove
it (`_local/tests/test_seeds.py`, `test_silver.py`, `test_gold.py`).

## What is there

- `silver/00_source_views.sql` — reads Rebecca's existing `Silver_Lakehouse` read-only and
  renames to clean snake_case `sv_*` views. **This is what gold currently uses.**
- `silver/01_source_views_cd.sql` — the same `sv_*` names sourced from our own
  `cd_silver_*`. Written, tested, unused. Flipping `SOURCE_VIEWS` in `deploy_gold.py`
  between these two files is the entire source migration; no gold file changes. That is why
  source naming is isolated in one file instead of spread across nine.
- `silver/10_procore_silver.sql` — 9 statements parsing bronze JSON into 8 typed tables plus
  `cd_dq_rejects`.
- `gold/0*` seeds, `gold/1*` dimensions, `gold/2*`–`3*` facts, `gold/4*` the `man_*` tables —
  **17** of them now (9 original plus 8 for the Project Quality Plan). The silver→gold link
  for `man_*` is written; the tables are empty only because no data has been entered.

## Constraints that are not negotiable

- **Spark SQL is the target**, DuckDB is only the offline proxy. Bare `VARCHAR` is invalid in
  Spark — always `STRING`. `_local/seedrunner.py` carries the compatibility macros; if you
  need a new one, add it there rather than weakening the SQL.
- **The `sv_*` column contract is load-bearing.** `test_silver.py` cross-checks silver's
  actual columns against what `01_source_views_cd.sql` selects. If you change a silver
  column name, that test fails — which is the point. Do not "fix" the test.
- **Dimensions UNION in observed keys from the fact sources.** Referential integrity holds by
  construction rather than by hope, because the real data has orphans: 6 budget lines, 4
  change orders, 9 submittals, 3 milestones and 69 cost codes with no master record. They are
  carried with `IsInCrosswalk` / `IsInSource` flags, not dropped.
- **Rows that fail validation go to `cd_dq_rejects` with a reason.** Never a silent drop —
  silent drops are how the workbook's defects survived for months.
- **Check the client's conventions before writing a data-quality flag.** A flag is a claim
  about the client's data. Three of the four defects fixed 2026-08-19 were ours, not theirs:
  Affect writes CSI divisions 1–9 **without a leading zero** (`1-1000` is Division 01, and
  requiring two digits marked 807 codes unparseable), and Procore sends the submittal status
  `For Record` where the workbook's dropdown says `For Record Only` (223 submittals matched
  no `CASE` branch). Both looked like bad client data and were bad parsing.
- **Dates**: submittals contain values before 1582-10-15. Anything before 1990 is floored to
  NULL. Facts outside `dim_Date`'s 2015–2035 range set `HasOutOfRangeDate` rather than
  producing a broken relationship.

## What good looks like

A new gold table ships with its assertions in the matching `_local/tests/test_*.py` in the
same turn. `run_tests.py` currently has **14** suites passing; leaving it green is the deploy gate,
not a nicety.

The DQ suite (`sql/dq/*.sql` → `cd_dq_results`) is built: **107 expectations, 83 blocking
and 23 warning**, run by `cd_40_dq_checks` through `lib/dq.py` with `SEVERITY_ERROR` /
`assert_no_blocking()`. `cd_dq_results` holds 104 rows. It wrote nothing at all until
2026-08-19 because `_persist_results` used a relative import that fails in the flat
`Files/lib` context and the error was swallowed by a `try`/`except`.
