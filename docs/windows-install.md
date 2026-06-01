# Windows 安装说明

StarBridge v0.1.0-alpha 面向 Windows-first / local-first 工作站。最小开发环境不需要安装 Adobe、AutoCAD、Blender、ComfyUI 或 CapCut；缺少这些软件时，探针应返回结构化 warning 或 unavailable，而不是让 CI 失败。

## 基础环境

- Windows 10/11 或 GitHub Actions `windows-2022`
- Python 3.10+
- Node.js 24，用于提前验证 `package.json` 和 npm scripts
- PowerShell 5+ 或 PowerShell 7+

## 安装步骤

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
node --version
npm --version
```

如果 PowerShell 拦截 `npm.ps1`，使用 `npm.cmd`：

```powershell
npm.cmd test
npm.cmd run starbridge:tools:safe
```

## 可选本机软件

这些软件只用于本机 smoke test，不是 CI 必需项：

| Bridge | Optional local app | Environment hints |
| --- | --- | --- |
| ComfyUI | Running local ComfyUI HTTP API | `STARBRIDGE_COMFYUI_URL` |
| Blender | Blender desktop or CLI | `STARBRIDGE_BLENDER_EXE` or `BLENDER_EXE` |
| AutoCAD/DXF | AutoCAD desktop for COM tests; `ezdxf` for sandbox DXF export | `AUTOCAD_EXE`, `STARBRIDGE_CAD_MODE` |
| Photoshop | Authorized Adobe Photoshop desktop | `PHOTOSHOP_EXE` |
| Illustrator | Authorized Adobe Illustrator desktop | `ILLUSTRATOR_EXE` |
| Jianying/CapCut | Local desktop app and draft directory | `JIANYING_EXE`, `CAPCUT_EXE`, `JIANYING_DRAFTS_DIR`, `CAPCUT_DRAFTS_DIR` |

Do not write real install paths into tracked files. Use local environment variables or a private `.env` file.

## Verification

```powershell
python -m unittest discover -s tests
python scripts\security_check.py
python scripts\starbridge_preflight.py --markdown
npm.cmd test
```

Real writes remain guarded: default `dry_run=true`; real output requires `confirm_write=true` or `confirm_export=true` and must stay under `examples/output/` or `examples/cad/output/`.
