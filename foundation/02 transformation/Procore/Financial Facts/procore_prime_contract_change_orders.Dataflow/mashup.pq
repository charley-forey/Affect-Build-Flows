[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_prime_change_orders = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_prime_change_orders", ItemKind = "Table"]}[Data],
  #"Renamed columns" = Table.RenameColumns(#"Navigation 2", {{"project_id", "Project ID"}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Renamed columns", {{"Project ID", type text}}),
  #"Removed columns" = Table.RemoveColumns(#"Changed column type", {"project_name"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"change_order_id", type text}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Changed column type 1", {{"change_order_id", "Change Order ID"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 1", {"pulled_at"}),
  #"Parsed JSON" = Table.TransformColumns(#"Removed columns 1", {{"raw_json", each Json.Document(_), type any}}),
  #"Expanded raw_json" = Table.ExpandRecordColumn(#"Parsed JSON", "raw_json", {"id", "batch_id", "billing_schedule_of_values_status", "change_order_change_reason", "contract_id", "created_at", "created_by", "currency_configuration", "custom_fields", "description", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "grand_total", "invoiced_date", "legacy_package_id", "legacy_request_id", "location_id", "number", "paid", "paid_date", "private", "received_from", "reference", "reviewed_at", "reviewed_by", "revised_substantial_completion_date", "revision", "schedule_impact_amount", "signature_required", "signed_change_order_received_date", "status", "title", "type"}, {"id", "batch_id", "billing_schedule_of_values_status", "change_order_change_reason", "contract_id", "created_at", "created_by", "currency_configuration", "custom_fields", "description", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "grand_total", "invoiced_date", "legacy_package_id", "legacy_request_id", "location_id", "number", "paid", "paid_date", "private", "received_from", "reference", "reviewed_at", "reviewed_by", "revised_substantial_completion_date", "revision", "schedule_impact_amount", "signature_required", "signed_change_order_received_date", "status", "title", "type"}),
  #"Removed columns 2" = Table.RemoveColumns(#"Expanded raw_json", {"id", "billing_schedule_of_values_status"}),
  #"Expanded change_order_change_reason" = Table.ExpandRecordColumn(#"Removed columns 2", "change_order_change_reason", {"change_reason"}, {"change_reason"}),
  #"Removed columns 3" = Table.RemoveColumns(#"Expanded change_order_change_reason", {"change_reason"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 3", {{"contract_id", "Contract ID"}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Renamed columns 2", {{"Contract ID", type text}}),
  #"Expanded created_by" = Table.ExpandRecordColumn(#"Changed column type 2", "created_by", {"id", "name"}, {"id", "name"}),
  #"Removed columns 4" = Table.RemoveColumns(#"Expanded created_by", {"name", "id", "currency_configuration", "custom_fields", "description", "designated_reviewer", "due_date", "enable_ssov", "executed", "field_change", "legacy_request_id", "legacy_package_id"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Removed columns 4", {{"grand_total", Currency.Type}}),
  #"Renamed columns 3" = Table.RenameColumns(#"Changed column type 3", {{"grand_total", "CO Value $"}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Renamed columns 3", {"location_id", "private", "received_from", "reference", "type", "title"}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Removed columns 5", {{"status", type text}}),
  #"Removed columns 6" = Table.RemoveColumns(#"Changed column type 4", {"signed_change_order_received_date", "signature_required", "revision", "revised_substantial_completion_date", "schedule_impact_amount", "reviewed_by", "reviewed_at", "paid_date", "paid", "invoiced_date"}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Removed columns 6", {{"batch_id", type text}}),
  #"Extracted first characters" = Table.TransformColumns(#"Changed column type 5", {{"created_at", each Text.Start(Text.From(_), 10), type text}}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Extracted first characters", {{"created_at", type date}}),
  #"Renamed columns 4" = Table.RenameColumns(#"Changed column type 6", {{"created_at", "Date Created"}}),
  #"Changed column type 7" = Table.TransformColumnTypes(#"Renamed columns 4", {{"number", Int64.Type}})
in
  #"Changed column type 7";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
