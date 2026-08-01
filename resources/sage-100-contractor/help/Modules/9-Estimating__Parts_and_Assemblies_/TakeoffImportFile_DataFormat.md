<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/TakeoffImportFile_DataFormat.htm (Sage 100 Contractor help v20.5) -->

# Format of takeoff and takeoff grid data

## Takeoff data files

Takeoff data consists of rows of ordered, tab-delimited fields that end with a carriage return or line feed. The rows are organized into specific sections that begin with one of the following special tags:

- *** Bid Items ***
- *** Job Phases ***
- *** Global Variables ***
- *** Takeoff Lines ***
- *** Summary ***
- *** Notes ***

### *** Bid Items ***

Recnum: Job number (replaced with new job number during import)

Itmnum: Bid item number

Itmcde: Item code

Itmnme: Description

Untdsc: Unit

Bidqty: Quantity

Itmtyp: Item type

Ovrhed: Overhead

Profit: Profit

Ntetxt: Notes

### *** Job Phases ***

Recnum: Job number (will replaced with new job number when file is imported)

Phsnum: Phase number

Phsnme: Description

Bllamt: Billing amount

Retain: Retention

Mdldsc: Model

Untdsc: Unit

Untqty: Quantity

Ntetxt: Notes

### ***Global Variables *** (Project Values)

Recnum: database record number

Dscrpt: Description

Abvnme: Variable name

Untdsc: Unit

Glbval: Value

Ntetxt: Notes

### *** Takeoff Lines *** (takeoff details)

recnum: Job number (will replaced with new job number when file is imported)

itmnum: bid item

phsnum: Phase number

linnum: Grid row

asmnum: Assembly number

asmchk: Assembly connection or labor part connection arrow code

prtnum: Part number

prtdsc: Description

alpnum: Alpha Part

untdsc: Unit

linqty: Quantity

linprc: Cost

linlck: Row lock

qtyfrm: Formula

extqty: Extended quantity

extttl: Extended Cost

taxdst (US) sbjpst (Canada): Tax District or Subject to PST

slstax: Sales tax

ovhmrk: overhead rate

ovhamt: Overhead amount

pftmrk: Profit rate

pftamt: Profit amount

bidprc: Extended price

prmvnd: Vendor

cstcde: Cost Code

csttyp: Cost type

tsknum: Task

invloc: inventory location

usrdf1: User defined

ntetxt: Notes

expnte: Export notes

### *** Summary *** (Insurance, Tax and Bonding)

paysbj: Payroll subject

subsbj: Subcontracts subject

bidsbj: Bid amount subject

taxsbj: Use tax bid amount subject

bndlt1: Bonding limit 1

bndlt2: Bonding limit 2

bndlt3: Bonding limit 3

payrte: Payroll rate

subrte: subcontracts rate

bidrte: Bid amount rate

taxrte: Use tax bid amount rate

lt1rte: Bonding rate 1

lt2rte: Bonding rate 2

lt3rte: Bonding rate 3

inscde: Insurance cost code

taxcde: Use tax cost code

bndcde: bonding cost code

instyp: Insurance cost type

taxtyp: Use tax cost type

bndtyp: Bonding cost type

insinc: Include in budget checkbox - Insurance

taxinc: Include in budget checkbox – Use tax

bndinc: Include in budget checkbox - Bondiong

insitm: Insurance bid item

taxitm: Use tax bid item

bnditm: Bonding bid item

insphs: Insurance phase

taxphs: Use tax phase

bndphs: Bonding phase

(Summary)

mrgmrk: Margin or markup (margin = 1 or markup = 2)

mrgovr: Gross margin override %

mrkrte: Markup %

mrkdlr: Dollar markup

bidovr: Bid amount override

lckbid: Lock bid amount checkbox

### *** Notes ***

Header notes text

## Takeoff grid data files

Takeoff grid data files include only the content that you import into the current grid. It is similar to the Takeoff Lines data beginning with the assembly number:

asmnum: Assembly number

asmchk: Assembly connection or labor part connection arrow code

prtnum: Part number

prtdsc: Description

alpnum: Alpha Part

untdsc: Unit

linqty: Quantity

linprc: Cost

linlck: Row lock

qtyfrm: Formula

extqty: Extended quantity

extttl: Extended Cost

taxdst (US) sbjpst (Canada): Tax District or Subject to PST

slstax: Sales tax

ovhmrk: overhead rate

ovhamt: Overhead amount

pftmrk: Profit rate

pftamt: Profit amount

bidprc: Extended price

prmvnd: Vendor

cstcde: Cost Code

csttyp: Cost type

tsknum: Task

invloc: inventory location

usrdf1: User defined

ntetxt: Notes

expnte: Export notes
