# WorldForge Architecture v1.1

## Purpose

WorldForge v1.1 separates scene evidence, recipe data, quality policy, and future Command Center contracts. The current goal is not to rebuild scenes, but to make WF0009 and WF0010 resumable, auditable, and safe for WF0010 LookDev.

## State Model

- `Saved/WorldForge/ProjectState.json` is project-level only.
- `Saved/WorldForge/Jobs/<job_id>.json` stores scene/job-specific evidence.
- `Saved/WorldForge/LatestJob.json` points to the latest job.
- `Saved/WorldForge/Checkpoints/WF_v1_1_phase_<n>.json` records resumable phase completion.
- `Saved/WorldForge/run_state.json` remains compatibility state for existing tools, but v1.1 readers should prefer ProjectState plus JobState.

## Recipe Model

- Authoritative recipes live under `Config/WorldForge/Recipes`.
- JSON recipes must not live under `Content/Python/worldforge/Recipes`, because UE can treat them as importable DataTable source files.
- `recipe_path_resolver.py` maps legacy Content recipe paths to the Config recipe directory.

## Spec Classes

- `SceneRecipe`: scene structure, required elements, actor budget, map path.
- `LookRecipe`: colors, materials, lighting, exposure, fog, background, forbidden visual motifs.
- `ShotRecipe`: camera position intent, target point, FOV, composition, depth-of-field guidance.
- `RenderProfile`: preview and still-output profiles such as `preview_quick`, `preview_standard`, and `render_final_still`.

## Front Contract

Front is the future Command Center user surface. It owns:

- user creative intent;
- recipe selection;
- state display;
- preview display;
- open-map actions.

Front must read `Saved/WorldForge/CommandCenter/dashboard_state.json` and should not inspect UE logs directly.

## Middle Contract

Middle coordinates execution and policy:

- `SceneCompiler`: turns SceneRecipe plus LookRecipe plus ShotRecipe into UE build/update plans.
- `JobOrchestrator`: owns job phases, checkpoints, resume, and latest-job pointers.
- `ResourcePolicy`: enforces P1/P2/P3 gates before launch.
- `QualityGate`: separates file validity, automatic visual metrics, and human review.
- `RecoveryManager`: handles stuck automation and crash evidence without force-killing unrelated processes.

## Back Contract

Back is UE-facing implementation:

- UE Python Core;
- ActorFactory;
- Material/Look Adapter;
- CameraPreview;
- SceneValidator.

Back must never mark a screenshot visually passed when only file validity is proven.

## Terminal Contract

Terminal is the local execution layer:

- PowerShell launchers;
- `UnrealEditor-Cmd.exe`;
- normal visible `UnrealEditor.exe`;
- `<WORLDFORGE_RUNTIME>/DDC`;
- `<WORLDFORGE_RUNTIME>/Logs`;
- `<WORLDFORGE_RUNTIME>/Receipts`;
- `<WORLDFORGE_RUNTIME>/Previews`.

Terminal must avoid `taskkill`, `Stop-Process -Force`, broad cleanup, and duplicate UE launch when a UE process is already active.

## Current Scene Status

- WF0009 SnowTemple R1: `DONE_WITH_PREVIEW_DEFECT`.
- WF0010 DNABonsaiWorkshop R1: `DONE_WITH_VISUAL_PASS`.

## LookDev Gate

WF0010 LookA may start only under `P2_LOOKDEV`:

- source job is `DONE_WITH_VISUAL_PASS`;
- available memory is at least 8 GB;
- C drive free space is at least 100 GB;
- only one UE process may be active;
- work occurs on a copied LookA branch map, not the WF0010 R1 structure baseline;
- output is a 1920x1080 standard preview;
- MRQ, Path Tracer, animation, and plugin activation are disabled.
