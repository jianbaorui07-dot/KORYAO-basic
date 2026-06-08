export const ALLOWLIST = {
  get: {
    descriptorId: "get_document_or_layer_info",
    riskLevel: "safe_read_only",
    requiresConfirmation: false,
    sandboxOnly: false,
  },
  duplicate: {
    descriptorId: "duplicate_current_document_to_sandbox",
    riskLevel: "guarded_local_write",
    requiresConfirmation: true,
    sandboxOnly: true,
  },
  save: {
    descriptorId: "export_preview_from_sandbox_copy",
    riskLevel: "guarded_local_write",
    requiresConfirmation: true,
    sandboxOnly: true,
  },
  make: {
    descriptorId: "create_test_adjustment_layer_in_sandbox",
    riskLevel: "guarded_local_write",
    requiresConfirmation: true,
    sandboxOnly: true,
  },
  set: {
    descriptorId: "rename_or_visibility_in_sandbox",
    riskLevel: "guarded_local_write",
    requiresConfirmation: true,
    sandboxOnly: true,
  },
  move: {
    descriptorId: "move_layer_in_sandbox",
    riskLevel: "guarded_local_write",
    requiresConfirmation: true,
    sandboxOnly: true,
  },
};

export const DENYLIST = new Set([
  "delete",
  "mergeLayersNew",
  "flattenImage",
  "rasterizeLayer",
  "placedLayerEditContents",
  "javascript",
  "batchPlay",
]);

export function validateDescriptor(descriptor) {
  const action = String(descriptor?._obj || descriptor?.method || "").trim();
  if (!action) {
    return {
      allowed: false,
      descriptorId: "missing_action",
      riskLevel: "guarded_local_write",
      requiresConfirmation: true,
      sandboxOnly: true,
      reason: "Descriptor is missing _obj or method.",
    };
  }
  if (DENYLIST.has(action)) {
    return {
      allowed: false,
      action,
      descriptorId: `denied_${action}`,
      riskLevel: "guarded_local_write",
      requiresConfirmation: true,
      sandboxOnly: true,
      reason: `Descriptor action ${action} is explicitly denied.`,
    };
  }
  const allowed = ALLOWLIST[action];
  if (!allowed) {
    return {
      allowed: false,
      action,
      descriptorId: `unknown_${action}`,
      riskLevel: "guarded_local_write",
      requiresConfirmation: true,
      sandboxOnly: true,
      reason: `Descriptor action ${action} is not in the allowlist.`,
    };
  }
  return {
    allowed: true,
    action,
    ...allowed,
    reason: "Descriptor is in the typed allowlist.",
  };
}
