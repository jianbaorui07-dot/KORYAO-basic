# WorldForge UE 5.2.1 适配层说明

UE 5.2.1 当前不使用官方 Unreal MCP。v0.1 通过项目级配置和本地 stdio MCP 桥接访问 127.0.0.1 Remote Control API。

安全边界：不监听 0.0.0.0，不监听局域网地址，不启用 WebSocket Remote Control，不启用 TCP Messaging，不启用 UDP Messaging Transport，不修改全局 Codex 配置。

所有 UE 内容写入 Content/WorldForge。旧 Content、默认地图、原始项目8均不得修改。
