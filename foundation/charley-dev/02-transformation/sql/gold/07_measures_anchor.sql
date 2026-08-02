-- gold: measures_anchor - a one-row physical table for the model's measures to live on.
--
-- Measures belong in their own table so they sort to the top of the field list instead of
-- being scattered across the facts they happen to reference. In an import model that table
-- would be a calculated table (`ROW("_placeholder", BLANK())`).
--
-- DIRECT LAKE DOES NOT SUPPORT CALCULATED TABLES. Adding one does not fail loudly - the
-- model deploys, reports success, and then loads NO tables at all. Every DAX query comes
-- back "Failed to resolve name 'dim_Date'", which looks like a broken pipeline rather than
-- a modelling mistake. Diagnosed by querying each of the 16 tables individually and
-- finding all of them missing.
--
-- So the anchor is a real Delta table with one row, exposed through Direct Lake like
-- everything else. One row, one hidden column, no calculated anything.

CREATE OR REPLACE TABLE measures_anchor AS
SELECT CAST('measures' AS STRING) AS _placeholder;
