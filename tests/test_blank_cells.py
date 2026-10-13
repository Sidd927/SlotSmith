"""Regression: a blank cell read from CSV/Excel is NaN (truthy). It used to make the blocked-row lookup miss the row, so a
row without a tag got a technical query but NO output row, and the independent verifier correctly failed Q-1 on an ordinary
partially valid file. Blank cells must be keyed by source row and exported as empty, never as 'nan'."""
from __future__ import annotations

from pathlib import Path

import openpyxl

from slotsmith.pipeline import run
from slotsmith.rules import default_ruleset
from slotsmith.verifier import verify

CSV = """Tag,IO Type,Cable,Pair,Grp,Seg
PT-101,AI,CBL-1,1,G1,A
PT-102,AI,CBL-1,2,G1,A
HS-201,DI,CBL-2,1,G1,B
ZZ-401,WEIRD-TYPE,CBL-3,2,G1,A
,AI,CBL-4,1,G1,A
LT-502,,CBL-5,1,G1,A
LT-503,AI,,2,G1,A
LT-504,AI,CBL-6,,G1,A
"""


def _run(tmp_path):
    p = tmp_path / "partial.csv"
    p.write_text(CSV)
    out = tmp_path / "out.xlsx"
    return run([p], default_ruleset(), out), out


def test_partially_valid_file_passes_verification_and_keeps_every_row(tmp_path):
    res, out = _run(tmp_path)
    assert [c for c in res.check if c["Result"] != "PASS"] == []                 # Q-1 no longer fails
    untagged = [r for r in res.rows if r["Source"].endswith(":csv:6")]            # the row without a tag
    assert len(untagged) == 1 and untagged[0]["Status"] == "TQ raised" and untagged[0]["TQ Ref"] and untagged[0]["Tag"] == ""
    assert any(q.rule_ref == "D-1" and "missing tag" in q.message for q in res.tqs)


def test_blank_cells_are_exported_empty_not_nan(tmp_path):
    res, out = _run(tmp_path)
    assert not any(str(v).lower() == "nan" for r in res.rows for v in r.values())
    ws = openpyxl.load_workbook(out, read_only=True)["IO Allocation"]
    cells = [str(c).lower() for row in ws.iter_rows(values_only=True) for c in row if c is not None]
    assert "nan" not in cells


def test_dropping_a_blocked_row_is_still_detected(tmp_path):
    res, out = _run(tmp_path)
    rows = [{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in res.rows if not r["Source"].endswith(":csv:6")]
    q1 = next(c for c in verify(rows, res.mdb.df, default_ruleset()) if c["Rule"] == "Q-1")
    assert q1["Result"] == "FAIL" and "row without tag" in q1["Examples"]       # the verifier is not weakened
