## Summary

- TODO

## Scope Check

- [ ] This PR stays within the stated branch scope.
- [ ] No real assets, models, drafts, videos, tokens, or local paths are committed.
- [ ] CI does not require local commercial software.
- [ ] README changes are absent or intentionally small.

## Verification

- [ ] `python -m unittest discover -s tests`
- [ ] `python -m starbridge_mcp.server --json`
- [ ] `powershell -ExecutionPolicy Bypass -File scripts\check_forbidden_files.ps1`
- [ ] `powershell -ExecutionPolicy Bypass -File scripts\check_repository_safety.ps1`
- [ ] `powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1`

## Notes

Mention any expected local-only failures, such as strict mode returning nonzero when desktop software is not configured.
