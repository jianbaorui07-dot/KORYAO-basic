# Codex 接入 Blender 插件工具规格

本文档描述一个可落地的 Codex Blender 插件/MCP 工具设计。它把当前 `blender-drawing-learning` skill 的脚本和数据结构升级为可注册、可调用、可验证的工具接口。

## 设计目标

1. 让 Codex 可以读取本地 Blender 资产并生成结构化学习数据。
2. 让 Codex 能够按单个 `.blend` 做实验：打开、profile、分析、生成笔记。
3. 让输出可以安全提交到 GitHub，不泄露本机路径和原始素材。
4. 为后续“自动建场景、自动打光、自动渲染验证”保留接口。

## 安全原则

- 默认只读。
- 默认不运行 `.blend` 内嵌脚本。
- 默认不导出渲染图、不复制贴图、不上传原始资产。
- 所有公开输出必须脱敏：不含本机绝对路径、账号、缓存目录、授权文件。
- 所有写入必须限制在仓库内的 `docs/blender-drawing-learning/` 或显式 sandbox 输出目录。

## 环境变量

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `BLENDER_EXE` | 是 | Blender 可执行文件路径。 |
| `BLENDER_ASSET_ROOT` | 是 | 本地 Blender 素材根目录。 |
| `BLENDER_LEARNING_OUT` | 否 | 输出根目录，默认 `docs/blender-drawing-learning`。 |
| `BLENDER_PROFILE_LIMIT` | 否 | 限制读取 `.blend` 数量。 |

## 工具 1：`blender_probe_environment`

检查 Blender 和素材根目录是否可用。

### 输入

```json
{
  "blenderExe": "string | optional",
  "assetRoot": "string | optional",
  "redactPaths": "boolean | default true"
}
```

### 输出

```json
{
  "ok": true,
  "blender": {
    "exists": true,
    "version": "5.1.2",
    "pathRedacted": true
  },
  "assetRoot": {
    "exists": true,
    "pathRedacted": true
  },
  "warnings": []
}
```

### 行为

- 如果 `blenderExe` 或 `assetRoot` 未传入，读取环境变量。
- 可以调用 `blender --version`。
- 输出中不得回显本机绝对路径，除非用户明确要求本地调试。

## 工具 2：`blender_index_assets`

生成脱敏素材索引。

### 输入

```json
{
  "assetRoot": "string",
  "outDir": "string",
  "includeExtensions": ["string"],
  "excludeArchives": "boolean | default false",
  "maxFiles": "integer | default 0"
}
```

### 输出

```json
{
  "ok": true,
  "fileCount": 778,
  "folderCount": 78,
  "totalGb": 50.653,
  "outputs": {
    "inventoryCsv": "docs/blender-drawing-learning/data/asset_inventory_redacted.csv",
    "summaryJson": "docs/blender-drawing-learning/data/asset_summary_redacted.json"
  }
}
```

### 字段说明

| 输入字段 | 说明 |
| --- | --- |
| `assetRoot` | 本地读取目录，只用于扫描。 |
| `outDir` | 仓库内输出目录。 |
| `includeExtensions` | 可选扩展名过滤，如 `[".blend", ".fbx"]`。 |
| `excludeArchives` | 是否跳过 `.zip/.rar/.7z`。 |
| `maxFiles` | `0` 表示不限制。 |

## 工具 3：`blender_profile_scenes`

使用 Blender 后台打开 `.blend` 并抽取 scene profile。

### 输入

```json
{
  "blenderExe": "string",
  "assetRoot": "string",
  "out": "string",
  "matchLabel": "string | optional",
  "limit": "integer | default 0",
  "schemaVersion": "0.2",
  "runEmbeddedScripts": "boolean | default false"
}
```

### 输出

```json
{
  "ok": true,
  "attempted": 25,
  "profileCount": 25,
  "errorCount": 0,
  "outputJson": "docs/blender-drawing-learning/data/blend_scene_profiles_redacted.json",
  "schemaVersion": "0.2"
}
```

### 行为

- 调用 Blender 后台命令。
- 使用 `--match-label` 可只读取一个案例。
- 默认不运行 embedded scripts。
- 输出遵循 `PARAMETER_SCHEMA.md`。

### 推荐命令形态

```powershell
& $env:BLENDER_EXE --background --python scripts\blender_scene_profile.py -- --root $env:BLENDER_ASSET_ROOT --out docs\blender-drawing-learning\data\blend_scene_profiles_redacted.json
```

单案例：

```powershell
& $env:BLENDER_EXE --background --python scripts\blender_scene_profile.py -- --root $env:BLENDER_ASSET_ROOT --out docs\blender-drawing-learning\data\case_profile_redacted.json --match-label "<case label>"
```

