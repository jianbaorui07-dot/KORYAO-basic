from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

SENSITIVE_FILE_EXTENSIONS = {
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".psd",
    ".ai",
    ".ait",
    ".dwg",
    ".dxf",
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".prproj",
    ".aep",
    ".aepx",
}
SENSITIVE_FILENAMES = {"draft_content.json", "draft_info.json"}
PRIVATE_PATH_PARTS = {"appdata", "desktop", "documents"}
SENSITIVE_KEYWORDS = (
    "password",
    "token",
    "cookie",
    "oauth",
    "secret",
    "api_key",
    "apikey",
    "authorization",
)


def _safe_tail(parts: list[str], separator: str) -> str:
    cleaned = [
        ("<REDACTED>" if part.lower() in PRIVATE_PATH_PARTS else part) for part in parts if part
    ]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return separator.join(cleaned)


REDACTION_PATTERNS = [
    (
        re.compile(
            r"(?i)(password|token|cookie|oauth_secret|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,;}]+"
        ),
        r"\1=<REDACTED>",
    ),
]

TEMP_PATH_ROOTS = (
    "/private/var/folders",
    "/private/var/tmp",
    "/private/tmp",
    "/var/folders",
    "/var/tmp",
    "/tmp",
)
TEMP_ROOT_TEXT_BOUNDARIES = "\"'`“”‘’<>.,;:!?，。；：！？、()（）[]{}【】《》…—"
TEMP_PATH_HARD_DELIMITERS = "\"'`“”‘’<>,;:!?，。；：！？、()（）[]{}【】《》…—"
TEMP_PATH_TRAILING_PUNCTUATION = "."
URI_REFERENCE_PATTERN = re.compile(
    r"(?i)\b[a-z][a-z0-9+.-]*://[^\s\"'`“”‘’<>()（）\[\]{}【】《》…—]+"
)


def _period_is_text_boundary(value: str, index: int) -> bool:
    if value.startswith("...", index):
        return True
    following = index + 1
    if following >= len(value):
        return True
    next_character = value[following]
    return next_character.isspace() or (
        next_character != "." and next_character in TEMP_ROOT_TEXT_BOUNDARIES
    )


def _temp_path_end(value: str, start: int, extra_delimiters: str = "") -> int | None:
    if start > 0:
        previous = value[start - 1]
        if previous.isalnum() or previous in "_/":
            return None

    lowered = value.casefold()
    root_end: int | None = None
    for root in TEMP_PATH_ROOTS:
        if lowered.startswith(root, start):
            root_end = start + len(root)
            break
    if root_end is None:
        return None
    if root_end == len(value):
        return root_end

    boundary = value[root_end]
    if boundary == "/":
        end = root_end
        while end < len(value):
            if value.startswith("...", end):
                break
            character = value[end]
            if (
                character.isspace()
                or character in TEMP_PATH_HARD_DELIMITERS
                or character in extra_delimiters
            ):
                break
            end += 1
        while end > root_end and value[end - 1] in TEMP_PATH_TRAILING_PUNCTUATION:
            end -= 1
        return end
    if boundary == ".":
        return root_end if _period_is_text_boundary(value, root_end) else None
    if (
        boundary.isspace()
        or boundary in TEMP_ROOT_TEXT_BOUNDARIES
        or boundary in extra_delimiters
    ):
        return root_end
    return None


def _redact_bare_temp_paths(value: str, extra_delimiters: str = "") -> tuple[str, bool]:
    parts: list[str] = []
    cursor = 0
    index = 0
    found = False
    while index < len(value):
        if value[index] != "/":
            index += 1
            continue
        path_end = _temp_path_end(value, index, extra_delimiters)
        if path_end is None:
            index += 1
            continue
        parts.append(value[cursor:index])
        parts.append("<REDACTED_PATH>")
        cursor = path_end
        index = path_end
        found = True
    parts.append(value[cursor:])
    return "".join(parts), found


