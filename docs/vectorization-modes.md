# 五模式图片矢量化

> Artisan 的最终渲染自适应少锚点阶段、三种兼容质量预设、缓存和回退语义见 [最少锚点、高相似度的自适应矢量优化](adaptive-vector-optimization.md)。`editable-99` 使用独立的五项硬门槛与颜色候选搜索；Exact、Smart、Lightweight 不进入 Artisan 阶段。

KORYAO 使用一个统一入口提供五种矢量化模式。原有智能、轻量、精确和匠心完整保留；`editable-99` 是独立的“质量约束下复杂度最小化”模式，不是旧模式改名。所有模式都只读取用户明确传入的一张 PNG/JPEG，并输出不含嵌入位图、脚本和外链的 SVG。

普通客户工作流不直接按单一模式起步，而是固定两阶段：先使用 `exact` 完成像素级打印 / 精确重建并验证基线，再按客户目标使用 `artisan` 或客户明确选择的 `smart` / `lightweight` 绘制矢量。两个阶段都禁止使用 Illustrator Image Trace；精确重建超限时停止，不自动描摹。

## 模式

| 模式 | 默认参数重点 | 适用场景 | 是否逐像素一致 |
| --- | --- | --- | --- |
| `artisan` 匠心矢量 | 16 色、自适应锚点、设计分层；细线稿可切换为中心线、续接交叉点并按几何意图分级 | 艺术稿、品牌图形、传统纹样、高级设计交付 | 否；受轮廓、面积、中心线、续接与意图分级质量门槛约束 |
| `smart` 智能矢量 | 24 色、4 级透明度、适度清理和节点简化 | 插画、海报素材、普通设计再编辑 | 否 |
| `lightweight` 轻量矢量 | 8 色、2 级透明度、更强碎片清理和简化 | Logo、图标、纹样、流畅编辑 | 否 |
| `exact` 精确重建 | 不缩放、不减色；同色扫描段横向与纵向合并 | 技术证明、RGBA 像素验证、存档 | 是 |
| `editable-99` 99% 可编辑 | Exact RGBA 可复核基线；256→32 色候选；误差热力图与局部恢复；复杂度保护 | 需要严格视觉门槛且要继续编辑的交付 | 不是逐像素要求；必须同时通过五项 99% 质量门槛 |

`balanced` 作为兼容别名会映射到 `smart`。

## 智能曲线精修 Skill

当智能或匠心结果出现白缝、轮廓破碎、锚点爆炸，或最终渲染与原图结构差异超过 30% 时，使用 `.codex/skills/starbridge-smart-vector-refinement/` 做候选精修。该 Skill 保留原模式和旧产物，通过可选的 VTracer stacked-spline 后端生成规范化曲线候选，再用仓库 SVG verifier 检查纯路径结构。

质量评分必须比较原图与**最终 SVG 的实际渲染图**。`preview.png` 可以作为本地量化中间件或候选输入，但不能冒充最终 SVG 的相似度证据。默认硬门槛为结构差异不高于 30%、归一化 MAE 不高于 0.12、子路径不超过 12,000、锚点不超过 120,000，并要求曲线候选至少包含一个三次贝塞尔段。完整流程和调参顺序见 [智能曲线精修 Skill](../.codex/skills/starbridge-smart-vector-refinement/SKILL.md)。

## 安装和运行

```powershell
python -m pip install -e ".[vectorization]"

# 碎片/差异修复的可选曲线后端
python -m pip install -e ".[vector-refinement]"

# 客户第一阶段：像素级打印 / 精确重建
python -m starbridge_mcp.vectorization.cli --input "<input.png>" --mode exact --reference-id "sample"

# 客户第二阶段：绘制型匠心矢量
python -m starbridge_mcp.vectorization.cli --input "<input.png>" --mode artisan --reference-id "sample"

# 客户明确要求五项 99% 质量门槛
python -m starbridge_mcp.vectorization.cli --input "<input.png>" --mode editable-99 --quality-preset editable-99 --target-difference 1.0 --reference-id "sample"

# 兼容旧入口：裸调用仍映射 smart；客户工作流不要裸调用
python -m starbridge_mcp.vectorization.cli --input "<input.png>" --reference-id "sample"

# 轻量矢量
python -m starbridge_mcp.vectorization.cli --input "<input.png>" --mode lightweight --reference-id "sample"

```

代理或自动化调用可增加 `--compact`，终端只返回关键指标、输出路径、`edit_ref` 和意图选择器；完整报告照常保存到输出目录，减少重复上下文和 token。

