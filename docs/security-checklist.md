# StarBridge 安全检查清单

本清单用于公开发布前的最小安全审计。

## 仓库内容

- 不提交真实用户目录、安装目录、缓存目录、素材目录或导出目录。
- 不提交密码、token、Cookie、OAuth 缓存、账号、许可证或支付信息。
- 不提交模型、LoRA、VAE、ControlNet、生成图片或 ComfyUI 输出。
- 不提交 PSD、AI、DWG、DXF、视频文件、真实剪映 / CapCut 草稿或客户文件。
- 示例只能使用占位素材名和参数化路径。

## 运行边界

- CI 只运行单元测试、安全脚本和只读状态检查。
- CI 不启动或连接 Photoshop、Illustrator、Blender、AutoCAD、ComfyUI、剪映或 CapCut。
- ComfyUI 示例默认 dry-run，不真实 queue。
- Jianying / CapCut 示例只生成 `draft_plan`，不写真实草稿目录。

## 发布前命令

```powershell
python -m unittest discover -s tests
python -m starbridge_mcp.server --json
python examples\bridge_status.py --json
powershell -ExecutionPolicy Bypass -File scripts\check_forbidden_files.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_repository_safety.ps1
powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1
```
