$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

python (Join-Path $repoRoot "scripts/security_check.py")

$status = git -C $repoRoot status --porcelain
$forbiddenUntracked = $status | Where-Object {
    $_ -match "^\?\?" -and (
        $_ -match "\.(safetensors|ckpt|pt|pth|psd|ai|ait|dwg|dxf|mp4|mov|mkv|avi|webm)$" -or
        $_ -match "(^|[\\/])\.env($|[\\/])" -or
        $_ -match "(research_repos|third_party_research|output|scratch|node_modules|__pycache__)"
    )
}

if ($forbiddenUntracked) {
    Write-Error "Forbidden untracked files are present. Move them outside the repo before publishing."
    $forbiddenUntracked | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "repository safety check passed"
