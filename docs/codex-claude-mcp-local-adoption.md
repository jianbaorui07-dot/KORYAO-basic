# Codex / Claude 接入 StarBridge MCP 本机落地

这份记录用于把 StarBridge 接到本机 AI 客户端，重点是 Codex 和 Claude Code。结论按“需要做什么”和“不需要做什么”区分，避免把 ChatGPT 远程 MCP、桌面软件授权、真实素材路径混进公开仓库。

## 搜集到的资料

| 来源 | 对 StarBridge 的意义 |
| --- | --- |
| OpenAI Codex MCP 文档：<https://developers.openai.com/codex/mcp> | Codex 支持本地 stdio MCP 和 streamable HTTP MCP；配置放在 `~/.codex/config.toml` 或受信任项目的 `.codex/config.toml`；可用 `codex mcp add` 管理。 |
| OpenAI Codex 配置说明：<https://developers.openai.com/codex/config-reference> | Codex 的 MCP server 配置使用 `[mcp_servers.<name>]` 表，支持 `command`、`args`、`env`、`cwd`、tool allow/deny 和审批模式。 |
| Anthropic Claude Code MCP 文档：<https://docs.anthropic.com/en/docs/claude-code/mcp> | Claude Code 支持远程 HTTP、本地 stdio、SSE、WebSocket；项目级共享配置写入 `.mcp.json`，本机私有配置写入 `~/.claude.json`；项目级 server 首次使用需要用户批准。 |
| MCP 官方介绍：<https://modelcontextprotocol.io/docs/getting-started/intro> | MCP 是让 AI 应用连接外部系统的开放标准；Claude、ChatGPT、开发工具和自建客户端都可复用同一类 server。 |
| OpenAI ChatGPT MCP 文档：<https://developers.openai.com/api/docs/mcp> | ChatGPT 接 MCP 走远程 HTTPS server / Apps / Connectors，不适合直接接这个本地 stdio 原型，除非以后给 StarBridge 包一层远程 HTTP server。 |

## 这台电脑现在需要什么

| 目标 | 需要 | 当前处理 |
| --- | --- | --- |
| Claude Code 调 StarBridge | 项目根目录 `.mcp.json`，stdio 启动 `python -m starbridge_mcp.mcp_server` | 已新增 `.mcp.json`，可提交到 GitHub。 |
| Codex 调 StarBridge | 本机 `.codex/config.toml` 或全局 `~/.codex/config.toml` | 公开模板保留在 `.codex/config.example.toml`；真实 `.codex/config.toml` 被 `.gitignore` 忽略，只留本机。 |
| 基础 MCP smoke test | Python 能从项目根目录启动 `starbridge_mcp.mcp_server` | 不需要 Photoshop、Illustrator、AutoCAD、Blender、ComfyUI 或 CapCut。 |
| 本机桥状态检查 | `python -m starbridge_mcp.server tools --json --safe-only` 和 `python examples/bridge_status.py --json --redact-paths --soft-exit` | 可在没有桌面软件时 soft-exit，输出应脱敏。 |
| 上传 GitHub | 只提交文档、共享配置、测试结果相关的安全内容 | 不提交 `.codex/config.toml`、`.env`、私有路径、真实素材和输出。 |

## 现在不需要什么

- 不需要把 StarBridge 暴露成公网 HTTPS MCP，除非目标是 ChatGPT Apps / Connectors。
- 不需要 OAuth、ngrok、Cloudflare Tunnel 或远程服务器。
- 不需要真实打开 PSD、AI、DWG、剪映草稿或客户素材来证明基础 MCP 可用。
- 不需要把 `PHOTOSHOP_EXE`、`ILLUSTRATOR_EXE`、`COMFY_ROOT`、`CAPCUT_DRAFTS_DIR` 等真实路径写入 GitHub。
- 不需要在公开仓库提交生成图、导出 SVG/PDF/PNG、模型文件、桌面软件缓存或账号状态。

## Claude Code 接入

项目级共享配置已经写入仓库根目录 `.mcp.json`：

```json
{
  "mcpServers": {
    "starbridge": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "starbridge_mcp.mcp_server"],
      "env": {
        "STARBRIDGE_PHOTOSHOP_SAFE_ONLY": "1",
        "STARBRIDGE_PHOTOSHOP_DEFAULT_DRY_RUN": "1",
        "STARBRIDGE_PHOTOSHOP_ALLOW_DESTRUCTIVE": "0"
      }
    }
  }
}
```

使用方式：

```powershell
cd <repo>
claude
/mcp
```

第一次看到 project-scoped server 时，Claude Code 会要求批准。批准后可以在 Claude Code 里让它列出 StarBridge tools，或直接问：

```text
用 StarBridge MCP 检查当前本机 creative software bridge 状态，只读，不写入。
```

如果不用 `.mcp.json`，也可以用命令写入项目级配置：

```powershell
claude mcp add --transport stdio --scope project starbridge -- python -m starbridge_mcp.mcp_server
```

## Codex 接入

Codex 的真实配置不提交。当前仓库保留安全模板：

```powershell
Copy-Item .codex\config.example.toml .codex\config.toml
```

项目级 `.codex/config.toml` 适合在本仓库内使用，内容形状如下：

```toml
[mcp_servers.starbridge]
command = "python"
args = ["-m", "starbridge_mcp.mcp_server"]

[mcp_servers.starbridge.env]
STARBRIDGE_PHOTOSHOP_SAFE_ONLY = "1"
STARBRIDGE_PHOTOSHOP_DEFAULT_DRY_RUN = "1"
STARBRIDGE_PHOTOSHOP_ALLOW_DESTRUCTIVE = "0"
```

如果写入全局 `~/.codex/config.toml`，建议补 `cwd` 指向本仓库根目录，但不要把这个真实路径提交到 GitHub。

Codex CLI 可用时检查：

```powershell
codex mcp list
```

如果当前电脑的 `codex.exe` 不能直接从 PowerShell 启动，可以只用本仓库的 stdio smoke test 验证 server；Codex app 下次读到本机配置后再验证 `/mcp` 面板。

## 本机测试命令

基础协议 smoke test：

```powershell
@'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"manual-test","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
'@ | python -m starbridge_mcp.mcp_server
```

安全能力和状态检查：

```powershell
python -m starbridge_mcp.server tools --json --safe-only
python examples\bridge_status.py --json --redact-paths --soft-exit
python scripts\security_check.py
python -m unittest discover -s tests
```

PowerShell 如果拦截 `npm.ps1`，用 `npm.cmd`：

```powershell
npm.cmd run starbridge:tools:safe
npm.cmd run bridge:status:safe
```

## 发布前判断

可以提交：

- `.mcp.json`
- `.codex/config.example.toml`
- `docs/` 里的接入说明
- 只读或 dry-run 测试

不提交：

- `.codex/config.toml`
- `.env`
- 本机绝对路径
- 真实 PSD / AI / DWG / DXF / 视频 / 模型 / 草稿 / 导出图
- OAuth、token、Cookie、账号和授权状态

