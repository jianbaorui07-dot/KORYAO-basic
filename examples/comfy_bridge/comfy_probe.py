from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


DEFAULT_BASE_URL = os.environ.get("COMFY_BASE_URL", "http://127.0.0.1:8188")


def build_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def get_json(base_url: str, path: str, timeout: int):
    with urllib.request.urlopen(build_url(base_url, path), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_checkpoint_names(base_url: str, timeout: int) -> list[str]:
    loader = get_json(base_url, "/object_info/CheckpointLoaderSimple", timeout)
    return loader["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]


def build_status(base_url: str, timeout: int) -> dict:
    stats = get_json(base_url, "/system_stats", timeout)
    queue = get_json(base_url, "/queue", timeout)
    checkpoints = get_checkpoint_names(base_url, timeout)
    return {
        "base_url": base_url,
        "version": stats.get("system", {}).get("comfyui_version"),
        "python": stats.get("system", {}).get("python_version"),
        "devices": stats.get("devices", []),
        "checkpoints": checkpoints,
        "queue_running": len(queue.get("queue_running", [])),
        "queue_pending": len(queue.get("queue_pending", [])),
    }


def print_text_report(status: dict) -> None:
    print("ComfyUI API:", status["base_url"])
    print("Version:", status.get("version"))
    print("Python:", status.get("python"))

    for device in status.get("devices", []):
        print("Device:", device.get("name"))
        print("VRAM free:", device.get("vram_free"))

    print("Checkpoints:")
    for name in status["checkpoints"]:
        print("-", name)

    print("Queue running:", status["queue_running"])
    print("Queue pending:", status["queue_pending"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Read local ComfyUI status and available checkpoints.")
    parser.add_argument("--comfy-url", default=DEFAULT_BASE_URL, help="ComfyUI API base URL.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP request timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        status = build_status(args.comfy_url, args.timeout)
    except (urllib.error.URLError, TimeoutError, OSError, KeyError) as exc:
        error = {
            "base_url": args.comfy_url,
            "status": "missing",
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(error, ensure_ascii=False, indent=2))
        raise SystemExit(f"ComfyUI is not reachable or returned an unexpected response: {exc}") from exc

    if args.json:
        print(json.dumps({"status": "ok", **status}, ensure_ascii=False, indent=2))
    else:
        print_text_report(status)


if __name__ == "__main__":
    main()
