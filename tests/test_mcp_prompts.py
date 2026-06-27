from __future__ import annotations

import json
import unittest
from pathlib import Path

from starbridge_mcp.mcp_server import handle_request

REPO_ROOT = Path(__file__).resolve().parents[1]
BANNED_OUTPUT_FRAGMENTS = (
    "C:\\Users\\",
    "/Users/",
    "/home/",
    "Desktop",
    "Documents",
    "AppData",
    str(REPO_ROOT),
)

EXPECTED_PROMPT_NAMES = {
    "bridge_status_check",
    "comfyui_safe_workflow",
    "cad_dxf_from_spec",
    "photoshop_recipe_run",
    "safe_write_protocol",
}


def request(message_id: int, method: str, params: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        payload["params"] = params
    response = handle_request(payload)
    assert response is not None
    return response


class McpPromptsTests(unittest.TestCase):
    def assert_no_private_paths(self, payload: object) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for fragment in BANNED_OUTPUT_FRAGMENTS:
            self.assertNotIn(fragment, text)

    def test_initialize_declares_prompts_capability(self) -> None:
        response = request(1, "initialize", {})
        self.assertIn("prompts", response["result"]["capabilities"])

    def test_prompts_list_returns_known_prompts(self) -> None:
        response = request(2, "prompts/list")
        prompts = response["result"]["prompts"]
        names = {item["name"] for item in prompts}
        self.assertEqual(EXPECTED_PROMPT_NAMES, names)
        for item in prompts:
            self.assertIn("description", item)
            self.assertIn("arguments", item)
        self.assert_no_private_paths(response)

    def test_required_arguments_are_marked(self) -> None:
        response = request(3, "prompts/list")
        by_name = {item["name"]: item for item in response["result"]["prompts"]}
        goal_args = {a["name"]: a for a in by_name["comfyui_safe_workflow"]["arguments"]}
        self.assertTrue(goal_args["goal"]["required"])
        self.assertFalse(goal_args["workflow_type"]["required"])

    def test_prompts_get_substitutes_arguments(self) -> None:
        response = request(
            4,
            "prompts/get",
            {
                "name": "comfyui_safe_workflow",
                "arguments": {"goal": "a teal travel poster", "workflow_type": "img2img"},
            },
        )
        result = response["result"]
        text = result["messages"][0]["content"]["text"]
        self.assertEqual("user", result["messages"][0]["role"])
        self.assertIn("a teal travel poster", text)
        self.assertIn("img2img", text)
        # Safe protocol must be baked in.
        self.assertIn("dry", text.lower())
        self.assert_no_private_paths(response)

    def test_all_prompts_render_with_empty_arguments(self) -> None:
        for name in sorted(EXPECTED_PROMPT_NAMES):
            with self.subTest(prompt=name):
                response = request(5, "prompts/get", {"name": name, "arguments": {}})
                messages = response["result"]["messages"]
                self.assertTrue(messages[0]["content"]["text"])
                self.assert_no_private_paths(response)

    def test_prompts_get_unknown_name_is_invalid_params(self) -> None:
        response = request(6, "prompts/get", {"name": "does-not-exist"})
        self.assertIn("error", response)
        self.assertEqual(-32602, response["error"]["code"])

    def test_prompts_get_requires_string_name(self) -> None:
        response = request(7, "prompts/get", {})
        self.assertIn("error", response)
        self.assertEqual(-32602, response["error"]["code"])


if __name__ == "__main__":
    unittest.main()
