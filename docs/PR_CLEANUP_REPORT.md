# KORYAO Pull Request 清理报告

更新时间：2026-07-23

## 结论

- GitHub 仓库已更名为 `jianbaorui07-dot/KORYAO-basic`。
- 审计时 Open Pull Request 数量为 `0`。
- 对话中提到的 PR #1—#8 已全部有明确结论：6 个已合并，2 个已关闭。
- PR #1 的 Illustrator 公共桥能力已由后续 Adobe/Illustrator PR 覆盖。
- PR #7 的发布边界、DXF 安全门、状态分类和测试要求已由后续主线实现覆盖。
- 最新 `main` 没有待解决的 PR 合并冲突；本轮仍发现并修复了格式基线和仓库更名后的 Rust updater 断言漂移。
- 本报告不把模型权重、客户素材、本机路径、PSD、AI、DWG、Blend 或授权密钥带入公开仓库。

## PR #1—#8 处置

| PR | 标题 | 最终状态 | 处理结论 |
| --- | --- | --- | --- |
| #1 | `[codex] add Illustrator bridge` | Closed，未合并 | 原 PR 因当时改为直接更新 `main` 而关闭。当前主线已包含 Illustrator 文档、只读/受控桥、UXP、Node proxy、MCP 能力与测试；由后续 PR #4 及其后的 Illustrator 工作替代。 |
| #2 | `Add StarBridge preflight and bridge capability matrix` | Merged | 已进入主线；安全扫描、preflight 和 capability matrix 继续由测试覆盖。 |
| #3 | `[codex] add Photoshop four-up hex poster experiment` | Merged | 已进入主线；公开实验与私有输出隔离规则保留。 |
| #4 | `Add Adobe sandbox demo bridges` | Merged | 已进入主线；同时覆盖 PR #1 中仍有价值的公共 Adobe/Illustrator 桥方向。 |
| #5 | `Polish release docs and Adobe demo evidence` | Merged | 已进入主线；未把未运行的真实 Adobe 软件写成已验证。 |
| #6 | `Add Computer Use planning layer` | Merged | 已进入主线；安全计划、GUI 指令和确认门继续由测试覆盖。 |
| #7 | `[codex] Prepare v0.1-alpha release prototype` | Closed，未合并 | 不再复活旧分支。当前主线已具备发布边界文档、optional dependencies、DXF dry-run/确认门、结构化 unavailable 状态和对应回归测试；旧实现已被后续主线替代。 |
| #8 | `[codex] StarBridge maintenance closeout` | Merged | 已进入主线；维护记录保留为历史证据。 |

## 当前主线审计

审计基线：

- 仓库：`jianbaorui07-dot/KORYAO-basic`
- 默认分支：`main`
- 审计起点：`8c87a38`（`feat: add editable-99 verified vectorization`）
- Open PR：`0`
- 本地开发分支：`codex/pr-cleanup`

发现的问题：

1. Ruff format 检查报告 5 个 Python 文件未格式化。
2. `cargo fmt --check` 报告 `adobe_export.rs` 有 1 处格式漂移。
3. 按 CI 准备 Tauri sidecar 占位资源后，Rust 单元测试发现 updater 测试仍断言旧仓库路径 `KORYAO`，而实际固定更新地址和产品文档已经使用 `KORYAO-basic`。

本轮修复：

- 对上述 Python 和 Rust 文件应用标准格式化。
- 将 updater 单元测试的固定仓库断言统一为 `KORYAO-basic`。
- 未修改 updater 的生产地址、验签要求或安全行为。

## 验证结果

以下验证在 Windows、本地隔离 `.venv` 和最新主线基线上执行：

| 验证 | 结果 |
| --- | --- |
| `python scripts/security_check.py` | Passed |
| `python scripts/check_product_facts.py` | Passed |
| `python scripts/check_text_encoding.py` | Passed |
| `python scripts/collect_bridge_status.py --json` | Passed；只输出公开安全的桥状态 |
| `python -m unittest discover -s tests` | Passed；870 tests，32 skipped |
| `python -m ruff check .` | Passed |
| `python -m ruff format --check .` | Passed；308 files formatted |
| `npm.cmd test --prefix apps\starbridge-desktop` | Passed；8 Vitest files / 35 tests，Tauri config 8 tests |
| `npm.cmd run build --prefix apps\starbridge-desktop` | Passed |
| `cargo fmt --manifest-path apps/starbridge-desktop/src-tauri/Cargo.toml --all -- --check` | Passed |
| `cargo test --manifest-path apps/starbridge-desktop/src-tauri/Cargo.toml` | Passed；27 tests |

桌面软件说明：

- AutoCAD、Photoshop、Illustrator、ComfyUI 和 Blender 的真实 GUI/E2E 运行不属于本轮 PR 清理的阻塞条件。
- 未启动或未授权的本地软件只能记录为 unavailable / 未运行，不能声称已验证。

## 后续门槛

本清理 PR 合并且最新 `main` 完整复验通过后：

1. 创建 `koryao-pr-cleanup-complete` 标签。
2. 冻结 `koryao-pre-model-v1` 基线标签。
3. 从该基线创建 `codex/model-contract`。
4. 才开始模型公共协议、私有运行端和私有数据治理工作。
