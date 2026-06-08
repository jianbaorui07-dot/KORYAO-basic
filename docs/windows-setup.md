# Windows Setup

这份文档记录第二台 Windows 机器把 StarBridge 仓库跑通的最小配置过程，只覆盖当前仓库实际验证过的环境修复、依赖安装和检查命令。

## 1. 先确认仓库根目录

当前工作目录应为你的 StarBridge 仓库根目录，例如：

```powershell
<repo-root>
```

如果你是从另一个本地镜像复制过来的仓库，先把这个目录加入 Git 安全目录：

```powershell
git config --global --add safe.directory <repo-root>
```

验证：

```powershell
git status -sb
```

## 2. Python 与 npm

这次验证机器上可用的是：

```powershell
python --version
py -0p
npm.cmd --version
```

实测结果基线：

- `python`: 3.12.10
- `py`: 同时发现 3.12 和 3.14
- `npm.cmd`: 11.13.0

如果 PowerShell 拦截 `npm.ps1`，请直接使用 `npm.cmd`，不要继续纠结 `npm` 别名。

## 3. 创建 repo-local 虚拟环境

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

这样可以把依赖固定在仓库内，不污染系统 Python。

## 4. 安装 Python 依赖

当前仓库没有顶层 `requirements.txt`，但 `cad-mcp-autocad` 子项目有运行依赖。先安装它：

```powershell
.\.venv\Scripts\python.exe -m pip install -r cad-mcp-autocad\requirements.txt
```

当前实际安装到 `.venv` 的关键包包括：

- `pywin32`
- `mcp`
- `pydantic`

## 5. 安装 GitHub CLI

如果后续要把配置过程发到 GitHub，这台机器需要 `gh`。本次使用 `winget` 安装：

```powershell
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
```

安装后可执行文件在：

```powershell
gh --version
```

如果 `gh auth status` 提示未登录，继续执行：

```powershell
gh auth login
```

## 6. 当前仓库的已验证检查命令

使用 repo-local Python 跑检查：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe scripts\security_check.py
.\.venv\Scripts\python.exe scripts\starbridge_preflight.py --markdown
```

Node 侧检查：

```powershell
npm.cmd test
```

本次机器上的实际结果：

- `unittest`: 88 tests, OK
- `security_check.py`: passed
- `starbridge_preflight.py --markdown`: ok
- `npm.cmd test`: OK

## 7. GitHub 推送前还要检查两件事

### `gh` 认证

```powershell
gh auth status
```

### `origin` 是否真的是 GitHub

本地验证仓库可能把 `origin` 指向另一个本地目录。当前工作树曾出现过这种情况：

```text
origin <local-mirror-path>
```

而它的上游真实 GitHub 远端是：

```text
https://github.com/jianbaorui07-dot/Codex-Integration-with-Creative-Industry-Software.git
```

确认方式：

```powershell
git remote -v
git -C <local-mirror-path> remote -v
```

如果当前仓库 `origin` 还是本地路径，需要先改回 GitHub：

```powershell
git remote set-url origin https://github.com/jianbaorui07-dot/Codex-Integration-with-Creative-Industry-Software.git
```

## 8. 最小发布流程

环境修复完成后，建议按这个顺序发：

```powershell
git status -sb
git add docs\windows-setup.md README.md
git commit -m "docs: add windows setup guide"
git push -u origin HEAD
```

如果还要开 PR：

```powershell
gh pr create --draft --fill
```

## 9. 这次机器上实际解决掉的环境问题

- `python` / `py` 现在可用。
- `npm.cmd` 可用，绕开了 PowerShell 对 `npm.ps1` 的执行策略拦截。
- `git status` 的 `dubious ownership` 通过 `safe.directory` 解决。
- `gh` 已安装，但是否能直接推送还取决于 `gh auth login` 和当前 `origin` 是否指向 GitHub。
