$ErrorActionPreference = "Stop"

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "SF3D Local Gradio.lnk"
$targetScript = "D:\AIGC\stable-fast-3d\start_sf3d_gradio.bat"

if (-not (Test-Path -LiteralPath $targetScript)) {
    throw "Start script not found: $targetScript"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$shortcut.Arguments = "/k `"$targetScript`""
$shortcut.WorkingDirectory = "D:\AIGC\stable-fast-3d"
$shortcut.Description = "Start Stable Fast 3D local Gradio"
$shortcut.IconLocation = "C:\Windows\System32\shell32.dll,13"
$shortcut.Save()

Write-Host "Created shortcut: $shortcutPath"
