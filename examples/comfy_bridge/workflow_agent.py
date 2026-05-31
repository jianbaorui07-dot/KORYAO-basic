from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any

from examples.comfy_bridge.validate_workflow import validate_workflow_payload
from starbridge_mcp.core.security import sanitize


BRIDGE_ID = "comfyui"
DEFAULT_BASE_URL = os.environ.get("STARBRIDGE_COMFYUI_URL") or os.environ.get("COMFY_BASE_URL", "http://127.0.0.1:8188")
DEFAULT_CHECKPOINT = os.environ.get("STARBRIDGE_COMFYUI_CHECKPOINT", "__checkpoint_name_required__")
DEFAULT_NEGATIVE_PROMPT = "low quality, blurry, distorted, bad anatomy, watermark, text"
SUPPORTED_WORKFLOW_TYPES = {"txt2img"}
REQUIRED_NODES = [
    "CheckpointLoaderSimple",
    "CLIPTextEncode_positive",
    "CLIPTextEncode_negative",
    "EmptyLatentImage",
    "KSampler",
    "VAEDecode",
    "SaveImage",
]


def _as_int(value: Any, default: int, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _as_float(value: Any, default: float, *, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _workflow_type(arguments: dict[str, Any]) -> str:
    requested = str(arguments.get("workflow_type") or "txt2img").strip().lower()
    return requested if requested in SUPPORTED_WORKFLOW_TYPES else "txt2img"


def _positive_prompt(arguments: dict[str, Any]) -> str:
    prompt = str(arguments.get("positive_prompt") or "").strip()
    if prompt:
        return prompt
    goal = str(arguments.get("goal") or "").strip()
    style = str(arguments.get("style") or "").strip()
    parts = [part for part in [goal, style, "high quality, detailed composition"] if part]
    return ", ".join(parts) if parts else "a high quality concept art scene"


def _negative_prompt(arguments: dict[str, Any]) -> str:
    return str(arguments.get("negative_prompt") or DEFAULT_NEGATIVE_PROMPT).strip()


def _checkpoint(arguments: dict[str, Any]) -> str:
    return str(arguments.get("checkpoint") or arguments.get("ckpt_name") or DEFAULT_CHECKPOINT).strip()


def _dimensions(arguments: dict[str, Any]) -> tuple[int, int]:
    return (
        _as_int(arguments.get("width"), 1024, minimum=64, maximum=4096),
        _as_int(arguments.get("height"), 1024, minimum=64, maximum=4096),
    )


def _sampler_settings(arguments: dict[str, Any]) -> dict[str, Any]:
    seed = arguments.get("seed")
    if seed is None and arguments.get("_random_seed"):
        seed = random.randint(1, 2**48)
    return {
        "seed": _as_int(seed, 123456789, minimum=0, maximum=2**63 - 1),
        "steps": _as_int(arguments.get("steps"), 20, minimum=1, maximum=150),
        "cfg": _as_float(arguments.get("cfg"), 7.0, minimum=1.0, maximum=30.0),
        "sampler_name": str(arguments.get("sampler_name") or arguments.get("sampler") or "euler"),
        "scheduler": str(arguments.get("scheduler") or "normal"),
        "denoise": _as_float(arguments.get("denoise"), 1.0, minimum=0.0, maximum=1.0),
    }


def workflow_hash(workflow: dict[str, Any]) -> str:
    canonical = json.dumps(workflow, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def workflow_summary(workflow: dict[str, Any]) -> dict[str, Any]:
    class_types: dict[str, int] = {}
    links = 0
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        class_type = str(node.get("class_type") or "unknown")
        class_types[class_type] = class_types.get(class_type, 0) + 1
        inputs = node.get("inputs", {})
        if isinstance(inputs, dict):
            links += sum(1 for value in inputs.values() if isinstance(value, list) and len(value) == 2)
    return {
        "node_count": len(workflow),
        "link_count": links,
        "class_types": dict(sorted(class_types.items())),
        "output_nodes": [
            node_id
            for node_id, node in workflow.items()
            if isinstance(node, dict) and node.get("class_type") == "SaveImage"
        ],
    }


def workflow_build_plan(arguments: dict[str, Any]) -> dict[str, Any]:
    workflow_type = _workflow_type(arguments)
    width, height = _dimensions(arguments)
    return sanitize(
        {
            "ok": True,
            "bridge": BRIDGE_ID,
            "action": "workflow_build_plan",
            "mode": "dry_run",
            "workflow_type": workflow_type,
            "goal": str(arguments.get("goal") or ""),
            "style": str(arguments.get("style") or ""),
            "width": width,
            "height": height,
            "required_nodes": REQUIRED_NODES,
            "will_build": False,
            "will_submit": False,
            "warnings": [] if workflow_type == "txt2img" else ["Only txt2img is implemented in this MVP."],
        }
    )


def build_txt2img_workflow(arguments: dict[str, Any]) -> dict[str, Any]:
    width, height = _dimensions(arguments)
    sampler = _sampler_settings(arguments)
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                **sampler,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": _checkpoint(arguments)},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": _positive_prompt(arguments), "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": _negative_prompt(arguments), "clip": ["4", 1]},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": str(arguments.get("filename_prefix") or "starbridge_agent_txt2img"), "images": ["8", 0]},
        },
    }


