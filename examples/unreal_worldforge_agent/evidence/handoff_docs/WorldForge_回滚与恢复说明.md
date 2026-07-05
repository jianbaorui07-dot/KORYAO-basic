# WorldForge 回滚与恢复说明

检查点只记录 WorldForgeManaged Actor 的名称、类别、Transform 和关键参数。恢复时只允许影响 WorldForgeManaged Actor，不删除或修改旧内容。

如果需要移除整个 WorldForge 框架，只删除增强副本中的 Content/WorldForge 以及 WORLDFORGE_ROOT 内的 WorldForge 文档、任务、日志和 MCP 桥接文件。原始项目8不受影响。
