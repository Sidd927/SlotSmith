"""Validate docs/SlotSmith_Technical_Dossier.md: relative links, images, heading anchors, and source line anchors.

    .venv/bin/python scripts/check_dossier.py            # exits 1 if anything is broken

Source anchors such as [`ffd_pack`](../src/slotsmith/allocator.py#L81) must point at a line (or one of the next two lines)
containing the backticked symbol, so a stale line number is caught after the code changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "SlotSmith_Technical_Dossier.md"


def slug(h: str) -> str:
    h = re.sub(r"<[^>]+>", "", h).strip().lower()
    h = re.sub(r"[`*_]", "", h)
    h = re.sub(r"[^\w\- ]", "", h, flags=re.UNICODE)
    return h.replace(" ", "-")


def main() -> int:
    text = DOC.read_text()
    errors: list[str] = []
    fence = False
    heads, seen = set(), {}
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence:
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                s = slug(m.group(2))
                n = seen.get(s, 0)
                seen[s] = n + 1
                heads.add(s if n == 0 else f"{s}-{n}")
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    n_links = n_src = n_img = 0
    for m in re.finditer(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", body):
        is_img, label, target = m.group(1) == "!", m.group(2), m.group(3)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        n_links += 1
        if target.startswith("#"):
            if target[1:] not in heads:
                errors.append(f"missing heading anchor {target} (link text: {label[:40]})")
            continue
        path, _, frag = target.partition("#")
        f = (DOC.parent / path).resolve()
        if not f.exists():
            errors.append(f"missing file {path}")
            continue
        if is_img:
            n_img += 1
        if frag and re.fullmatch(r"L\d+(-L\d+)?", frag):
            n_src += 1
            ln = int(frag[1:].split("-")[0])
            lines = f.read_text().splitlines()
            if ln > len(lines):
                errors.append(f"{path}#{frag}: file has only {len(lines)} lines")
                continue
            sym = re.fullmatch(r"`([^`]+)`", label)
            if sym:
                needle = sym.group(1).split("(")[0].split(".")[-1]
                window = " ".join(lines[ln - 1: ln + 2])
                if needle not in window:
                    errors.append(f"{path}#{frag}: expected symbol {needle!r} near that line")
    print(f"links checked: {n_links} (images {n_img}, source anchors {n_src}); headings: {len(heads)}")
    for e in errors:
        print("ERROR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
