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
- `gold/0*` seeds, `gold/1*` dimensions, `gold/2*`–`3*` facts, `gold/4*` the empty `man_*`
  tables.

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
- **Dates**: submittals contain values before 1582-10-15. Anything before 1990 is floored to
  NULL. Facts outside `dim_Date`'s 2015–2035 range set `HasOutOfRangeDate` rather than
  producing a broken relationship.

## What good looks like

A new gold table ships with its assertions in the matching `_local/tests/test_*.py` in the
same turn. `run_tests.py` currently has 8 suites passing; leaving it green is the deploy gate,
not a nicety.

The DQ suite (`sql/dq/*.sql` → `cd_dq_results`) is the notable gap: the pipeline is designed
to fail a run on a blocking expectation, and `lib/dq.py` already implements the runner with
`SEVERITY_ERROR` / `assert_no_blocking()`. The SQL that feeds it does not exist yet.
