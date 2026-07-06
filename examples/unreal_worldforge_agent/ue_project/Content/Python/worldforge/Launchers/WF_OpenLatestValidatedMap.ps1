param(
    [string]$RecipePath = ""
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
if ([string]::IsNullOrWhiteSpace($RecipePath)) {
    $RecipePath = Join-Path $ProjectRoot 'Config\WorldForge\Recipes\WF0009_SnowTemple_R1.json'
}
& (Join-Path $PSScriptRoot 'WF_RunRecipe.ps1') -RecipePath $RecipePath -Force:$false
