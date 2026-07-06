param(
    [string]$RecipePath = "",
    [switch]$Force,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

function Get-ProjectRoot {
    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

function Write-Utf8Json {
    param([string]$Path, [object]$Payload, [int]$Depth = 12)
    [System.IO.Directory]::CreateDirectory((Split-Path -Parent $Path)) | Out-Null
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, (($Payload | ConvertTo-Json -Depth $Depth) + [Environment]::NewLine), $utf8)
}

function Get-FreeMemoryGB {
    $os = Get-CimInstance Win32_OperatingSystem
    [math]::Round(($os.FreePhysicalMemory * 1KB) / 1GB, 2)
}

function Get-CDriveFreeGB {
    [math]::Round((Get-PSDrive -Name C).Free / 1GB, 2)
}

function Test-ValidPng {
    param([string]$Path, [int]$MinBytes = 16384)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path
    if ($item.Length -le $MinBytes) { return $false }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $bytes = New-Object byte[] 8
        if ($stream.Read($bytes, 0, 8) -ne 8) { return $false }
        $expected = [byte[]](0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)
        for ($i = 0; $i -lt 8; $i++) {
            if ($bytes[$i] -ne $expected[$i]) { return $false }
        }
        return $true
    }
    finally {
        $stream.Dispose()
    }
}

