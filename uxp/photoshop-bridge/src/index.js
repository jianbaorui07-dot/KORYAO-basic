import { BridgeClient } from "./bridge-client.js";
import { executeTypedBatchPlay, runModalJob, validateBatchPlay } from "./batchplay-runner.js";

const photoshop = require("photoshop");
const { app } = photoshop;

function currentHost() {
  return {
    app: "Photoshop",
    version: String(app?.version || "unknown"),
  };
}

function activeDocumentOrNull() {
  return app?.activeDocument || null;
}

function safeLayerItem(layer, groupPath = []) {
  return {
    id: String(layer?._id || layer?.id || ""),
    name: String(layer?.name || ""),
    kind: String(layer?.kind || "layer"),
    type: String(layer?.kind || "layer"),
    visible: Boolean(layer?.visible ?? true),
    locked: Boolean(layer?.locked ?? false),
    opacity: Number(layer?.opacity ?? 100),
    blendMode: String(layer?.blendMode || "normal"),
    bounds: layer?.bounds ? {
      left: Number(layer.bounds.left || 0),
      top: Number(layer.bounds.top || 0),
      right: Number(layer.bounds.right || 0),
      bottom: Number(layer.bounds.bottom || 0),
    } : null,
    group_path: groupPath.join("/"),
  };
}

function flattenLayers(layers, groupPath = []) {
  const rows = [];
  for (const layer of layers || []) {
    rows.push(safeLayerItem(layer, groupPath));
    if (layer?.layers?.length) {
      rows.push(...flattenLayers(layer.layers, [...groupPath, String(layer.name || "")]));
    }
  }
  return rows;
}

async function ping() {
  return {
    plugin_status: "ok",
    photoshop_host: currentHost(),
    plugin_version: "1.0.0",
    now: new Date().toISOString(),
  };
}

async function documentInfo() {
  const document = activeDocumentOrNull();
  if (!document) {
    return { ok: false, installed: true, message: "No active Photoshop document." };
  }
  const activeLayer = document.activeLayers?.[0] || null;
  return {
    ok: true,
    photoshop_host: currentHost(),
    document: {
      document_id: String(document._id || document.id || ""),
      title: String(document.title || document.name || ""),
      name: String(document.title || document.name || ""),
      width: Number(document.width || 0),
      height: Number(document.height || 0),
      resolution: Number(document.resolution || 72),
      color_mode: String(document.mode || ""),
      bit_depth: Number(document.bitsPerChannel || 8),
      active_layer_id: String(activeLayer?._id || activeLayer?.id || ""),
      active_layer_name: String(activeLayer?.name || ""),
      layer_count: Array.isArray(document.layers) ? document.layers.length : 0,
      saved: typeof document.saved === "boolean" ? document.saved : null,
    },
  };
}

async function layersList() {
  const document = activeDocumentOrNull();
  if (!document) {
    return { ok: false, installed: true, message: "No active Photoshop document.", layers: [] };
  }
  return {
    ok: true,
    photoshop_host: currentHost(),
    layers: flattenLayers(document.layers || []),
  };
}

async function previewExport(params) {
  const document = activeDocumentOrNull();
  if (!document) {
    return { ok: false, installed: true, message: "No active Photoshop document." };
  }
  if (!params?.confirm_write) {
    return { ok: false, message: "confirm_write=true is required." };
  }
  return runModalJob("ps.preview.export", { commandName: "StarBridge Preview Export" }, async () => ({
    preview_path: String(params.output_path || ""),
    layers_snapshot: flattenLayers(document.layers || []),
    photoshop_host: currentHost(),
    warnings: ["UXP preview export path is registered, but actual bitmap encoding still depends on local host support."],
  }));
}

async function batchplayValidate(params) {
  const descriptors = params?.descriptors || (params?.descriptor ? [params.descriptor] : []);
  const validations = await validateBatchPlay(descriptors);
  return {
    ok: validations.every((item) => item.allowed),
    validations,
    photoshop_host: currentHost(),
  };
}

async function batchplayExecuteConfirmed(params) {
  const descriptors = params?.descriptors || (params?.descriptor ? [params.descriptor] : []);
  const result = await executeTypedBatchPlay({
    descriptors,
    requireConfirmation: Boolean(params?.confirm_write),
    sandboxOnly: true,
    commandName: "StarBridge Typed BatchPlay",
  });
  const document = activeDocumentOrNull();
  return {
    ...result,
    preview_path: String(params?.output_path || ""),
    layers_snapshot: document ? flattenLayers(document.layers || []) : [],
    photoshop_host: currentHost(),
  };
}

const handlers = {
  "starbridge.ping": ping,
  "ps.document.info": documentInfo,
  "ps.layers.list": layersList,
  "ps.preview.export": previewExport,
  "ps.batchplay.validate.local": batchplayValidate,
  "ps.batchplay.execute_confirmed": batchplayExecuteConfirmed,
};

const client = new BridgeClient({ handlers });
client.connect();

if (typeof entrypoints !== "undefined") {
  entrypoints.setup({
    commands: {
      starbridgePing: async () => ping(),
    },
  });
}
