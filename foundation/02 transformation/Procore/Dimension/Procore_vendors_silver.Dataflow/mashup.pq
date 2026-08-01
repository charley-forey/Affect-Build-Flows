[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared procore_vendors_raw = let
  Source = Lakehouse.Contents(null),
  Navigation = Source{[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data],
  #"Navigation 1" = Navigation{[lakehouseId = "4256b1ed-3884-4e26-96b5-aac4d8e6281f"]}[Data],
  #"Navigation 2" = #"Navigation 1"{[Id = "procore_vendors_raw", ItemKind = "Table"]}[Data]
in
  #"Navigation 2";
