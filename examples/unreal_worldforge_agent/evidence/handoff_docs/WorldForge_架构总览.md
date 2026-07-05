# WorldForge 架构总览

造境WorldForge：虚幻引擎 3D 世界开发 Agent v0.1 采用保守分层：Codex 负责规划和审查，本地 MCP 只作为 stdio 桥接，Remote Control 只允许 127.0.0.1，UE 内只暴露受控蓝图入口，所有场景写入限定在 Content/WorldForge。

当前 UE 5.2.1 路径采用：Codex -> 项目级 MCP 配置 -> 本地 stdio MCP 桥接 -> 127.0.0.1 Remote Control API -> 受控蓝图入口 -> WorldForge 安全控制器 -> UE 场景和蓝图。

v0.1 不创建 C++、不编译插件、不下载资产、不修改原始项目8。
