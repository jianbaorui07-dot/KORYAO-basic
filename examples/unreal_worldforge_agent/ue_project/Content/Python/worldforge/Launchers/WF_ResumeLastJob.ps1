param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
$StatePath = Join-Path $ProjectRoot 'Saved\WorldForge\run_state.json'
if (-not (Test-Path -LiteralPath $StatePath)) {
    throw "No run_state.json found."
}
$state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if (-not $state.active_recipe_path) {
    throw "run_state.json has no active_recipe_path to resume."
}
if ($state.phase -in @('FRAMEWORK_READY', 'DONE') -and -not $Force) {
    [pscustomobject]@{
        status = 'nothing_to_resume'
        phase = $state.phase
        active_scene_id = $state.active_scene_id
        active_recipe_path = $state.active_recipe_path
    } | ConvertTo-Json -Depth 4
    exit 0
}
& (Join-Path $PSScriptRoot 'WF_RunRecipe.ps1') -RecipePath $state.active_recipe_path -Force:$Force
