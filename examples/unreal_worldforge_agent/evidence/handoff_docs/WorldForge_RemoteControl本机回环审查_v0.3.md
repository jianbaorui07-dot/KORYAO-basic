# WorldForge Remote Control 本机回环审查 v0.3

生成时间：2026-07-05 15:37 +08:00
状态：未通过放行条件，未启用 Remote Control，未启用 MCP。

## 1. 审查方式

本轮仅做只读文件、日志、进程和端口审查：

- 未启动 UE。
- 未启用 Remote Control。
- 未创建 Remote Control Preset。
- 未创建 CommandGate。
- 未修改项目设置。
- 未修改防火墙、注册表、系统环境变量或全局 Codex 配置。

## 2. 当前端口状态

目标端口：

- `30010`
- `30020`
- `8000`
- `6666`
- `30000`

当前实测：

- TCP 监听：0
- UDP 端点：0
- UnrealEditor 进程：0

这说明当前没有残留服务，但不等于 Remote Control 可安全启用。

## 3. 项目配置审查

`.uproject` 当前未启用 RemoteControl 插件。

`Content\WorldForge\RemoteControl` 目录存在但文件数为 0。

以下目标资源尚不存在：

- `/Game/WorldForge/CommandGate/BP_WorldForgeCommandGate`
- `/Game/WorldForge/RemoteControl/RC_WorldForgeCommandGate`
- `/Game/WorldForge/Data/CommandContracts/DA_WorldForgeCommandPolicy`
- `WorldForge_Command_Whitelist_v0.3.json`
- `004_LocalLoopbackProof.json`

项目级 `.codex\config.toml` 不存在。

## 4. 风险日志

最新增强副本 UE 日志仍记录：

- `LogTcpMessaging: Initializing TcpMessaging bridge`
- `LogModuleManager: Shutting down and abandoning module UdpMessaging`
- `LogModuleManager: Shutting down and abandoning module TcpMessaging`
- `LogModuleManager: Shutting down and abandoning module WebSockets`
- `LogModuleManager: Shutting down and abandoning module HTTP`
- `LogHttp` 关闭阶段仍存在 `https://datarouter.ol.epicgames.com/... UploadType=eteventstream`

这些记录证明：虽然当前没有目标端口监听，但无法确认下一次 UE 图形界面启动和 Remote Control 启用时满足以下条件：

- 禁止 TCP Messaging。
- 禁止 WebSocket。
- 禁止外部 HTTP。
- 仅 Remote Control API 可用。
- 监听地址严格限制为 `127.0.0.1` 或 `::1`。

## 5. 放行条件逐项结论

- 仅启用 Remote Control API：未验证，未放行。
- 禁止 Remote Control Web Interface：未验证，未放行。
- 禁止 WebSocket：最新日志仍有 WebSockets 模块关闭记录，未放行。
- 禁止 UDP Messaging：当前无端口残留，但日志仍有模块记录；只能继续使用启动参数隔离，未放行 Remote Control。
- 禁止 TCP Messaging：最新日志有 `TcpMessaging bridge` 初始化，未通过。
- 禁止 Multi-User：未见启用证据，但未通过 GUI 复核。
- 禁止 Live Link：未见启用证据，但未通过 GUI 复核。
- 禁止 Pixel Streaming：未见启用证据，但未通过 GUI 复核。
- 禁止自动启动 Web Server：未验证，未放行。
- 禁止自动启动 WebSocket Server：未验证，未放行。
- 禁止 Remote Python Execution：未见启用证据，但未通过 GUI 复核。
- 禁止 Execute Console Command Remote Execution：未验证，未放行。
- 禁止 Allow Any Remote Function Call：未验证，未放行。
- 只允许固定函数：CommandGate 尚未创建，未放行。
- 监听地址仅 `127.0.0.1` 或 `::1`：未启用服务，不能证明，未放行。

## 6. 结论

Remote Control 本机回环审查 v0.3 未通过。

按强制停止条件：

- 不启用 Remote Control。
- 不启用 MCP。
- 不创建 stdio MCP server。
- 不写项目级 `.codex\config.toml`。
- 不修改防火墙、注册表、环境变量或全局 Codex 配置。
- 保持 Offline Agent Bridge 路线。

需要先通过 UE 图形界面明确关闭或证明 TCP Messaging、WebSocket、外部 HTTP/DataRouter 风险，再重新进行本机回环审查。
