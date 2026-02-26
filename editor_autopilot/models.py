from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    SUGGESTION = "SUGGESTION"


@dataclass
class Location:
    paragraph_index: int | None = None
    table_index: int | None = None
    cell: str | None = None
    section: str | None = None


@dataclass
class Issue:
    category: str
    severity: Severity
    message: str
    location: Location = field(default_factory=Location)
    suggestion: str | None = None
    auto_fixed: bool = False


@dataclass
class ChangeItem:
    location: str
    original: str
    revised: str
    reason: str


@dataclass
class ConsistencyResult:
    score: float
    mismatches: list[str]


@dataclass
class Report:
    style: str
    input_file: str
    issues: list[Issue]
    changes: list[ChangeItem]
    consistency: ConsistencyResult
    stats: dict[str, Any]

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessingOptions:
    style: str = "nursing_cn"
    aggressive: bool = False
    track_changes: bool = False
    citation_style: Literal["bracket", "paren", "superscript"] = "bracket"
