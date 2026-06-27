"""StarBridge MCP prompts.

Prompts are the third MCP primitive (alongside tools and resources). They let a
server expose reusable, parameterized prompt templates that clients can surface
as slash commands. StarBridge prompts bake the safe-by-default protocol
(read-only first, dry-run, explicit confirmation, sandbox-only writes) directly
into each template so an agent starts from a safe plan instead of a blank call.

Every prompt is text-only, generated in-process, network free, and free of
private paths.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from starbridge_mcp.core.security import sanitize

JsonObject = dict[str, Any]

_SAFE_FOOTER = (
    "安全约束：默认只读 / dry-run；真实写入或导出必须显式确认"
    "（confirm_write / confirm_export / confirm_run），且输出只能落在声明的 sandbox 根目录；"
    "不打开私有 PSD/AI/DWG/.blend/草稿/模型/客户素材，不登录、不支付、不绕过授权。"
)


def _arg(name: str, description: str, *, required: bool = False) -> JsonObject:
    return {"name": name, "description": description, "required": required}


def _messages(text: str) -> list[JsonObject]:
    return [{"role": "user", "content": {"type": "text", "text": text}}]


def _bridge_status_check(arguments: JsonObject) -> str:
    bridge = str(arguments.get("bridge") or "all").strip() or "all"
    if bridge == "all":
        target = "所有本地创意软件 bridge"
        call = "请调用 `starbridge.status`（bridge=all）"
    else:
        target = f"`{bridge}` bridge"
        call = f"请调用 `starbridge.probe`（bridge={bridge}）"
    return (
        f"{call}，对 {target} 做只读状态检查。"
        "只输出统一 JSON 摘要（ok、bridge、action、message、warnings、next_steps）。"
        "若某个软件未安装或未启动，请用 warnings 和 next_steps 说明，不要报错中断。"
        f"\n\n{_SAFE_FOOTER}"
    )


def _comfyui_safe_workflow(arguments: JsonObject) -> str:
    goal = str(arguments.get("goal") or "（未提供目标，请先向用户确认）").strip()
    workflow_type = str(arguments.get("workflow_type") or "txt2img").strip() or "txt2img"
    return (
        f"目标：{goal}\n工作流类型：{workflow_type}\n\n"
        "请按 validate-first 顺序操作，不要直接提交生成任务：\n"
        f"1. 调用 `comfy.workflow_draft`（task_type={workflow_type}）生成安全占位草案。\n"
        "2. 调用 `comfyui.workflow_validate` 校验草案是否为合法 /prompt API 格式。\n"
        "3. 如需检查本机服务，调用 `comfyui.system_probe`（只读，不提交）。\n"
        "4. 如要真实生成，调用 `comfyui.agent_run` 并保持默认 dry-run；"
        "只有用户明确同意后才设 confirm_run=true。\n"
        "不要读取模型目录或私有图片，不要输出生成图片的真实路径。"
        f"\n\n{_SAFE_FOOTER}"
    )


def _cad_dxf_from_spec(arguments: JsonObject) -> str:
    spec = str(arguments.get("spec") or "（未提供 spec，请先向用户确认零件尺寸和图层）").strip()
    return (
        f"CAD 需求 / spec：{spec}\n\n"
        "请按离线 DXF 流程操作，默认不写真实文件：\n"
        "1. 调用 `autocad_dxf.create_dxf_plan`（prompt_or_spec=上面的 spec）生成可审查 plan。\n"
        "2. 调用 `autocad_dxf.validate_cad_plan` 校验单位、图层和实体结构。\n"
        "3. 调用 `autocad_dxf.summarize_plan` 汇总图层和实体数量供复核。\n"
        "4. 调用 `autocad_dxf.write_dxf` 并保持 dry_run=true 预览；"
        "真实写入需 confirm_write=true，且 output_path 必须位于 examples/cad/output。\n"
        "不要打开客户 DWG/DXF，不要控制真实 AutoCAD。"
        f"\n\n{_SAFE_FOOTER}"
    )


def _photoshop_recipe_run(arguments: JsonObject) -> str:
    recipe_id = str(arguments.get("recipe_id") or "sandbox_demo_preview").strip()
    return (
        f"Photoshop recipe：{recipe_id}\n\n"
        "请按受控 recipe 流程操作，默认 dry-run：\n"
        "1. 调用 `photoshop.recipe_list` 确认 recipe 可用及其安全边界。\n"
        f"2. 调用 `photoshop.recipe_plan`（recipe_id={recipe_id}）查看计划、输出清单和质量门。\n"
        "3. 调用 `photoshop.recipe_validate` 校验 sandbox 输出边界和 manifest 门。\n"
        f"4. 调用 `photoshop.recipe_run`（recipe_id={recipe_id}）并保持 dry_run=true；"
        "真实写入需 confirm_write=true，输出只能落在 examples/output/photoshop。\n"
        "不要在客户原始 PSD 上操作，只在 sandbox 副本上执行。"
        f"\n\n{_SAFE_FOOTER}"
    )


def _safe_write_protocol(_arguments: JsonObject) -> str:
    return (
        "在调用任何 StarBridge 写入 / 导出 / 启动本机软件的工具前，请遵守安全协议：\n"
        "1. 先用只读 / probe / validate / plan 工具理解现状。\n"
        "2. 写入类工具默认 dry_run=true，先预览计划和输出清单。\n"
        "3. 真实动作需显式确认（confirm_write / confirm_export / confirm_run），"
        "缺少确认时工具会返回 ok=false 并拒绝。\n"
        "4. 写入路径必须留在声明的 sandbox / ignored output 根目录"
        "（参见 `starbridge://safe-roots` 资源）。\n"
        "5. 禁止：自动登录、支付、上传客户素材、删除文件、绕过验证码 / 付费墙 / 授权。\n"
        "可先读取 `starbridge://safety-policy` 资源和 `starbridge.tools` 能力清单。"
    )


# name -> (title, description, arguments, builder)
_PROMPT_TABLE: tuple[tuple[str, str, str, list[JsonObject], Callable[[JsonObject], str]], ...] = (
    (
        "bridge_status_check",
        "Bridge Status Check",
        "生成对一个或全部 bridge 做只读状态检查的安全提示词。",
        [
            _arg(
                "bridge",
                "要检查的 bridge（comfyui/photoshop/illustrator/blender/autocad/autocad_dxf/jianying_capcut），缺省为 all。",
            )
        ],
        _bridge_status_check,
    ),
    (
        "comfyui_safe_workflow",
        "ComfyUI Safe Workflow",
        "生成 ComfyUI 的 validate-first 工作流提示词，默认不提交生成任务。",
        [
            _arg("goal", "图像生成目标描述。", required=True),
            _arg("workflow_type", "工作流类型：txt2img/img2img/inpaint/upscale，缺省 txt2img。"),
        ],
        _comfyui_safe_workflow,
    ),
    (
        "cad_dxf_from_spec",
        "CAD DXF From Spec",
        "生成离线 DXF 出图提示词：plan → validate → summarize → dry-run write。",
        [_arg("spec", "自然语言需求或结构化 CAD plan。", required=True)],
        _cad_dxf_from_spec,
    ),
    (
        "photoshop_recipe_run",
        "Photoshop Recipe Run",
        "生成受控 Photoshop recipe 提示词：list → plan → validate → dry-run run。",
        [_arg("recipe_id", "recipe 标识，缺省 sandbox_demo_preview。")],
        _photoshop_recipe_run,
    ),
    (
        "safe_write_protocol",
        "Safe Write Protocol",
        "返回 StarBridge 通用安全写入协议提示词，无需参数。",
        [],
        _safe_write_protocol,
    ),
)

_PROMPT_BUILDERS = {name: builder for (name, _t, _d, _a, builder) in _PROMPT_TABLE}


def list_prompts() -> list[JsonObject]:
    """Return the MCP prompts/list payload entries."""
    return [
        {
            "name": name,
            "title": title,
            "description": description,
            "arguments": arguments,
        }
        for (name, title, description, arguments, _builder) in _PROMPT_TABLE
    ]


def get_prompt(name: str, arguments: JsonObject | None = None) -> JsonObject | None:
    """Return the MCP prompts/get payload for a prompt, or None if unknown."""
    builder = _PROMPT_BUILDERS.get(name)
    if builder is None:
        return None
    text = builder(arguments or {})
    description = next((desc for (n, _t, desc, _a, _b) in _PROMPT_TABLE if n == name), name)
    return sanitize({"description": description, "messages": _messages(text)})
