[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared dim_projects = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_projects_raw", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"id", "Project ID"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"company"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns", {{"completion_date", type date}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Changed column type", {"country_code", "county", "created_at"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns 1", {{"actual_start_date", type datetime}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type 1", {"delivery_method", "description", "estimated_value", "fax", "latitude", "is_demo", "longitude", "work_scope", "total_value", "time_zone", "state_code"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Removed columns 2", {{"start_date", type date}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type 2", {"square_feet", "sector", "projected_finish_date", "project_type", "project_stage", "project_sector_id", "project_owner_type_id", "project_bid_type_id", "phone"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 3", {{"name", "Project Name"}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Renamed columns 1", {"parent_job_id", "custom_fields", "created_by", "city", "address"}),
  #"Extracted text before delimiter" = Table.TransformColumns(#"Removed columns 4", {{"actual_start_date", each Text.BeforeDelimiter(Text.From(_), " ", 0), type text}}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Extracted text before delimiter", {{"actual_start_date", type date}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 3", {"active", "actual_start_date", "completion_date", "erp_integrated", "photo_id", "display_name"}),
  #"Filtered rows" = Table.SelectRows(#"Removed columns 5", each ([Project Name] <> "Sandbox Test Project" and [Project Name] <> "Standard Project Template" and [Project Name] <> "TEST - ABM SUBORDINATE")),
  #"Removed columns 6" = Table.RemoveColumns(#"Filtered rows", {"start_date", "updated_at", "zip"}),
  #"Trimmed text" = Table.TransformColumns(#"Removed columns 6", {{"Project ID", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Trimmed text", {{"Project ID", type text}})
in
  #"Changed column type 4";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
[BindToDefaultDestination = true]
shared dim_projects_procoreXsage = let
  Source = dim_projects,
  #"Sorted rows" = Table.Sort(Source, {{"Project Name", Order.Ascending}}),
  #"Merged queries 1" = Table.NestedJoin(#"Sorted rows", {"Project ID"}, Table, {"Procore Project ID"}, "Table", JoinKind.LeftOuter),
  #"Expanded Table" = Table.ExpandTableColumn(#"Merged queries 1", "Table", {"Sage Project ID"}, {"Sage Project ID"}),
  #"Removed columns" = Table.RemoveColumns(#"Expanded Table", {"origin_data", "origin_id", "project_number"}),
  #"Replaced value" = Table.ReplaceValue(#"Removed columns", null, "0", Replacer.ReplaceValue, {"origin_code"})
in
  #"Replaced value";
[BindToDefaultDestination = true]
shared Table = let
  Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("XdC7DQQhDATQXog38G9sU8tq+2/jEBDYl/ppZhDvO3g8Ay7T5oSlKsLG97wD5Q4iRui+s1RgTiY54BVEEDMPRIM1ILxhtgk3NzqBrKCckPMmbglJt/ANddpmaOht4j/wvE3owCmxQesdFEQ3QC2wqm5A2n+oQ/wCNQi4rqrvBw==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"Sage Project ID" = _t, #"Procore Project ID" = _t]),
  #"Changed column type" = Table.TransformColumnTypes(Source, {{"Sage Project ID", type text}})
in
  #"Changed column type";
