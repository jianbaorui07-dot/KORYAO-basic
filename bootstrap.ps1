[CmdletBinding()]
param(
    [ValidateSet("auto", "core", "standard", "all")]
    [string]$Profile = "auto",
    [switch]$SkipNode,
    [switch]$SkipCodexConfig,
    [switch]$DryRun,
    [switch]$Json
)

$quickstart = Join-Path $PSScriptRoot "scripts\quickstart.ps1"
if (-not (Test-Path -LiteralPath $quickstart)) {
    throw "Missing scripts\quickstart.ps1"
}

$arguments = @("-Profile", $Profile)
if ($SkipNode) { $arguments += "-SkipNode" }
if ($SkipCodexConfig) { $arguments += "-SkipCodexConfig" }
if ($DryRun) { $arguments += "-DryRun" }
if ($Json) { $arguments += "-Json" }
& $quickstart @arguments
exit $LASTEXITCODE
