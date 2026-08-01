[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared dim_procore_cost_codes = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_cost_codes_raw", ItemKind = "Table"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 2", {"biller", "biller_id", "biller_type", "budgeted"}),
  #"Parsed JSON" = Table.TransformColumns(#"Removed columns", {{"parent", each Json.Document(_), type any}}),
  #"Expanded parent" = Table.ExpandRecordColumn(#"Parsed JSON", "parent", {"id"}, {"id.1"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Expanded parent", {"line_item_types", "created_at", "updated_at", "project_name"}),
  #"Sorted rows" = Table.Sort(#"Removed columns 1", {{"name", Order.Ascending}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Sorted rows", {{"id", Int64.Type}}),
  #"Trimmed text" = Table.TransformColumns(#"Changed column type", {{"project_id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Trimmed text 1" = Table.TransformColumns(#"Trimmed text", {{"id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Trimmed text 2" = Table.TransformColumns(#"Trimmed text 1", {{"project_id", each Text.Trim(_), type nullable text}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Trimmed text 2", {{"id.1", Int64.Type}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Changed column type 2", {{"id", Int64.Type}}),
  #"Removed duplicates" = Table.Distinct(#"Changed column type 1", {"id"}),
  #"Reordered columns" = Table.ReorderColumns(#"Removed duplicates", {"standard_cost_code_id", "id", "name", "full_code", "code", "id.1", "sortable_code", "project_id"}),
  #"Trimmed text 3" = Table.TransformColumns(#"Reordered columns", {{"standard_cost_code_id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Trimmed text 3", {"standard_cost_code_id"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns 2", {{"id", "Cost Code ID"}}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Renamed columns", {{"Cost Code ID", type text}, {"id.1", type text}, {"project_id", type text}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Changed column type 3", {{"project_id", "Project ID"}, {"name", "Cost Code (Name)"}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Renamed columns 1", {{"Cost Code (Name)", type text}, {"full_code", type text}, {"code", type text}, {"id.1", type text}, {"sortable_code", type text}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type 4", {"Project ID"}),
  #"Appended query" = Table.Combine({#"Removed columns 3", NonTrade}),
  #"Removed columns 4" = Table.RemoveColumns(#"Appended query", {"sortable_code", "code", "full_code"})
in
  #"Removed columns 4";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
[BindToDefaultDestination = true]
shared NonTrade = let
  Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WMlDSUfLLz9MNKUpMSVXQV3BPzUstSsxRcM7PS8ksyczPKwYp8PfTDQlydHFFY+eV5uSgCMXGAgA=", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"Cost Code ID" = _t, #"Cost Code (Name)" = _t, full_code = _t, code = _t, id.1 = _t, sortable_code = _t]),
  #"Changed column type" = Table.TransformColumnTypes(Source, {{"Cost Code ID", type text}, {"Cost Code (Name)", type text}, {"full_code", type text}, {"code", type text}, {"id.1", type text}, {"sortable_code", type text}})
in
  #"Changed column type";
