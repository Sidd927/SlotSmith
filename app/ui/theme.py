"""SlotSmith design tokens and stylesheet (design.md sections C and D).

Colours are CSS custom properties declared on `.stApp` with `light-dark()`. Streamlit sets `color-scheme`
on `.stApp` for its active theme, so these flip with the native Settings switch (or the system setting) with no
rerun, no JavaScript and no server-side theme state. A hex fallback precedes each pair for older browsers.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# name: (light, dark)
TOKENS: dict[str, tuple[str, str]] = {
    "bg": ("#F2F0EB", "#0D1013"),
    "surface": ("#FCFBF8", "#14181C"),
    "surface-2": ("#ECE9E2", "#1B2025"),
    "border": ("#DAD6CC", "#272D34"),
    "border-strong": ("#A9A498", "#434C57"),
    "text": ("#14181D", "#ECEAE4"),
    "text-2": ("#454A52", "#AAAFB6"),
    "text-3": ("#5E626A", "#8C929A"),
    "ink": ("#14181D", "#ECEAE4"),
    "ink-fg": ("#FCFBF8", "#0D1013"),
    "accent": ("#0A6C7A", "#4FC3CF"),
    "accent-fg": ("#FFFFFF", "#062329"),
    "accent-soft": ("#D8EBEB", "#143A41"),
    "ok": ("#187233", "#4CC775"),
    "ok-soft": ("#E1F2E6", "#173A24"),
    "warn": ("#8A5A00", "#F0B64A"),
    "warn-soft": ("#FBEFD2", "#41330F"),
    "bad": ("#B3261E", "#FF8F86"),
    "bad-soft": ("#FBE4E2", "#472220"),
    "info": ("#2B5DB8", "#86AEF5"),
    "info-soft": ("#E3ECFA", "#1C2D4C"),
    # signal types: fill, text
    "t-ai": ("#CFE6F5", "#1E3F57"), "t-ai-fg": ("#0B4A72", "#9FD3F5"),
    "t-ao": ("#F0D3E3", "#4A2A3D"), "t-ao-fg": ("#6B2146", "#F1B4D2"),
    "t-di": ("#C8EBDD", "#1B4636"), "t-di-fg": ("#0A5640", "#8FE0C0"),
    "t-do": ("#F8E3B0", "#4D3A12"), "t-do-fg": ("#6B4700", "#F5CF75"),
    "t-df": ("#F7D3BB", "#55301A"), "t-df-fg": ("#7A3200", "#F5B188"),
    "t-rl": ("#CDD6F6", "#2A3566"), "t-rl-fg": ("#1F3A8A", "#B8C6FF"),
}

FONT_SANS = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
FONT_MONO = 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace'


def _token_block() -> str:
    lines = []
    for name, (light, dark) in TOKENS.items():
        lines.append(f"--ss-{name}:{light};--ss-{name}:light-dark({light},{dark});")
    return "".join(lines)


FONT_DISPLAY = '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Charter, Georgia, serif'
_CSS_DIR = Path(__file__).parent / "css"
_CSS_FILES = ("base.css", "workbench.css", "landing.css", "responsive.css")


@lru_cache(maxsize=1)
def stylesheet() -> str:
    css = "\n".join((_CSS_DIR / f).read_text(encoding="utf-8") for f in _CSS_FILES)
    return (css.replace("@@TOKENS@@", _token_block()).replace("@@SANS@@", FONT_SANS)
            .replace("@@MONO@@", FONT_MONO).replace("@@DISPLAY@@", FONT_DISPLAY))


def maxw_override(px: int) -> str:
    """Per-page content width (landing 1200, workbench 1360)."""
    return f".stApp{{--ss-maxw:{int(px)}px;}}"
