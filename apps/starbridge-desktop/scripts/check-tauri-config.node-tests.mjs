import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { after, test } from "node:test";
import { fileURLToPath } from "node:url";

import { mergePatch } from "./check-tauri-config.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DESKTOP_DIR = path.resolve(SCRIPT_DIR, "..");
const CHECKER = path.join(SCRIPT_DIR, "check-tauri-config.mjs");
const TAURI_CLI = path.join(
  DESKTOP_DIR,
  "node_modules/@tauri-apps/cli/tauri.js",
);
const TAURI_SCHEMA = path.join(
  DESKTOP_DIR,
  "node_modules/@tauri-apps/cli/config.schema.json",
);
const TAURI_CLI_VERSION = JSON.parse(
  fs.readFileSync(
    path.join(DESKTOP_DIR, "node_modules/@tauri-apps/cli/package.json"),
    "utf8",
  ),
).version;
const BASE_CONFIG = JSON.parse(
  fs.readFileSync(path.join(DESKTOP_DIR, "src-tauri/tauri.conf.json"), "utf8"),
);
const WINDOWS_PATCH = JSON.parse(
  fs.readFileSync(
    path.join(DESKTOP_DIR, "src-tauri/tauri.windows.conf.json"),
    "utf8",
  ),
);
const temporaryDirectories = [];

after(() => {
  for (const directory of temporaryDirectories) {
    fs.rmSync(directory, { force: true, recursive: true });
  }
});

const clone = (value) => JSON.parse(JSON.stringify(value));

const temporaryDirectory = () => {
  const directory = fs.mkdtempSync(
    path.join(os.tmpdir(), "CreNexus Tauri config with spaces "),
  );
  temporaryDirectories.push(directory);
  return directory;
};

const writeCheckerFixture = ({
  base = BASE_CONFIG,
  patch = WINDOWS_PATCH,
  schema = JSON.parse(fs.readFileSync(TAURI_SCHEMA, "utf8")),
  writePatch = true,
} = {}) => {
  const directory = temporaryDirectory();
  fs.writeFileSync(path.join(directory, "tauri.conf.json"), JSON.stringify(base));
  if (writePatch) {
    fs.writeFileSync(
      path.join(directory, "tauri.windows.conf.json"),
      JSON.stringify(patch),
    );
  }
  const schemaPath = path.join(directory, "Tauri schema with spaces.json");
  fs.writeFileSync(schemaPath, JSON.stringify(schema));
  return { directory, schemaPath };
};

const runChecker = (fixture, platform = "windows") =>
  spawnSync(
    process.execPath,
    [
      CHECKER,
      "--config-dir",
      fixture.directory,
      "--schema",
      fixture.schemaPath,
      "--platform",
      platform,
    ],
    { encoding: "utf8" },
  );

const writeTauriFixture = (configText) => {
  const directory = temporaryDirectory();
  const tauriDirectory = path.join(directory, "src-tauri");
  fs.mkdirSync(tauriDirectory);
  fs.mkdirSync(path.join(directory, "dist"));
  fs.writeFileSync(path.join(tauriDirectory, "tauri.conf.json"), configText);
  fs.writeFileSync(
    path.join(tauriDirectory, "Cargo.toml"),
    '[package]\nname = "tauri-config-fixture"\nversion = "0.0.0"\nedition = "2021"\n\n[dependencies]\ntauri = "2"\n',
  );
  fs.writeFileSync(
    path.join(directory, "package.json"),
    JSON.stringify({
      devDependencies: { "@tauri-apps/cli": TAURI_CLI_VERSION },
      name: "tauri-config-fixture",
      private: true,
      version: "0.0.0",
    }),
  );
  return directory;
};

const runTauriParser = (config) => {
  const directory = writeTauriFixture(JSON.stringify(config));
  return spawnSync(process.execPath, [TAURI_CLI, "info"], {
    cwd: directory,
    encoding: "utf8",
  });
};

const runTauriBuildParser = (configText) => {
  const directory = writeTauriFixture(configText);
  return spawnSync(
    process.execPath,
    [TAURI_CLI, "build", "--no-bundle", "--runner", process.execPath],
    { cwd: directory, encoding: "utf8" },
  );
};

