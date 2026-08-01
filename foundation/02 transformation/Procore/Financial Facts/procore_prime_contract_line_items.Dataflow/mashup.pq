[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_prime_contract_line_items = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_prime_contract_line_items", ItemKind = "Table"]}[Data],
  #"Trimmed text" = Table.TransformColumns(#"Navigation 2", {{"project_id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Trimmed text", {{"project_id", Int64.Type}}),
  #"Renamed columns" = Table.RenameColumns(#"Changed column type", {{"project_id", "Project ID"}}),
  #"Trimmed text 1" = Table.TransformColumns(#"Renamed columns", {{"prime_contract_id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Trimmed text 1", {{"prime_contract_id", "Prime Contract ID"}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Renamed columns 1", {{"Prime Contract ID", Int64.Type}}),
  #"Trimmed text 2" = Table.TransformColumns(#"Changed column type 1", {{"line_item_id", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Renamed columns 2" = Table.RenameColumns(#"Trimmed text 2", {{"line_item_id", "Line Item ID"}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Renamed columns 2", {{"Line Item ID", Int64.Type}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type 2", {{"raw_json", each Json.Document(_), type any}}),
  #"Expanded raw_json" = Table.ExpandRecordColumn(#"Parsed JSON", "raw_json", {"id", "created_at", "updated_at", "amount", "company", "cost_code", "extended_type", "holder", "line_item_type", "origin_id", "position", "project", "quantity", "total_amount", "extended_amount", "unit_cost", "currency_configuration", "wbs_code", "_project_id", "_prime_contract_id", "_prime_contract_title"}, {"id", "created_at", "updated_at", "amount", "company", "cost_code", "extended_type", "holder", "line_item_type", "origin_id", "position", "project", "quantity", "total_amount", "extended_amount", "unit_cost", "currency_configuration", "wbs_code", "_project_id", "_prime_contract_id", "_prime_contract_title"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Expanded raw_json", {{"amount", Currency.Type}}),
  #"Removed columns" = Table.RemoveColumns(#"Changed column type 3", {"company", "id", "created_at", "updated_at"}),
  #"Renamed columns 3" = Table.RenameColumns(#"Removed columns", {{"amount", "$ Amount"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 3", {"extended_type"}),
  #"Expanded cost_code" = Table.ExpandRecordColumn(#"Removed columns 1", "cost_code", {"id", "name", "full_code", "origin_id", "origin_data"}, {"id", "name", "full_code", "origin_id.1", "origin_data"}),
  #"Renamed columns 4" = Table.RenameColumns(#"Expanded cost_code", {{"id", "Cost Code ID"}}),
  #"Trimmed text 3" = Table.TransformColumns(#"Renamed columns 4", {{"Cost Code ID", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Trimmed text 3", {{"Cost Code ID", Int64.Type}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type 4", {"name", "project", "quantity", "line_item_type", "origin_id", "holder", "origin_data", "origin_id.1"}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Removed columns 2", {{"total_amount", Currency.Type}, {"extended_amount", Currency.Type}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type 5", {"unit_cost", "currency_configuration", "_project_id", "_prime_contract_title", "pulled_at", "_prime_contract_id"}),
  #"Expanded wbs_code" = Table.ExpandRecordColumn(#"Removed columns 3", "wbs_code", {"description", "flat_code", "id"}, {"description", "flat_code", "id"}),
  #"Removed columns 4" = Table.RemoveColumns(#"Expanded wbs_code", {"description", "prime_contract_title", "flat_code", "id"}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Removed columns 4", {{"Project ID", type text}, {"Prime Contract ID", type text}, {"Line Item ID", type text}, {"Cost Code ID", type text}, {"full_code", type text}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 6", {"extended_amount", "position"})
in
  #"Removed columns 5";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
