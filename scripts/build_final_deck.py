"""Build deliverables/pitch_deck/SlotSmith_Final_Pitch_Deck.pptx on the official Apex 3.0 template pages.

    .venv/bin/python scripts/build_final_deck.py

All measured numbers are read from the benchmark artifacts (see docs/pitch_deck/benchmark_audit.md);
the screenshots in deliverables/pitch_deck/assets/screens are crops of the real Streamlit workbench.
The original Round 1 deck (scripts/build_deck.py, deliverables/round1/) is left untouched.
Edit the three URL constants below to change the closing-slide links.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

from deck_lib import (AMBER, CYAN, GREEN, GREEN_DK, IO_COLORS, MUTED, PANEL, PANEL2, RED, TEXT, WHITE,  # noqa: E402
                      add_bg_slide, arrow, box, new_presentation, notes, rgb, text)

# ----------------------------------------------------------------------------- editable links
GITHUB_URL = "https://github.com/Sidd927/SlotSmith"
YOUTUBE_URL = "{{YOUTUBE_DEMO_URL}}"
DOCS_URL = "{{DOCUMENTATION_URL}}"

BG = ROOT / "deliverables" / "round1" / "build" / "bg"
PD = ROOT / "deliverables" / "pitch_deck"
SCREENS = PD / "assets" / "screens"
LOGOS = PD / "assets" / "logos"
OUT = PD / "SlotSmith_Final_Pitch_Deck.pptx"

TEAM = ["Aayush Aade (lead)", "Siddhant Patil", "Gaurang Bagwe"]
DIM = "7F9A86"          # dimmed text for planned items
SIDE_A, SIDE_B = "F2B84B", "5FC8F0"


# ----------------------------------------------------------------------------- evidence
def evidence() -> dict:
    """Numbers used on the slides, computed from the artifacts (never typed by hand)."""
    A = ROOT / "artifacts"
    runs = {"run1": A / "benchmarks.json", "run2": A / "repro" / "benchmarks_clean_run2.json",
            "run4": A / "pitch_deck_repro" / "benchmarks_rerun.json"}
    B = {k: json.loads(p.read_text()) for k, p in runs.items()}
    audit = json.loads((A / "audit" / "revision_status.json").read_text())
    per_case = []  # per case: list of moved counts over the 4 runs
    for i in range(10):
        vals = [B[k]["revisions"][i]["moved_incremental"] for k in B] + [audit["cases"][i]["moved"]]
        per_case.append({"signals": B["run1"]["revisions"][i]["signals"], "seed": B["run1"]["revisions"][i]["seed"],
                         "moved": vals, "scratch": B["run1"]["revisions"][i]["moved_from_scratch"]})
    totals = sorted(sum(c["moved"][j] for c in per_case) for j in range(4))
    scratch_totals = {sum(r["moved_from_scratch"] for r in b["revisions"]) for b in B.values()}
    assert len(scratch_totals) == 1
    walls = [b["summary"]["wall_20k_median_s"] for b in B.values()] + [5.93]  # + pre-audit run (benchmarks_pre_audit.json)
    pts = [(r["mdb_rows"], r["wall_s"]) for b in B.values() for r in b["scale"]]
    s1 = B["run1"]["summary"]
    return {"per_case": per_case, "totals": totals, "scratch_total": scratch_totals.pop(), "walls": walls, "pts": pts,
            "violations": max(b["summary"]["max_violations"] for b in B.values()),
            "tq": (s1["tq_detected"], s1["tq_injected"]), "over_exact": max(b["summary"]["baseplates_over_exact_max"] for b in B.values()),
            "n_scale_runs": len(B["run1"]["scale"]), "cpsat": (audit["summary"]["accepted_proven_exact"], audit["summary"]["accepted_windows"]),
            "cpsat_cases": s1["rev_cpsat_cases"], "machine": B["run1"]["machine"]["cpu"], "ram": B["run1"]["machine"]["ram_gb"]}


# ----------------------------------------------------------------------------- small helpers
def T(s, x, y, w, h, paras, size=12, **kw):
    return text(s, x, y, w, h, paras, size=size, **kw)


def run(t, **o):
    return (t, o)


def panel(s, x, y, w, h, title=None, line=GREEN_DK, tcol=GREEN, fill=PANEL, tr=10, tsize=11, dash=False):
    box(s, x, y, w, h, fill=fill, line=line, transparency=tr, radius=0.04, dash=dash)
    if title:
        T(s, x + 0.18, y + 0.08, w - 0.3, 0.3, [[run(title, bold=True)]], size=tsize, color=tcol)


def chip(s, x, y, w, h, label, fill=GREEN, fg="06140A", size=10, bold=True, line=None, dash=False):
    b = box(s, x, y, w, h, fill=fill, line=line, radius=0.35, dash=dash)
    T(s, 0, 0, 0, 0, [label], size=size, color=fg, bold=bold, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
    return b


STATUS = {"built": ("Built", GREEN, "06140A", None), "planned": ("Planned", None, AMBER, AMBER),
          "idea": ("Idea, untested", None, DIM, DIM), "synthetic": ("Synthetic data", None, CYAN, CYAN)}


def status(s, x, y, kind, w=None, size=9.5):
    label, fill, fg, line = STATUS[kind]
    w = w or 0.11 * len(label) + 0.3
    if fill is None:
        chip(s, x, y, w, 0.24, label, fill="06140A", fg=fg, size=size, line=line, dash=(kind != "synthetic"))
    else:
        chip(s, x, y, w, 0.24, label, fill=fill, fg=fg, size=size)
    return w


def cells(s, x, y, kinds, cw=0.3, ch=0.3, gap=0.04, labels=None, size=9):
    for i, k in enumerate(kinds):
        cx = x + i * (cw + gap)
        if k in ("A", "B"):
            col = SIDE_A if k == "A" else SIDE_B
            b = box(s, cx, y, cw, ch, fill="2A2208" if k == "A" else "0B2B38", line=col, line_w=1.25, radius=0.15)
            T(s, 0, 0, 0, 0, [k], size=size, color=col, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
        else:
            col = IO_COLORS[k]
            b = box(s, cx, y, cw, ch, fill=col, line="2E4A35" if k == "FREE" else None, line_w=0.75, radius=0.15)
            if labels and labels.get(i):
                T(s, 0, 0, 0, 0, [labels[i]], size=size, color="06140A", bold=True, align=PP_ALIGN.CENTER,
                  anchor=MSO_ANCHOR.MIDDLE, shape=b)


def logo_png(name: str) -> Path | None:
    """Render a Simple Icons SVG (CC0 data) in the deck's light text colour."""
    src, dst = LOGOS / f"{name}.svg", LOGOS / f"{name}_light.png"
    if dst.exists():
        return dst
    if not src.exists():
        return None
    import pymupdf
    svg = src.read_text().replace("<svg ", f'<svg fill="#{TEXT}" ', 1).encode()
    doc = pymupdf.open(stream=svg, filetype="svg")
    doc[0].get_pixmap(matrix=pymupdf.Matrix(12, 12), alpha=True).save(str(dst))
    return dst


