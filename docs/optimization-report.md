# StarBridge 优化报告

时间：2026-05-24

## 本轮完成内容

- 完整审计了 README、AGENTS、`package.json`、`docs/`、`examples/`、`scripts/`、`cad-mcp-autocad/` 和现有 tests。
- 新增 `third_party_research/` 作为本机-only 第三方研究目录，并加入 `.gitignore`。
- 浅克隆并只读研究 Photoshop、Illustrator、Blender、AutoCAD/CAD、ComfyUI、剪映/CapCut 相关项目。
- 新增 [docs/advanced-project-comparison.md](advanced-project-comparison.md)，按 P0/P1/P2/P3 记录可借鉴点、风险和许可证情况。
- 新增 `starbridge_mcp/` 最小框架：
  - `core/config.py`
  - `core/security.py`
  - `core/result_schema.py`
  - `server.py`
- 新增统一状态入口：

```powershell
python -m starbridge_mcp.server --json
```

- 新增 `.env.example`、`scripts/setup_starbridge.ps1`、[docs/local-mcp-setup.md](local-mcp-setup.md)。
- 新增 `tests/test_starbridge_schema.py` 和 `tests/test_security_boundaries.py`。
- 补强 `.gitignore`，覆盖 `research_repos/`、`third_party_research/`、模型、PSD、AI、DWG、DXF、视频、剪映草稿和临时输出。
- 更新 README，把项目定位为 “StarBridge：Codex 本地创意软件 MCP 桥接框架”。
- 补强旧 `examples/bridge_status.py` 的输出脱敏，避免 JSON 状态里出现真实用户目录。

## 当前能力矩阵

| 方向 | 已具备 | 缺口 |
| --- | --- | --- |
| ComfyUI | API 探针、基础节点检查、txt2img workflow 示例、参数化文生图脚本 | img2img/inpaint/upscale、资产索引、MCP tool registry |
| Blender | manifest、环境探针、总状态检查 | 场景生成、渲染验证、Blender addon/MCP 接入 |
| AutoCAD/CAD | `cad-mcp-autocad/` MCP 子项目、CAD JSON -> DXF MVP、AutoCAD COM 测试脚本 | 统一 adapter、离线 DXF 与真实 COM 控制分层、安全确认流程 |
| Photoshop | PowerShell 诊断、COM 探针、当前文档信息、主体抠图实验 | 稳定工具接口、动作权限、安全输出目录策略 |
| Illustrator | manifest、COM 探针、总状态检查 | 当前文档只读信息、测试画板、Image Trace、SVG/PDF/PNG 导出 |
| 剪映/CapCut | manifest、可执行文件/草稿目录探针、草稿桥路线文档 | 草稿结构只读摘要、安全测试草稿、是否采用 MCP 或 CLI 包装 |

## 验证结果

### `python -m unittest discover -s tests`

结果：通过。

摘要：

```text
Ran 41 tests
OK
```

### `python examples\bridge_status.py --json`

结果：通过，退出码 `0`。本机运行状态/环境变量未满足时，脚本仍输出 JSON，并通过 bridge status 表达未就绪。

摘要：

```text
ComfyUI: missing，127.0.0.1:8188 拒绝连接，需要先启动 ComfyUI。
Blender: missing，未找到 Blender 可执行文件，需要配置 BLENDER_EXE。
CAD: warn，MCP 子项目存在，但未找到 AutoCAD，可配置 AUTOCAD_EXE。
Photoshop: ok，pywin32 可用；本次未加 --probe-executables，所以跳过 COM 实连。
Illustrator: warn，pywin32 可用，但未配置 ILLUSTRATOR_EXE，也未实连 COM。
JianyingCapCut: warn，未配置 JIANYING_EXE/CAPCUT_EXE/草稿目录。
```

下一步需要用户提供或手动完成：

- 启动本机 ComfyUI，或设置 `STARBRIDGE_COMFYUI_URL`。
- 设置 `BLENDER_EXE`、`AUTOCAD_EXE`、`ILLUSTRATOR_EXE` 等本机路径。
- 手动确认 Adobe、AutoCAD、Blender、剪映/CapCut 已安装并授权。
- 需要真实 COM 探测时再运行 `python examples\bridge_status.py --probe-executables --json`。

### `npm.cmd test`

结果：通过。

摘要：

```text
Ran 41 tests
OK
```

### 额外安全验证

命令：

```powershell
python scripts\security_check.py
```

结果：

```text
security check passed
```

### StarBridge 统一入口验证

命令：

```powershell
python -m starbridge_mcp.server --json
```

结果：通过，退出码 `0`。部分本机软件未启动或未配置时，统一入口仍输出 JSON；只有显式加 `--strict` 时才返回失败退出码。所有 bridge result 均包含：

```text
ok, bridge, action, message, details, warnings, next_steps
```

## 第二轮状态探针优化

时间：2026-05-24

本轮只基于已提交的 StarBridge MVP 做增量增强，没有修改未跟踪的 CAD MVP 根目录文件。

完成内容：

- `starbridge_mcp.server` 为六个 bridge 增加更清楚的状态元信息：
  - `comfyui`
  - `photoshop`
  - `illustrator`
  - `blender`
  - `autocad`
  - `jianying_capcut`
- 每个 bridge 的 `details` 增加：
  - `display_name`
  - `software`
  - `probe_type`
  - `required_env`
  - `ready_when`
  - `safety_boundary`
  - `current_actions`
- 保留旧 CLI alias：
  - `cad_autocad` -> `autocad`
  - `capcut_jianying` -> `jianying_capcut`
- 新增 [docs/starbridge-tool-roadmap.md](starbridge-tool-roadmap.md)，规划 `status`、`probe`、`open_file`、`read_document_info`、`export_result`、`run_script`。
- 新增 [docs/codex-usage-prompts.md](codex-usage-prompts.md)，整理未来 Codex 调用 StarBridge 的标准提示词。
- 增加 schema 测试，覆盖所有 bridge profile 的统一返回字段。

第二轮验证结果：

```text
python -m unittest discover -s tests
Ran 42 tests
OK

python -m starbridge_mcp.server --json
exit code 0

python examples\bridge_status.py --json
exit code 0

npm.cmd test
Ran 42 tests
OK
```

## 风险和下一步

- 当前 `starbridge_mcp.server` 是 CLI-style JSON 入口，还不是完整 MCP stdio server。下一轮应接入 `mcp` SDK，注册 `starbridge.status` 和 `starbridge.probe`。
- `examples/bridge_status.py` 仍是实际探测逻辑中心，后续应逐步迁移到 `starbridge_mcp.core`，避免双入口长期分叉。
- Photoshop、Illustrator、AutoCAD 的写入动作必须先加输入/输出路径审计和用户确认策略。
- 剪映/CapCut 不建议先做桌面自动点击，优先研究草稿桥和 CLI 方式。
