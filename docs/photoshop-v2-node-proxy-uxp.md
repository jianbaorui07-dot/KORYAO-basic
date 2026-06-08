# Photoshop v2 Node Proxy + UXP

## 1. 启动 Node Proxy

```powershell
cd node_proxy\photoshop-bridge
npm install
npm start
```

默认监听：

```text
http://127.0.0.1:8971
ws://127.0.0.1:8971/uxp
```

## 2. 加载 UXP 插件

在 UXP Developer Tool 中加载：

```text
uxp/photoshop-bridge
```

## 3. 启动 MCP Server

```powershell
python -m starbridge_mcp.mcp_server
```

## 4. 调用 `ps.probe`

确认：

- `node_proxy_running`
- `uxp_client_connected`
- `photoshop_host_seen`
- COM fallback 状态

## 5. 调用 `ps.document.info`

读取当前活动文档：

- document id
- title / name
- width / height
- resolution
- color mode
- bit depth
- active layer
- layer count

## 6. 调用 `ps.layers.list`

读取当前图层树和基础属性。

## 7. 调用 `ps.batchplay.validate`

只允许 typed allowlist：

- get current document info
- get layers list
- duplicate current document to sandbox copy
- export preview from sandbox copy
- create test adjustment layer in sandbox copy
- rename / visibility / move only in sandbox copy

## 8. 确认后调用 `ps.batchplay.execute_confirmed`

需要：

- `confirm_write=true`
- `requires_confirmation=true`
- sandbox 路径

## 9. 当前真实 DOM 读取

- 已接入：`ps.document.info`、`ps.layers.list`

## 10. 当前 executeAsModal 可控写入雏形

- 已接入：typed BatchPlay confirmed path
- 仍然要求 allowlist + confirmation + sandbox only

## 11. 当前仍然禁用

- delete layer
- merge / flatten / rasterize
- overwrite save
- arbitrary script execution
- sandbox 外写入
