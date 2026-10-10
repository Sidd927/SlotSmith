"""Reproducible SYNTHETIC IO MDB generator built from the PS #02 rulebook.

The organiser's sample MDB is not public (docs/known_limitations.md). These files are
synthetic and labelled as such. Passing on them proves nothing about the hidden test set;
they exercise the published rules at chosen scales.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import pandas as pd

IO_MIX = [("AI", 0.36), ("DI", 0.26), ("AO", 0.13), ("DO", 0.08), ("DO-SOV", 0.09),
          ("DO-HORN", 0.02), ("DO-RELAY", 0.03), ("AI-RTD", 0.03)]
PREFIX = {"AI": ["PT", "FT", "LT", "TT"], "AO": ["FV", "LV", "PV"], "DI": ["HS", "ZS", "LS", "PS"],
          "DO": ["XY", "HY"], "DO-SOV": ["XV"], "DO-HORN": ["HN"], "DO-RELAY": ["MY"], "AI-RTD": ["TE"]}
SIZE_MIX = [(24, 0.35), (12, 0.30), (6, 0.20), (2, 0.15)]
USED = {24: (19, 22), 12: (9, 11), 6: (4, 6), 2: (1, 2)}


@dataclass
class GenResult:
    df: pd.DataFrame
    injected: list[dict] = field(default_factory=list)   # ground truth of injected data errors


def _pick(rng, mix):
    x, acc = rng.random(), 0.0
    for v, w in mix:
        acc += w
        if x <= acc:
            return v
    return mix[-1][0]


def generate(n_signals: int, seed: int = 1, unit: str = "10", groups: int | None = None,
             ungrouped_frac: float = 0.15, ab_frac: float = 0.25, include_cable_size: bool = True,
             inject_errors: int = 0) -> GenResult:
    rng = random.Random(seed)
    n_groups = groups or max(1, n_signals // 450)
    rows: list[dict] = []
    loop = 1000
    cab_no = 0

    def new_cable():
        nonlocal cab_no
        cab_no += 1
        return f"CBL-{cab_no:04d}"

    def fill(cable, size, grp, seg, suffix, template=None):
        nonlocal loop
        lo, hi = USED[size]
        k = len(template) if template else rng.randint(lo, hi)
        out = []
        for p in range(1, k + 1):
            if template:
                io, base = template[p - 1]
            else:
                io = _pick(rng, IO_MIX)
                loop += 1
                base = f"{unit}-{rng.choice(PREFIX[io])}-{loop}"
            out.append((io, base))
            rows.append({"Tag": base + suffix, "IO": io, "Cable": cable, "Cable Size": size, "Pair": p,
                         "Grp": grp, "Seg": seg})
        return out

    while len(rows) < n_signals:
        size = _pick(rng, SIZE_MIX)
        if rng.random() < ungrouped_frac:
            fill(new_cable(), size, None, None, "")
            continue
        grp = f"G{rng.randint(1, n_groups)}"
        if rng.random() < ab_frac:
            tpl = fill(new_cable(), size, grp, "A", "A")      # duty
            fill(new_cable(), size, grp, "B", "B", tpl)       # standby twin on its own cable
        else:
            fill(new_cable(), size, grp, None, "")
    df = pd.DataFrame(rows)
    injected = _inject(df, rng, inject_errors) if inject_errors else []
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)   # MDBs are rarely sorted
    if not include_cable_size:
        df = df.drop(columns=["Cable Size"])
    return GenResult(df=df, injected=injected)


def _inject(df: pd.DataFrame, rng: random.Random, k: int) -> list[dict]:
    kinds = ["duplicate_tag", "missing_io", "unknown_io", "pair_over_size", "duplicate_pair",
             "mixed_ab_cable", "mixed_group_cable", "bad_seg", "missing_cable"]
    truth = []
    used_idx: set[int] = set()
    cables = df["Cable"].unique().tolist()
    for i in range(k):
        kind = kinds[i % len(kinds)]
        idx = rng.choice([j for j in range(len(df)) if j not in used_idx])
        used_idx.add(idx)
        tag, cable = df.at[idx, "Tag"], df.at[idx, "Cable"]
        if kind == "duplicate_tag":
            other = rng.choice([j for j in range(len(df)) if j not in used_idx and df.at[j, "Cable"] != cable])
            used_idx.add(other)
            df.at[other, "Tag"] = tag
        elif kind == "missing_io":
            df.at[idx, "IO"] = None
        elif kind == "unknown_io":
            df.at[idx, "IO"] = "PULSE-XYZ"
        elif kind == "pair_over_size":
            df.at[idx, "Pair"] = int(df.at[idx, "Cable Size"]) + 1
        elif kind == "duplicate_pair":
            same = [j for j in df.index[df["Cable"] == cable] if j != idx and j not in used_idx]
            if not same:
                continue
            j = same[0]
            used_idx.add(j)
            df.at[j, "Pair"] = df.at[idx, "Pair"]
        elif kind == "mixed_ab_cable":
            same = [j for j in df.index[df["Cable"] == cable] if j != idx and j not in used_idx]
            if not same:
                continue
            df.at[idx, "Seg"], df.at[same[0], "Seg"] = "A", "B"
            used_idx.add(same[0])
            df.loc[df["Cable"] == cable, "Grp"] = df.loc[df["Cable"] == cable, "Grp"].fillna("G1")
        elif kind == "mixed_group_cable":
            same = [j for j in df.index[df["Cable"] == cable] if j != idx and j not in used_idx]
            if not same:
                continue
            df.loc[df["Cable"] == cable, "Grp"] = "G1"
            df.at[same[0], "Grp"] = "G2"
            used_idx.add(same[0])
        elif kind == "bad_seg":
            df.at[idx, "Seg"] = "C"
        elif kind == "missing_cable":
            df.at[idx, "Cable"] = None
        truth.append({"kind": kind, "tag": tag, "cable": cable})
    return truth


def make_revision(rev_a: pd.DataFrame, seed: int = 2, delete_frac: float = 0.03, add_frac: float = 0.05,
                  modify_frac: float = 0.02, regroup_cables: int = 1) -> pd.DataFrame:
    """Rev B: delete, add (on spare pairs and on new cables), modify IO type, regroup a cable."""
    rng = random.Random(seed)
    df = rev_a.copy()
    n = len(df)
    # deletions
    drop = rng.sample(range(n), int(n * delete_frac))
    df = df.drop(index=drop).reset_index(drop=True)
    # IO-type modifications in place (CHARM swap, same slot)
    for i in rng.sample(range(len(df)), int(len(df) * modify_frac)):
        df.at[i, "IO"] = {"DI": "DO", "DO": "DI", "AI": "AI-RTD", "AI-RTD": "AI"}.get(df.at[i, "IO"], df.at[i, "IO"])
    # additions on spare pairs of existing cables
    adds = []
    n_add = int(n * add_frac)
    sizes = df.groupby("Cable")["Cable Size"].first()
    used = df.groupby("Cable")["Pair"].apply(lambda s: set(int(x) for x in s))
    spare_slots = [(c, p) for c in used.index for p in range(1, int(sizes[c]) + 1) if p not in used[c]]
    rng.shuffle(spare_slots)
    meta = df.groupby("Cable")[["Grp", "Seg"]].first()
    loop = 90000
    for c, p in spare_slots[: n_add // 2]:
        loop += 1
        io = _pick(rng, IO_MIX)
        g, s = meta.loc[c, "Grp"], meta.loc[c, "Seg"]
        adds.append({"Tag": f"10-{rng.choice(PREFIX[io])}-{loop}{s or ''}", "IO": io, "Cable": c,
                     "Cable Size": int(sizes[c]), "Pair": p, "Grp": g, "Seg": s})
    # additions on new cables (existing groups)
    groups = [g for g in df["Grp"].dropna().unique()]
    k = 0
    while len(adds) < n_add:
        k += 1
        size = _pick(rng, SIZE_MIX)
        c = f"CBL-R{k:03d}"
        g = rng.choice(groups) if groups else None
        for p in range(1, rng.randint(*USED[size]) + 1):
            loop += 1
            io = _pick(rng, IO_MIX)
            adds.append({"Tag": f"10-{rng.choice(PREFIX[io])}-{loop}", "IO": io, "Cable": c, "Cable Size": size,
                         "Pair": p, "Grp": g, "Seg": None})
    df = pd.concat([df, pd.DataFrame(adds)], ignore_index=True)
    # regroup whole cables (forces those signals to move)
    plain = df[df["Seg"].isna() & df["Grp"].notna()]["Cable"].unique().tolist()
    for c in rng.sample(plain, min(regroup_cables, len(plain))):
        cur = df.loc[df["Cable"] == c, "Grp"].iloc[0]
        others = [g for g in groups if g != cur]
        if others:
            df.loc[df["Cable"] == c, "Grp"] = rng.choice(others)
    return df
