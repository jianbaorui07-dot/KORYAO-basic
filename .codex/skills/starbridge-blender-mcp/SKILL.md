---
name: starbridge-blender-mcp
description: Use StarBridge Blender MCP safely from Codex. Use when the user mentions Blender, .blend, scene plans, 3D objects, materials, render, viewport, Blender MCP, blender.environment_probe, blender.scene_plan, or asks Codex to inspect or extend Blender-related StarBridge MCP tools.
---

# StarBridge Blender MCP

## Core Rule

Prefer environment probes and dry-run scene plans before launching Blender or rendering. Treat `.blend` files, textures, asset libraries, render caches, and generated frames as private unless the user provides a public test asset.

Do not open private `.blend` files, run arbitrary Blender Python, scan asset libraries, download models, or render to tracked paths.

## Read First

Read only what is needed:

- `docs/04-codex-blender.md`
- `examples/blender_bridge/`
- `examples/blender_bridge/probe.py`
- `examples/blender_bridge/scene_plan.py`
- `starbridge_mcp/bridges/blender_safe_scene.py`
- `tests/test_computer_use_plans.py`
- `tests/test_tool_registry.py`

If available and the task is scene safety specific, also use `.codex/skills/blender-safe-scene-skill/SKILL.md`. If changing shared MCP behavior, read `.codex/skills/starbridge-mcp/SKILL.md`.

## Safe Commands

```powershell
npm.cmd run blender:scene:plan
python examples\blender_bridge\probe.py --json
python examples\blender_bridge\scene_plan.py --json
python -m starbridge_mcp.server tools --json --safe-only
python examples\bridge_status.py --json --redact-paths --soft-exit
python scripts\security_check.py
```

Do not require Blender in CI. A missing Blender executable should return a structured warning, not a crash.

## Tool Routing

| Need | Preferred tool path | Boundary |
| --- | --- | --- |
| Check Blender availability | `blender.environment_probe` | Read-only, no `.blend` open |
| Build safe scene idea | `blender.scene_plan` | Dry-run JSON plan only |
| Inspect real viewport | Computer Use only if user asks for GUI diagnosis | No private asset scan |
| Render | future confirmed sandbox recipe | No tracked output, no private textures |

## Forbidden Work

Do not add tools that:

- execute arbitrary Python inside Blender
- open arbitrary `.blend` files
- load private texture or asset folders
- download model assets
- write renders outside ignored output directories
- commit screenshots, frames, caches, or `.blend` outputs

Use fixed templates, safe parameters, and sanitized evidence.

## Validation

After Blender MCP changes, run:

```powershell
python -m unittest discover -s tests
python scripts\starbridge_preflight.py --markdown
python scripts\security_check.py
python -m starbridge_mcp.server tools --json --safe-only
npm.cmd test
```

Report Blender desktop or CLI checks as local-only. CI should validate schema, dry-run plans, metadata, and safety boundaries without launching Blender.
