# Contributing to CreNexus

谢谢你关注 CreNexus。这个仓库欢迎围绕 **AI agent / MCP / 本地创意软件自动化** 的安全改进、文档补充、探针脚本和测试用例。

This repository is Chinese-first, but English issues and pull requests are welcome. Please keep commands, environment variables, MCP tool names, file names, and API names in English.

## What Fits This Repository

Good contributions:

- Safer MCP stdio tools for local creative software.
- Read-only probes for ComfyUI, Blender, AutoCAD, Photoshop, Illustrator, CapCut / Jianying, and similar tools.
- Workflow validators, JSON schemas, redacted status output, and tests.
- Documentation that helps users run the bridge without exposing private paths or assets.
- Small examples that work without commercial assets, private projects, model files, or account secrets.

Please avoid:

- Private PSD, AI, DWG, blend files, drafts, model checkpoints, LoRA, VAE, generated images, videos, client assets, or paid fonts.
- Hard-coded personal paths, usernames, install directories, tokens, cookies, OAuth cache, API keys, or license files.
- Broad refactors that are unrelated to a specific bridge or MCP tool.
- Automation that writes to private project files without an explicit confirmation flag.

## Development Setup

Use Windows PowerShell. Prefer `npm.cmd` on machines where PowerShell blocks `npm.ps1`.

```powershell
python -m unittest discover -s tests
python scripts\security_check.py
python scripts\starbridge_preflight.py --markdown
npm.cmd test
```

Useful local commands:

```powershell
npm.cmd run bridge:status:safe
npm.cmd run starbridge:tools:safe
npm.cmd run starbridge:mcp
```

Some checks depend on local desktop software. AutoCAD, Photoshop, Illustrator, Blender, ComfyUI, CapCut, and Jianying are optional unless your change specifically targets that bridge.

## Pull Request Checklist

- Keep the change focused on one bridge, one tool, or one documentation topic.
- Add or update tests when behavior changes.
- Run the security check before publishing.
- Use parameterized input/output paths; do not commit real local paths.
- Mark experimental behavior clearly in docs and tool metadata.
- If a tool can write files, require an explicit confirmation argument and keep default behavior dry-run or read-only.

## Language Style

- Chinese is preferred for user-facing explanations.
- English is preferred for commands, config keys, API names, schemas, MCP tool names, and code identifiers.
- Write practical instructions first; keep roadmap claims conservative.
