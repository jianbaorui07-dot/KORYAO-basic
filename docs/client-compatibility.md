# Client Compatibility

This page records the current MCP client compatibility status for StarBridge v0.1.0-alpha. It is intentionally conservative: passing mock stdio tests proves protocol shape, not real desktop software automation.

| Client | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Mock stdio | Tested | `python -m unittest discover -s tests` covers `initialize`, `tools/list`, and `tools/call` through `starbridge_mcp.mcp_server`. | CI safe; no local creative software required. |
| Codex | Configuration documented | `.codex/config.example.toml` uses Codex `[mcp_servers.starbridge]` stdio configuration. `python -m starbridge_mcp.mcp_server` exposes stdio tools and `python -m starbridge_mcp.server tools --json --safe-only` lists safe capabilities. | The real `.codex/config.toml` stays local and ignored because it may contain workstation paths. |
| Claude Code | Project configuration documented | `.mcp.json` provides a project-scoped stdio MCP server configuration for `python -m starbridge_mcp.mcp_server`. | First use requires user approval in Claude Code because project-scoped MCP servers are shared through version control. |
| Claude Desktop | Not yet manually verified | Server is stdio-compatible by protocol shape. | Planned manual test: add the local command to Claude Desktop MCP settings and confirm `tools/list`. |
| Cursor | Not yet manually verified | Server is stdio-compatible by protocol shape. | Planned manual test: add the local command to Cursor MCP settings and confirm safe tool discovery. |

## Current stdio command

```powershell
python -m starbridge_mcp.mcp_server
```

## Safe discovery command

```powershell
python -m starbridge_mcp.server tools --json --safe-only
```

## Compatibility boundaries

- Client discovery does not prove Photoshop, Illustrator, AutoCAD, Blender, ComfyUI, or CapCut are installed.
- Real desktop probes must return structured JSON warnings when local software is unavailable.
- Write tools must keep `dry_run=true` by default.
- Real writes require explicit `confirm_write=true` or `confirm_export=true` and sandbox output paths.
- ChatGPT Apps / Connectors require a remote HTTPS MCP server; this repository currently exposes a local stdio server for local developer clients such as Codex and Claude Code.
