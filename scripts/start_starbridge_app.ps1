param(
    [string]$HostName = "127.0.0.1",
    [int]$BackendPort = 8765,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $RepoRoot "examples\starbridge_frontend"
$BackendUrl = "http://${HostName}:${BackendPort}"
$FrontendUrl = "http://${HostName}:${FrontendPort}"

Write-Host "Starting StarBridge backend:  $BackendUrl"
$backend = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m", "starbridge_mcp.backend", "--host", $HostName, "--port", "$BackendPort") `
    -WorkingDirectory $RepoRoot `
    -PassThru `
    -WindowStyle Hidden

try {
    Start-Sleep -Seconds 2
    $health = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 8
    if (-not $health.ok) {
        throw "backend health check failed"
    }

    Write-Host "Backend ready."
    Write-Host "Starting StarBridge frontend: $FrontendUrl"
    Write-Host "Press Ctrl+C to stop the frontend. Backend pid: $($backend.Id)"

    $env:VITE_STARBRIDGE_API_URL = $BackendUrl
    npm.cmd --prefix $FrontendDir run dev -- --host $HostName --port $FrontendPort
}
finally {
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force
    }
}
