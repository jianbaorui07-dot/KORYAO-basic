# 造境WorldForge：虚幻引擎 3D 世界开发 Agent Example

This folder packages the local `codex接入UE` work as a repository-safe Unreal Engine evidence bundle.

The project theme is: Unreal Engine is entering its Codex moment. Instead of a small parameter-tuning plugin, the goal is a 3D-aware agent that can take a creative description such as "build a technology city" and produce an editable world: terrain, buildings, interiors, interactive objects, physics, gameplay rules, dynamic environments, and eventually characters, NPC logic, quests, and weather.

The current checked-in bundle is the honest first stage of that direction. It preserves what was actually run and reviewed locally, while keeping unsafe/private runtime state out of Git.

## Folder Map

| Path | Purpose |
| --- | --- |
| `ue_project/Content/WorldForge/` | UE maps, blueprints, materials, UI, and editor utility assets created for the WorldForge sandbox. |
| `ue_project/Project8_WorldForge.uproject` | Minimal sanitized project descriptor copied from the enhanced UE project. |
| `control_layer/` | Offline control scripts, task schemas, task JSON, and sanitized execution evidence. |
| `tasks_and_checkpoints/` | Plans and checkpoint JSON used by the WorldForge offline workflow. |
| `evidence/` | Sanitized reports, performance baselines, stop reports, screenshots, and handoff docs. |
| `legacy_pre_audit/` | Earlier UE/Codex pre-audit scripts and evidence from the same local project line. |
| `manifest.json` | Generated package inventory and exclusion policy. |

## What Is Included

- WorldForge UE assets under `Content/WorldForge`.
- Offline Agent Bridge scripts and task files.
- Checkpoint JSON evidence.
- v0.1, v0.2, and v0.3 handoff reports.
- Performance and safety reports.
- Screenshots from the early UE audit.

## What Is Excluded

- The private original UE project backup.
- Full enhanced project `Saved/` and `Intermediate/` folders.
- Raw UE logs with full telemetry URLs.
- pycache files.
- Global Codex config.
- Any software installer or downloaded external asset.

## Current Status

This package is an evidence bundle and prototype seed, not a finished Unreal plugin.

Verified or documented from the source run:

- UE 5.2.1 local project copy.
- `M_WorldForgeLab` and `M_WorldForgeBlockoutSandbox`.
- roughly 42 WorldForge-managed actors after the city upgrade task.
- offline task runner, city mood controller, explorer pawn, control desk, materials, and checkpoint evidence.
- no Remote Control or MCP enablement in the uploaded package.

Still gated:

- UE GUI patch for the `ToggleCityMood` keyboard/UI path.
- Remote Control loopback-only command gate.
- stdio MCP bridge.
- large-scale dynamic generation, NPCs, skeletal characters, and full playable game logic.
