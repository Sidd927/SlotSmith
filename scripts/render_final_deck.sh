#!/bin/zsh
# Render deliverables/pitch_deck/SlotSmith_Final_Pitch_Deck.pptx to PDF + per-slide JPG (LibreOffice + pdftoppm).
set -e
cd "$(dirname "$0")/.."
D=deliverables/pitch_deck
.venv/bin/python scripts/build_final_deck.py
soffice --headless --convert-to pdf --outdir "$D" "$D/SlotSmith_Final_Pitch_Deck.pptx" >/dev/null 2>&1
rm -f "$D"/rendered/slide-*.jpg(N)
pdftoppm -r 144 -jpeg -jpegopt quality=90 "$D/SlotSmith_Final_Pitch_Deck.pdf" "$D/rendered/slide"
ls "$D" "$D/rendered"
