# StarBridge 路线图

## 已完成

- StarBridge MVP 状态入口。
- 统一结果 schema、warnings 和 next_steps。
- 路径和敏感输出脱敏。
- ComfyUI bridge 最小注册和 dry-run 示例。
- Jianying / CapCut bridge 最小注册和 safe draft_plan 示例。
- 发布审计 CI、SECURITY、CONTRIBUTING、模板和检查脚本。

## 下一步

- 把 release-readiness 分支开 PR 到 `main` 前做一次人工审阅。
- 单独处理 CAD/DXF 分支，不混入发布审计提交。
- 后续再评估完整 MCP stdio server 和 tool registry。
- 继续补充 bridge 能力矩阵，但保持真实资产和本机路径不进仓库。

## 暂不做

- 真实 ComfyUI queue。
- 真实剪映 / CapCut 草稿写入。
- 客户 CAD/DWG/DXF 工程处理。
- 自动上传或保存真实 artifact。
