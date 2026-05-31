# Computer Use vs MCP

Codex 接入本机创意软件时有三条常见通道：GUI Computer Use、CLI / PowerShell、MCP stdio tools。它们不是互相替代，而是用于不同风险和稳定性层级。

## 三种方式对比

| 方式 | 最适合 | 优点 | 风险 | 本仓库定位 |
| --- | --- | --- | --- | --- |
| GUI Computer Use | 观察真实桌面、点击复现、截图验证、处理弱 API 软件 | 能看见用户看到的界面；适合菜单、弹窗、画布、时间线和授权提示排查 | 依赖窗口状态；不适合长期批处理；误点可能造成副作用 | 作为 GUI evidence 和问题复现通道 |
| CLI / PowerShell | 本机脚本、测试、preflight、probe、文件格式校验 | 可重复、易记录、适合 CI；比 GUI 更稳定 | 平台依赖明显；脚本如果不收敛参数可能泄露路径或误写文件 | 作为开发和验证入口 |
| MCP stdio tools | Codex / Cursor / Claude Code 可调用的结构化工具 | 参数化、可测试、可声明风险等级；适合稳定生产动作 | 需要先设计 schema、安全边界和错误格式 | 作为 StarBridge 的核心生产通道 |

## 分工原则

GUI 适合观察和交互：确认软件是否打开、按钮是否存在、菜单路径是否变化、画布或时间线是否出现预期状态、错误弹窗写了什么。

MCP 适合稳定执行和验证：读取状态、校验 workflow、生成 CAD plan、输出脱敏 JSON、执行 dry-run、把可确认的写入动作限制在参数和目录边界内。

CLI / PowerShell 适合仓库维护：跑测试、做安全扫描、执行发布前体检、生成本地报告和验证脚本行为。

## 推荐决策树

```text
要做的事是否需要看真实桌面窗口？
  是 -> 先用 Computer Use 做 L0 观察或低风险复现。
       能否整理成参数化、可重复的动作？
         能 -> 迁移到 MCP tool 或 CLI 脚本，再用测试验证。
         不能 -> 只保留为 GUI 复现说明和脱敏截图证据。
  否 -> 是否已有 MCP tool？
       有 -> 用 MCP tool，记录输入、输出和风险等级。
       没有 -> 是否是仓库维护或本机验证？
            是 -> 用 CLI / PowerShell，并补测试或 preflight。
            否 -> 先写工具 schema 和安全边界，不直接做生产写入。
```

## 推荐选择

| 任务 | 首选通道 | 说明 |
| --- | --- | --- |
| 查看 Photoshop 图层面板是否卡住 | GUI Computer Use | 需要看真实窗口和弹窗 |
| 读取当前 Photoshop 文档尺寸摘要 | MCP stdio tools | 结果应结构化、脱敏、可测试 |
| 校验 ComfyUI workflow JSON | MCP stdio tools | 不需要 GUI，应该可 CI 复现 |
| 查看 ComfyUI 节点图为什么红了 | GUI Computer Use | GUI 错误和节点状态更直观 |
| 生成离线 DXF plan | MCP stdio tools | 参数化、dry-run、可审查 |
| 跑发布前检查 | CLI / PowerShell | `npm.cmd run preflight` 更稳定 |
| 记录视觉证据 | GUI Computer Use + Safety layer | 截图描述必须脱敏，不提交私有素材 |

## 不建议的选择

- 不用 GUI 点击来替代已经存在的 MCP 工具。
- 不把一次成功点击当作可复现生产流程。
- 不在 README、docs、workflow 或脚本默认值里写真实本机路径。
- 不把客户素材、模型路径、账号状态、授权信息或导出结果作为公开证据。
- 不为绕过登录、验证码、支付、系统安全设置或软件授权检查设计工具。
