from __future__ import annotations

import re
from pathlib import Path
from typing import Any


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


def _home_pattern() -> str:
    home = str(Path.home())
    return re.escape(home) if home else r"a^"


REDACTION_PATTERNS = [
    (re.compile(_home_pattern(), re.IGNORECASE), "<USER_HOME>"),
    (re.compile(r"C:\\Users\\[^\\\s\"']+", re.IGNORECASE), r"<USER_HOME>"),
    (re.compile(r"C:/Users/[^/\s\"']+", re.IGNORECASE), r"<USER_HOME>"),
    (re.compile(r"(?i)(password|token|cookie|oauth_secret|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,;}]+"), r"\1=<REDACTED>"),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    for filename in SENSITIVE_FILENAMES:
        redacted = re.sub(re.escape(filename), "<SENSITIVE_DRAFT_FILE>", redacted, flags=re.IGNORECASE)

    for extension in SENSITIVE_FILE_EXTENSIONS:
        escaped = re.escape(extension.lstrip("."))
        redacted = re.sub(
            rf"(?i)([A-Za-z]:)?[^\s\"'<>|]+\.{escaped}\b",
            "<SENSITIVE_FILE>",
            redacted,
        )
    return redacted


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
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
    if re.search(r"C:/Users/(?!用户名|<USER_HOME>)[^/\s]+", text, re.IGNORECASE):
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
