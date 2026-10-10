"""Core data structures shared by validation, allocation, export and revision."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Signal:
    tag: str
    io_type: str            # normalised key, e.g. "AI", "DO-SOV"
    io_type_raw: str
    cable: str
    pair: int
    group: Optional[str]
    seg: Optional[str]
    src: str                # "file:sheet:row"


@dataclass
class CableBlock:
    """A whole multi-pair cable: the unit of placement (rule K-1)."""

    cable: str
    size: int                         # number of pairs = number of slots occupied
    group: Optional[str]
    seg: Optional[str]
    signals: dict[int, Signal] = field(default_factory=dict)  # pair -> signal

    @property
    def n_baseplates(self) -> int:
        """Baseplates spanned when the cable is larger than one baseplate (24-pair = 2)."""
        return 1

    @property
    def spare_pairs(self) -> list[int]:
        return [p for p in range(1, self.size + 1) if p not in self.signals]


@dataclass
class TQ:
    id: str
    severity: str              # "blocking" | "warning" | "info"
    category: str              # "data" | "rule-conflict" | "capacity" | "hardware"
    rule_ref: str              # rule register ID, e.g. "S-2"
    message: str
    tags: list[str] = field(default_factory=list)
    cables: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    suggested_action: str = ""


@dataclass(frozen=True)
class SlotAddr:
    cabinet: int     # 1-based marshalling cabinet sequence
    cioc: int        # 1-based CIOC position inside the cabinet (1..4)
    baseplate: int   # 1..8
    slot: int        # 1..12


@dataclass
class Placement:
    cable: str
    cabinet: int
    cioc: int
    baseplate: int       # first baseplate
    start_slot: int      # first slot (pair 1 lands here)
