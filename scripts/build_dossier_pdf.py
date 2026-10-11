"""Render docs/SlotSmith_Technical_Dossier.md to docs/SlotSmith_Technical_Dossier.pdf.

    pip install markdown pygments                      # build-time only; not part of the project's runtime
    .venv/bin/python scripts/build_dossier_pdf.py      # needs Google Chrome (or set CHROME=/path/to/chrome)

The Markdown file is the single editable source; this script never edits it. Relative image links are resolved
against docs/. Chrome's headless print-to-PDF does the page layout.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SRC = DOCS / "SlotSmith_Technical_Dossier.md"
PDF = DOCS / "SlotSmith_Technical_Dossier.pdf"
HTML = Path(os.environ.get("DOSSIER_HTML", "/tmp/slotsmith_dossier.html"))
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
@page wide { size: A4 landscape; margin: 12mm; }
.wide { page: wide; break-before: page; break-after: page; }
.wide img { max-height: 165mm; }
html { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #1b2430; }
h1 { font-size: 24pt; margin: 0 0 4pt; } h2 { font-size: 16pt; margin: 22pt 0 6pt; border-bottom: 1.5px solid #2f7d4a; padding-bottom: 3pt; break-after: avoid; }
h3 { font-size: 12.5pt; margin: 14pt 0 4pt; break-after: avoid; } h4 { font-size: 10.5pt; break-after: avoid; }
p, li { orphans: 3; widows: 3; } a { color: #0a5c8a; text-decoration: none; }
code { font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 8.4pt; background: #f1f4f7; padding: 0 2pt; border-radius: 2px; word-break: break-word; }
pre { background: #f6f8fa; border: 1px solid #dde3ea; padding: 6pt 8pt; font-size: 7.6pt; line-height: 1.3; white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 7.6pt; line-height: 1.28; }
th, td { border: 1px solid #cfd6de; padding: 3pt 4pt; vertical-align: top; word-break: normal; overflow-wrap: anywhere; hyphens: manual; }
th { background: #eaf3ec; text-align: left; } tr { break-inside: avoid; }
img { max-width: 100%; max-height: 232mm; width: auto; height: auto; display: block; margin: 6pt auto; break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 4pt 10pt; border-left: 3px solid #b07a00; background: #fff8e6; }
blockquote table { font-size: 7.6pt; }
hr { border: 0; border-top: 1px solid #d5dbe2; margin: 14pt 0; }
em { color: #333; }
"""


def main() -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"], extension_configs={"toc": {"permalink": False}})
    body = md.convert(SRC.read_text())
    html = (f'<!doctype html><html><head><meta charset="utf-8"><base href="file://{DOCS}/">'
            f"<title>SlotSmith Technical Dossier</title><style>{CSS}</style></head><body>{body}</body></html>")
    # landscape pages for the wide diagrams and for tables with many columns
    html = re.sub(r'(<p><img alt="Figure (?:B|J|K)\b.*?</p>\s*<p><em>.*?</em></p>)', r'<div class="wide">\1</div>', html, flags=re.S)

    def wrap_wide(m: re.Match) -> str:
        return f'<div class="wide">{m.group(0)}</div>' if m.group(0).count("<th") >= 8 else m.group(0)

    html = re.sub(r"<table>.*?</table>", wrap_wide, html, flags=re.S)
    HTML.write_text(html)
    ids = set(re.findall(r'id="([^"]+)"', html))
    missing = sorted({a for a in re.findall(r'href="#([^"]+)"', html) if a not in ids})
    if missing:
        print("WARNING: internal anchors without a heading id:", missing[:20])
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={PDF}", f"file://{HTML}"]
    subprocess.run(cmd, check=True, capture_output=True, timeout=240)
    print("wrote", PDF, PDF.stat().st_size, "bytes")


if __name__ == "__main__":
    sys.exit(main())
