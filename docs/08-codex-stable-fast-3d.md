# Codex Stable Fast 3D local bridge

Stable Fast 3D is useful when StarBridge needs a local image-to-3D asset generator before handing GLB/OBJ/FBX outputs
to Blender or another DCC tool. This repository does not redistribute the upstream project or model weights; it keeps a
small Windows integration package under `integrations/stable-fast-3d/`.

## Local Workflow

```text
input image -> background removal mask -> SF3D mesh generation -> texture baking -> GLB export -> Blender cleanup
```

Recommended local layout:

```text
D:\AIGC\stable-fast-3d
D:\AIGC\hf-cache\hub
D:\AIGC\u2net
```

## Entry Points

- `integrations/stable-fast-3d/install_windows.ps1`
- `integrations/stable-fast-3d/start_sf3d_gradio.bat`
- `integrations/stable-fast-3d/patches/texture_baker_cpu_fallback.patch`
- `examples/stable_fast_3d_bridge/probe.py`

## Verification Notes

The local Windows run used an 8 GB VRAM NVIDIA laptop GPU. The official `chair1.png` sample exported `mesh.glb` with
about 6.2 GB peak VRAM at 512 texture resolution.

The main Windows compatibility issue was `texture_baker_cpp::rasterize` lacking a CUDA backend. The included patch moves
that texture-baking operation through the CPU operator while keeping the model inference path on CUDA.

## Repository Boundary

Do not commit:

- Hugging Face tokens
- model weights or ONNX files
- `.venv`
- local generated meshes
- private source images
