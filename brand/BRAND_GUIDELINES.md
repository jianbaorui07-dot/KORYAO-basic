# 创枢 CreNexus 品牌指南

## 品牌核心

- 中文名称：**创枢**
- 英文名称：**CreNexus**
- 标准组合：**创枢 CreNexus**
- 产品描述：**AI 创意软件协同平台**
- 品牌承诺：让创意工具在用户自己的电脑上安全协同，用户文件不上传到 CreNexus 服务器。

禁止使用“AI 万能创作平台”“一键控制所有软件”“全自动替代设计师”“无限智能”等夸大表述。

## 正式资产

`assets/crenexus-software-icon.png` 是软件图标的唯一正式源文件，来自用户提供的 1024×1024 原图。构建流程只执行等比缩放和格式转换，不重绘、不补字、不生成新画面。

该图用于：

- Windows 可执行文件、安装器、任务栏和桌面快捷方式；
- 桌面软件左上角品牌图标；
- GitHub README 的主视觉图标。

`assets/creative-codex-web-brand.png` 只作为网页视觉风格参考。网页构建脚本从其中截取真实的 C/code 图形，与可访问、可缩放的原生文字“创枢 CreNexus”组合；旧的 CreativeCodeX 字样不会出现在网页成品中。

## 兼容资产

下列小写 `starbridge` 路径和标识暂时保留，以免破坏已有 MCP、Skill、环境变量、升级链路和用户数据：

- `starbridge-symbol.svg` 及历史 SVG 导出；
- `starbridge_mcp`、`STARBRIDGE_*` 与现有脚本文件名；
- `io.starbridge.desktop` Windows 应用标识。

这些兼容标识不是对外品牌名。界面、文档、安装包标题和 GitHub 项目统一显示 CreNexus。

## 颜色与使用

- 软件图标保留原图的深海军蓝圆角底、蓝紫渐变 C/无限轨迹、钢笔和画笔造型。
- 不裁掉圆角外框，不改变图形比例，不为小尺寸版本添加文字。
- 网页字标使用蓝、紫、青渐变，与真实图标的色彩保持一致。
- 中文界面使用 `Microsoft YaHei UI`、`PingFang SC` 回退；英文字标使用 Windows 系统字体栈。

## 构建

```powershell
npm.cmd run brand:build
```

构建不访问网络，输出 16、24、32、48、64、128、256、512 px PNG、多尺寸 Windows ICO、favicon、Tauri 应用图标和网页图形。`exports/`、桌面 `src/assets/` 与 Tauri `icons/` 中的适配文件均由脚本生成，不手工修改。
