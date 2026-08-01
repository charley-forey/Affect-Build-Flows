[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_requisitions_silver = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_requisitions_raw", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 2", {{"total_claimed_amount", Currency.Type}, {"requisition_end", type date}, {"requisition_start", type date}, {"billing_date", type date}}),
  #"Removed columns" = Table.RemoveColumns(#"Changed column type", {"currency_configuration", "payment_date"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns", {{"percent_complete", Percentage.Type}}),
  #"Reordered columns" = Table.ReorderColumns(#"Changed column type 1", {"attachments", "billing_date", "comment", "commitment_id", "number", "percent_complete", "vendor_id", "project_id", "period_id", "commitment_type", "contract_invoicing_method", "contract_name", "created_at", "created_by", "custom_fields", "deletable", "erp_status", "final", "id", "invoice_number", "invoice_type", "move_materials_to_previous_work_completed", "payment_summary", "previous_requisition_id", "requisition_end", "requisition_start", "status", "submitted_at", "summary", "total_claimed_amount", "updated_at", "vendor_name", "project_name"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Reordered columns", {"attachments"}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Removed columns 1", {"billing_date", "comment", "commitment_id", "number", "percent_complete", "vendor_id", "project_id", "period_id", "status", "commitment_type", "contract_invoicing_method", "contract_name", "created_at", "created_by", "custom_fields", "deletable", "erp_status", "final", "id", "invoice_number", "invoice_type", "move_materials_to_previous_work_completed", "payment_summary", "previous_requisition_id", "requisition_end", "requisition_start", "submitted_at", "summary", "total_claimed_amount", "updated_at", "vendor_name", "project_name"}),
  #"Removed columns 2" = Table.RemoveColumns(#"Reordered columns 1", {"custom_fields"}),
  #"Reordered columns 2" = Table.ReorderColumns(#"Removed columns 2", {"billing_date", "comment", "commitment_id", "number", "percent_complete", "total_claimed_amount", "vendor_id", "project_id", "period_id", "status", "payment_summary", "commitment_type", "contract_invoicing_method", "contract_name", "created_at", "created_by", "deletable", "erp_status", "final", "id", "invoice_number", "invoice_type", "move_materials_to_previous_work_completed", "previous_requisition_id", "requisition_end", "requisition_start", "submitted_at", "summary", "updated_at", "vendor_name", "project_name"}),
  #"Removed columns 3" = Table.RemoveColumns(#"Reordered columns 2", {"project_name", "vendor_name", "previous_requisition_id", "move_materials_to_previous_work_completed", "billing_date"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns 3", {{"total_claimed_amount", "Invoiced Amount ($)"}, {"percent_complete", "Percent Complete (%)"}, {"number", "Invoice Number"}, {"vendor_id", "Vendor ID"}, {"project_id", "Project ID"}, {"status", "Invoice Status"}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Renamed columns", {"deletable"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Removed columns 4", {{"submitted_at", type date}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 2", {"submitted_at"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 5", {{"invoice_number", "Vendor's Invoice Number"}}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Renamed columns 1", {{"commitment_id", type text}, {"Invoice Number", Int64.Type}, {"Vendor ID", type text}, {"Project ID", type text}, {"period_id", type text}, {"id", type text}})
in
  #"Changed column type 3";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
[BindToDefaultDestination = true]
shared Procore_commitmentsXvendor = let
  Source = procore_requisitions_silver,
  #"Removed other columns" = Table.SelectColumns(Source, {"commitment_id", "Vendor ID"}),
  #"Removed duplicates" = Table.Distinct(#"Removed other columns", {"commitment_id"})
in
  #"Removed duplicates";
