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
- `Scenes`
- `UI`
- `../Python/worldforge`
- `../../Config/WorldForge`

Known important assets from the source run:

- `Maps/M_WorldForgeLab.umap`
- `Maps/M_WorldForgeBlockoutSandbox.umap`
- `Blueprints/BP_WorldForgeOfflineTaskRunner.uasset`
- `Blueprints/BP_WorldForgeCityMoodController.uasset`
- `Blueprints/BP_WorldForgeExplorerPawn.uasset`
- `EditorTools/EUW_WorldForgeControlDesk.uasset`
- `UI/WBP_WorldForgeStatus.uasset`
- `Scenes/WF0009_SnowTemple/Maps/L_WF0009_SnowTemple_Micro_R1.umap`
- `Scenes/WF0009_SnowTemple/Blueprints/BP_WF0009_RobotScout.uasset`
- `Scenes/WF0010_DNABonsaiWorkshop/Maps/L_WF0010_DNABonsaiWorkshop_R1.umap`
- `Scenes/WF0010_DNABonsaiWorkshop/Materials/M_WF0010_*.uasset`
- `Content/Python/worldforge/Core/camera_preview.py`
- `Content/Python/worldforge/Launchers/WF_RunRecipe.ps1`
- `Config/WorldForge/Recipes/WF0010_DNABonsaiWorkshop_R1.json`

## Evidence

Evidence is intentionally text-first and sanitized:

- `evidence/audit_baseline`
- `evidence/audit_logs`
- `evidence/handoff_docs`
- `evidence/legacy_summary`
- `evidence/performance`
- `evidence/receipts`
- `evidence/state`
- `evidence/universe_registry`
- `evidence/framework_baselines`
- `evidence/checkpoints`
- `evidence/command_center`
- `evidence/screenshots`

Important later-run evidence:

- WF0009 R1 receipts record a generated SnowTemple micro-scene plus a preview defect where the captured PNG is valid but visually black.
- WF0010 R1 receipts record a DNA bonsai workshop scene with 25 generated actors and preview metrics that passed non-black visual checks.
- WF0011 records are planning/universe-registry artifacts for a low-rise future-tech city. They do not claim that a finished UE map was generated.

## Exclusion Policy

The package excludes full UE runtime folders, raw editor logs, crash dumps, private `Saved/Config` state, caches, and the original project backup. This keeps the GitHub repository focused on the WorldForge agent framework evidence rather than private machine state.
