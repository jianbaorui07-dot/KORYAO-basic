# StarBridge 发布检查清单

发布前只确认公开协作仓库是否安全、可测试、可说明清楚。

## 必须满足

- `python -m unittest discover -s tests` 通过。
- `python -m starbridge_mcp.server --json` 返回 exit code 0。
- 未配置本机软件时，bridge 返回 `ok=false`、`warnings`、`next_steps`，不能崩溃。
- `python examples\bridge_status.py --json` 可运行。
- 发布检查脚本通过。
- CI 文件存在并且不依赖商业软件。
- `SECURITY.md`、`CONTRIBUTING.md`、PR 模板和 issue 模板存在。

## 可接受情况

- `python -m starbridge_mcp.server --json --strict` 在未配置本机软件时返回 exit code 1。
- Photoshop、Illustrator、Blender、AutoCAD、ComfyUI、剪映 / CapCut 未安装或未启动。
- ComfyUI 状态为不可达，但输出结构完整。
- Jianying / CapCut 草稿目录未配置，但输出结构完整。

## 不在本轮处理

- CAD/DXF MVP 分支。
- release 后的完整 MCP stdio server。
- 真实 ComfyUI queue。
- 真实剪映 / CapCut 草稿写入。
