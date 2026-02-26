from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from difflib import SequenceMatcher

from .models import Issue, Location, Severity


UNIT_RE = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>mmHg|mg/L|mmol/L|kg|cm|min|h|%|℃|次/min)")
CITATION_RE = re.compile(r"\[(\d+)\]")
TABLE_REF_RE = re.compile(r"表\s*(\d+)")
FIG_REF_RE = re.compile(r"图\s*(\d+)")


def check_structure(paragraphs: list[str], required_sections: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    joined = "\n".join(paragraphs)
    for section in required_sections:
        if section not in joined:
            issues.append(
                Issue(
                    category="structure",
                    severity=Severity.MAJOR,
                    message=f"缺少结构要素：{section}",
                    suggestion=f"补充“{section}”部分",
                )
            )
    return issues


def check_numbering(paragraphs: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    title_nums = []
    for i, p in enumerate(paragraphs):
        m = re.match(r"^(\d+(?:\.\d+)*)\s+", p)
        if m:
            title_nums.append((i, m.group(1)))
    roots = [int(x[1].split(".")[0]) for x in title_nums if "." not in x[1]]
    for idx in range(1, len(roots)):
        if roots[idx] != roots[idx - 1] + 1:
            issues.append(
                Issue(
                    category="numbering",
                    severity=Severity.MAJOR,
                    message=f"标题编号不连续：{roots[idx-1]} -> {roots[idx]}",
                    location=Location(paragraph_index=title_nums[idx][0]),
                )
            )
    return issues


def check_units(paragraphs: list[str], tables: list[list[list[str]]], unit_whitelist: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    var_unit_map: dict[str, set[str]] = {}
    for i, p in enumerate(paragraphs):
        for m in UNIT_RE.finditer(p):
            unit = m.group("unit")
            if unit not in unit_whitelist:
                issues.append(
                    Issue(
                        category="unit",
                        severity=Severity.MINOR,
                        message=f"发现非白名单单位：{unit}",
                        location=Location(paragraph_index=i),
                    )
                )
        vm = re.findall(r"([\u4e00-\u9fa5A-Za-z]+)\s*[：:]?\s*\d+(?:\.\d+)?\s*(mmHg|mg/L|mmol/L|kg|cm|min|h|%)", p)
        for var, unit in vm:
            var_unit_map.setdefault(var, set()).add(unit)
    for var, units in var_unit_map.items():
        if len(units) > 1:
            issues.append(
                Issue(
                    category="unit",
                    severity=Severity.MAJOR,
                    message=f"变量“{var}”出现多个单位：{', '.join(sorted(units))}",
                    suggestion="统一同一指标单位",
                )
            )

    for ti, table in enumerate(tables):
        if not table:
            continue
        header = table[0]
        header_units = [re.findall(r"\(([^)]+)\)", h) for h in header]
        for ri, row in enumerate(table[1:], start=1):
            for ci, cell in enumerate(row):
                found = UNIT_RE.search(cell)
                if found and header_units[ci]:
                    hu = header_units[ci][0]
                    if found.group("unit") != hu:
                        issues.append(
                            Issue(
                                category="unit",
                                severity=Severity.MAJOR,
                                message=f"表头单位与单元格单位不一致：{hu} vs {found.group('unit')}",
                                location=Location(table_index=ti, cell=f"R{ri}C{ci}"),
                            )
                        )
    return issues


def check_percent_totals(tables: list[list[list[str]]], tolerance: float) -> list[Issue]:
    issues: list[Issue] = []
    for ti, table in enumerate(tables):
        for ci in range(len(table[0]) if table else 0):
            vals = []
            for row in table[1:]:
                if ci < len(row):
                    m = re.search(r"(\d+(?:\.\d+)?)%", row[ci])
                    if m:
                        vals.append(float(m.group(1)))
            if len(vals) >= 2:
                s = sum(vals)
                if math.fabs(s - 100.0) > tolerance:
                    issues.append(
                        Issue(
                            category="numeric",
                            severity=Severity.MAJOR,
                            message=f"表{ti+1}第{ci+1}列百分比合计为{s:.2f}%",
                            suggestion="检查分组占比与四舍五入误差",
                            location=Location(table_index=ti),
                        )
                    )
    return issues


def check_citations(paragraphs: list[str], reference_count: int | None = None) -> list[Issue]:
    issues: list[Issue] = []
    seen: list[int] = []
    for i, p in enumerate(paragraphs):
        for m in CITATION_RE.findall(p):
            n = int(m)
            seen.append(n)
            if len(seen) >= 2 and n > max(seen[:-1]) + 1:
                issues.append(
                    Issue(
                        category="citation",
                        severity=Severity.MAJOR,
                        message=f"引用跳号：[{max(seen[:-1])}] 后直接到 [{n}]",
                        location=Location(paragraph_index=i),
                    )
                )
    if seen:
        c = Counter(seen)
        for n, count in c.items():
            if count > 1:
                issues.append(
                    Issue(
                        category="citation",
                        severity=Severity.MINOR,
                        message=f"引用 [{n}] 出现 {count} 次",
                    )
                )
        if reference_count is not None and max(seen) != reference_count:
            issues.append(
                Issue(
                    category="citation",
                    severity=Severity.MAJOR,
                    message=f"正文最大引用序号 {max(seen)} 与文末参考文献条目数 {reference_count} 不一致",
                )
            )
    return issues


def check_figure_table_refs(paragraphs: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    table_titles = set()
    fig_titles = set()
    refs_table = set()
    refs_fig = set()
    for i, p in enumerate(paragraphs):
        if re.match(r"^表\s*\d+", p):
            table_titles.add(int(re.findall(r"\d+", p)[0]))
        if re.match(r"^图\s*\d+", p):
            fig_titles.add(int(re.findall(r"\d+", p)[0]))
        refs_table.update(int(x) for x in TABLE_REF_RE.findall(p))
        refs_fig.update(int(x) for x in FIG_REF_RE.findall(p))
    for n in sorted(table_titles - refs_table):
        issues.append(Issue(category="figure_table", severity=Severity.MINOR, message=f"表{n}未在正文引用"))
    for n in sorted(fig_titles - refs_fig):
        issues.append(Issue(category="figure_table", severity=Severity.MINOR, message=f"图{n}未在正文引用"))
    return issues


def check_abstract_consistency(paragraphs: list[str]) -> tuple[float, list[str]]:
    text = "\n".join(paragraphs)
    abstract = next((p for p in paragraphs if p.startswith("摘要")), "")
    body = text.replace(abstract, "")
    mismatches: list[str] = []

    abs_ns = re.findall(r"n\s*=\s*(\d+)", abstract, flags=re.I)
    for n in abs_ns:
        if not re.search(rf"n\s*=\s*{re.escape(n)}", body, flags=re.I):
            mismatches.append(f"摘要样本量 n={n} 在正文未匹配")

    for key in ["目的", "方法", "结果", "结论"]:
        if key in abstract and key not in body:
            mismatches.append(f"摘要含“{key}”但正文未见对应关键词")

    abs_numbers = re.findall(r"\d+(?:\.\d+)?", abstract)
    missed = 0
    for num in abs_numbers:
        if num and num not in body:
            missed += 1
    score = max(0.0, 1.0 - (len(mismatches) + missed * 0.1) / 10)

    if abstract and body:
        sim = SequenceMatcher(None, abstract[:200], body[:500]).ratio()
        score = (score + sim) / 2

    return round(score, 3), mismatches
