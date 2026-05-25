# Git 分支工作流

## 分支类型

| 类型 | 用途 |
| --- | --- |
| `codex/*` | Codex 产生的功能或修复分支。 |
| `continue/*` | 接手已有工作的连续分支。 |
| `integration/*` | 多个已验证分支的集成分支。 |
| `audit/*` | 发布审计、安全检查和 release-readiness 分支。 |

## 合并原则

- integration 分支只合并明确目标分支。
- 不把 CAD/DXF、release-readiness、新 bridge 开发混在同一个提交里。
- 合并冲突优先保留当前已验证的 bridge 代码和测试。
- 发布审计分支只改 `.github/`、`SECURITY.md`、`CONTRIBUTING.md`、`docs/` 和安全检查脚本。
- 不恢复不明 stash，不使用 broad staging。

## 推荐验证

```powershell
git status
python -m unittest discover -s tests
python -m starbridge_mcp.server --json
powershell -ExecutionPolicy Bypass -File scripts\check_release_ready.ps1
```
