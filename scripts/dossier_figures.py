"""Generate the data-driven figures of docs/SlotSmith_Technical_Dossier.md (pure Python SVG, PNG via PyMuPDF).

    .venv/bin/python scripts/dossier_figures.py

Inputs are the recorded benchmark artifacts; nothing is typed by hand.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "assets" / "slotsmith" / "charts"
DATA = ROOT / "docs" / "assets" / "slotsmith" / "data"
OUT.mkdir(parents=True, exist_ok=True)

A = ROOT / "artifacts"
BATCHES = [  # (label, file) in chronological order; all on one Apple M5 laptop, synthetic data, default rule set
    ("batch 1 (10 Oct, clean run 1)", A / "benchmarks.json"),
    ("batch 2 (10 Oct, clean run 2)", A / "repro" / "benchmarks_clean_run2.json"),
    ("batch 3 (11 Oct, re-run with other load)", A / "pitch_deck_repro" / "benchmarks_rerun.json"),
    ("batch 4 (11 Oct, light background load)", A / "dossier_repro" / "benchmarks_dossier.json"),
]
COLORS = ["#2f7d4a", "#3a6ea5", "#b07a00", "#8a3fa5"]
FONT = "Helvetica, Arial, sans-serif"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def add(self, s):
        self.parts.append(s)

    def rect(self, x, y, w, h, fill, stroke="none", sw=1, rx=0):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>')

    def line(self, x1, y1, x2, y2, stroke="#444", sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def circle(self, x, y, r, fill, op=1.0, stroke="none"):
        self.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}"/>')

    def text(self, x, y, s, size=12, fill="#222", anchor="start", weight="normal", rot=None):
        t = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{t}>{esc(s)}</text>')

    def save(self, name):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.parts) + "</svg>")
        (OUT / f"{name}.svg").write_text(svg)
        import pymupdf
        doc = pymupdf.open(stream=svg.encode(), filetype="svg")
        doc[0].get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5)).save(str(OUT / f"{name}.png"))


def load():
    runs = []
    for label, p in BATCHES:
        b = json.loads(p.read_text())
        runs.append({"label": label, "file": str(p.relative_to(ROOT)), "generated_at": b["generated_at"], "b": b})
    return runs


def runtime_chart(runs):
    s = Svg(900, 520)
    s.text(450, 28, "End-to-end time (ingest, validate, allocate, export, verify) vs. I/O list size", 15, anchor="middle", weight="bold")
    s.text(450, 48, "SYNTHETIC data, default rule set, Apple M5 (10 cores, 16 GB). 12 allocation runs per batch, 4 batches (48 points).", 11, "#555", "middle")
    x0, x1, y0, y1 = 90, 860, 440, 80
    xmax, ymax = 21000, 9.5
    X = lambda v: x0 + v / xmax * (x1 - x0)
    Y = lambda v: y0 - v / ymax * (y0 - y1)
    for t in range(0, 10, 2):
        s.line(x0, Y(t), x1, Y(t), "#e3e3e3")
        s.text(x0 - 8, Y(t) + 4, f"{t}", 11, "#444", "end")
    for t in (0, 5000, 10000, 15000, 20000):
        s.line(X(t), y0, X(t), y0 + 5, "#444")
        s.text(X(t), y0 + 20, f"{t:,}", 11, "#444", "middle")
    s.line(x0, y0, x1, y0)
    s.line(x0, y0, x0, y1)
    s.text(450, 490, "Rows in the I/O list (signals)", 12, anchor="middle")
    s.text(28, 260, "Wall time per run (seconds)", 12, anchor="middle", rot=-90)
    allp = {}
    for i, r in enumerate(runs):
        for sc in r["b"]["scale"]:
            n, t = sc["mdb_rows"], sc["wall_s"]
            bucket = 500 if n < 1000 else 2000 if n < 5000 else 10000 if n < 15000 else 20000
            allp.setdefault(bucket, []).append(t)
            s.circle(X(n) + (i - 1.5) * 4, Y(t), 4.5, COLORS[i], 0.75)
    pts = [(k, statistics.median(v)) for k, v in sorted(allp.items())]
    for (k1, m1), (k2, m2) in zip(pts, pts[1:]):
        s.line(X(k1), Y(m1), X(k2), Y(m2), "#222", 1.5, "5 3")
    for k, m in pts:
        s.text(X(k) + 14, Y(m) + 24, f"median {m:.2f} s", 11, "#222")
    for i, r in enumerate(runs):
        yy = 112 + i * 18
        s.circle(130, yy - 4, 4.5, COLORS[i], 0.85)
        s.text(142, yy, r["label"], 11)
    s.text(450, 510, "Line joins the medians of all 48 points per size. Batch 3 contains an 8.7 s outlier recorded while other work ran on the machine; batch 4 had only light background load.", 10, "#555", "middle")
    s.save("fig_I1_runtime")
    return {str(k): round(m, 3) for k, m in pts}


def revision_chart(runs):
    audits = [json.loads((A / "audit" / "revision_status.json").read_text()),
              json.loads((A / "dossier_repro" / "revision_status_run2.json").read_text())]
    cases = []
    for i in range(10):
        moved = [r["b"]["revisions"][i]["moved_incremental"] for r in runs] + [a["cases"][i]["moved"] for a in audits]
        b0 = runs[0]["b"]["revisions"][i]
        cases.append({"signals": b0["signals"], "seed": b0["seed"], "moved": moved, "scratch": b0["moved_from_scratch"]})
        assert all(r["b"]["revisions"][i]["moved_from_scratch"] == b0["moved_from_scratch"] for r in runs)
    s = Svg(960, 540)
    s.text(480, 28, "Signals moved by a Rev B revision, per case (log scale)", 15, anchor="middle", weight="bold")
    s.text(480, 48, "SYNTHETIC. 10 cases (2,000 and 10,000 signals x 5 seeds). Green: revision-aware engine, median of 6 runs, whisker = min to max. Orange: full re-allocation (identical in all runs).", 10.5, "#555", "middle")
    x0, x1, y0, y1 = 80, 930, 440, 90
    dec = (y0 - y1) / 4.0
    Y = lambda v: y0 - math.log10(max(v, 1)) * dec
    for d in range(5):
        yy = y0 - d * dec
        s.line(x0, yy, x1, yy, "#e3e3e3")
        s.text(x0 - 8, yy + 4, f"{10 ** d:,}", 11, "#444", "end")
    s.line(x0, y0, x1, y0)
    s.line(x0, y0, x0, y1)
    s.text(28, 265, "Signals moved (tag changes slot)", 12, anchor="middle", rot=-90)
    gw = (x1 - x0) / 10
    for i, c in enumerate(cases):
        gx = x0 + i * gw
        med, mn, mx = statistics.median(c["moved"]), min(c["moved"]), max(c["moved"])
        bw = gw * 0.34
        s.rect(gx + gw * 0.10, Y(med), bw, y0 - Y(med), "#2f7d4a")
        s.rect(gx + gw * 0.10 + bw + 3, Y(c["scratch"]), bw, y0 - Y(c["scratch"]), "#d08a2e")
        if mn != mx:
            wx = gx + gw * 0.10 + bw / 2
            s.line(wx, Y(mx), wx, Y(mn), "#111", 1.6)
            s.line(wx - 5, Y(mx), wx + 5, Y(mx), "#111", 1.6)
            s.line(wx - 5, Y(mn), wx + 5, Y(mn), "#111", 1.6)
        s.text(gx + gw / 2, y0 + 18, f"{'2k' if c['signals'] == 2000 else '10k'} #{c['seed']}", 11, "#444", "middle")
        s.text(gx + gw * 0.10 + bw / 2, Y(mx) - 6, f"{mn}" if mn == mx else f"{mn}-{mx}", 10, "#1d5a33", "middle", "bold")
        s.text(gx + gw * 0.10 + bw * 1.5 + 3, Y(c["scratch"]) - 6, f"{c['scratch']:,}", 10, "#8a5a10", "middle")
    s.rect(100, 480, 12, 12, "#2f7d4a")
    s.text(118, 491, "revision-aware engine: median of 6 runs, whisker min-max", 11)
    s.rect(500, 480, 12, 12, "#d08a2e")
    s.text(518, 491, "full re-allocation of Rev B with the same engine (naive reference)", 11)
    s.text(480, 520, "Moves counted identically for both methods (revision.impact_report). A lower number is better only while all hard rules hold (verifier violations were 0 in every case).", 10, "#555", "middle")
    s.save("fig_I2_revision_moves")
    totals = [sum(c["moved"][j] for c in cases) for j in range(len(cases[0]["moved"]))]
    return cases, totals


def main():
    runs = load()
    med = runtime_chart(runs)
    cases, totals = revision_chart(runs)
    summary = {"batches": [{"label": r["label"], "file": r["file"], "generated_at": r["generated_at"],
                            "wall_20k_median_s": r["b"]["summary"]["wall_20k_median_s"],
                            "rev_moved_total": r["b"]["summary"]["rev_moved_incremental_total"],
                            "rev_moved_scratch_total": r["b"]["summary"]["rev_moved_scratch_total"],
                            "cpsat_windows_status_OPTIMAL": r["b"]["summary"]["rev_cpsat_windows_accepted_optimal"],
                            "cpsat_windows_status_FEASIBLE_only": r["b"]["summary"]["rev_cpsat_windows_accepted_feasible_only"],
                            "max_violations": r["b"]["summary"]["max_violations"], "tq": f"{r['b']['summary']['tq_detected']}/{r['b']['summary']['tq_injected']}",
                            "baseplates_over_exact_max": r["b"]["summary"]["baseplates_over_exact_max"],
                            "rev_time_max_s": r["b"]["summary"]["rev_time_max_s"]} for r in runs],
               "runtime_median_by_size_s": med,
               "revision_total_moved_per_run_incl_status_audits": totals,
               "strict_proven_exact_windows_status_audits": [f"{a['summary']['accepted_proven_exact']}/{a['summary']['accepted_windows']}" for a in [json.loads((A / "audit" / "revision_status.json").read_text()), json.loads((A / "dossier_repro" / "revision_status_run2.json").read_text())]],
               "per_case": cases}
    (DATA / "benchmark_runs_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: v for k, v in summary.items() if k != "per_case"}, indent=1))


if __name__ == "__main__":
    main()
