#!/usr/bin/env python3
"""Multimodal Design Agent — an MCP server for Claude Code.

Ports the three-agent UI/UX design analysis from
https://github.com/gokubuilds/Multimodal_design_agent (Streamlit) into a
Model Context Protocol server so it is callable directly from Claude Code
(the CLI), the same way ruflo is.

Three specialized analyses run over a local design image:
  * Visual   — design elements, hierarchy, color, typography, components
  * UX       — user flows, usability, accessibility, improvements
  * Market   — trends, competitors, positioning, opportunities

Powered by ``gpt-4o`` via OpenRouter when ``OPENROUTER_API_KEY`` is set in the
environment. With no key the server stays useful: it returns a structured
heuristic checklist per lens plus setup instructions, and never fails hard.

Privacy / safety:
  * Reads a local image path you provide; no image is uploaded anywhere except
    (when you enable it with a key) the OpenRouter model you chose.
  * The API key is read only from the environment — never printed, logged, or
    returned in tool output.
  * No files are written or mutated; analysis is read-only.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

try:  # optional: load a local .env if python-dotenv is present
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("design-agent")

MODEL = os.environ.get("DESIGN_AGENT_MODEL", "openai/gpt-4o")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}

# Verbatim agent instructions from the original Multimodal_design_agent project.
AGENTS: dict[str, dict[str, str]] = {
    "visual": {
        "title": "Visual Design Analysis",
        "prompt": (
            "You are a visual analysis expert that:\n"
            "1. Identifies design elements, patterns, and visual hierarchy\n"
            "2. Analyzes color schemes, typography, and layouts\n"
            "3. Detects UI components and their relationships\n"
            "4. Evaluates visual consistency and branding\n"
            "Be specific and technical in your analysis"
        ),
        "checklist": [
            "Visual hierarchy — is the primary action obvious within 3 seconds?",
            "Color — palette count, contrast ratios (WCAG AA 4.5:1 for text), semantic use.",
            "Typography — type scale, line-length (45-75 chars), weight/contrast pairing.",
            "Layout — grid/alignment, spacing rhythm, density and whitespace balance.",
            "Components — button/input/card consistency, state coverage, iconography.",
            "Branding — consistency of tone, logo treatment, and visual identity.",
        ],
    },
    "ux": {
        "title": "UX Analysis",
        "prompt": (
            "You are a UX analysis expert that:\n"
            "1. Evaluates user flows and interaction patterns\n"
            "2. Identifies usability issues and opportunities\n"
            "3. Suggests UX improvements based on best practices\n"
            "4. Analyzes accessibility and inclusive design\n"
            "Focus on user-centric insights and practical improvements"
        ),
        "checklist": [
            "Primary flow — steps to the core task; any dead-ends or friction.",
            "Feedback — loading, empty, error, and success states present?",
            "Affordances — do interactive elements look interactive?",
            "Accessibility — focus order, alt text, target sizes (44px), color independence.",
            "Cognitive load — choices per screen, progressive disclosure.",
            "Recovery — undo, confirmation on destructive actions, forgiving inputs.",
        ],
    },
    "market": {
        "title": "Market Research",
        "prompt": (
            "You are a market research expert that:\n"
            "1. Identifies market trends and competitor patterns\n"
            "2. Analyzes similar products and features\n"
            "3. Suggests market positioning and opportunities\n"
            "4. Provides industry-specific insights\n"
            "Focus on actionable market intelligence"
        ),
        "checklist": [
            "Category — what product space does this UI signal?",
            "Comparable patterns — which established products use similar layouts?",
            "Differentiators — what, if anything, stands out vs. the norm?",
            "Positioning — premium / utilitarian / playful; who is the target user?",
            "Opportunity — an underserved need this design could lean into.",
            "Risk — where it may feel generic or fall behind category expectations.",
        ],
    },
}

ANALYSIS_ALIASES = {
    "visual": "visual", "vision": "visual", "design": "visual",
    "ux": "ux", "usability": "ux", "accessibility": "ux",
    "market": "market", "research": "market", "competitor": "market",
}


def _has_key() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _resolve_lenses(analyses: list[str] | None) -> list[str]:
    if not analyses:
        return ["visual", "ux", "market"]
    out: list[str] = []
    for a in analyses:
        key = ANALYSIS_ALIASES.get(str(a).strip().lower())
        if key and key not in out:
            out.append(key)
    return out or ["visual", "ux", "market"]


def _image_data_url(image_path: str) -> tuple[str | None, str | None]:
    """Return (data_url, error). Reads a local image and base64-encodes it."""
    p = Path(os.path.expanduser(image_path)).resolve()
    if not p.is_file():
        return None, f"No file at: {p}"
    ext = p.suffix.lower()
    if ext not in _MIME:
        return None, f"Unsupported image type '{ext}'. Use one of: {', '.join(sorted(_MIME))}."
    data = p.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        return None, f"Image is {len(data) // 1024} KB; max is {MAX_IMAGE_BYTES // 1024} KB."
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{_MIME[ext]};base64,{b64}", None


def _heuristic_section(lens: str, context: str) -> str:
    agent = AGENTS[lens]
    lines = [f"## {agent['title']}", ""]
    lines.append("_No `OPENROUTER_API_KEY` set — returning a structured review checklist instead of a live model analysis._")
    lines.append("")
    for item in agent["checklist"]:
        lines.append(f"- [ ] {item}")
    if context:
        lines.append("")
        lines.append(f"**Your context:** {context}")
    return "\n".join(lines)


def _model_section(lens: str, data_url: str, context: str) -> str:
    from openai import OpenAI  # imported lazily so the server loads without the SDK

    agent = AGENTS[lens]
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=os.environ["OPENROUTER_API_KEY"])
    user_text = "Analyze this UI/UX design image."
    if context:
        user_text += f"\n\nAdditional context from the user: {context}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": agent["prompt"]},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ],
        max_tokens=1200,
    )
    body = (resp.choices[0].message.content or "").strip()
    return f"## {agent['title']}\n\n{body}"


@mcp.tool()
def analyze_design(image_path: str, analyses: list[str] | None = None, context: str = "") -> str:
    """Analyze a UI/UX design image across visual, UX, and market lenses.

    Args:
        image_path: Absolute or ~ path to a local design image (png/jpg/jpeg/webp/gif).
        analyses: Which lenses to run. Any of "visual", "ux", "market". Defaults to all three.
        context: Optional notes about the product, audience, or a specific question.

    Returns Markdown with one section per requested lens. Uses gpt-4o via
    OpenRouter when OPENROUTER_API_KEY is set; otherwise returns a structured
    heuristic checklist per lens.
    """
    lenses = _resolve_lenses(analyses)
    data_url, err = _image_data_url(image_path)
    if err:
        return f"⚠️ {err}"

    header = f"# Design Analysis — `{Path(image_path).name}`\n"
    sections: list[str] = []
    if _has_key():
        for lens in lenses:
            try:
                sections.append(_model_section(lens, data_url, context))
            except Exception as exc:  # surface, don't crash the tool
                sections.append(f"## {AGENTS[lens]['title']}\n\n⚠️ Model call failed: {exc}\n\n" + _heuristic_section(lens, context))
    else:
        for lens in lenses:
            sections.append(_heuristic_section(lens, context))

    return header + "\n\n" + "\n\n---\n\n".join(sections)


@mcp.tool()
def design_agent_status() -> str:
    """Report configuration and privacy posture of the design agent."""
    return (
        "# Multimodal Design Agent — status\n\n"
        f"- Model: `{MODEL}` via OpenRouter\n"
        f"- OpenRouter key configured: {'yes' if _has_key() else 'no (running in heuristic mode)'}\n"
        f"- Lenses: visual, ux, market\n"
        f"- Max image size: {MAX_IMAGE_BYTES // (1024 * 1024)} MB (png/jpg/jpeg/webp/gif)\n\n"
        "Privacy: reads a local image path you provide; nothing is uploaded except to the "
        "OpenRouter model when a key is set. The API key is read only from the environment "
        "and is never printed, logged, or returned.\n\n"
        "To enable live AI analysis: set OPENROUTER_API_KEY in the environment, then re-run."
    )


if __name__ == "__main__":
    mcp.run()
