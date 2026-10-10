"""Core tests: validation/TQs, every hard rule, corrupted allocations, revisions, export.

All data here is SYNTHETIC. Passing these tests does not demonstrate compatibility with the
organiser's hidden dataset.
"""
from __future__ import annotations

import copy
import math

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from slotsmith.allocator import allocate, ffd_pack
from slotsmith.generator import generate, make_revision
from slotsmith.ingest import auto_map, read_mdb
from slotsmith.model import CableBlock
from slotsmith.pipeline import run
from slotsmith.revision import impact_report, revise
from slotsmith.rules import RuleSet, default_ruleset
from slotsmith.verifier import load_allocation, total_violations, verify

R = default_ruleset()


def mdb(rows):
    df = pd.DataFrame(rows, columns=["Tag", "IO", "Cable", "Cable Size", "Pair", "Grp", "Seg"])
    df = df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                            "Pair": "pair", "Grp": "group", "Seg": "seg"})
    df["src_file"], df["src_sheet"], df["src_row"] = "t.xlsx", "S", range(2, len(df) + 2)
    return df.astype(object).where(df.notna(), None)


PS_EXAMPLE = [  # the six example rows from PS #02 p.4 (cable sizes assumed)
    ["10-PT-1001A", "AI", "CBL-101", 24, 1, "G1", "A"],
    ["10-PT-1001B", "AI", "CBL-102", 24, 1, "G1", "B"],
    ["10-XV-1005", "DO-SOV", "CBL-105", 6, 3, "G1", "A"],
    ["10-HS-1007", "DI", "CBL-107", 12, 2, None, None],
    ["10-HN-1009", "DO-Horn", "CBL-109", 2, 1, "G2", None],
    ["10-FV-1010", "AO", "CBL-110", 6, 4, "G2", None],
]


def run_df(df, rules=R):
    return run(None, rules, None, df=df)


# ---------------------------------------------------------------- ingestion

def test_auto_map_ps_headers():
    cm = auto_map(["Tag", "IO", "Cable", "Pair", "Grp", "Seg"])
    assert cm.mapping == {"tag": "Tag", "io_type": "IO", "cable": "Cable", "pair": "Pair", "group": "Grp", "seg": "Seg"}


def test_auto_map_variant_headers():
    cm = auto_map(["Instrument Tag", "Signal Type", "Cable No", "Pair No", "IO Grouping", "Segregation", "No of Pairs"])
    assert not cm.unmapped_required
    assert cm.mapping["cable_size"] == "No of Pairs"


def test_read_mdb_with_title_row(tmp_path):
    p = tmp_path / "m.xlsx"
    df = pd.DataFrame([["Customer IO list rev A", None, None, None], ["Tag", "IO", "Cable", "Pair"],
                       ["T1", "AI", "C1", 1]])
    df.to_excel(p, index=False, header=False)
    m = read_mdb([p])
    assert m.df.iloc[0]["tag"] == "T1" and m.df.iloc[0]["src_row"] == 3


# ---------------------------------------------------------------- PS example

def test_ps_example_rows_allocate_clean():
    res = run_df(mdb(PS_EXAMPLE))
    assert res.metrics["violations"] == 0
    assert res.metrics["signals_allocated"] == 6
    sig = {r["Tag"]: r for r in res.rows if r["Row Kind"] == "Signal"}
    assert sig["10-XV-1005"]["CHARM Type"] == "DO 24 V DC Isolated CHARM"
    assert sig["10-XV-1005"]["Terminal Block"] == "Fused-injected-power"
    assert sig["10-PT-1001A"]["CIOC"] != sig["10-PT-1001B"]["CIOC"]          # A/B never share a CIOC
    assert sig["10-PT-1001A"]["Marshalling Cabinet"] == "AR1-DCM-100-01"     # naming pattern
    assert sig["10-PT-1001A"]["CIOC"] == "AR1CIOC100001"
    assert sig["10-PT-1001A"]["Baseplate"] == "001-CBP-1"
    assert sig["10-PT-1001A"]["Controller"] == "AR1CTL10001"


def test_24_pair_cable_takes_two_full_baseplates():
    rows = [[f"T{i}", "AI", "C24", 24, i, None, None] for i in range(1, 23)]  # 22 signals + 2 spares
    res = run_df(mdb(rows))
    cab = [r for r in res.rows if r["Cable"] == "C24"]
    assert len(cab) == 24
    assert {r["Baseplate"] for r in cab} == {"001-CBP-1", "001-CBP-2"}
    assert sum(r["Row Kind"] == "Spare pair" for r in cab) == 2
    assert res.metrics["violations"] == 0


# ---------------------------------------------------------------- validation / TQs

