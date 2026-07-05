# WorldForge v0.3 接手审查报告

生成时间：2026-07-05 15:37 +08:00
状态：接手审查完成，进入安全停止路径。未修改 UE 资产，未启动 UE，未启用 Remote Control，未创建 MCP。

## 1. 范围确认

- 唯一工作根目录：`<WORLDFORGE_ROOT>`
- 唯一允许编辑的 UE 项目：`<WORLDFORGE_ROOT>\02_项目8_WorldForge增强版`
- 原始项目8：`<ORIGINAL_PROJECT8>`
- 本轮对原始项目8仅做只读哈希复核，未打开、未编辑、未移动、未删除、未重命名。
- WorldForge 仅作为本项目命名前缀处理，未下载或安装任何名为 WorldForge 的程序。

## 2. 已读取的既有成果

- `07_文档与报告\WorldForge_UE_Agent_Framework_v0.1_最终报告.md`
- `07_文档与报告\WorldForge_OfflineAgentBridge_v0.1_与未来城市漫游升级报告.md`
- `07_文档与报告\WorldForge_UE_Codex本机闭环接入_v0.2_最终报告.md`
- `07_文档与报告\DataRouter_来源核查.md`
- `07_文档与报告\WorldForge_停止报告_网络越界风险_20260705_145007.md`
- `06_性能与测试\WorldForge_性能基线.md`
- `00_审查与基线\WorldForge_接入前总审查报告.md`
- `00_审查与基线\WorldForge增强副本创建报告_20260705_142105.md`
- `00_审查与日志\项目8备份与增强副本复制报告_20260705_133650_corrected.md`
- `03_WorldForge控制层\Logs\WorldForge_OfflineBridge_任务002执行结果.json`

## 3. 当前实测结论

- 原项目8与只读备份文件数：75 / 75
- 原项目8与只读备份哈希差异：0
- 当前只有 `02_项目8_WorldForge增强版` 被列为本轮允许编辑项目。
- `M_WorldForgeLab.umap` 已存在。
- `M_WorldForgeBlockoutSandbox.umap` 已存在。
- 离线任务 002 记录的 `WorldForgeManaged Actor` 数：42。
- Actor 总数限制：60，当前记录未超过限制。
- `EUW_WorldForgeControlDesk.uasset` 已存在。
- `BP_WorldForgeOfflineTaskRunner.uasset` 已存在。
- `BP_WorldForgeCityMoodController.uasset` 已存在。
- `BP_WorldForgeExplorerPawn.uasset` 已存在。
- 检查点机制已存在，当前检查点包括 `checkpoint_001_future_city_initial.json`、`checkpoint_002_pre_city_upgrade.json`、`checkpoint_002_post_city_upgrade.json`。
- 当前无 `UnrealEditor.exe`、`UnrealEditor-Cmd.exe`、`CrashReportClient.exe` 残留进程。
- 目标端口 `30010`、`30020`、`8000`、`6666`、`30000` 的 TCP 监听数为 0，UDP 端点数为 0。
- 当前未创建项目级 `.codex\config.toml`。
- 全局 Codex 配置只读复核 SHA256：`B2638BC00D387E95D9BC97AD4ED038FB3AB5A5B4B1692F03224A4A9E31DD5970`。

## 4. Content\WorldForge 当前资源

当前 `Content\WorldForge` 下只读统计到 24 个资产文件：

