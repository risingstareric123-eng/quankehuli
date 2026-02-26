from __future__ import annotations

import difflib
import json
from pathlib import Path

from .models import Report


def _render_report_md(report: Report) -> str:
    lines = [
        "# 编辑部校对报告",
        "",
        f"- 样式: {report.style}",
        f"- 输入文件: {report.input_file}",
        f"- 一致性评分: {report.consistency.score}",
        "",
        "## 摘要一致性不匹配",
    ]
    if report.consistency.mismatches:
        lines.extend([f"- {m}" for m in report.consistency.mismatches])
    else:
        lines.append("- 无")

    lines += ["", "## 问题清单"]
    if report.issues:
        for issue in report.issues:
            lines += [
                f"- [{issue.severity}] **{issue.category}**: {issue.message}",
                f"  - 定位: {issue.location.__dict__}",
                f"  - 建议: {issue.suggestion or '—'}",
                f"  - 自动修复: {issue.auto_fixed}",
            ]
    else:
        lines.append("- 无")

    lines += ["", "## 变更清单"]
    if report.changes:
        for c in report.changes:
            lines += [
                f"- {c.location}",
                f"  - 原文: {c.original}",
                f"  - 修改: {c.revised}",
                f"  - 原因: {c.reason}",
            ]
    else:
        lines.append("- 无")
    return "\n".join(lines)


def write_report_files(report: Report, outdir: str) -> None:
    o = Path(outdir)
    o.mkdir(parents=True, exist_ok=True)
    (o / "report.json").write_text(
        json.dumps(report.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (o / "report.md").write_text(_render_report_md(report), encoding="utf-8")


def write_changes(changes_md: str, outdir: str) -> None:
    Path(outdir, "changes.md").write_text(changes_md, encoding="utf-8")


def make_changes_markdown(original: list[str], revised: list[str]) -> tuple[str, str]:
    lines = ["# 修改对照", ""]
    for i, (o, r) in enumerate(zip(original, revised)):
        if o != r:
            lines += [f"## 段落 {i}", f"- 原句：{o}", f"- 新句：{r}", ""]
    md = "\n".join(lines)

    html = difflib.HtmlDiff(wrapcolumn=80).make_file(
        original, revised, fromdesc="original", todesc="edited", context=True, numlines=1
    )
    return md, html
