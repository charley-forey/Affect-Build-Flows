[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_commitment_change_orders = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_commitment_change_orders", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 2", {{"project_id", type text}, {"change_order_id", type text}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type", {{"raw_json", each Json.Document(_), type any}}),
  #"Expanded raw_json" = Table.ExpandRecordColumn(#"Parsed JSON", "raw_json", {"id", "batch_id", "billing_schedule_of_values_status", "change_order_change_reason", "contract_id", "created_at", "created_by", "currency_configuration", "custom_fields", "description", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "grand_total", "invoiced_date", "legacy_package_id", "legacy_request_id", "location_id", "number", "paid", "paid_date", "private", "received_from", "reference", "reviewed_at", "reviewed_by", "revision", "schedule_impact_amount", "signature_required", "signed_change_order_received_date", "status", "title", "type", "updated_at", "_project_id"}, {"id", "batch_id", "billing_schedule_of_values_status", "change_order_change_reason", "contract_id", "created_at", "created_by", "currency_configuration", "custom_fields", "description", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "grand_total", "invoiced_date", "legacy_package_id", "legacy_request_id", "location_id", "number", "paid", "paid_date", "private", "received_from", "reference", "reviewed_at", "reviewed_by", "revision", "schedule_impact_amount", "signature_required", "signed_change_order_received_date", "status", "title", "type", "updated_at", "_project_id"}),
  #"Removed columns" = Table.RemoveColumns(#"Expanded raw_json", {"batch_id", "change_order_change_reason", "created_at", "currency_configuration", "description"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"grand_total", Currency.Type}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Changed column type 1", {"_project_id", "pulled_at", "updated_at", "type", "custom_fields", "created_by"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns 1", {{"contract_id", "Work Order Contract ID"}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Renamed columns", {{"Work Order Contract ID", type text}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Changed column type 2", {{"project_id", "Procore Project ID"}, {"change_order_id", "Change Order ID"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 1", {"billing_schedule_of_values_status", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "legacy_request_id", "legacy_package_id", "invoiced_date", "location_id", "paid_date", "paid", "private", "received_from", "reference", "reviewed_at", "reviewed_by", "revision", "schedule_impact_amount", "signature_required", "signed_change_order_received_date"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Removed columns 2", {{"id", type text}, {"number", type text}, {"status", type text}, {"title", type text}})
in
  #"Changed column type 3";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
