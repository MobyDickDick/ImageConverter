[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][DateTimeOffset]$StartUtc,
    [Parameter(Mandatory = $true)][DateTimeOffset]$EndUtc,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = 'Stop'
if ($EndUtc -le $StartUtc) {
    throw 'EndUtc must be later than StartUtc'
}
$events = @(Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = @('Microsoft-Windows-Kernel-Power', 'Microsoft-Windows-Power-Troubleshooter')
    StartTime = $StartUtc.LocalDateTime
    EndTime = $EndUtc.LocalDateTime
} | Sort-Object TimeCreated, RecordId | ForEach-Object {
    [ordered]@{
        record_id = $_.RecordId
        provider = $_.ProviderName
        event_id = $_.Id
        time_utc = $_.TimeCreated.ToUniversalTime().ToString('o')
        message = $_.Message
    }
})
$report = [ordered]@{
    schema = 'deadline_power_events_v1'
    start_utc = $StartUtc.UtcDateTime.ToString('o')
    end_utc = $EndUtc.UtcDateTime.ToString('o')
    events = $events
}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding utf8
