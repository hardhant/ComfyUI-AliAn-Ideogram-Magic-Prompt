"""Ideogram Magic Prompt -- ComfyUI custom node package.

Drop this entire folder into ComfyUI/custom_nodes/ and restart ComfyUI.
The nodes "Ideogram Magic Prompt" and "Ideogram Suppress Artifacts" will
appear under the Ideogram category.
"""

from .nodes import IdeogramExtension, IdeogramMagicPrompt, IdeogramSuppressArtifacts

# V1-compatible fallback for older ComfyUI installs (V1 schema) so the
# node still loads even if comfy_api.latest isn't available. ComfyUI's
# loader expects NODE_CLASS_MAPPINGS / NODE_DISPLAY_NAME_MAPPINGS at
# module import time.
NODE_CLASS_MAPPINGS = {
    "IdeogramMagicPrompt": IdeogramMagicPrompt,
    "IdeogramSuppressArtifacts": IdeogramSuppressArtifacts,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IdeogramMagicPrompt": "Ideogram Magic Prompt",
    "IdeogramSuppressArtifacts": "Ideogram Suppress Artifacts",
}

# Web-exposed metadata
__all__ = [
    "IdeogramMagicPrompt",
    "IdeogramSuppressArtifacts",
    "IdeogramExtension",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