也可以使用：

```powershell
npm.cmd run illustrator:vectorize -- --input "<input.png>" --mode smart --reference-id "sample"
```

## 桌面软件原型

安装 GUI 可选依赖并启动：

```powershell
python -m pip install -e ".[vector-app]"
vectorflow-studio

# 或
npm.cmd run vector-app:start
```

当前桌面原型提供：

- PNG/JPEG 文件选择与拖放；
- 匠心、智能、轻量、精确、99% 可编辑五种模式卡片；
- 颜色、最大尺寸、路径平滑、碎片清理和透明阈值；
- 后台工作线程，转换时界面保持响应；
- 原图与处理预览并排查看；
- 颜色、子路径、节点、SVG 大小、耗时、精确像素验证和匠心锚点减少指标；
- 打开本地输出目录。

GUI 不会上传素材，也不会自动启动 Illustrator。`.ai` 保存仍然是用户明确请求后执行的可选桌面交付阶段。

## 可调参数

```text
--max-colors
--max-dimension
--simplify-ratio
--min-region-area
--alpha-threshold
--max-subpaths
--max-points
--max-svg-size-mb
```

没有显式传入的参数由模式预设提供。安全上限被超过时，流程在发布目标文件前停止，不会自动回退到 Illustrator Image Trace。

## 输出

默认输出到被 Git 忽略的：

```text
examples/output/vectorization/<reference-id>/<mode>/
  vector.svg
  preview.png
  parameters.json
  vector_report.json
  vector_report.md
  editable_99.json       # 仅 editable-99
  error_heatmap.png      # 仅 editable-99
  svg_render.png         # 最终 SVG 渲染证据
  artisan_structure.json  # 仅匠心模式
  artisan_edit_index.json # 仅匠心模式，代理优先读取
```

报告包含源文件 SHA-256、原始/输出尺寸、颜色、复合路径、子路径、节点、SVG 字节数、运行参数、安全验证和耗时。报告不记录源文件名或绝对路径。

`editable_99.json` 额外保存颜色日程、每个候选的五项指标、子路径、节点、SVG 大小、耗时、淘汰原因、局部恢复区域和前后变化、最终状态及 Illustrator 风险策略。硬门槛为：

- `SSIM ≥ 0.990`
- `difference_percent ≤ 1.0`
- `normalized_mae ≤ 0.010`
- `edge_dice ≥ 0.980`
- `alpha_mae ≤ 0.005`

指标范围固定如下：SSIM、normalized MAE、edge Dice、alpha MAE 均使用 `[0, 1]`；`difference_percent = max(0, (1 - SSIM) × 100)`。RGB 指标在白底合成后的 8-bit RGB 上计算，normalized MAE 为平均绝对通道误差除以 255；alpha MAE 为 8-bit alpha 平均绝对误差除以 255；edge Dice 使用同一 Canny 与 3×3 邻域容差。候选、局部恢复和最终结果使用同一计算函数。

通过候选按 `subpaths → points → colors → SVG bytes → elapsed` 选择。`subpaths ≤ 30,000` 且 `points ≤ 120,000` 才允许默认自动打开；超过 60,000 子路径或 240,000 节点默认禁止自动打开，超过 300,000 子路径只存档。阈值属于 CreNexus 工程保护，不是 Adobe 官方上限。

匠心完整结构文件额外记录基础、主体、细节、点睛图层，稳定的 `shape-*` / `layer-*` ID、父子层级、颜色、边界框和锚点指标。第 5 轮再按局部几何分成 `flow-contour`、`ornament`、`detail` 和 `micro-detail`；这些是曲线意图，不是人物、文字或物体内容识别。

`artisan_edit_index.json` schema v2 使用紧凑数组保存选择器、形状 ID、设计师可读名称、边界框、锚点和子路径，并用 `svg_sha256` 绑定基础 SVG。后续代理优先读取它，可只检查一个局部范围：

```powershell
python -m starbridge_mcp.vectorization.artisan_edit `
  --index "<output>/artisan_edit_index.json" `
  --selector intent:ornament
```

返回值只包含 `edit_ref`、匹配对象数、合并边界框、局部锚点、设计师名称和最多 24 个形状 ID，不包含源文件名或绝对路径。Iteration 6 可把三个客户答案编译为短 `profile_ref`，随后用 `artisan_refine` 对选中描边执行矢量到矢量局部精修；Iteration 7 再用 `artisan_paint` 安全合并非重叠叶子块面；Iteration 8 用 `artisan_direction` 编译客户明确给出的颜色组和设计命名。操作会生成短引用和父补丁链，完整结构、预校准和局部处理都在本地执行，`external_ai_calls` 为 `0`。

