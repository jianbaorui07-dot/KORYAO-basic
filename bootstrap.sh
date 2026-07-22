#!/usr/bin/env bash
# Cross-platform bootstrap for the safe Python/MCP path. It deliberately does
# not install system packages or start the Tauri desktop runtime.
set -euo pipefail

profile="auto"
skip_node=0
skip_codex_config=0
dry_run=0
json=0

step_names=()
step_statuses=()
step_details=()
warnings=()

usage() {
    cat <<'EOF'
Usage: bash ./bootstrap.sh [options]

Create a repository-local Python environment, install the selected public
CreNexus extras, write the safe local Codex MCP configuration, and run the
safe Python checks.

Options:
  --profile PROFILE       auto, core, standard, or all (default: auto)
  --skip-node             Do not install optional Node bridge dependencies
  --skip-codex-config     Do not write .codex/config.toml
  --dry-run               Show the planned reversible operations only
  --json                  Emit a machine-readable result
  -h, --help              Show this help

macOS notes: Homebrew, Xcode Command Line Tools, Rosetta, and desktop software
are never installed or changed by this script. The script only reports missing
prerequisites and continues with the safe core path when possible. It never
invokes the Tauri desktop application or npm.cmd.
EOF
}

die() {
    printf 'CreNexus bootstrap failed: %s\n' "$*" >&2
    exit 1
}

warn() {
    warnings+=("$1")
    if (( ! json )); then
        printf 'WARN: %s\n' "$1" >&2
    fi
}

add_step() {
    step_names+=("$1")
    step_statuses+=("$2")
    step_details+=("$3")
}

command_display() {
    local part separator=""
    for part in "$@"; do
        printf '%s' "$separator"
        if [[ "$part" == *[[:space:]]* ]]; then
            printf '"%s"' "${part//\"/\\\"}"
        else
            printf '%s' "$part"
        fi
        separator=" "
    done
}

run_step() {
    local name="$1"
    shift
    local detail
    detail="$(command_display "$@")"

    if (( dry_run )); then
        add_step "$name" "planned" "$detail"
        return
    fi

    if (( json )); then
        local captured
        if ! captured="$("$@" 2>&1)"; then
            die "$name failed: $captured"
        fi
        add_step "$name" "completed" "${captured##*$'\n'}"
        return
    fi

    "$@"
    add_step "$name" "completed" "$detail"
}

toml_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '%s' "$value"
}

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/\\r}"
    value="${value//$'\t'/\\t}"
    printf '%s' "$value"
}

json_string_array() {
    local value
    local first=1
    printf '['
    for value in "$@"; do
        (( first )) || printf ','
        first=0
        printf '"%s"' "$(json_escape "$value")"
    done
    printf ']'
}

json_steps() {
    local index
    printf '['
    for index in "${!step_names[@]}"; do
        (( index == 0 )) || printf ','
        printf '{"name":"%s","status":"%s","detail":"%s"}' \
            "$(json_escape "${step_names[index]}")" \
            "$(json_escape "${step_statuses[index]}")" \
            "$(json_escape "${step_details[index]}")"
    done
    printf ']'
}

emit_result() {
    local codex_config_json="null"
    if (( ! skip_codex_config )); then
        codex_config_json='".codex/config.toml"'
    fi

    if (( json )); then
        printf '{\n'
        printf '  "ok": true,\n'
        printf '  "repo": "%s",\n' "$(json_escape "$repo_root")"
        printf '  "profile_requested": "%s",\n' "$(json_escape "$profile")"
        printf '  "profile_applied": "%s",\n' "$(json_escape "$effective_profile")"
        printf '  "python": "%s",\n' "$(json_escape "$python_version")"
        printf '  "venv": ".venv/bin/python",\n'
        printf '  "extras": '
        json_string_array "${extras[@]}"
        printf ',\n  "codex_config": %s,\n' "$codex_config_json"
        printf '  "steps": '
        json_steps
        printf ',\n  "warnings": '
        json_string_array "${warnings[@]}"
        printf ',\n  "next": ["Open a new Codex task in this repository so it reloads .codex/config.toml.","Use the version coordinator to probe capabilities; software version is advisory, not a whitelist.","Run bash ./bootstrap.sh --profile standard or --profile all when you need optional bridge dependencies."]\n'
        printf '}\n'
        return
    fi

    printf 'CreNexus bootstrap completed (%s).\n' "$effective_profile"
    printf 'Python: %s\n' "$python_version"
    printf 'Virtual environment: %s\n' "$venv_path"
    if (( skip_codex_config )); then
        printf 'Codex config: skipped\n'
    else
        printf 'Codex config: %s\n' "$config_path"
    fi
    local index
    for index in "${!step_names[@]}"; do
        printf -- '- %s: %s\n' "${step_names[index]}" "${step_statuses[index]}"
    done
    printf 'Next: start a new Codex task in this repository.\n'
}