function Convert-MapToDiskPath {
    param([string]$ProjectRoot, [string]$MapAssetPath)
    if (-not $MapAssetPath.StartsWith('/Game/')) {
        throw "Unsupported map path: $MapAssetPath"
    }
    $relative = $MapAssetPath.Substring(6).Replace('/', '\') + '.umap'
    Join-Path (Join-Path $ProjectRoot 'Content') $relative
}

function Write-RunState {
    param(
        [string]$ProjectRoot,
        [hashtable]$Update
    )
    $statePath = Join-Path $ProjectRoot 'Saved\WorldForge\run_state.json'
    $runtimePath = Join-Path $ProjectRoot 'runtime\run_state.json'
    $current = @{}
    if (Test-Path -LiteralPath $statePath) {
        $raw = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        foreach ($prop in $raw.PSObject.Properties) { $current[$prop.Name] = $prop.Value }
    }
    foreach ($key in $Update.Keys) { $current[$key] = $Update[$key] }
    $current['framework_version'] = '1.0.0'
    $current['available_memory_gb'] = Get-FreeMemoryGB
    $current['c_drive_free_gb'] = Get-CDriveFreeGB
    $current['source_of_truth'] = $statePath
    $current['updated_at'] = (Get-Date).ToString('o')
    Write-Utf8Json -Path $statePath -Payload $current
    $mirror = @{}
    foreach ($key in $current.Keys) { $mirror[$key] = $current[$key] }
    $mirror['compatibility_mirror_of'] = $statePath
    $mirror['mirror_note'] = 'Saved\WorldForge\run_state.json is the only authoritative state file.'
    Write-Utf8Json -Path $runtimePath -Payload $mirror
}

function Get-UProject {
    param([string]$ProjectRoot)
    $items = @(Get-ChildItem -LiteralPath $ProjectRoot -Filter '*.uproject' -File)
    if ($items.Count -ne 1) { throw "Expected one .uproject, found $($items.Count)" }
    $items[0].FullName
}

function Start-VisibleEditor {
    param(
        [string]$ProjectRoot,
        [string]$MapAssetPath,
        [object]$Recipe
    )
    $editor = '<UE_5_2_ROOT>\Engine\Binaries\Win64\UnrealEditor.exe'
    if (-not (Test-Path -LiteralPath $editor)) { throw "UnrealEditor.exe missing: $editor" }
    $uproject = Get-UProject -ProjectRoot $ProjectRoot
    $logDir = '<WORLDFORGE_RUNTIME>\Logs'
    [System.IO.Directory]::CreateDirectory($logDir) | Out-Null
    $stdout = Join-Path $logDir "$($Recipe.scene_id)_$($Recipe.scene_revision)_visible_editor_stdout.log"
    $stderr = Join-Path $logDir "$($Recipe.scene_id)_$($Recipe.scene_revision)_visible_editor_stderr.log"
    $argLine = "`"$uproject`" $MapAssetPath -log"
    $existing = @(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" | Where-Object { $_.CommandLine -like "*$MapAssetPath*" })
    if ($existing.Count -gt 0) {
        $pid = [int]$existing[0].ProcessId
        $started = $false
    }
    else {
        $proc = Start-Process -FilePath $editor -ArgumentList $argLine -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $pid = [int]$proc.Id
        $started = $true
    }
    $checks = @()
    for ($i = 0; $i -lt 6; $i++) {
        Start-Sleep -Seconds 5
        $live = Get-Process -Id $pid -ErrorAction SilentlyContinue
        $checks += [ordered]@{
            elapsed_seconds = (($i + 1) * 5)
            running = ($null -ne $live)
            working_set_mb = $(if ($live) { [math]::Round($live.WorkingSet64 / 1MB, 2) } else { $null })
        }
        if (-not $live) { break }
    }
    return [ordered]@{
        editor_pid = $pid
        editor_started_new_process = $started
        editor_running_after_30s = ($checks.Count -eq 6 -and $checks[-1].running)
        editor_args = $argLine
        editor_stdout = $stdout
        editor_stderr = $stderr
        editor_checks = $checks
    }
}

$projectRoot = Get-ProjectRoot
if ([string]::IsNullOrWhiteSpace($RecipePath)) {
    $RecipePath = Join-Path $projectRoot 'Config\WorldForge\Recipes\WF0009_SnowTemple_R1.json'
}
if (-not [System.IO.Path]::IsPathRooted($RecipePath)) {
    $RecipePath = Join-Path $projectRoot $RecipePath
}
if (-not (Test-Path -LiteralPath $RecipePath)) {
    $candidate = Join-Path (Join-Path $projectRoot 'Config\WorldForge\Recipes') (Split-Path -Leaf $RecipePath)
    if (Test-Path -LiteralPath $candidate) {
        $RecipePath = $candidate
    }
}
$RecipePath = (Resolve-Path -LiteralPath $RecipePath).Path
$recipe = Get-Content -LiteralPath $RecipePath -Raw | ConvertFrom-Json

$runtimeDirs = @('<WORLDFORGE_RUNTIME>\DDC','<WORLDFORGE_RUNTIME>\Logs','<WORLDFORGE_RUNTIME>\Previews','<WORLDFORGE_RUNTIME>\Receipts')
foreach ($dir in $runtimeDirs) { [System.IO.Directory]::CreateDirectory($dir) | Out-Null }

$policy = if ([string]$recipe.mode -like 'P2*') { 'P2_STANDARD' } else { 'P1_LIGHTWEIGHT' }
$mapDiskPath = Convert-MapToDiskPath -ProjectRoot $projectRoot -MapAssetPath $recipe.map_asset_path
$previewPath = [string]$recipe.preview_profile.target_path
$minBytes = if ($recipe.preview_profile.min_bytes) { [int]$recipe.preview_profile.min_bytes } else { 16384 }

Write-RunState -ProjectRoot $projectRoot -Update @{
    phase = 'PREFLIGHT'
    active_scene_id = $recipe.scene_id
    active_recipe_path = $RecipePath
    requested_map_path = $recipe.map_asset_path
    resource_policy = $policy
    ddc_path = '<WORLDFORGE_RUNTIME>\DDC'
    ddc_exists = (Test-Path -LiteralPath '<WORLDFORGE_RUNTIME>\DDC')
    last_error = ''
}

if ($recipe.mode -eq 'DEFINITION_ONLY') {
    $receipt = [ordered]@{
        status = 'definition_only'
        scene_id = $recipe.scene_id
        recipe_path = $RecipePath
        message = 'Recipe is defined but no builder is enabled yet.'
        written_at = (Get-Date).ToString('o')
    }
    $receiptPath = Join-Path $projectRoot "Saved\WorldForge\Receipts\$($recipe.scene_id)_definition_only_receipt.json"
    Write-Utf8Json -Path $receiptPath -Payload $receipt
    Write-RunState -ProjectRoot $projectRoot -Update @{
        phase = 'BUILD_SKIPPED'
        active_scene_id = $recipe.scene_id
        active_recipe_path = $RecipePath
        build_skipped_reason = 'definition_only_recipe'
        last_receipt_path = $receiptPath
        last_error = 'WF0010_builder_not_implemented'
    }
    exit 0
}

if ($recipe.build_strategy -eq 'existing_validated_map' -and -not (Test-Path -LiteralPath $mapDiskPath)) {
    throw "Existing validated map is missing: $mapDiskPath"
}

$validationReceipt = Join-Path $projectRoot "Saved\WorldForge\Receipts\$($recipe.scene_id)_R1_test_validation.json"
if ($recipe.scene_id -eq 'WF0009') {
    $validationReceipt = Join-Path $projectRoot 'Saved\WorldForge\Receipts\WF0009_R1_test_validation.json'
}
if (-not (Test-Path -LiteralPath $validationReceipt)) {
    throw "Validation receipt missing: $validationReceipt"
}
$previewValid = Test-ValidPng -Path $previewPath -MinBytes $minBytes

if ((-not $previewValid) -and (-not $Force)) {
    throw "Preview is missing or invalid. Re-run with -Force to regenerate preview."
}

if ((-not $previewValid) -and $Force) {
    $editor = '<UE_5_2_ROOT>\Engine\Binaries\Win64\UnrealEditor.exe'
    $uproject = Get-UProject -ProjectRoot $projectRoot
    $previewScript = Join-Path $projectRoot 'Content\Python\WorldForge\Core\camera_preview.py'
    $previewReceipt = "<WORLDFORGE_RUNTIME>\Logs\$($recipe.scene_id)_$($recipe.scene_revision)_preview_receipt.json"
    $previewStdout = "<WORLDFORGE_RUNTIME>\Logs\$($recipe.scene_id)_$($recipe.scene_revision)_preview_stdout.log"
    $previewStderr = "<WORLDFORGE_RUNTIME>\Logs\$($recipe.scene_id)_$($recipe.scene_revision)_preview_stderr.log"
    [Environment]::SetEnvironmentVariable('WORLDFORGE_PROJECT_ROOT', $projectRoot, 'Process')
    [Environment]::SetEnvironmentVariable('WORLDFORGE_RECIPE_PATH', $RecipePath, 'Process')
    [Environment]::SetEnvironmentVariable('WORLDFORGE_PREVIEW_PATH', $previewPath, 'Process')
    [Environment]::SetEnvironmentVariable('WORLDFORGE_PREVIEW_RECEIPT', $previewReceipt, 'Process')
    [Environment]::SetEnvironmentVariable('WORLDFORGE_QUIT_AFTER_PREVIEW', '1', 'Process')
    [Environment]::SetEnvironmentVariable('UE-LocalDataCachePath', '<WORLDFORGE_RUNTIME>\DDC', 'Process')
    $safeScript = $previewScript.Replace('\', '/')
    $exec = "py exec(open(r'$safeScript').read())"
    $argLine = "`"$uproject`" $($recipe.map_asset_path) -nosplash -log -ExecCmds=`"$exec`""
    $proc = Start-Process -FilePath $editor -ArgumentList $argLine -PassThru -RedirectStandardOutput $previewStdout -RedirectStandardError $previewStderr
    $deadline = (Get-Date).AddSeconds(240)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        if (Test-Path -LiteralPath $previewReceipt) {
            $previewState = Get-Content -LiteralPath $previewReceipt -Raw | ConvertFrom-Json
            if ($previewState.status -eq 'preview_ready') { break }
            if ($previewState.status -eq 'preview_timeout' -or $previewState.status -eq 'failed') { throw "Preview failed: $($previewState.status)" }
        }
        if (-not (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)) { break }
    }
    $previewValid = Test-ValidPng -Path $previewPath -MinBytes $minBytes
    if (-not $previewValid) { throw "Preview regeneration did not produce a valid PNG." }
}

