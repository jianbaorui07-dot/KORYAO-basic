# Stable Fast 3D bridge example

This example records the local SF3D image-to-3D bridge status for StarBridge. It is intentionally read-mostly and does
not submit generation jobs by default.

## Safe Boundaries

- Do not commit generated 3D assets.
- Do not commit model weights, ONNX files, Hugging Face tokens, or `.venv`.
- Keep generated outputs under `D:\AIGC\stable-fast-3d\outputs` or another ignored local directory.
- Treat SF3D as an external dependency installed from the official upstream repository.

## Probe

```powershell
python examples\stable_fast_3d_bridge\probe.py
python examples\stable_fast_3d_bridge\probe.py --json
```

Optional environment variables:

```powershell
$env:SF3D_ROOT="D:\AIGC\stable-fast-3d"
$env:SF3D_URL="http://127.0.0.1:7860"
$env:HUGGINGFACE_HUB_CACHE="D:\AIGC\hf-cache\hub"
$env:U2NET_HOME="D:\AIGC\u2net"
```
