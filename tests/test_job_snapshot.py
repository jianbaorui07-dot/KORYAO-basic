from __future__ import annotations

import json
import os
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch

from starbridge_mcp.core.control_planner import build_control_plan
from starbridge_mcp.core.job_snapshot import build_job_snapshot
from starbridge_mcp.core.job_snapshot_schema import SCHEMA_VERSION
from starbridge_mcp.core.tool_registry import list_capabilities
from starbridge_mcp.mcp_server import TOOL_DEFINITIONS, handle_request

JOB_ID = "00000000-0000-0000-0000-000000000000"


def sample_job_payload(status: str = "in_progress") -> dict:
    return {
        "id": JOB_ID,
        "status": status,
        "outputs_count": 0 if status in {"pending", "in_progress"} else 2,
        "workflow": {"prompt": {"text": "sensitive_prompt_marker"}},
        "outputs": {"9": {"images": [{"filename": "sensitive_output_marker.png"}]}},
        "preview_output": {"content": "sensitive_preview_marker"},
        "execution_error": {
            "exception_message": "sensitive_error_marker",
            "traceback": ["sensitive_trace_marker"],
        },
        "execution_status": {"messages": ["sensitive_status_marker"]},
    }


class JobSnapshotTests(unittest.TestCase):
    def test_default_is_plan_only_and_hashes_job_id(self) -> None:
        def fail_if_called(_base_url: str, _job_id: str, _timeout: int) -> dict:
            raise AssertionError("network fetch must not run")

        result = build_job_snapshot(job_id=JOB_ID, fetcher=fail_if_called)
        serialized = json.dumps(result, ensure_ascii=False)

        self.assertTrue(result["ok"])
        self.assertEqual("planned", result["mode"])
        self.assertEqual("planned", result["decision"])
        self.assertFalse(result["connected"])
        self.assertFalse(result["safety"]["network_access"])
        self.assertRegex(result["job"]["logical_job_id"], r"^job_[0-9a-f]{12}$")
        self.assertNotIn(JOB_ID, serialized)

    def test_live_snapshot_discards_sensitive_job_fields(self) -> None:
        result = build_job_snapshot(
            job_id=JOB_ID,
            probe=True,
            fetcher=lambda _base_url, _job_id, _timeout: sample_job_payload(),
        )
        serialized = json.dumps(result, ensure_ascii=False)

        self.assertTrue(result["ok"])
        self.assertEqual("live", result["mode"])
        self.assertEqual("in_progress", result["decision"])
        self.assertEqual("in_progress", result["job"]["status"])
        self.assertFalse(result["job"]["terminal"])
        self.assertFalse(result["job"]["completion_ready"])
        self.assertEqual(0, result["job"]["outputs_count"])
        self.assertTrue(result["redactions_applied"])
        for marker in (
            JOB_ID,
            "sensitive_prompt_marker",
            "sensitive_output_marker",
            "sensitive_preview_marker",
            "sensitive_error_marker",
            "sensitive_trace_marker",
            "sensitive_status_marker",
        ):
            self.assertNotIn(marker, serialized)
        self.assertEqual(
            {
                "logical_job_id",
                "status",
                "terminal",
                "completion_ready",
                "outputs_count",
            },
            set(result["job"]),
        )
        self.assertFalse(result["safety"]["workflow_payloads_returned"])
        self.assertFalse(result["safety"]["output_payloads_returned"])
        self.assertFalse(result["safety"]["raw_payload_retained"])

    def test_terminal_statuses_drive_completion_notice(self) -> None:
        for status in ("completed", "failed", "cancelled"):
            with self.subTest(status=status):
                result = build_job_snapshot(
                    job_id=JOB_ID,
                    probe=True,
                    fetcher=lambda _base_url, _job_id, _timeout, value=status: sample_job_payload(
                        value
                    ),
                )
                self.assertEqual(status, result["decision"])
                self.assertTrue(result["job"]["terminal"])
                self.assertTrue(result["job"]["completion_ready"])
                self.assertEqual(2, result["job"]["outputs_count"])

    def test_job_id_and_loopback_url_are_strictly_validated(self) -> None:
        invalid_ids: tuple[object, ...] = (
            "not-a-uuid",
            "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
            f"{JOB_ID}/history",
            7,
            None,
        )
        for value in invalid_ids:
            with self.subTest(job_id=value), self.assertRaises(ValueError):
                build_job_snapshot(job_id=value)  # type: ignore[arg-type]

        for url in (
            "https://127.0.0.1:8188",
            "http://example.invalid:8188",
            "http://127.0.0.1:8188/api",
            "http://name:x@127.0.0.1:8188",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                build_job_snapshot(job_id=JOB_ID, comfy_url=url)

    def test_invalid_or_mismatched_payload_is_rejected(self) -> None:
        bad_payloads = (
            {**sample_job_payload(), "id": "11111111-1111-1111-1111-111111111111"},
            {**sample_job_payload(), "status": "mystery"},
            {**sample_job_payload(), "outputs_count": -1},
            {**sample_job_payload(), "outputs_count": True},
            {**sample_job_payload(), "outputs_count": 1_000_001},
            [sample_job_payload()],
        )
        for payload in bad_payloads:
            with self.subTest(payload_type=type(payload).__name__):
                result = build_job_snapshot(
                    job_id=JOB_ID,
                    probe=True,
                    fetcher=lambda _base_url, _job_id, _timeout, value=payload: value,
                )
                self.assertFalse(result["ok"])
                self.assertTrue(result["connected"])
                self.assertEqual("unavailable", result["decision"])
                self.assertEqual("job_payload_invalid", result["error_code"])

    def test_direct_loopback_http_ignores_proxy_and_never_follows_redirects(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            mode = "success"

            def do_GET(self) -> None:  # noqa: N802
                if self.mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/else")
                    self.end_headers()
                    return
                body = json.dumps(sample_job_payload()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}"
            with patch.dict(
                os.environ,
                {"HTTP_PROXY": "http://127.0.0.1:1", "NO_PROXY": ""},
                clear=False,
            ):
                result = build_job_snapshot(
                    job_id=JOB_ID,
                    probe=True,
                    comfy_url=url,
                    timeout=2,
                )
            self.assertTrue(result["ok"])
            self.assertFalse(result["safety"]["proxy_used"])

            Handler.mode = "redirect"
            redirected = build_job_snapshot(
                job_id=JOB_ID,
                probe=True,
                comfy_url=url,
                timeout=2,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertFalse(redirected["ok"])
        self.assertEqual("job_endpoint_unavailable", redirected["error_code"])
        self.assertFalse(redirected["safety"]["redirects_followed"])

    def test_not_found_is_distinguished_from_missing_route(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            mode = "job_not_found"

            def do_GET(self) -> None:  # noqa: N802
                if self.mode == "job_not_found":
                    body = json.dumps({"error": "Job not found"}).encode("utf-8")
                    content_type = "application/json"
                else:
                    body = b"404: Not Found"
                    content_type = "text/plain"
                self.send_response(404)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}"
            missing = build_job_snapshot(
                job_id=JOB_ID,
                probe=True,
                comfy_url=url,
                timeout=2,
            )
            Handler.mode = "route_missing"
            unavailable = build_job_snapshot(
                job_id=JOB_ID,
                probe=True,
                comfy_url=url,
                timeout=2,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertFalse(missing["ok"])
        self.assertTrue(missing["connected"])
        self.assertEqual("not_found", missing["decision"])
        self.assertEqual("job_not_found", missing["error_code"])
        self.assertFalse(unavailable["connected"])
        self.assertEqual("job_endpoint_unavailable", unavailable["error_code"])

    def test_tool_registry_planner_recipe_and_mcp_are_wired(self) -> None:
        definitions = {item["name"]: item for item in TOOL_DEFINITIONS}
        tool = definitions["comfyui.job_snapshot"]
        self.assertTrue(tool["annotations"]["readOnlyHint"])
        self.assertTrue(tool["annotations"]["safeDefault"])
        self.assertEqual(["job_id"], tool["inputSchema"]["required"])
        self.assertEqual(
            SCHEMA_VERSION,
            tool["outputSchema"]["properties"]["schema_version"]["const"],
        )

        capabilities = {item["name"] for item in list_capabilities(include_guarded=False)}
        self.assertIn("comfyui.job_snapshot", capabilities)

        plan = build_control_plan(goal="搭建 ComfyUI 文生图 workflow")
        observe = next(phase for phase in plan["phases"] if phase["phase"] == "observe")
        self.assertIn("comfyui.job_snapshot", observe["tools"])
        self.assertFalse(observe["tool_arguments"]["comfyui.job_snapshot"]["probe"])
        self.assertIn("job_id", observe["required_tool_arguments"]["comfyui.job_snapshot"])
        self.assertIn("terminal_status_reviewed", plan["quality_gates"])

        recipe_response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "starbridge.recipe_plan",
                    "arguments": {"recipe_id": "comfyui_txt2img_lifecycle"},
                },
            }
        )
        assert recipe_response is not None
        recipe_plan = recipe_response["result"]["structuredContent"]["plan"]
        self.assertEqual(SCHEMA_VERSION, recipe_plan["job_snapshot"]["schema_version"])
        self.assertIn(
            "comfyui.job_snapshot",
            recipe_plan["action_plan"]["tool_sequence"],
        )

        planned = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "comfyui.job_snapshot",
                    "arguments": {"job_id": JOB_ID},
                },
            }
        )
        assert planned is not None
        self.assertFalse(planned["result"]["isError"])
        self.assertEqual(
            SCHEMA_VERSION,
            planned["result"]["structuredContent"]["schema_version"],
        )

        with patch(
            "starbridge_mcp.core.job_snapshot._read_job",
            return_value=sample_job_payload("completed"),
        ):
            live = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 12,
                    "method": "tools/call",
                    "params": {
                        "name": "comfyui.job_snapshot",
                        "arguments": {"job_id": JOB_ID, "probe": True},
                    },
                }
            )
        assert live is not None
        self.assertFalse(live["result"]["isError"])
        self.assertEqual("completed", live["result"]["structuredContent"]["decision"])
        self.assertNotIn(JOB_ID, json.dumps(live, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
