"""Read customer IO MDB workbooks, auto-map columns and keep row provenance.

Mapping is deterministic (synonym table + fuzzy match). An LLM may later be used to
*suggest* a mapping for headers this table cannot resolve, but the user always confirms
it, and the confirmed mapping is stored as data (rule register D-1).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

CANONICAL = ["tag", "io_type", "cable", "pair", "group", "seg", "cable_size"]
REQUIRED = ["tag", "io_type", "cable", "pair"]

SYNONYMS: dict[str, list[str]] = {
    "tag": ["tag", "tag no", "tag number", "tagname", "instrument tag", "signal tag", "dst", "loop tag", "device tag"],
    "io_type": ["io", "io type", "i/o", "i/o type", "signal type", "type", "io_type", "channel type"],
    "cable": ["cable", "cable no", "cable number", "cable tag", "multicore", "multi core", "cable id", "mc cable"],
    "pair": ["pair", "pair no", "pair number", "core", "core no", "pair#"],
    "group": ["grp", "group", "io grouping", "io group", "logical group", "grouping"],
    "seg": ["seg", "segregation", "a/b", "redundancy", "duty/standby", "side"],
    "cable_size": ["cable size", "pairs", "no of pairs", "cable pairs", "size", "cable type", "cores"],
}


def _norm(h: str) -> str:
    return re.sub(r"[^a-z0-9/#]+", " ", str(h).lower()).strip()


@dataclass
class ColumnMapping:
    mapping: dict[str, str]                  # canonical -> source header
    confidence: dict[str, float]
    unmapped_required: list[str] = field(default_factory=list)
    unused_headers: list[str] = field(default_factory=list)


def auto_map(headers: list[str]) -> ColumnMapping:
    normed = {h: _norm(h) for h in headers}
    mapping: dict[str, str] = {}
    conf: dict[str, float] = {}
    used: set[str] = set()
    for canon in CANONICAL:
        best, best_s = None, 0.0
        for h, n in normed.items():
            if h in used:
                continue
            for syn in SYNONYMS[canon]:
                s = 1.0 if n == syn else difflib.SequenceMatcher(None, n, syn).ratio()
                if s > best_s:
                    best, best_s = h, s
        if best is not None and best_s >= 0.8:
            mapping[canon] = best
            conf[canon] = round(best_s, 2)
            used.add(best)
    missing = [c for c in REQUIRED if c not in mapping]
    return ColumnMapping(mapping, conf, missing, [h for h in headers if h not in used])


@dataclass
class MDB:
    df: pd.DataFrame               # canonical columns + 'src_file', 'src_sheet', 'src_row'
    mapping: dict[str, ColumnMapping]


def _find_header_row(raw: pd.DataFrame, max_scan: int = 15) -> int:
    """Pick the first row that maps all required columns (tolerates title rows)."""
    for i in range(min(max_scan, len(raw))):
        cm = auto_map([str(x) for x in raw.iloc[i].tolist()])
        if not cm.unmapped_required:
            return i
    return 0


def read_mdb(paths: list[str | Path], mapping_override: dict[str, str] | None = None) -> MDB:
    frames, maps = [], {}
    for p in paths:
        p = Path(p)
        sheets = {"csv": pd.read_csv(p, header=None, dtype=str)} if p.suffix.lower() == ".csv" else \
            pd.read_excel(p, sheet_name=None, header=None, dtype=str)
        for sheet, raw in sheets.items():
            raw = raw.dropna(how="all")
            if raw.empty:
                continue
            hdr = _find_header_row(raw)
            headers = [str(x) for x in raw.iloc[hdr].tolist()]
            cm = auto_map(headers)
            if mapping_override:
                cm.mapping.update(mapping_override)
                cm.unmapped_required = [c for c in REQUIRED if c not in cm.mapping]
            if cm.unmapped_required:
                continue  # not an IO list sheet
            body = raw.iloc[hdr + 1:].copy()
            body.columns = headers
            out = pd.DataFrame({c: body[cm.mapping[c]] if c in cm.mapping else None for c in CANONICAL})
            out["src_file"] = p.name
            out["src_sheet"] = sheet
            out["src_row"] = [int(i) + 1 for i in body.index]  # 1-based Excel row number
            frames.append(out)
            maps[f"{p.name}:{sheet}"] = cm
    if not frames:
        raise ValueError("No sheet with the required columns (tag, IO type, cable, pair) was found")
    df = pd.concat(frames, ignore_index=True)
    for c in ["tag", "io_type", "cable", "group", "seg", "pair", "cable_size"]:
        df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "-", "–", "nan", "None") else str(v).strip())
    return MDB(df=df, mapping=maps)
