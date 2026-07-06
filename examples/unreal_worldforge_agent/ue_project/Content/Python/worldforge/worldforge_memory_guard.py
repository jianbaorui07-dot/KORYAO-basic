"""Compatibility wrapper for v1.1 memory guard."""

from .memory_guard import snapshot, write_memory_profile, project_root_from_env

__all__ = ["snapshot", "write_memory_profile", "project_root_from_env"]
