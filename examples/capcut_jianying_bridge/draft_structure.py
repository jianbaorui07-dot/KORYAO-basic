from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "starbridge_mcp").is_dir():
        sys.path.insert(0, str(parent))
        break

from starbridge_mcp.bridges.capcut_draft_structure import draft_structure_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Jianying / CapCut draft directories without reading draft content.")
    parser.add_argument("--max-entries", type=int, default=25)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = draft_structure_summary(max_entries=args.max_entries)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("Jianying / CapCut draft structure summary")
    print("mode:", result["mode"])
    print("ok:", result["ok"])
    for root in result["roots"]:
        print(f"- {root['env']}: exists={root['exists']}, sample_entries={root['entry_count_sample']}")


if __name__ == "__main__":
    main()
