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

EXPECTED_RESOURCE_URIS = {
    "starbridge://capabilities",
    "starbridge://safe-roots",
    "starbridge://bridges",
    "starbridge://safety-policy",
}


def request(message_id: int, method: str, params: dict | None = None) -> dict:
    payload = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        payload["params"] = params
    response = handle_request(payload)
    assert response is not None
    return response


class McpResourcesTests(unittest.TestCase):
    def assert_no_private_paths(self, payload: object) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        for fragment in BANNED_OUTPUT_FRAGMENTS:
            self.assertNotIn(fragment, text)

    def test_initialize_declares_resources_capability_and_instructions(self) -> None:
        response = request(1, "initialize", {})
        result = response["result"]
        self.assertIn("resources", result["capabilities"])
        self.assertIn("tools", result["capabilities"])
        self.assertIsInstance(result.get("instructions"), str)
        self.assertIn("dry_run", result["instructions"])
        self.assertIn("starbridge://safety-policy", result["instructions"])

    def test_resources_list_returns_known_resources(self) -> None:
        response = request(2, "resources/list")
        resources = response["result"]["resources"]
        uris = {item["uri"] for item in resources}
        self.assertEqual(EXPECTED_RESOURCE_URIS, uris)
        for item in resources:
            self.assertIn("name", item)
            self.assertIn("description", item)
            self.assertIn("mimeType", item)
        self.assert_no_private_paths(response)

    def test_resources_read_returns_sanitized_content(self) -> None:
        for uri in sorted(EXPECTED_RESOURCE_URIS):
            with self.subTest(uri=uri):
                response = request(3, "resources/read", {"uri": uri})
                contents = response["result"]["contents"]
                self.assertEqual(1, len(contents))
                entry = contents[0]
                self.assertEqual(uri, entry["uri"])
                self.assertTrue(entry["text"])
                self.assert_no_private_paths(response)

    def test_capabilities_resource_is_valid_json_matching_tool_registry(self) -> None:
        response = request(4, "resources/read", {"uri": "starbridge://capabilities"})
        payload = json.loads(response["result"]["contents"][0]["text"])
        self.assertEqual("tools", payload["action"])
        self.assertGreater(payload["capability_count"], 0)
        self.assertTrue(all("current_status" in item for item in payload["capabilities"]))

    def test_safe_roots_resource_matches_safe_roots_tool_shape(self) -> None:
        response = request(5, "resources/read", {"uri": "starbridge://safe-roots"})
        payload = json.loads(response["result"]["contents"][0]["text"])
        self.assertEqual("safe_roots", payload["action"])
        paths = {item["path"] for item in payload["roots"]}
        self.assertIn("examples/output/photoshop", paths)

    def test_resources_read_unknown_uri_is_invalid_params(self) -> None:
        response = request(6, "resources/read", {"uri": "starbridge://does-not-exist"})
        self.assertIn("error", response)
        self.assertEqual(-32602, response["error"]["code"])

    def test_resources_read_requires_string_uri(self) -> None:
        response = request(7, "resources/read", {})
        self.assertIn("error", response)
        self.assertEqual(-32602, response["error"]["code"])


if __name__ == "__main__":
    unittest.main()
