$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$forbiddenExtensions = @(
    ".safetensors", ".ckpt", ".pt", ".pth",
    ".psd", ".ai", ".ait", ".dwg", ".dxf",
    ".mp4", ".mov", ".mkv", ".avi", ".webm",
    ".prproj", ".aep", ".aepx"
)
$forbiddenPathParts = @(
    "research_repos/", "third_party_research/", "output/", "scratch/",
    "node_modules/", "__pycache__/"
)

$tracked = git -C $repoRoot ls-files
$failures = New-Object System.Collections.Generic.List[string]

foreach ($file in $tracked) {
    $normalized = $file.Replace("\", "/")
    $extension = ""
    if ($normalized -match "(\.[^./]+)$") {
        $extension = $Matches[1].ToLowerInvariant()
    }
    if ($forbiddenExtensions -contains $extension) {
        $failures.Add("forbidden tracked extension: $normalized")
    }
    if ($normalized -eq ".env" -or $normalized.StartsWith(".env/")) {
        $failures.Add("forbidden tracked path: $normalized")
    }
    foreach ($part in $forbiddenPathParts) {
        if ($normalized -eq $part.TrimEnd("/") -or $normalized.StartsWith($part)) {
            $failures.Add("forbidden tracked path: $normalized")
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "forbidden file check passed"