def fmt(n) -> str:
    return f"{int(n):,}"


# ============================================================================= slide 1
def slide1(prs, E):
    s = add_bg_slide(prs, str(BG / "bg1.jpg"))
    T(s, 3.38, 5.225, 6.0, 0.35, [[run("Mac_Enthu", bold=True)]], size=17, color=WHITE)
    T(s, 4.55, 5.64, 6.0, 0.35, [[run("Aayush Aade", bold=True)]], size=17, color=WHITE)
    T(s, 6.12, 6.07, 6.8, 0.35, [[run("Track 1 (Emerson) · PS 1.2 Project IO SIGNAL SUDOKU", bold=True)]], size=15, color=WHITE)
    T(s, 1.67, 6.42, 11.2, 0.3, [[run("SlotSmith", bold=True, color=GREEN, size=15),
                                 run("  ·  rule-driven, independently checked, revision-aware DeltaV I/O allocation", color=TEXT, size=14)]])
    T(s, 1.67, 6.69, 11.2, 0.22, [[run("Places each signal in cabinet → CIOC → baseplate → CHARM under project rules and re-checks the export independently. "
                                      "Prototype, synthetic data.", color=MUTED, size=10.5)]])
    notes(s, "Team Mac_Enthu. Track 1 (Emerson), PS 1.2 Project IO SIGNAL SUDOKU. SlotSmith is a working prototype tested on synthetic data only; "
             "no organiser sample data or template had been released when this deck was prepared.")


