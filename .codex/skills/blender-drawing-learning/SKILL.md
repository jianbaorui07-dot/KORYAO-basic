---
name: blender-drawing-learning
description: Use when learning from local Blender assets or turning Blender .blend files into structured drawing, modeling, material, lighting, camera, and render-study notes. Also use when the user wants to ingest Blender data, refine a Blender learning workflow, generate per-case experiment notes, or publish redacted Blender learning data to GitHub.
---

# Blender Drawing Learning

Use this skill to turn Blender asset folders into reusable learning knowledge without publishing raw assets.

## Safety Boundary

- Do not commit raw `.blend`, `.fbx`, `.obj`, `.gltf`, `.hdr`, `.exr`, texture images, archives, rendered derivatives, or local cache files unless the user explicitly asks and rights are clear.
- Commit redacted labels, counts, structure, learning notes, scripts, and public-safe CSV/JSON only.
- Do not write local absolute paths into public docs or generated data. Use environment variables such as `BLENDER_ASSET_ROOT` and `BLENDER_EXE`.
- When Blender opens files that contain embedded scripts, keep script execution disabled unless the user explicitly trusts the file.

## Workflow

1. Build a redacted inventory:

```powershell
python scripts\analyze_blender_learning_assets.py --root $env:BLENDER_ASSET_ROOT --out-dir docs\blender-drawing-learning\data
```

2. Profile `.blend` scenes with Blender:

```powershell
& $env:BLENDER_EXE --background --python scripts\blender_scene_profile.py -- --root $env:BLENDER_ASSET_ROOT --out docs\blender-drawing-learning\data\blend_scene_profiles_redacted.json
```

For one case:

```powershell
& $env:BLENDER_EXE --background --python scripts\blender_scene_profile.py -- --root $env:BLENDER_ASSET_ROOT --out docs\blender-drawing-learning\data\case_profile_redacted.json --match-label "<case label>"
```

3. Generate per-case notes:

```powershell
python scripts\generate_blender_case_notes.py --profiles docs\blender-drawing-learning\data\blend_scene_profiles_redacted.json --out-dir docs\blender-drawing-learning\experiments
```

4. Study each case in this order:

- Object structure: count mesh, curve, armature, empty, light, camera.
- Modeling method: inspect `MIRROR`, `SUBSURF`, `SOLIDIFY`, `BEVEL`, `ARMATURE`, `NODES`.
- Material method: inspect node materials, texture roles, roughness, normal, metallic, emission, alpha.
- Lighting method: classify key, fill, rim, world/HDR, color contrast, energy balance.
- Camera method: record focal length, perspective type, framing, and whether the scene was built for that camera.
- Experiment plan: rebuild a simplified version before copying details.

## Output Shape

Public learning output should usually include:

- `docs/blender-drawing-learning/README.md`
- `docs/blender-drawing-learning/LEARNING_NOTES.md`
- `docs/blender-drawing-learning/PRACTICE_ROADMAP.md`
- `docs/blender-drawing-learning/data/*_redacted.json`
- `docs/blender-drawing-learning/data/*_redacted.csv`
- `docs/blender-drawing-learning/experiments/all-blend-cases.md`
- `docs/blender-drawing-learning/experiments/cases/*.md`

## GitHub Publish

Before committing:

```powershell
rg -n "[A-Z]:\\\\" docs\blender-drawing-learning scripts\*.py .codex\skills\blender-drawing-learning
python -m py_compile scripts\analyze_blender_learning_assets.py scripts\blender_scene_profile.py scripts\generate_blender_case_notes.py
git status -sb
```

Then stage only the Blender learning files, commit, and push the branch.

## Reference Docs

- For exact input parameters and output schema, read `docs/blender-drawing-learning/PARAMETER_SCHEMA.md`.
- For Codex plugin or MCP tool design, read `docs/blender-drawing-learning/CODEX_BLENDER_PLUGIN_SPEC.md`.
- For user-facing learning interpretation, read `docs/blender-drawing-learning/LEARNING_NOTES.md`.

## Tool Parameter Summary

Core command parameters:

| Parameter | Required | Used by | Meaning |
| --- | --- | --- | --- |
| `BLENDER_EXE` | Yes | Blender profiling and rendering tools | Path to the local Blender executable. |
| `BLENDER_ASSET_ROOT` | Yes | Inventory and scene profiling tools | Local asset root; never write this path into public outputs. |
| `--root` | Yes | `analyze_blender_learning_assets.py`, `blender_scene_profile.py` | Local read root. |
| `--out-dir` | Yes | Inventory and case-note generation | Directory for generated redacted artifacts. |
| `--out` | Yes | Scene profiling | JSON profile output path. |
| `--match-label` | No | Scene profiling | Filter by redacted relative label for one-case experiments. |
| `--limit` | No | Scene profiling | Limit number of `.blend` files; `0` means no limit. |
| `--profiles` | Yes | Case-note generation | Input scene profile JSON. |

Key profile fields to inspect:

- `render_settings`: engine, resolution, frame range, samples, denoising, transparency.
- `objects_sample`: object transforms, mesh stats, material slots, modifiers.
- `modifiers`: subtype and parameters such as `levels`, `render_levels`, `width`, `segments`, `thickness`, `offset`.
- `materials_sample`: node use, node types, diffuse color, sampled node inputs.
- `lights`: type, energy, color, transform, size, shadow settings.
- `cameras`: lens, sensor width, transform, clipping, depth of field.
- `world`: world color or world node samples.
