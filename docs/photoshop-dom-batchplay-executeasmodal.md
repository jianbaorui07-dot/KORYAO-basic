# Photoshop DOM + batchPlay + executeAsModal

## 1. 启动 Node Proxy

```powershell
cd node_proxy\photoshop-bridge
npm install
npm start
```

## 2. 在 UXP Developer Tool 加载插件

加载目录：

```text
uxp/photoshop-bridge
```

## 3. 启动 MCP Server

```powershell
python -m starbridge_mcp.mcp_server
```

## 4. 调用 `ps.probe`

先看 `node_proxy_uxp -> com -> mock` 哪条链路可用。

## 5. 调用 `ps.document.info`

当前优先走 `node_proxy_uxp`，读取活动文档 DOM 信息；失败再退回 COM 或 mock。

## 6. 调用 `ps.layers.list`

当前优先走 `node_proxy_uxp`，读取图层树；失败再退回 COM 或 mock。

## 7. 调用 `ps.batchplay.validate`

只校验 typed allowlist，不执行。

## 8. 确认后调用 `ps.batchplay.execute_confirmed`

必须同时满足：

- `ps.batchplay.validate` 先通过
- `requires_confirmation=true`
- `confirm_write=true`
- 输出仍然限制在 `sandbox/` 或 `output/`

## 9. 当前哪些是真实 DOM 读取

- `ps.document.info`
- `ps.layers.list`
- `starbridge.ping`

前提是 Node Proxy 已启动且 UXP 插件已连接；否则回退到 COM 或 mock。

## 10. 当前哪些是 executeAsModal 可控写入雏形

- `ps.batchplay.execute_confirmed`
- `ps.preview.export`

它们只允许 sandbox copy 路径，且没有确认就不会执行。

## 11. 当前哪些仍然禁用

- 任意 script execution
- delete / merge / flatten / rasterize / overwrite save
- sandbox 之外的文件写入
