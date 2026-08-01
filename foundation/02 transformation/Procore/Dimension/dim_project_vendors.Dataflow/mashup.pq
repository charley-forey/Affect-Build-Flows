[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared dim_procore_project_vendor = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_project_vendors_raw", ItemKind = "Table"]}[Data],
  #"Parsed JSON" = Table.TransformColumns(#"Navigation 2", {{"project_ids", each Json.Document(_), type any}}),
  #"Reordered columns" = Table.ReorderColumns(#"Parsed JSON", {"id", "abbreviated_name", "address", "attachments", "authorized_bidder", "business_id", "business_phone", "city", "company", "origin_id", "origin_data", "origin_code", "company_vendor", "country_code", "created_at", "email_address", "fax_number", "is_active", "is_connected", "labor_union", "license_number", "logo", "name", "non_union_prevailing_wage", "notes", "prequalified", "primary_contact", "project_ids", "state_code", "synced_to_erp", "trade_name", "union_member", "updated_at", "website", "zip", "project_id", "project_name"}),
  #"Expanded project_ids" = Table.ExpandListColumn(#"Reordered columns", "project_ids"),
  #"Filtered rows" = Table.SelectRows(#"Expanded project_ids", each ([name] <> "Affect")),
  #"Renamed columns 1" = Table.RenameColumns(#"Filtered rows", {{"name", "Vendor Name"}, {"id", "Procore Vendor ID"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 1", {"business_phone", "email_address", "city", "company", "country_code"}),
  #"Removed other columns" = Table.SelectColumns(#"Removed columns 2", {"Procore Vendor ID", "Vendor Name", "origin_id", "origin_data", "origin_code"}),
  #"Removed duplicates" = Table.Distinct(#"Removed other columns", {"Procore Vendor ID"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed duplicates", {{"Procore Vendor ID", type text}}),
  #"Replaced value" = Table.ReplaceValue(#"Changed column type", null, "0", Replacer.ReplaceValue, {"origin_code"}),
  #"Renamed columns" = Table.RenameColumns(#"Replaced value", {{"origin_code", "Sage Vendor ID"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"origin_data", "origin_id"}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Removed columns", {"Procore Vendor ID", "Sage Vendor ID", "Vendor Name"}),
  #"Filtered rows 1" = Table.SelectRows(#"Reordered columns 1", each ([Sage Vendor ID] <> "0"))
in
  #"Filtered rows 1";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