$launch = $null
if (-not $NoOpen) {
    Write-RunState -ProjectRoot $projectRoot -Update @{ phase = 'EDITOR_LAUNCHING'; preview_exists = $true; preview_path = $previewPath }
    $launch = Start-VisibleEditor -ProjectRoot $projectRoot -MapAssetPath $recipe.map_asset_path -Recipe $recipe
}

$receipt = [ordered]@{
    status = 'validated'
    scene_id = $recipe.scene_id
    recipe_path = $RecipePath
    map_asset_path = $recipe.map_asset_path
    map_disk_path = $mapDiskPath
    map_exists = (Test-Path -LiteralPath $mapDiskPath)
    validation_receipt_path = $validationReceipt
    preview_path = $previewPath
    preview_valid = $previewValid
    launch = $launch
    written_at = (Get-Date).ToString('o')
}
$receiptPath = Join-Path $projectRoot "Saved\WorldForge\Receipts\$($recipe.scene_id)_$($recipe.scene_revision)_run_recipe_receipt.json"
Write-Utf8Json -Path $receiptPath -Payload $receipt

$phase = if ($launch -and $launch.editor_running_after_30s) { 'DONE' } elseif ($NoOpen) { 'FRAMEWORK_READY' } else { 'FAILED' }
Write-RunState -ProjectRoot $projectRoot -Update @{
    phase = $phase
    active_scene_id = $recipe.scene_id
    active_recipe_path = $RecipePath
    actual_map_exists = (Test-Path -LiteralPath $mapDiskPath)
    validation_receipt_path = $validationReceipt
    preview_exists = $previewValid
    preview_path = $previewPath
    ue_process_running = $(if ($launch) { $launch.editor_running_after_30s } else { $false })
    ue_pid = $(if ($launch) { $launch.editor_pid } else { $null })
    last_receipt_path = $receiptPath
    last_error = $(if ($phase -eq 'FAILED') { 'editor_not_running_after_30s' } else { '' })
}

if ($phase -eq 'FAILED') { exit 1 }
