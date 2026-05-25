# Security Policy

StarBridge is a public collaboration repository for local creative-software bridge research. The public repository must not contain private projects, real assets, model files, account data, local machine paths, or generated outputs.

## Supported Scope

Security review currently covers:

- StarBridge status and probe code.
- Public examples under `examples/`.
- Public documentation under `docs/`.
- CI and repository safety scripts.

Local desktop automation for Photoshop, Illustrator, Blender, AutoCAD, ComfyUI, and Jianying / CapCut depends on software installed and licensed on the user's machine. Do not report missing local commercial software as a vulnerability by itself.

## Do Not Commit

- Passwords, tokens, cookies, OAuth caches, account details, or payment data.
- Real user home paths, application cache paths, desktop paths, document paths, install locations, source asset paths, or export paths.
- ComfyUI models, LoRA, VAE, ControlNet files, generated images, or output folders.
- PSD, AI, DWG, DXF, video files, private drafts, customer drawings, or purchased assets.
- Jianying / CapCut real draft directories or draft content files.

## Reporting

Open a GitHub issue for public-safe problems such as missing redaction, unsafe defaults, or CI guardrail gaps. If the report contains credentials, private paths, customer content, or proprietary files, do not paste them into an issue. Share only a redacted summary and coordinate a private remediation path with the repository owner.

## Baseline Checks

Before opening a PR, run:

```powershell
python -m unittest discover -s tests
python -m starbridge_mcp.server --json
powershell -ExecutionPolicy Bypass -File scripts\check_forbidden_files.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_repository_safety.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1
```