@pytest.mark.parametrize("bad,rule", [
    (["X1", None, "C1", 12, 1, None, None], "D-1"),
    (["X1", "WEIRD", "C1", 12, 1, None, None], "H-*"),
    (["X1", "AI", "C1", 12, 13, None, None], "D-3"),
    (["X1", "AI", "C1", 12, 1, None, "Z"], "S-3"),
    (["X1", "AI", None, 12, 1, None, None], "D-1"),
])
def test_row_level_tqs(bad, rule):
    res = run_df(mdb([bad, ["OK1", "AI", "C9", 12, 1, None, None]]))
    assert any(q.rule_ref == rule for q in res.tqs)
    st_ = {r["Tag"]: r["Status"] for r in res.rows if r["Tag"]}
    assert st_["OK1"] == "Allocated"
    assert res.metrics["coverage_pct"] == 100.0 and res.metrics["violations"] == 0


def test_cable_with_a_and_b_is_blocked():
    res = run_df(mdb([["A1", "AI", "C1", 6, 1, "G1", "A"], ["B1", "AI", "C1", 6, 2, "G1", "B"]]))
    assert any(q.rule_ref == "S-2" for q in res.tqs)
    assert res.metrics["signals_allocated"] == 0 and res.metrics["violations"] == 0


def test_duplicate_tag_and_pair():
    res = run_df(mdb([["T1", "AI", "C1", 6, 1, None, None], ["T1", "AI", "C2", 6, 1, None, None],
                      ["T2", "AI", "C3", 6, 1, None, None], ["T3", "DI", "C3", 6, 1, None, None]]))
    refs = {q.rule_ref for q in res.tqs}
    assert {"D-4", "D-5"} <= refs and res.metrics["violations"] == 0


