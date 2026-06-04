"""Ideogram Magic Prompt -- ComfyUI custom node.

Generates the structured JSON caption that Ideogram 4 expects from a
plain-text prompt, using Ideogram's free hosted magic-prompt API.

Inputs:  prompt (multiline text), api_key (password), aspect_ratio (combo)
Output:  json_caption (string, displayed via the built-in JsonPreview tool)

Drop this folder into your ComfyUI/custom_nodes/ directory and restart
ComfyUI. The node will appear under the "Ideogram" category.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

try:
    from comfy_api.latest import ComfyExtension, io, ui
except ImportError:  # older ComfyUI / V1 fallback
    from comfy_api.v0_0_2 import ComfyExtension, io, ui  # type: ignore[no-redef]

from .negative_prompt import (
    NEGATIVE_PLAIN,
    merge_into_json_caption,
    plain_prompt_with_negatives,
)

MAGIC_PROMPT_URL = "https://api.ideogram.ai/v1/ideogram-v4/magic-prompt"

# 18 aspect ratios accepted by the Ideogram magic-prompt API
SUPPORTED_ARS = [
    "AUTO",
    "1x4", "1x3", "1x2",
    "9x16", "10x16",
    "2x3", "3x4", "4x5",
    "1x1",
    "5x4", "4x3", "3x2",
    "16x10", "16x9",
    "2x1", "3x1", "4x1",
]

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Api-Key": "",  # filled at call time
}

DEFAULT_TIMEOUT = 120.0


def _post_magic_prompt(prompt: str, aspect_ratio: str, api_key: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Call Ideogram's hosted magic-prompt API. Returns the parsed JSON
    caption dict (after stripping `aspect_ratio` and bboxes so the
    caption is a clean drop-in for the Ideogram4Pipeline)."""
    headers = {**DEFAULT_HEADERS, "Api-Key": api_key}
    body = json.dumps({"text_prompt": prompt, "aspect_ratio": aspect_ratio}).encode("utf-8")
    req = urllib.request.Request(MAGIC_PROMPT_URL, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Ideogram magic-prompt API HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Ideogram magic-prompt API unreachable: {e.reason}") from e

    jp = payload.get("json_prompt")
    if not jp:
        raise RuntimeError(f"Ideogram API returned no json_prompt: {payload}")
    # Clean up the caption: drop the echoed aspect_ratio and any
    # bboxes (the model sometimes includes them in the upstream JSON).
    jp.pop("aspect_ratio", None)
    for el in jp.get("compositional_deconstruction", {}).get("elements", []):
        if isinstance(el, dict):
            el.pop("bbox", None)
    return jp


class IdeogramMagicPrompt(io.ComfyNode):
    """Expand a plain prompt into Ideogram 4's native structured JSON caption.

    The output is a stringified JSON object. Feed it directly into an
    Ideogram4 generation node (or paste into the ideogram4 gradio UI).
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="IdeogramMagicPrompt",
            display_name="Ideogram Magic Prompt",
            category="Ideogram",
            description=(
                "Rewrites a plain prompt into the structured JSON caption "
                "format the Ideogram 4 model was trained on. Uses Ideogram's "
                "free hosted magic-prompt API."
            ),
            inputs=[
                io.String.Input(
                    "prompt",
                    multiline=True,
                    tooltip="Plain-text prompt to expand.",
                ),
                io.String.Input(
                    "api_key",
                    default="",
                    tooltip="IDEOGRAM_API_KEY from https://ideogram.ai/api/learn/",
                ),
                io.Combo.Input(
                    "aspect_ratio",
                    options=SUPPORTED_ARS,
                    default="1x1",
                    tooltip="Closest aspect ratio for which to lay out the caption.",
                ),
                io.Boolean.Input(
                    "suppress_artifacts",
                    default=True,
                    tooltip=(
                        "Append the negative-prompt snippet (no noise, no blur, "
                        "no jpeg, no chromatic aberration...) to the caption. "
                        "Ideogram 4 has no native negative_prompt field; this "
                        "is the closest equivalent."
                    ),
                ),
            ],
            outputs=[
                io.String.Output(
                    "json_caption",
                    tooltip="Stringified JSON caption -- feed to Ideogram4 generate.",
                ),
            ],
        )

    @classmethod
    def execute(
        cls, prompt: str, api_key: str, aspect_ratio: str, suppress_artifacts: bool
    ) -> io.NodeOutput:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt is empty.")
        if not api_key or not api_key.strip():
            raise ValueError(
                "IDEOGRAM_API_KEY is empty. Get one at "
                "https://ideogram.ai/api/learn/ and paste it into the node."
            )

        t0 = time.time()
        caption_obj = _post_magic_prompt(prompt, aspect_ratio, api_key)
        elapsed = time.time() - t0

        if suppress_artifacts:
            caption_obj = merge_into_json_caption(caption_obj)
            log_suffix = " (artifact-suppression snippet merged)"
        else:
            log_suffix = ""

        caption_str = json.dumps(caption_obj, ensure_ascii=False, separators=(",", ":"))
        log = f"magic-prompt expansion: {elapsed:.1f}s, aspect={aspect_ratio}{log_suffix}"
        return io.NodeOutput(
            caption_str,
            ui=ui.PreviewText(log),
        )


class IdeogramSuppressArtifacts(io.ComfyNode):
    """Append the artifact-suppression snippet to any text or JSON caption.

    Useful as a standalone post-processing step if you already have a
    hand-written or LLM-generated caption and just want to bolt on the
    noise/blur/jpeg suppression language without re-running the API.

    Set `mode` to:
      - "auto"       -- parse the input as JSON if it looks like a JSON
                         object/array; else treat as plain text.
      - "json"       -- force JSON merge (style_description / HLD postfix).
      - "plain text" -- append the plain-prompt snippet.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="IdeogramSuppressArtifacts",
            display_name="Ideogram Suppress Artifacts",
            category="Ideogram",
            description=(
                "Appends a positive-constraint snippet ('no noise, no grain, "
                "no blur, no jpeg, no chromatic aberration...') to either a "
                "JSON caption (merged into style_description) or a plain-text "
                "prompt. Closest equivalent to a negative prompt in Ideogram 4."
            ),
            inputs=[
                io.String.Input(
                    "caption",
                    multiline=True,
                    tooltip="Either a stringified JSON caption or a plain prompt.",
                ),
                io.Combo.Input(
                    "mode",
                    options=["auto", "json", "plain text"],
                    default="auto",
                    tooltip=(
                        "auto: parse as JSON if input looks like JSON object/array. "
                        "json: force JSON merge. "
                        "plain text: append the snippet to the input as-is."
                    ),
                ),
            ],
            outputs=[
                io.String.Output(
                    "caption",
                    tooltip="Caption with the artifact-suppression snippet applied.",
                ),
            ],
        )

    @classmethod
    def execute(cls, caption: str, mode: str) -> io.NodeOutput:
        if not caption or not caption.strip():
            raise ValueError("Caption is empty.")

        stripped = caption.strip()
        looks_json = stripped.startswith(("{", "[")) and stripped.endswith(("}", "]"))
        effective_mode = mode
        if mode == "auto":
            effective_mode = "json" if looks_json else "plain text"

        if effective_mode == "json":
            try:
                obj = json.loads(caption)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Input looks like JSON but couldn't be parsed: {e}. "
                    f"Switch mode to 'plain text' or fix the JSON."
                ) from e
            if not isinstance(obj, (dict, list)):
                raise ValueError(
                    f"Expected a JSON object or array, got {type(obj).__name__}. "
                    f"Switch mode to 'plain text'."
                )
            if isinstance(obj, dict):
                merged = merge_into_json_caption(obj)
            else:
                # list of captions -- merge into each dict element
                merged = [merge_into_json_caption(x) if isinstance(x, dict) else x for x in obj]
            out = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
            log = f"artifact-suppression merged into JSON ({'array of ' + str(len(merged)) if isinstance(merged, list) else 'object'})"
        else:
            out = plain_prompt_with_negatives(caption)
            log = "artifact-suppression appended to plain text"

        return io.NodeOutput(out, ui=ui.PreviewText(log))


class IdeogramExtension(ComfyExtension):
    """Registers the Ideogram magic-prompt nodes with ComfyUI."""

    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [IdeogramMagicPrompt, IdeogramSuppressArtifacts]


async def comfy_entrypoint() -> IdeogramExtension:  # noqa: D401
    return IdeogramExtension()
