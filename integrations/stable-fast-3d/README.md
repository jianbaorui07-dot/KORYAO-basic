# Stable Fast 3D local integration

This folder documents a Windows-first Stable Fast 3D setup for StarBridge users. It does not vendor the upstream
`Stability-AI/stable-fast-3d` repository, Hugging Face model weights, virtual environments, or generated 3D assets.

## What This Adds

- A repeatable local install path for `D:\AIGC\stable-fast-3d`.
- D-drive cache defaults for Hugging Face and `rembg` model files.
- A local Gradio launcher for `http://127.0.0.1:7860`.
- A Windows compatibility patch for `texture_baker` when its CUDA kernel is unavailable.
- A read-only probe example under `examples/stable_fast_3d_bridge/`.

## Local Layout

Recommended local folders:

```text
D:\AIGC\stable-fast-3d       upstream SF3D checkout and Python venv
D:\AIGC\hf-cache\hub         Hugging Face model cache
D:\AIGC\u2net                rembg / u2net background-removal model
D:\AIGC\stable-fast-3d\outputs
```

Large files stay outside this repository. Do not commit:

- `.venv/`
- `*.safetensors`, `*.onnx`, `*.ckpt`, `*.pt`, `*.pth`
- generated `.glb`, `.obj`, `.fbx`, `.stl`
- private Hugging Face tokens or browser/session data

## Install

Prerequisites:

- Windows 10/11
- NVIDIA GPU and current driver
- Git
- `uv`
- Visual Studio 2022 Build Tools with C++ workload
- Hugging Face account with access accepted for `stabilityai/stable-fast-3d`

Run:

```powershell
cd integrations\stable-fast-3d
.\install_windows.ps1
```

If Hugging Face needs your local proxy:

```powershell
.\install_windows.ps1 -UseProxy -ProxyUrl "http://127.0.0.1:7897"
```

After installation, start the local UI:

```powershell
D:\AIGC\stable-fast-3d\start_sf3d_gradio.bat
```

Or create a desktop shortcut:

```powershell
.\create_desktop_shortcut.ps1
```

## Why the Texture Baker Patch Exists

On some Windows installs, `texture_baker` compiles only the CPU operator even when PyTorch can use CUDA. The upstream
Gradio app keeps tensors on CUDA and then calls `texture_baker_cpp::rasterize`, which fails with:

```text
Could not run 'texture_baker_cpp::rasterize' with arguments from the 'CUDA' backend
```

The patch keeps model inference on the GPU but moves the final texture baking call through the CPU operator when needed.
This is slower than a native CUDA texture baker, but it allows GLB export on 8 GB VRAM Windows laptops.

## Local Validation

The setup was validated on:

- RTX 5060 Laptop GPU, 8 GB VRAM
- 32 GB system memory
- Python 3.11
- PyTorch CUDA 12.8
- SF3D Gradio on `http://127.0.0.1:7860`

The official `chair1.png` example exported `mesh.glb` successfully with about 6.2 GB peak VRAM at 512 texture resolution.
