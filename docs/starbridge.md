# StarBridge Computer Use Architecture

StarBridge is a Codex automation bridge for Windows creative software. It combines Windows Computer Use for foreground GUI work, structured tools for deterministic outputs, and safety guards for local-first execution.

## Positioning

StarBridge lets Codex use scripts, APIs, CLI tools, COM, JSX, UXP, SVG, DXF, and workflow JSON where those channels are stable. It also prepares explicit Windows Computer Use plans for software tasks that need the real GUI, such as Photoshop layers, Illustrator export dialogs, Blender windows, AutoCAD views, or CapCut timelines.

The repository does not call a private OpenAI or Codex Computer Use API from Python. The real GUI executor is Codex itself. This repo provides plans, protocols, safety checks, instructions, logs, and evidence formats.

## Three Layers

1. Computer Use Execution Layer

Use this when the target app has no stable API or when the user explicitly asks Codex to operate the visible software UI. Plans can include launching apps, focusing windows, clicking menus, typing text, using shortcuts, checking panels, taking screenshots, and deciding the next step from screen state.

2. Structured Tools Layer

Use this first when a task can be completed deterministically through scripts or files. Examples include Photoshop JSX, Illustrator JSX or SVG, ComfyUI workflow validation, Blender Python generation, AutoCAD DXF generation, file existence checks, export validation, version probes, and logs.

3. Safety Guard Layer

All GUI and write-capable plans are guarded. Defaults are dry-run and no user file overwrite. Real writes require `--confirm-write`. GUI operation requires `--allow-computer-use`. Destructive operations require a separate human checkpoint. StarBridge never enters passwords, tokens, verification codes, payment data, or account credentials.

## Limits

Windows Computer Use usually controls the foreground input session. User supervision is required for sensitive steps. Popups, app versions, and license states can change execution. Password, authorization, payment, account, email, chat, and cloud-drive operations must be confirmed by the user. CI must never start real Photoshop, Illustrator, CapCut, or other desktop apps.

## Recommended Flow

1. `plan`: normalize an `ActionPlan`.
2. `safety-check`: inspect the `SafetyDecision`.
3. `run structured`: create deterministic files when possible.
4. `gui-instructions`: generate Codex-readable GUI steps.
5. `computer use`: Codex Windows operates the visible app.
6. `gui-record`: record result and evidence.
7. `verify output`: inspect exported files and logs.

## Commands

```powershell
python -m starbridge_mcp.server plan examples/plans/photoshop_poster_gui.json
python -m starbridge_mcp.server gui-instructions examples/plans/photoshop_poster_gui.json
python -m starbridge_mcp.server demo photoshop --mode gui
python -m starbridge_mcp.server demo photoshop --mode gui --allow-computer-use --confirm-write
python -m starbridge_mcp.server demo illustrator --mode gui
python -m starbridge_mcp.server demo capcut --mode gui
python -m starbridge_mcp.server gui-record --plan-id photoshop-demo --ok true --screenshot outputs/evidence/photoshop-demo.png
```

## Output Policy

Computer Use evidence, run logs, generated fallback assets, and demo outputs must stay under `outputs/`, `examples/`, or `tmp/`. Public repository examples should avoid private absolute paths, model names, customer assets, PSD/AI/DWG source files, draft files, tokens, cookies, and account data.

