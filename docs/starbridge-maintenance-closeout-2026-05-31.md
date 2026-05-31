# StarBridge maintenance closeout - 2026-05-31

This note records the current public-safe maintenance status for the StarBridge Creative Software MCP repository.

## Scope

- Keep the repository local-first and public-safe.
- Preserve MCP stdio discovery for safe tools.
- Add CAD / AutoCAD / DXF plan validation and summary capability before any DXF writer is enabled.
- Do not commit generated media, real local paths, customer files, PSD/AI/DWG/Blend assets, CapCut/Jianying drafts, tokens, cookies, or account caches.

## Implemented in the local working tree

The local working tree currently contains these verified changes:

- Public-boundary docs: SECURITY.md, CONTRIBUTING.md, ROADMAP.md.
- StarBridge preflight: scripts/starbridge_preflight.py.
- MCP stdio registry: starbridge_mcp/server.py and starbridge_mcp/mcp_server.py.
- Read-only bridge tools for Adobe, Blender, CAD/AutoCAD, ComfyUI, Jianying/CapCut.
- CAD/DXF plan tools:
  - autocad_dxf.status
  - autocad_dxf.validate_cad_plan
  - autocad_dxf.summarize_plan
- Public-safe CAD example plan: examples/cad_specs/connection_plate.plan.example.json.
- CAD plan CLI examples: examples/cad_bridge/validate_plan.py and examples/cad_bridge/summarize_plan.py.

## Safety boundary

The CAD/DXF plan tools are read-only. They report:

- writes_file: false
- starts_autocad: false
- reads_customer_drawing: false
- write_tools_enabled: false

Future write_dxf work must remain dry-run by default or require an explicit confirmation flag.

## Local validation results

Validated locally with the available Python runtime:

- python scripts/security_check.py: passed
- python scripts/starbridge_preflight.py --markdown: passed
- python -m unittest discover -s tests: 79 tests OK
- npm.cmd test: 79 tests OK
- python -m starbridge_mcp.server --json: safe_tool_count 12
- python -m starbridge_mcp.server tools --json --safe-only: passed
- python examples/bridge_status.py --json --redact-paths --soft-exit: completed with expected local software not configured / not running statuses

## Publish limitation

The current Codex checkout cannot use normal local git publishing yet:

- gh is not installed in the local shell.
- The checkout origin points to a local path, not a GitHub URL.
- git add fails because .git/index.lock cannot be created: Permission denied.

This closeout file was written through the GitHub connector on branch codex/photoshop-4up-hex-poster-experiment so the maintenance state is visible on GitHub while the local git permissions are repaired.
