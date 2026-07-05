# Asset Manifest

The WorldForge package includes a compact UE content subset and the evidence needed to understand how it was produced.

## UE Content

The UE assets live in `ue_project/Content/WorldForge/`.

Top-level content groups:

- `Blueprints`
- `EditorTools`
- `Maps`
- `Materials`
- `RemoteControl`
- `UI`

Known important assets from the source run:

- `Maps/M_WorldForgeLab.umap`
- `Maps/M_WorldForgeBlockoutSandbox.umap`
- `Blueprints/BP_WorldForgeOfflineTaskRunner.uasset`
- `Blueprints/BP_WorldForgeCityMoodController.uasset`
- `Blueprints/BP_WorldForgeExplorerPawn.uasset`
- `EditorTools/EUW_WorldForgeControlDesk.uasset`
- `UI/WBP_WorldForgeStatus.uasset`

## Evidence

Evidence is intentionally text-first and sanitized:

- `evidence/audit_baseline`
- `evidence/audit_logs`
- `evidence/handoff_docs`
- `evidence/legacy_summary`
- `evidence/performance`
- `evidence/screenshots`

## Exclusion Policy

The package excludes full UE runtime folders and the original project backup. This keeps the GitHub repository focused on the WorldForge agent framework evidence rather than private machine state.