const assertCheckerAndTauri = ({ base, expectedStatus, label }) => {
  const fixture = writeCheckerFixture({ base });
  const checker = runChecker(fixture);
  const tauri = runTauriParser(mergePatch(base, WINDOWS_PATCH));
  assert.equal(
    checker.status,
    expectedStatus,
    `${label}: checker output\n${checker.stderr}${checker.stdout}`,
  );
  assert.equal(
    tauri.status,
    expectedStatus,
    `${label}: Tauri CLI output\n${tauri.stderr}${tauri.stdout}`,
  );
};

test("valid base and Windows merge agree with the installed Tauri CLI", () => {
  assert.equal(TAURI_CLI_VERSION, "2.11.4");
  assertCheckerAndTauri({
    base: clone(BASE_CONFIG),
    expectedStatus: 0,
    label: "valid configuration",
  });
});

test("invalid devUrl URI fails closed in checker and Tauri CLI", () => {
  const base = clone(BASE_CONFIG);
  base.build.devUrl = "this is not a URL";
  assertCheckerAndTauri({ base, expectedStatus: 1, label: "invalid devUrl" });
});

test("invalid numeric range fails closed in checker and Tauri CLI", () => {
  const base = clone(BASE_CONFIG);
  base.bundle.android = { versionCode: 2100000001 };
  assertCheckerAndTauri({ base, expectedStatus: 1, label: "invalid versionCode" });
});

test("UUID and integer formats are enforced", () => {
  const uuidBase = clone(BASE_CONFIG);
  uuidBase.bundle.windows = { wix: { upgradeCode: "not-a-uuid" } };
  const uuid = runChecker(writeCheckerFixture({ base: uuidBase }));
  assert.equal(uuid.status, 1, `${uuid.stderr}${uuid.stdout}`);
  assert.match(uuid.stderr, /uuid/iu);

  const integerBase = clone(BASE_CONFIG);
  integerBase.app.windows[0].backgroundColor = [256, 0, 0];
  const integer = runChecker(writeCheckerFixture({ base: integerBase }));
  assert.equal(integer.status, 1, `${integer.stderr}${integer.stdout}`);
  assert.match(integer.stderr, /uint8|format/iu);
});

test("unknown schema formats fail instead of being skipped", () => {
  const schema = JSON.parse(fs.readFileSync(TAURI_SCHEMA, "utf8"));
  schema.properties.identifier.format = "future-tauri-format";
  const result = runChecker(writeCheckerFixture({ schema }));
  assert.equal(result.status, 1, `${result.stderr}${result.stdout}`);
  assert.match(result.stderr, /unsupported formats: future-tauri-format/iu);
});

test("invalid JSON and a missing platform patch fail safely", () => {
  const invalidJson = writeCheckerFixture();
  fs.writeFileSync(path.join(invalidJson.directory, "tauri.conf.json"), "{");
  const invalid = runChecker(invalidJson);
  assert.equal(invalid.status, 1, `${invalid.stderr}${invalid.stdout}`);
  assert.match(invalid.stderr, /not valid JSON/iu);
  const tauri = runTauriBuildParser("{");
  assert.equal(tauri.status, 1, `${tauri.stderr}${tauri.stdout}`);
  assert.match(tauri.stderr, /failed to parse config/iu);

  const missing = runChecker(writeCheckerFixture({ writePatch: false }));
  assert.equal(missing.status, 1, `${missing.stderr}${missing.stdout}`);
  assert.match(missing.stderr, /tauri\.windows\.conf\.json could not be read/iu);
});

test("unknown platforms fail before platform files are read", () => {
  const result = runChecker(writeCheckerFixture(), "solaris");
  assert.equal(result.status, 1, `${result.stderr}${result.stdout}`);
  assert.match(result.stderr, /unknown Tauri platform: solaris/iu);
});

test("paths containing spaces preserve config and schema argument boundaries", () => {
  const fixture = writeCheckerFixture();
  assert.match(fixture.directory, / /u);
  const result = runChecker(fixture);
  assert.equal(result.status, 0, `${result.stderr}${result.stdout}`);
});
