from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
class BootstrapEntrypointTests(unittest.TestCase):
    def test_profile_is_forwarded_by_name_and_dry_run_returns_json(self) -> None:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(REPO_ROOT / "bootstrap.ps1"),
                "-Profile",
                "auto",
                "-SkipNode",
                "-SkipCodexConfig",
                "-DryRun",
                "-Json",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("auto", payload["profile_requested"])
        self.assertIn(payload["profile_applied"], {"core", "standard"})
        self.assertTrue(payload["ok"])


@unittest.skipUnless(
    os.name != "nt" and shutil.which("bash"),
    "Bash on a POSIX platform is required",
)
class PosixBootstrapEntrypointTests(unittest.TestCase):
    def run_bootstrap(self, repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(repo_root / "bootstrap.sh"), *arguments],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def make_config_fixture(
        self, temporary_root: Path, directory_name: str = "CreNexus config with spaces"
    ) -> tuple[Path, dict[str, str]]:
        repo_root = temporary_root / directory_name
        fake_bin = temporary_root / "bin"
        (repo_root / "starbridge_mcp").mkdir(parents=True)
        coordinator = repo_root / "plugins/starbridge-version-coordinator/scripts"
        coordinator.mkdir(parents=True)
        (coordinator / "version_coordinator_mcp.py").write_text("", encoding="utf-8")
        (repo_root / "pyproject.toml").write_text("[project]\nname = 'fixture'\n", encoding="utf-8")
        (repo_root / "package.json").write_text("{}\n", encoding="utf-8")
        shutil.copy2(REPO_ROOT / "bootstrap.sh", repo_root / "bootstrap.sh")

        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text(
            "#!/usr/bin/env bash\n"
            "set -eu\n"
            "if [[ \"${1:-}\" == \"--version\" ]]; then echo 'Python 3.12.1'; exit 0; fi\n"
            "if [[ \"${1:-}\" == \"-\" || \"${1:-}\" == \"-c\" ]]; then\n"
            f"  exec {shlex.quote(sys.executable)} \"$@\"\n"
            "fi\n"
            "if [[ \"${1:-}\" == \"-m\" && \"${2:-}\" == \"venv\" ]]; then\n"
            "  mkdir -p \"$3/bin\"\n"
            "  cp \"$0\" \"$3/bin/python\"\n"
            "  chmod +x \"$3/bin/python\"\n"
            "fi\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        environment = os.environ | {"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"}
        return repo_root, environment

    def run_fixture_bootstrap(
        self, repo_root: Path, environment: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(repo_root / "bootstrap.sh"), "--profile", "core", "--skip-node", "--json"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
        )

    def load_toml(self, path: Path) -> dict[str, object]:
        try:
            import tomllib
        except ModuleNotFoundError:  # Python 3.10 project environments install tomli.
            import tomli as tomllib

        with path.open("rb") as source:
            return tomllib.load(source)

    def assert_no_config_temporaries(self, config_path: Path) -> None:
        self.assertEqual([], list(config_path.parent.glob(".config.toml.*")))

    def test_help_describes_safe_platform_boundaries(self) -> None:
        completed = self.run_bootstrap(REPO_ROOT, "--help")

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Usage: bash ./bootstrap.sh", completed.stdout)
        self.assertIn("never installed or changed", completed.stdout)
        self.assertIn("never\ninvokes the Tauri desktop application", completed.stdout)

    def test_profiles_keep_python_extra_contract_and_dry_run_is_json(self) -> None:
        expected_extras = {
            "core": {"dev", "vectorization"},
            "standard": {"dev", "vectorization", "cad", "comfy", "adobe", "illustrator-vector"},
            "all": {
                "dev",
                "vectorization",
                "cad",
                "comfy",
                "adobe",
                "illustrator-vector",
                "illustrator-trace",
                "vector-refinement",
                "vector-app",
            },
        }
        for profile, extras in expected_extras.items():
            with self.subTest(profile=profile):
                completed = self.run_bootstrap(
                    REPO_ROOT,
                    "--profile",
                    profile,
                    "--skip-node",
                    "--skip-codex-config",
                    "--dry-run",
                    "--json",
                )

                self.assertEqual(0, completed.returncode, completed.stderr)
                payload = json.loads(completed.stdout)
                self.assertTrue(payload["ok"])
                self.assertEqual(profile, payload["profile_requested"])
                self.assertEqual(profile, payload["profile_applied"])
                self.assertEqual(extras, set(payload["extras"]))
                self.assertEqual(".venv/bin/python", payload["venv"])
                self.assertIsNone(payload["codex_config"])
                self.assertTrue(
                    any(
                        step["name"] == "install Python extras" and step["status"] == "planned"
                        for step in payload["steps"]
                    )
                )

    def test_dry_run_resolves_a_repository_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cre nexus bootstrap ") as temporary_directory:
            linked_repo = Path(temporary_directory) / "CreNexus checkout with spaces"
            linked_repo.symlink_to(REPO_ROOT, target_is_directory=True)
            completed = self.run_bootstrap(
                linked_repo,
                "--profile",
                "core",
                "--skip-node",
                "--skip-codex-config",
                "--dry-run",
                "--json",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(str(linked_repo), payload["repo"])
            venv_step = next(
                step for step in payload["steps"] if step["name"] == "create virtual environment"
            )
            self.assertIn(str(linked_repo), venv_step["detail"])

    def test_config_write_is_idempotent_in_an_isolated_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cre nexus bootstrap ") as temporary_directory:
            temporary_root = Path(temporary_directory)
            repo_root, environment = self.make_config_fixture(
                temporary_root, 'CreNexus config with spaces "and quote" \\ path'
            )
            codex_config = repo_root / ".codex/config.toml"
            codex_config.parent.mkdir()
            codex_config.write_text(
                "[existing]\nkeep = true\n\n"
                "# BEGIN STARBRIDGE QUICKSTART (managed by scripts/quickstart.ps1)\n"
                "old = true\n"
                "# END STARBRIDGE QUICKSTART\n",
                encoding="utf-8",
            )

            for _ in range(2):
                completed = self.run_fixture_bootstrap(repo_root, environment)
                self.assertEqual(0, completed.returncode, completed.stderr)
                self.assertTrue(json.loads(completed.stdout)["ok"])

            config_text = codex_config.read_text(encoding="utf-8")
            self.assertIn("[existing]", config_text)
            self.assertNotIn("old = true", config_text)
            self.assertEqual(1, config_text.count("# BEGIN STARBRIDGE QUICKSTART"))
            self.assertIn('\\"and quote\\"', config_text)
            self.assertIn('\\\\ path', config_text)
            parsed = self.load_toml(codex_config)
            servers = parsed["mcp_servers"]
            self.assertEqual(f"{repo_root}/.venv/bin/python", servers["starbridge"]["command"])
            self.assertEqual(str(repo_root), servers["starbridge"]["cwd"])
            self.assert_no_config_temporaries(codex_config)

    def test_config_conflicts_fail_closed_without_rewriting_bytes(self) -> None:
        cases = {
            "server_table": b'[mcp_servers.starbridge]\ncommand = "user-managed"\n',
            "server_subtable": b'[mcp_servers.starbridge.env]\nSAFE = "0"\n',
            "server_key": b'[mcp_servers]\nstarbridge = "user-managed"\n',
            "coordinator_table": b'[mcp_servers.starbridge-version-coordinator]\ncommand = "user-managed"\n',
        }
        for name, original in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="cre nexus bootstrap ") as temporary_directory:
                repo_root, environment = self.make_config_fixture(Path(temporary_directory), name)
                codex_config = repo_root / ".codex/config.toml"
                codex_config.parent.mkdir()
                codex_config.write_bytes(original)

                completed = self.run_fixture_bootstrap(repo_root, environment)

                self.assertNotEqual(0, completed.returncode)
                self.assertIn("refusing to overwrite", completed.stderr)
                self.assertEqual(original, codex_config.read_bytes())
                self.assert_no_config_temporaries(codex_config)

    def test_invalid_or_repeated_managed_config_fails_closed(self) -> None:
        cases = {
            "invalid_toml": b"[broken\n",
            "unclosed_marker": b"# BEGIN STARBRIDGE QUICKSTART\n[existing]\nkeep = true\n",
            "repeated_marker": (
                b"# BEGIN STARBRIDGE QUICKSTART\n# END STARBRIDGE QUICKSTART\n"
                b"# BEGIN STARBRIDGE QUICKSTART\n# END STARBRIDGE QUICKSTART\n"
            ),
        }
        for name, original in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="cre nexus bootstrap ") as temporary_directory:
                repo_root, environment = self.make_config_fixture(Path(temporary_directory), name)
                codex_config = repo_root / ".codex/config.toml"
                codex_config.parent.mkdir()
                codex_config.write_bytes(original)

                completed = self.run_fixture_bootstrap(repo_root, environment)

                self.assertNotEqual(0, completed.returncode)
                self.assertIn("no configuration changes were made", completed.stderr)
                self.assertEqual(original, codex_config.read_bytes())
                self.assert_no_config_temporaries(codex_config)

    def test_control_character_repository_paths_fail_before_config_writes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cre nexus bootstrap ") as temporary_directory:
            temporary_root = Path(temporary_directory)
            repo_root, environment = self.make_config_fixture(temporary_root, "safe fixture")
            codex_config = repo_root / ".codex/config.toml"
            codex_config.parent.mkdir()
            original = b"[existing]\nkeep = true\n"
            codex_config.write_bytes(original)

            for character in ("\n", "\r", "\x1f"):
                with self.subTest(character=repr(character)):
                    unsafe_link = temporary_root / f"unsafe{character}checkout"
                    unsafe_link.symlink_to(repo_root, target_is_directory=True)
                    completed = subprocess.run(
                        ["bash", str(unsafe_link / "bootstrap.sh"), "--profile", "core", "--skip-node", "--json"],
                        cwd=unsafe_link,
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        env=environment,
                    )

                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn("ASCII control characters", completed.stderr)
                    self.assertEqual(original, codex_config.read_bytes())
                    self.assert_no_config_temporaries(codex_config)


if __name__ == "__main__":
    unittest.main()
