from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "starbridge_mcp").is_dir():
        sys.path.insert(0, str(parent))
        break

from starbridge_mcp.bridges.illustrator_preflight import preflight_summary


def _load_summary(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a public-safe Illustrator preflight summary."
    )
    parser.add_argument("--summary-json", help="Optional sanitized document summary JSON.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = preflight_summary(_load_summary(args.summary_json))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("Illustrator preflight metadata summary")
    print("mode:", result["mode"])
    print("ok:", result["ok"])
    for check in result["checks"]:
        print(f"- {check['name']}: {check['ok']}")


if __name__ == "__main__":
    main()
