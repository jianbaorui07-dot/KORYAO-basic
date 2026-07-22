import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Ajv from "ajv";
import addFormats from "ajv-formats";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_CONFIG_DIR = path.resolve(SCRIPT_DIR, "../src-tauri");
const DEFAULT_SCHEMA = path.resolve(
  SCRIPT_DIR,
  "../node_modules/@tauri-apps/cli/config.schema.json",
);
const ALLOWED_PLATFORMS = new Set([
  "windows",
  "linux",
  "macos",
  "android",
  "ios",
]);
const SUPPORTED_SCHEMA_FORMATS = new Set([
  "double",
  "int32",
  "int64",
  "uint32",
  "uint8",
  "uri",
  "uuid",
]);

const readJson = (filePath, label) => {
  let text;
  try {
    text = fs.readFileSync(filePath, "utf8");
  } catch (error) {
    throw new Error(`${label} could not be read: ${error.code ?? error.message}`);
  }
  try {
    const value = JSON.parse(text);
    if (value === null || Array.isArray(value) || typeof value !== "object") {
      throw new Error("top-level value must be an object");
    }
    return value;
  } catch (error) {
    throw new Error(`${label} is not valid JSON: ${error.message}`);
  }
};

export const mergePatch = (base, patch) => {
  if (patch === null || Array.isArray(patch) || typeof patch !== "object") {
    return patch;
  }

  const merged =
    base !== null && !Array.isArray(base) && typeof base === "object"
      ? { ...base }
      : {};
  for (const [key, value] of Object.entries(patch)) {
    if (value === null) {
      delete merged[key];
    } else {
      merged[key] = mergePatch(merged[key], value);
    }
  }
  return merged;
};

const collectFormats = (value, formats = new Set()) => {
  if (value === null || typeof value !== "object") {
    return formats;
  }
  if (typeof value.format === "string") {
    formats.add(value.format);
  }
  for (const child of Object.values(value)) {
    collectFormats(child, formats);
  }
  return formats;
};

const createValidator = (schema) => {
  const declaredFormats = collectFormats(schema);
  const unsupportedFormats = [...declaredFormats]
    .filter((format) => !SUPPORTED_SCHEMA_FORMATS.has(format))
    .sort();
  if (unsupportedFormats.length > 0) {
    throw new Error(
      `Tauri schema declares unsupported formats: ${unsupportedFormats.join(", ")}`,
    );
  }

  const ajv = new Ajv({
    allErrors: true,
    strict: true,
    unicodeRegExp: false,
    validateFormats: true,
  });
  addFormats(ajv, {
    formats: ["uri", "uuid"],
    keywords: false,
    mode: "full",
  });
  ajv.addFormat("double", {
    type: "number",
    validate: Number.isFinite,
  });
  ajv.addFormat("int32", {
    type: "number",
    validate: (value) =>
      Number.isInteger(value) && value >= -2147483648 && value <= 2147483647,
  });
  ajv.addFormat("int64", {
    type: "number",
    validate: Number.isSafeInteger,
  });
  ajv.addFormat("uint32", {
    type: "number",
    validate: (value) =>
      Number.isInteger(value) && value >= 0 && value <= 4294967295,
  });
  ajv.addFormat("uint8", {
    type: "number",
    validate: (value) => Number.isInteger(value) && value >= 0 && value <= 255,
  });
  return {
    declaredFormats: [...declaredFormats].sort(),
    validate: ajv.compile(schema),
  };
};

const assertValid = (validate, name, config) => {
  if (!validate(config)) {
    const details = validate.errors
      .map(({ instancePath, message }) => `${instancePath || "/"} ${message}`)
      .join("; ");
    throw new Error(
      `${name} does not match the selected Tauri v2 schema: ${details}`,
    );
  }
};

const parseArgs = (args) => {
  let configDir = DEFAULT_CONFIG_DIR;
  let schemaPath = DEFAULT_SCHEMA;
  let platforms;
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    const value = args[index + 1];
    if (argument === "--config-dir" || argument === "--schema") {
      if (!value) {
        throw new Error(`${argument} requires a path argument`);
      }
      if (argument === "--config-dir") {
        configDir = path.resolve(value);
      } else {
        schemaPath = path.resolve(value);
      }
      index += 1;
    } else if (argument === "--platform") {
      if (!value) {
        throw new Error("--platform requires a platform name");
      }
      platforms ??= [];
      platforms.push(value);
      index += 1;
    } else {
      throw new Error(`unknown argument: ${argument}`);
    }
  }
  return { configDir, platforms: platforms ?? ["windows"], schemaPath };
};

export const validateTauriConfigs = ({ configDir, platforms, schemaPath }) => {
  for (const platform of platforms) {
    if (!ALLOWED_PLATFORMS.has(platform)) {
      throw new Error(`unknown Tauri platform: ${platform}`);
    }
  }

  const schema = readJson(schemaPath, "Tauri schema");
  const { declaredFormats, validate } = createValidator(schema);
  const base = readJson(
    path.join(configDir, "tauri.conf.json"),
    "tauri.conf.json",
  );
  assertValid(validate, "tauri.conf.json", base);

  for (const platform of platforms) {
    const patchName = `tauri.${platform}.conf.json`;
    const patch = readJson(path.join(configDir, patchName), patchName);
    assertValid(
      validate,
      `tauri.conf.json + ${patchName}`,
      mergePatch(base, patch),
    );
  }
  return declaredFormats;
};

export const main = (args = process.argv.slice(2)) => {
  const options = parseArgs(args);
  const declaredFormats = validateTauriConfigs(options);
  console.log(
    `Tauri v2 schema check passed for base and merged platforms: ${options.platforms.join(", ")}.`,
  );
  console.log(
    `Active validators for every schema-declared format: ${declaredFormats.join(", ")}.`,
  );
  console.log(
    "int64 values outside Node.js's exact integer range are rejected fail closed.",
  );
};

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  try {
    main();
  } catch (error) {
    console.error(`Tauri configuration check failed: ${error.message}`);
    process.exitCode = 1;
  }
}
