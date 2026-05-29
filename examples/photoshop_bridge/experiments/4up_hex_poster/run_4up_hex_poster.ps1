param(
    [string]$PythonExe = "python",
    [switch]$GenerateOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Generator = Join-Path $ScriptDir "generate_4up_hex_photoshop_poster.py"

if (-not (Test-Path $Generator)) {
    throw "Missing generator: $Generator"
}

Push-Location $ScriptDir
try {
    & $PythonExe $Generator
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $jsx = Join-Path $ScriptDir "photoshop_4up_hex_automation\generate_4up_hex_poster.jsx"
    if (-not (Test-Path $jsx)) {
        throw "Generator did not create JSX: $jsx"
    }

    if ($GenerateOnly) {
        Write-Host "Generated Photoshop JSX only: $jsx"
        exit 0
    }

    $ps = New-Object -ComObject Photoshop.Application
    $ps.Visible = $true
    $ps.DoJavaScriptFile((Resolve-Path $jsx).Path)
    Write-Host "Photoshop 4-up hex poster automation completed."
}
finally {
    Pop-Location
}
