param(
    [string]$RepoRoot = "C:\codex-cad-bridge-sync",
    [string]$WorkspaceRoot = "",
    [string]$JobsRoot = "",
    [string]$PythonExe = (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
)

$ErrorActionPreference = "Stop"
$gitCmd = "C:\Program Files\Git\cmd\git.exe"
$gitBin = "C:\Program Files\Git\mingw64\bin"
$env:Path = "$gitBin;C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;$env:Path"

if (-not (Test-Path -LiteralPath $gitCmd)) {
    throw "Git executable not found: $gitCmd"
}

if (-not $WorkspaceRoot) {
    $workspaceCandidates = @(
        "C:\cad_exact_trace_workspace",
        (Join-Path $env:USERPROFILE "OneDrive\*\New project\cad_exact_trace")
    )
    foreach ($candidate in $workspaceCandidates) {
        if ($candidate -like "*`**") {
            $match = Get-Item -Path $candidate -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($match) {
                $WorkspaceRoot = $match.FullName
                break
            }
        } elseif (Test-Path -LiteralPath $candidate) {
            $WorkspaceRoot = $candidate
            break
        }
    }
    if (-not $WorkspaceRoot) {
        throw "No CAD workspace root found in known locations."
    }
}

if (-not $JobsRoot) {
    $jobCandidates = @(
        (Join-Path (Split-Path -Parent $WorkspaceRoot) "cad_jobs_local"),
        "C:\cad_jobs"
    )
    $resolvedJobsRoot = $jobCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $resolvedJobsRoot) {
        throw "No CAD jobs root found in known locations."
    }
    $JobsRoot = $resolvedJobsRoot
}

$exporter = Join-Path $RepoRoot "scripts\export_cad_trace_snapshot.py"
if (-not (Test-Path -LiteralPath $PythonExe)) { throw "Python runtime not found: $PythonExe" }
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (-not (Test-Path -LiteralPath $exporter)) { throw "Snapshot exporter not found: $exporter" }
if (-not (Test-Path -LiteralPath $WorkspaceRoot)) { throw "Workspace root not found: $WorkspaceRoot" }
if (-not (Test-Path -LiteralPath $JobsRoot)) { throw "Jobs root not found: $JobsRoot" }

& $PythonExe $exporter --workspace-root $WorkspaceRoot --jobs-root $JobsRoot --repo-root $RepoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Snapshot export failed with exit code $LASTEXITCODE"
}

$userNameRaw = & $gitCmd -C $RepoRoot config user.name
$userName = if ($null -eq $userNameRaw) { "" } else { "$userNameRaw".Trim() }
if (-not $userName) {
    & $gitCmd -C $RepoRoot config user.name "Codex CAD Sync" | Out-Null
}

$userEmailRaw = & $gitCmd -C $RepoRoot config user.email
$userEmail = if ($null -eq $userEmailRaw) { "" } else { "$userEmailRaw".Trim() }
if (-not $userEmail) {
    & $gitCmd -C $RepoRoot config user.email "codex-cad-sync@users.noreply.github.com" | Out-Null
}

& $gitCmd -C $RepoRoot add -- scripts/export_cad_trace_snapshot.py scripts/sync_cad_trace_snapshot.ps1 scripts/register_cad_trace_sync_task.ps1 docs/cad_exact_trace_sync

$pending = (& $gitCmd -C $RepoRoot status --porcelain).Trim()
if (-not $pending) {
    Write-Host "No CAD sync changes to commit."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
& $gitCmd -C $RepoRoot commit -m "chore: sync cad exact trace snapshot $timestamp" | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Snapshot commit failed with exit code $LASTEXITCODE"
}

& $gitCmd -C $RepoRoot pull --rebase origin main | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Git pull --rebase did not complete. Snapshot was committed locally and needs manual attention."
    exit 0
}

& $gitCmd -C $RepoRoot push origin main | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Git push did not complete. Snapshot was committed locally. Finish Git credential sign-in on this PC and the scheduled sync will start pushing automatically."
    exit 0
}

Write-Host "CAD snapshot pushed to GitHub."
