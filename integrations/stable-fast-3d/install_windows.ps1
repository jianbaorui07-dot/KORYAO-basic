param(
    [string]$Root = "D:\AIGC",
    [switch]$UseProxy,
    [string]$ProxyUrl = "http://127.0.0.1:7897"
)

$ErrorActionPreference = "Stop"

$ProjectDir = Join-Path $Root "stable-fast-3d"
$HfCache = Join-Path $Root "hf-cache\hub"
$U2netHome = Join-Path $Root "u2net"
$PatchFile = Join-Path $PSScriptRoot "patches\texture_baker_cpu_fallback.patch"
$StartScript = Join-Path $PSScriptRoot "start_sf3d_gradio.bat"

New-Item -ItemType Directory -Force -Path $Root, $HfCache, $U2netHome | Out-Null

if ($UseProxy) {
    $env:HTTP_PROXY = $ProxyUrl
    $env:HTTPS_PROXY = $ProxyUrl
}

$env:HUGGINGFACE_HUB_CACHE = $HfCache
$env:U2NET_HOME = $U2netHome
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it first, then rerun this script."
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    git clone https://github.com/Stability-AI/stable-fast-3d.git $ProjectDir
}

Set-Location $ProjectDir

uv python install 3.11
uv venv .venv --python 3.11
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
uv pip install pip setuptools==69.5.1 wheel

$reqNoLocal = Join-Path $env:TEMP "sf3d-req-no-local.txt"
Get-Content -LiteralPath "requirements.txt" |
    Where-Object { $_ -and ($_ -notmatch '^\./') } |
    Set-Content -LiteralPath $reqNoLocal -Encoding ascii

& ".venv\Scripts\python.exe" -m pip install -r $reqNoLocal -r requirements-demo.txt
& ".venv\Scripts\python.exe" -m pip install "fastapi==0.112.2" "starlette==0.38.6" "pydantic==2.8.2" "pydantic-core==2.20.1"

if (Test-Path -LiteralPath $PatchFile) {
    git apply --check $PatchFile 2>$null
    if ($LASTEXITCODE -eq 0) {
        git apply $PatchFile
    } else {
        Write-Host "Patch is already applied or cannot be applied cleanly; continuing."
    }
}

$vsDevCmd = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
if (-not (Test-Path -LiteralPath $vsDevCmd)) {
    throw "Visual Studio 2022 Build Tools with C++ workload is required. Example: winget install --id Microsoft.VisualStudio.2022.BuildTools -e"
}

& cmd.exe /d /c "`"$vsDevCmd`" -arch=x64 && set `"DISTUTILS_USE_SDK=1`" && set `"MSSdk=1`" && `"$ProjectDir\.venv\Scripts\python.exe`" -m pip install --no-build-isolation ./texture_baker ./uv_unwrapper"

& ".venv\Scripts\huggingface-cli.exe" download stabilityai/stable-fast-3d config.yaml model.safetensors
& ".venv\Scripts\python.exe" -u -c "import rembg; rembg.new_session(); from sf3d.system import SF3D; SF3D.from_pretrained('stabilityai/stable-fast-3d', config_name='config.yaml', weight_name='model.safetensors'); print('SF3D cache ready')"

Copy-Item -LiteralPath $StartScript -Destination (Join-Path $ProjectDir "start_sf3d_gradio.bat") -Force

Write-Host "Stable Fast 3D is installed at $ProjectDir"
Write-Host "Start it with: $ProjectDir\start_sf3d_gradio.bat"
