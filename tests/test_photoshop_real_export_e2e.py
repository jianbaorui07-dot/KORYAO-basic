"""End-to-end test for the real Photoshop preview export chain.

This test exercises the *real* node_proxy + UXP + Photoshop link end-to-end and
verifies that a genuine PNG is produced under examples/output/photoshop along
with a manifest whose hash/dimensions actually match the file on disk.

Distinction from the protocol/format tests in test_photoshop_adapter_v1.py:
- those tests use bridge_kind="mock" and verify protocol shape only.
- this test refuses to run unless a live node_proxy with a connected UXP
  client is detectable. When the link is missing it skips - never mocks.
"""

from __future__ import annotations

import hashlib
import os
import unittest
from pathlib import Path

from starbridge_mcp.adapters.photoshop.evidence import read_png_dimensions
from starbridge_mcp.adapters.photoshop.node_proxy_client import bridge_status, health
from starbridge_mcp.mcp_server import handle_request

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "examples" / "output" / "photoshop"


def _live_chain_available() -> tuple[bool, str]:
    """Return (available, reason). available=True only when node_proxy is up
    AND a UXP client is connected. We never fall back to mock from here."""
    if os.environ.get("STARBRIDGE_PHOTOSHOP_E2E") != "1":
        return False, "STARBRIDGE_PHOTOSHOP_E2E env var is not set to 1"
    h = health(timeout=2)
    if not h.get("ok") or not h.get("node_proxy_running"):
        return False, f"node_proxy not running: {h.get('message') or h}"
    status = bridge_status(timeout=2)
    if not status.get("uxp_client_connected"):
        return False, "UXP client is not connected to node_proxy"
    if not status.get("photoshop_host_seen"):
        return False, "Photoshop host was not seen by node_proxy"
    return True, "ok"


def _call(name: str, arguments: dict) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 9001,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response = handle_request(payload)
    assert response is not None
    return response["result"]["structuredContent"]


class PhotoshopRealExportE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        available, reason = _live_chain_available()
        if not available:
            raise unittest.SkipTest(
                "Live Photoshop chain unavailable; skipping real e2e. Reason: " + reason
            )

    def test_strict_probe_passes_when_uxp_is_connected(self) -> None:
        result = _call("ps.probe", {"strict": True})
        self.assertTrue(result["ok"], msg=result)
        self.assertEqual("node_proxy_uxp", result["details"]["bridge_kind"])

    def test_real_preview_export_writes_png_with_matching_manifest(self) -> None:
        result = _call(
            "ps.preview.export",
            {
                "dry_run": False,
                "writes_files": True,
                "requires_confirmation": True,
                "confirm_write": True,
                "strict": True,
                "output_dir": "examples/output/photoshop",
            },
        )
        self.assertTrue(result["ok"], msg=result)
        details = result["details"]
        self.assertEqual("node_proxy_uxp", details["bridge_kind"])
        artifacts = details["output_artifacts"]
        self.assertEqual(1, len(artifacts), msg=details)
        artifact = artifacts[0]

        png_path = REPO_ROOT / artifact["relative_path"]
        self.assertTrue(png_path.is_file(), f"expected real PNG at {png_path}")
        self.assertTrue(
            png_path.is_relative_to(OUTPUT_DIR),
            f"PNG escaped sandbox: {png_path}",
        )

        data = png_path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        width, height = read_png_dimensions(data)
        self.assertEqual(sha, artifact["sha256"])
        self.assertEqual(len(data), artifact["bytes"])
        self.assertEqual(width, artifact["width"])
        self.assertEqual(height, artifact["height"])
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

        manifest_path_rel = details["evidence_path"]
        self.assertIsNotNone(manifest_path_rel)
        self.assertTrue((REPO_ROOT / manifest_path_rel).is_file())
        manifest = details["evidence_manifest"]
        self.assertEqual("node_proxy_uxp", manifest["bridge_kind"])
        self.assertNotEqual("mock", manifest["bridge_kind"])
        self.assertIn(artifact, manifest["output_artifacts"])


if __name__ == "__main__":
    unittest.main()
