"""Sage silver reconciliation predicates, embedded into the Fabric notebook.

Each query returns violations. One cent is the explicit per-invoice tolerance;
missing lines or amounts are unknown, never a zero-dollar reconciliation.
"""


def checks() -> dict[str, str]:
    rules = {}
    for direction, header_source, line_source in (
        ("ar", "acrinv", "arivln"), ("ap", "acpinv", "apivln")
    ):
        headers = f"cd_silver_sage_{direction}_invoices"
        lines = f"cd_silver_sage_{direction}_lines"
        rules[f"sage_{direction}.header_keys"] = f"""
SELECT invoice_uid FROM {headers}
GROUP BY invoice_uid HAVING invoice_uid IS NULL OR COUNT(*) > 1
"""
        rules[f"sage_{direction}.line_keys"] = f"""
SELECT line_uid FROM {lines}
GROUP BY line_uid HAVING line_uid IS NULL OR COUNT(*) > 1
"""
        rules[f"sage_{direction}.orphan_lines"] = f"""
SELECT l.* FROM {lines} l
LEFT JOIN {headers} h ON l.invoice_uid = h.invoice_uid
WHERE h.invoice_uid IS NULL
"""
        for kind, silver, bronze in (
            ("headers", headers, header_source), ("lines", lines, line_source)
        ):
            rules[f"sage_{direction}.{kind}_row_conservation"] = f"""
SELECT b.n AS bronze_rows, s.n AS silver_rows
FROM (SELECT COUNT(*) AS n FROM cd_bronze_sage_{bronze}) b
CROSS JOIN (SELECT COUNT(*) AS n FROM {silver}) s
WHERE b.n <> s.n
"""
        rules[f"sage_{direction}.invoice_line_amounts"] = f"""
SELECT h.invoice_uid, h.invoice_id, h.invoice_total,
       l.line_count, l.known_amounts, l.line_total,
       h.invoice_total - l.line_total AS difference
FROM {headers} h
LEFT JOIN (
    SELECT invoice_uid, COUNT(*) AS line_count, COUNT(line_total) AS known_amounts,
           SUM(line_total) AS line_total
    FROM {lines} GROUP BY invoice_uid
) l ON h.invoice_uid = l.invoice_uid
WHERE h.invoice_total IS NULL OR l.line_count IS NULL
   OR l.known_amounts <> l.line_count
   OR ABS(h.invoice_total - l.line_total) > 0.01
"""
    return rules
