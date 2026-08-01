[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[BindToDefaultDestination = true]
shared procore_submittals_silver = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_submittals_raw", ItemKind = "Table"]}[Data],
  #"Changed column type" = Table.TransformColumnTypes(#"Navigation 2", {{"closed_at", type datetime}, {"created_at", type datetime}, {"current_revision", type logical}, {"distributed_at", type datetime}, {"due_date", type date}, {"issue_date", type date}, {"submit_by", type date}, {"updated_at", type datetime}}),
  #"Parsed JSON" = Table.TransformColumns(#"Changed column type", {{"status", each Json.Document(_), type any}}),
  #"Expanded status" = Table.ExpandRecordColumn(#"Parsed JSON", "status", {"id", "name", "status"}, {"id.1", "name", "status.1"}),
  #"Renamed columns" = Table.RenameColumns(#"Expanded status", {{"name", "status"}}),
  #"Parsed JSON 3" = Table.TransformColumns(#"Renamed columns", {{"created_by", each Json.Document(_), type any}}),
  #"Expanded created_by" = Table.ExpandRecordColumn(#"Parsed JSON 3", "created_by", {"id", "name"}, {"id.4", "name.1"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Expanded created_by", {{"name.1", type text}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Changed column type 3", {{"name.1", "Created BY"}, {"id.4", "Created by ID"}, {"status", "Status"}}),
  #"Renamed columns 2" = Table.RenameColumns(#"Renamed columns 1", {{"project_id", "Project ID"}}),
  #"Renamed columns 5" = Table.RenameColumns(#"Renamed columns 2", {{"cost_code_id", "Cost Code ID"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 5", {"project_name", "type", "title", "submittal_workflow_template_applied_at", "submittal_workflow_template", "submittal_package", "submittal_manager"}),
  #"Renamed columns 6" = Table.RenameColumns(#"Removed columns 2", {{"status.1", "Submittal Status"}}),
  #"Changed column type 5" = Table.TransformColumnTypes(#"Renamed columns 6", {{"Submittal Status", type text}}),
  #"Reordered columns" = Table.ReorderColumns(#"Changed column type 5", {"Project ID", "Status", "Cost Code ID", "Submittal Status", "id", "actual_delivery_date", "approvers", "associated_attachments", "responsible_contractor", "ball_in_court", "closed_at", "created_at", "Created by ID", "Created BY", "current_revision", "custom_fields", "description", "distributed_at", "distribution_members", "drawing_ids", "due_date", "formatted_number", "issue_date", "last_distributed_submittal", "lead_time", "linked_drawing_ids", "location_id", "number", "private", "received_date", "received_from", "required_on_site_date", "revision", "scheduled_task", "specification_section", "id.1", "submit_by", "updated_at"}),
  #"Removed columns" = Table.RemoveColumns(#"Reordered columns", {"responsible_contractor"}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Removed columns", {"Project ID", "Status", "Cost Code ID", "Submittal Status", "id", "ball_in_court", "actual_delivery_date", "approvers", "associated_attachments", "closed_at", "created_at", "Created by ID", "Created BY", "current_revision", "custom_fields", "description", "distributed_at", "distribution_members", "drawing_ids", "due_date", "formatted_number", "issue_date", "last_distributed_submittal", "lead_time", "linked_drawing_ids", "location_id", "number", "private", "received_date", "received_from", "required_on_site_date", "revision", "scheduled_task", "specification_section", "id.1", "submit_by", "updated_at"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Reordered columns 1", {"approvers", "actual_delivery_date", "id.1", "received_from", "private", "linked_drawing_ids", "last_distributed_submittal", "lead_time", "drawing_ids", "distribution_members", "distributed_at", "custom_fields", "due_date", "ball_in_court", "associated_attachments", "closed_at", "formatted_number", "scheduled_task", "specification_section", "submit_by", "location_id", "issue_date"}),
  #"Replaced value" = Table.ReplaceValue(#"Removed columns 1", null, 0, Replacer.ReplaceValue, {"Cost Code ID"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Replaced value", {{"Status", type text}, {"Cost Code ID", type text}, {"id", type text}}),
  #"Extracted first characters" = Table.TransformColumns(#"Changed column type 1", {{"created_at", each Text.Start(Text.From(_), 9), type text}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Extracted first characters", {{"created_at", type date}}),
  #"Renamed columns 3" = Table.RenameColumns(#"Changed column type 2", {{"created_at", "Created At"}}),
  #"Changed column type 4" = Table.TransformColumnTypes(#"Renamed columns 3", {{"received_date", type date}, {"required_on_site_date", type date}}),
  #"Extracted first characters 1" = Table.TransformColumns(#"Changed column type 4", {{"updated_at", each Text.Start(Text.From(_), 9), type text}}),
  #"Changed column type 6" = Table.TransformColumnTypes(#"Extracted first characters 1", {{"updated_at", type date}}),
  #"Renamed columns 4" = Table.RenameColumns(#"Changed column type 6", {{"updated_at", "Updated At"}, {"description", "Description"}}),
  #"Changed column type 7" = Table.TransformColumnTypes(#"Renamed columns 4", {{"Project ID", type text}})
in
  #"Changed column type 7";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
