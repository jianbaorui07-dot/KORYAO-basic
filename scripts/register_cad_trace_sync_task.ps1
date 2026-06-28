param(
    [string]$TaskName = "CodexCadTraceGitHubSync",
    [string]$SyncScript = "C:\codex-cad-bridge-git\scripts\sync_cad_trace_snapshot.ps1"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SyncScript)) {
    throw "Sync script not found: $SyncScript"
}

$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$SyncScript`""

schtasks /Create /TN $TaskName /SC MINUTE /MO 15 /TR $taskCommand /F | Out-Host
schtasks /Query /TN $TaskName /V /FO LIST | Out-Host
