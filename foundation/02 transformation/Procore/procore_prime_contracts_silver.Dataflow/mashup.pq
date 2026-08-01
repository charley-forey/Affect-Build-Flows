[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_prime_contracts_silver = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_prime_contracts_raw", ItemKind = "Table"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 2", {"type"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns", {{"retainage_percent", type number}}),
  #"Added custom" = Table.AddColumn(#"Changed column type", "Custom", each [retainage_percent] / 100),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Added custom", {{"Custom", Percentage.Type}}),
  #"Reordered columns" = Table.ReorderColumns(#"Changed column type 1", {"id", "accounting_method", "allow_change_orders_ssov", "allow_comments", "allow_markups", "allow_payment_applications", "allow_payments", "auto_approve_prefilled_requisitions_on_payapp", "change_order_level_of_detail", "contract_estimated_completion_date", "contract_start_date", "contractor", "created_at", "created_by", "currency_configuration", "description", "display_materials_retainage", "display_work_retainage", "enable_ssov", "exclusions", "executed", "grand_total", "inclusions", "number", "private", "Custom", "retainage_percent", "show_cost_code_on_pdf", "show_line_items_to_non_admins", "signed_contract_received_date", "status", "title", "updated_at", "vendor", "project_id", "project_name", "architect"}),
  #"Renamed columns" = Table.RenameColumns(#"Reordered columns", {{"Custom", "retainage_percent 2"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns", {"retainage_percent"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 1", {{"retainage_percent 2", "retainage_percent"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 1", {"private"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Removed columns 2", {{"contract_estimated_completion_date", type date}, {"contract_start_date", type date}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type 2", {"contractor"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Removed columns 3", {{"grand_total", Currency.Type}, {"signed_contract_received_date", type date}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Changed column type 3", {"accounting_method", "allow_change_orders_ssov", "allow_comments", "allow_markups", "allow_payment_applications", "allow_payments", "auto_approve_prefilled_requisitions_on_payapp", "change_order_level_of_detail"}),
  #"Extracted first characters" = Table.TransformColumns(#"Removed columns 4", {{"created_at", each Text.Start(_, 10), type text}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Extracted first characters", {{"created_at", type date}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 4", {"created_by", "currency_configuration", "description", "display_materials_retainage", "display_work_retainage", "enable_ssov", "exclusions"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 5", {{"grand_total", "Prime Contract Value"}}),
  #"Removed columns 6" = Table.RemoveColumns(#"Renamed columns 2", {"inclusions", "project_name"}),
  #"Extracted first characters 1" = Table.TransformColumns(#"Removed columns 6", {{"updated_at", each Text.Start(_, 10), type text}}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Extracted first characters 1", {{"updated_at", type date}}),
  #"Removed columns 7" = Table.RemoveColumns(#"Changed column type 5", {"title"}),
  #"Renamed columns 3" = Table.RenameColumns(#"Removed columns 7", {{"status", "Status"}}),
  #"Removed columns 8" = Table.RemoveColumns(#"Renamed columns 3", {"show_line_items_to_non_admins", "show_cost_code_on_pdf"}),
  #"Renamed columns 4" = Table.RenameColumns(#"Removed columns 8", {{"retainage_percent", "Retainage %"}}),
  #"Removed columns 9" = Table.RemoveColumns(#"Renamed columns 4", {"number", "architect"}),
  #"Renamed columns 5" = Table.RenameColumns(#"Removed columns 9", {{"project_id", "Project ID"}}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Renamed columns 5", {{"Project ID", type text}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type 6", {{"vendor", each Json.Document(_), type any}}),
  #"Renamed columns 6" = Table.RenameColumns(#"Parsed JSON", {{"updated_at", "Updated At"}, {"signed_contract_received_date", "Signed Contract Recieved Date"}, {"created_at", "Created At"}}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Renamed columns 6", {"id", "contract_estimated_completion_date", "contract_start_date", "Created At", "Updated At", "executed", "Prime Contract Value", "Retainage %", "Signed Contract Recieved Date", "Status", "vendor", "Project ID"}),
  #"Renamed columns 7" = Table.RenameColumns(#"Reordered columns 1", {{"executed", "Executed"}, {"contract_estimated_completion_date", "Estimated Completion Date"}, {"contract_start_date", "Start Date"}, {"id", "Prime Contract ID"}}),
  #"Reordered columns 2" = Table.ReorderColumns(#"Renamed columns 7", {"Prime Contract ID", "Project ID", "Estimated Completion Date", "Start Date", "Created At", "Updated At", "Executed", "Prime Contract Value", "Retainage %", "Signed Contract Recieved Date", "Status", "vendor"})
in
  #"Reordered columns 2";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
