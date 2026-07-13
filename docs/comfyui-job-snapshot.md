# ComfyUI 任务状态快照

`comfyui.job_snapshot` 用于在 WebSocket 观察中断后，按调用方显式提供的 ComfyUI `job_id` 重新获取一次任务状态。默认只返回调用计划；只有 `probe=true` 才会向本机 loopback ComfyUI 发送一次只读 `GET /api/jobs/{job_id}`。

这个接口适合“稍后再查”和完成通知判断，不替代实时的 `comfyui.progress_monitor`，也不会提交、取消、重排或清理任务。

## 为什么需要单独的安全摘要

新版 ComfyUI 的单任务接口可能同时返回 workflow、outputs、preview、execution error、traceback 和节点级执行信息。StarBridge 只保留以下低敏字段：

- 哈希后的 `logical_job_id`；
- 标准化状态：`pending`、`in_progress`、`completed`、`failed` 或 `cancelled`；
- 是否已经进入终态；
- 有界的 `outputs_count`，不返回文件名、路径或内容。

原始响应只在内存中进行有界解析，不写入磁盘，不进入 evidence，不返回给 Codex；workflow、prompt、模型名、输出引用、预览内容、错误正文和 traceback 都会丢弃。

## 默认计划

```json
{
  "name": "comfyui.job_snapshot",
  "arguments": {
    "job_id": "00000000-0000-0000-0000-000000000000"
  }
}
```

默认结果为 `mode=planned`、`decision=planned`、`connected=false`，不会联网。`job_id` 必须是 canonical lowercase UUID；响应中只出现对应的哈希逻辑 ID。

## 显式读取

```json
{
  "name": "comfyui.job_snapshot",
  "arguments": {
    "job_id": "00000000-0000-0000-0000-000000000000",
    "probe": true,
    "comfy_url": "http://127.0.0.1:8188",
    "timeout": 5
  }
}
```

live 模式遵守以下边界：

- 只允许 `http://127.0.0.1`、`http://localhost` 或 `http://[::1]`；
- 直接建立并复核 loopback socket，不使用系统 HTTP proxy；
- 不跟随 redirect；
- 最多读取 1 MiB JSON；
- 每次调用只查询一个显式 job ID；
- 不回退到 `/history`，也不枚举 `/api/jobs`；
- 不保留原始 HTTP 响应。

## 结构化降级

| 情况 | `error_code` | 说明 |
| --- | --- | --- |
| 本机服务未启动、超时或版本没有单任务路由 | `job_endpoint_unavailable` | 保持 loopback 边界后重试或升级本机 ComfyUI |
| 任务不存在 | `job_not_found` | 不扩大为 history 或全量任务搜索 |
| JSON 超限、状态非法、响应 ID 不一致 | `job_payload_invalid` | 拒绝不可信响应，不输出原始内容 |

## 与实时监控的配合

1. 真实提交仍由 `comfyui.agent_run` 的确认门控制。
2. 运行期间用 `comfyui.progress_monitor` 获取有界实时进度。
3. WebSocket 窗口结束、断开或 Codex 稍后恢复任务时，用原始 `job_id` 调用本工具。
4. 只有 `terminal=true` 才能作为完成、失败或取消通知依据；不能根据队列深度推断完成。

官方依据：ComfyUI 当前 server 路由提供 `GET /api/jobs/{job_id}`，并将任务状态统一为 pending、in progress、completed、failed、cancelled；完整响应同时可能包含 workflow 和 outputs，因此 StarBridge 必须做字段级最小化。

- [ComfyUI server.py：`/api/jobs/{job_id}`](https://github.com/Comfy-Org/ComfyUI/blob/master/server.py)
- [ComfyUI jobs.py：任务状态与响应归一化](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_execution/jobs.py)
