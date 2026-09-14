# Read-only validation through Fabric's SQL analytics endpoint. No table writes.
$ErrorActionPreference = 'Stop'
$config = Get-Content (Join-Path $PSScriptRoot 'fabric_ids.json') -Raw | ConvertFrom-Json
$rulesJson = @'
import json, sys
sys.path.insert(0, sys.argv[1])
from sage_validation import checks
rules = checks()
for direction, source in [('ar', 'arivln'), ('ap', 'apivln')]:
    rules[f'sage_{direction}.bronze_orphan_lines'] = f'''
SELECT l._idnum AS line_uid, l._idref AS invoice_uid
FROM cd_bronze_sage_{source} l
LEFT JOIN cd_silver_sage_{direction}_invoices h ON l._idref = h.invoice_uid
WHERE h.invoice_uid IS NULL'''
    header = 'acrinv' if direction == 'ar' else 'acpinv'
    amount = 'extprc' if direction == 'ar' else 'extttl'
    rules[f'sage_{direction}.bronze_invoice_line_amounts'] = rules[f'sage_{direction}.invoice_line_amounts'].replace(
        f'cd_silver_sage_{direction}_invoices',
        f'(SELECT _idnum AS invoice_uid, recnum AS invoice_id, '
        f'COALESCE(NULLIF(invamt,0), amtpad+invbal) AS invoice_total FROM cd_bronze_sage_{header})'
    ).replace(f'cd_silver_sage_{direction}_lines',
              f'(SELECT _idref AS invoice_uid, {amount} AS line_total FROM cd_bronze_sage_{source}) AS bronze_lines')
    rules[f'sage_{direction}.missing_silver_headers'] = f'''
SELECT b._idnum AS invoice_uid, b.recnum AS invoice_id, b.jobnum AS sage_job,
       b.amtpad AS paid, b.invbal AS balance, b.upddte AS updated_at,
       COALESCE(NULLIF(b.invamt, 0), b.amtpad + b.invbal) AS invoice_total
FROM cd_bronze_sage_{header} b
LEFT JOIN cd_silver_sage_{direction}_invoices s ON b._idnum = s.invoice_uid
WHERE s.invoice_uid IS NULL'''
    rules[f'sage_{direction}.bronze_header_orphans'] = f'''
SELECT l._idnum AS line_uid, l._idref AS invoice_uid
FROM cd_bronze_sage_{source} l
LEFT JOIN cd_bronze_sage_{header} h ON l._idref = h._idnum
WHERE h._idnum IS NULL'''
print(json.dumps(rules))
'@ | python - $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Cannot build reconciliation queries' }
$rules = $rulesJson | ConvertFrom-Json
$evidence = [ordered]@{
    started_at = [DateTime]::UtcNow.ToString('o')
    source = 'Fabric SQL analytics endpoint; current visible bronze and silver tables'
    limitation = 'Endpoint synchronization and upstream source freshness are not certified by these queries.'
    workspace_id = $config._workspace.id
    database = 'CD_Silver_Lakehouse'
    checks = @()
}
$authToken = az account get-access-token --resource https://database.windows.net/ --query accessToken -o tsv
if ($LASTEXITCODE -ne 0) { throw 'Database authentication failed' }
$connection = [System.Data.SqlClient.SqlConnection]::new(
    "Server=tcp:$($config.CD_Silver_Lakehouse.sqlEndpoint),1433;Initial Catalog=CD_Silver_Lakehouse;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;")
$connection.AccessToken = $authToken
try {
    $connection.Open()
    foreach ($rule in $rules.PSObject.Properties) {
        $query = $rule.Value.Replace('cd_bronze_sage_', '[CD_Bronze_Lakehouse].[dbo].cd_bronze_sage_')
        $result = [ordered]@{ name=$rule.Name; query=$query; status='unknown'; rows=@() }
        $command = $connection.CreateCommand()
        $command.CommandText = $query
        $command.CommandTimeout = 120
        $reader = $null
        try {
            $reader = $command.ExecuteReader()
            while ($reader.Read()) {
                $row = [ordered]@{}
                for ($i=0; $i -lt $reader.FieldCount; $i++) {
                    $row[$reader.GetName($i)] = if ($reader.IsDBNull($i)) { $null } else { $reader.GetValue($i) }
                }
                $result.rows += $row
            }
            $result.status = if ($result.rows.Count -eq 0) { 'passed' } else { 'violations' }
            $result.failing_rows = $result.rows.Count
        } catch {
            $result.status = 'error'
            $result.error = $_.Exception.Message
        } finally {
            if ($null -ne $reader) { $reader.Dispose() }
            $command.Dispose()
        }
        $evidence.checks += $result
        Write-Output "$($result.name): $($result.status) ($($result.rows.Count) rows)"
    }
} finally {
    $connection.Dispose()
    $authToken = $null
    $evidence.completed_at = [DateTime]::UtcNow.ToString('o')
    $evidence | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 (
        Join-Path $PSScriptRoot '../_docs/sage-reconciliation-evidence.json')
}
if (@($evidence.checks | Where-Object { $_.status -ne 'passed' }).Count -gt 0) { exit 1 }
