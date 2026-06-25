# GitHub Comparison Notes

This note tracks ideas from comparable public creative-software MCP projects that can be adopted into StarBridge without copying implementation code.

## Compared Projects

| Project | Area | Useful Pattern |
| --- | --- | --- |
| [artokun/comfyui-mcp](https://github.com/artokun/comfyui-mcp) | ComfyUI MCP | Asset IDs, job status, workflow visualization, workflow diff, generation metadata, VRAM checks, progress monitor. |
| [IO-AtelierTech/comfyui-mcp](https://github.com/IO-AtelierTech/comfyui-mcp) | ComfyUI MCP | Explicit API vs UI workflow format separation, schema validation, node discovery, queue/history tools, compatibility notes. |
| [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) | Blender MCP | Blender addon + MCP server split, viewport screenshot, scene inspection. |
| [djeada/blender-mcp-server](https://github.com/djeada/blender-mcp-server) | Blender MCP | Namespace grouping, scripts/demos/tests/docs structure, mocked Blender tests. |
| [ie3jp/illustrator-mcp-server](https://github.com/ie3jp/illustrator-mcp-server) | Illustrator MCP | Read/manipulate/export/preflight grouping and multilingual docs. |
| [krVatsal/illustrator-mcp](https://github.com/krVatsal/illustrator-mcp) | Illustrator MCP | Windows COM and macOS AppleScript wrapper split plus screenshot feedback. |
| [loonghao/photoshop-python-api-mcp-server](https://github.com/loonghao/photoshop-python-api-mcp-server) | Photoshop MCP | Photoshop COM session/document/layer read-only boundary and controlled operations. |
| [00bx/00bx-photoshop-mcp](https://github.com/00bx/00bx-photoshop-mcp) | Photoshop MCP | MCP tools plus skills knowledge-loading pattern and tool categorization. |
| [adobe/generator-app-remote-mcp-server-generic](https://github.com/adobe/generator-app-remote-mcp-server-generic) | Adobe MCP template | Official Adobe App Builder + MCP server template; useful for remote MCP packaging, not local desktop control. |
| [stewberticus/adobe-mcp](https://github.com/stewberticus/adobe-mcp) | Adobe suite MCP | Unified bridge registry across Photoshop, Premiere Pro, Illustrator, and InDesign. |
| [dcc-mcp/dcc-mcp-photoshop](https://github.com/dcc-mcp/dcc-mcp-photoshop) | Photoshop UXP MCP | UXP WebSocket adapter pattern for separating Photoshop plugin code from MCP tool calls. |
| [Dakkshin/after-effects-mcp](https://github.com/Dakkshin/after-effects-mcp) | After Effects MCP | ExtendScript-based composition/layer/property tool grouping for a future AE bridge. |
| [leancoderkavy/premiere-pro-mcp](https://github.com/leancoderkavy/premiere-pro-mcp) | Premiere Pro MCP | CEP/ExtendScript bridge and timeline-oriented tool vocabulary. |
| [zachshallbetter/indesign-mcp-server](https://github.com/zachshallbetter/indesign-mcp-server) | InDesign MCP | Document/page/text/style tool grouping for future layout preflight. |
| [Automaat/lightroom-mcp](https://github.com/Automaat/lightroom-mcp) | Lightroom MCP | Lightroom Classic metadata and catalog bridge direction; useful only after strict photo-library boundaries are defined. |

## Directly Pullable Ideas

1. Add a richer `ExecutionResult` and `EvidenceManifest` layer for generated assets:
   - stable asset IDs
   - source plan ID
   - originating workflow or GUI step IDs
   - output file list
   - screenshots
   - validation status

2. Split ComfyUI plan handling into explicit workflow formats:
   - `api_workflow` for execution and validation
   - `ui_workflow` for editor-only review
   - reject ambiguous workflow plans before execution

3. Add job lifecycle vocabulary across all bridges:
   - `queued`
   - `running`
   - `completed`
   - `failed`
   - `cancelled`
   - `needs_user`

4. Add optional progress/evidence monitoring:
   - structured tools can report job status
   - Computer Use plans can report current GUI step and screenshot evidence
   - no CI path should launch real desktop software

5. Expand bridge capability descriptions by category:
   - discovery
   - planning
   - execution
   - validation
   - evidence
   - cleanup

6. Keep Adobe expansion staged:
   - Photoshop and Illustrator stay as the current implementation focus.
   - Premiere Pro, After Effects, InDesign, and Lightroom remain research-only until read-only schemas and privacy boundaries are documented.
   - UXP, CEP, Generator API, and cloud Adobe APIs require separate approval because they can write user directories, require account state, or depend on desktop plugins.

## Not Directly Pulled Yet

- External source code was not copied.
- StarBridge只学习公开架构模式、schema 设计、tool grouping 和安全边界，不复制第三方实现代码、桌面脚本或私有素材假设。
- Node.js/TypeScript tool implementations were not ported into the Python StarBridge server.
- Blender addon server patterns were not added because this repository keeps real desktop automation behind probes, sandbox plans, and explicit user approval.
- Model download, registry search, and custom node installation were not added because they need stricter token, license, cache, and path policies first.
- Adobe third-party plugin code, arbitrary JSX/ExtendScript executors, cloud API calls, and generated project files were not copied or enabled.

## Recommended Next PR

Implement `EvidenceManifest` and `JobStatus` dataclasses, then expose:

- `starbridge evidence init`
- `starbridge evidence add-screenshot`
- `starbridge evidence validate`
- `starbridge job-status`

Those additions would reuse the Computer Use planning layer added in PR #6 while preserving StarBridge's local-first safety boundary.

