# Codex 接入 Adobe 项目调研

调研日期：2026-06-25。范围是 GitHub 上公开的 Adobe / Photoshop / Illustrator / Premiere Pro / After Effects / InDesign / Lightroom / Firefly MCP 项目，以及明确提到 Codex、Claude Code、Cursor 或 AI agent 的本地软件桥项目。

本文只记录公开架构、接口形状和安全边界；不复制第三方源码、安装脚本、桌面路径、素材路径、账号信息、导出结果或私有工程。

## 本地拉取状态

已把高相关仓库浅克隆到本机忽略目录 `third_party_research/`，用于只读研究。该目录已被 `.gitignore` 忽略，不进入公开发布范围。

## 优先参考项目

| 项目 | 软件范围 | 参考价值 | StarBridge 吸收方式 |
| --- | --- | --- | --- |
| [adobe/generator-app-remote-mcp-server-generic](https://github.com/adobe/generator-app-remote-mcp-server-generic) | Adobe App Builder / remote MCP | Adobe 官方 MCP 模板 | 只参考 remote MCP 包装方式，不引入云运行时依赖 |
| [mikechambers/adb-mcp](https://github.com/mikechambers/adb-mcp) | Photoshop / Premiere | Adobe 工具经 MCP 暴露给 AI 的早期 PoC | 只参考分层方式，不接入任意脚本执行 |
| [stewberticus/adobe-mcp](https://github.com/stewberticus/adobe-mcp) | Photoshop / Premiere / Illustrator / InDesign | 多 Adobe 软件统一 MCP registry | 借鉴 bridge registry 和 tool grouping |
| [corbett3000/adobe-mcp-server](https://github.com/corbett3000/adobe-mcp-server) | InDesign / Photoshop / Illustrator | macOS Adobe Creative Cloud 控制思路 | 仅作跨平台对照 |
| [helloprkr/mcp-adobe-cloud](https://github.com/helloprkr/mcp-adobe-cloud) | Lightroom / Premiere / After Effects / Aero | Adobe cloud 方向集合 | 只记录路线，不接入账号/API 调用 |
| [alisaitteke/photoshop-mcp](https://github.com/alisaitteke/photoshop-mcp) | Photoshop | 工具分类、平台 detector/executor、本地 UI | 吸收工具分层和审计卡片思路 |
| [loonghao/photoshop-python-api-mcp-server](https://github.com/loonghao/photoshop-python-api-mcp-server) | Photoshop | Windows COM / Python 边界清楚 | 对齐 `photoshop.session_info`、`document_info`、layer 摘要 |
| [dcc-mcp/dcc-mcp-photoshop](https://github.com/dcc-mcp/dcc-mcp-photoshop) | Photoshop UXP | UXP WebSocket 适配器 | 对齐 Node Proxy + UXP v2 实验链路 |
| [rookietopred02-gif/photoshop-mcp-windows-first](https://github.com/rookietopred02-gif/photoshop-mcp-windows-first) | Photoshop | Windows-first、Codex skill、smoke coverage | 参考 Windows 结构化状态和 Codex skill 组织 |
| [00bx/00bx-photoshop-mcp](https://github.com/00bx/00bx-photoshop-mcp) | Photoshop | 大规模工具索引和 skill 知识加载 | 只参考目录组织，不复制工具实现 |
| [ie3jp/illustrator-mcp-server](https://github.com/ie3jp/illustrator-mcp-server) | Illustrator | read / manipulate / export / preflight 分组成熟 | 先扩展只读 `document_info` 和导出 preflight |
| [krVatsal/illustrator-mcp](https://github.com/krVatsal/illustrator-mcp) | Illustrator | Windows COM 与 macOS AppleScript 双路线 | 参考跨平台抽象和脚本投递边界 |
| [spencerhhubert/illustrator-mcp-server](https://github.com/spencerhhubert/illustrator-mcp-server) | Illustrator | 直接投递 Illustrator JavaScript 的简洁模型 | 只作风险对照，不接任意脚本入口 |
| [zipging/illustrator-mcp-for-codex](https://github.com/zipging/illustrator-mcp-for-codex) | Illustrator / Codex | 明确面向 Codex 的 Illustrator MCP | 参考 Codex 配置说明和最小工具面 |
| [Dakkshin/after-effects-mcp](https://github.com/Dakkshin/after-effects-mcp) | After Effects | 高关注 AE ExtendScript MCP | 只作为未来 AE bridge 研究 |
| [JUNKDOGE-JOE/after-effects-mcp](https://github.com/JUNKDOGE-JOE/after-effects-mcp) | After Effects | 明确面向 Codex / Cursor / Claude Code | 参考 agent 入口和工具命名 |
| [ishu86/after-effects-mcp](https://github.com/ishu86/after-effects-mcp) | After Effects | comp/layer/keyframe/effect 工具覆盖 | 未来先做只读 comp/layer 摘要 |
| [hetpatel-11/Adobe_Premiere_Pro_MCP](https://github.com/hetpatel-11/Adobe_Premiere_Pro_MCP) | Premiere Pro | 高关注 Premiere MCP，明确支持 Codex | 参考 timeline / export / project summary 分层 |
| [leancoderkavy/premiere-pro-mcp](https://github.com/leancoderkavy/premiere-pro-mcp) | Premiere Pro | CEP / ExtendScript 路线清楚 | 未来 Premiere bridge 先做 project/timeline 只读摘要 |
| [antipaster/Adobe-Premiere-Pro-MCP](https://github.com/antipaster/Adobe-Premiere-Pro-MCP) | Premiere Pro | 面向 Claude/Codex 的编辑工具集 | 参考本地 MCP 配置和工具粒度 |
| [sylphiette269/premiere-mcp-editor-cn](https://github.com/sylphiette269/premiere-mcp-editor-cn) | Premiere Pro / 中文工作流 | 面向 Claude Code、Codex、OpenClaw 的中文剪辑助手 | 参考中文提示词与素材目录边界 |
| [zachshallbetter/indesign-mcp-server](https://github.com/zachshallbetter/indesign-mcp-server) | InDesign | 文档、文本、页面、样式工具覆盖完整 | 未来 InDesign bridge 先做文档结构 preflight |
| [lucdesign/indesign-mcp-server](https://github.com/lucdesign/indesign-mcp-server) | InDesign | InDesign automation 工具分组 | 参考文档生命周期和页面对象摘要 |
| [popscallion/indesign-mcp](https://github.com/popscallion/indesign-mcp) | InDesign / Illustrator | Creative Suite ExtendScript 路线 | 只作跨软件桥接对照 |
| [Automaat/lightroom-mcp](https://github.com/Automaat/lightroom-mcp) | Lightroom Classic | Lightroom Classic 本地桥 | 未来只做照片 catalog metadata 摘要 |
| [noopz/lightroom_mcp](https://github.com/noopz/lightroom_mcp) | Lightroom Classic | Lightroom MCP 对照实现 | 记录目录和 catalog 风险 |
| [yjx-184/Lightroom_mcp](https://github.com/yjx-184/Lightroom_mcp) | Lightroom / Codex | 仓库描述含 Lightroom Codex Bridge | 参考 Codex 入口说明 |
| [krishnapallapolu/adobe-firefly-mcp](https://github.com/krishnapallapolu/adobe-firefly-mcp) | Adobe Firefly | Firefly API MCP 方向 | 只记录云 API 风险，不接 token |
| [nolandubeau/adobe-firefly-mcp-hub](https://github.com/nolandubeau/adobe-firefly-mcp-hub) | Adobe Firefly Services | 统一 Firefly Services API MCP | 只研究 schema，不真实调用 |

## 结论

Adobe 接入不是单一工具问题，而是三类桥接方式并存：

| 路线 | 典型项目 | 可吸收内容 | 暂不吸收内容 |
| --- | --- | --- | --- |
| 桌面脚本桥 | Illustrator、Premiere、After Effects、InDesign MCP 项目 | 工具分组、参数 schema、只读摘要、导出 preflight | 任意 JSX / ExtendScript 执行入口 |
| Windows COM / 本机对象桥 | Photoshop COM、Illustrator COM 项目 | session/document/layer 只读边界、结构化 error、soft-exit | 打开私有 PSD/AI 或批量改真实工程 |
| 插件 / 本地代理桥 | Photoshop UXP、CEP、Generator 项目 | Node Proxy、UXP/CEP 与 MCP server 分层 | 自动安装插件、写用户目录、保存 token |

StarBridge 应继续保持当前策略：先稳定 `status`、`document_info`、`preflight`、`dry-run plan` 和 sandbox demo，再把写入类能力放到显式确认、输出目录约束、路径脱敏和 evidence manifest 后面。

## 安全准入规则

新增 Adobe 类 MCP tool 前必须满足：

1. 先补中文文档、tool schema 和测试。
2. 默认只读、dry-run，或只写入忽略目录。
3. 输入路径必须由用户显式传入，不写个人桌面、安装目录或源图默认值。
4. 输出只允许进入 `examples/output/...` 或本机忽略目录，真实写入必须显式确认。
5. 返回结果必须路径脱敏，不输出用户名、安装路径、素材路径、账号状态、Creative Cloud 缓存或许可证信息。
6. CI 只验证 schema、dry-run、safe-only registry 和安全扫描，不启动真实 Adobe 桌面软件。
7. 不接入任意脚本执行工具；只能接入白名单动作和可审计参数。

## 暂不进入公开仓库

- 第三方源码、插件包、全局安装脚本和用户目录写入逻辑。
- 真实 PSD、AI、AEP、PRPROJ、INDD、Lightroom catalog、照片库、客户素材、商业字体和导出结果。
- Firefly、Adobe Cloud、Adobe Express 等需要账号、token、订阅或云 API 的真实调用。
- 自动登录、许可证绕过、付费能力绕过、批量下载和上传。