feature_hint_present() {
    local name
    for name in PHOTOSHOP_EXE ILLUSTRATOR_EXE AUTOCAD_EXE BLENDER_EXE COMFY_ROOT \
        STARBRIDGE_COMFYUI_URL JIANYING_EXE CAPCUT_EXE; do
        if [[ -n "${!name:-}" ]]; then
            return 0
        fi
    done
    for name in blender acad photoshop illustrator jianying capcut; do
        if command -v "$name" >/dev/null 2>&1; then
            return 0
        fi
    done
    return 1
}

find_python() {
    local candidate version major minor
    for candidate in python3 python; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        version="$($candidate --version 2>&1 || true)"
        if [[ "$version" =~ Python[[:space:]]+([0-9]+)\.([0-9]+) ]]; then
            major="${BASH_REMATCH[1]}"
            minor="${BASH_REMATCH[2]}"
            if (( major > 3 || (major == 3 && minor >= 10) )); then
                python_command="$candidate"
                python_version="$version"
                return
            fi
        fi
    done
    die "Python 3.10+ was not found. Install Python manually, then run this command again."
}

validate_repository_path() {
    local control_byte control_code escaped
    # NUL cannot appear in a POSIX path. Reject the other C0 controls and DEL
    # before building TOML so a failed bootstrap leaves configuration untouched.
    for control_code in {1..31} 127; do
        printf -v escaped '\\%03o' "$control_code"
        printf -v control_byte '%b' "$escaped"
        if [[ "$repo_root" == *"$control_byte"* ]]; then
            die "Repository paths containing ASCII control characters are not supported; rename or move the checkout before bootstrapping."
        fi
    done
}

check_platform_prerequisites() {
    local platform architecture
    platform="$(uname -s)"
    architecture="$(uname -m)"
    case "$platform" in
        Darwin|Linux) ;;
        *) die "Unsupported platform: $platform. Use bootstrap.ps1 on Windows." ;;
    esac

    if ! command -v git >/dev/null 2>&1; then
        warn "Git was not found. Bootstrap can continue, but clone/update operations must be done manually."
    fi

    if [[ "$platform" == "Darwin" ]]; then
        if ! command -v brew >/dev/null 2>&1; then
            warn "Homebrew was not found. It is optional and will not be installed automatically; install Python/Node manually if they are missing."
        fi
        if ! xcode-select -p >/dev/null 2>&1; then
            warn "Xcode Command Line Tools were not found. They are not installed automatically; some native Python packages may require a manual installation."
        fi
        if [[ "$architecture" == "arm64" ]] && ! /usr/bin/arch -x86_64 /usr/bin/true >/dev/null 2>&1; then
            warn "Rosetta 2 is unavailable. It is only needed for Intel-only third-party tools and will not be installed automatically."
        fi
    fi
}

toml_file_is_valid() {
    local file_path="$1"
    "$venv_python" - "$file_path" >/dev/null 2>&1 <<'PY'
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

with Path(sys.argv[1]).open("rb") as source:
    tomllib.load(source)
PY
}

managed_markers_are_valid() {
    local file_path="$1"
    awk '
        BEGIN { markers = 0; inside = 0 }
        /^# BEGIN STARBRIDGE QUICKSTART/ {
            if (inside || markers >= 1) { exit 1 }
            inside = 1
            markers++
            next
        }
        /^# END STARBRIDGE QUICKSTART/ {
            if (!inside) { exit 1 }
            inside = 0
            next
        }
        { next }
        END { if (inside) { exit 1 } }
    ' "$file_path" >/dev/null
}

