# WorldForge 离线执行说明

WorldForge Offline Agent Bridge v0.1 使用本地任务文件驱动 UE 编辑器内执行层。

流程：Codex 创意指令 -> 本地任务 JSON -> WorldForge 安全检查 / 预览 / 检查点 -> UE 内置 Python 或 Editor Utility Widget -> UE 5.2.1 场景、蓝图、材质、交互。

边界：不使用网络端口，不监听局域网，不创建常驻服务，不启用 Remote Control，不创建 MCP，不修改全局 Codex 配置。

任务文件必须先通过 schema 和白名单校验。执行层只处理 M_WorldForgeBlockoutSandbox，只操作带 WorldForgeManaged 标签的 Actor，写操作前创建检查点，写操作后输出 World Summary。
