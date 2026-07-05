# DataRouter 来源核查

生成时间：2026-07-05 14:56:19 +08:00
核查日志：<WORLDFORGE_ROOT>\02_项目8_WorldForge增强版\Saved\Logs\我的项目8.log

## 结论

DataRouter 记录来源可确认是 UE 5.2.1 编辑器自身的 Analytics / Event Stream 记录，而不是 WorldForge 脚本主动发起的网络请求，也不是 Remote Control、MCP、WebSocket 或本地 HTTP 服务。

证据：

- 日志中出现 LogAnalytics: Display: [UEEditor.Rocket.Release] APIServer = https://datarouter.ol.epicgames.com/。
- 日志中关闭阶段出现 LogModuleManager: Shutting down and abandoning module AnalyticsET。
- 完整 POST 行中 AppID=UEEditor.Rocket.Release，UploadType=eteventstream。
- 关闭阶段 FHttpManager::Flush 显示仍有 1 个 outstanding request，状态为 Processing。日志未显示明确的发送成功结果，因此只能确认请求被创建/处理中，不能确认已成功发送完成。
- 日志同时有 Started CrashReportClient，但 DataRouter URL 本身是 eteventstream，不是 CrashReport 上传路径；本次未发现 UE 崩溃记录。

## 关键日志行

- Line 9: LogWindows: Started CrashReportClient (pid=19780)
- Line 1023: [2026.07.05-06.47.22:853][  0]LogAnalytics: Display: [UEEditor.Rocket.Release] APIServer = https://datarouter.ol.epicgames.com/. AppVersion = 5.2.1-26001984+++UE5+Release-5.2
- Line 1708: [2026.07.05-06.48.06:568][  3]LogModuleManager: Shutting down and abandoning module AnalyticsET (865)
- Line 2102: [2026.07.05-06.48.06:807][  3]LogHttp: Warning: [FHttpManager::Flush] FlushReason was Shutdown. Unbinding delegates for 1 outstanding Http Requests:
- Line 2103: [2026.07.05-06.48.06:807][  3]LogHttp: Warning: 	verb=[POST] url=[https://datarouter.ol.epicgames.com/datarouter/api/v1/public/data?SessionID=<REDACTED>&AppID=UEEditor.Rocket.Release&AppVersion=5.2.1-26001984%2B%2B%2BUE5%2BRelease-5.2&UserID=<REDACTED>&AppEnvironment=datacollector-binary&UploadType=eteventstream] refs=[1] status=Processing


## 请求信息

- 时间：2026-07-05 06:48:06 UTC / 2026-07-05 14:48:06 +08:00
- 进程：UnrealEditor.exe，本次自动化启动 PID 13020；日志另记录 CrashReportClient pid=19780。
- 方法：POST
- 域名：datarouter.ol.epicgames.com
- URL：verb=[POST] url=[https://datarouter.ol.epicgames.com/datarouter/api/v1/public/data?SessionID=<REDACTED>&AppID=UEEditor.Rocket.Release&AppVersion=5.2.1-26001984%2B%2B%2BUE5%2BRelease-5.2&UserID=<REDACTED>&AppEnvironment=datacollector-binary&UploadType=eteventstream] refs=[1] status=Processing
- 状态：Processing；无明确 success/completed 行。

## 是否修改 UE Bug Reports 隐私设置

否。

原因：本次来源更明确指向 UE Editor Analytics / Event Stream，而非单纯 Bug Report 设置；用户只允许通过 UE 图形界面执行 Privacy -> Bug Reports -> Don't Send，且禁止手动编辑 AppData、注册表、防火墙、网络设置、引擎目录或原项目。因此本次不改任何隐私设置，只记录来源并继续离线 Agent Bridge 路线。

## 后续边界

本次继续不启用 Remote Control、不启动 MCP、不创建 HTTP 服务、不改全局 Codex 配置。后续每次启动 UE 仍需复核日志和端口，DataRouter 外部 URL 若再次出现，必须继续记录为网络边界风险。
