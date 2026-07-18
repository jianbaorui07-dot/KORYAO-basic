# GitHub 可见性优化

这份文件记录本仓库面向 GitHub 搜索、外部协作者和 MCP 生态的公开呈现方式。它只涉及公开元数据和说明文字，不涉及账号、token、素材、模型或本机路径。

## 推荐仓库描述

建议 GitHub repository description 使用：

```text
Windows-first local MCP stdio server and safety bridge for AI agents connecting to ComfyUI, Blender, AutoCAD/DXF, Photoshop, Illustrator, and CapCut/Jianying.
```

如果想保留中文，可以使用：

```text
CreNexus: Codex/AI agent 接入 ComfyUI、Blender、AutoCAD、Photoshop、Illustrator、剪映的本地 MCP stdio 安全桥。
```

## 推荐 Topics

GitHub topics 建议控制在 20 个以内，优先覆盖 MCP、AI agent、本地软件桥和具体创意软件：

```text
mcp
model-context-protocol
codex
ai-agent
local-first
creative-tools
creative-software
comfyui
blender
autocad
dxf
photoshop
illustrator
capcut
jianying
windows
workflow-validation
automation
```

## README 首屏原则

README 首屏应该让陌生访问者在 10 秒内看懂三件事：

| 问题 | 首屏答案 |
| --- | --- |
| 这是什么 | Windows-first、local-first 的 creative software MCP stdio server |
| 能接什么 | ComfyUI、Blender、AutoCAD/DXF、Photoshop、Illustrator、CapCut/Jianying |
| 安全边界是什么 | 探针、校验、脱敏状态和受保护写入，不上传私有资产 |

## 外部协作入口

为了让别人更容易参与，仓库应该保留这些文件：

| 文件 | 用途 |
| --- | --- |
| `CONTRIBUTING.md` | 告诉外部贡献者什么能改、怎么测、什么不能提交 |
| `SECURITY.md` | 说明隐私资产、路径、凭证和写入工具的安全边界 |
| `.github/ISSUE_TEMPLATE/bridge_request.yml` | 收集新软件桥需求 |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | 收集可复现的问题 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 强制贡献者检查测试和隐私边界 |

## 本机执行命令

如果 GitHub CLI 已登录，可以用下面命令设置公开元数据：

```powershell
gh repo edit jianbaorui07-dot/CreNexus --description "Windows-first local MCP stdio server and safety bridge for AI agents connecting to ComfyUI, Blender, AutoCAD/DXF, Photoshop, Illustrator, and CapCut/Jianying."
gh repo edit jianbaorui07-dot/CreNexus --add-topic mcp --add-topic model-context-protocol --add-topic codex --add-topic ai-agent --add-topic local-first --add-topic creative-tools --add-topic creative-software --add-topic comfyui --add-topic blender --add-topic autocad --add-topic dxf --add-topic photoshop --add-topic illustrator --add-topic capcut --add-topic jianying --add-topic windows --add-topic workflow-validation --add-topic automation
```

当前机器如果 `gh auth status` 显示未登录，需要先由仓库所有者手动运行：

```powershell
gh auth login
```