def workflow_build(arguments: dict[str, Any]) -> dict[str, Any]:
    workflow_type = _workflow_type(arguments)
    workflow = build_txt2img_workflow(arguments)
    validation = validate_workflow_payload(workflow, workflow_name="agent_generated_txt2img")
    return sanitize(
        {
            "ok": bool(validation.get("ok")),
            "bridge": BRIDGE_ID,
            "action": "workflow_build",
            "mode": "dry_run",
            "workflow_type": workflow_type,
            "workflow": workflow,
            "workflow_hash": workflow_hash(workflow),
            "node_summary": workflow_summary(workflow),
            "validation": validation,
            "will_submit": False,
            "warnings": [] if validation.get("ok") else validation.get("warnings", []),
            "next_steps": ["Review the workflow, then call comfyui.agent_run with confirm_run=true to submit."],
        }
    )


def _find_nodes(workflow: dict[str, Any], class_type: str) -> list[str]:
    return [node_id for node_id, node in workflow.items() if isinstance(node, dict) and node.get("class_type") == class_type]


def workflow_repair(arguments: dict[str, Any]) -> dict[str, Any]:
    source = arguments.get("workflow")
    base_arguments = {key: value for key, value in arguments.items() if key != "workflow"}
    repaired = build_txt2img_workflow(base_arguments)
    changes: list[str] = []

    if isinstance(source, dict):
        candidate = copy.deepcopy(source)
        for node_id, fallback_node in repaired.items():
            node = candidate.get(node_id)
            if not isinstance(node, dict) or node.get("class_type") != fallback_node["class_type"]:
                candidate[node_id] = copy.deepcopy(fallback_node)
                changes.append(f"recreated node {node_id}:{fallback_node['class_type']}")
            else:
                inputs = node.setdefault("inputs", {})
                if not isinstance(inputs, dict):
                    node["inputs"] = {}
                    inputs = node["inputs"]
                    changes.append(f"recreated inputs for node {node_id}")
                for input_name, fallback_value in fallback_node["inputs"].items():
                    if input_name not in inputs or inputs[input_name] in (None, ""):
                        inputs[input_name] = copy.deepcopy(fallback_value)
                        changes.append(f"filled {node_id}.{input_name}")
        repaired = candidate
    else:
        changes.append("created workflow from scratch")

    repaired["3"]["inputs"].update(_sampler_settings(repaired["3"].get("inputs", {})))
    repaired["5"]["inputs"]["width"], repaired["5"]["inputs"]["height"] = _dimensions(repaired["5"].get("inputs", {}))
    if not str(repaired["6"]["inputs"].get("text") or "").strip():
        repaired["6"]["inputs"]["text"] = _positive_prompt(base_arguments)
        changes.append("filled positive prompt")
    if not str(repaired["7"]["inputs"].get("text") or "").strip():
        repaired["7"]["inputs"]["text"] = _negative_prompt(base_arguments)
        changes.append("filled negative prompt")

    required_links = {
        ("3", "model"): ["4", 0],
        ("3", "positive"): ["6", 0],
        ("3", "negative"): ["7", 0],
        ("3", "latent_image"): ["5", 0],
        ("6", "clip"): ["4", 1],
        ("7", "clip"): ["4", 1],
        ("8", "samples"): ["3", 0],
        ("8", "vae"): ["4", 2],
        ("9", "images"): ["8", 0],
    }
    for (node_id, input_name), expected in required_links.items():
        inputs = repaired[node_id].setdefault("inputs", {})
        if inputs.get(input_name) != expected:
            inputs[input_name] = copy.deepcopy(expected)
            changes.append(f"repaired link {node_id}.{input_name}")

    validation = validate_workflow_payload(repaired, workflow_name="agent_repaired_txt2img")
    return sanitize(
        {
            "ok": bool(validation.get("ok")),
            "bridge": BRIDGE_ID,
            "action": "workflow_repair",
            "mode": "dry_run",
            "workflow_type": "txt2img",
            "workflow": repaired,
            "workflow_hash": workflow_hash(repaired),
            "node_summary": workflow_summary(repaired),
            "repairs": changes,
            "validation": validation,
            "will_submit": False,
        }
    )


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def get_json(base_url: str, path: str, timeout: int) -> dict[str, Any]:
    with urllib.request.urlopen(_url(base_url, path), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url: str, path: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        _url(base_url, path),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def output_manifest_from_history(prompt_id: str, history: dict[str, Any]) -> dict[str, Any]:
    prompt_history = history.get(prompt_id, {}) if isinstance(history, dict) else {}
    outputs = []
    for node_id, node_output in prompt_history.get("outputs", {}).items():
        for image in node_output.get("images", []):
            outputs.append(
                {
                    "node_id": str(node_id),
                    "filename": str(image.get("filename") or ""),
                    "subfolder": str(image.get("subfolder") or ""),
                    "type": str(image.get("type") or "output"),
                }
            )
    return sanitize({"prompt_id": prompt_id, "image_count": len(outputs), "images": outputs})


def query_job_status(base_url: str, prompt_id: str, timeout: int) -> dict[str, Any]:
    history = get_json(base_url, f"/history/{prompt_id}", timeout)
    if prompt_id in history:
        return {
            "state": "completed",
            "history_available": True,
            "output_manifest": output_manifest_from_history(prompt_id, history),
        }
    return {"state": "queued_or_running", "history_available": False, "output_manifest": {"prompt_id": prompt_id, "image_count": 0, "images": []}}


def submit_workflow(
    workflow: dict[str, Any],
    *,
    base_url: str,
    timeout: int,
    wait_seconds: int,
) -> dict[str, Any]:
    response = post_json(base_url, "/prompt", {"prompt": workflow}, timeout)
    prompt_id = str(response.get("prompt_id") or "")
    if not prompt_id:
        return {"ok": False, "error": "missing_prompt_id", "response": response}

    status = {"state": "submitted", "history_available": False, "output_manifest": {"prompt_id": prompt_id, "image_count": 0, "images": []}}
    deadline = time.time() + max(0, wait_seconds)
    while time.time() <= deadline:
        status = query_job_status(base_url, prompt_id, timeout)
        if status["state"] == "completed":
            break
        if wait_seconds <= 0:
            break
        time.sleep(1)
    return {"ok": True, "prompt_id": prompt_id, "job_status": status}


def agent_run(arguments: dict[str, Any]) -> dict[str, Any]:
    plan = workflow_build_plan(arguments)
    run_arguments = dict(arguments)
    if bool(run_arguments.get("confirm_run", False)) and run_arguments.get("seed") is None:
        run_arguments["_random_seed"] = True
    workflow = build_txt2img_workflow(run_arguments)
    validation = validate_workflow_payload(workflow, workflow_name="agent_generated_txt2img")
    repaired = None
    if not validation.get("ok"):
        repaired_result = workflow_repair({**arguments, "workflow": workflow})
        repaired = {
            "workflow_hash": repaired_result["workflow_hash"],
            "node_summary": repaired_result["node_summary"],
            "repairs": repaired_result["repairs"],
            "validation": repaired_result["validation"],
        }
        workflow = repaired_result["workflow"]
        validation = repaired_result["validation"]

    confirm_run = bool(arguments.get("confirm_run", False))
    if not confirm_run:
        return sanitize(
            {
                "ok": True,
                "bridge": BRIDGE_ID,
                "action": "agent_run",
                "mode": "dry_run",
                "workflow_type": _workflow_type(arguments),
                "build_plan": plan,
                "workflow_hash": workflow_hash(workflow),
                "node_summary": workflow_summary(workflow),
                "validation": validation,
                "repaired": repaired is not None,
                "submitted": False,
                "prompt_id": None,
                "job_status": {"state": "not_submitted"},
                "output_manifest": {"image_count": 0, "images": []},
                "warnings": ["Refusing to submit to ComfyUI without confirm_run=true."],
                "next_steps": ["Call again with confirm_run=true after reviewing the dry-run plan."],
            }
        )

    if not validation.get("ok"):
        return sanitize(
            {
                "ok": False,
                "bridge": BRIDGE_ID,
                "action": "agent_run",
                "mode": "confirmed",
                "workflow_type": _workflow_type(arguments),
                "submitted": False,
                "prompt_id": None,
                "validation": validation,
                "warnings": ["Workflow validation failed after repair; refusing to submit."],
                "next_steps": ["Inspect validation errors and call workflow_repair with explicit parameters."],
            }
        )

    base_url = str(arguments.get("comfy_url") or DEFAULT_BASE_URL)
    timeout = _as_int(arguments.get("timeout"), 30, minimum=1, maximum=300)
    wait_seconds = _as_int(arguments.get("wait_seconds", arguments.get("timeout_seconds")), 10, minimum=0, maximum=600)
    try:
        submission = submit_workflow(workflow, base_url=base_url, timeout=timeout, wait_seconds=wait_seconds)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        return sanitize(
            {
                "ok": False,
                "bridge": BRIDGE_ID,
                "action": "agent_run",
                "mode": "confirmed",
                "workflow_type": _workflow_type(arguments),
                "submitted": False,
                "prompt_id": None,
                "workflow_hash": workflow_hash(workflow),
                "job_status": {"state": "comfyui_unavailable"},
                "output_manifest": {"image_count": 0, "images": []},
                "warnings": [f"Unable to submit to ComfyUI: {exc}"],
                "next_steps": ["Start local ComfyUI, confirm the checkpoint placeholder is valid, then retry."],
            }
        )

    job_status = submission.get("job_status", {})
    return sanitize(
        {
            "ok": bool(submission.get("ok")),
            "bridge": BRIDGE_ID,
            "action": "agent_run",
            "mode": "confirmed",
            "workflow_type": _workflow_type(arguments),
            "submitted": bool(submission.get("ok")),
            "prompt_id": submission.get("prompt_id"),
            "workflow_hash": workflow_hash(workflow),
            "node_summary": workflow_summary(workflow),
            "validation": validation,
            "job_status": {key: value for key, value in job_status.items() if key != "output_manifest"},
            "output_manifest": job_status.get("output_manifest", {"image_count": 0, "images": []}),
            "warnings": [] if submission.get("ok") else [str(submission.get("error") or "ComfyUI submission failed.")],
            "next_steps": [] if submission.get("ok") else ["Inspect the ComfyUI response and local console."],
        }
    )
