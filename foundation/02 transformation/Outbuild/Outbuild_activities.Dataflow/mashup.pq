[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared Outbuild_activities = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "bronze_outbuild_activities", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"procore_project_id", "Procore Project ID"}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Renamed columns", {{"Procore Project ID", type text}}),
  #"Removed columns" = Table.RemoveColumns(#"Changed column type", {"project_name"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns", {{"outbuild_project_id", "Outbuild Project ID"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 1", {"organization_id"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns 1", {{"cost_actual", Currency.Type}, {"cost_earned", Currency.Type}}),
  #"Extracted first characters" = Table.TransformColumns(#"Changed column type 1", {{"updated_at", each Text.Start(_, 10), type text}}),
  #"Extracted first characters 1" = Table.TransformColumns(#"Extracted first characters", {{"created_at", each Text.Start(_, 10), type text}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Extracted first characters 1", {{"created_at", type date}, {"updated_at", type date}}),
  #"Extracted first characters 2" = Table.TransformColumns(#"Changed column type 2", {{"end_date", each Text.Start(_, 10), type text}}),
  #"Extracted first characters 3" = Table.TransformColumns(#"Extracted first characters 2", {{"start_date", each Text.Start(_, 10), type text}}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Extracted first characters 3", {{"start_date", type date}, {"end_date", type date}, {"cost_budgeted", Currency.Type}}),
  #"Extracted first characters 4" = Table.TransformColumns(#"Changed column type 3", {{"constraint_date", each Text.Start(_, 10), type text}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Extracted first characters 4", {{"constraint_date", type date}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type 4", {"description"}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Removed columns 2", {{"free_float", Int64.Type}}),
  #"Divided column" = Table.TransformColumns(#"Changed column type 5", {{"progress", each _ / 100, type number}}),
  #"Added custom" = Table.AddColumn(#"Divided column", "Status", each if [is_critical] = true and [progress] < 1 and [end_date] < Date.From(DateTime.LocalNow()) then "Delayed"
else if [end_date] < Date.From(DateTime.LocalNow()) and [progress] < 1 then "Overdue"
else if [free_float] = 0 and [is_critical] = true then "No Float - High Risk"
else if [progress] = 0 and [start_date] < Date.From(DateTime.LocalNow()) then "Not Started - At Risk"
else "On Track"),
  #"Removed columns 3" = Table.RemoveColumns(#"Added custom", {"ingested_at"}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Removed columns 3", {{"progress", Percentage.Type}, {"Status", type text}, {"Outbuild Project ID", type text}})
in
  #"Changed column type 6";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
