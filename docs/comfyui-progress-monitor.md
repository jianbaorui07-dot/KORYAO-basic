# ComfyUI 实时进度监控

`comfyui.progress_monitor` 把 ComfyUI `/ws` 的执行事件转换成适合 Codex 判断长任务状态的脱敏快照。默认调用只返回连接计划；只有显式传入 `connect=true` 才会连接本机 loopback WebSocket。

该工具是只读观察层，不提交、取消、移动或清空队列，也不读取 `/history`、workflow、模型信息、生成图、输出文件或异常 traceback。

## 安全默认值

- 默认 `connect=false`，不访问网络，也不要求安装 WebSocket 依赖。
- live 模式只接受 `http://127.0.0.1`、`http://localhost` 或 `http://[::1]` 形式的基础地址。
- 连接固定转换到 `/ws`，使用直接 loopback socket；不使用环境代理，不跟随 WebSocket 握手重定向。
- 二进制预览帧只计数后丢弃，不解码、不保存、不返回。
- `prompt_id` 和 node ID 只在内存中匹配，输出统一为 SHA-256 截断后的逻辑 ID。
- `executed.output`、`execution_error` 的异常文字和所有未知嵌套字段都不会进入结果。
- 单次监听最长 30 秒、最多 500 个事件；单个文本帧最大 1 MiB。

live 支持使用可选依赖：

```powershell
python -m pip install -e ".[comfy]"
```

未安装依赖时，plan-only 仍然可用；live 调用会返回结构化的 `websocket_dependency_unavailable`，不会临时下载软件包。

## MCP 调用

只查看契约，不联网：

```json
{
  "name": "comfyui.progress_monitor",
  "arguments": {}
}
```

监听本机事件：

```json
{
  "name": "comfyui.progress_monitor",
  "arguments": {
    "connect": true,
    "listen_seconds": 5,
    "stall_after_seconds": 5,
    "max_events": 100
  }
}
```

如调用方已经从受控提交结果取得原始 `prompt_id`，可以只监控该任务：

```json
{
  "name": "comfyui.progress_monitor",
  "arguments": {
    "connect": true,
    "target_job_id": "<prompt-id-from-current-session>"
  }
}
```

`target_job_id` 不会被回显。结果中的 `logical_job_id` 只能用于同一次控制链路内关联，不能提交回 ComfyUI。

## 状态判定

| decision | 含义 |
| --- | --- |
| `planned` | 未连接，只返回安全计划 |
| `unavailable` | 依赖、loopback endpoint 或事件载荷不可用 |
| `observing` | 已连接，但监听窗口内没有足够信息判断某个任务 |
| `idle` | 收到权威 `status`，且 `queue_remaining=0` |
| `queued` | 尚未开始执行，且 `queue_remaining>0` |
| `running` | 已收到匹配任务的开始、节点或有效进度事件 |
| `stalled` | 任务仍在运行，但在阈值内没有节点切换、节点完成或数值进度增长 |
| `completed` | 收到 `execution_success`，或兼容旧协议的 `executing.node=null` |
| `failed` | 收到 `execution_error`；不会返回异常内容 |
| `interrupted` | 收到 `execution_interrupted` |

stall 使用“有效前进”而不是“收到任意消息”计时。重复 `status`、重复进度或未知事件不会刷新计时器；同一节点内回退的 `progress.value` 会被拒绝并记录 `progress_regression_ignored`。节点切换会开始新的 `scope=current_node` 进度段，允许数值从较小值重新开始，不会伪造整个 workflow 的总百分比。因此工具不会把活跃但没有真实进展的消息流误判为健康运行。

## 能力边界

本工具不会自动重连、自动取消、重启 ComfyUI 或读取 history 来补全断线期间的状态。一次返回只是有界监听窗口的安全快照；需要持续观察时，由调用方再次显式调用。若调用方保留了当前受控提交返回的原始 job UUID，可改用 [`comfyui.job_snapshot`](comfyui-job-snapshot.md) 做一次字段最小化的终态查询。受控 cancel 必须作为独立 tool，另行补文档、schema、测试和确认门。
