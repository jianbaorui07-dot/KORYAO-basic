import importlib.metadata
import json
import sys

VECTOR60_RUNTIME_VERSIONS = {
    "vtracer": "0.6.15",
    "skia-pathops": "0.9.2",
    "svgpathtools": "1.7.2",
}


def vector60_runtime_check() -> None:
    import pathops  # noqa: F401
    import svgpathtools  # noqa: F401
    import vtracer  # noqa: F401

    actual = {name: importlib.metadata.version(name) for name in VECTOR60_RUNTIME_VERSIONS}
    if actual != VECTOR60_RUNTIME_VERSIONS:
        raise RuntimeError(
            f"Vector60 runtime mismatch: expected {VECTOR60_RUNTIME_VERSIONS}, got {actual}"
        )
    print(json.dumps({"ok": True, "versions": actual}, sort_keys=True))


if __name__ == "__main__":
    if sys.argv[1:] == ["--vector60-runtime-check"]:
        vector60_runtime_check()
    elif sys.argv[1:] == ["--mcp"]:
        from starbridge_mcp.mcp_server import main as mcp_main

        mcp_main()
    else:
        from starbridge_mcp.backend import main as backend_main

        backend_main()
