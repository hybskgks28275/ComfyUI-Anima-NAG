"""ComfyUI-Anima-NAG extension entrypoint."""

from typing_extensions import override

from .anima_nag import AnimaNormalizedAttentionGuidance
from .comfy_api_compat import ComfyExtension, io


class AnimaNAGExtension(ComfyExtension):
    """Comfy extension wrapper for Anima NAG nodes."""

    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [
            AnimaNormalizedAttentionGuidance,
        ]


async def comfy_entrypoint() -> ComfyExtension:
    return AnimaNAGExtension()
