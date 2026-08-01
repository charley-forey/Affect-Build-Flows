"""Data-quality expectations.

Every expectation is a SQL predicate that returns the *failing* rows. That single choice
is what makes this useful rather than decorative: a failure is not a boolean, it is a set
of rows you can look at.

Results land in `cd_dq_results`; failing rows land in `cd_dq_rejects` with a reason. A
`severity="error"` expectation that fails stops the pipeline, so bad numbers are never
published to a report going to leadership. That is the exact failure mode the Excel had -
defects #2 and #6 survived for months because nothing ever looked.

Self-check: python dq.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"

RESULTS_TABLE = "cd_dq_results"
REJECTS_TABLE = "cd_dq_rejects"


@dataclass(frozen=True)
class Expectation:
    """One check against one table.

    `failing_sql` must select the rows that VIOLATE the rule. Zero rows = pass.
    """

    name: str
    table: str
    failing_sql: str
    severity: str = SEVERITY_ERROR
    description: str = ""

    def __post_init__(self) -> None:
        if self.severity not in (SEVERITY_ERROR, SEVERITY_WARN):
            raise ValueError(f"unknown severity {self.severity!r}")


@dataclass
class Result:
    expectation: Expectation
    failing_rows: int

    @property
    def passed(self) -> bool:
        return self.failing_rows == 0

    @property
    def blocking(self) -> bool:
        return not self.passed and self.expectation.severity == SEVERITY_ERROR


# --------------------------------------------------------------------------
# Expectation builders - the five shapes that cover everything we check
# --------------------------------------------------------------------------


def not_null(table: str, column: str, severity: str = SEVERITY_ERROR) -> Expectation:
    return Expectation(
        name=f"{table}.{column}.not_null",
        table=table,
        failing_sql=f"SELECT * FROM {table} WHERE `{column}` IS NULL",
        severity=severity,
        description=f"{column} must be populated",
    )


def unique_key(table: str, columns: list[str], severity: str = SEVERITY_ERROR) -> Expectation:
    cols = ", ".join(f"`{c}`" for c in columns)
    return Expectation(
        name=f"{table}.{'_'.join(columns)}.unique",
        table=table,
        failing_sql=(
            f"SELECT {cols}, COUNT(*) AS n FROM {table} "
            f"GROUP BY {cols} HAVING COUNT(*) > 1"
        ),
        severity=severity,
        description=f"({', '.join(columns)}) must be unique",
    )


def referential(
    table: str, column: str, parent_table: str, parent_column: str, severity: str = SEVERITY_ERROR
) -> Expectation:
    """Orphan check: fact rows whose dimension key does not resolve.

    NULL is excluded deliberately - "not yet known" is a different problem from "points at
    something that does not exist", and conflating them buries the second in the first.
    """
    return Expectation(
        name=f"{table}.{column}.fk_{parent_table}",
        table=table,
        failing_sql=(
            f"SELECT c.* FROM {table} c "
            f"LEFT JOIN {parent_table} p ON c.`{column}` = p.`{parent_column}` "
            f"WHERE c.`{column}` IS NOT NULL AND p.`{parent_column}` IS NULL"
        ),
        severity=severity,
        description=f"{column} must resolve to {parent_table}.{parent_column}",
    )


def in_range(
    table: str, column: str, low: float | None = None, high: float | None = None,
    severity: str = SEVERITY_WARN,
) -> Expectation:
    if low is None and high is None:
        raise ValueError("in_range needs at least one bound")
    bounds = []
    if low is not None:
        bounds.append(f"`{column}` < {low}")
    if high is not None:
        bounds.append(f"`{column}` > {high}")
    return Expectation(
        name=f"{table}.{column}.range",
        table=table,
        failing_sql=(
            f"SELECT * FROM {table} WHERE `{column}` IS NOT NULL AND ({' OR '.join(bounds)})"
        ),
        severity=severity,
        description=f"{column} within [{low}, {high}]",
    )


def freshness(table: str, column: str, max_age_hours: int, severity: str = SEVERITY_WARN) -> Expectation:
    """Fails when the newest row is older than max_age_hours.

    Catches the silent failure mode where a pipeline stops running and the report keeps
    cheerfully showing last month's numbers.
    """
    return Expectation(
        name=f"{table}.{column}.freshness",
        table=table,
        failing_sql=(
            f"SELECT MAX(`{column}`) AS newest FROM {table} "
            f"HAVING MAX(`{column}`) < CURRENT_TIMESTAMP() - INTERVAL {max_age_hours} HOURS"
        ),
        severity=severity,
        description=f"{table} refreshed within {max_age_hours}h",
    )


def date_order(table: str, start_column: str, end_column: str, severity: str = SEVERITY_WARN) -> Expectation:
    """Start must not be after end. This is Excel defect #6, caught at load time."""
    return Expectation(
        name=f"{table}.{start_column}_{end_column}.order",
        table=table,
        failing_sql=(
            f"SELECT * FROM {table} "
            f"WHERE `{start_column}` IS NOT NULL AND `{end_column}` IS NOT NULL "
            f"AND `{start_column}` > `{end_column}`"
        ),
        severity=severity,
        description=f"{start_column} <= {end_column}",
    )


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