```powershell
python -m starbridge_mcp.vectorization.artisan_paint `
  --svg "<output>/vector.svg" `
  --index "<output>/artisan_edit_index.json" `
  --profile "artisan_style_profile.json" `
  --selector intent:paint-region `
  --output-dir "<new-output>"
```

`preserve-palette` 只允许完全同色块面合并；`reduce-near-colors` 额外启用 Delta-E 近色门；`monochrome` 必须由客户明确选择；`manual-groups` 必须再提供经过编译的人工指令，不提供时安全拒绝。块面合并只接受同角色、同深度、同父对象、无子对象、边界框互不重叠的对象，并保持源子路径和锚点不变。

人工指令源文件只包含短引用和数组映射：

```json
{
  "base_edit_ref": "edit:0123456789ab",
  "profile_ref": "style:abcdef012345",
  "palette_groups": [["#b94f42", ["#b94f42", "#ba5043"]]],
  "object_names": [["shape-0004", "朱红装饰"]],
  "layer_names": [["subject", "主体色块"]]
}
```

```powershell
python -m starbridge_mcp.vectorization.artisan_direction `
  --spec "artisan_direction_spec.json" `
  --output "artisan_direction.json"

python -m starbridge_mcp.vectorization.artisan_paint `
  --svg "<output>/vector.svg" `
  --index "<output>/artisan_edit_index.json" `
  --profile "artisan_style_profile.json" `
  --direction "artisan_direction.json" `
  --selector intent:paint-region `
  --output-dir "<new-output>"
```

输出额外包含 `artisan_illustrator_map.json`。它绑定输出 SVG 哈希、`edit_ref` 与 `direction_ref`，仅描述客户指定的设计层和对象名称；真正写入 Illustrator 仍需明确确认。

Iteration 9 使用经过验证的 map 生成确认式桌面应用计划。先读取脱敏状态 revision，再审查不足 1 KB 的计划和 `approval_ref`：

```powershell
python -m starbridge_mcp.vectorization.artisan_illustrator probe --soft-exit

python -m starbridge_mcp.vectorization.artisan_illustrator plan `
  --svg "<output>/vector.svg" `
  --index "<output>/artisan_edit_index.json" `
  --direction "artisan_direction.json" `
  --map "<output>/artisan_illustrator_map.json" `
  --state-revision 7 `
  --output "artisan_apply_plan.json"

python -m starbridge_mcp.vectorization.artisan_illustrator execute `
  --plan "artisan_apply_plan.json" `
  --map "<output>/artisan_illustrator_map.json" `
  --approval-ref "approve:0123456789ab" `
  --confirm-write `
  --receipt "artisan_apply_receipt.json" `
  --soft-exit
```

`approval_ref` 必须使用实际计划返回值，示例值不能执行。代理只监听 loopback；应用前再次核对状态 revision。主机端解析完全部目标后才写入，随后回读匹配数量并提交事务；回读或提交失败自动回滚。代理未启动、没有活动文档或状态过期时返回脱敏 `not_available`，不阻塞 Ubuntu CI。

精确模式额外报告：

```text
pixel_match
different_pixel_count
maximum_channel_difference
```

正式验收要求分别为 `true`、`0`、`0`。

## 产品边界

- 智能和轻量模式是可编辑近似结果，会主动减色、清理小区域并简化轮廓。
- 匠心模式额外使用曲线拟合、设计角色层级和线稿自适应。细线稿中心线、交叉点续接和几何意图候选分别通过独立质量门；意图候选必须再减少至少 3% 子路径、锚点和总点数，编辑批次不增加，精确率/Dice 下降不超过 0.6 个百分点、召回率下降不超过 1 个百分点。失败时依次保留第 4 轮续接中心线、第 3 轮中心线或第 2 轮轮廓填充。当前角色来自本地几何推断，不宣称已经识别人脸、文字或具体物体语义。
- 精确模式保留源像素网格，但大量矩形不等同于轻量商业矢量插画。
- `editable-99` 只在五项指标全部通过后宣称质量通过；`high-fidelity`、smart、artisan、lightweight 不能改名冒充 99%。
- 当前统一核心负责 SVG、预览、参数和报告；Illustrator `.ai` 保存仍是可选桌面交付步骤，需要用户明确请求。
- 源图和生成结果只留在本地忽略目录，不能提交到公开仓库。
