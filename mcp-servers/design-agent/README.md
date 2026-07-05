# Multimodal Design Agent — MCP server

Brings the three-agent UI/UX design analysis from
[gokubuilds/Multimodal_design_agent](https://github.com/gokubuilds/Multimodal_design_agent)
into **Claude Code (the CLI) as an MCP server** — the same way ruflo is added —
so you can analyze designs from any Claude Code session instead of a separate
Streamlit app.

## What it does

Given a local design image, it runs up to three specialized analyses (verbatim
prompts from the original project):

| Lens | Focus |
|------|-------|
| `visual` | design elements, visual hierarchy, color, typography, components, branding |
| `ux` | user flows, usability, accessibility, practical improvements |
| `market` | trends, competitors, positioning, opportunities |

Powered by `gpt-4o` via OpenRouter when a key is set. **Without a key it still
works** — it returns a structured review checklist per lens and setup steps, and
never fails hard.

## Tools

- `analyze_design(image_path, analyses?, context?)` — Markdown analysis of a
  local image. `analyses` is any subset of `["visual","ux","market"]` (default:
  all). `context` is optional product/audience notes or a specific question.
- `design_agent_status()` — model, key status (boolean only), and privacy notes.

## Install

Register the launcher with Claude Code (it self-bootstraps a venv on first run):

```bash
claude mcp add design-agent -- bash "$(pwd)/mcp-servers/design-agent/run.sh"
```

Enable live AI analysis by exporting your OpenRouter key before starting Claude
Code (optionally set a different model):

```bash
export OPENROUTER_API_KEY=sk-or-...        # required for live analysis
export DESIGN_AGENT_MODEL=openai/gpt-4o    # optional override
```

Then, in Claude Code:

> Use design-agent to analyze `~/Desktop/dashboard.png` for ux and visual issues.

## Privacy & safety

- Reads only the **local image path you provide**. Nothing is uploaded except to
  the OpenRouter model you chose, and only when a key is set.
- The API key is read **only from the environment** — never printed, logged, or
  returned in tool output (`design_agent_status` reports a boolean, not the key).
- Read-only: the server writes/mutates **no** files.
- Supported: png, jpg, jpeg, webp, gif · max 10 MB.

## Credit

Analysis prompts and the three-agent concept are from
[gokubuilds/Multimodal_design_agent](https://github.com/gokubuilds/Multimodal_design_agent)
(Streamlit + Agno). This is a reimplementation as an MCP server for Claude Code.
