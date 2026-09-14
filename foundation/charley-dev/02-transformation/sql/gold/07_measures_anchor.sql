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

-- _built_at carries the gold build time so [Last Refresh] can put it in the report footer.
-- An exported page has to state what it is a snapshot of; the workbook used TODAY(), which
-- meant a saved file re-dated itself every time it was opened (defect #5). Stamping at
-- BUILD time rather than at view time is the whole point.
-- Seeding runs independently of ingestion and must not advance the report's build time.
-- deploy_gold stamps this only after the gold statements and verification succeed.
CREATE TABLE IF NOT EXISTS measures_anchor AS
SELECT CAST('measures' AS STRING) AS _placeholder,
       CAST(NULL AS TIMESTAMP)    AS _built_at;
