# 矢量短华语指令协议

## 目标

用户用简短华语描述矢量任务，StarBridge 将其编译为严格 `VectorTask`，再生成 `VectorSceneGraph`。短令只描述目标和约束，不直接包含文件路径、脚本或桌面软件命令。

标准形式：

```text
任务｜模式｜结构｜样式｜约束｜验收｜输出
```

示例：

```text
照图重绘｜语义重建｜分层+少节点+文字可编｜限5色+无渐变｜轮廓负形必准｜五维90分+修2轮｜SVG+PDF
```

## 公开词汇

| 短令 | 结构化含义 |
| --- | --- |
| `照图重绘` | `task=reference_vector_rebuild` |
| `图标重绘` | `task=icon_rebuild` |
| `线稿转矢量` | `task=line_art_vectorization` |
| `剪影重建` | `task=silhouette_rebuild` |
| `语义重建` | `strategy=semantic_reconstruction` |
| `轮廓重建` | `strategy=contour_reconstruction` |
| `几何重建` | `strategy=geometric_reconstruction` |
| `分层` | `semantic_layers=true` |
| `少节点` | `anchor_policy=minimal` |
| `文字可编` | `live_text=true` |
| `组件复用` | `reuse_symbols=true` |
| `不用描摹` | `image_trace=false` |
| `允许描摹` | `image_trace=true`，只能作中间步骤 |
| `限5色` | `max_colors=5` |
| `无渐变` | `gradient_allowed=false` |
| `保留渐变` | `gradient_allowed=true` |
| `轮廓优先` | 质量优先级从 silhouette 开始 |
| `负形必准` | `negative_space` 作为 hard gate |
| `五维90分` | 总分阈值 `90` |
| `修2轮` | 最多两轮局部修复 |
| `只修差异` | `patch_mode=diff_only` |
| `SVG+PDF` | `exports=[svg,pdf]` |

`3色`、`8色`、`修1轮`、`修3轮`、`五维95分` 等数字参数通过受限正则提取，不执行其中任何代码。

## 默认策略

只输入 `照图重绘` 时，系统默认：

- 语义重建，不使用 Image Trace。
- 语义分层、少节点、文字可编、symbol 复用。
- 优先轮廓、比例、负形、拓扑，再处理视觉细节。
- 总分不低于 `90`，单维不低于 `75`。
- 最多两轮 `diff_only` 修复。
- 默认只计划，不写入文件。
- 默认交付格式为 SVG。

## 冲突处理

以下组合必须返回结构化错误，不自行选择：

- `不用描摹` + `允许描摹`
- `文字可编` + `文字转曲`
- `无渐变` + `保留渐变`
- `保持原色` + `品牌色优先`
- `只预览` + `确认执行`

未识别的短语保留在 `unrecognized_terms`，不猜测其为高风险写入指令。

## 协议链

```text
short Chinese command
  -> VectorTask
  -> CreativeTransaction
  -> VectorSceneGraph
  -> schema validation
  -> in-memory SVG compile
  -> sandbox preview after explicit confirmation
  -> five-dimension quality report
  -> VectorPatch
```

`VectorPatch` 只能引用 Scene Graph 中的 object id，不得携带文件路径或任意脚本。
