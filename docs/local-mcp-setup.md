# StarBridge 本地 MCP 接入说明

StarBridge 当前实现的是最小统一状态入口：先让 Codex、Cursor、Claude Code 或其他 MCP 客户端能用同一套 JSON 查看各软件桥状态。后续再逐步把稳定动作封装成 MCP tools。

## 1. 本机准备

必须由用户手动完成：

- Adobe Photoshop / Illustrator：安装、登录、授权，并确认桌面软件可正常打开。
- AutoCAD / ZWCAD / GstarCAD / BricsCAD：安装、授权；AutoCAD 自动化需要 Windows COM 或对应 MCP 子项目。
- Blender：安装 desktop 或 CLI；如使用 Blender MCP，需要手动安装 addon。
- ComfyUI：本机启动 server，默认 `http://127.0.0.1:8188`。
- 剪映 / CapCut：安装客户端，手动确认草稿目录；不要让脚本自动登录账号。

可先运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_starbridge.ps1
python -m starbridge_mcp.server --json
```

如果只检查某一个桥：

```powershell
python -m starbridge_mcp.server --bridge comfyui --json
python -m starbridge_mcp.server --bridge photoshop --json
python -m starbridge_mcp.server --bridge illustrator --json
```

## 2. 本地环境变量

把 `.env.example` 复制成本机 `.env` 或设置 PowerShell 用户环境变量。不要把真实路径、账号、token、模型文件名、素材路径写进公开仓库。

常用变量：

```powershell
$env:STARBRIDGE_COMFYUI_URL="http://127.0.0.1:8188"
$env:COMFY_ROOT="<path-to-ComfyUI>"
$env:BLENDER_EXE="<path-to-blender.exe>"
$env:AUTOCAD_EXE="<path-to-acad.exe>"
$env:PHOTOSHOP_EXE="<path-to-Photoshop.exe>"
$env:ILLUSTRATOR_EXE="<path-to-Illustrator.exe>"
$env:JIANYING_DRAFTS_DIR="<path-to-jianying-drafts>"
$env:CAPCUT_DRAFTS_DIR="<path-to-capcut-drafts>"
```

## 3. Codex / Cursor / Claude Code 配置方向

当前 `starbridge_mcp.server` 是 CLI-style JSON 状态入口，还不是完整 MCP stdio server。MCP 客户端可以先用“本地命令工具”或 workspace 脚本调用它；后续会把同一套 schema 挂到真正 MCP tool registry。

建议的未来 MCP 配置形态：

```json
{
  "mcpServers": {
    "starbridge": {
      "command": "python",
      "args": ["-m", "starbridge_mcp.server", "--json"]
    }
  }
}
```

如果客户端严格要求 stdio MCP 协议，这个配置需要等下一轮补 `mcp` SDK server 后再启用。当前可执行验证命令是：

```powershell
python -m starbridge_mcp.server --json
```

## 4. 安全边界

- 状态入口只读，不自动打开客户文件，不写真实素材。
- 输出会脱敏用户目录、token、Cookie、OAuth、PSD/AI/DWG/DXF、模型文件、剪映草稿和导出视频。
- `output/`、`scratch/`、`third_party_research/`、模型、PSD、AI、DWG、DXF、视频和草稿文件已加入 `.gitignore`。
- 需要登录、订阅、验证码、OAuth、Adobe 授权、AutoCAD 授权或 GitHub 授权时，必须由用户手动处理。

## 5. 后续 MCP 工具规划

优先顺序：

1. `starbridge.status`：返回所有桥统一状态。
2. `starbridge.probe(bridge)`：返回单桥探针结果。
3. `comfyui.validate_workflow` / `comfyui.submit_txt2img`：只用 API workflow，不提交模型或输出图。
4. `photoshop.get_document_info` / `illustrator.get_document_info`：只读当前文档。
5. `cad.generate_dxf`：离线 DXF 生成优先，AutoCAD COM 作为可选。
6. `capcut.inspect_drafts`：只读草稿目录结构摘要，不输出素材路径。
