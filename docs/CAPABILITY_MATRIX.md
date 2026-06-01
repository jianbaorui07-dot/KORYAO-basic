# StarBridge v0.1.0-alpha 能力矩阵

本矩阵只记录当前仓库可以公开发布和测试的能力边界。`stable` 表示有离线测试或 CI 安全验证；`experimental` 表示已有探针或 sandbox demo，但依赖本机软件或还不能承诺生产闭环；`planned` 表示路线图能力，不能写成已经完成。

`not implemented` 表示不支持的能力，例如自动登录、绕过授权、读取客户工程文件、提交模型或无确认写入真实桌面软件。

| Bridge | Stable | Experimental | Planned | Writes files | CI safe | Needs local app | Safety notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| StarBridge core | `starbridge.status`、`starbridge.tools`、MCP stdio `tools/list` / `tools/call` | 无 | 更多客户端适配 | No | Yes | No | read-only；所有返回走 sanitizer；不打开用户文件。 |
| ComfyUI | `comfyui.workflow_validate`；公开 workflow JSON 离线校验 | `comfyui.system_probe` 需要本机服务在线时才返回 ok；txt2img CLI 仍是本机实验入口 | img2img、inpaint、upscale、job manifest | No for validate/probe；生成脚本只写本机输出且不提交 | Yes for workflow validate；probe 离线时返回 `ok=false` / warning | Only for live probe or generation | 不提交模型、LoRA、VAE、ControlNet、生成图片或本机 ComfyUI 输出。 |
| AutoCAD / DXF headless | `autocad_dxf.validate_cad_plan`、`autocad_dxf.summarize_plan`、DXF dry-run、guarded `write_dxf` | 真实 DXF 写入依赖可选 `ezdxf` | 更完整 CAD entity schema | Only `examples/cad/output` and only with `confirm_write=true` | Yes | No | 不需要 AutoCAD；默认 `dry_run=true`；路径不能逃出 `examples/cad/output`。 |
| CAD / AutoCAD desktop probe | `cad_autocad.environment_probe` | 真实 AutoCAD COM/MCP 控制 | 受控桌面 CAD demo | No | Yes, as unavailable/warning when app is absent | Yes for real automation | CI 不依赖 AutoCAD；不能打开客户 DWG/DXF 或写真实项目输出。 |
| Photoshop | read-only status shape / `photoshop.session_info` safe probing | 真实 COM、`document_info`、sandbox PSD create/export demo | subject extract MCP tool | Only `examples/output/photoshop` and only with `confirm_write=true` or `confirm_export=true` | No for real COM; dry-run schema is CI safe | Yes | 真实 COM 操作是 experimental；不打开私有 PSD；不提交 PSD、源图、导出图、安装路径或商业素材。 |
| Illustrator | read-only status shape | 真实 COM、`document_info`、sandbox artboard/export demo | preflight、trace image to vector | Only `examples/output/illustrator` and only with `confirm_write=true` or `confirm_export=true` | No for real COM; dry-run schema is CI safe | Yes | 真实 Illustrator 操作是 experimental；不读取客户 `.ai`、源图路径或导出目录。 |
| Blender | `blender.environment_probe` | 无公开写入闭环 | safe scene script、render manifest | No | Yes, as unavailable/warning when app is absent | Only for future scene scripts | 不打开私有 `.blend`，不执行任意用户 Python，不下载外部资产。 |
| CapCut / Jianying | `jianying_capcut.draft_probe` 只检查环境变量和目录配置形状 | 无 | safe draft skeleton / manifest research | No | Yes, as unavailable/warning when app is absent | Only for future local validation | 只做 draft directory probe；不读取 `draft_content.json`、草稿内容、账号、缓存或导出视频。 |

## 明确边界

- `starbridge.status` 是 stable、CI safe、read-only。
- `comfyui.workflow_validate` 是 stable、CI safe、read-only。
- `autocad_dxf.validate_cad_plan`、`autocad_dxf.summarize_plan` 和 DXF dry-run 是 stable、CI safe。
- Photoshop 和 Illustrator 的真实 COM 操作是 experimental、requires local app、not CI safe。
- Adobe demo 的真实输出只能写到 `examples/output/photoshop` 或 `examples/output/illustrator`，并且必须被 `.gitignore` 忽略。
- CapCut / Jianying 只做 draft directory probe，不读取草稿内容。
