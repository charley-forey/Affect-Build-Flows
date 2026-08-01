[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;
shared AP_Open_Complete = let
  Source = Expenditure_AllTIme_raw,
  #"Sorted rows" = Table.Sort(Source, {{"Invoiced Date", Order.Descending}}),
  #"Filtered rows" = Table.SelectRows(#"Sorted rows", each ([Invoice Balance] <> 0)),
  #"Changed column type" = Table.TransformColumnTypes(#"Filtered rows", {{"Vendor_ID", type text}, {"Job Number", type text}})
in
  #"Changed column type";
shared AR_Open_Complete = let
  Source = Revenue_AllTime_raw,
  #"Removed columns" = Table.RemoveColumns(Source, {"recnum"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Removed columns", {"acri_u", "acrpmt(_idnum)", "acrpmt(recnum)", "actrec", "arivln(_idnum)", "arivln(recnum)", "artxdt(_idnum)", "artxdt(recnum)", "jobphs", "taxdst(taxdst)", "upddte"}),
  #"Filtered rows" = Table.SelectRows(#"Removed columns 1", each ([Invoice Balance] <> 0)),
  #"Changed column type" = Table.TransformColumnTypes(#"Filtered rows", {{"jobnum", type text}})
in
  #"Changed column type";
[BindToDefaultDestination = true]
shared Expenditure_AllTIme_raw = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "acpinv"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 1", {"_idnum", "invnum"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns", {{"vndnum", "Vendor_ID"}, {"dscrpt", "Description"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns", {"phsnum"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 1", {{"jobnum", "Job Number"}, {"pchord", "PO Number"}, {"ctcnum", "Contract Number"}, {"invdte", "Invoiced Date"}, {"duedte", "Due Date"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 1", {"payee2", "dscavl", "usrdf2", "usrdf1"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 2", {{"amtpad", "Amount Paid"}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Renamed columns 2", {{"Amount Paid", Currency.Type}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Changed column type", {"dsctkn"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Removed columns 3", {{"invttl", Currency.Type}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Changed column type 1", {"adjust", "freigh"}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Removed columns 4", {{"ttlpad", Currency.Type}, {"invbal", Currency.Type}}),
  #"Renamed columns 3" = Table.RenameColumns(#"Changed column type 2", {{"invbal", "Invoice Balance"}}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Renamed columns 3", {{"invnet", Currency.Type}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Changed column type 3", {"usrnme", "shpnum", "cmpamt", "usetax", "ntetxt", "hotlst", "gstamt", "hstamt", "qstamt", "pstamt", "hldrem", "hldbll", "hldamt", "subttl", "invamt", "insusr", "updusr", "apinte", "usedst", "usettl", "taxcde", "rcpamt", "slstax", "acpi_u", "acppmt(_idnum)", "taxdst", "scdpay(recnum)", "scdpay(_idnum)", "jobphs", "ca_tax", "apivln(recnum)", "apivln(_idnum)", "actrec", "actpay", "acppmt(recnum)"})
in
  #"Removed columns 5";
[BindToDefaultDestination = true]
shared Revenue_AllTime_raw = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "acrinv"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 1", {"_idnum"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns", {{"invdte", "Invoice Date"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns", {"phsnum", "refnum", "pchord", "taxdst", "usrdf1", "usrdf2", "dscavl", "slstax", "dsctkn"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 1", {{"amtpad", Currency.Type}}),
  #"Renamed columns 1" = Table.RenameColumns(#"Changed column type", {{"amtpad", "Amount Paid"}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Renamed columns 1", {{"invttl", Currency.Type}, {"invbal", Currency.Type}}),
  #"Renamed columns 2" = Table.RenameColumns(#"Changed column type 1", {{"invbal", "Invoice Balance"}}),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Renamed columns 2", {{"invnet", Currency.Type}, {"taxabl", Currency.Type}, {"nontax", Currency.Type}, {"ttlpad", Currency.Type}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type 2", {"usrnme", "imgfle", "ntetxt", "updusr", "insusr", "gstamt", "hstsbj", "hstamt", "invamt", "postyr", "hldbll", "hldrem", "pstsbj", "pstamt", "gstsbj", "hotlst", "subttl", "hldamt"}),
  #"Sorted rows" = Table.Sort(#"Removed columns 2", {{"Invoice Date", Order.Descending}})
in
  #"Sorted rows";
shared Payments = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "acppmt"]}[Data],
  #"Sorted rows" = Table.Sort(#"Navigation 1", {{"chkdte", Order.Descending}}),
  #"Removed columns" = Table.RemoveColumns(#"Sorted rows", {"_idnum", "_idref"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns", {{"amount", Currency.Type}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Changed column type", {"aplcrd", "dsctkn", "achbch", "insusr", "depdte", "updusr", "upddte"}),
  #"Expanded acpinv(_idref)" = Table.ExpandRecordColumn(#"Removed columns 1", "acpinv(_idref)", {"_idnum", "recnum", "invnum", "pchord", "ctcnum", "vndnum", "jobnum", "phsnum", "dscrpt", "invdte", "duedte", "refnum", "dscdte", "invtyp", "status", "payee2", "usrdf1", "usrdf2", "dscavl", "retain", "setpay", "amtpad", "dsctkn", "invttl", "adjust", "freigh", "ttlpad", "invbal", "invnet", "actper", "entdte", "lgrrec", "usrnme", "btcnum", "hotlst", "shpnum", "cmpamt", "usetax", "ntetxt", "vodrec", "subttl", "hldamt", "hldbll", "hldrem", "pstamt", "qstamt", "gstamt", "hstamt", "invamt", "slstax", "postyr", "taxcde", "rcpamt", "insdte", "insusr", "upddte", "updusr", "apinte", "usedst", "usettl", "acpi_u", "acppmt(_idnum)", "acppmt(recnum)", "actpay", "actrec", "apivln(_idnum)", "apivln(recnum)", "ca_tax", "jobphs", "scdpay(_idnum)", "scdpay(recnum)", "taxdst"}, {"_idnum", "recnum.1", "invnum", "pchord", "ctcnum", "vndnum", "jobnum", "phsnum", "dscrpt.1", "invdte", "duedte", "refnum", "dscdte", "invtyp", "status", "payee2", "usrdf1", "usrdf2", "dscavl", "retain", "setpay", "amtpad", "dsctkn", "invttl", "adjust", "freigh", "ttlpad", "invbal", "invnet", "actper.1", "entdte", "lgrrec.1", "usrnme", "btcnum", "hotlst", "shpnum", "cmpamt", "usetax", "ntetxt", "vodrec", "subttl", "hldamt", "hldbll", "hldrem", "pstamt", "qstamt", "gstamt", "hstamt", "invamt", "slstax", "postyr.1", "taxcde", "rcpamt", "insdte.1", "insusr", "upddte", "updusr", "apinte", "usedst", "usettl", "acpi_u", "acppmt(_idnum)", "acppmt(recnum)", "actpay", "actrec", "apivln(_idnum)", "apivln(recnum)", "ca_tax", "jobphs", "scdpay(_idnum)", "scdpay(recnum)", "taxdst"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Expanded acpinv(_idref)", {{"vndnum", "Vendor_ID"}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Renamed columns 1", {{"amtpad", Currency.Type}, {"invttl", Currency.Type}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type 1", {"recnum", "dscrpt"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 2", {{"actper", "Billing Period"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 2", {"lgrrec", "postyr", "insdte", "_idnum", "recnum.1"}),
  #"Filtered rows" = Table.SelectRows(#"Removed columns 3", each ([vodrec] = "")),
  #"Renamed columns 3" = Table.RenameColumns(#"Filtered rows", {{"invbal", "Invoice Balance"}, {"amtpad", "Amount Paid"}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Renamed columns 3", {"pchord", "ctcnum", "invnum"}),
  #"Renamed columns 4" = Table.RenameColumns(#"Removed columns 4", {{"jobnum", "Job Number"}, {"Vendor_ID", "Vendor ID"}}),
  #"Removed columns 5" = Table.RemoveColumns(#"Renamed columns 4", {"phsnum"}),
  #"Renamed columns 5" = Table.RenameColumns(#"Removed columns 5", {{"dscrpt.1", "Description"}, {"invdte", "Invoice Date"}, {"chkdte", "Payment Date"}, {"duedte", "Due Date"}}),
  #"Reordered columns" = Table.ReorderColumns(#"Renamed columns 5", {"chknum", "Payment Date", "Billing Period", "amount", "Vendor ID", "Job Number", "Description", "Invoice Date", "Due Date", "Amount Paid", "Invoice Balance", "status", "refnum", "dscdte", "invtyp", "payee2", "usrdf1", "usrdf2", "dscavl", "retain", "setpay", "dsctkn", "invttl", "adjust", "freigh", "ttlpad", "invnet", "actper.1", "entdte", "lgrrec.1", "usrnme", "btcnum", "hotlst", "shpnum", "cmpamt", "usetax", "ntetxt", "vodrec", "subttl", "hldamt", "hldbll", "hldrem", "pstamt", "qstamt", "gstamt", "hstamt", "invamt", "slstax", "postyr.1", "taxcde", "rcpamt", "insdte.1", "insusr", "upddte", "updusr", "apinte", "usedst", "usettl", "acpi_u", "acppmt(_idnum)", "acppmt(recnum)", "actpay", "actrec", "apivln(_idnum)", "apivln(recnum)", "ca_tax", "jobphs", "scdpay(_idnum)", "scdpay(recnum)", "taxdst", "acpinv(recnum)"}),
  #"Removed other columns" = Table.SelectColumns(#"Reordered columns", {"status", "Invoice Balance", "Amount Paid", "Due Date", "Invoice Date", "Description", "Job Number", "Vendor ID", "amount", "Billing Period", "Payment Date", "chknum"}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Removed other columns", {"status", "Invoice Balance", "Amount Paid", "Due Date", "Invoice Date", "chknum", "Description", "Job Number", "Vendor ID", "amount", "Billing Period", "Payment Date"}),
  #"Removed columns 6" = Table.RemoveColumns(#"Reordered columns 1", {"chknum"})
in
  #"Removed columns 6";
shared Reciepts = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "acrpmt"]}[Data],
  #"Sorted rows" = Table.Sort(#"Navigation 1", {{"chkdte", Order.Descending}}),
  #"Removed columns" = Table.RemoveColumns(#"Sorted rows", {"dscrpt", "_idnum", "_idref", "recnum", "chknum"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns", {{"actper", "Billing Period"}, {"amount", "Amount"}}),
  #"Changed column type" = Table.TransformColumnTypes(#"Renamed columns", {{"Amount", Currency.Type}, {"Billing Period", Int64.Type}}),
  #"Expanded acrinv(_idref)" = Table.ExpandRecordColumn(#"Changed column type", "acrinv(_idref)", {"jobnum"}, {"jobnum"}),
  #"Expanded acrinv(recnum)" = Table.ExpandRecordColumn(#"Expanded acrinv(_idref)", "acrinv(recnum)", {"invdte"}, {"invdte"}),
  #"Reordered columns" = Table.ReorderColumns(#"Expanded acrinv(recnum)", {"chkdte", "Billing Period", "Amount", "dsctkn", "lgrrec", "aplcrd", "postyr", "insdte", "insusr", "upddte", "updusr", "jobnum", "invdte"}),
  #"Removed columns 1" = Table.RemoveColumns(#"Reordered columns", {"lgrrec", "aplcrd", "insdte", "insusr", "postyr", "dsctkn", "upddte", "updusr"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 1", {{"jobnum", "Job Number"}, {"invdte", "Invoice Date"}, {"chkdte", "Payment Date"}}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Renamed columns 1", {"Invoice Date", "Payment Date", "Billing Period", "Job Number", "Amount"})
in
  #"Reordered columns 1";
[BindToDefaultDestination = true]
shared Dim_Sage_Vendors = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "actpay"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 1", {"_idnum", "paymth", "updusr", "elc199", "eml199", "inactv", "utwarn", "eftrtn", "eftact", "eftcde", "efteml", "taxcde", "prente", "eftpay", "acheml", "bnkact", "rtnmbr", "eftiid"}),
  #"Sorted rows" = Table.Sort(#"Removed columns", {{"vndnme", Order.Ascending}}),
  #"Renamed columns" = Table.RenameColumns(#"Sorted rows", {{"vndnme", "Vendor Name"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns", {"ownnme", "addrs1", "addrs2", "ctynme", "state_", "zipcde", "fedidn", "steidn", "resnum", "actnum", "licnum", "usrdf1", "usrdf2", "phnnum", "pagnum", "faxnum", "cllphn", "homphn", "e_mail", "dscrte", "dscdte", "duedte", "lgrdft", "cdedft", "typdft", "begbal", "wrndft", "stsdft"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 1", {{"endbal", Currency.Type}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Changed column type", {"vndtyp", "prt199", "minsts", "taxdst", "intrnl", "cmprte", "utxrte", "hotlst", "insusr", "tolprc", "tolexc", "dirdep", "rfpdsc", "sepchk", "contct", "pomesg", "toltyp", "tolamt", "rfptyp", "dupchk", "imgfle", "ntetxt", "ordtyp", "orddsc", "contyp", "condsc"}),
  #"Expanded acpinv" = Table.ExpandTableColumn(#"Removed columns 2", "acpinv", {"_idnum", "vndnum"}, {"_idnum", "vndnum"}),
  #"Removed duplicates" = Table.Distinct(#"Expanded acpinv", {"shtnme"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed duplicates", {{"recnum", "Vendor ID"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 1", {"shtnme", "acttyp", "insdte", "upddte", "_idnum", "endbal"}),
  #"Reordered columns" = Table.ReorderColumns(#"Removed columns 3", {"Vendor ID", "Vendor Name", "vndnum", "actp_u", "actrec(recnum)", "aiafrm", "actrec(recnum) 2", "aialin", "ca_tax", "coresp", "cstcde", "csttyp", "eqpcst", "eqpmnt", "fdrpsb", "jobcst", "lgract", "lgrtrn", "lonfrm", "lonlin", "pchord", "pchtyp", "pclsln(recnum)", "pclsln(recnum) 2", "plnrcd", "plnrcv", "privnd(_idnum)", "privnd(recnum)", "rccpay", "rcctrn", "reqinf", "reqprp", "reqtyp", "sbcgln", "sbctyp", "scdlen(recnum)", "scdlen(recnum) 2", "schsub", "srvsch", "subcon", "submtl", "taxdst(taxdst)", "tkflin", "trnmtl", "untbll", "vndbal(_idnum)", "vndbal(recnum)", "vndcnt(_idnum)", "vndcnt(recnum)", "vndcrt(_idnum)", "vndcrt(recnum)", "vndprc", "vndrmt(_idnum)", "vndrmt(recnum)", "vndtyp(vndtyp)", "vndytd(_idnum)", "vndytd(recnum)"}),
  #"Removed other columns" = Table.SelectColumns(#"Reordered columns", {"Vendor ID", "Vendor Name", "vndnum"}),
  #"Added custom" = Table.AddColumn(#"Removed other columns", "Entity", each "Build"),
  #"Reordered columns 1" = Table.ReorderColumns(#"Added custom", {"Entity", "Vendor ID", "Vendor Name", "vndnum"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Reordered columns 1", {{"Vendor ID", type text}})
in
  #"Changed column type 1";
[BindToDefaultDestination = true]
shared Dim__Sage_Projects = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  #"Navigation 1" = Source{[Schema = "dbo", Item = "actrec"]}[Data],
  #"Removed columns" = Table.RemoveColumns(#"Navigation 1", {"_idnum", "shtnme", "clnnum", "contct", "addrs1", "addrs2", "ctynme", "state_"}),
  #"Reordered columns" = Table.ReorderColumns(#"Removed columns", {"recnum", "jobnme", "zipcde", "phnnum", "faxnum", "lender", "achtct", "sprvsr", "slsemp", "estemp", "usrdf1", "usrdf2", "lcltax", "slstax", "lgract", "dptmnt", "dscdte", "duedte", "dsccnt", "finchg", "retain", "cntrct", "begbal", "endbal", "biddte", "plnrcv", "actbid", "ctcdte", "prelen", "sttdte", "cmpdte", "lenfld", "lenrls", "jobtyp", "status", "pstwip", "crtfid", "connum", "pchord", "imgfle", "csttym", "csttyl", "csttye", "csttys", "csttyo", "usrcs6", "usrcs7", "usrcs8", "usrcs9", "ntetxt", "export", "lotclr", "lotprm", "plnprc", "actprc", "estdte", "actdte", "lotnum", "modnme", "sqarft", "usrlst", "catxex", "pstexm", "insdte", "insusr", "upddte", "updusr", "inactv", "fedsck", "stmeml", "ncrtck", "rtejob", "rtervw", "county", "fednum", "stenum", "awddte", "strdte", "dtecmp", "pctcmp", "typwrk", "subcnt", "prmnme", "prmadd", "prmcty", "prmste", "prmzip", "prmphn", "prmeml", "acpinv", "acrinv", "actpay(achtct)", "actpay(lender)", "actr_u", "aiafrm", "biditm(_idnum)", "biditm(recnum)", "budget", "coresp", "cstcmp", "dlypyr", "dptmnt(dptmnt)", "employ(estemp)", "employ(slsemp)", "employ(sprvsr)", "emptme", "eqprvw", "export(_idnum)", "export(recnum)", "fldrpt", "hrscmp", "invalc", "jobcnt(_idnum)", "jobcnt(recnum)", "jobcst", "jobpgp(_idnum)", "jobpgp(recnum)", "jobphs(_idnum)", "jobphs(recnum)", "jobtyp(jobtyp)", "lgract(lgract)", "loctax", "lonfrm", "pchlst", "pchord(recnum)", "plnrcd", "prelen(_idnum)", "prelen(recnum)", "prmchg", "propsl", "ptotkf", "rcapjb", "rcarjb", "rccjob", "rccpay", "rccrec", "reccln", "remids", "reqinf", "reqprp", "scdlen(_idnum)", "scdlen(recnum)", "schedl", "schprd", "srvinv", "subcon", "submtl", "taxdst", "timmat", "tmcdln", "trnmtl", "untbll", "untcmp", "untlin", "untprp", "vndcrt"}),
  #"Removed other columns" = Table.SelectColumns(#"Reordered columns", {"recnum", "jobnme"}),
  #"Added custom" = Table.AddColumn(#"Removed other columns", "Entity", each "Build"),
  #"Reordered columns 1" = Table.ReorderColumns(#"Added custom", {"Entity", "recnum", "jobnme"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Reordered columns 1", {{"recnum", type text}})
in
  #"Changed column type";
[BindToDefaultDestination = true]
shared AR_Open = let
  Source = AR_Open_Complete,
  #"Filtered rows" = Table.SelectRows(Source, each ([status] = 1)),
  #"Reordered columns" = Table.ReorderColumns(#"Filtered rows", {"Invoice Date", "invnum", "jobnum", "dscrpt", "duedte", "dscdte", "invtyp", "status", "retain", "Amount Paid", "invttl", "Invoice Balance", "invnet", "taxabl", "actper", "lgrrec", "nontax", "entdte", "ttlpad", "vodrec", "insdte"}),
  #"Renamed columns" = Table.RenameColumns(#"Reordered columns", {{"dscrpt", "Description"}, {"duedte", "Due Date"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"dscdte", "invtyp", "status"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns", {{"invttl", "Invoice Total"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 1", {"taxabl"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 1", {{"actper", "Billing Period"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 2", {"invnum"}),
  #"Renamed columns 3" = Table.RenameColumns(#"Removed columns 2", {{"jobnum", "Job Number"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 3", {"retain", "invnet"}),
  #"Reordered columns 1" = Table.ReorderColumns(#"Removed columns 3", {"Invoice Date", "Job Number", "Description", "Due Date", "Billing Period", "Amount Paid", "Invoice Total", "Invoice Balance", "lgrrec", "nontax", "entdte", "ttlpad", "vodrec", "insdte"}),
  #"Removed columns 4" = Table.RemoveColumns(#"Reordered columns 1", {"lgrrec", "nontax", "entdte", "ttlpad", "vodrec", "insdte"}),
  #"Added custom" = Table.AddColumn(#"Removed columns 4", "Days Aged", each Duration.Days(Date.From(DateTime.LocalNow()) - Date.From([Invoice Date]))),
  #"Added custom 1" = Table.AddColumn(#"Added custom", "Aging Bucket", each if [Days Aged] <= 30 then "1-30"
  else if [Days Aged] <= 60 then "31-60"
  else if [Days Aged] <= 90 then "61-90"
  else "90+"),
  #"Reordered columns 2" = Table.ReorderColumns(#"Added custom 1", {"Invoice Date", "Job Number", "Description", "Due Date", "Billing Period", "Amount Paid", "Invoice Total", "Invoice Balance", "Aging Bucket", "Days Aged"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Reordered columns 2", {{"Aging Bucket", type text}, {"Days Aged", Int64.Type}}),
  #"Added custom 2" = Table.AddColumn(#"Changed column type", "Entity", each "Build"),
  #"Reordered columns 3" = Table.ReorderColumns(#"Added custom 2", {"Entity", "Invoice Date", "Job Number", "Description", "Due Date", "Billing Period", "Amount Paid", "Invoice Total", "Invoice Balance", "Aging Bucket", "Days Aged"}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Reordered columns 3", {{"Job Number", type text}})
in
  #"Changed column type 1";
[BindToDefaultDestination = true]
shared AP_Open = let
  Source = AP_Open_Complete,
  #"Removed columns" = Table.RemoveColumns(Source, {"recnum", "invtyp", "setpay", "Amount Paid", "ttlpad", "vodrec", "upddte"}),
  #"Filtered rows 1" = Table.SelectRows(#"Removed columns", each ([status] = 1)),
  #"Sorted rows" = Table.Sort(#"Filtered rows 1", {{"Invoiced Date", Order.Ascending}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Sorted rows", {"insdte", "lgrrec", "entdte"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns 1", {{"actper", "Billing Period"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns", {"status", "dscdte", "refnum", "Contract Number", "PO Number", "retain"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 2", {{"invttl", "Invoice Total"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 1", {"invnet", "btcnum", "postyr"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 3", {{"Billing Period", Int64.Type}}),
  #"Changed column type 1" = Table.TransformColumnTypes(#"Changed column type", {{"Invoiced Date", type date}}),
  #"Added custom" = Table.AddColumn(#"Changed column type 1", "Days Aged", each Duration.Days(Date.From(DateTime.LocalNow()) - Date.From([Invoiced Date]))),
  #"Added custom 1" = Table.AddColumn(#"Added custom", "Aging Bucket", each if [Days Aged] <= 30 then "1-30"
  else if [Days Aged] <= 60 then "31-60"
  else if [Days Aged] <= 90 then "61-90"
  else "90+"),
  #"Changed column type 2" = Table.TransformColumnTypes(#"Added custom 1", {{"Days Aged", Int64.Type}, {"Aging Bucket", type text}}),
  #"Reordered columns" = Table.ReorderColumns(#"Changed column type 2", {"Vendor_ID", "Job Number", "Description", "Invoiced Date", "Due Date", "Billing Period", "Invoice Total", "Invoice Balance", "Aging Bucket", "Days Aged"}),
  #"Added custom 2" = Table.AddColumn(#"Reordered columns", "Entity", each "Build"),
  #"Reordered columns 1" = Table.ReorderColumns(#"Added custom 2", {"Entity", "Vendor_ID", "Job Number", "Description", "Invoiced Date", "Due Date", "Billing Period", "Invoice Total", "Invoice Balance", "Aging Bucket", "Days Aged"}),
  #"Changed column type 3" = Table.TransformColumnTypes(#"Reordered columns 1", {{"Job Number", type text}, {"Vendor_ID", type text}})
in
  #"Changed column type 3";
shared DefaultDestination = Lakehouse.Contents([EnableFolding = false]){[workspaceId = "1f7caed6-f88a-4e52-bc83-9a498a165301"]}[Data]{[lakehouseId = "2e05dca7-ff80-4646-b711-6681dd4993e1"]}[Data];
[BindToDefaultDestination = true]
shared Revenue_AllTime = let
  Source = Revenue_AllTime_raw,
  #"Filtered rows" = Table.SelectRows(Source, each ([vodrec] = 0)),
  #"Removed columns" = Table.RemoveColumns(#"Filtered rows", {"recnum"}),
  #"Renamed columns" = Table.RenameColumns(#"Removed columns", {{"dscrpt", "Description"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns", {"invnum"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns 1", {{"jobnum", "Job Number"}, {"duedte", "Due Date"}}),
  #"Removed columns 2" = Table.RemoveColumns(#"Renamed columns 1", {"dscdte", "invtyp", "retain"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 2", {{"invttl", "Invoice Total"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 2", {"invnet", "taxabl"}),
  #"Renamed columns 3" = Table.RenameColumns(#"Removed columns 3", {{"actper", "Billing Period"}}),
  #"Removed columns 4" = Table.RemoveColumns(#"Renamed columns 3", {"lgrrec", "nontax", "entdte", "ttlpad", "vodrec"}),
  #"Removed other columns" = Table.SelectColumns(#"Removed columns 4", {"Billing Period", "Invoice Balance", "Invoice Total", "Amount Paid", "status", "Due Date", "Description", "Job Number", "Invoice Date"}),
  #"Removed columns 5" = Table.RemoveColumns(#"Removed other columns", {"status"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 5", {{"Job Number", type text}})
in
  #"Changed column type";
[BindToDefaultDestination = true]
shared Expenditure_AllTIme = let
  Source = Expenditure_AllTIme_raw,
  #"Filtered rows" = Table.SelectRows(Source, each ([vodrec] = "")),
  #"Renamed columns" = Table.RenameColumns(#"Filtered rows", {{"actper", "Billing Period"}}),
  #"Removed columns" = Table.RemoveColumns(#"Renamed columns", {"invnet", "recnum", "PO Number", "Contract Number"}),
  #"Renamed columns 1" = Table.RenameColumns(#"Removed columns", {{"Vendor_ID", "Vendor ID"}}),
  #"Removed columns 1" = Table.RemoveColumns(#"Renamed columns 1", {"refnum", "dscdte", "invtyp"}),
  #"Removed columns 2" = Table.RemoveColumns(#"Removed columns 1", {"status", "retain", "setpay"}),
  #"Renamed columns 2" = Table.RenameColumns(#"Removed columns 2", {{"invttl", "Invoice Total"}}),
  #"Removed columns 3" = Table.RemoveColumns(#"Renamed columns 2", {"ttlpad", "entdte", "upddte", "insdte", "postyr", "vodrec", "btcnum", "lgrrec"}),
  #"Changed column type" = Table.TransformColumnTypes(#"Removed columns 3", {{"Vendor ID", type text}, {"Job Number", type text}, {"Billing Period", type text}})
in
  #"Changed column type";
