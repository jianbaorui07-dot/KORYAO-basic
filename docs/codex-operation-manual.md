# Codex 操作手册

本手册记录 Codex 在 StarBridge 仓库中的最小安全操作方式。

## 开始前

```powershell
git fetch origin
git status
git branch --show-current
git log --oneline -5
```

如果工作区不干净，先确认变更是否属于当前任务。不要恢复不明 stash，不要删除本机文件。

## 发布审计任务

允许修改：

- `.github/`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/`
- `scripts/check_repository_safety.ps1`
- `scripts/check_release_ready.ps1`
- `scripts/check_forbidden_files.ps1`

禁止混入：

- CAD/DXF MVP 文件。
- 真实素材、模型、视频、PSD、AI、DWG、DXF。
- `.env`、token、账号、API key。
- 本机绝对路径、真实草稿目录或导出路径。

## 验证

```powershell
python -m unittest discover -s tests
python -m starbridge_mcp.server --json
python examples\bridge_status.py --json
python examples\comfyui\dry_run_queue.py
python examples\jianying\generate_draft_plan.py
powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1
```

`--strict` 在未配置本机软件时可以失败，但普通 `--json` 必须成功。
