"""Per-table high-water marks, so a load pulls only what changed.

The Jul 23 warehouse review: "Notebooks currently replace the whole table on each run
(full reload). Needs to move to incremental refresh - pull only new/changed rows."

This is the state that makes that possible. One row per (table, endpoint) holding the
newest source timestamp successfully loaded.

Two rules that stop this being a footgun:

1. **The watermark advances only on success.** Writing it before the load means a crash
   mid-run silently skips rows forever, and nobody notices until a number is wrong.
2. **Reads overlap backwards by an hour.** Procore's `updated_at` has second granularity
   and clock skew between their servers and ours is real. Re-pulling an hour costs
   nothing because the load is a MERGE, not an append.

Self-check: python watermark.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

WATERMARK_TABLE = "cd_meta_watermark"

# How far back to re-read on each incremental pull. See rule 2 above.
OVERLAP = timedelta(hours=1)

_SCHEMA = (
    "table_name string, endpoint string, watermark timestamp, "
    "batch_id string, updated_at timestamp"
)


def read_watermark(spark: Any, table: str, endpoint: str) -> datetime | None:
    """Newest successfully-loaded source timestamp, or None on first run.

    None means "full reload" - correct for a first run, and safe on any run because the
    load merges on the natural key.
    """
    if not spark.catalog.tableExists(WATERMARK_TABLE):
        return None
    rows = spark.sql(
        f"SELECT watermark FROM {WATERMARK_TABLE} "
        f"WHERE table_name = '{table}' AND endpoint = '{endpoint}' "
        f"ORDER BY updated_at DESC LIMIT 1"
    ).collect()
    return rows[0]["watermark"] if rows else None


def write_watermark(spark: Any, table: str, endpoint: str, value: datetime, batch_id: str) -> None:
    """Record a new high-water mark. Call only after the load has succeeded."""
    from .fabric_common import merge_delta, utc_now

    df = spark.createDataFrame(
        [(table, endpoint, value, batch_id, utc_now())], _SCHEMA
    )
    merge_delta(spark, df, WATERMARK_TABLE, ["table_name", "endpoint"])


def read_since(spark: Any, table: str, endpoint: str) -> datetime | None:
    """The value to pass to the API filter: the watermark, less the overlap."""
    mark = read_watermark(spark, table, endpoint)
    return apply_overlap(mark)


def apply_overlap(mark: datetime | None) -> datetime | None:
    """Pure function so the overlap rule is testable without Spark."""
    if mark is None:
        return None
    if mark.tzinfo is None:
        mark = mark.replace(tzinfo=timezone.utc)
    return mark - OVERLAP


def high_water(records: list[dict[str, Any]], field: str = "updated_at") -> datetime | None:
    """Newest timestamp across a batch of source records.

    Returns None for an empty batch, which correctly leaves the watermark untouched -
    an empty pull must not advance it.
    """
    stamps = [_parse(r.get(field)) for r in records]
    stamps = [s for s in stamps if s is not None]
    return max(stamps) if stamps else None


def _parse(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _selftest() -> None:
    base = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)

    # First run pulls everything.
    assert apply_overlap(None) is None
    # Later runs step back by exactly the overlap.
    assert apply_overlap(base) == base - OVERLAP
    # Naive timestamps are treated as UTC rather than crashing.
    assert apply_overlap(datetime(2026, 8, 1, 12, 0)) == base - OVERLAP

    records = [
        {"updated_at": "2026-07-30T10:00:00Z"},
        {"updated_at": "2026-08-01T09:30:00Z"},
        {"updated_at": "2026-07-31T23:59:59Z"},
    ]
    assert high_water(records) == datetime(2026, 8, 1, 9, 30, tzinfo=timezone.utc)

    # An empty pull leaves the watermark alone - otherwise a quiet day skips rows forever.
    assert high_water([]) is None
    # Unparseable or missing timestamps are ignored, not fatal.
    assert high_water([{"updated_at": None}, {"updated_at": "not-a-date"}, {}]) is None
    assert high_water([{"updated_at": "bad"}, {"updated_at": "2026-08-01T00:00:00Z"}]) == datetime(
        2026, 8, 1, tzinfo=timezone.utc
    )

    print("watermark: all checks passed")


if __name__ == "__main__":
    _selftest()
