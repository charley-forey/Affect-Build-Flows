[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_work_order_line_item_silver_test = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_work_order_line_items", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"project_id", "Project ID"}, {"work_order_contract_id", "Commitment ID"}}),
  #"Parsed JSON" = Table.TransformColumns(#"Renamed columns", {{"raw_json", each Json.Document(_), type any}}),
  #"Expanded raw_json" = Table.ExpandRecordColumn(#"Parsed JSON", "raw_json", {"id", "created_at", "updated_at", "amount", "company", "cost_code", "wbs_code", "description", "extended_type", "holder", "line_item_type", "origin_id", "position", "project", "quantity", "total_amount", "extended_amount", "unit_cost", "currency_configuration", "_project_id", "_work_order_contract_id", "_work_order_contract_title"}, {"id", "created_at", "updated_at", "amount", "company", "cost_code", "wbs_code", "description", "extended_type", "holder", "line_item_type", "origin_id", "position", "project", "quantity", "total_amount", "extended_amount", "unit_cost", "currency_configuration", "_project_id", "_work_order_contract_id", "_work_order_contract_title"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Expanded raw_json", {{"amount", Currency.Type}}),
  #"Expanded cost_code" = Table.ExpandRecordColumn(#"Changed column type", "cost_code", {"full_code", "origin_id", "origin_data", "standard_cost_code_id", "code", "parent", "sortable_code", "line_item_types"}, {"full_code", "origin_id.1", "origin_data", "standard_cost_code_id", "code", "parent", "sortable_code", "line_item_types"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Expanded cost_code", {{"full_code", "Cost Code"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns 1", {"Project ID", "Commitment ID", "amount", "Cost Code", "line_item_id", "id", "created_at", "updated_at", "company", "origin_id.1", "origin_data", "standard_cost_code_id", "code", "parent", "sortable_code", "line_item_types", "wbs_code", "description", "extended_type", "holder", "line_item_type", "origin_id", "position", "project", "quantity", "total_amount", "extended_amount", "unit_cost", "currency_configuration", "_project_id", "_work_order_contract_id", "_work_order_contract_title", "pulled_at"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Reordered columns", {{"standard_cost_code_id", "Cost Code ID"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns 2", {"pulled_at", "_work_order_contract_title", "_project_id", "currency_configuration", "unit_cost", "extended_amount", "total_amount", "quantity", "project", "line_item_type", "holder", "extended_type", "wbs_code", "line_item_types"}),
  #"Expanded parent" = Table.ExpandRecordColumn(#"Removed columns", "parent", {"id"}, {"id.1"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Expanded parent", {"id.1", "code"}),
  #"Expanded company" = Table.ExpandRecordColumn(#"Removed columns 1", "company", {"id", "name"}, {"id.1", "name"}),
  #"Removed columns 2" = Table.RemoveColumns(#"Expanded company", {"id.1", "name"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns 2", {{"Cost Code ID", Int64.Type}}),
  #"Trimmed text" = Table.TransformColumns(#"Changed column type 1", {{"Commitment ID", each Text.Trim(Text.From(_)), type nullable text}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Trimmed text", {{"Commitment ID", Int64.Type}, {"id", Int64.Type}}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Changed column type 2", {"Project ID", "Cost Code ID", "Commitment ID", "amount", "Cost Code", "line_item_id", "id", "created_at", "updated_at", "origin_id.1", "origin_data", "sortable_code", "description", "origin_id", "position"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Reordered columns 1", {{"position", Int64.Type}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type 3", {"origin_id", "origin_data", "origin_id.1", "updated_at", "created_at"}),
  #"Renamed columns 3" = Table.RenameColumns(#"Removed columns 3", {{"line_item_id", "Line Item ID"}}),
  #"Reordered columns 2" = Table.ReorderColumns(#"Renamed columns 3", {"Project ID", "Cost Code ID", "Commitment ID", "Line Item ID", "amount", "Cost Code", "id", "sortable_code", "description", "position"}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Reordered columns 2", {{"Project ID", type text}, {"Cost Code ID", type text}, {"Commitment ID", type text}, {"Line Item ID", type text}, {"id", type text}, {"Cost Code", type text}, {"description", type text}, {"sortable_code", type text}}),
  #"Reordered columns 3" = Table.ReorderColumns(#"Changed column type 4", {"Project ID", "Cost Code ID", "Commitment ID", "_work_order_contract_id", "Line Item ID", "amount", "Cost Code", "id", "sortable_code", "description", "position"}),
  #"Renamed columns 4" = Table.RenameColumns(#"Reordered columns 3", {{"_work_order_contract_id", "Work Order Contract ID"}}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Renamed columns 4", {{"Work Order Contract ID", type text}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Changed column type 5", {"Cost Code", "sortable_code", "description", "position"})
in
  #"Removed columns 4";
[BindToDefaultDestination = true]
shared Dim_commitments = let
  Source = procore_work_order_line_item_silver_test,
  #"Removed duplicates" = Table.Distinct(Source, {"Commitment ID"}),
  #"Removed duplicates 1" = Table.Distinct(#"Removed duplicates", {"Commitment ID"}),
  #"Removed columns" = Table.RemoveColumns(#"Removed duplicates 1", {"id", "amount", "Line Item ID", "Work Order Contract ID", "Cost Code ID", "Project ID"}),
  #"Removed duplicates 2" = Table.Distinct(#"Removed columns", {"Commitment ID"})
in
  #"Removed duplicates 2";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