- `Blueprints\BP_WorldForgeAgentDirector.uasset`
- `Blueprints\BP_WorldForgeBlockoutBuilder.uasset`
- `Blueprints\BP_WorldForgeCheckpointManager.uasset`
- `Blueprints\BP_WorldForgeCityMoodController.uasset`
- `Blueprints\BP_WorldForgeCommandRouter.uasset`
- `Blueprints\BP_WorldForgeExplorerPawn.uasset`
- `Blueprints\BP_WorldForgeOfflineTaskRunner.uasset`
- `Blueprints\BP_WorldForgeSafetyController.uasset`
- `Blueprints\BP_WorldForgeWorldProbe.uasset`
- `Blueprints\BP_CodexControlActor.uasset`
- `EditorTools\EUW_WorldForgeControlDesk.uasset`
- `Maps\M_WorldForgeBlockoutSandbox.umap`
- `Maps\M_WorldForgeLab.umap`
- `Materials\M_WorldForge_Accent.uasset`
- `Materials\M_WorldForge_Building.uasset`
- `Materials\M_WorldForge_Ground.uasset`
- `Materials\M_WorldForge_Plaza.uasset`
- `Materials\M_WorldForge_Road.uasset`
- `Materials\M_WorldForge_Tower.uasset`
- `Materials\M_WorldForge_Upgrade_GuideLine.uasset`
- `Materials\M_WorldForge_Upgrade_LightStrip.uasset`
- `Materials\M_WorldForge_Upgrade_Observation.uasset`
- `Materials\M_WorldForge_Upgrade_WindowGlow.uasset`
- `UI\WBP_WorldForgeStatus.uasset`

预留目录状态：

- `Content\WorldForge\RemoteControl` 已存在，文件数 0。
- `Content\WorldForge\CommandGate` 不存在。
- `Content\WorldForge\Data\CommandContracts` 不存在。
- `Content\WorldForge\Input` 不存在。

## 5. 当前未启用状态

本轮实测和文件审查确认：

- Remote Control 未创建 Preset，项目 `.uproject` 未启用 RemoteControl 插件。
- MCP 未创建，未启动，未写项目级 Codex 配置。
- 未启动任何本地 HTTP 或 WebSocket 服务。
- 当前端口检查没有发现目标端口监听。

但最新 UE 日志仍记录以下风险：

- `LogTcpMessaging: Initializing TcpMessaging bridge`
- `LogModuleManager: Shutting down and abandoning module WebSockets`
- `LogModuleManager: Shutting down and abandoning module HTTP`
- `LogHttp` 中仍有 `https://datarouter.ol.epicgames.com/... UploadType=eteventstream`

这些日志不等于当前存在监听端口，但足以说明 Remote Control 启用前的“禁用 TCP Messaging、WebSocket、外部 HTTP 风险”尚未达到可放行状态。

## 6. Enhanced Input 状态

`Config\DefaultInput.ini` 显示：

- `DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput`
- `DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent`

因此作品交互线的人工 GUI 补丁应优先走 Enhanced Input 最小路径，但本轮未通过 Python 或二进制方式修改蓝图。

## 7. 本轮不继续的原因

v0.2 已证明 UE 5.2 Python 不适合作为可靠修改 Blueprint K2 节点、InputKey 节点、WidgetTree、OnClicked 图表的自动化路径。当前 Codex 会话没有可验证、可回滚的 UE 图形界面节点编辑能力。按本轮授权边界，不能伪造 E 键/UI 成功，也不能继续 Python 探针或二进制资产补丁。

Remote Control 本机回环审查也未通过放行条件：最新 UE 日志仍出现 TcpMessaging 初始化和 DataRouter 外部 HTTP 记录，且无法通过当前会话的 UE 图形界面确认 Remote Control API 将仅绑定 `127.0.0.1` 或 `::1`。

## 8. 接手结论

- 原项目8是否修改：否。
- 原项目8与备份差异：0。
- 全局 Codex 配置是否修改：否。
- 是否安装软件：否。
- 是否升级 UE：否。
- 是否修改防火墙、注册表、环境变量：否。
- 是否启用 Remote Control：否。
- 是否启用 MCP：否。
- 是否启动 HTTP/WebSocket 服务：否。
- 是否继续 Python 蓝图探针：否。
- 是否创建 CommandGate：否。

下一步应先由人工在 UE 5.2.1 图形界面完成最小 E 键/UI 蓝图补丁；随后重新做端口、日志、Messaging 和 DataRouter 审查。只有审查全部通过，才允许进入 Remote Control 和 stdio MCP。
