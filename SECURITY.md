# Security Policy

StarBridge is designed as a local-first bridge between AI coding agents and desktop creative software. The public repository must not contain private assets, credentials, installation paths, customer files, or generated production output.

## Reporting a Security Issue

If you find a leak risk, unsafe write path, credential pattern, or MCP tool behavior that could expose private files, please open a GitHub issue with:

- the affected file or MCP tool name;
- the unsafe behavior;
- a minimal reproduction that does not include private data;
- the expected safer behavior.

Do not paste tokens, cookies, OAuth cache, license files, personal paths, client files, PSD/AI/DWG assets, model files, generated images, or exported videos into an issue.

## Project Safety Rules

- Public examples must use placeholder paths such as `<source-image>` and `$env:TEMP`.
- Local paths, usernames, install locations, and output folders should be passed through environment variables.
- Read-only probes should return redacted status summaries.
- File-writing tools should default to dry-run or require an explicit confirmation flag.
- Output reports and manifests must pass the shared sanitizer/redactor before being printed or written.
- Paths, HOME, USERPROFILE, usernames, tokens, API keys, cookies, passwords, OAuth values, and secrets must be redacted.
- GUI / Adobe / CapCut / Blender write actions are experimental unless a real reviewed E2E run proves otherwise; by default they must stay inside demo or sandbox output directories.
- AutoCAD/DXF headless writes are only allowed under `examples/cad/output` and require explicit `confirm_write=true`; missing optional DXF dependencies must return structured unavailable rather than crashing.
- Security checks should fail before private assets or obvious credentials are committed.

## Local Validation

Run these before publishing changes:

```powershell
python scripts\security_check.py
python scripts\starbridge_preflight.py --markdown
python -m unittest discover -s tests
```
