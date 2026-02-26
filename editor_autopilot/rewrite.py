from __future__ import annotations

import re

from .models import ChangeItem


PUNCT_MAP = {
    ",": "，",
    ";": "；",
    ":": "：",
    "(": "（",
    ")": "）",
}


SAFE_PATTERNS = [
    (re.compile(r"\s+"), " "),
    (re.compile(r"，，+"), "，"),
    (re.compile(r"。。+"), "。"),
    (re.compile(r"(\d)\s*(mmHg|mg/L|mmol/L|kg|cm|min|h|%)"), r"\1 \2"),
    (re.compile(r"\bBmi\b"), "BMI"),
    (re.compile(r"\bSbp\b"), "SBP"),
]


def normalize_sentence(text: str, aggressive: bool = False) -> str:
    revised = text
    for src, tgt in PUNCT_MAP.items():
        revised = revised.replace(src, tgt)
    for pattern, rep in SAFE_PATTERNS:
        revised = pattern.sub(rep, revised)
    revised = revised.strip()
    if aggressive:
        revised = re.sub(r"\b非常\b", "较", revised)
        revised = re.sub(r"\b然后\b", "随后", revised)
    return revised


def rewrite_paragraphs(paragraphs: list[str], aggressive: bool = False) -> tuple[list[str], list[ChangeItem]]:
    out: list[str] = []
    changes: list[ChangeItem] = []
    for i, p in enumerate(paragraphs):
        new = normalize_sentence(p, aggressive=aggressive)
        out.append(new)
        if new != p:
            changes.append(
                ChangeItem(
                    location=f"paragraph:{i}",
                    original=p,
                    revised=new,
                    reason="标点/空格/缩写规范化与轻量语句润色",
                )
            )
    return out, changes
