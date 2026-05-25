# Contributing

StarBridge keeps the public repository focused on Codex integration with local creative software. Contributions should be small, reviewable, and public-safe.

## Scope

Preferred contributions:

- Bridge status and probe improvements.
- Public-safe examples with placeholder inputs.
- Chinese-first documentation for setup, safety boundaries, and bridge status.
- Tests and CI checks that do not require commercial desktop software.

Out of scope for public PRs:

- Private assets, generated media, model files, customer drawings, and real software drafts.
- Hardcoded local paths, install locations, cache directories, or output folders.
- New bridge development mixed into release-readiness or documentation-only work.

## Local Checks

Run the core checks before submitting:

```powershell
python -m unittest discover -s tests
python -m starbridge_mcp.server --json
python examples\bridge_status.py --json
powershell -ExecutionPolicy Bypass -File scripts\check_forbidden_files.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_repository_safety.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1
```

`python -m starbridge_mcp.server --json --strict` may return exit code 1 when local software is not configured. That is acceptable outside CI if the non-ready bridges return structured `warnings` and `next_steps`.

## Pull Request Rules

- Keep README edits small unless the PR is explicitly about README structure.
- Do not use broad staging for mixed work. Stage only the files needed for the PR.
- Do not include CAD/DXF, ComfyUI model, Adobe project, video, or Jianying / CapCut draft files.
- If a script writes output, keep it under an ignored demo output directory and never under a real draft or project directory.
