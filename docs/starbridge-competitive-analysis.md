# StarBridge 竞品和参考边界

本仓库会参考已有 MCP、REST API 和桌面自动化项目，但不直接复制高风险能力。

## 参考方向

| 方向 | 可借鉴 | StarBridge 边界 |
| --- | --- | --- |
| ComfyUI MCP | workflow schema、节点发现、任务状态 | 默认 dry-run，不下载模型，不提交真实 queue。 |
| Adobe 桥 | COM / JSX 调用模式、文档信息读取 | 不打开私有工程，不导出客户素材。 |
| Blender MCP | addon 与本地 server 分离 | 不执行任意 Python，不下载外部资产。 |
| Jianying / CapCut 工具 | 草稿结构和时间线抽象 | 当前只生成 `draft_plan`，不写真实草稿。 |

## 发布审计重点

- 公开仓库内容是否脱敏。
- 示例是否只使用占位素材。
- CI 是否不依赖商业软件。
- 脚本是否只读或写入安全 demo 输出目录。