@dataclass
class Suite:
    expectations: list[Expectation] = field(default_factory=list)

    def add(self, *expectations: Expectation) -> "Suite":
        self.expectations.extend(expectations)
        return self

    def run(self, spark: Any, batch_id: str, persist: bool = True) -> list[Result]:
        """Evaluate every expectation. Never short-circuits.

        Running all of them even after one fails matters: you want the full picture in one
        pass, not a game of whack-a-mole across ten pipeline runs.
        """
        results: list[Result] = []
        for exp in self.expectations:
            try:
                failing = spark.sql(exp.failing_sql)
                count = failing.count()
            except Exception as exc:  # noqa: BLE001 - a broken check is itself a failure
                results.append(Result(exp, failing_rows=-1))
                print(f"[dq] {exp.name}: CHECK FAILED TO RUN - {exc}")
                continue

            results.append(Result(exp, failing_rows=count))
            if count and persist:
                _persist_rejects(spark, exp, failing, batch_id)

        if persist:
            _persist_results(spark, results, batch_id)
        return results


def _persist_rejects(spark: Any, exp: Expectation, failing: Any, batch_id: str) -> None:
    from pyspark.sql import functions as F  # noqa: N812 - Spark convention

    (
        failing.limit(1000)
        .withColumn("_dq_expectation", F.lit(exp.name))
        .withColumn("_dq_reason", F.lit(exp.description or exp.name))
        .withColumn("_batch_id", F.lit(batch_id))
        .selectExpr("_dq_expectation", "_dq_reason", "_batch_id", "to_json(struct(*)) AS _row")
        .write.format("delta").mode("append").saveAsTable(REJECTS_TABLE)
    )


def _persist_results(spark: Any, results: list[Result], batch_id: str) -> None:
    from .fabric_common import utc_now

    rows = [
        (batch_id, r.expectation.name, r.expectation.table, r.expectation.severity,
         r.failing_rows, r.passed, utc_now())
        for r in results
    ]
    schema = (
        "batch_id string, expectation string, table_name string, severity string, "
        "failing_rows long, passed boolean, checked_at timestamp"
    )
    spark.createDataFrame(rows, schema).write.format("delta").mode("append").saveAsTable(RESULTS_TABLE)


def assert_no_blocking(results: list[Result]) -> None:
    """Raise if any error-severity expectation failed.

    Call this at the end of the DQ notebook. It is what turns the suite from a report
    into a gate - the pipeline stops instead of publishing numbers nobody checked.
    """
    blocking = [r for r in results if r.blocking]
    if blocking:
        detail = "\n".join(
            f"  - {r.expectation.name}: {r.failing_rows} failing rows "
            f"({r.expectation.description})"
            for r in blocking
        )
        raise RuntimeError(f"{len(blocking)} blocking data-quality failure(s):\n{detail}")


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------


def _selftest() -> None:
    e = not_null("fct_X", "ProjectKey")
    assert "IS NULL" in e.failing_sql and e.severity == SEVERITY_ERROR

    u = unique_key("dim_Project", ["ProjectKey"])
    assert "HAVING COUNT(*) > 1" in u.failing_sql

    r = referential("fct_X", "ProjectKey", "dim_Project", "ProjectKey")
    # Orphans only - a NULL key is a different defect and must not be reported as an orphan.
    assert "IS NOT NULL" in r.failing_sql and "LEFT JOIN" in r.failing_sql

    rng = in_range("fct_X", "Pct", low=0, high=1)
    assert "`Pct` < 0" in rng.failing_sql and "`Pct` > 1" in rng.failing_sql
    assert rng.severity == SEVERITY_WARN

    d = date_order("fct_Milestone", "BaselineStart", "BaselineFinish")
    assert "> `BaselineFinish`" in d.failing_sql

    try:
        in_range("t", "c")
    except ValueError:
        pass
    else:
        raise AssertionError("in_range with no bounds should raise")

    try:
        Expectation("x", "t", "SELECT 1", severity="loud")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown severity should raise")

    # A warn-severity failure must not block; an error-severity one must.
    warn_fail = Result(in_range("t", "c", low=0), failing_rows=3)
    err_fail = Result(not_null("t", "c"), failing_rows=1)
    passing = Result(not_null("t", "c"), failing_rows=0)
    assert not warn_fail.blocking and err_fail.blocking and not passing.blocking
    assert_no_blocking([warn_fail, passing])  # must not raise
    try:
        assert_no_blocking([err_fail])
    except RuntimeError:
        pass
    else:
        raise AssertionError("blocking failure should raise")

    print("dq: all checks passed")


if __name__ == "__main__":
    _selftest()
