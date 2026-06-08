import http from "node:http";
import { URL } from "node:url";

let WebSocketServer = null;
try {
  ({ WebSocketServer } = await import("ws"));
} catch (_error) {
  WebSocketServer = null;
}

const PORT = Number(process.env.STARBRIDGE_PHOTOSHOP_PROXY_PORT || 8971);
const state = {
  node_proxy_running: true,
  uxp_client_connected: false,
  photoshop_host_seen: false,
  last_ping_at: null,
  pending_jobs: 0,
  photoshop_host: {},
};

const pending = new Map();
let currentClient = null;

function sendJson(response, status, payload) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

function healthPayload() {
  return {
    ok: true,
    node_proxy_running: true,
    uxp_client_connected: state.uxp_client_connected,
    photoshop_host_seen: state.photoshop_host_seen,
    last_ping_at: state.last_ping_at,
    pending_jobs: state.pending_jobs,
    websocket_enabled: Boolean(WebSocketServer),
  };
}

function bridgeStatusPayload() {
  return {
    ...healthPayload(),
    photoshop_host: state.photoshop_host,
  };
}

function rpcToUxp(message) {
  return new Promise((resolve) => {
    if (!currentClient || currentClient.readyState !== 1) {
      resolve({
        jsonrpc: "2.0",
        id: message.id,
        error: { code: -32001, message: "uxp_client_not_connected" },
      });
      return;
    }
    pending.set(message.id, resolve);
    state.pending_jobs = pending.size;
    currentClient.send(JSON.stringify(message));
    setTimeout(() => {
      if (pending.has(message.id)) {
        pending.delete(message.id);
        state.pending_jobs = pending.size;
        resolve({
          jsonrpc: "2.0",
          id: message.id,
          error: { code: -32002, message: "uxp_timeout" },
        });
      }
    }, 8000);
  });
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url || "/", `http://127.0.0.1:${PORT}`);
  if (request.method === "GET" && url.pathname === "/health") {
    sendJson(response, 200, healthPayload());
    return;
  }
  if (request.method === "GET" && url.pathname === "/bridge/status") {
    sendJson(response, 200, bridgeStatusPayload());
    return;
  }
  if (request.method === "POST" && url.pathname === "/rpc") {
    const chunks = [];
    for await (const chunk of request) {
      chunks.push(chunk);
    }
    const message = JSON.parse(Buffer.concat(chunks).toString("utf-8") || "{}");
    const reply = await rpcToUxp(message);
    if (message.method === "starbridge.ping" && reply.result) {
      state.last_ping_at = new Date().toISOString();
      state.photoshop_host_seen = Boolean(reply.result.photoshop_host);
      state.photoshop_host = reply.result.photoshop_host || {};
    }
    sendJson(response, 200, reply);
    return;
  }
  sendJson(response, 404, { ok: false, message: "not_found" });
});

if (WebSocketServer) {
  const wss = new WebSocketServer({ noServer: true });
  server.on("upgrade", (request, socket, head) => {
    if (!request.url?.startsWith("/uxp")) {
      socket.destroy();
      return;
    }
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit("connection", ws, request);
    });
  });
  wss.on("connection", (ws) => {
    currentClient = ws;
    state.uxp_client_connected = true;
    ws.on("message", (data) => {
      const message = JSON.parse(String(data || "{}"));
      if (message.type === "register") {
        state.photoshop_host_seen = true;
        state.last_ping_at = new Date().toISOString();
        return;
      }
      if (message.result?.photoshop_host) {
        state.photoshop_host = message.result.photoshop_host;
        state.photoshop_host_seen = true;
      }
      const resolver = pending.get(message.id);
      if (resolver) {
        pending.delete(message.id);
        state.pending_jobs = pending.size;
        resolver(message);
      }
    });
    ws.on("close", () => {
      if (currentClient === ws) {
        currentClient = null;
      }
      state.uxp_client_connected = false;
    });
  });
}

server.listen(PORT, "127.0.0.1");
