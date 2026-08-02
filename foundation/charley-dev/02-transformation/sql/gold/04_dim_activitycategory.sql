-- gold: dim_ActivityCategory - safety (DROPDOWN!I, 16) + quality (DROPDOWN!K, 11) = 27.
--
-- Verbatim from analysis/excel-tracker/dropdowns-and-status.md:103-150.
--
-- Both lists carry an implicit two-level structure, "Type - Qualifier", separated by an
-- EN DASH (U+2013, not a hyphen). Splitting it turns a flat 16-item picklist into a
-- filterable hierarchy: you can ask "all Toolbox Talks" or "everything Scheduled"
-- instead of only ever matching the whole string.
--
-- FullLabel keeps the original string verbatim, en dash and all, so an export can still
-- reproduce exactly what the workbook shows. Nothing joins on it.
--
-- One value in the quality list has no qualifier structure in the usual sense -
-- "Quality - High-Risk Observation" - so its Type is 'Quality'. Kept as-is rather than
-- reclassified: it is their vocabulary, not ours.

CREATE OR REPLACE TABLE dim_ActivityCategory AS
SELECT * FROM (VALUES
    (0,  'Unassigned', 'Unassigned',      CAST(NULL AS STRING),          'Unassigned'),

    -- DROPDOWN!I - safety activity category (16)
    (1,  'Safety',  'High-Risk Item',    'Completed',                    'High-Risk Item – Completed'),
    (2,  'Safety',  'High-Risk Item',    'Upcoming',                     'High-Risk Item – Upcoming'),
    (3,  'Safety',  'Toolbox Talk',      'Completed',                    'Toolbox Talk – Completed'),
    (4,  'Safety',  'Toolbox Talk',      'Scheduled',                    'Toolbox Talk – Scheduled'),
    (5,  'Safety',  'Safety Standdown',  'Completed',                    'Safety Standdown – Completed'),
    (6,  'Safety',  'Safety Standdown',  'Scheduled',                    'Safety Standdown – Scheduled'),
    (7,  'Safety',  'Weekend/OT Work',   'Completed',                    'Weekend/OT Work – Completed'),
    (8,  'Safety',  'Weekend/OT Work',   'Planned',                      'Weekend/OT Work – Planned'),
    (9,  'Safety',  'Notable Visitor',   'DOB',                          'Notable Visitor – DOB'),
    (10, 'Safety',  'Notable Visitor',   'FDNY',                         'Notable Visitor – FDNY'),
    (11, 'Safety',  'Notable Visitor',   'Client',                       'Notable Visitor – Client'),
    (12, 'Safety',  'Notable Visitor',   'OSHA',                         'Notable Visitor – OSHA'),
    (13, 'Safety',  'Notable Visitor',   'Other',                        'Notable Visitor – Other'),
    (14, 'Safety',  'Safety Win',        'Team Performance',             'Safety Win – Team Performance'),
    (15, 'Safety',  'Safety Win',        'Milestone with No Incidents',  'Safety Win – Milestone with No Incidents'),
    (16, 'Safety',  'Safety Win',        'Inspection Success',           'Safety Win – Inspection Success'),

    -- DROPDOWN!K - quality category (11)
    (20, 'Quality', 'Quality',           'High-Risk Observation',        'Quality – High-Risk Observation'),
    (21, 'Quality', 'Benchmark',         'Completed',                    'Benchmark – Completed'),
    (22, 'Quality', 'Benchmark',         'Scheduled',                    'Benchmark – Scheduled'),
    (23, 'Quality', 'Mockup',            'Completed',                    'Mockup – Completed'),
    (24, 'Quality', 'Mockup',            'Scheduled',                    'Mockup – Scheduled'),
    (25, 'Quality', 'Delivery',          'Rejected',                     'Delivery – Rejected'),
    (26, 'Quality', 'Delivery',          'Upcoming',                     'Delivery – Upcoming'),
    (27, 'Quality', 'Commissioning',     'Completed',                    'Commissioning – Completed'),
    (28, 'Quality', 'Commissioning',     'Upcoming',                     'Commissioning – Upcoming'),
    (29, 'Quality', 'Inspection',        'Special',                      'Inspection – Special'),
    (30, 'Quality', 'Inspection',        'NCR',                          'Inspection – NCR')
) AS t(CategoryKey, Domain, CategoryType, CategoryQualifier, FullLabel);
