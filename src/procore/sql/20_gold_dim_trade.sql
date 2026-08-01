-- gold: dim_Trade - static seed from DROPDOWN!M4:M32.
--
-- 29 cells, but `Metals` appears twice (analysis/excel-tracker/field-inventory.md:218)
-- so 28 distinct values after the dedup powerbi/semantic-model.md:114 calls for.
-- All values are seeded already-trimmed: 12 of the originals carry trailing whitespace
-- and "Metals  " never equals "Metals" in a join (defect #9).
--
-- TradeKey 0 = Unassigned. Procore does not carry Affect's trade vocabulary, so items
-- that cannot be mapped land here rather than vanishing - a visible bar on the chart
-- beats a silently missing one.

CREATE OR REPLACE TABLE dim_Trade AS
SELECT * FROM (VALUES
    (0,  'Unassigned',                  999),
    (1,  'Existing Conditions',           1),
    (2,  'Concrete',                      2),
    (3,  'Foundation',                    3),
    (4,  'Superstructure',                4),
    (5,  'Masonry',                       5),
    (6,  'Metals',                        6),
    (7,  'Drywall & Carpentry',           7),
    (8,  'Roofing',                       8),
    (9,  'Millwork',                      9),
    (10, 'Finishes',                     10),
    (11, 'Specialties',                  11),
    (12, 'Equipment',                    12),
    (13, 'Doors & Frames',               13),
    (14, 'Glass & Glazing',              14),
    (15, 'Conveying Equipment',          15),
    (16, 'Sprinkler',                    16),
    (17, 'Plumbing',                     17),
    (18, 'HVAC',                         18),
    (19, 'Building Automation Systems',  19),
    (20, 'Electrical',                   20),
    (21, 'Low Voltage',                  21),
    (22, 'Utilities',                    22),
    (23, 'Painting',                     23),
    (24, 'Flooring',                     24),
    (25, 'Self Levelling',               25),
    (26, 'Windows',                      26),
    (27, 'Lighting',                     27),
    (28, 'Exterior Improvements',        28)
) AS t(TradeKey, TradeName, SortOrder);
