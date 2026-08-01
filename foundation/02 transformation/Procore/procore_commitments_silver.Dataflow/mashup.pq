[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_commitments_silver_2 = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_commitments_raw", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 2", {{"approved_change_orders", Currency.Type}, {"contract_date", type date}, {"draft_change_orders_amount", Currency.Type}, {"grand_total", Currency.Type}, {"pending_revised_contract", Currency.Type}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type", {{"project", each Json.Document(_), type any}}),
  #"Expanded project" = Table.ExpandRecordColumn(#"Parsed JSON", "project", {"id", "name", "origin_data", "origin_id"}, {"id.1", "name", "origin_data", "origin_id"}),
  #"Renamed columns" = Table.RenameColumns(#"Expanded project", {{"id.1", "Project ID"}, {"name", "Project Name"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"origin_data", "origin_id"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"remaining_balance_outstanding", Currency.Type}, {"revised_contract", Currency.Type}, {"signed_contract_received_date", type date}, {"total_payments", Currency.Type}, {"total_requisitions_amount", Currency.Type}}),
  #"Parsed JSON 1" = Table.TransformColumns(#"Changed column type 1", {{"vendor", each Json.Document(_), type any}}),
  #"Expanded vendor" = Table.ExpandRecordColumn(#"Parsed JSON 1", "vendor", {"id", "company", "origin_data", "origin_id"}, {"id.1", "company", "origin_data", "origin_id"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Expanded vendor", {{"id.1", "Vendor ID"}, {"company", "Vendor Name"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 1", {"origin_data", "bill_to_address", "ship_to_address", "ship_via"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Removed columns 1", {{"retainage_percent", type number}}),
  #"Added custom" = Table.AddColumn(#"Changed column type 2", "Custom", each [retainage_percent] / 100),
  #"Removed columns 2" = Table.RemoveColumns(#"Added custom", {"retainage_percent"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 2", {{"Custom", "retainage_percent"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns 2", {"id", "accounting_method", "actual_completion_date", "allow_change_orders_ssov", "approved_change_orders", "billing_schedule_of_values_status", "contract_date", "contract_estimated_completion_date", "contract_start_date", "created_at", "created_by_id", "currency_configuration", "custom_fields", "description", "draft_change_orders_amount", "enable_ssov", "exclusions", "executed", "grand_total", "has_change_order_packages", "has_potential_change_orders", "inclusions", "issued_on_date", "number", "pending_change_orders", "pending_revised_contract", "percentage_paid", "private", "Project ID", "Project Name", "remaining_balance_outstanding", "retainage_percent", "requisitions_are_enabled", "revised_contract", "show_line_items_to_non_admins", "signed_contract_received_date", "status", "title", "total_draw_requests_amount", "total_payments", "total_requisitions_amount", "updated_at", "Vendor ID", "Vendor Name", "origin_id", "project_id", "project_name", "commitment_type", "assignee", "delivery_date", "payment_terms"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Reordered columns", {{"retainage_percent", Percentage.Type}}),
  #"Renamed columns 3" = Table.RenameColumns(#"Changed column type 3", {{"id", "Commitment ID"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 3", {"currency_configuration", "custom_fields", "description"}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Removed columns 3", {{"issued_on_date", type date}, {"pending_change_orders", Currency.Type}}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Changed column type 4", {{"percentage_paid", type number}}),
  #"Added custom 1" = Table.AddColumn(#"Changed column type 5", "Custom", each [percentage_paid] / 100),
  #"Reordered columns 1" = Table.ReorderColumns(#"Added custom 1", {"Commitment ID", "accounting_method", "actual_completion_date", "allow_change_orders_ssov", "approved_change_orders", "billing_schedule_of_values_status", "contract_date", "contract_estimated_completion_date", "contract_start_date", "created_at", "created_by_id", "draft_change_orders_amount", "enable_ssov", "exclusions", "executed", "grand_total", "has_change_order_packages", "has_potential_change_orders", "inclusions", "issued_on_date", "number", "pending_change_orders", "pending_revised_contract", "Custom", "percentage_paid", "private", "Project ID", "Project Name", "remaining_balance_outstanding", "retainage_percent", "requisitions_are_enabled", "revised_contract", "show_line_items_to_non_admins", "signed_contract_received_date", "status", "title", "total_draw_requests_amount", "total_payments", "total_requisitions_amount", "updated_at", "Vendor ID", "Vendor Name", "origin_id", "project_id", "project_name", "commitment_type", "assignee", "delivery_date", "payment_terms"}),
  #"Removed columns 4" = Table.RemoveColumns(#"Reordered columns 1", {"percentage_paid"}),
  #"Renamed columns 4" = Table.RenameColumns(#"Removed columns 4", {{"Custom", "percentage_paid"}}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Renamed columns 4", {{"percentage_paid", Percentage.Type}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 6", {"private"}),
  #"Added custom 2" = Table.AddColumn(#"Removed columns 5", "Custom", each "test")
in
  #"Added custom 2";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