def _encoded_path_prefix_length(raw_path: str, decoded_prefix: str) -> int | None:
    if unquote(raw_path) == decoded_prefix:
        return len(raw_path)
    for end in range(1, len(raw_path) + 1):
        if unquote(raw_path[:end]) == decoded_prefix:
            return end
    return None


def _redact_local_file_uri(value: str) -> tuple[str, bool]:
    parsed = urlsplit(value)
    if parsed.scheme.casefold() != "file" or parsed.netloc.casefold() not in {"", "localhost"}:
        return value, False
    decoded_path = unquote(parsed.path)
    path_end = _temp_path_end(decoded_path, 0)
    if path_end is None:
        return value, False
    raw_prefix_length = _encoded_path_prefix_length(parsed.path, decoded_path[:path_end])
    if raw_prefix_length is None:
        return value, False
    path_start = value.find(parsed.path, value.find("://") + 3)
    if path_start < 0:
        return value, False
    raw_path_end = path_start + raw_prefix_length
    redacted = value[:path_start] + "<REDACTED_PATH>" + value[raw_path_end:]
    return redacted, True


def _redact_uri_query_and_fragment(value: str) -> tuple[str, bool]:
    query_start = value.find("?")
    fragment_start = value.find("#")
    component_starts = [index for index in (query_start, fragment_start) if index >= 0]
    if not component_starts:
        return value, False
    metadata_start = min(component_starts)
    metadata = value[metadata_start:]
    parts: list[str] = []
    cursor = 0
    index = 0
    found = False
    while index < len(metadata):
        encoded_slash = metadata[index : index + 3].casefold() == "%2f"
        if metadata[index] != "/" and not encoded_slash:
            index += 1
            continue
        decoded_before = unquote(metadata[:index])
        if decoded_before and (
            decoded_before[-1].isalnum() or decoded_before[-1] in "_/"
        ):
            index += 1
            continue
        component_end = len(metadata)
        for delimiter in "&#":
            delimiter_index = metadata.find(delimiter, index)
            if delimiter_index >= 0:
                component_end = min(component_end, delimiter_index)
        raw_component = metadata[index:component_end]
        decoded_component = unquote(raw_component)
        path_end = _temp_path_end(decoded_component, 0, extra_delimiters="&#")
        if path_end is None:
            index += 1
            continue
        raw_prefix_length = _encoded_path_prefix_length(
            raw_component, decoded_component[:path_end]
        )
        if raw_prefix_length is None:
            index += 1
            continue
        parts.append(metadata[cursor:index])
        parts.append("<REDACTED_PATH>")
        cursor = index + raw_prefix_length
        index = cursor
        found = True
    parts.append(metadata[cursor:])
    redacted_metadata = "".join(parts)
    return value[:metadata_start] + redacted_metadata, found


def _redact_uri_reference(value: str) -> tuple[str, bool]:
    redacted, path_found = _redact_local_file_uri(value)
    redacted, metadata_found = _redact_uri_query_and_fragment(redacted)
    return redacted, path_found or metadata_found


def _redact_temp_references(value: str) -> tuple[str, bool]:
    parts: list[str] = []
    cursor = 0
    found = False
    for match in URI_REFERENCE_PATTERN.finditer(value):
        plain_text, plain_found = _redact_bare_temp_paths(value[cursor : match.start()])
        uri_text, uri_found = _redact_uri_reference(match.group(0))
        parts.extend((plain_text, uri_text))
        found = found or plain_found or uri_found
        cursor = match.end()
    plain_text, plain_found = _redact_bare_temp_paths(value[cursor:])
    parts.append(plain_text)
    return "".join(parts), found or plain_found


