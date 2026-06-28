# Forward Vector Line-Rebuild — Training Data

This folder holds **synthetic training data** for the *forward* direction of the
Illustrator vector pipeline: given a reference line drawing, **reconstruct it as
editable vector strokes by computing the geometry and drawing it one path at a
time** — never by image trace / auto-vectorization.

It complements [`docs/illustrator-vector-line-rebuild-pipeline.md`](../../../../docs/illustrator-vector-line-rebuild-pipeline.md),
which covers the *reverse* direction (existing `.ai`/PDF/SVG → extracted lines →
reduced contours).

```text
reference image (line art)
  -> describe geometry parametrically (projection, profile curves, lattice)
  -> emit ExtendScript (JSX) that draws every line via pathItems.setEntirePath
  -> inject into a running Illustrator over COM (app.DoJavaScript)
  -> export a PNG preview, compare to the reference, refine parameters
  -> repeat until the silhouette and key construction lines match
```

## Why this is "no image trace"

Every stroke is produced from numbers the agent computed, not from pixels:

- `pathItems.add()` + `setEntirePath([[x, y], ...])` for each polyline.
- `filled = false; stroked = true` — real editable strokes.
- No `ImageTrace`, no `Live Trace`, no raster placement.

This keeps the output fully editable and deterministic, which is the same
principle as the reverse pipeline's "geometry engine, not pixels" boundary.

## Files

| File | What it is |
| --- | --- |
| `forward_line_reconstruction.jsonl` | The dataset. One JSON record per line: instruction, constraints, method, key parameters, verification, and the lesson learned (including failure→fix records). |
| `jsx/eiffel_tower_lines.jsx` | Reference artifact: parametric Eiffel Tower as ~170 stroked lines (silhouette + iron lattice + platforms + antenna). |
| `jsx/staircase_oblique.jsx` | Reference artifact: a perspective staircase rebuilt with an **oblique projection** (horizontal treads, vertical risers, depth receding up-right). |

## Record schema (`*.jsonl`)

```json
{
  "id": "string, stable identifier",
  "skill": "illustrator-forward-vector-line-rebuild",
  "instruction": "user-style request",
  "constraints": ["no image trace", "line-by-line stroked paths"],
  "approach": "short reasoning summary",
  "method": { "transport": "...", "draw_api": "...", "key_parameters": { } },
  "code_ref": "jsx/<file>.jsx or an inline snippet",
  "verification": "how the result was checked",
  "lesson": "the transferable takeaway"
}
```

## Reproducing locally (COM transport, Windows)

The transport is the StarBridge Illustrator pattern: attach to the **already
running** Illustrator and inject a JSX string prefixed with a config block.
Paths below are placeholders — never commit machine-specific paths.

```powershell
$jsx = Get-Content "<path>\jsx\staircase_oblique.jsx" -Raw -Encoding UTF8
$cfg = "var STARBRIDGE_CONFIG = { strokeWidth:2.0, lineColor:[15,15,18] };`r`n"
$ai  = [Runtime.InteropServices.Marshal]::GetActiveObject("Illustrator.Application")
$ai.DoJavaScript($cfg + $jsx)
# then export a PNG preview and compare to the reference, refine, repeat
```

## Safety rules (inherited from the pipeline doc)

- Synthetic examples only — no private/client artwork.
- No machine-specific paths, account metadata, or source files committed.
- Destructive steps write new files; never overwrite the source.
