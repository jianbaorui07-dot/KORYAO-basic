# StarBridge 项目结构

StarBridge 是 Codex 接入本地创意软件的公开协作仓库。公开内容以状态检查、只读探针、示例和中文文档为主。

## 主要目录

| 路径 | 用途 |
| --- | --- |
| `starbridge_mcp/` | StarBridge CLI-style 状态入口、统一结果 schema、脱敏逻辑和 bridge 模块。 |
| `examples/` | 公开安全的 bridge manifest、只读探针和最小示例。 |
| `docs/` | 中文说明、安全边界、路线图和发布清单。 |
| `tests/` | 单元测试和安全边界测试。 |
| `scripts/` | 仓库检查脚本、状态汇总脚本和既有本地辅助脚本。 |
| `.github/` | CI、PR 模板和 issue 模板。 |
| `cad-mcp-autocad/` | 既有 AutoCAD MCP 子项目。发布审计任务不在这里开发 CAD/DXF。 |

## 发布范围

本轮发布审计只覆盖 CI、文档、安全脚本和公开安全检查。ComfyUI/Jianying bridge 已在 integration 分支完成最小注册；CAD/DXF 分支仍留到后续单独处理。
