# CreNexus v0.1.0-alpha.2 integrated preview release notes

## Summary

CreNexus v0.1.0-alpha.2 is the integrated Windows preview for the customer-facing Codex creative workflow. It retains local data compatibility with alpha.1 and adds a visible pixel-vector route, higher bounded SVG limits, in-app Codex conversation, and confirmed PSD/AI save-path delivery. It is still an unsigned internal preview package, not a signed public desktop release.

## Highlights

* Local MCP stdio server
* Visible Codex conversation workspace inside the desktop client
* Pixel Vector mode backed by the existing exact RGBA-to-SVG geometry engine and pixel-match verification
* 64/128/256 MB bounded SVG choices with a 256 MB hard safety cap
* Explicit save-path delivery to native Illustrator AI and layered Photoshop PSD, without overwriting source assets
* Safe migration of legacy `starbridge-desktop` Codex configuration with an automatic local backup
* Explicit first-install guidance to fully restart Codex before pairing a newly installed local MCP connector
* Direct replacement upgrade from the previous desktop build while preserving local data and other MCP entries
* Editorial StarBridge desktop interface with the existing projects, workflows, evidence, and creative software connections retained
* Safe bridge registry with BaseBridge for modularity (adapters/bridges)
* 5+ core Photoshop recipes: remove_background, enhance_portrait, frequency_separation, color_grade, prepare_for_web (with steps, safety, action_plan support)
* Action Plan mode: plan-then-execute with repair for fewer LLM roundtrips
* Photoshop: ps.get_preview (base64 for vision), ps.get_state (lightweight snapshot), enhanced previews
* ruff lint/format in CI and pre-commit for long-term quality
* Improved release process: .github/workflows/release.yml, updated install-and-publish.md, CHANGELOG
* Guarded outputs under examples/output, EvidenceManifests, redaction
* Git ignored generated assets
* CI with Windows + Ubuntu, security/preflight checks

## How to verify

```powershell
python -m unittest discover -s tests
python scripts/security_check.py
python scripts/starbridge_preflight.py --markdown
npm.cmd run starbridge:tools:safe
npm.cmd run photoshop:recipe:plan -- --recipe_id remove_background --action_plan
# Test new tools
# Use ps.get_preview and ps.get_state in your MCP client
```

## Not included

* No private PSD / AI files
* No generated binary demo assets
* No customer material
* Ordinary customer delivery never uses or falls back to Image Trace; a retained guarded experimental protocol exists only for explicit technical workflows
* The Windows internal preview remains unsigned and still requires a clean-machine install/uninstall pass before public distribution
