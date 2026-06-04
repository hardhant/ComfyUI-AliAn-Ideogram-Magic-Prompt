# ComfyUI Ideogram Magic Prompt

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![ComfyUI V3](https://img.shields.io/badge/ComfyUI-V3%20%2F%20Modern%20Node%20Design-blueviolet)](https://docs.comfy.org/)

A ComfyUI custom node that calls Ideogram's hosted **magic-prompt API** to
turn a plain-text prompt into the structured JSON caption that Ideogram 4
expects.

It uses Ideogram's free hosted service — no model download, no GPU usage.
Typical round-trip: 2-5 seconds.

## Preview

```
┌─────────────────────────────────────┐
│  prompt: "a ginger cat wearing a   │
│   tiny wizard hat reading a        │
│   spellbook"                       │
│  api_key: ••••••                   │
│  aspect_ratio: [1x1 ▾]             │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│  json_caption:                      │
│  {                                  │
│   "high_level_description": "...",  │
│   "style_description": { ... },     │
│   "compositional_deconstruction": { │
│     "background": "...",            │
│     "elements": [                   │
│       { "type": "obj", "bbox": ... }│
│     ]                               │
│   }                                 │
│  }                                  │
└─────────────────────────────────────┘
```

## Install

### Option A — ComfyUI Manager (recommended)

1. Open ComfyUI Manager.
2. Search for **"Ideogram Magic Prompt"** (or the repo name
   `ComfyUI-AliAn-Ideogram-Magic-Prompt`).
3. Click **Install**. The Manager reads `pyproject.toml` for the
   version, PublisherId, and DisplayName automatically.
4. Restart ComfyUI.

### Option B — Manual install

1. Drop the entire `comfyui_ideogram_magic_prompt/` folder into
   `<your-comfyui>/custom_nodes/`.
2. Restart ComfyUI.
3. The node **"Ideogram Magic Prompt"** will appear under the
   **Add Node → Ideogram** category.

No `pip install` needed — the node uses only `urllib` from the Python
standard library plus the `comfy_api` module shipped with ComfyUI.

## Inputs

| Name | Type | Description |
| --- | --- | --- |
| `prompt` | multiline string | The plain-text prompt to expand. |
| `api_key` | string (password) | Your `IDEOGRAM_API_KEY` from [ideogram.ai/api/learn/](https://ideogram.ai/api/learn/). |
| `aspect_ratio` | combo | One of the 18 ratios accepted by Ideogram's magic-prompt API, plus `AUTO`. Pick the closest match to your target image. |

### Supported aspect ratios

`AUTO`, `1x4`, `1x3`, `1x2`, `9x16`, `10x16`, `2x3`, `3x4`, `4x5`, `1x1`,
`5x4`, `4x3`, `3x2`, `16x10`, `16x9`, `2x1`, `3x1`, `4x1`

## Output

| Name | Type | Description |
| --- | --- | --- |
| `json_caption` | string (JsonPreview) | Stringified JSON caption ready to feed into any Ideogram 4 generation node. |

The output is automatically parsed and displayed as a JSON tree in the
node (ComfyUI's built-in `JsonPreview` tool). You can also connect it as
a string to downstream text-handling nodes.

The output caption is cleaned of `aspect_ratio` echoes and any
`bbox` fields, so it's a clean drop-in for
`Ideogram4Pipeline.__call__(prompt=...)` or any equivalent.

## Usage

```
plain prompt ─┐
               ├──▶ Ideogram Magic Prompt ──▶ json_caption ──▶ [your Ideogram4 generator]
IDEOGRAM_API_KEY ┘                                  ▲
                                                      │
                                          live JSON preview
```

In a typical workflow you would:
1. Add the **Ideogram Magic Prompt** node.
2. Plug in a free-form text prompt and your API key.
3. Connect the `json_caption` output to your Ideogram 4 generation node
   (e.g. `Ideogram4Pipeline.__call__` from a custom node, or paste the
   JSON into the standalone `gradio_app.py` UI as
   `--prompt (Get-Content .\caption.json)`).

## Compatibility

| ComfyUI version | Status |
| --- | --- |
| **V3 (Modern Node Design)** | ✅ Primary target. Uses `io.ComfyNode`, `io.Schema`, `ComfyExtension`, `comfy_entrypoint()`. |
| **V1 / older installs** | ✅ Works. Re-exports `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` for the legacy loader. |

The package has no runtime dependencies beyond `comfy_api` (bundled with
ComfyUI V3) and the Python standard library.

## Development

Run the tests locally:

```bash
python -m pip install -e .[test]   # if you add a test extra
python -m pytest
```

There's no test suite in this drop — pull requests welcome.

## License

[MIT](LICENSE) — see `LICENSE` for the full text.
