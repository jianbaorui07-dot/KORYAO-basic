# Blender reference-verified reconstruction

This note collects the GitHub research and the StarBridge design direction for
turning a user-provided reference image into a Blender reconstruction workflow
that is checked against the original view before handoff.

The goal is not "image in, hallucinated 3D out." The goal is:

```text
reference image(s)
-> segmentation, edges, camera, depth, and scale constraints
-> semantic Blender scene graph
-> same-camera render
-> measured difference report
-> handoff only when visible-view metrics pass
```

## Non-hallucination contract

The pipeline must not present hidden geometry as fact. From a single image, the
following are unknown unless the user provides more views, measurements, or a
trusted CAD/product source:

- back side geometry;
- occluded interior structure;
- true material thickness;
- absolute dimensions without a known scale anchor;
- material construction that is not visible in the reference.

Generated completion can still be useful, but it must be labeled as an
assumption. For example, "back side completion is inferred by symmetry" is
acceptable; "this is the true back side" is not.

## Current StarBridge landing point

The repository now exposes a safe planning layer:

- MCP tool: `blender.reference_reconstruction_plan`
- CLI: `python examples/blender_bridge/reference_reconstruction_plan.py --json`
- npm shortcut: `npm.cmd run blender:reference:plan`
- implementation: `starbridge_mcp/bridges/blender_safe_scene.py`

This layer is intentionally dry-run only. It does not read image pixels, launch
Blender, open `.blend` files, execute arbitrary Python, download external
models, or write outputs. Its job is to define the gate that a future local
execution path must pass.

## Pipeline stages

| Stage | Purpose | Candidate projects |
| --- | --- | --- |
| Input gate | Accept only user-provided references, view count, licensing status, and optional scale anchors. | StarBridge `EvidenceManifest` |
| Visual decomposition | Extract object masks, part masks, material regions, edges, and dominant lines before modeling. | [SAM 2](https://github.com/facebookresearch/sam2), [GroundingDINO](https://github.com/IDEA-Research/GroundingDINO), [Grounded-Segment-Anything](https://github.com/IDEA-Research/Grounded-Segment-Anything), Photoshop masks |
| Edge and line evidence | Recover clean silhouettes, hard-surface edges, facade lines, and candidate vanishing directions. | [DeepLSD](https://github.com/cvg/DeepLSD), [DexiNed](https://github.com/xavysp/DexiNed), [XiaohuLuVPDetection](https://github.com/rayryeng/XiaohuLuVPDetection) |
| Camera and scale recovery | Match the camera to the reference image and recover metric scale where anchors exist. | [fSpy](https://github.com/stuffmatic/fSpy), [fSpy-Blender](https://github.com/stuffmatic/fSpy-Blender), [EyeLib](https://github.com/carlosbeltran/EyeLib), [Single-View-Metrology](https://github.com/bliuag/Single-View-Metrology) |
| Geometry initialization | Produce camera guesses, depth maps, point clouds, or coarse meshes before any artistic completion. | [VGGT](https://github.com/facebookresearch/vggt), [Depth Anything 3](https://github.com/ByteDance-Seed/depth-anything-3), [MapAnything](https://github.com/facebookresearch/map-anything), [DUSt3R](https://github.com/naver/dust3r), [MASt3R](https://github.com/naver/mast3r), [vggt-blender](https://github.com/xy-gao/vggt-blender), [DA3-blender](https://github.com/xy-gao/DA3-blender) |
| Multi-view baseline | Use traditional photogrammetry when the user provides enough views. | [COLMAP](https://github.com/colmap/colmap), [Meshroom](https://github.com/alicevision/meshroom), [OpenMVG](https://github.com/openMVG/openMVG), [OpenMVS](https://github.com/cdcseacave/openMVS) |
| Mesh and point processing | Clean point clouds, register geometry, reconstruct surfaces, and simplify meshes. | [Open3D](https://github.com/isl-org/Open3D), [PyMeshLab](https://github.com/cnr-isti-vclab/PyMeshLab), [trimesh](https://github.com/mikedh/trimesh) |
| Differentiable fitting | Optimize geometry/camera/material parameters against silhouette and edge losses. | [PyTorch3D](https://github.com/facebookresearch/pytorch3d), [nvdiffrast](https://github.com/NVlabs/nvdiffrast), [Kaolin](https://github.com/NVIDIAGameWorks/kaolin), [BlenderModelFitting](https://github.com/hansgaensbauer/BlenderModelFitting) |
| Blender evidence render | Render RGB, depth, masks, and segmentation from the recovered camera for review. | [BlenderProc](https://github.com/DLR-RM/BlenderProc), Blender Python, Blender MCP |
| Difference report | Compare the same-camera render against the reference before delivery. | OpenCV, [Kornia](https://github.com/kornia/kornia), [LPIPS](https://github.com/richzhang/PerceptualSimilarity) |

## Verification metrics

A local execution path should produce a report with at least these metrics:

| Metric | Why it matters | Suggested gate |
| --- | --- | --- |
| Silhouette IoU | Checks whether the model covers the same visible shape. | `>= 0.97` for hard-surface/product/facade tasks |
| Edge chamfer distance | Checks visible outline and line placement. | `<= 3-5 px`, depending on reference resolution |
| Camera reprojection error | Checks whether recovered camera and keypoints are aligned. | `<= 3-5 px` |
| Visible part coverage | Checks whether named parts were modeled instead of skipped. | `>= 0.95` for required parts |
| Material region IoU | Checks whether visible material/color regions land in the right areas. | `>= 0.90` |
| Declared unknown regions | Ensures invisible geometry is labeled, not invented. | Required for single-view jobs |

The final status should stay `needs_user` or `failed` when these metrics do not
pass. A model should only be called final when the same-camera evidence passes
and the unknown regions are explicitly declared.

## Recommended integration order

1. Keep the current `blender.reference_reconstruction_plan` as the public-safe
   planning entrypoint.
2. Add a local-only reference manifest format for user-provided images, view
   count, scale anchors, and allowed output directory.
3. Add mask/edge extraction adapters first: Photoshop masks, SAM2, GroundingDINO,
   DeepLSD, and DexiNed.
4. Add camera/depth initialization adapters: fSpy, VGGT, Depth Anything 3, or
   MapAnything. Prefer multi-view COLMAP/Meshroom when enough photos exist.
5. Add Blender same-camera render evidence: RGB, mask, depth, and segmentation.
6. Add metric comparison and evidence manifest output.
7. Only then add controlled Blender write/render execution, with explicit local
   confirmation and ignored output directories.

## What not to do

- Do not use Hunyuan3D, TripoSR, TRELLIS, or other image-to-3D generators as the
  sole truth source for visible geometry.
- Do not bypass the same-camera comparison report.
- Do not run arbitrary user Python in Blender.
- Do not download third-party models into the public repository.
- Do not commit `.blend`, textures, generated renders, private client images, or
  local model caches.

Generative image-to-3D tools can be a completion layer for invisible regions,
but the handoff must label those regions as inferred and keep the visible-view
metrics separate.