# ============================================================================= slide 2
def slide2(prs, E):
    s = add_bg_slide(prs, str(BG / "bg2.jpg"))
    # The template prints the three headings (Who is affected / The current gap / Why it matters now); text sits under them.
    L, W = 0.78, 6.55
    T(s, L, 2.72, W, 1.0, [[run("DeltaV project and I/O engineers ", bold=True, color=WHITE),
                            run("must give every field signal an exact home: cabinet → CIOC → baseplate → CHARM slot. "
                                "Panel builders and site teams then wire to that allocation.")]], size=12.5)
    T(s, L, 3.97, W + 0.1, 1.05, [[run("Emerson's PS: ", bold=True, color=WHITE),
                                   run("10,000+ signals are allocated by hand in Excel, and each customer revision means reworking it and tracing the impact again. "),
                                   run("DeltaV tools automate the steps around it (auto-sense, late binding, Bulk Edit); we found no public tool that places "
                                       "signals from project rules (internal tools may exist).", color=MUTED)]], size=12)
    T(s, L, 5.18, W + 0.1, 1.2, [[run("Electronic Marshalling makes late changes physically cheap (\"without lifting a wire\"), ", color=TEXT),
                                  run("but allocation planning and revision tracking remain a manual workflow burden (per the PS). ", bold=True, color=WHITE),
                                  run("Six interacting rules must hold at once, on every revision, with a technical query (TQ) for each data conflict.")]], size=12.5)
    T(s, L, 6.52, W + 0.1, 0.34, [[run("Sources: Emerson PS #02 p.4; DeltaV Electronic Marshalling PDS (Aug 2026); Smart Commissioning WP (2021) p.5; Bulk Edit WP (2022).",
                                       italic=True)]], size=9.5, color=MUTED)

    X, Y, PW, PH = 7.62, 1.92, 5.25, 4.88
    panel(s, X, Y, PW, PH, "THE PUZZLE, PER EMERSON'S RULEBOOK")
    hx, hy, hw, hh, hg = X + 0.2, Y + 0.42, 1.0, 0.56, 0.283
    for i, (a, b_) in enumerate([("Cabinet", "≤ 4 CIOCs"), ("CIOC", "8 baseplates"), ("Baseplate", "12 CHARMs"), ("CHARM", "1 signal")]):
        bx = hx + i * (hw + hg)
        bb = box(s, bx, hy, hw, hh, fill=PANEL2, line=GREEN, line_w=1, radius=0.12)
        T(s, 0, 0, 0, 0, [[run(a, bold=True, color=WHITE, size=11)], [run(b_, size=9.5, color=MUTED)]],
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=bb, spacing_after=0)
        if i < 3:
            arrow(s, bx + hw + 0.02, hy + hh / 2, bx + hw + hg - 0.02, hy + hh / 2, width=1.5)
    # one concrete interaction
    iy = Y + 1.1
    T(s, X + 0.2, iy, PW - 0.4, 0.26, [[run("ONE INTERACTION  two 6-pair cables, one on side A, one on side B", bold=True)]], size=10, color=AMBER)
    T(s, X + 0.2, iy + 0.3, 2.3, 0.22, ["Would fit one baseplate…"], size=10.5, color=TEXT)
    cells(s, X + 0.2, iy + 0.56, ["A"] * 6 + ["B"] * 6, cw=0.16, ch=0.26, gap=0.02, size=8)
    x_ = box(s, X + 0.2, iy + 0.9, 2.2, 0.28, fill="2A0F0F", line=RED, radius=0.3)
    T(s, 0, 0, 0, 0, [[run("✕ A and B never share a CIOC", color=RED, bold=True)]], size=9.5,
      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=x_)
    arrow(s, X + 2.55, iy + 0.7, X + 2.8, iy + 0.7, width=1.75)
    T(s, X + 2.9, iy + 0.3, 2.2, 0.22, ["…so each gets its own CIOC"], size=10.5, color=TEXT)
    cells(s, X + 2.9, iy + 0.56, ["A"] * 6 + ["FREE"] * 6, cw=0.16, ch=0.26, gap=0.02, size=8)
    cells(s, X + 2.9, iy + 0.9, ["B"] * 6 + ["FREE"] * 6, cw=0.16, ch=0.26, gap=0.02, size=8)
    T(s, X + 0.2, iy + 1.26, PW - 0.4, 0.5, [[run("Rule 4 keeps each cable whole, in pair order, so both baseplates stay half empty. "
                                                    "Capacity (rule 3) and the spare reserve (rule 5) must absorb that.", color=MUTED)]], size=10)
    # six rules -> eleven checks
    my = Y + 3.0
    T(s, X + 0.2, my, PW - 0.4, 0.26, [[run("SIX RULES, ELEVEN INDEPENDENT CHECKS", bold=True)]], size=10, color=GREEN)
    rules6 = [("1", "Groups together", "G-1"), ("2", "A and B apart", "S-1"), ("3", "Capacity 12·8·4", "C-1"),
              ("4", "Cable intact", "K-1"), ("5", "~10% spare", "P-1"), ("6", "CHARM + block", "H-1..6")]
    cw_, rh_ = 1.56, 0.36
    for i, (n, r_, fid) in enumerate(rules6):
        cx = X + 0.2 + (i % 3) * (cw_ + 0.085)
        cy = my + 0.3 + (i // 3) * (rh_ + 0.08)
        b = box(s, cx, cy, cw_, rh_, fill=PANEL2, line=GREEN_DK, radius=0.25)
        T(s, 0, 0, 0, 0, [[run(f"{n} {r_} ", color=WHITE), run(fid, color=AMBER, bold=True)]], size=9.3,
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, shape=b)
    b = box(s, X + 0.2, my + 1.2, PW - 0.4, 0.5, fill="0A2433", line=CYAN, radius=0.1)
    T(s, 0, 0, 0, 0, [[run("+5 checks on data and output: ", bold=True, color=CYAN),
                       run("Q-1 every signal placed or queried · D-2 one signal per slot · N-1..6 names · C-2 controllers · M-1 rows match the MDB", color=TEXT)]],
      size=9.3, shape=b, anchor=MSO_ANCHOR.MIDDLE, margin=0.1)
    notes(s, "Sources: Emerson PS #02 p.4-5 (six rules, 10,000+ signals by hand, revisions); DeltaV Electronic Marshalling PDS (12 CHARMs per baseplate, "
             "8 baseplates per CIOC; 4 CIOCs per cabinet is a PS project rule); Smart Commissioning and Bulk Edit white papers. "
             "The interaction example uses PS rule 2 (A and B never share a CIOC) and rule 4 (cable whole, in pair order); in the engine a cable that mixes A and B "
             "becomes a TQ (S-2). The six PS rules map to six verifier families (G-1, S-1, C-1, K-1, P-1, H-1..6); the verifier has five more "
             "(Q-1, D-2, N-1..6, C-2, M-1), 11 in total (src/slotsmith/verifier.py CHECKS). 'We found no public tool' reflects the sources reviewed, not proof of absence.")


# ============================================================================= slide 3
def slide3(prs, E):
    s = add_bg_slide(prs, str(BG / "bg3.jpg"))
    # The template prints three headings on the left (What makes it different / Core mechanism / Why it's feasible in this timeframe).
    L, W = 0.7, 7.1
    pts = [("Independently checked: ", "a separate module re-reads the exported file (11 checks)."),
           ("Revision-aware: ", "unchanged cables stay put; CP-SAT repairs a local window."),
           ("Configurable: ", "rule parameters live in JSON; new rule types may need code."),
           ("Traceable: ", "every TQ cites a rule ID and the file, sheet and row.")]
    T(s, L, 2.8, W, 1.05, [{"runs": [(a, {"bold": True, "color": WHITE}), (b_, {})], "bullet": True} for a, b_ in pts], size=11.8, spacing_after=1)
    T(s, L, 4.22, W, 1.1, [[run("Baseline allocation is constructive, with no solver: ", bold=True, color=WHITE),
                            run("each cable becomes one block of 24/12/6/2 slots and first-fit-decreasing (FFD) packs blocks per group and A/B side into baseplates, CIOCs and cabinets. "),
                            run("CP-SAT enters only to repair a revision (10 s limit per window) and reports each window as proven exact or best found.", color=MUTED)]], size=11.8)
    T(s, L, 5.62, W, 0.95, [[run("Open-source Python, OR-Tools and openpyxl; 122 automated tests pass. The prototype allocates and verifies 20,033 synthetic signals in about 6 s on a laptop (slide 6). "
                                 "AI helpers are planned and would only suggest; none runs today.")]], size=12)

    # right: workflow
    X, Y, PW = 7.95, 1.92, 4.92
    panel(s, X, Y, PW, 3.05, "WORKFLOW")
    steps = [("1 Input", GREEN, "Excel or CSV lists; columns auto-mapped; file · sheet · row kept"),
             ("2 Validate", GREEN, "Missing, duplicate or conflicting data → TQs with rule ID"),
             ("3 Allocate", GREEN, "Constructive first-fit-decreasing packing, no solver"),
             ("4 Verify", AMBER, "Separate module re-reads the exported file; 11 checks"),
             ("5 Revise", GREEN, "Pin unchanged, CP-SAT window repair, impact sheet")]
    for i, (a, col, d) in enumerate(steps):
        yy = Y + 0.42 + i * 0.52
        b = box(s, X + 0.18, yy, 1.2, 0.4, fill="2A1F0A" if col == AMBER else PANEL2, line=col, line_w=1.4, radius=0.15)
        T(s, 0, 0, 0, 0, [[run(a, bold=True, color=col, size=11.5)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
        T(s, X + 1.5, yy - 0.02, PW - 1.65, 0.45, [d], size=10.3, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
        if i < 4:
            arrow(s, X + 0.78, yy + 0.4, X + 0.78, yy + 0.52, color=col if col == AMBER else GREEN, width=1.4)
    # proved / tested / not claimed
    ty = Y + 3.15
    rows = [("PROVED", GREEN, "First-fit-decreasing uses the fewest baseplates for one A/B side with cable sizes 2/6/12."),
            ("TESTED", CYAN, "Group baseplate totals matched exact CP-SAT optima in all 19,682 small cases and 148 of 150 larger groups (2 unproven, none worse)."),
            ("NOT CLAIMED", AMBER, "Minimum CIOCs, cabinets or revision moves; global optimality; results on organiser data.")]
    panel(s, X, ty, PW, 1.73, tr=8)
    for i, (a, col, d) in enumerate(rows):
        yy = ty + 0.1 + i * 0.54
        chip(s, X + 0.18, yy + 0.08, 1.2, 0.3, a, fill="06140A", fg=col, size=10, line=col)
        T(s, X + 1.5, yy, PW - 1.65, 0.52, [d], size=10, color=TEXT, anchor=MSO_ANCHOR.MIDDLE)
    notes(s, "Allocation is constructive (per-class first-fit-decreasing); CP-SAT is used only to repair revisions inside a window of cabinets. "
             "Proof: docs/architecture.md section 4 (divisible item sizes 2, 6, 12 with capacity 12: free space is always a multiple of the current size, "
             "so FFD opens a new bin only when all others are full). Exhaustive audit: artifacts/audit/ffd_exact.json (19,682 group cases against CP-SAT, all solved to OPTIMAL, "
             "0 worse), artifacts/audit/lb_gap.json (150 random larger groups, 148 OPTIMAL / 2 FEASIBLE, 0 worse). The audit compares baseplate counts per group "
             "under the same A/B and group-isolation rules; it does not cover CIOC or cabinet counts. Verifier: src/slotsmith/verifier.py imports only rules.py; "
             "pipeline.py re-reads the exported workbook before verifying. 122 tests = 31 engine (25 + 6 audit regressions) + 91 UI.")


# ============================================================================= slide 4
def slide4(prs, E):
    s = add_bg_slide(prs, str(BG / "bg4.jpg"))
    # --- left: the template prints five stack boxes (Frontend / Backend / Database / AI-APIs / Hosting-DevOps); text goes inside them
    boxes = [(2.21, "Streamlit workbench (built): 7 stages, cabinet map, TQs, revision diff", ["streamlit"]),
             (3.03, "Python 3.12 · pandas · openpyxl · pydantic typed rule sets · CLI", ["python", "pandas", "pydantic"]),
             (3.86, "No database: xlsx / csv in, JSON rule sets, xlsx workbooks out", []),
             (4.73, "OR-Tools CP-SAT for revision repair only. No LLM runs today; an optional helper is planned", []),
             (5.60, "Local run · pytest + Hypothesis · Docker bundle planned", [])]
    for y, t_, logos in boxes:
        x_t = 2.85 if y > 5.5 else 1.98     # the template's "Hosting / DevOps" label is wider than the others
        T(s, x_t, y + 0.03, 4.5 - x_t, 0.42 if logos else 0.62, [t_], size=10, color=TEXT, anchor=MSO_ANCHOR.TOP if logos else MSO_ANCHOR.MIDDLE)
        for j, lg in enumerate(logos):
            lp = logo_png(lg)
            if lp:
                s.shapes.add_picture(str(lp), Inches(1.98 + j * 0.36), Inches(y + 0.4), height=Inches(0.24))

    # --- right: data flow in three lanes on one grid
    DX, DY, DW, DH = 4.95, 1.92, 7.93, 4.88
    panel(s, DX, DY, DW, DH)
    T(s, DX + 0.18, DY + 0.07, DW - 0.3, 0.26, [[run("DATA FLOW", bold=True), run("   solid = built · amber = verification · dashed = planned", color=MUTED, size=10)]],
      size=11, color=GREEN)
    nw, g = 1.13, 0.17
    cx = lambda k: DX + 0.18 + k * (nw + g)

    def node(x, y, w, h, title, sub, col=GREEN, fill=PANEL2, dash=False, tcol=WHITE):
        b = box(s, x, y, w, h, fill=fill, line=col, line_w=1.4, radius=0.1, dash=dash)
        T(s, 0, 0, 0, 0, [[run(title, bold=True, color=tcol, size=10.8)], [run(sub, size=9, color=MUTED if not dash else DIM)]],
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b, spacing_after=0)
        return b

    rb = box(s, DX + 0.18, DY + 0.4, DW - 0.36, 0.36, fill="12202A", line=CYAN, radius=0.3)
    T(s, 0, 0, 0, 0, [[run("Rule set ", bold=True, color=CYAN), run("JSON, typed with pydantic · read by validate, allocate, revise and verify", color=TEXT)]],
      size=10.3, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=rb)
    ay, nh = DY + 0.95, 0.82
    node(cx(0), ay, nw, nh, "Rev A list", "xlsx or csv, one or many files", col=CYAN, fill="12202A")
    node(cx(1), ay, nw, nh, "Ingest", "map columns, keep file·sheet·row")
    node(cx(2), ay, nw, nh, "Validate", "rules + data → TQs")
    node(cx(3), ay, nw, nh, "Allocate", "FFD packing → baseplates, CIOCs, cabinets")
    node(cx(4), ay, nw, nh, "Export", "writes the workbook sheets")
    node(cx(5), ay, nw, nh, "Workbook", "sheets: allocation, summary, TQs, rule check", col=CYAN, fill="12202A")
    for k in range(5):
        arrow(s, cx(k) + nw + 0.01, ay + nh / 2, cx(k + 1) - 0.01, ay + nh / 2, width=1.75)
    by = ay + nh + 0.45
    node(cx(2), by, nw, nh, "Rev B list", "xlsx or csv", col=CYAN, fill="12202A")
    node(cx(3), by, nw * 2 + g, nh, "Revision engine", "pin unchanged → greedy fill → CP-SAT window repair → full re-run only as fallback")
    arrow(s, cx(2) + nw + 0.01, by + nh / 2, cx(3) - 0.01, by + nh / 2, width=1.75)
    arrow(s, cx(4) + nw / 2, by - 0.01, cx(4) + nw / 2, ay + nh + 0.01, width=1.75)
    T(s, cx(0), by + 0.05, nw * 2 + g, nh, [[run("Revisions add a Revision Impact sheet: added, deleted, moved, modified.", italic=True, color=MUTED)]], size=9.5)
    node(cx(5), by, nw, nh, "Verify", "11 checks on the exported file", col=AMBER, fill="2A1F0A", tcol=AMBER)
    arrow(s, cx(5) + nw / 2, ay + nh + 0.01, cx(5) + nw / 2, by - 0.01, color=AMBER, width=1.75)
    # lane C: surfaces, storage, planned
    cy_ = by + nh + 0.38
    T(s, DX + 0.18, cy_ - 0.01, 5, 0.22, [[run("SURFACES, TESTS AND STORAGE", bold=True)]], size=9.5, color=MUTED)
    sy = cy_ + 0.24
    sh = 0.72
    node(cx(0), sy, nw, sh, "Streamlit", "7-stage workbench")
    node(cx(1), sy, nw, sh, "CLI", "slotsmith run / revise")
    node(cx(2), sy, nw, sh, "pytest", "122 tests")
    node(cx(3), sy, nw, sh, "Files only", "no database")
    node(cx(4), sy, nw, sh, "LLM helper", "planned", col=DIM, dash=True, tcol=DIM, fill="06140A")
    node(cx(5), sy, nw, sh, "Docker", "planned", col=DIM, dash=True, tcol=DIM, fill="06140A")
    T(s, DX + 0.18, DY + DH - 0.3, DW - 0.4, 0.26, [[run("The verifier imports only the rule set and parses exported names back into positions.",
                                                          italic=True, color=MUTED)]], size=9.3)
    notes(s, "Follows src/slotsmith: ingest.py, validate.py, rules.py, allocator.py, export.py, verifier.py, revision.py + repair_cpsat.py, pipeline.py, cli.py; "
             "UI in app/. Verifier imports only rules.py. pipeline.run re-reads the exported workbook for verification. "
             "Planned items per docs/technology_decisions.md: optional LLM for mapping suggestions and rule drafts (never in the placement path), Docker deferred, "
             "React optional later. A SQLite run log appeared in the earlier deck but is not in the code or docs, so it is no longer shown. "
             "Technology logos: Simple Icons (CC0 data), see docs/pitch_deck/research_notes.md; openpyxl and OR-Tools have no logo here and are text.")


# ============================================================================= slide 5
def slide5(prs, E):
    s = add_bg_slide(prs, str(BG / "bg5.jpg"))
    stages = ["Input", "Review", "Allocate", "Results", "Cabinets", "Revise (Rev B)", "Deliverables"]
    x = 0.6
    T(s, x, 1.93, 2.6, 0.3, [[run("WORKBENCH · 7 STAGES BUILT", bold=True)]], size=10.5, color=GREEN)
    x = 3.2
    for i, st_ in enumerate(stages):
        w = 0.092 * len(st_) + 0.45
        b = box(s, x, 1.93, w, 0.3, fill=PANEL2, line=GREEN, radius=0.3)
        T(s, 0, 0, 0, 0, [f"{i + 1} · {st_}"], size=10.5, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
        x += w + 0.1
    # dominant screenshot
    iy = 2.36
    from PIL import Image
    def pic(name, x, y, w):
        im = Image.open(SCREENS / name)
        h = w * im.size[1] / im.size[0]
        s.shapes.add_picture(str(SCREENS / name), Inches(x), Inches(y), Inches(w), Inches(h))
        box(s, x, y, w, h, fill=None, line=GREEN_DK, line_w=1, radius=0.0, shape=MSO_SHAPE.RECTANGLE)
        return h
    h1 = pic("ui_cabinets.png", 0.6, iy, 5.75)
    T(s, 0.6, iy + h1 + 0.05, 5.75, 0.4, [[run("Cabinet inspector. ", bold=True, color=WHITE),
                                           run("Every slot shows its signal type; hatched = wired spare, ! = held for a TQ. "
                                               "2 of 4 CIOCs of cabinet AR1-DCM-100-01.", color=MUTED)]], size=10.5)
    # supporting: results and revision, with annotations
    rx, rw = 6.55, 3.6
    h2 = pic("ui_results.png", rx, iy, rw)
    h3 = pic("ui_revise.png", rx, iy + h2 + 0.14, rw)
    ax, aw = rx + rw + 0.18, 12.85 - (rx + rw + 0.18)
    T(s, ax, iy + 0.02, aw, h2, [[run("RESULTS", bold=True, color=GREEN, size=10)], [run("0 violations", bold=True, color=WHITE, size=19)],
                                 [run("Verifier re-read the exported rows: all 11 rule families pass, for this dataset and these rules only.")],
                                 [run("29 rows held under 6 blocking TQs; every row placed or queried.", color=MUTED)]], size=10.8, spacing_after=3)
    T(s, ax, iy + h2 + 0.16, aw, h3, [[run("REVISE (REV B)", bold=True, color=GREEN, size=10)], [run("46 moved", bold=True, color=WHITE, size=19)],
                                      [run("of 1,981 allocated signals; 111 added, 58 deleted, 28 modified in place, 0 violations.")],
                                      [run("Repair window proven exact in this run; runs can differ.", color=MUTED)]], size=10.8, spacing_after=3)
    T(s, 0.6, 6.62, 12.25, 0.22, [[run("Real screenshots of the current build, captured 11 Oct 2026. Data is SYNTHETIC: 2,000-signal MDB with 6 injected errors plus a synthetic Rev B. "
                                       "Not customer data.", italic=True, color=AMBER)]], size=10)
    notes(s, "Crops of the running Streamlit workbench (app/), dark theme, synthetic demo dataset (seed 7, 2,000 signals, 6 injected errors). Screens: Cabinets, Results, Revise (Rev B). "
             "Capture method and raw files: docs/pitch_deck/visual_qa_report.md and deliverables/pitch_deck/assets/screens/raw. "
             "Numbers on the slide are read from those screenshots. Repair-window status and move counts vary between runs (CP-SAT, multi-threaded, wall-clock limit).")


# ============================================================================= slide 6
def slide6(prs, E):
    s = add_bg_slide(prs, str(BG / "bg6.jpg"))
    cols = [("BUILT · AS OF 11 OCT", "built", GREEN, False, ["Engine: ingest to verified export", "Revision engine + CP-SAT repair",
                                                              "Streamlit workbench, 7 stages", "122 automated tests pass"]),
            ("ROUND 2 · 15–18 OCT", "planned", AMBER, True, ["Map export to organiser template, if released", "Confirm open rule readings with mentors",
                                                            "Reduce CP-SAT run-to-run variance", "UI: mapping review and override"]),
            ("GRAND FINALE · 24 OCT", "planned", CYAN, True, ["Run on organiser samples + hidden test", "AI mapping suggestions, user-reviewed",
                                                            "Demo hardening, offline bundle"]),
            ("BEYOND", "idea", DIM, True, ["Bulk-Edit-style export (format unvalidated)", "Other electronic-marshalling platforms", "Cabinet labels and drawings"])]
    x0, w, g, y = 0.6, 2.98, 0.11, 1.95
    spine_y = y + 0.1
    box(s, x0, spine_y - 0.02, 12.25, 0.04, fill=GREEN_DK, line=None, radius=0.0, shape=MSO_SHAPE.RECTANGLE)
    for i, (title, kind, col, dash, items) in enumerate(cols):
        xx = x0 + i * (w + g)
        box(s, xx + 0.12, spine_y - 0.09, 0.18, 0.18, fill=col if not dash else "06140A", line=col, line_w=1.5, shape=MSO_SHAPE.OVAL, dash=dash)
        panel(s, xx, y + 0.28, w, 1.58, line=col, tcol=col, tr=8, dash=dash)
        T(s, xx + 0.15, y + 0.33, w - 0.9, 0.28, [[run(title, bold=True)]], size=10.5, color=col)
        status(s, xx + w - (0.8 if kind != "idea" else 1.2) - 0.1, y + 0.34, kind, w=0.8 if kind != "idea" else 1.2, size=9)
        T(s, xx + 0.15, y + 0.66, w - 0.25, 1.12, [{"runs": [(it, {"color": TEXT if kind == "built" else "C9D9CD"})], "bullet": True} for it in items],
          size=10.5, spacing_after=2)
    # --- evidence zone
    ey = y + 1.92
    T(s, 0.6, ey, 12.25, 0.24, [[run("EVIDENCE · SYNTHETIC DATA ONLY", bold=True, color=CYAN),
                                 run(f"   {E['machine']} laptop, {E['ram']} GB · not evidence about the hidden test", italic=True, color=MUTED)]], size=10.5)
    # chart panel
    cx, cy, cw, ch = 0.6, ey + 0.27, 7.7, 2.4
    panel(s, cx, cy, cw, ch)
    lo, hi = E["totals"][0], E["totals"][-1]
    T(s, cx + 0.15, cy + 0.06, cw - 0.3, 0.3, [[run("Revision cost: signals moved per case, log scale", bold=True, color=GREEN, size=11),
                                                run(f"   total {lo}–{hi} over 4 runs vs {fmt(E['scratch_total'])} for a full re-run", color=WHITE, size=10.5)]])
    # plot
    px0, pw = cx + 0.55, cw - 0.75
    py_top, py_bot = cy + 0.62, cy + 1.7
    decade_h = (py_bot - py_top) / 4.0
    def yv(v):
        return py_bot - math.log10(max(v, 1)) * decade_h
    for d in range(0, 5):
        yy = py_bot - d * decade_h
        box(s, px0, yy - 0.004, pw, 0.008, fill="1F3A26", line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
        T(s, cx + 0.1, yy - 0.09, 0.42, 0.18, [f"{10 ** d:,}"], size=8.5, color=MUTED, align=PP_ALIGN.RIGHT)
    gw = pw / 10
    bw = gw * 0.34
    for i, c in enumerate(E["per_case"]):
        gx = px0 + i * gw
        med = statistics.median(c["moved"])
        mn, mx = min(c["moved"]), max(c["moved"])
        b1x = gx + gw * 0.12
        b2x = b1x + bw + 0.03
        box(s, b1x, yv(med), bw, py_bot - yv(med), fill=GREEN, line=None, radius=0.0, shape=MSO_SHAPE.RECTANGLE)
        box(s, b2x, yv(c["scratch"]), bw, py_bot - yv(c["scratch"]), fill="C98A2B", line=None, radius=0.0, shape=MSO_SHAPE.RECTANGLE)
        if mx != mn:  # whisker for run-to-run range
            wx = b1x + bw / 2
            box(s, wx - 0.008, yv(mx), 0.016, yv(mn) - yv(mx), fill=WHITE, line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
            box(s, wx - 0.05, yv(mx) - 0.008, 0.1, 0.016, fill=WHITE, line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
        lab = f"{mn}" if mn == mx else f"{mn}–{mx}"
        T(s, gx - 0.02, py_bot + 0.03, gw, 0.18, [f"{'2k' if c['signals'] == 2000 else '10k'}·{c['seed']}"], size=8.5, color=MUTED, align=PP_ALIGN.CENTER)
        T(s, gx - 0.02, py_bot + 0.2, gw, 0.18, [lab], size=8.5, color=GREEN, bold=True, align=PP_ALIGN.CENTER)
    # legend
    lx, ly = cx + 4.0, cy + 2.12
    box(s, lx - 3.3, ly + 0.04, 0.14, 0.14, fill=GREEN, line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
    T(s, lx - 3.12, ly, 3.6, 0.22, ["SlotSmith: median; green figures = min–max of 4 runs"], size=9, color=TEXT)
    box(s, lx + 0.1, ly + 0.04, 0.14, 0.14, fill="C98A2B", line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
    T(s, lx + 0.28, ly, 3.4, 0.22, ["Full re-run of Rev B (same in all 4 runs)"], size=9, color=TEXT)
    # metric cards
    mx0, mw = 8.45, 4.4
    cards = [(str(E["violations"]), "verifier violations", f"{E['n_scale_runs']} allocation runs, 10 revisions, 500 to 20,033 signals"),
             (f"{E['tq'][0]}/{E['tq'][1]}", "injected errors raised as TQs", "3 synthetic MDBs, 27 errors each"),
             (str(E["over_exact"]), "baseplates over the exact minimum", f"closed form, sizes 2/6/12, {E['n_scale_runs']} runs"),
             (f"{E['cpsat'][0]} of {E['cpsat'][1]}", "repair windows proven exact", f"{E['cpsat'][1] - E['cpsat'][0]} best-found; {E['cpsat_cases']} of 10 revisions used CP-SAT")]
    chh = 1.16
    for i, (big, label, sub) in enumerate(cards):
        xx = mx0 + (i % 2) * (mw / 2 + 0.05)
        yy = cy + (i // 2) * (chh + 0.08)
        panel(s, xx, yy, mw / 2 - 0.05, chh, tr=8)
        T(s, xx + 0.12, yy + 0.03, mw / 2 - 0.3, 0.38, [[run(big, bold=True)]], size=20, color=WHITE)
        T(s, xx + 0.12, yy + 0.42, mw / 2 - 0.28, 0.36, [[run(label, bold=True)]], size=9.5, color=GREEN)
        T(s, xx + 0.12, yy + 0.78, mw / 2 - 0.28, 0.36, [[run(sub, color=MUTED)]], size=8.8)
    T(s, 0.6, 6.57, 12.25, 0.24, [[run("Event dates from the Code Apex 3.0 handbook (subject to change); roadmap items are intentions, not commitments. "
                                     "The re-run baseline re-allocates Rev B from scratch with the same engine; it is a naive reference, not an optimum.", italic=True, color=MUTED)]], size=9)
    notes(s, "Revision metric: 10 synthetic revision cases (5 at 2,000 signals, 5 at 10,000), Rev B = about 3% deleted, 5% added, 2% type changes, 1 cable regrouped. "
             "Moves are counted identically for both methods with revision.impact_report: a tag present in both revisions whose cabinet/CIOC/baseplate/slot differs. "
             f"SlotSmith total moved over the 10 cases in 4 independent runs: {', '.join(map(str, E['totals']))}; the full re-run total is {fmt(E['scratch_total'])} in every run (deterministic). "
             "The difference between runs comes from CP-SAT repair (multi-threaded under a wall-clock limit). One run overlapped with other CPU load and gave a worse result for one case; "
             "the cause was not isolated. 'Cases' vs 'windows': 7 of the 10 revisions needed CP-SAT; across those, 11 repair windows were accepted (7 proven exact, 4 best-found within 10 s); "
             "further windows were tried and rejected as infeasible or unanswered. 'Exact per-group minimum' is the closed-form minimum from the divisible-size lemma "
             "(allocator.exact_group_baseplates), validated against CP-SAT in the exhaustive audit. All 12 allocation runs: 0 violations, 100% of rows placed or covered by a TQ. "
             "Sources: artifacts/benchmarks.json, artifacts/repro/benchmarks_clean_run2.json, artifacts/pitch_deck_repro/benchmarks_rerun.json, artifacts/audit/revision_status.json. "
             "Dates: HANDBOOK_CODEAPEX_3.0.pdf timeline (Round 2 15-18 Oct, Grand Finale 24 Oct).")


# ============================================================================= slide 7
def slide7(prs, E):
    s = add_bg_slide(prs, str(BG / "bg7.jpg"))
    # --- runtime chart (measured)
    X, Y, W, H = 0.6, 1.95, 6.05, 2.5
    panel(s, X, Y, W, H)
    T(s, X + 0.15, Y + 0.06, W - 0.3, 0.3, [[run("MEASURED TODAY · SYNTHETIC", bold=True, color=GREEN, size=11),
                                             run("   end-to-end time vs signals", color=WHITE, size=10.5)]])
    px0, pw = X + 0.65, W - 0.95
    py_top, py_bot = Y + 0.42, Y + 1.55
    xmax, ymax = 21000, 9
    xv = lambda v: px0 + v / xmax * pw
    yv = lambda v: py_bot - v / ymax * (py_bot - py_top)
    for t_ in (0, 3, 6, 9):
        box(s, px0, yv(t_) - 0.004, pw, 0.008, fill="1F3A26", line=None, radius=0, shape=MSO_SHAPE.RECTANGLE)
        T(s, X + 0.1, yv(t_) - 0.09, 0.5, 0.18, [f"{t_} s"], size=8.5, color=MUTED, align=PP_ALIGN.RIGHT)
    for t_ in (500, 5000, 10000, 15000, 20000):
        T(s, xv(t_) - 0.35, py_bot + 0.04, 0.7, 0.18, [f"{t_:,}"], size=8.5, color=MUTED, align=PP_ALIGN.CENTER)
    for n, t_ in E["pts"]:
        box(s, xv(n) - 0.045, yv(t_) - 0.045, 0.09, 0.09, fill=GREEN, line=None, shape=MSO_SHAPE.OVAL, transparency=25)
    med = {}
    for n, t_ in E["pts"]:
        med.setdefault(500 if n < 1000 else int(round(n, -3)) if n < 5000 else 10000 if n < 15000 else 20000, []).append(t_)
    prev = None
    for k in sorted(med):
        m = statistics.median(med[k])
        if prev:
            ln = s.shapes.add_connector(1, Inches(xv(prev[0])), Inches(yv(prev[1])), Inches(xv(k)), Inches(yv(m)))
            ln.line.color.rgb = rgb(CYAN)
            ln.line.width = Pt(1.25)
        prev = (k, m)
    T(s, X + 0.15, Y + H - 0.62, W - 0.3, 0.6, [[run("Dots: every allocation run in 3 batches (3 per size); line: medians. 20,033 signals took about 6 s on one laptop "
                                                     "(batch medians 6.0, 6.0, 6.3 s; one 8.7 s outlier). Observed, not a complexity proof. "
                                                     "Allocation alone is about 0.01 s; the rest is Excel I/O, validation and verification.", color=MUTED)]], size=9.3)
    # --- expected benefits
    bx, bw = 6.8, 6.05
    panel(s, bx, Y, bw, H, "EXPECTED BENEFITS · NOT MEASURED", tcol=GREEN)
    ben = [("IO / project engineers", "Allocation becomes a re-runnable, rule-checked step instead of hand-editing 10,000+ rows."),
           ("Reviewers and QA", "Every export carries a rule-check report; every placement and TQ traces to a file, sheet and row."),
           ("Customers and EPCs", "Specific, traceable TQs and a Rev A → Rev B impact list.")]
    for i, (a, b_) in enumerate(ben):
        yy = Y + 0.42 + i * 0.64
        T(s, bx + 0.2, yy, bw - 0.4, 0.25, [[run(a, bold=True, color=WHITE)]], size=11.5)
        T(s, bx + 0.2, yy + 0.23, bw - 0.4, 0.42, [b_], size=10.8, color=TEXT)
    T(s, bx + 0.2, Y + H - 0.3, bw - 0.4, 0.25, [[run("No time or cost saving has been measured, so none is claimed.", italic=True, color=AMBER)]], size=10)
    # --- bottom row
    y2 = Y + H + 0.12
    h2 = 6.8 - y2
    panel(s, 0.6, y2, 3.95, h2, "SCALE CONTEXT · SOURCED", tcol=GREEN)
    T(s, 0.8, y2 + 0.42, 3.6, 0.4, [[run("10,000+", bold=True)]], size=20, color=WHITE)
    T(s, 0.8, y2 + 0.82, 3.6, 0.5, ["signals per project, allocated by hand today (Emerson PS)"], size=10.5)
    T(s, 0.8, y2 + 1.3, 3.6, 0.4, [[run("≤ 28,800", bold=True)]], size=20, color=WHITE)
    T(s, 0.8, y2 + 1.7, 3.6, 0.6, ["CHARM channels per DeltaV system (300 CIOCs × 96): a spec maximum, not a typical project"], size=10.5)
    panel(s, 4.65, y2, 3.95, h2, "WHERE IT FITS", tcol=GREEN)
    b1 = box(s, 4.83, y2 + 0.45, 1.75, 1.0, fill=PANEL2, line=MUTED, radius=0.08)
    T(s, 0, 0, 0, 0, [[run("DeltaV tools", bold=True, color=WHITE, size=11)], [run("auto-sense, late binding, Bulk Edit", size=9.5, color=MUTED)]],
      shape=b1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing_after=1)
    b2 = box(s, 6.78, y2 + 0.45, 1.65, 1.0, fill=PANEL2, line=GREEN, radius=0.08)
    T(s, 0, 0, 0, 0, [[run("SlotSmith", bold=True, color=GREEN, size=11)], [run("allocation planning, checking, Rev B impact", size=9.5, color=TEXT)]],
      shape=b2, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing_after=1)
    arrow(s, 6.6, y2 + 0.95, 6.76, y2 + 0.95, width=1.5, dash=True)
    T(s, 4.83, y2 + 1.55, 3.65, 0.75, [[run("Complements DeltaV tools; it does not replace them. Export adapters to their import formats and other marshalling platforms are untested ideas.", color=MUTED)]], size=10)
    panel(s, 8.7, y2, 4.15, h2, "LIMITS · NEXT VALIDATION", line=AMBER, tcol=AMBER, fill="231A08", tr=8)
    T(s, 8.88, y2 + 0.4, 3.85, h2 - 0.45, [
        {"runs": [run("Next dependency: the organiser's sample MDB and allocation template (not released).", bold=True, color=WHITE)], "bullet": True},
        {"runs": [run("Synthetic data only; no official-template compatibility claimed.")], "bullet": True},
        {"runs": [run("Rule readings (straddling, spare rounding, controller mapping) await mentors.")], "bullet": True},
        {"runs": [run("New rule types need code; CP-SAT repair is window-local and varies between runs.")], "bullet": True}],
      size=10.3, spacing_after=2)
    notes(s, "Measured today: runtime points are every allocation run in three benchmark batches (about 500, 2,000, 10,000 and 20,000 signals, three seeds each) on an Apple M5, "
             "synthetic data. Wall time covers ingest, validate, allocate, export and verification. Observed scaling only; no asymptotic claim. One 20k run took 8.7 s while "
             "other work was running on the machine. Scale context: PS #02 p.4 (10,000+ signals); DeltaV Electronic Marshalling PDS 'Number of CIOCs per System: 300' and 96 channels "
             "per CIOC = 28,800 (specification maximum). Benefits are expected, not measured. Complement-not-replace: DeltaV auto-sense, late binding and Bulk Edit are documented by Emerson; "
             "SlotSmith plans the allocation before them.")


# ============================================================================= slide 8
def slide8(prs, E):
    s = add_bg_slide(prs, str(BG / "bg8.jpg"))
    T(s, 0.45, 6.12, 7.6, 0.4, [[run("Allocation you can re-run, check independently, and revise without starting over.", bold=True, color=WHITE)]], size=14)
    T(s, 0.45, 6.62, 7.8, 0.32, [[run("Team ", color=MUTED), run("Mac_Enthu", bold=True, color=WHITE), run("  ·  " + "  ·  ".join(TEAM), color=TEXT)]], size=12)
    X, Y, W = 8.35, 5.12, 4.5
    panel(s, X, Y, W, 1.75, "LINKS", tr=5)
    rows = [("GitHub", GITHUB_URL, True), ("Demo video", YOUTUBE_URL, False), ("Documentation", DOCS_URL, False)]
    for i, (a, u, link) in enumerate(rows):
        yy = Y + 0.46 + i * 0.4
        T(s, X + 0.18, yy, 1.35, 0.3, [[run(a, bold=True, color=MUTED)]], size=11)
        tb = T(s, X + 1.5, yy, W - 1.6, 0.3, [[run(u, color=CYAN if link else AMBER, size=11 if link else 12, bold=not link)]], size=11)
        if link:
            tb.click_action.hyperlink.address = u
    notes(s, "Links: the GitHub address is the team repository. The YouTube demo and documentation links are placeholders ({{YOUTUBE_DEMO_URL}}, {{DOCUMENTATION_URL}}) "
             "to be replaced before submission. Check that the repository is public or shared with the judges.")


def ensure_backgrounds():
    """Render the official template pages (PDF only) to slide backgrounds if they are missing (same as build_deck.py)."""
    if all((BG / f"bg{i}.jpg").exists() for i in range(1, 9)):
        return
    import pymupdf
    from PIL import Image
    BG.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(ROOT / "reference" / "official" / "Apex_3.0_PPT_Template.pdf")
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=144)
        Image.frombytes("RGB", [pix.width, pix.height], pix.samples).save(BG / f"bg{i}.jpg", quality=88)


def main():
    ensure_backgrounds()
    E = evidence()
    prs = new_presentation()
    prs.core_properties.title = "SlotSmith · VIT Code Apex 3.0 · Team Mac_Enthu (final pitch deck)"
    prs.core_properties.author = "Team Mac_Enthu"
    for f in (slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8):
        f(prs, E)
    PD.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
