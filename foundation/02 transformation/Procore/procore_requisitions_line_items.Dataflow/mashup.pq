[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_requisition_line_items = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_requisition_line_items_raw", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"cost_code_id", "Cost Code ID"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"currency_configuration", "item_type"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns", {{"scheduled_value", Currency.Type}, {"total_completed_and_stored_to_date", Currency.Type}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type", {{"wbs_code", each Json.Document(_), type any}}),
  #"Expanded wbs_code" = Table.ExpandRecordColumn(#"Parsed JSON", "wbs_code", {"description", "flat_code", "id"}, {"description", "flat_code", "id.1"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Expanded wbs_code", {{"id.1", "WBS ID?"}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Renamed columns 1", {{"work_completed_from_previous_application", Currency.Type}}),
  #"Renamed columns 2" = Table.RenameColumns(#"Changed column type 1", {{"project_id", "Project ID"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns 2", {"id", "Project ID", "Cost Code ID", "description_of_work", "detail_line_item_id", "materials_moved", "materials_presently_stored", "materials_retainage_retained_moved", "materials_stored_retainage_currently_retained", "materials_stored_retainage_percent_this_period", "materials_stored_retainage_released_this_period", "position", "scheduled_value", "ssr_manual_override", "status", "subcontractor_claimed_amount", "total_completed_and_stored_to_date", "total_completed_and_stored_to_date_percent", "description", "flat_code", "WBS ID?", "work_completed_from_previous_application", "work_completed_retainage_from_previous_application", "work_completed_retainage_percent_this_period", "work_completed_retainage_released_this_period", "work_completed_retainage_retained_this_period", "work_completed_this_period", "requisition_id", "requisition_number", "requisition_status", "project_name"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Reordered columns", {{"subcontractor_claimed_amount", Currency.Type}, {"WBS ID?", type text}, {"id", type text}, {"Project ID", type text}, {"Cost Code ID", type text}, {"detail_line_item_id", type text}, {"requisition_id", type text}})
in
  #"Changed column type 2";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
