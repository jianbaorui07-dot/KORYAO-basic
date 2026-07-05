# WorldForge 安全边界

1. 不修改原始项目8。
2. 不修改全局 Codex 配置。
3. 不安装软件，不下载插件或资产。
4. 不创建 C++ Source 或 Native Plugin。
5. 不监听 0.0.0.0、局域网或公网地址。
6. 只允许 Remote Control 绑定 127.0.0.1。
7. 只操作 Content/WorldForge 和带 WorldForgeManaged 标签的 Actor。
8. 超出 Actor 预算、内存不足、温度超限、UE 崩溃或网络越界时立即停止。
