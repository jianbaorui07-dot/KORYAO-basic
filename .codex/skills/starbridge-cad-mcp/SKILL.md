---
name: starbridge-cad-mcp
description: Use CreNexus CAD and AutoCAD MCP safely from Codex. Use when the user mentions CAD, AutoCAD, DXF, DWG, CAD plan JSON, engineering drawing, layer validation, AutoCAD COM, cad-mcp-autocad, or asks Codex to inspect, validate, generate, or extend CAD-related CreNexus MCP tools.
---

# CreNexus CAD MCP

## Core Rule

Prefer offline CAD plan validation and DXF dry-run before any real AutoCAD desktop control. Treat DWG, customer drawings, licensed CAD files, and real project outputs as private.

Do not read commercial DWG/DXF files, scan project folders, open customer drawings, or write outside approved sandbox output.

## Read First

Read only what is needed:

- `docs/01-codex-cad.md`
- `AUTOCAD_MCP_SETUP.md`
- `cad-mcp-autocad/README.md`
- `cad-mcp-autocad/requirements.txt`
- `examples/cad/`
- `examples/cad_bridge/probe.py`
- `starbridge_mcp/bridges/autocad_dxf.py`
- `starbridge_mcp/bridges/cad_schema.py`
- `tests/test_autocad_dxf_bridge.py`
- `tests/test_sandbox_output_paths.py`

If changing shared MCP behavior, also read `.codex/skills/starbridge-mcp/SKILL.md`.

## Safe Commands

```powershell
npm.cmd run cad:dxf:dry-run
python examples\cad\generate_dxf_plan.py
python examples\cad_bridge\probe.py --json
python scripts\test_autocad_mcp.py
python -m starbridge_mcp.server tools --json --safe-only
python scripts\security_check.py
```

Run `scripts\test_autocad_mcp.py` only when the task is specifically about local AutoCAD MCP validation. It may require Windows and installed CAD software.

## Tool Routing

| Need | Preferred tool path | Boundary |
| --- | --- | --- |
| CAD environment check | `cad_autocad.environment_probe` | Read-only, no DWG open |
| Offline DXF status | `autocad_dxf.status` | No AutoCAD required |
| Validate plan | `autocad_dxf.validate_cad_plan` | JSON only |
| Create plan | `autocad_dxf.create_dxf_plan` | Plan first, no write |
| Summarize plan | `autocad_dxf.summarize_plan` | Read plan structure only |
| Write DXF | `autocad_dxf.write_dxf` | Dry-run by default; real write needs confirmation and sandbox |

## Write Rules

Any real DXF write must require:

- `confirm_write=true`
- output under `examples/cad/output`
- validated CAD JSON plan
- no path escaping
- sanitized result
- no customer project names or private dimensions unless user explicitly provided public specs

Never commit `.dwg`, `.dxf`, customer drawings, license files, or real project outputs.

## Validation

After CAD MCP changes, run:

```powershell
python -m unittest discover -s tests
python scripts\starbridge_preflight.py --markdown
python scripts\security_check.py
python -m starbridge_mcp.server tools --json --safe-only
npm.cmd test
```

Report AutoCAD desktop checks as manual or local-only. CI must keep CAD checks offline unless they are pure parser/schema/dry-run tests.
