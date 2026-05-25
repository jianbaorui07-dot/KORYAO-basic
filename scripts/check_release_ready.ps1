$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$requiredFiles = @(
    ".github/workflows/ci.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bridge-safety.yml",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "docs/security-checklist.md",
    "docs/release-checklist.md",
    "docs/project-structure.md",
    "docs/git-branch-workflow.md",
    "docs/starbridge-product-positioning.md",
    "docs/starbridge-competitive-analysis.md",
    "docs/starbridge-roadmap.md",
    "docs/codex-operation-manual.md",
    "scripts/check_repository_safety.ps1",
    "scripts/check_release_ready.ps1",
    "scripts/check_forbidden_files.ps1"
)

$missing = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $repoRoot $file))) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    $missing | ForEach-Object { Write-Error "missing release file: $_" }
    exit 1
}

python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m starbridge_mcp.server --json | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/security_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

powershell -ExecutionPolicy Bypass -File (Join-Path $repoRoot "scripts/check_forbidden_files.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "release readiness check passed"
