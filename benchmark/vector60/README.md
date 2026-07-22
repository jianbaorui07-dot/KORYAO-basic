# Vector60 基准汇总

这里仅保存 Vector60 的**脱敏汇总框架**。脚本不读取图片、SVG、渲染结果或软件账号状态，也不证明当前实现已经通过 Vector60。

## 输入约束

`aggregate.py` 只接受 `vector60-summary-v1` JSON。必须恰好包含以下四类、每类 10 个匿名案例：

- `logo_or_icon-01` 至 `logo_or_icon-10`
- `lineart-01` 至 `lineart-10`
- `flat-01` 至 `flat-10`
- `illustration-01` 至 `illustration-10`

每个案例只允许 `case_id`、`category`、`status` 和 `metrics` 白名单字段。不得加入文件名、路径、素材内容、Token、Cookie、账号状态或其他元数据；任何额外字段都会让输入整体拒绝。案例 `status` 只能是 `passed`、`failed`、`skipped` 或 `unverified`。

指标字段为：

- `edge_dice` 与 `artisan_baseline_edge_dice`，范围 `[0, 1]`；
- `normalized_mae`，范围 `[0, 1]`；
- `seam_free_4x`，仅接受布尔值；
- `anchor_count` 与 `artisan_baseline_anchor_count`，仅接受非负整数；
- `safe_svg.no_bitmap`、`no_script`、`no_external_links`，仅接受布尔值。

根对象还可包含 Exact 三值验证和全量测试状态：

```json
{
  "schema_version": "vector60-summary-v1",
  "cases": [],
  "exact_validation": {
    "pixel_match": true,
    "different_pixel_count": 0,
    "maximum_channel_difference": 0
  },
  "test_suites": {
    "python": "passed",
    "frontend": "passed",
    "rust": "passed"
  }
}
```

上例省略了必需的 40 个案例，因此本身不能运行。不要把真实素材或临时渲染补进本目录。

## 计算口径

- 成功数必须达到 `38/40`；只有案例状态 `passed` 计为成功。
- Edge Dice 和 normalized MAE 中位数必须拥有全部 40 张正式 SVG 原分辨率渲染证据；缺一项即为 `unverified`。
- 4 倍白缝检查必须拥有全部 40 张证据，至少 32 张为 `true`。
- 锚点门优先检查结果中位数是否比 Artisan 基线减少至少 25%。备用规则要求锚点中位数不增加超过 10%，且 40 组结果/基线 Edge Dice 的单侧符号检验 `p < 0.05`、配对差值中位数大于 0。
- 所有 40 张正式 SVG 都必须明确通过无位图、无脚本、无外链验证。
- Exact 必须精确保持 `pixel_match=true`、`different_pixel_count=0`、`maximum_channel_difference=0`。
- Python、前端与 Rust 全量测试必须全部为 `passed`。`skipped` 和 `unverified` 不会被视为通过。

已知失败证据使硬门为 `failed`；证据缺失使硬门为 `unverified`。只有全部硬门为 `passed` 时，总状态才为 `passed`。

## 运行

输出到标准输出，脚本不会回显输入文件路径：

```powershell
python -m benchmark.vector60.aggregate --input <脱敏摘要.json> --format json
python -m benchmark.vector60.aggregate --input <脱敏摘要.json> --format markdown
```

生成的 Markdown 只预留 `comparisons/<类别>/<匿名案例>.png` 相对引用，且默认标为 `unverified`。只有脱敏前后对比图真实生成并复核后，才可在交付记录中更新其状态。
