[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;

// ============================================================================
// CD_Sage_Ingest - Sage 100 Contractor -> CD_Bronze_Lakehouse
//
// Same source and same on-prem gateway as the existing Build_Sage_Test dataflow:
//   Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group")
//
// WHAT IS DIFFERENT, AND WHY IT MATTERS
//
// The existing dataflow pulls six header tables and explicitly REMOVES the columns that
// point at the line tables - "arivln(recnum)", "apivln(recnum)" appear only in
// Table.RemoveColumns. So the line detail has never been queried.
//
// That matters for one number in particular. RETAINAGE. `retain` is present on the invoice
// header and is ZERO across all 940 invoices - verified, commit db0d11e. It is not held
// there for this company. A report sourced from the header shows $0 retainage and nobody
// notices until a client asks where their retention is. The real values live in the line
// tables, alongside the cost codes that the header also does not carry.
//
// So this dataflow adds `arivln` and `apivln`, and keeps the headers raw rather than
// pre-filtering them.
//
// RAW, NOT SHAPED. The existing dataflow filters (Invoice Balance <> 0) and renames columns
// inside Power Query. Ours lands the tables as they are and does the shaping in
// sql/silver/, where it is diffable, testable offline in DuckDB, and reviewable in a pull
// request. A Power Query step is none of those things. This is the same bronze rule the
// Procore side follows: never drop a column at the boundary, because a transform bug should
// be a re-run and not a re-extract.
//
// NOT YET BOUND TO THE GATEWAY. The connection is Affect's to authorise - see
// _docs/sage-ingestion.md. Everything else is complete, so binding is the only step left.
// ============================================================================

// ---------------------------------------------------------------- AR (revenue)

[BindToDefaultDestination = true]
shared cd_bronze_sage_acrinv = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "acrinv"]}[Data]
in
  Navigation;

// AR invoice LINES. Never queried by the existing dataflow. Cost codes and the real
// retainage live here, not on the header.
[BindToDefaultDestination = true]
shared cd_bronze_sage_arivln = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "arivln"]}[Data]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_sage_acrpmt = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "acrpmt"]}[Data]
in
  Navigation;

// ---------------------------------------------------------------- AP (expenditure)

[BindToDefaultDestination = true]
shared cd_bronze_sage_acpinv = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "acpinv"]}[Data]
in
  Navigation;

// AP invoice LINES. Same story as arivln - the header hides the cost code.
[BindToDefaultDestination = true]
shared cd_bronze_sage_apivln = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "apivln"]}[Data]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_sage_acppmt = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "acppmt"]}[Data]
in
  Navigation;

// ---------------------------------------------------------------- jobs and ledger

// THE JOIN KEY. Per resources/sage-100-contractor/schema/README.md, `jobnum` on an invoice
// is a foreign key to actrec.recnum - it is NOT a readable job code. That is why
// dim_projects_procoreXsage IS the Procore-to-Sage join rather than a convenience lookup,
// and why this table is not optional.
//
// actrec.retain is also one of the three candidate sources for real retainage (open
// question 4), which cannot be settled until the data is here to look at.
[BindToDefaultDestination = true]
shared cd_bronze_sage_actrec = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "actrec"]}[Data]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_sage_actpay = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "actpay"]}[Data]
in
  Navigation;
