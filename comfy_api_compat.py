"""Comfy API import compatibility helpers."""

from __future__ import annotations

try:
    from comfy_api.latest import ComfyExtension, io
except Exception:  # pragma: no cover - runtime compatibility path
    from comfy_api import ComfyExtension, io

__all__ = ["ComfyExtension", "io"]