external_mcp_config_is_unclaimed() {
    local file_path="$1"
    "$venv_python" - "$file_path" >/dev/null 2>&1 <<'PY'
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

with Path(sys.argv[1]).open("rb") as source:
    document = tomllib.load(source)

servers = document.get("mcp_servers")
if servers is not None:
    if not isinstance(servers, dict):
        raise SystemExit(1)
    if "starbridge" in servers or "starbridge-version-coordinator" in servers:
        raise SystemExit(1)
PY
}

write_codex_config() {
    if (( skip_codex_config )); then
        add_step "configure Codex MCP" "skipped" "--skip-codex-config"
        return
    fi
    if (( dry_run )); then
        add_step "configure Codex MCP" "planned" "$config_path"
        return
    fi

    if [[ -f "$config_path" ]]; then
        if ! toml_file_is_valid "$config_path"; then
            die "Existing .codex/config.toml is not valid TOML; no configuration changes were made."
        fi
        if ! managed_markers_are_valid "$config_path"; then
            die "Existing .codex/config.toml has an unclosed or repeated STARBRIDGE QUICKSTART block; no configuration changes were made."
        fi
    fi

    mkdir -p -- "$config_dir"
    local temporary_config
    temporary_config="$(mktemp "$config_dir/.config.toml.XXXXXX")"
    if [[ -f "$config_path" ]]; then
        if ! awk '
            /^# BEGIN STARBRIDGE QUICKSTART/ { inside = 1; next }
            /^# END STARBRIDGE QUICKSTART/ { inside = 0; next }
            !inside { print }
        ' "$config_path" > "$temporary_config"; then
            rm -f -- "$temporary_config"
            die "Could not prepare .codex/config.toml for a safe update; no configuration changes were made."
        fi
    else
        : > "$temporary_config"
    fi

    if ! toml_file_is_valid "$temporary_config"; then
        rm -f -- "$temporary_config"
        die "Existing .codex/config.toml outside the managed block is not valid TOML; no configuration changes were made."
    fi
    if ! external_mcp_config_is_unclaimed "$temporary_config"; then
        rm -f -- "$temporary_config"
        die "Existing .codex/config.toml already defines a Starbridge MCP server or a conflicting mcp_servers structure; refusing to overwrite it."
    fi

    local python_toml root_toml coordinator_toml
    python_toml="$(toml_escape "$venv_python")"
    root_toml="$(toml_escape "$repo_root")"
    coordinator_toml="$(toml_escape "$repo_root/plugins/starbridge-version-coordinator/scripts/version_coordinator_mcp.py")"
    if ! cat >> "$temporary_config" <<EOF

# BEGIN STARBRIDGE QUICKSTART (managed by bootstrap.sh)
[mcp_servers.starbridge]
command = "$python_toml"
args = ["-m", "starbridge_mcp.mcp_server"]
cwd = "$root_toml"

[mcp_servers.starbridge.env]
STARBRIDGE_PHOTOSHOP_SAFE_ONLY = "1"
STARBRIDGE_PHOTOSHOP_DEFAULT_DRY_RUN = "1"
STARBRIDGE_PHOTOSHOP_ALLOW_DESTRUCTIVE = "0"

[mcp_servers.starbridge-version-coordinator]
command = "$python_toml"
args = ["$coordinator_toml"]
cwd = "$root_toml"
# END STARBRIDGE QUICKSTART
EOF
    then
        rm -f -- "$temporary_config"
        die "Could not generate .codex/config.toml; no configuration changes were made."
    fi
    if ! toml_file_is_valid "$temporary_config"; then
        rm -f -- "$temporary_config"
        die "Generated .codex/config.toml is not valid TOML; no configuration changes were made."
    fi
    if ! mv -- "$temporary_config" "$config_path"; then
        rm -f -- "$temporary_config"
        die "Could not atomically replace .codex/config.toml; no configuration changes were made."
    fi
    add_step "configure Codex MCP" "completed" "$config_path"
}

