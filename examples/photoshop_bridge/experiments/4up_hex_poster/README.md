# Photoshop 四联科技六边形海报实验

这个目录保存一次可公开复现的 Photoshop COM + ExtendScript 自动化实验：从零新建 8360px × 2820px、300DPI、sRGB 的四联竖向科技六边形海报，并通过可编辑图层组、智能对象模板、参考线、蒙版、调色层和导出步骤完成本地闭环。

仓库只提交参数化脚本、模板和验证摘要，不提交 PSD、高清 PNG、JPG 导出图或任何本机路径。运行脚本时，所有生成物会写到当前实验目录，且已经由本目录 `.gitignore` 忽略。

## 内容

| 文件 | 用途 |
| --- | --- |
| `generate_4up_hex_photoshop_poster.py` | 生成 Photoshop JSX、SVG 智能对象模板和布局 manifest |
| `run_4up_hex_poster.ps1` | 本机运行入口，可只生成 JSX，也可调用 Photoshop COM 完整执行 |
| `templates/*.svg` | 六边形智能对象模板的公开 SVG 版本 |
| `sample_verification_report.json` | 本轮本地实验的尺寸、数量、Alpha 和 SHA256 摘要 |

## 本机运行

先确认 Windows 上已授权 Photoshop，并且 COM 类型 `Photoshop.Application` 可用。建议先手动打开 Photoshop。

只生成 JSX、模板和 manifest：

```powershell
powershell -ExecutionPolicy Bypass -File examples\photoshop_bridge\experiments\4up_hex_poster\run_4up_hex_poster.ps1 -GenerateOnly
```

完整执行 Photoshop 自动化：

```powershell
powershell -ExecutionPolicy Bypass -File examples\photoshop_bridge\experiments\4up_hex_poster\run_4up_hex_poster.ps1
```

脚本会在实验目录内生成：

| 文件名 | 说明 |
| --- | --- |
| `4联科技六边形几何海报_高级分层源文件.psd` | 分层 PSD 源文件 |
| `4联科技六边形几何海报_白底高清.png` | 白底高清 PNG |
| `4联科技六边形几何海报_透明底高清.png` | 透明底高清 PNG |
| `4联科技六边形几何海报_预览.jpg` | 快速预览 JPG |
| `photoshop_4up_hex_automation/` | 运行时 JSX、模板、manifest 和日志 |

## 本轮验证摘要

- Photoshop：27.1.0
- 画布：8360px × 2820px
- 分辨率：300DPI
- 子海报：4 张，每张 1920px × 2500px
- 六边形智能对象实例：392 个
- 白底 PNG：RGB，8360px × 2820px
- 透明 PNG：RGBA，8360px × 2820px，Alpha 范围 0 到 255
- 预览 JPG：RGB，8360px × 2820px

PSD 和高清 PNG 属于本机生成物，不进入 GitHub。需要核对本轮真实产物时，查看 `sample_verification_report.json` 中的文件大小和 SHA256。

## 安全边界

- 不提交本机绝对路径、桌面路径、源素材路径或输出目录。
- 不提交 PSD、PNG、JPG、商业字体、笔刷、购买素材或客户素材。
- 不把生成后的 JSX 作为固定源文件提交，因为 JSX 内会包含运行时输出路径。
- 公开仓库只保存可复跑的参数化脚本、模板和验证摘要。
