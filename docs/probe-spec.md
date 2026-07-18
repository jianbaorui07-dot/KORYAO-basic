# CreNexus 本地桥 probe 规范

probe 是每条本地桥的只读健康检查脚本。它只回答“本机是否具备接入条件”，不生成作品、不读取私人素材、不上传文件。

## 统一规则

1. 只检测本地软件、本地服务或本地配置是否存在。
2. 不生成真实作品。
3. 不上传任何文件。
4. 不读取用户私人素材。
5. 不写入危险路径。
6. 输出安全 JSON report。
7. 失败时必须返回明确错误原因。
8. 所有本地路径必须脱敏，例如 `C:\Users\用户名\xxx` 替换为 `<USER_HOME>\xxx`。

## 统一输出格式

每个 probe 的 stdout 或 report 文件必须符合这个结构：

```json
{
  "bridge_id": "",
  "ok": false,
  "detected": {},
  "errors": [],
  "warnings": [],
  "safe_to_commit": true
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `bridge_id` | 固定桥 ID，例如 `comfyui`、`photoshop`、`cad_autocad` |
| `ok` | 本机是否满足最小 probe 条件 |
| `detected` | 只保存布尔值、版本号、数量、脱敏后的占位信息 |
| `errors` | 阻止本机接入的结构化错误，包含 `code` 和 `message` |
| `warnings` | 不阻止 probe 输出但需要用户处理的问题 |
| `safe_to_commit` | 样例 report 必须为 `true`，真实本机 report 仍然不提交 |

## 各桥 probe 边界

| 桥 | 允许检测 | 禁止行为 |
| --- | --- | --- |
| ComfyUI | 服务地址、`/system_stats`、`/object_info`、基础节点是否存在 | 提交 `/prompt` 生成任务、读取模型文件、提交输出图 |
| Photoshop | Windows、`Photoshop.Application` COM 类型、`PHOTOSHOP_EXE` 是否配置 | 打开 PSD、保存图片、读取客户素材 |
| CAD / AutoCAD | Windows、`STARBRIDGE_CAD_MODE`、`AUTOCAD_EXE`、COM 注册线索 | 打开 DWG、写入 CAD 文件、读取授权文件 |
| Blender | `STARBRIDGE_BLENDER_EXE` / `BLENDER_EXE`、PATH 中的 `blender` | 生成模型、打开 `.blend`、渲染输出 |
| Illustrator | Windows、`Illustrator.Application` COM 类型、`ILLUSTRATOR_EXE` 是否配置 | 打开 `.ai`、Image Trace 真实源图、导出 SVG/PDF/PNG |
| 剪映 / CapCut | 可执行文件环境变量、草稿目录环境变量是否配置 | 控制桌面版、读取草稿内容、读取素材和字幕、导出视频 |

## report 保存位置

真实本机 probe report 默认写入各桥目录下的 `reports/`：

```text
examples/<bridge>_bridge/reports/
```

`reports/` 已被 `.gitignore` 忽略。仓库只提交 `sample_report.example.json`，用于测试和格式说明。
