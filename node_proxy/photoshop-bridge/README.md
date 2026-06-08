# StarBridge Photoshop Node Proxy

Starts a local HTTP JSON-RPC bridge between the StarBridge MCP server and the Photoshop UXP plugin.

## Start

```powershell
cd node_proxy\photoshop-bridge
npm install
npm start
```

## Endpoints

- `GET /health`
- `GET /bridge/status`
- `POST /rpc`

## Notes

- The UXP plugin connects to `ws://127.0.0.1:8971/uxp`.
- If no UXP client is connected, `/rpc` returns `uxp_client_not_connected`.
- Keep all writes inside `sandbox/` or `output/`.
