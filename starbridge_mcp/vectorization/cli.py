from __future__ import annotations

import argparse
import json

from .engine import RunConfig, VectorizationError, run_vectorization


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise VectorizationError(
            "invalid_arguments", "Required or supplied vectorization arguments are invalid."
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = SafeArgumentParser(
        description=(
            "Convert one explicit PNG/JPEG to verified raster-free SVG. "
            "Smart vector is the default mode."
        )
    )
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--mode",
        default="smart",
        help=(
            "smart (default), lightweight, exact, artisan; balanced is accepted as a smart alias"
        ),
    )
    parser.add_argument("--reference-id", default="vector-job")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--max-colors", type=int, default=None)
    parser.add_argument("--max-dimension", type=int, default=None)
    parser.add_argument("--simplify-ratio", type=float, default=None)
    parser.add_argument("--min-region-area", type=int, default=None)
    parser.add_argument("--alpha-threshold", type=int, default=None)
    parser.add_argument("--max-subpaths", type=int, default=None)
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--max-svg-size-mb", type=float, default=None)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print an agent-friendly summary; the full report is still saved to disk.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> RunConfig:
    return RunConfig(
        input_path=args.input,
        mode=args.mode,
        reference_id=args.reference_id,
        output_dir=args.output_dir,
        colors=args.max_colors,
        max_dimension=args.max_dimension,
        simplify_ratio=args.simplify_ratio,
        min_region_area=args.min_region_area,
        alpha_threshold=args.alpha_threshold,
        max_subpaths=args.max_subpaths,
        max_points=args.max_points,
        max_svg_size_mb=args.max_svg_size_mb,
    )


def compact_result(result: dict[str, object]) -> dict[str, object]:
    if not result.get("ok"):
        return result
    mode = result["mode"]
    vector = result["vector"]
    validation = result["validation"]
    structure = result.get("artisan_structure")
    assert isinstance(mode, dict)
    assert isinstance(vector, dict)
    assert isinstance(validation, dict)
    summary_fields = (
        "width",
        "height",
        "path_objects",
        "subpaths",
        "points",
        "svg_bytes",
        "anchor_reduction_ratio",
        "centerline_candidate_used",
        "centerline_anchor_reduction_ratio",
        "centerline_precision",
        "centerline_recall",
        "centerline_dice",
        "continuation_candidate_used",
        "continuation_path_reduction_ratio",
        "continuation_anchor_reduction_ratio",
        "continuation_batch_reduction_ratio",
        "continuation_mean_path_length_gain_ratio",
    )
    artifacts = result.get("artifacts")
    artifact_refs = (
        [
            {"role": item["role"], "path": item["path"]}
            for item in artifacts
            if isinstance(item, dict) and "role" in item and "path" in item
        ]
        if isinstance(artifacts, list)
        else []
    )
    return {
        "ok": True,
        "mode": mode["key"],
        "output_dir": result["output_dir"],
        "vector": {key: vector[key] for key in summary_fields if key in vector},
        "validation": {
            "svg_verified": validation["svg_verified"],
            "embedded_raster_count": validation["embedded_raster_count"],
            "external_reference_count": validation["external_reference_count"],
        },
        "edit_ref": structure.get("structure_ref") if isinstance(structure, dict) else None,
        "artifacts": artifact_refs,
        "elapsed_seconds": result["elapsed_seconds"],
    }


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        result = run_vectorization(config_from_args(args))
        if args.compact:
            result = compact_result(result)
    except VectorizationError as exc:
        result = {"ok": False, "error": {"code": exc.code, "message": str(exc)}}
    except Exception:
        result = {
            "ok": False,
            "error": {
                "code": "vectorization_failed",
                "message": "Vectorization failed before verified artifacts were published.",
            },
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
