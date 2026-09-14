# Sage 100 Contractor — complete extracted reference

Everything this repo knows about the Sage 100 Contractor database: tables, columns, keys,
types, the silver/gold layers built on top, and the measured values. Compiled from the four
places the knowledge actually lives (see [Sources](#sources) at the end).

**Sage publishes no table schema for this product.** Across 2,023 help topics and five PDF
guides, exactly one physical table name appears (`CMPANY`). Everything below is reconstructed
from production Power Query, our own dataflow, and measurements against live data — not from
vendor documentation.

---

## 1. Connection

| Fact | Value |
|---|---|
| Server / instance | `NC-AFFECT-1\SAGE100CON` (on-premises) |
| Database | `Affect Group` — **not** `ABMI`; the NTC handoff document is wrong |
| Schema | `dbo` (the only schema the gateway connection exposes) |
| Auth | SQL Server auth, login `FabricReader`, read-only |
| Connector | Native SQL Server (`Sql.Database`). **ODBC is a dead end** — that guidance is for the pre-SQL FoxPro 2.6 era |
| Gateway | On-premises data gateway `1e798beb-…`, datasource `835e72c8-…` (`nc-affect-1\sage100con;Affect Group`) |
| Logon trigger | Sage runs a SQL Server logon trigger with an application-name allow-list. `Mashup Engine (TridentDataflowNative)` passes; `.Net SqlClient Data Provider` is **blocked** (error 17892) despite being listed in §9 of the handoff. Diagnostic: Event ID 17063 in the Application log on `NC-AFFECT-1` |
| Catalogue discovery | **Not possible through this connection.** `INFORMATION_SCHEMA.TABLES` fails with `Expression.Error 10061` — the connection exposes `dbo` objects only, not the catalogue views |

### The authoritative queries, for whoever has direct DB access

```sql
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM   INFORMATION_SCHEMA.TABLES
ORDER  BY TABLE_SCHEMA, TABLE_NAME;

SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM   INFORMATION_SCHEMA.COLUMNS
ORDER  BY TABLE_NAME, ORDINAL_POSITION;
```

Neither has ever been run. Everything in this document is what we reconstructed instead.

---

## 2. Naming conventions

Consistent enough to predict table and column names you have not seen.

- **Six lowercase characters, vowels dropped.** `acpinv` = **ac**counts **p**ayable
  **inv**oice. `arivln` = **AR** **inv**oice **l**i**n**e. `vndnme` = vendor name,
  `jobnum` = job number, `invdte` = invoice date, `dscrpt` = description,
  `extprc` = extended price, `amtpad` = amount paid, `hldamt` = hold (retainage) amount.
- **`ac[p|r]` prefix** = accounts payable / receivable. **`act` prefix** = *master* record
  (`actpay` = vendor master, `actrec` = job master). These are **not** transaction tables —
  easy to misread.
- **`…ivln` suffix** = invoice line / detail table.
- **Keys.** Every table carries `_idnum` and `recnum`. `recnum` is the visible business key;
  `_idnum` is the internal surrogate. Line tables carry `_idref` pointing at the parent's
  `_idnum` — see [§5 Keys](#5-keys-and-joins-verified).
- **Audit columns are uniform:** `insdte` / `insusr` (inserted), `upddte` / `updusr` (updated).
- **User-defined columns:** `usrdf1`, `usrdf2`, `usrnme`, `usrcs6`–`usrcs9`.
- **Navigation properties.** The SQL Server connector surfaces foreign keys as pseudo-columns
  named `table(key)`, e.g. `apivln(recnum)` on `acpinv`. **They are not selectable columns** —
  they are relationship handles. They are also the only way we learned the names of tables we
  have never queried ([§8](#8-tables-known-only-by-foreign-key)).

### The header/detail rule, from Sage's own docs

> In windows such as **4-3 Vendor Payments**, **3-5 Jobs**, or **3-3-1 Cash Receipts** a
> single database table exists, containing all the information. In other windows such as
> **4-2 Payable Invoices** or **3-2 Receivable Invoices**, there are two database tables.
> When Sage 100 Contractor uses two tables to store data, the first table stores information
> from the text boxes and lists and the second table stores data from the grid.

So: invoices are header + detail (`acpinv`/`apivln`, `acrinv`/`arivln`); payments, jobs and
cash receipts are single-table.

---

## 3. The eight tables we extract

Landed by `CD_Sage_Ingest` into `CD_Bronze_Lakehouse/Tables/dbo` as `cd_bronze_sage_*`.
Row counts measured on the first successful run, **2026-08-25 09:25 UTC**.

| Table | Sage screen | Holds | Rows | In the old dataflow? |
|---|---|---|---:|---|
| `actrec` | 3-5 Jobs | **Job / project master** — the spine | 27 | yes |
| `actpay` | 4-4 Vendors | Vendor master (payable accounts) | 1,080 | yes |
| `acrinv` | 3-2 Receivable Invoices | AR invoice **headers** | 148 | yes |
| **`arivln`** | 3-2 (grid) | **AR invoice lines** | **258** | **no** |
| `acrpmt` | 3-3-1 Cash Receipts | AR payments / cash receipts | 86 | yes |
| `acpinv` | 4-2 Payable Invoices | AP invoice **headers** | 871 | yes |
| **`apivln`** | 4-2 (grid) | **AP invoice lines** | **901** | **no** |
| `acppmt` | 4-3 Vendor Payments | AP payments | 656 | yes |

**4,027 rows total.** AR line value **$25,613,659.66**; AP line value **$15,509,381.78**.

The two line tables are the point of the exercise. The pre-existing `Build_Sage_Test`
dataflow does not merely omit them — it explicitly strips their pointer columns
(`"arivln(recnum)"`, `"apivln(_idnum)"` etc. appear in `Table.RemoveColumns`). Nobody at
Affect had ever queried line-level Sage data.

---

## 4. Columns by table

> **Observed, not exhaustive.** These lists are the union of columns named in production
> Power Query (dropped, renamed or retyped) and columns read by our silver SQL. A column
> missing here only means no query has ever touched it. `INFORMATION_SCHEMA` is still the
> authority; it has never been runnable.
>
> Types marked ✅ come from SQL Server via the lakehouse and are trustworthy. Types marked ~
> come from the semantic model's interpretation and are indicative only.

### `dbo.actrec` — Job / project master (screen 3-5)

131 scalar columns observed. The spine: every invoice's `jobnum` points here.

```
_idnum    achtct    actbid    actdte    actprc    actr_u    addrs1    addrs2
aiafrm    awddte    begbal    biddte    budget    catxex    clnnum    cmpdte
cntrct    connum    contct    coresp    county    crtfid    cstcmp    csttye
csttyl    csttym    csttyo    csttys    ctcdte    ctynme    dlypyr    dsccnt
dscdte    dtecmp    duedte    emptme    endbal    eqprvw    estdte    estemp
faxnum    fednum    fedsck    finchg    fldrpt    hrscmp    imgfle    inactv
insdte    insusr    invalc    jobcst    jobnme    lcltax    lender    lenfld
lenrls    loctax    lonfrm    lotclr    lotnum    lotprm    modnme    ncrtck
ntetxt    pchlst    pctcmp    phnnum    plnprc    plnrcd    plnrcv    prmadd
prmchg    prmcty    prmeml    prmnme    prmphn    prmste    prmzip    propsl
pstexm    pstwip    ptotkf    rcapjb    rcarjb    rccjob    rccpay    rccrec
reccln    recnum    remids    reqinf    reqprp    retain    rtejob    rtervw
schedl    schprd    shtnme    slsemp    slstax    sprvsr    sqarft    srvinv
state_    status    stenum    stmeml    strdte    sttdte    subcnt    subcon
submtl    timmat    tmcdln    trnmtl    typwrk    untbll    untcmp    untlin
untprp    upddte    updusr    usrcs6    usrcs7    usrcs8    usrcs9    usrdf1
usrdf2    usrlst    zipcde
```

Key columns:

| Column | Meaning | Type |
|---|---|---|
| `recnum` | **Job PK** — the target of every `jobnum` FK | `bigint` ✅ |
| `_idnum` | Internal surrogate | |
| `jobnme` | Human-readable job name (`recnum` is *not* readable) | text |
| `shtnme` | Short name | text |
| `clnnum` | Client FK | |
| `ctynme`, `state_`, `zipcde`, `county` | Job site address | text |
| `status` | Status code | int |
| `strdte`, `cmpdte`, `ctcdte`, `dtecmp`, `awddte`, `biddte`, `estdte` | Start / completion / contract / award / bid / estimate dates | date |
| `begbal`, `endbal` | Beginning / ending balance | `Currency` ~ |
| `retain` | Job-level retainage — **zero on all 27 rows** | decimal |
| `pctcmp`, `cstcmp`, `untcmp`, `hrscmp` | Percent / cost / units / hours complete | |
| `budget`, `jobcst`, `emptme`, `schedl` | **Very likely table-valued relationships**, not scalars — job cost, budget, employee time, schedule. Unexplored, and the most valuable unopened door in the database |
| `upddte` / `updusr`, `insdte` / `insusr` | Audit | |

Navigation properties: `acpinv`, `acrinv`, `actpay` (via `achtct`, `lender`), `biditm`,
`dptmnt`, `employ` (via `estemp`, `slsemp`, `sprvsr`), `export`, `jobcnt`, `jobpgp`,
`jobphs`, `jobtyp`, `lgract`, `pchord`, `prelen`, `scdlen`, `taxdst`, `vndcrt`.

### `dbo.actpay` — Vendor master (screen 4-4)

113 scalar columns observed.

```
_idnum    acheml    actnum    actp_u    acttyp    addrs1    addrs2    aiafrm
aialin    begbal    bnkact    ca_tax    cdedft    cllphn    cmprte    condsc
contct    contyp    coresp    cstcde    csttyp    ctynme    dirdep    dscdte
dscrte    duedte    dupchk    e_mail    eftact    eftcde    efteml    eftiid
eftpay    eftrtn    elc199    eml199    endbal    eqpcst    eqpmnt    faxnum
fdrpsb    fedidn    homphn    hotlst    imgfle    inactv    insdte    insusr
intrnl    jobcst    lgrdft    lgrtrn    licnum    lonfrm    lonlin    minsts
ntetxt    orddsc    ordtyp    ownnme    pagnum    paymth    pchtyp    phnnum
plnrcd    plnrcv    pomesg    prente    prt199    rccpay    rcctrn    recnum
reqinf    reqprp    reqtyp    resnum    rfpdsc    rfptyp    rtnmbr    sbcgln
sbctyp    schsub    sepchk    shtnme    srvsch    state_    steidn    stsdft
subcon    submtl    taxcde    tkflin    tolamt    tolexc    tolprc    toltyp
trnmtl    typdft    untbll    upddte    updusr    usrdf1    usrdf2    utwarn
utxrte    vndnme    vndnum    vndprc    wrndft    zipcde
```

Key columns: `recnum` (**vendor PK**, labelled *Vendor ID*), `vndnme` (*Vendor Name*),
`vndnum`, `shtnme`, `acttyp`, `addrs1/2` + `ctynme`/`state_`/`zipcde`, `phnnum`/`faxnum`/
`cllphn`/`e_mail`, `fedidn`/`steidn` (tax IDs), `licnum`, `begbal`/`endbal`, `paymth`,
`dscrte`/`dscdte`/`duedte` (terms), `subcon`, `inactv`, `taxcde`.

Also carries pseudo-columns `actrec(recnum)`, `pclsln(recnum)`, `scdlen(recnum)`.

Navigation properties: `actrec`, `lgract`, `pchord`, `pclsln`, `privnd`, `scdlen`, `taxdst`,
`vndbal`, `vndcnt`, `vndcrt`, `vndrmt`, `vndtyp`, `vndytd`.

### `dbo.acrinv` — AR invoice header (screen 3-2)

29 columns named by the old dataflow, plus the ones our silver reads (which the old dataflow
kept and therefore never named):

```
_idnum    amtpad    dscavl    dsctkn    gstamt    gstsbj    hldamt    hldbll
hldrem    hotlst    hstamt    hstsbj    imgfle    insusr    invamt    invbal
invdte    ntetxt    phsnum    postyr    pstamt    pstsbj    refnum    slstax
subttl    updusr    usrdf1    usrdf2    usrnme
+ recnum  invnum  jobnum  duedte  dscrpt  status  retain  vodrec  upddte
```

| Column | Meaning | Type | Note |
|---|---|---|---|
| `_idnum` | Internal PK | | **The FK target for `arivln._idref`** |
| `recnum` | Invoice business key | | |
| `invnum` | Invoice number | text | |
| `jobnum` | **FK → `actrec.recnum`** | `bigint` ✅ | Not a readable job code |
| `invdte`, `duedte` | Invoice / due date | `date` ~ | |
| `dscrpt` | Description | text | |
| `invamt` | Invoice total | `Currency` ~ | ⚠️ **Zero on all 148 rows** — see [§6](#6-measured-values-the-traps) |
| `amtpad` | Amount paid | `Currency` ~ | |
| `invbal` | Invoice balance | `Currency` ~ | |
| `hldamt`, `hldbll`, `hldrem` | Hold / retainage amounts | | zero throughout |
| `retain` | Retainage | decimal | ⚠️ **Zero on all rows** |
| `subttl`, `slstax`, `gstamt`, `pstamt`, `hstamt` | Subtotal and tax components | | |
| `gstsbj`, `pstsbj`, `hstsbj` | Tax-subject flags | | |
| `status` | Status code | int | |
| `phsnum` | Phase | | 0 throughout |
| `postyr` | Posting year | | |
| `vodrec` | Void record | `bigint` | ⚠️ `bigint` here but `varchar` on `acpinv` — the M code tests `= 0` here and `= ""` there. Not a typo; mirror it |

Navigation properties: `pchord`, `taxdst`. (`arivln` reached via `_idref`.)

### `dbo.arivln` — AR invoice lines

Columns confirmed by `26_sage_silver.sql`. The old dataflow never touched this table, so the
full column list is unknown.

| Column | Meaning | Note |
|---|---|---|
| `_idnum` | Line PK | |
| `_idref` | **FK → `acrinv._idnum`** | The real join key |
| `invrec` | *Documented* FK to `acrinv.recnum` | ⚠️ **Orphans 258 of 258 rows.** Do not use |
| `linnum` | Line number | int |
| `dscrpt` | Line description | |
| `linqty` | Quantity | double |
| `linprc` | Unit price | double |
| `extprc` | **Extended line total** | AR's total column (AP uses `extttl`) |
| `hldamt` | Hold / retainage | **Zero on all 258 rows** |
| `bllamt` | Billed amount | |
| `cstcde` | **CSI cost code** | Present on only **25 of 258** lines (10%) |
| `lgract` | Ledger account | |
| `upddte` | Audit | |

### `dbo.acpinv` — AP invoice header (screen 4-2)

43 columns named by the old dataflow, plus the ones silver reads:

```
_idnum    acpi_u    adjust    amtpad    apinte    ca_tax    cmpamt    ctcnum
dscavl    dscrpt    dsctkn    duedte    freigh    gstamt    hldamt    hldbll
hldrem    hotlst    hstamt    insusr    invamt    invbal    invdte    invnum
jobnum    ntetxt    payee2    phsnum    pstamt    qstamt    rcpamt    shpnum
slstax    subttl    taxcde    updusr    usedst    usetax    usettl    usrdf1
usrdf2    usrnme    vndnum
+ recnum  status  retain  vodrec  upddte  pchord
```

| Column | Meaning | Note |
|---|---|---|
| `_idnum` | Internal PK | **FK target for `apivln._idref`** |
| `recnum` | Invoice business key | |
| `invnum` | Invoice number | |
| `vndnum` | **FK → `actpay.recnum`** | labelled *Vendor_ID* |
| `jobnum` | **FK → `actrec.recnum`** | |
| `ctcnum` | Contract number | |
| `pchord` | PO number | |
| `invdte`, `duedte` | Invoice / due date | |
| `dscrpt` | Description | |
| `invamt` | Invoice total | ⚠️ **Zero on all 871 rows** |
| `amtpad`, `invbal` | Paid / balance | The real total is their sum |
| `hldamt`, `hldbll`, `hldrem`, `retain` | Retainage | Zero throughout |
| `phsnum` | Phase | ⚠️ **0 on all 871 headers** — kills phase-level AP analysis |
| `subttl`, `slstax`, `usetax`, `usedst`, `usettl`, `gstamt`, `pstamt`, `qstamt`, `ca_tax`, `taxcde` | Tax stack | |
| `freigh`, `shpnum`, `payee2`, `rcpamt`, `cmpamt`, `adjust`, `apinte` | Freight, shipment, payee, receipt/compound/adjustment/interest amounts | |
| `dscavl`, `dsctkn` | Discount available / taken | |
| `vodrec` | Void record | `varchar` here (vs `bigint` on `acrinv`) |

Navigation properties: `acppmt`, `actpay`, `actrec`, `apivln`, `jobphs`, `pchord`, `scdpay`,
`taxdst`.

### `dbo.apivln` — AP invoice lines

Columns confirmed by `26_sage_silver.sql`.

| Column | Meaning | Note |
|---|---|---|
| `_idnum` | Line PK | |
| `_idref` | **FK → `acpinv._idnum`** | The real join key |
| `invrec` | *Documented* FK to `acpinv.recnum` | ⚠️ **Orphans 901 of 901 rows.** Do not use |
| `linnum` | Line number | |
| `prtdsc` | Part / line description | Note: **`prtdsc`, not `dscrpt`** — AR and AP lines differ |
| `linqty` | Quantity | |
| `linprc` | Unit price | |
| `extttl` | **Extended line total** | AP's total column (AR uses `extprc`) |
| `hldamt` | Hold / retainage | **Zero on all 901 rows** |
| `invamt` | Invoiced amount | |
| `actnum` | **GL account** | Present on **901 of 901** lines — but see the distribution in [§6](#6-measured-values-the-traps) |
| `subact` | Sub-account | **NULL on every row** |
| `upddte` | Audit | |

**The two line tables do not share a shape.** AP codes to `actnum`/`subact` (GL account), AR
to `cstcde` (cost code); AP's total is `extttl`, AR's is `extprc`. They are deliberately not
unioned in silver — one table with half its columns null per direction reads as a data
problem forever after.

### `dbo.acrpmt` — AR payments / cash receipts (screen 3-3-1)

18 columns observed. Single-table screen (no detail table).

```
_idnum    _idref    actper    amount    aplcrd    chkdte    chknum    dscrpt
dsctkn    insdte    insusr    invdte    jobnum    lgrrec    postyr    recnum
upddte    updusr
```

| Column | Meaning |
|---|---|
| `_idref` | FK → `acrinv` (the invoice being settled) |
| `actper` | Accounting / billing period |
| `amount` | Payment amount (`Currency`) |
| `chkdte`, `chknum` | Payment date, cheque number |
| `jobnum` | FK → `actrec.recnum` |
| `lgrrec` | Ledger record FK |
| `aplcrd` | Applied credit |
| `postyr` | Posting year |

### `dbo.acppmt` — AP payments / vendor payments (screen 4-3)

68 columns observed — it repeats most of the invoice header shape.

```
_idnum    _idref    achbch    acpi_u    actper    adjust    amount    amtpad
apinte    aplcrd    btcnum    ca_tax    chkdte    chknum    cmpamt    ctcnum
depdte    dscavl    dscdte    dscrpt    dsctkn    duedte    entdte    freigh
gstamt    hldamt    hldbll    hldrem    hotlst    hstamt    insdte    insusr
invamt    invbal    invdte    invnet    invnum    invttl    invtyp    jobnum
lgrrec    ntetxt    payee2    phsnum    postyr    pstamt    qstamt    rcpamt
recnum    refnum    retain    setpay    shpnum    slstax    status    subttl
taxcde    ttlpad    upddte    updusr    usedst    usetax    usettl    usrdf1
usrdf2    usrnme    vndnum    vodrec
```

Distinctive columns: `_idref` (FK → `acpinv`), `chkdte`/`chknum`/`depdte` (payment and
deposit dates), `achbch`/`btcnum` (ACH batch, batch number), `invnet`, `invttl`, `ttlpad`,
`invtyp`, `setpay`, `entdte`.

Navigation properties: `acpinv`, `acppmt`, `actpay`, `actrec`, `apivln`, `jobphs`, `pchord`,
`scdpay`, `taxdst`.

---

## 5. Keys and joins (verified)

```
acrinv.jobnum   → actrec.recnum       AR invoice to job      ✅ 0 of 148 orphaned
acpinv.jobnum   → actrec.recnum       AP invoice to job      ✅
acpinv.vndnum   → actpay.recnum       AP invoice to vendor   ✅
arivln._idref   → acrinv._idnum       AR line to header      ✅ 0 orphaned
apivln._idref   → acpinv._idnum       AP line to header      ✅ 0 orphaned
acrpmt._idref   → acrinv._idnum       receipt to invoice
acppmt._idref   → acpinv._idnum       payment to invoice
```

### The documented join key is wrong

The schema notes implied lines hang off headers by `invrec`. Measured 2026-08-25:

| Join | Result |
|---|---|
| `arivln.invrec` → `acrinv.recnum` | **258 of 258 orphaned** |
| `apivln.invrec` → `acpinv.recnum` | **901 of 901 orphaned** |
| **`arivln._idref` → `acrinv._idnum`** | **0 orphaned** |
| **`apivln._idref` → `acpinv._idnum`** | **0 orphaned** |

`_idnum`/`_idref` look like internal plumbing, which is presumably how the wrong answer got
documented. They are the foreign key. Getting this wrong does not error — it silently
produces zero rows.

### `jobnum` is not a job number

`jobnum` is a `bigint` FK to `actrec.recnum`. The readable name is `actrec.jobnme`. It does
**not** match a Procore project number or the `YY-000` codes in the Excel filenames. The
Procore↔Sage join goes through `dim_projects_procoreXsage` (`Sage Project ID` ↔ `Project ID`),
which is a real crosswalk, not a convenience lookup — and it is **incomplete**: 15 of 23–27
Sage projects are mapped, and six job numbers on real AR invoices have no entry at all.
Anything joining through it silently drops those jobs.

---

## 6. Measured values (the traps)

Every one of these is a defect that produces a plausible-looking wrong number rather than an
error.

### `invamt` is zero on every invoice

Measured 2026-08-25: `acrinv.invamt` = 0 on all 148 rows, `acpinv.invamt` = 0 on all 871.
The obvious "invoice total" column is simply not populated by this company. Taking it at face
value puts **$0 on every invoice**, with total confidence and no error.

**The total is `amtpad + invbal`**, and it cross-checks exactly against the line tables — an
independent source:

| | Paid | + Outstanding | = Total | Line-table sum |
|---|---:|---:|---:|---|
| **AR** | $18,713,981.77 | $6,899,677.89 | **$25,613,659.66** | `SUM(arivln.extprc)` — identical |
| **AP** | $11,103,345.67 | $4,406,036.11 | **$15,509,381.78** | `SUM(apivln.extttl)` — identical |

Silver uses `COALESCE(NULLIF(invamt, 0), amtpad + invbal)` so `invamt` becomes authoritative
again if Sage ever starts populating it.

### Sage holds no retainage anywhere

| Location | Rows checked | Rows with retainage | Total |
|---|---:|---:|---:|
| `acrinv.retain` / `acpinv.retain` (headers) | 940 | 0 | $0.00 |
| `arivln.hldamt` (AR lines) | 258 | 0 | $0.00 |
| `apivln.hldamt` (AP lines) | 901 | 0 | $0.00 |
| `actrec.retain` (jobs) | 27 | 0 | $0.00 |

**A Sage-sourced retainage figure of $0 is correct, not a bug.** The real figures come from
Procore progress billing and are in `fct_Billing` via `21_financial_silver.sql`: owner
retainage held **$830,725.87**, sub retainage held **$486,030.04**, net **$344,695.83**.

Process note worth raising: Affect withholds retainage on Procore contracts but records none
of it in Sage, so the two systems disagree by design.

### Actual-cost-by-cost-code is NOT available from Sage

`apivln` carries `actnum` on 901 of 901 lines — but those are **GL accounts, not cost codes**,
and the distribution kills the idea:

| `actnum` | Lines | Value |
|---|---:|---:|
| **50004** | **431** | **$10,437,732.28** |
| 50001 | 160 | $2,777,337.76 |
| 50005 | 56 | $137,715.03 |
| 50400 | 41 | $422,154.68 |
| everything else | 213 | $1,734,442.03 |

Two-thirds of the money sits on one account. `subact` is NULL on every row and `phsnum` is 0
on all 871 AP headers. The only dimensions Sage AP offers are project and a roughly four-way
GL split. Repointing `fct_BudgetLine.SpentToDate` at this would replace cost-code-level
Procore figures with a project-level number that is 67% one bucket — it would make the report
worse and look like an upgrade. **Not done, deliberately.**

On the AR side, `arivln.cstcde` is populated on only **25 of 258** lines (10%), so
revenue-by-cost-code is not available either and must not be promised.

### Other measured facts

| Check | Result |
|---|---|
| AR invoice date range | 2024-12-31 → **2026-08-31** |
| AP invoice date range | 2025-01-02 → 2026-07-24 |
| Distinct jobs on AR invoices | 24 |
| Sage projects vs. Procore crosswalk | 23–27 projects, **15** mapped |
| AR job numbers with no crosswalk entry | **6** |
| History depth | ~19 months, and it does **not** accumulate — full replace every run |
| Audit/history tables | Exist, but retention defaults to **90 days** and older rows are purged nightly. Usable as CDC, never as a history store |

---

## 7. What we build on top

### Bronze — `CD_Bronze_Lakehouse`

`CD_Sage_Ingest.Dataflow` (Dataflow Gen2), 8 queries, one per table, landing raw:

```m
shared cd_bronze_sage_acrinv = let
  Source = Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group"),
  Navigation = Source{[Schema = "dbo", Item = "acrinv"]}[Data]
in Navigation;
```

No filtering, no renames, no type changes at the boundary — shaping happens in SQL where it
is diffable, reviewable and testable offline in DuckDB. Update method `Replace`. Runs as
`Ingest Sage` inside `CD_Master_Pipeline`, parallel to Procore extraction, ahead of Bronze→Silver.

### Silver — `26_sage_silver.sql`, five typed tables

**`cd_silver_sage_jobs`** ← `cd_bronze_sage_actrec`

| Column | Type | Source |
|---|---|---|
| `sage_project_id` | STRING | `recnum` |
| `job_name` | STRING | `TRIM(jobnme)` |
| `job_short_name` | STRING | `TRIM(shtnme)` |
| `client_id` | STRING | `clnnum` |
| `city` | STRING | `TRIM(ctynme)` |
| `state` | STRING | `TRIM(state_)` |
| `status_code` | INT | `status` |
| `start_date` | DATE | `strdte` |
| `completion_date` | DATE | `cmpdte` |
| `contract_date` | DATE | `ctcdte` |
| `beginning_balance` | DOUBLE | `begbal` |
| `ending_balance` | DOUBLE | `endbal` |
| `updated_at` | TIMESTAMP | `upddte` |

**`cd_silver_sage_ar_invoices`** ← `cd_bronze_sage_acrinv` (+ jobs)

| Column | Type | Source |
|---|---|---|
| `invoice_uid` | | `_idnum` |
| `invoice_id` | STRING | `recnum` |
| `invoice_number` | STRING | `TRIM(invnum)` |
| `sage_project_id` | STRING | `jobnum` |
| `job_name` | STRING | joined from `cd_silver_sage_jobs` |
| `invoice_date` | DATE | `invdte` |
| `due_date` | DATE | `duedte` |
| `description` | STRING | `TRIM(dscrpt)` |
| `invoice_total` | DOUBLE | `COALESCE(NULLIF(invamt,0), amtpad + invbal)` |
| `amount_paid` | DOUBLE | `amtpad` |
| `invoice_balance` | DOUBLE | `invbal` |
| `hold_amount` | DOUBLE | `hldamt` (always 0; carried so a future non-zero shows up) |
| `status_code` | INT | `status` |
| `billing_period` | STRING | `yyyy-MM` derived from `invdte` — Sage has no such field |
| `updated_at` | TIMESTAMP | `upddte` |

**`cd_silver_sage_ap_invoices`** — same shape, plus `sage_vendor_id` (← `vndnum`), from `acpinv`.

**`cd_silver_sage_ar_lines`** ← `cd_bronze_sage_arivln`

`line_uid` (`_idnum`), `invoice_uid` (`_idref`), `invoice_id`, `sage_project_id`,
`line_number` INT (`linnum`), `description` (`dscrpt`), `quantity` DOUBLE (`linqty`),
`unit_price` DOUBLE (`linprc`), `line_total` DOUBLE (**`extprc`**), `hold_amount` DOUBLE,
`billed_amount` DOUBLE (`bllamt`), `cost_code` STRING (`cstcde`, NULL when 0),
`ledger_account` STRING (`lgract`), `updated_at`.

**`cd_silver_sage_ap_lines`** ← `cd_bronze_sage_apivln`

`line_uid`, `invoice_uid`, `invoice_id`, `sage_project_id`, `sage_vendor_id`,
`line_number` INT, `description` (**`prtdsc`**), `quantity`, `unit_price`,
`line_total` DOUBLE (**`extttl`**), `hold_amount`, `invoiced_amount` (`invamt`),
`ledger_account` STRING (**`actnum`** — named for what it is; calling it `cost_code` would
invite a join against `dim_CostCode` that cannot succeed), `sub_account` (`subact`, always
NULL), `updated_at`.

62 offline checks cover these in `test_silver.py`.

### Gold

`sv_ar_invoices` reads `cd_silver_sage_*` (no longer the pre-existing warehouse). Feeding it
moved `fct_Invoice` from **122 → 148 rows** and **$23.70M → $25.61M**, latest invoice
Jul 31 → **Aug 31**. Also consumed by `22_fct_invoice.sql`, `30_fct_financialperiod.sql`,
`17_dim_costcodecrosswalk.sql`.

### Power BI semantic layer (pre-existing, Rebecca's)

`Sage AP-AR.SemanticModel` — queries Sage **live over SQL, bypassing the lakehouse**:

| Model table | Source | Notes |
|---|---|---|
| `Revenue_AllTime` | `acrinv` | filtered `Invoice Balance <> 0` — **drops fully-paid invoices**, making "total billed to date" unanswerable |
| `AR_Open` | `acrinv` | + `Aging Bucket` (string), `Days Aged` (int64) |
| `Expenditure_AllTIme` | `acpinv` | (sic — misspelled in production) |
| `AP_Open` | `acpinv` | + aging |
| `Reciepts` | `acrpmt` | (sic — misspelled in production; renaming is a breaking change) |
| `Payments` | `acppmt` | |
| `Dim_Sage_Vendors` | `actpay` | `Vendor Name`, `vndnum` int64, `Vendor ID` string |
| `Dim__Sage_Projects` | `actrec` | `jobnme` string, `recnum` string |

Column labels it applies to Sage columns:

| Sage | Label | | Sage | Label |
|---|---|---|---|---|
| `amtpad` | Amount Paid | | `invbal` | Invoice Balance |
| `invdte` | Invoice(d) Date | | `duedte` | Due Date |
| `dscrpt` | Description | | `jobnum` | Job Number |
| `vndnum` | Vendor_ID | | `actpay.recnum` | Vendor ID |
| `actpay.vndnme` | Vendor Name | | `ctcnum` | Contract Number |
| `pchord` | PO Number | | `actper` | Billing Period |
| `amount` | Amount | | | |

Types it applies: `Currency.Type` for `amtpad`, `invbal`, `invttl`, `invnet`, `ttlpad`,
`endbal`, `amount`, `taxabl`, `nontax`; `type text` for `jobnum`, `recnum`, `Job Number`,
`Vendor ID`; `type date` for `Invoiced Date`; `Int64.Type` for `Billing Period`, `Days Aged`.
This old dataflow refreshes **weekly** (Mondays 06:00 Eastern) and writes straight to Silver
with `Replace`.

---

## 8. Tables known only by foreign key

Never queried by anyone. Named only because the SQL connector exposed them as navigation
properties on the eight tables above. This is the closest thing to a table catalogue that
exists for the rest of the database.

| Table | Likely holds | Reached from |
|---|---|---:|
| `pchord` | Purchase orders | 5 |
| `taxdst` | Tax districts | 5 |
| `jobphs` | Job phases | 3 |
| `scdlen` | Schedule / subcontract lines | 2 |
| `scdpay` | Scheduled payments | 2 |
| `lgract` | GL accounts | 2 |
| `vndcrt` | Vendor certificates (insurance/licence) | 2 |
| `biditm` | Bid items | 1 |
| `dptmnt` | Departments | 1 |
| `employ` | **Employees** (via `estemp`, `slsemp`, `sprvsr`) | 1 |
| `export` | Export definitions | 1 |
| `jobcnt` | Job contacts | 1 |
| `jobpgp` | Job pay groups | 1 |
| `jobtyp` | Job types | 1 |
| `pclsln` | Purchase-class lines | 1 |
| `prelen` | Prelien / preliminary notice | 1 |
| `privnd` | Preferred vendors | 1 |
| `vndbal` | Vendor balances | 1 |
| `vndcnt` | Vendor contacts | 1 |
| `vndrmt` | Vendor remittance | 1 |
| `vndtyp` | Vendor types | 1 |
| `vndytd` | Vendor year-to-date | 1 |

Plus `CMPANY` — the one table name Sage's own documentation mentions, in an SQL example
(`Select USRDF1 From CMPANY`).

---

## 9. Known gaps

| Wanted | Status |
|---|---|
| Total billed, AR outstanding, aging, invoice dates | ✅ covered |
| Total paid | ✅ `acrpmt` / `acppmt` |
| Line-level AR/AP detail | ✅ **now covered** — `arivln` / `apivln` |
| Retainage | ✅ **answered**: Sage holds none. Source is Procore progress billing |
| **Job cost / cost to complete / spent to date** | ❌ No job-cost table read. `actrec` exposes `jobcst`, `budget`, `cstcmp` as unexplored relationships |
| **Hours worked / OT by job** | ❌ No payroll table read. `actrec` exposes `emptme`, `hrscmp`; `employ` known only by FK |
| **Cost-coded actuals** | ❌ Not derivable from these eight tables — see [§6](#6-measured-values-the-traps) |
| Full column lists for `arivln` / `apivln` | ❌ Only the columns silver reads are known |
| Complete Procore↔Sage crosswalk | ❌ 15 of 23–27 mapped; 6 AR job numbers unmapped |
| Alerting on the DQ gate | ❌ Gate fails the run; nothing emails a person |

**The single question that unblocks the biggest one:** *which table holds job cost detail by
cost code?* It needs somebody with direct database access (Rebecca, or Nerds That Care) —
we cannot enumerate the catalogue through the gateway connection. Add it to `mashup.pq` and
the budget fact becomes real.

---

## Sources

Everything above is derived from these, in the repo:

| Path | What it contributes |
|---|---|
| `resources/sage-100-contractor/schema/OBSERVED-SCHEMA.md` | Column lists for the six original tables, navigation properties, the FK-only table catalogue. Generated by `derive_schema.py` from the production Power Query |
| `resources/sage-100-contractor/schema/README.md` | Naming conventions, joins in use, gaps, live verification results |
| `resources/sage-100-contractor/schema/derive_schema.py` | Regenerates `OBSERVED-SCHEMA.md`. `--selftest` for its own checks |
| `resources/sage-100-contractor/INTEGRATION-NOTES.md` | Why no published schema exists; header/detail rule; audit-table retention; connection mechanics; the `INFORMATION_SCHEMA` queries |
| `resources/sage-100-contractor/help/` | 2,023 v20.5 help topics — the **semantic** layer (what each screen means). Index at `help/INDEX.md` |
| `resources/sage-100-contractor/guides/` | Five PDF guides as text (DB & Company Administration ×3, Your Business 2026.1, User's Guide v23.1) |
| `foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow/mashup.pq` | The pre-existing production Power Query — the origin of most column knowledge |
| `foundation/charley-dev/01-ingestion/Sage/CD_Sage_Ingest.Dataflow/mashup.pq` | Our 8-table raw extract |
| `foundation/charley-dev/02-transformation/sql/silver/26_sage_silver.sql` | Silver schemas, the `_idref` finding, the `invamt` finding |
| `foundation/charley-dev/_docs/sage-ingestion.md` | Run history, row counts, measured totals, the GL-account distribution, gateway saga |
| `foundation/04-semantic_models/Sage AP-AR.SemanticModel/` | Power BI table/column types and business labels |
| `deliverables/03-sage100-ingestion.md` | Status, acceptance criteria, dated log |

Upstream (all verified to resolve, Aug 2026):

- [Database & Company Administration Guide 2025 v27.2 US](https://docs.sage.com/docs/en/customer/100contractor/27_2US/open/DatabaseAndCompanyAdministrationGuide.pdf) — SQL Server admin, **no table reference**
- [Sage 100 Contractor and Your Business 2026.1 US](https://docs.sage.com/docs/en/customer/100contractor/2026_1US/open/Sage100ContractorandYourBusiness.pdf)
- [User's Guide 2021 SQL US](https://docs.sage.com/docs/en/customer/100contractor/23_1US/open/UserGuide.pdf)
- [About Structured Query Language (online help)](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/19_7/Content/Modules/13-Review_and_Reporting/About_Structured_Query_Language.htm)
- [Sage Construction & Real Estate community](https://communityhub.sage.com/us/sage_construction_and_real_estate/)

> Sage publishes a table-by-table schema for Sage 100 **ERP** — a *different product* that
> shares the name. That documentation does not apply here.

---

*Compiled 2026-09-02. Regenerate the observed half with `python resources/sage-100-contractor/schema/derive_schema.py`;
the measured half comes from the lakehouse and is dated inline.*
