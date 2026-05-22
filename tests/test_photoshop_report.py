from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from examples.photoshop_bridge.write_practice_report import (  # noqa: E402
    artifact_info,
    png_dimensions,
    render_artifact_table,
)


def minimal_png(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)


class PhotoshopReportTest(unittest.TestCase):
    def test_png_dimensions_reads_header_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.png"
            path.write_bytes(minimal_png(320, 240))

            self.assertEqual(png_dimensions(path), (320, 240))

    def test_artifact_info_records_png_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "demo.png"
            path.write_bytes(minimal_png(640, 480))

            info = artifact_info("测试图片", str(path))

            self.assertTrue(info["exists"])
            self.assertEqual(info["png_width"], 640)
            self.assertEqual(info["png_height"], 480)
            self.assertEqual(len(info["sha256"]), 64)

    def test_artifact_table_contains_chinese_headers(self) -> None:
        rows = render_artifact_table(
            [
                {
                    "role": "测试图片",
                    "path": "D:/demo.png",
                    "exists": True,
                    "bytes": 123,
                    "sha256": "abcdef1234567890",
                    "png_width": 10,
                    "png_height": 20,
                }
            ]
        )
        table = "\n".join(rows)

        self.assertIn("产物", table)
        self.assertIn("图片尺寸", table)
        self.assertIn("10 x 20", table)


if __name__ == "__main__":
    unittest.main()