## 工具 4：`blender_generate_case_notes`

从 profile JSON 生成逐案例学习笔记。

### 输入

```json
{
  "profiles": "string",
  "outDir": "string",
  "language": "zh-CN | default zh-CN",
  "filenameMode": "ascii | default ascii",
  "includeExperimentChecklist": "boolean | default true"
}
```

### 输出

```json
{
  "ok": true,
  "caseCount": 25,
  "indexMarkdown": "docs/blender-drawing-learning/experiments/all-blend-cases.md",
  "casesDir": "docs/blender-drawing-learning/experiments/cases"
}
```

### 行为

- 读取 `blend_scene_profiles_redacted.json`。
- 生成 `all-blend-cases.md`。
- 生成 `cases/case-001.md` 到 `cases/case-NNN.md`。
- 文件名默认 ASCII，避免跨系统编码问题。

## 工具 5：`blender_create_learning_pack`

组合工具：一次完成索引、profile、案例笔记。

### 输入

```json
{
  "blenderExe": "string",
  "assetRoot": "string",
  "outRoot": "string | default docs/blender-drawing-learning",
  "matchLabel": "string | optional",
  "limit": "integer | default 0",
  "publishSafe": "boolean | default true"
}
```

### 输出

```json
{
  "ok": true,
  "outputs": {
    "assetSummary": "docs/blender-drawing-learning/data/asset_summary_redacted.json",
    "assetInventory": "docs/blender-drawing-learning/data/asset_inventory_redacted.csv",
    "sceneProfiles": "docs/blender-drawing-learning/data/blend_scene_profiles_redacted.json",
    "caseIndex": "docs/blender-drawing-learning/experiments/all-blend-cases.md",
    "caseNotes": "docs/blender-drawing-learning/experiments/cases"
  },
  "checks": {
    "pathRedaction": "passed",
    "rawAssetsCommitted": false
  }
}
```

### 行为

1. 运行环境检查。
2. 生成资产索引。
3. 生成 scene profile。
4. 生成案例笔记。
5. 运行脱敏检查。
6. 输出 GitHub 提交建议。

## 工具 6：`blender_render_preview`

后续实验工具，用于生成小尺寸预览。当前建议作为 planned，不默认启用。

### 输入

```json
{
  "blenderExe": "string",
  "blendFile": "string",
  "outPng": "string",
  "cameraName": "string | optional",
  "resolution": [960, 540],
  "samples": "integer | default 32",
  "publishSafe": "boolean | default false"
}
```

### 安全要求

- 默认不提交预览图到 GitHub。
- 如果预览图可能复现原始素材，应只留本地。
- 只有在用户明确授权且版权安全时，才可提交图像。

## 插件清单建议

如果做成 Codex plugin，可包含：

```text
blender-drawing-plugin/
  .codex-plugin/
    plugin.json
  skills/
    blender-drawing-learning/
      SKILL.md
  scripts/
    analyze_blender_learning_assets.py
    blender_scene_profile.py
    generate_blender_case_notes.py
  mcp/
    blender_learning_server.py
  docs/
    PARAMETER_SCHEMA.md
    CODEX_BLENDER_PLUGIN_SPEC.md
```

## MCP Server 工具注册草案

| MCP 工具名 | 对应脚本/动作 | 写入范围 |
| --- | --- | --- |
| `blender_probe_environment` | 检查 Blender 和素材根目录 | 无 |
| `blender_index_assets` | `analyze_blender_learning_assets.py` | `docs/blender-drawing-learning/data` |
| `blender_profile_scenes` | `blender_scene_profile.py` | `docs/blender-drawing-learning/data` |
| `blender_generate_case_notes` | `generate_blender_case_notes.py` | `docs/blender-drawing-learning/experiments` |
| `blender_create_learning_pack` | 组合流程 | `docs/blender-drawing-learning` |
| `blender_render_preview` | Blender 渲染预览 | sandbox，本地优先 |

## 验证门槛

发布前必须通过：

```powershell
rg -n "[A-Z]:\\\\" docs\blender-drawing-learning scripts\*.py .codex\skills\blender-drawing-learning
python -m py_compile scripts\analyze_blender_learning_assets.py scripts\blender_scene_profile.py scripts\generate_blender_case_notes.py
git status -sb
```

如果要验证 profile 内容：

```powershell
python -c "import json; d=json.load(open('docs/blender-drawing-learning/data/blend_scene_profiles_redacted.json', encoding='utf-8')); print(d['profile_count'], d['error_count'], d['profiles'][0]['schema_version'])"
```
