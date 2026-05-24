from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from starbridge_mcp.core.config import StarBridgeConfig, env_summary
from starbridge_mcp.core.result_schema import make_result, validate_result
from starbridge_mcp.core.security import sanitize


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


BRIDGE_NAME_MAP = {
    "ComfyUI": "comfyui",
    "Blender": "blender",
    "CAD": "cad_autocad",
    "Photoshop": "photoshop",
    "Illustrator": "illustrator",
    "JianyingCapCut": "capcut_jianying",
}


def _legacy_status_to_ok(status: str) -> bool:
    return status == "ok"


def _next_steps_from_legacy(details: list[str], status: str) -> list[str]:
    steps = []
    for detail in details:
        if "处理建议" in detail or "下一步" in detail:
            steps.append(detail)
    if not steps and status != "ok":
        steps.append("根据 details 配置本机软件、环境变量或先手动启动对应桌面软件。")
    return steps


def normalize_legacy_status(result: dict[str, Any]) -> dict[str, Any]:
    name = str(result.get("name") or result.get("bridge_id") or "unknown")
    bridge = BRIDGE_NAME_MAP.get(name, name.lower())
    status = str(result.get("status") or ("ok" if result.get("ok") else "warn"))
    details_list = [str(item) for item in result.get("details", [])]
    warnings = []
    if status != "ok":
        warnings.append(str(result.get("status_label") or status))
    message = str(result.get("label") or name)
    unified = make_result(
        ok=_legacy_status_to_ok(status),
        bridge=bridge,
        action="status",
        message=f"{message}: {status}",
        details={
            "legacy_status": status,
            "legacy_name": name,
            "data": result.get("data", {}),
            "notes": details_list,
        },
        warnings=warnings,
        next_steps=_next_steps_from_legacy(details_list, status),
    )
    sanitized = sanitize(unified)
    validate_result(sanitized)
    return sanitized


def collect_status(*, comfy_url: str, timeout: int, probe_executables: bool) -> list[dict[str, Any]]:
    from examples import bridge_status as legacy

    legacy_results = [
        legacy.check_comfy(comfy_url, timeout),
        legacy.check_blender(probe_executables, timeout),
        legacy.check_cad(),
        legacy.check_photoshop(probe_executables),
        legacy.check_illustrator(probe_executables),
        legacy.check_jianying_capcut(),
    ]
    return [normalize_legacy_status(item) for item in legacy_results]


def build_response(args: argparse.Namespace) -> dict[str, Any]:
    config = StarBridgeConfig(timeout=args.timeout)
    comfy_url = args.comfy_url or config.comfy_url
    results = collect_status(
        comfy_url=comfy_url,
        timeout=args.timeout,
        probe_executables=args.probe_executables,
    )
    if args.bridge != "all":
        results = [item for item in results if item["bridge"] == args.bridge]
    return sanitize(
        {
            "ok": all(item["ok"] for item in results),
            "framework": "StarBridge",
            "action": "status",
            "results": results,
            "env": env_summary(),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="StarBridge 本地创意软件 MCP 桥接框架最小状态入口。")
    parser.add_argument("action", nargs="?", default="status", choices=["status"], help="当前实现 status。")
    parser.add_argument(
        "--bridge",
        default="all",
        choices=["all", "comfyui", "blender", "cad_autocad", "photoshop", "illustrator", "capcut_jianying"],
    )
    parser.add_argument("--comfy-url", default=None)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--probe-executables", action="store_true")
    parser.add_argument("--json", action="store_true", help="保留给兼容；当前始终输出 JSON。")
    parser.add_argument("--strict", action="store_true", help="任一 bridge 未通过时返回退出码 1。")
    args = parser.parse_args()

    response = build_response(args)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    if args.strict and any(not item["ok"] for item in response["results"]):
        raise SystemExit(1)


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        raise SystemExit("建议使用 Python 3.10 或更新版本运行 StarBridge。")
    main()
