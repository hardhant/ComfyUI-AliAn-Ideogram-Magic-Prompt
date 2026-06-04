"""Negative prompt snippets for Ideogram 4.

Ideogram 4 has no dedicated `negative_prompts` field in its caption
schema (unlike SD/A1111). The way to suppress noise, blur, and other
artifacts is to STATE the positive attributes you want instead:

  - Instead of "no noise"      -> "clean signal, no grain"
  - Instead of "no blur"       -> "sharp focus, no motion blur"
  - Instead of "no jpeg"       -> "high fidelity, no compression artifacts"
  - Instead of "no chromatic"  -> "no chromatic aberration, accurate color"

Both forms below apply the same principle: explicit positive constraints
on style_description, plus a list of pre-baked phrases you can paste
into a plain prompt or merge into a JSON caption.
"""

import json  # used by merge_into_json_caption

# ----------------------------------------------------------------------
# 1. PLAIN-TEXT SNIPPET
# ----------------------------------------------------------------------
# Paste this at the end of your plain prompt (before magic-prompt
# expansion), or hand it to a magic-prompt LLM as a "must include" cue.

NEGATIVE_PLAIN = (
    "high quality, clean image, no visible noise, no film grain, no "
    "chromatic aberration, no jpeg compression artifacts, no motion blur, "
    "sharp focus throughout, no double exposure, no lens flare, no "
    "oversaturation, no blown highlights, no crushed shadows, "
    "professional color grading, accurate white balance, no color banding"
)


# ----------------------------------------------------------------------
# 2. JSON CAPTAIN SNIPPET
# ----------------------------------------------------------------------
# Merge this into a hand-written (or LLM-generated) JSON caption. It
# covers the most common artifact categories Ideogram 4 can produce.

NEGATIVE_JSON = {
    "high_level_description_postfix": (
        ", clean image with no visible noise, no grain, no blur, no "
        "compression artifacts, and accurate color reproduction"
    ),
    "style_description": {
        "aesthetics": (
            "high quality, professional color grading, accurate color "
            "reproduction, no oversaturation, no color banding, no "
            "blown highlights, no crushed shadows, smooth gradients"
        ),
        "lighting": (
            "even, clean illumination, no harsh shadows, no blown "
            "highlights, no lens flare, no double exposure"
        ),
        "photo": (
            "sharp focus edge-to-edge, no motion blur, no focus fall-off, "
            "f/8 depth of field, no chromatic aberration, no lens "
            "distortion, low ISO, no digital noise, no film grain, no "
            "jpeg compression artifacts"
        ),
        "medium": "photograph",
    },
}


def merge_into_json_caption(caption: dict) -> dict:
    """Return a new caption with negative-prompt constraints merged in.
    Style descriptions are appended (so existing descriptions win), and
    the high-level description gets a 'clean image' postfix.
    """
    out = json.loads(json.dumps(caption))  # deep copy

    hld = out.get("high_level_description", "")
    if hld and NEGATIVE_JSON["high_level_description_postfix"] not in hld:
        hld = hld.rstrip(" .,") + NEGATIVE_JSON["high_level_description_postfix"]
        out["high_level_description"] = hld

    sd = out.setdefault("style_description", {})
    for key, val in NEGATIVE_JSON["style_description"].items():
        if val and val not in sd.get(key, ""):
            sd[key] = (sd.get(key, "") + " " + val).strip()
    out["style_description"] = sd

    return out


def plain_prompt_with_negatives(prompt: str) -> str:
    """Return `prompt` with the negative-plain snippet appended."""
    if NEGATIVE_PLAIN in prompt:
        return prompt
    return f"{prompt.rstrip('. ')}, {NEGATIVE_PLAIN}"


if __name__ == "__main__":
    import json
    print("--- NEGATIVE_PLAIN ---")
    print(NEGATIVE_PLAIN)
    print()
    print("--- NEGATIVE_JSON ---")
    print(json.dumps(NEGATIVE_JSON, indent=2, ensure_ascii=False))
    print()
    print("--- merge example ---")
    sample = {
        "high_level_description": "A ginger cat reading a spellbook.",
        "style_description": {
            "aesthetics": "warm and magical",
            "photo": "shallow depth of field",
        },
        "compositional_deconstruction": {"background": "cozy study", "elements": []},
    }
    print(json.dumps(merge_into_json_caption(sample), indent=2, ensure_ascii=False))
