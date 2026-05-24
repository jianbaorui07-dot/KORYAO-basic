from __future__ import annotations

import unittest

from starbridge_mcp.core.result_schema import REQUIRED_RESULT_FIELDS, make_result, validate_result
from starbridge_mcp.server import normalize_legacy_status


class StarBridgeSchemaTests(unittest.TestCase):
    def test_make_result_contains_required_fields(self) -> None:
        result = make_result(ok=True, bridge="comfyui", action="status", message="ready")
        self.assertEqual(tuple(result.keys()), REQUIRED_RESULT_FIELDS)
        validate_result(result)

    def test_legacy_status_normalizes_to_schema(self) -> None:
        result = normalize_legacy_status(
            {
                "name": "ComfyUI",
                "label": "ComfyUI 图像生成桥",
                "status": "warn",
                "status_label": "需配置",
                "details": ["处理建议：先启动 ComfyUI。"],
                "data": {"base_url": "http://127.0.0.1:8188"},
            }
        )
        validate_result(result)
        self.assertFalse(result["ok"])
        self.assertEqual(result["bridge"], "comfyui")
        self.assertEqual(result["action"], "status")
        self.assertTrue(result["next_steps"])


if __name__ == "__main__":
    unittest.main()
