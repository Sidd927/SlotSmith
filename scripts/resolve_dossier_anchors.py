"""Expand @@path:symbol@@ placeholders of a dossier draft into verified source links with line anchors.

    .venv/bin/python scripts/resolve_dossier_anchors.py draft.md docs/SlotSmith_Technical_Dossier.md

A placeholder looks up the first line that defines `symbol` in `path` (def, class, UPPER_CASE constant or a
module-level name) and becomes [`symbol`](../path#Lnn). Used once to produce the dossier; afterwards
scripts/check_dossier.py keeps the anchors honest after code changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_line(path: str, symbol: str) -> int:
    lines = (ROOT / path).read_text().splitlines()
    pat = re.compile(rf"^\s*(?:def|class)\s+{re.escape(symbol)}\b|^{re.escape(symbol)}\s*[=:]")
    for i, ln in enumerate(lines, 1):
        if pat.search(ln):
            return i
    raise SystemExit(f"symbol {symbol!r} not found in {path}")


def main(src: str, dst: str) -> None:
    text = Path(src).read_text()

    def sub(m: re.Match) -> str:
        path, symbol = m.group(1), m.group(2)
        return f"[`{symbol}`](../{path}#L{find_line(path, symbol)})"

    def sub_link(m: re.Match) -> str:       # [label](@@path:symbol@@): keep the label, add the anchor
        return f"[{m.group(1)}](../{m.group(2)}#L{find_line(m.group(2), m.group(3))})"

    text, n1 = re.subn(r"\[([^\]]+)\]\(@@([\w./]+):([\w]+)@@\)", sub_link, text)
    out, n2 = re.subn(r"@@([\w./]+):([\w]+)@@", sub, text)
    n = n1 + n2
    Path(dst).write_text(out)
    print(f"resolved {n} anchors -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
