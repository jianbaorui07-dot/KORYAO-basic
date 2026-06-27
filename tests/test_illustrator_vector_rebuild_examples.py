from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTOR_REBUILD_DIR = REPO_ROOT / "examples" / "illustrator_bridge" / "vector_rebuild"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


extract_vector_lines = load_module(
    "extract_vector_lines", VECTOR_REBUILD_DIR / "extract_vector_lines.py"
)
reduce_closed_contours = load_module(
    "reduce_closed_contours", VECTOR_REBUILD_DIR / "reduce_closed_contours.py"
)


class IllustratorVectorRebuildExamplesTest(unittest.TestCase):
    def test_help_does_not_require_optional_geometry_dependencies(self) -> None:
        scripts = (
            VECTOR_REBUILD_DIR / "extract_vector_lines.py",
            VECTOR_REBUILD_DIR / "reduce_closed_contours.py",
        )
        for script in scripts:
            with self.subTest(script=script.name):
                completed = subprocess.run(
                    [sys.executable, str(script), "--help"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self.assertIn("usage:", completed.stdout)

    def test_extract_path_data_reports_line_and_curve_lengths(self) -> None:
        items = [
            ("l", type("P", (), {"x": 0, "y": 0})(), type("P", (), {"x": 3, "y": 4})()),
            (
                "c",
                type("P", (), {"x": 0, "y": 0})(),
                type("P", (), {"x": 1, "y": 0})(),
                type("P", (), {"x": 2, "y": 1})(),
                type("P", (), {"x": 3, "y": 1})(),
            ),
        ]

        path_d, length = extract_vector_lines.path_data_and_length(items, samples_per_curve=6)

        self.assertIn("L 3.0000 4.0000", path_d)
        self.assertIn("C 1.0000 0.0000", path_d)
        self.assertGreater(length, 5.0)

    def test_closed_contour_modes_are_distinct(self) -> None:
        coarse = reduce_closed_contours.parameters_for_mode("coarse")
        fine = reduce_closed_contours.parameters_for_mode("fine")
        outer = reduce_closed_contours.parameters_for_mode("outer-only")

        self.assertGreater(coarse["dilate_px"], fine["dilate_px"])
        self.assertEqual(coarse, outer)


if __name__ == "__main__":
    unittest.main()
