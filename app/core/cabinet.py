"""Cabinet model: turns exported allocation rows into a CIOC x baseplate x slot structure.

Pure data transformation over `RunResult.rows` (no backend logic is duplicated: positions, hardware and names
come straight from the rows the engine produced).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

TYPE_CODES = {
    "AI": "AI", "AO": "AO", "DI": "DI", "DO": "DO", "DF": "DF", "RL": "RL",
}
TYPE_WORDS = {
    "AI": "Analog input", "AO": "Analog output", "DI": "Digital input", "DO": "Digital output",
    "DF": "DO, isolated + fused terminal block", "RL": "DO, relay terminal block",
}
BP_PER_CIOC = 8
SLOTS_PER_BP = 12


def type_code(row: dict) -> str:
    tb = row.get("Terminal Block") or ""
    if tb == "Fused-injected-power":
        return "DF"
    if tb == "Relay output":
        return "RL"
    io = (row.get("IO Type") or "").upper()
    for p in ("AO", "DI", "DO"):
        if io.startswith(p):
            return p
    return "AI"


@dataclass(frozen=True)
class Slot:
    cioc: str
    bp: int
    slot: int
    kind: str                 # "signal" | "spare" | "held" | "free"
    code: str = ""
    tag: str = ""
    io_type: str = ""
    cable: str = ""
    pair: str = ""
    group: str = ""
    seg: str = ""
    charm: str = ""
    terminal_block: str = ""
    address: str = ""
    baseplate_name: str = ""
    controller: str = ""
    status: str = ""
    tq_ref: str = ""
    source: str = ""

    @property
    def key(self) -> str:
        return f"{self.cioc}|{self.bp}|{self.slot}"

    @property
    def label(self) -> str:
        if self.kind == "signal":
            return f"{self.tag}, {self.code}, cable {self.cable} pair {self.pair}"
        if self.kind == "spare":
            return f"Wired spare pair, cable {self.cable} pair {self.pair}"
        if self.kind == "held":
            return f"Held for a technical query, cable {self.cable} pair {self.pair}"
        return "Free slot"


@dataclass
class CiocModel:
    name: str
    group: str
    seg: str
    controller: str
    slots: dict[tuple[int, int], Slot] = field(default_factory=dict)

    def slot(self, bp: int, n: int) -> Slot:
        return self.slots.get((bp, n)) or Slot(self.name, bp, n, "free")

    @property
    def used_baseplates(self) -> int:
        return len({bp for (bp, _) in self.slots})


@dataclass
class CabinetModel:
    name: str
    ciocs: list[CiocModel]

    def all_slots(self) -> Iterable[Slot]:
        for c in self.ciocs:
            yield from c.slots.values()


def cabinet_names(rows: list[dict]) -> list[str]:
    seen: dict[str, int] = {}
    for r in rows:
        n, c = r.get("Marshalling Cabinet"), r.get("_cab")
        if n and c is not None:
            seen[n] = c
    return [n for n, _ in sorted(seen.items(), key=lambda kv: kv[1])]


def _s(v: Any) -> str:
    return "" if v is None else str(v)


def build_cabinet(rows: list[dict], cabinet: str) -> CabinetModel:
    by_cioc: dict[str, CiocModel] = {}
    order: dict[str, int] = {}
    for r in rows:
        if r.get("Marshalling Cabinet") != cabinet or not r.get("Slot"):
            continue
        cioc = _s(r["CIOC"])
        order.setdefault(cioc, int(r.get("_cioc") or 0))
        m = by_cioc.setdefault(cioc, CiocModel(cioc, "", "", _s(r.get("Controller"))))
        if r.get("IO Group") and not m.group:
            m.group = _s(r["IO Group"])
        if r.get("Segregation") and not m.seg:
            m.seg = _s(r["Segregation"])
        bp = int(r["_bp"])
        n = int(float(r["Slot"]))
        kind_raw = r.get("Row Kind", "")
        if kind_raw == "Signal":
            kind = "signal"
        elif kind_raw == "Spare pair":
            kind = "spare"
        else:
            kind = "held"
        m.slots[(bp, n)] = Slot(
            cioc=cioc, bp=bp, slot=n, kind=kind,
            code=type_code(r) if kind == "signal" else "",
            tag=_s(r.get("Tag")), io_type=_s(r.get("IO Type")), cable=_s(r.get("Cable")),
            pair=_s(r.get("Pair")), group=_s(r.get("IO Group")), seg=_s(r.get("Segregation")),
            charm=_s(r.get("CHARM Type")), terminal_block=_s(r.get("Terminal Block")),
            address=_s(r.get("CHARM Address")), baseplate_name=_s(r.get("Baseplate")),
            controller=_s(r.get("Controller")), status=_s(r.get("Status")), tq_ref=_s(r.get("TQ Ref")),
            source=_s(r.get("Source")),
        )
    return CabinetModel(cabinet, [by_cioc[c] for c in sorted(by_cioc, key=lambda x: order[x])])


def find_slots(model: CabinetModel, query: str = "", codes: Iterable[str] = ()) -> list[Slot]:
    """Occupied/spare/held slots matching a text query (tag, cable, address, charm) and optional type codes."""
    q = (query or "").strip().lower()
    codes = set(codes or ())
    out = []
    for s in model.all_slots():
        if codes and s.code not in codes:
            continue
        if q and not any(q in v.lower() for v in (s.tag, s.cable, s.address, s.charm, s.io_type, s.group)):
            continue
        out.append(s)
    return sorted(out, key=lambda s: (s.cioc, s.bp, s.slot))
