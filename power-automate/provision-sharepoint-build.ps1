# Provision the BUILD site that the two Power Automate job flows drive.
#
# Creates, in one pass and in this order:
#   - the BUILD site itself (team site)
#   - document libraries '01 ESTIMATING' and '00 PROJECTS'
#   - the two template folder trees the flows copy from
#   - the 'Job Register' list, which is the trigger, the sequential-number
#     authority, the audit log and the future dim_Job all at once
#
# ---------------------------------------------------------------------------
# HOW TO RUN THIS  (about ten minutes, once)
#
# 1. Install the module:
#
#        Install-Module PnP.PowerShell -Scope CurrentUser -Force
#
# 2. Register an Entra app for sign-in. PnP.PowerShell 2.x REMOVED the built-in
#    multi-tenant app, so `Connect-PnPOnline -Interactive` on its own now fails
#    with 'ClientId is required'. This is the step people get stuck on. Run it
#    ONCE per tenant - it prints a ClientId, keep that:
#
#        Register-PnPEntraIDAppForInteractiveLogin -ApplicationName 'PnP Rocks' -Tenant <tenant>.onmicrosoft.com -Interactive
#
#    It asks a tenant admin to consent. If you are not one, someone who is has to
#    approve it - that is the only admin step in this whole file.
#
# 3. Edit $BUILD_SITE_URL below to the real URL. It is a placeholder on purpose;
#    the script refuses to run while it still says REPLACE-ME.
#
# 4. Connect to ANY site in the tenant and dry-run. The site does not have to
#    exist yet - step 5 creates it - so connect to the tenant root:
#
#        Connect-PnPOnline -Url https://<tenant>.sharepoint.com -Interactive -ClientId <the id from step 2>
#        ./provision-sharepoint-build.ps1
#
#    That reads and prints; it writes nothing.
#
# 5. Re-run with -Apply to write:
#
#        ./provision-sharepoint-build.ps1 -Apply
#
#    (Commands are on one line each on purpose - a copied backslash is not a
#    PowerShell line continuation and fails with a confusing parse error.)
#
# 6. Import the two flows from flows/ and set their SiteUrl parameter to the
#    same $BUILD_SITE_URL. See README.md, 'Manual import steps'.
# ---------------------------------------------------------------------------
#
# Idempotent: an existing site, library, folder or column is left alone, so
# re-running after a change is safe and is the intended way to apply one.
#
# DRY RUN BY DEFAULT. Nothing is written without -Apply. Reads happen either
# way, so a dry run reports exactly what a real run would do.