install_node_bridges() {
    if (( skip_node )); then
        add_step "install optional Node bridge dependencies" "skipped" "--skip-node"
        return
    fi
    if [[ "$effective_profile" != "standard" && "$effective_profile" != "all" ]]; then
        add_step "install optional Node bridge dependencies" "skipped_profile" "$effective_profile"
        return
    fi
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
        warn "Node.js/npm were not found; optional Node bridge dependencies were not installed. Python/MCP flows remain available."
        return
    fi

    local proxy_root package_lock
    for proxy_root in "$repo_root/node_proxy/photoshop-bridge" "$repo_root/node_proxy/illustrator-bridge"; do
        [[ -f "$proxy_root/package.json" ]] || continue
        package_lock="$proxy_root/package-lock.json"
        if [[ -f "$package_lock" ]]; then
            run_step "install Node bridge $(basename "$proxy_root")" npm ci --prefix "$proxy_root" --no-audit --no-fund
        else
            run_step "install Node bridge $(basename "$proxy_root")" npm install --prefix "$proxy_root" --no-package-lock --no-audit --no-fund
        fi
    done
}

while (( $# > 0 )); do
    case "$1" in
        --profile)
            (( $# >= 2 )) || die "--profile requires a value"
            profile="$2"
            shift 2
            ;;
        --profile=*)
            profile="${1#*=}"
            shift
            ;;
        --skip-node)
            skip_node=1
            shift
            ;;
        --skip-codex-config)
            skip_codex_config=1
            shift
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        --json)
            json=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

case "$profile" in
    auto|core|standard|all) ;;
    *) die "Invalid profile '$profile'. Choose auto, core, standard, or all." ;;
esac

script_dir="$(cd -L -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -L)"
repo_root="$script_dir"
[[ -f "$repo_root/pyproject.toml" && -f "$repo_root/package.json" && -d "$repo_root/starbridge_mcp" ]] \
    || die "bootstrap.sh must run from a CreNexus repository checkout."

validate_repository_path
check_platform_prerequisites
find_python

effective_profile="$profile"
if [[ "$profile" == "auto" ]]; then
    if feature_hint_present; then
        effective_profile="standard"
    else
        effective_profile="core"
    fi
fi

extras=(dev vectorization)
if [[ "$effective_profile" == "standard" || "$effective_profile" == "all" ]]; then
    extras+=(cad comfy adobe illustrator-vector)
fi
if [[ "$effective_profile" == "all" ]]; then
    extras+=(illustrator-trace vector-refinement vector-app)
fi
extras_csv="$(IFS=,; printf '%s' "${extras[*]}")"

venv_path="$repo_root/.venv"
venv_python="$venv_path/bin/python"
config_dir="$repo_root/.codex"
config_path="$config_dir/config.toml"

if [[ -d "$venv_path" ]]; then
    if (( ! dry_run )) && [[ ! -x "$venv_python" ]]; then
        die "The virtual environment exists but does not contain $venv_python. Remove it manually only if it is safe to do so, then rerun."
    fi
    add_step "create virtual environment" "skipped_existing" "$venv_path"
else
    run_step "create virtual environment" "$python_command" -m venv "$venv_path"
fi

run_step "upgrade pip" "$venv_python" -m pip install --upgrade pip
run_step "install Python extras" "$venv_python" -m pip install ".[${extras_csv}]"
install_node_bridges
write_codex_config

if [[ "$effective_profile" == "standard" || "$effective_profile" == "all" ]]; then
    warn "Desktop software is not probed, installed, opened, or granted permissions by bootstrap.sh; verify optional desktop capabilities separately."
fi

run_step "verify Python package" "$venv_python" -c "import starbridge_mcp; print('starbridge_mcp import: ok')"
run_step "verify version coordinator" "$venv_python" "$repo_root/plugins/starbridge-version-coordinator/scripts/version_coordinator_mcp.py" self-test
run_step "verify safe MCP tools" "$venv_python" -m starbridge_mcp.server tools --json --safe-only

emit_result
