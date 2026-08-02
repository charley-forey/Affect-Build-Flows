[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;

// ============================================================================
// CD_Manual_Ingest - SharePoint lists -> CD_Bronze_Lakehouse
//
// The ~40% of the monthly report that exists in no system of record: wins, the risk
// register, priority items, the client survey, contract milestone dates, safety hours.
// Today those are ~700 hand-typed cells in one spreadsheet that one person owns.
//
// SITE URL IS A PLACEHOLDER. The lists live in Affect's tenant and need SharePoint admin
// rights to create - see _docs/sharepoint-lists.md, which is written to hand over. Replace
// SITE below with the real URL and this dataflow is ready to bind.
//
// LANDED RAW, SHAPED IN SQL. No filtering, renaming or retyping happens here. Power Query
// steps are not diffable in review, not testable offline, and not re-runnable against data
// already pulled; sql/silver/30_manual_silver.sql is all three. Same bronze rule the
// Procore and Sage sides follow - never drop a column at the boundary, so a transform bug
// is a re-run rather than asking people to retype a month of work.
//
// Expand=false on lookup columns keeps ProjectKey as the raw lookup record. Silver reads
// the id out of it; expanding here would bake a display name into bronze, and a renamed
// project would then silently orphan its history.
// ============================================================================

SITE = "https://REPLACE-ME.sharepoint.com/sites/AffectProjectReporting";

[BindToDefaultDestination = true]
shared cd_bronze_man_projects = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Projects"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_wins = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Wins"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_risks = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Risks"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_priority_items = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Priority Items"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_flags = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Flags"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_survey = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Survey"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_safety_monthly = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Safety Monthly"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_quality_monthly = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Quality Monthly"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_milestones = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Milestones"]}[Items]
in
  Navigation;

[BindToDefaultDestination = true]
shared cd_bronze_man_daily_log_compliance = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{[Title = "CD Daily Log Compliance"]}[Items]
in
  Navigation;