[CmdletBinding()]
param(
    [string]$SiteUrl,
    [switch]$Apply,
    # Use the connection already open in this session, and skip the site-existence check.
    #
    # The site block below calls Get-PnPTenantSite, which needs the -admin endpoint, and
    # then reconnects with -Interactive. Both are wrong when the site already exists and
    # you signed in some other way - -DeviceLogin in particular, where an -Interactive
    # reconnect discards the session you just approved and demands a browser that may not
    # be on the machine running this.
    [switch]$UseExistingConnection
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# PLACEHOLDER. Replace with the real BUILD site URL before running.
# Same convention as CD_Manual_Ingest.Dataflow/mashup.pq - never guess a tenant.
$BUILD_SITE_URL = 'https://REPLACE-ME.sharepoint.com/sites/BUILD'
# ---------------------------------------------------------------------------

if (-not $SiteUrl) { $SiteUrl = $BUILD_SITE_URL }
if ($SiteUrl -match 'REPLACE-ME') {
    throw "SiteUrl is still the placeholder. Edit `$BUILD_SITE_URL at the top of this script, or pass -SiteUrl."
}

$SiteTitle = 'BUILD'
$SiteAlias = ($SiteUrl -split '/')[-1]

if (-not $Apply) { Write-Host 'DRY RUN - nothing will be written. Re-run with -Apply.' -ForegroundColor Yellow }
Write-Host "site: $SiteUrl"
Write-Host ''

# ---------------------------------------------------------------------------
# TEMPLATE TREES
#
# OPEN QUESTION. The SOP names the two template folders but never says what is
# inside them. Everything below except '01-BIDDING/02-ESTIMATING' is a
# PLACEHOLDER structure - it is here so the flows have something real to copy
# and so the shape is reviewable, not because the client specified it.
#
# '01-BIDDING/02-ESTIMATING' is the one certainty: the Convert-to-Bidding SOP
# step copies the estimating folder into exactly that path, so the standard
# project template must contain it or the flow has nowhere to land.
#
# Affect must replace these with the real trees, and the boilerplate DOCUMENTS
# inside them have to come from the client or be lifted from an existing job.
# See README.md, 'What Affect must supply'.
$EstimatingTemplate = @(
    '01-ENQUIRY',
    '02-DRAWINGS',
    '03-TAKEOFF',
    '04-SUBCONTRACTOR QUOTES',
    '05-SUPPLIER QUOTES',
    '06-ESTIMATE SUMMARY',
    '07-SUBMISSION'
)

$ProjectTemplate = @(
    '01-BIDDING',
    '01-BIDDING/01-TENDER',
    '01-BIDDING/02-ESTIMATING',   # <- required by the SOP, not a placeholder
    '02-CONTRACT',
    '03-DRAWINGS',
    '04-SUBMITTALS',
    '05-RFI',
    '06-SITE',
    '07-COMMERCIAL',
    '08-HANDOVER'
)

$EstimatingLibrary   = '01 ESTIMATING'
$ProjectsLibrary     = '00 PROJECTS'
$EstimatingTemplateRoot = '02 E26-000 BOILER PLATE'
$ProjectTemplateRoot    = 'YY-000 STANDARD PROJECT TEMPLATE'

# ---------------------------------------------------------------------------
function Step($label, [scriptblock]$body) {
    if ($Apply) {
        Write-Host "  + $label"
        & $body
    } else {
        Write-Host "  would create $label"
    }
}

# --------------------------------------------------------------------- site
if (-not (Get-PnPContext)) { throw 'Connect-PnPOnline first - see step 4 in the header.' }

if ($UseExistingConnection) {
    Write-Host 'using the connection already open in this session'
    $siteExists = $true
} else {
    $siteExists = $null -ne (Get-PnPTenantSite -Identity $SiteUrl -ErrorAction SilentlyContinue)
    if (-not $siteExists) {
        # Falls back to a read attempt for accounts without tenant-admin rights;
        # Get-PnPTenantSite needs the admin endpoint, a plain connect does not.
        try { Connect-PnPOnline -Url $SiteUrl -Interactive -ErrorAction Stop; $siteExists = $true } catch { }
    }

    if ($siteExists) {
        Write-Host "site exists - leaving it alone"
    } else {
        Step "site $SiteTitle ($SiteUrl)" {
            New-PnPSite -Type TeamSite -Title $SiteTitle -Alias $SiteAlias -Wait | Out-Null
        }
    }
}

if ($Apply -and -not $UseExistingConnection) { Connect-PnPOnline -Url $SiteUrl -Interactive }
elseif (-not $siteExists) {
    Write-Host ''
    Write-Host 'Site does not exist yet, so the libraries and list below cannot be'
    Write-Host 'inspected. Re-run with -Apply to create everything in one pass.'
    return
}

# ---------------------------------------------------------------- libraries
function Ensure-Library($title) {
    $existing = Get-PnPList -Identity $title -ErrorAction SilentlyContinue
    if ($null -eq $existing) {
        Step "library $title" {
            New-PnPList -Title $title -Template DocumentLibrary -EnableVersioning | Out-Null
        }
    } else {
        Write-Host "  $title exists"
    }
}

Write-Host ''
Write-Host 'libraries'
Ensure-Library $EstimatingLibrary
Ensure-Library $ProjectsLibrary

# ------------------------------------------------------------ template trees
# Folders are created parent-first, so the arrays above must stay ordered
# shallowest-first. Add-PnPFolder takes the parent and the leaf name separately.
function Ensure-Folder($library, $relativePath) {
    $full = "$library/$relativePath"
    if (Get-PnPFolder -Url $full -ErrorAction SilentlyContinue) {
        Write-Host "  $full exists"
        return
    }
    $parent = Split-Path $relativePath -Parent
    $leaf   = Split-Path $relativePath -Leaf
    $parentUrl = if ($parent) { "$library/$($parent -replace '\\','/')" } else { $library }
    Step "folder $full" {
        Add-PnPFolder -Name $leaf -Folder $parentUrl | Out-Null
    }
}

Write-Host ''
Write-Host "template: $EstimatingLibrary/$EstimatingTemplateRoot"
Ensure-Folder $EstimatingLibrary $EstimatingTemplateRoot
foreach ($f in $EstimatingTemplate) { Ensure-Folder $EstimatingLibrary "$EstimatingTemplateRoot/$f" }

Write-Host ''
Write-Host "template: $ProjectsLibrary/$ProjectTemplateRoot"
Ensure-Folder $ProjectsLibrary $ProjectTemplateRoot
foreach ($f in $ProjectTemplate) { Ensure-Folder $ProjectsLibrary "$ProjectTemplateRoot/$f" }

# ------------------------------------------------------------- Job Register
# ONE list is the trigger, the sequential-number authority, the audit log and
# the source Fabric will ingest as dim_Job. Every run is therefore logged by
# construction - there is no separate log to forget to write to.
#
# Versioning is what gives every field change a who and a when, which is the
# difference between "the flow failed" and "the flow failed at 14:02 for Sam
# on job 26-025 with this message".
Write-Host ''
Write-Host 'list: Job Register'
$register = Get-PnPList -Identity 'Job Register' -ErrorAction SilentlyContinue
if ($null -eq $register) {
    Step 'list Job Register' {
        New-PnPList -Title 'Job Register' -Template GenericList -EnableVersioning | Out-Null
    }
} else {
    Write-Host '  Job Register exists - adding any missing columns'
}

if ($Apply) {
    Set-PnPList -Identity 'Job Register' -EnableVersioning $true -MajorVersions 500

    # Title is the project name, exactly as the SOP asks for it ("Enter a
    # Project Name"). It is deliberately the raw name, never the sanitised one -
    # the sanitised form only ever exists as a folder name, and keeping the
    # original is what lets someone see why a folder came out different.
    Set-PnPField -List 'Job Register' -Identity 'Title' -Values @{
        Title = 'Project Name'
        Description = 'The project name as requested. Folder names are derived from this; forbidden characters are stripped by the flow.'
        Required = $true
    }

    try {
        Add-PnPField -List 'Job Register' -DisplayName 'JobYear' -InternalName 'JobYear' -Type Number -AddToDefaultView -ErrorAction Stop | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'JobYear' -Values @{ Description = 'Two-digit year the number was issued in, e.g. 26. Written by the flow.' }
        Add-PnPField -List 'Job Register' -DisplayName 'JobSeq' -InternalName 'JobSeq' -Type Number -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'JobSeq' -Values @{ Description = 'Sequential number within JobYear. THE authority - do not edit by hand.' }
        Add-PnPField -List 'Job Register' -DisplayName 'JobNumber' -InternalName 'JobNumber' -Type Text -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'JobNumber' -Values @{ Description = 'YY-### , e.g. 26-025. Written by the flow.' }
        Add-PnPField -List 'Job Register' -DisplayName 'Stage' -InternalName 'Stage' -Type Choice -Choices 'Requested','Estimating','Bidding','Failed' -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'Stage' -Values @{
            DefaultValue = 'Requested'
            Required = $true
            Description = 'Requested -> the Estimating Setup flow picks it up. Set it to Bidding to fire the Convert to Bidding flow. Failed means read ErrorDetail.'
        }
        Add-PnPField -List 'Job Register' -DisplayName 'EstimatingFolderUrl' -InternalName 'EstimatingFolderUrl' -Type URL -AddToDefaultView | Out-Null
        Add-PnPField -List 'Job Register' -DisplayName 'ProjectFolderUrl' -InternalName 'ProjectFolderUrl' -Type URL -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'ProjectFolderUrl' -Values @{ Description = 'Empty until the job converts. The Convert flow tests this for emptiness - that is what stops it re-triggering on its own update.' }
        # Text, not a Person column. A Person column arrives in Fabric as a
        # nested record that silver then has to unpick, and the flow only ever
        # has an email anyway.
        Add-PnPField -List 'Job Register' -DisplayName 'RequestedBy' -InternalName 'RequestedBy' -Type Text -AddToDefaultView | Out-Null
        Add-PnPField -List 'Job Register' -DisplayName 'RequestedAt' -InternalName 'RequestedAt' -Type DateTime -AddToDefaultView | Out-Null
        Add-PnPField -List 'Job Register' -DisplayName 'CompletedAt' -InternalName 'CompletedAt' -Type DateTime -AddToDefaultView | Out-Null
        Add-PnPField -List 'Job Register' -DisplayName 'CopyJobStatus' -InternalName 'CopyJobStatus' -Type Text -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'CopyJobStatus' -Values @{ Description = 'Last CreateCopyJobs outcome, e.g. Completed, or JobError with the log line.' }
        Add-PnPField -List 'Job Register' -DisplayName 'ErrorDetail' -InternalName 'ErrorDetail' -Type Note -AddToDefaultView | Out-Null
        Set-PnPField -List 'Job Register' -Identity 'ErrorDetail' -Values @{ Description = 'Written by the on-failure scope. Empty on a healthy run.' }
    } catch [System.Management.Automation.RuntimeException] {
        # Add-PnPField throws if the column already exists. That is the idempotent
        # path, not a failure - anything else rethrows.
        if ($_.Exception.Message -notmatch 'already exists') { throw }
    }
} else {
    foreach ($c in @('JobYear','JobSeq','JobNumber','Stage','EstimatingFolderUrl','ProjectFolderUrl','RequestedBy','RequestedAt','CompletedAt','CopyJobStatus','ErrorDetail')) {
        Write-Host "  would create column $c"
    }
}

Write-Host ''
if ($Apply) {
    Write-Host 'Done. 2 libraries, 2 template trees, Job Register with 11 columns.'
    Write-Host 'Next: import flows/EstimatingSetup.json and flows/ConvertToBidding.json,'
    Write-Host "set their SiteUrl parameter to $SiteUrl, and confirm the trigger"
    Write-Host 'concurrency is 1 - see README.md.'
} else {
    Write-Host 'DRY RUN - nothing written. Re-run with -Apply.'
}