def test_injected_errors_all_detected():
    g = generate(3000, seed=4, inject_errors=18)
    df = g.df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                              "Pair": "pair", "Grp": "group", "Seg": "seg"})
    df["src_file"], df["src_sheet"], df["src_row"] = "g", "S", range(2, len(df) + 2)
    df = df.astype(object).where(df.notna(), None)
    for c in ["pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None else str(int(float(v))))
    res = run_df(df)
    for inj in g.injected:
        assert any(inj["tag"] in q.tags or inj["cable"] in q.cables for q in res.tqs), inj
    assert res.metrics["violations"] == 0


# ---------------------------------------------------------------- verifier catches corruption

@pytest.fixture(scope="module")
def clean_alloc(tmp_path_factory):
    p = tmp_path_factory.mktemp("a")
    g = generate(2000, seed=9)
    g.df.to_excel(p / "m.xlsx", index=False)
    res = run([p / "m.xlsx"], R, p / "out.xlsx")
    assert res.metrics["violations"] == 0
    return load_allocation(p / "out.xlsx"), res.mdb.df


def _fails(rows, df):
    return {c["Rule"] for c in verify(rows, df, R) if c["Result"] == "FAIL"}


def test_verifier_passes_clean(clean_alloc):
    rows, df = clean_alloc
    assert not _fails(rows, df)


def test_verifier_catches_double_booked_slot(clean_alloc):
    rows, df = copy.deepcopy(clean_alloc[0]), clean_alloc[1]
    s = [r for r in rows if r["Row Kind"] == "Signal"]
    for k in ["Marshalling Cabinet", "CIOC", "Baseplate", "Slot", "CHARM Address"]:
        s[1][k] = s[0][k]
    assert "D-2" in _fails(rows, df)


def test_verifier_catches_wrong_terminal_block(clean_alloc):
    rows, df = copy.deepcopy(clean_alloc[0]), clean_alloc[1]
    r = next(r for r in rows if r["Terminal Block"] == "Fused-injected-power")
    r["Terminal Block"] = "Standard"
    assert "H-1..6" in _fails(rows, df)


def test_verifier_catches_ab_mix_and_missing_signal(clean_alloc):
    rows, df = copy.deepcopy(clean_alloc[0]), clean_alloc[1]
    a = next(r for r in rows if r["Segregation"] == "A")
    b = next(r for r in rows if r["Segregation"] == "B")
    b["CIOC"] = a["CIOC"]
    b["Baseplate"] = a["Baseplate"]
    assert "S-1" in _fails(rows, df)
    rows2 = [r for r in clean_alloc[0] if r["Tag"] != a["Tag"]]
    assert "Q-1" in _fails(rows2, df)


def test_verifier_catches_spare_budget_and_cable_split(clean_alloc):
    rows, df = copy.deepcopy(clean_alloc[0]), clean_alloc[1]
    strict = default_ruleset()
    strict.spare_percent = 60.0
    assert "P-1" in {c["Rule"] for c in verify(rows, df, strict) if c["Result"] == "FAIL"}
    r = next(r for r in rows if r["Row Kind"] == "Signal" and r["Pair"] == "2")
    r["Slot"] = str(int(r["Slot"]) + 5) if int(r["Slot"]) <= 7 else str(int(r["Slot"]) - 5)
    assert "K-1" in _fails(rows, df)


# ---------------------------------------------------------------- packing optimality

@settings(max_examples=200, deadline=None)
@given(st.lists(st.sampled_from([2, 6, 12]), min_size=1, max_size=60))
def test_ffd_divisible_sizes_is_optimal(sizes):
    blocks = [CableBlock(cable=f"C{i}", size=s, group=None, seg=None) for i, s in enumerate(sizes)]
    bins = ffd_pack(blocks, 12)
    assert len(bins) == math.ceil(sum(sizes) / 12)  # = trivial lower bound -> optimal


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.integers(min_value=50, max_value=1500), st.integers(min_value=0, max_value=10_000))
def test_property_random_mdbs_zero_violations(n, seed):
    g = generate(n, seed=seed)
    df = g.df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                              "Pair": "pair", "Grp": "group", "Seg": "seg"})
    df["src_file"], df["src_sheet"], df["src_row"] = "g", "S", range(2, len(df) + 2)
    df = df.astype(object).where(df.notna(), None)
    for c in ["pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None else str(int(float(v))))
    res = run_df(df)
    assert res.metrics["violations"] == 0
    assert res.metrics["coverage_pct"] == 100.0


# ---------------------------------------------------------------- rules are data

def test_rule_change_without_code_change(tmp_path):
    rs = default_ruleset()
    rs.spare_percent = 25.0          # 8 of 32 baseplates kept empty
    rs.naming.area = "ZZ9"
    p = tmp_path / "rules.json"
    rs.save(p)
    loaded = RuleSet.load(p)
    res = run_df(mdb(PS_EXAMPLE), loaded)
    assert res.metrics["violations"] == 0
    assert all(r["Marshalling Cabinet"].startswith("ZZ9-DCM") for r in res.rows if r["Slot"])
    assert loaded.reserved_baseplates_per_cabinet == 8


def test_segregation_toggle_off_is_caught_by_strict_verifier():
    loose = default_ruleset()
    for t in loose.toggles:
        if t.id == "R2-segregation":
            t.enabled = False
    rows = [[f"A{i}", "AI", f"CA{i}", 2, 1, "G1", "A"] for i in range(3)] + \
           [[f"B{i}", "AI", f"CB{i}", 2, 1, "G1", "B"] for i in range(3)]
    res = run_df(mdb(rows), loose)
    strict = verify([{k: (None if v in ("", None) else str(v)) for k, v in r.items()} for r in res.rows],
                    res.mdb.df, R)
    assert any(c["Rule"] == "S-1" and c["Result"] == "FAIL" for c in strict)


# ---------------------------------------------------------------- revisions

def test_revision_keeps_unchanged_signals_in_place():
    g = generate(3000, seed=31)
    df_a = _canon(g.df)
    a = run_df(df_a)
    b_raw = make_revision(g.df, seed=8)
    rr = revise(a.rows, _canon(b_raw), R)
    assert rr.metrics["violations"] == 0
    assert not rr.metrics["fallback_full_reallocation"]
    scratch = run_df(_canon(b_raw))
    _, m = impact_report(a.rows, scratch.rows)
    assert rr.metrics["moved"] < m["moved"] / 2   # far fewer moves than a from-scratch re-run


def test_signal_added_on_spare_pair_lands_without_moves():
    base = [[f"T{i}", "AI", "C1", 12, i, None, None] for i in range(1, 11)]
    a = run_df(mdb(base))
    b = mdb(base + [["NEW", "DI", "C1", 12, 11, None, None]])
    rr = revise(a.rows, b, R)
    assert rr.metrics["moved"] == 0 and rr.metrics["added"] == 1 and rr.metrics["violations"] == 0
    new = next(r for r in rr.rows if r["Tag"] == "NEW")
    old_spare = next(r for r in a.rows if r["Cable"] == "C1" and r["Pair"] == 11)
    assert (new["Baseplate"], new["Slot"]) == (old_spare["Baseplate"], old_spare["Slot"])


def _canon(df):
    df = df.rename(columns={"Tag": "tag", "IO": "io_type", "Cable": "cable", "Cable Size": "cable_size",
                            "Pair": "pair", "Grp": "group", "Seg": "seg"}).copy()
    df["src_file"], df["src_sheet"], df["src_row"] = "g", "S", range(2, len(df) + 2)
    df = df.astype(object).where(df.notna(), None)
    for c in ["pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None else str(int(float(v))))
    return df


# ---------------------------------------------------------------- export round-trip

def test_workbook_has_required_sheets(tmp_path):
    g = generate(300, seed=2)
    g.df.to_excel(tmp_path / "m.xlsx", index=False)
    run([tmp_path / "m.xlsx"], R, tmp_path / "o.xlsx")
    xl = pd.ExcelFile(tmp_path / "o.xlsx")
    assert {"IO Allocation", "Cabinet Summary", "TQ List", "Rule Check", "Rule Set"} <= set(xl.sheet_names)
    chk = pd.read_excel(tmp_path / "o.xlsx", sheet_name="Rule Check")
    assert (chk["Result"] == "PASS").all()