def sanitize_path(value: str) -> str:
    redacted = value

    def replace_windows_user(match: re.Match[str]) -> str:
        return "<REDACTED_PATH>"

    def replace_unix_user(match: re.Match[str]) -> str:
        return "<REDACTED_PATH>"

    def replace_drive_path(match: re.Match[str]) -> str:
        return "<REDACTED_PATH>"

    home = str(Path.home())
    if home:
        home_pattern = re.compile(
            re.escape(home) + r"(?P<tail>(?:[\\/][^\s\"'<>，）)]+)*)", re.IGNORECASE
        )
        redacted = home_pattern.sub(
            lambda match: (
                replace_windows_user(match) if "\\" in match.group(0) else replace_unix_user(match)
            ),
            redacted,
        )

    redacted = re.sub(
        "C:" + r"[\\/]Users[\\/][^\\/\s\"'<>，）)]+(?P<tail>(?:[\\/][^\s\"'<>，）)]+)*)",
        replace_windows_user,
        redacted,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"/Users/[^/\s\"'<>，）)]+(?P<tail>(?:/[^\s\"'<>，）)]+)*)",
        replace_unix_user,
        redacted,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"/home/[^/\s\"'<>，）)]+(?P<tail>(?:/[^\s\"'<>，）)]+)*)",
        replace_unix_user,
        redacted,
        flags=re.IGNORECASE,
    )
    redacted, _ = _redact_temp_references(redacted)
    redacted = re.sub(
        r"(?i)\b[A-Z]:[\\/][^\s\"'<>，）)]+(?:[\\/][^\s\"'<>，）)]+)*",
        replace_drive_path,
        redacted,
    )
    for private_part in PRIVATE_PATH_PARTS:
        redacted = re.sub(
            rf"(?i)([\\/]){re.escape(private_part)}(?=([\\/])|$)", r"\1<REDACTED_PATH>", redacted
        )
    for filename in SENSITIVE_FILENAMES:
        redacted = re.sub(
            re.escape(filename), "<SENSITIVE_DRAFT_FILE>", redacted, flags=re.IGNORECASE
        )
    for extension in SENSITIVE_FILE_EXTENSIONS:
        escaped = re.escape(extension.lstrip("."))
        redacted = re.sub(
            rf"(?i)([A-Za-z]:)?[^\s\"'<>|]+\.{escaped}\b",
            "<SENSITIVE_FILE>",
            redacted,
        )
    return redacted


def redact_path(value: str) -> str:
    return sanitize_path(value)


def sanitize_text(value: str) -> str:
    redacted = sanitize_path(value)
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted


def redact_text(value: str) -> str:
    return sanitize_text(value)


def sanitize_details(value: Any) -> Any:
    return sanitize(value)


def sanitize_result(result: Any) -> Any:
    return sanitize(value=result)


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(keyword in key_text.lower() for keyword in SENSITIVE_KEYWORDS):
                sanitized[key_text] = "<REDACTED>"
            else:
                sanitized[key_text] = sanitize(item)
        return sanitized
    return value


def contains_sensitive_text(value: Any) -> bool:
    text = str(value)
    if str(Path.home()) and str(Path.home()) in text:
        return True
    if re.search(r"C:\\Users\\(?!用户名|<USER_HOME>)[^\\\s]+", text, re.IGNORECASE):
        return True
    if re.search("C:" + r"/Users/(?!用户名|<USER_HOME>)[^/\s]+", text, re.IGNORECASE):
        return True
    if re.search(r"/Users/(?!<USER_HOME>)[^/\s]+", text, re.IGNORECASE):
        return True
    if re.search(r"/home/(?!<USER_HOME>)[^/\s]+", text, re.IGNORECASE):
        return True
    _, has_temp_reference = _redact_temp_references(text)
    if has_temp_reference:
        return True
    if re.search(r"(?i)\b[A-Z]:[\\/][^\s\"'<>]+", text):
        return True
    if any(part in text.lower() for part in PRIVATE_PATH_PARTS):
        return True
    if re.search(r"(?i)(password|token|cookie|oauth_secret|api[_-]?key)\s*[:=]\s*[^<\s]+", text):
        return True
    lowered = text.lower()
    if any(filename in lowered for filename in SENSITIVE_FILENAMES):
        return True
    for extension in SENSITIVE_FILE_EXTENSIONS:
        escaped = re.escape(extension.lstrip("."))
        if re.search(rf"(?i)([A-Za-z]:)?[^\s\"'<>|]+\.{escaped}\b", text):
            return True
    return False
