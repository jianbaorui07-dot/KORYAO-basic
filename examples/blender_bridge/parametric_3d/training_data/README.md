# Parametric 3D Rebuild — Training Data (Blender)

This folder holds **synthetic training data** for the *forward* direction of the
Blender bridge: given a reference **2D drawing** (an elevation / line art), **rebuild
it as an editable parametric 3D scene by computing the geometry and emitting `bpy`
code** — never by sculpting by hand or importing a pre-made mesh.

It is the 3D sibling of
[`examples/illustrator_bridge/vector_rebuild/training_data`](../../../illustrator_bridge/vector_rebuild/training_data/README.md):
same principle — *the agent is the geometry engine, the DCC app is the renderer* —
applied to Blender instead of Illustrator.

```text
reference drawing (e.g. an elevation: key elevations, base width, profile)
  -> describe geometry parametrically (profile curves, lattice rules, section sizes)
  -> emit bpy that builds every member (curve + bevel = tubes, bmesh slabs, etc.)
  -> run it: live over the BlenderMCP socket, or headless via `blender --background`
  -> render a preview, compare to the reference, refine the parameters
  -> repeat until silhouette + key construction lines match
```

## Why "no sculpting, no asset import"

Every vertex comes from numbers the agent computed, not from a kit-bashed asset:

- Lattice ironwork = a `CURVE` datablock, one `POLY` spline per structural member,
  with `bevel_depth` giving each edge a real tube cross-section.
- Platforms = `bmesh` boxes at the documented elevations.
- Arches = swept `CURVE` profiles.
- No Sketchfab / Poly Haven / Hyper3D / generated-mesh import; no manual sculpt.

The output stays fully editable and deterministic — re-running the script reproduces
the model exactly, and a single parameter (`bevel_depth`, subdivision count) restyles
the whole structure.

## Worked example: the Eiffel Tower

Rebuilt from a real **South Elevation** drawing (sheet `SB-AI-001`) using the documented
elevations: `0 / +57.63 / +115.73 / +276.13 / +300.65 / +330 m`, 125 m square base.
Objects: `EiffelLattice` (dense lattice, ~2340 members), `EiffelPlatforms`, `EiffelArches`,
plus ground / sun / camera.

## Files

| File | What it is |
| --- | --- |
| `parametric_lattice_3d.jsonl` | The dataset. One JSON record per line: instruction, constraints, method, key parameters, verification, and the lesson learned (including failure→fix records). |
| `scripts/build_eiffel_tower.py` | Reference artifact: the full parametric build, runnable headless. Writes `.blend` + `.glb` and a render preview to an output dir you pass in. No machine-specific paths. |

## Record schema (`*.jsonl`)

```json
{
  "id": "string, stable identifier",
  "skill": "blender-parametric-3d-rebuild",
  "instruction": "user-style request",
  "constraints": ["no sculpting", "no asset import", "editable parametric output"],
  "approach": "short reasoning summary",
  "method": { "transport": "...", "draw_api": "...", "key_parameters": { } },
  "code_ref": "scripts/<file>.py or an inline snippet",
  "verification": "how the result was checked",
  "lesson": "the transferable takeaway"
}
```

## Reproducing locally

Two transports, same script body.

**A. Headless (reliable, for final artifacts)** — a separate process; never touches a
Blender window you have open:

```powershell
# BLENDER_EXE points at your Blender 4.x/5.x executable
& $env:BLENDER_EXE --background --factory-startup `
    --python examples\blender_bridge\parametric_3d\training_data\scripts\build_eiffel_tower.py `
    -- --out .\out
# -> .\out\EiffelTower.blend, .\out\EiffelTower.glb, .\out\preview.png
```

**B. Live (for iterating / previewing)** — paste the body of the script (minus the
export tail) through the BlenderMCP socket (`execute_blender_code`) into a running
Blender, then `get_viewport_screenshot` to inspect.

## Safety rules (inherited from the bridge)

- Synthetic / public-reference examples only — no private or client assets.
- No machine-specific paths, account metadata, or source binaries committed.
  Output paths are passed at run time and default to a relative `./out`.
- Destructive steps write **new** files into the output dir; never overwrite a source.
