import { validateDescriptor } from "./batchplay-schema.js";

const photoshop = require("photoshop");
const { action, core } = photoshop;

export async function runModalJob(method, params, handler) {
  const commandName = params?.commandName || method;
  try {
    const result = await core.executeAsModal(async (executionContext) => {
      const payload = await handler(executionContext);
      return {
        success: true,
        history_state: executionContext?.historyStateInfo?.name || commandName,
        warnings: payload?.warnings || [],
        errors: payload?.errors || [],
        ...(payload || {}),
      };
    }, { commandName });
    return result;
  } catch (error) {
    return {
      success: false,
      history_state: null,
      warnings: [],
      errors: [{ message: String(error?.message || error), name: String(error?.name || "Error") }],
    };
  }
}

export async function validateBatchPlay(descriptors) {
  return (descriptors || []).map((descriptor, index) => ({
    index: index + 1,
    ...validateDescriptor(descriptor),
  }));
}

export async function executeTypedBatchPlay({ descriptors, requireConfirmation = true, sandboxOnly = true, commandName = "StarBridge BatchPlay" }) {
  const validations = await validateBatchPlay(descriptors);
  const blocked = validations.filter((item) => !item.allowed);
  if (blocked.length) {
    return {
      executed: false,
      validation_result: {
        ok: false,
        blocked_count: blocked.length,
        validations,
      },
      warnings: blocked.map((item) => item.reason),
      errors: [],
    };
  }
  if (!requireConfirmation) {
    return {
      executed: false,
      validation_result: { ok: false, blocked_count: 1, validations },
      warnings: [],
      errors: [{ message: "Confirmation is required." }],
    };
  }
  return runModalJob("ps.batchplay.execute_confirmed", { commandName, sandboxOnly }, async () => {
    const result = await action.batchPlay(descriptors, { synchronousExecution: true, modalBehavior: "execute" });
    return {
      executed: true,
      batchplay_result: result,
      validation_result: { ok: true, blocked_count: 0, validations },
    };
  });
}
