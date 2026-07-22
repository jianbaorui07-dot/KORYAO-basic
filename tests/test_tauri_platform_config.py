from __future__ import annotations

import json
import os
import shlex
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = REPO_ROOT / "apps" / "starbridge-desktop" / "src-tauri"
BASE_CONFIG = TAURI_DIR / "tauri.conf.json"
WINDOWS_CONFIG = TAURI_DIR / "tauri.windows.conf.json"
DESKTOP_PACKAGE = REPO_ROOT / "apps" / "starbridge-desktop" / "package.json"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "starbridge-desktop-release.yml"


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Tauri config must be a JSON object: {path}")
    return value


def merge_patch(base: Any, patch: Any) -> Any:
    """Apply RFC 7396, matching Tauri's documented platform config merge."""
    if not isinstance(patch, dict):
        return patch
    merged = dict(base) if isinstance(base, dict) else {}
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = merge_patch(merged.get(key), value)
    return merged


class TauriPlatformConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.base = load_config(BASE_CONFIG)
        self.windows = merge_patch(self.base, load_config(WINDOWS_CONFIG))

    def test_config_files_are_parseable_tauri_v2_json_objects(self) -> None:
        self.assertEqual("https://schema.tauri.app/config/2", self.base["$schema"])
        self.assertIsInstance(load_config(WINDOWS_CONFIG), dict)
        self.assertIsInstance(self.base["build"], dict)
        self.assertIsInstance(self.base["bundle"], dict)
        self.assertIsInstance(self.windows["bundle"], dict)

    def test_posix_hooks_use_cross_platform_npm_entrypoint(self) -> None:
        build = self.base["build"]
        self.assertEqual("npm run dev", build["beforeDevCommand"])
        self.assertEqual("npm run build", build["beforeBuildCommand"])
        for command in (build["beforeDevCommand"], build["beforeBuildCommand"]):
            self.assertNotIn("npm.cmd", command.lower())
            self.assertEqual("npm", shlex.split(command, posix=True)[0])

    @unittest.skipIf(os.name == "nt", "POSIX hook execution is covered on macOS and Ubuntu")
    def test_posix_hook_preserves_space_path_and_argument_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="CreNexus Tauri hook ") as temporary:
            root = Path(temporary)
            bin_dir = root / "fake npm bin"
            frontend_dir = root / "frontend with spaces"
            capture = root / "captured arguments.json"
            bin_dir.mkdir()
            frontend_dir.mkdir()
            npm = bin_dir / "npm"
            npm.write_text(
                "#!/bin/sh\n"
                'python3 - "$TAURI_HOOK_CAPTURE" "$PWD" "$@" <<\'PY\'\n'
                "import json, sys\n"
                "from pathlib import Path\n"
                "Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]), encoding='utf-8')\n"
                "PY\n",
                encoding="utf-8",
            )
            npm.chmod(npm.stat().st_mode | stat.S_IXUSR)
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
            env["TAURI_HOOK_CAPTURE"] = str(capture)

            subprocess.run(
                self.base["build"]["beforeBuildCommand"],
                shell=True,
                cwd=frontend_dir,
                env=env,
                check=True,
            )

            captured = json.loads(capture.read_text(encoding="utf-8"))
            self.assertEqual(frontend_dir.resolve(), Path(captured[0]).resolve())
            self.assertEqual(["run", "build"], captured[1:])

    def test_windows_merge_retains_sidecar_resources_and_nsis(self) -> None:
        bundle = self.windows["bundle"]
        self.assertTrue(bundle["active"])
        self.assertEqual(["nsis"], bundle["targets"])
        self.assertEqual(["binaries/starbridge-sidecar"], bundle["externalBin"])
        self.assertEqual({"binaries/_internal/": "_internal/"}, bundle["resources"])
        self.assertEqual("currentUser", bundle["windows"]["nsis"]["installMode"])
        package = load_config(DESKTOP_PACKAGE)
        self.assertEqual(
            "tauri build --bundles nsis",
            package["scripts"]["tauri:bundle:nsis"],
        )
        self.assertEqual(
            "node --test scripts/check-tauri-config.node-tests.mjs && node scripts/check-tauri-config.mjs",
            package["scripts"]["test:tauri-config"],
        )
        release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "npm run tauri -- build --bundles nsis --config $releaseConfig",
            release_workflow,
        )
        self.assertIn("Build-Sidecar.ps1", release_workflow)
        self.assertIn("New-StarBridgeUpdateManifest.ps1", release_workflow)

    def test_non_windows_base_does_not_require_a_windows_or_darwin_sidecar(self) -> None:
        bundle = self.base["bundle"]
        self.assertFalse(bundle["active"])
        self.assertNotIn("externalBin", bundle)
        config_text = "\n".join(
            path.read_text(encoding="utf-8") for path in (BASE_CONFIG, WINDOWS_CONFIG)
        ).lower()
        self.assertNotIn("apple-darwin", config_text)
        self.assertNotIn("aarch64", config_text)
        self.assertNotIn("x86_64", config_text)


if __name__ == "__main__":
    unittest.main()
