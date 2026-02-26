from __future__ import annotations

import re
from pathlib import Path

from .checks import (
    check_abstract_consistency,
    check_citations,
    check_figure_table_refs,
    check_numbering,
    check_percent_totals,
    check_structure,
    check_units,
)
from .config import load_config
from .docx_io import load_docx, save_docx
from .models import ConsistencyResult, ProcessingOptions, Report
from .reporting import make_changes_markdown, write_changes, write_report_files
from .rewrite import rewrite_paragraphs


def _reference_count(paragraphs: list[str]) -> int | None:
    start = None
    for i, p in enumerate(paragraphs):
        if "参考文献" in p:
            start = i
            break
    if start is None:
        return None
    count = 0
    for p in paragraphs[start + 1 :]:
        if re.match(r"^\[?\d+\]?", p.strip()):
            count += 1
    return count or None


def process_docx(input_path: str, outdir: str, options: ProcessingOptions, config_path: str | None = None) -> Report:
    cfg = load_config(config_path)
    parsed = load_docx(input_path)

    revised_paragraphs, changes = rewrite_paragraphs(parsed.paragraphs, aggressive=options.aggressive)

    for para, new_text in zip(parsed.document.paragraphs, revised_paragraphs):
        if para.text != new_text:
            para.text = new_text

    issues = []
    issues.extend(check_structure(revised_paragraphs, cfg["required_sections"]))
    issues.extend(check_numbering(revised_paragraphs))
    issues.extend(check_units(revised_paragraphs, parsed.tables, cfg["unit_whitelist"]))
    issues.extend(check_percent_totals(parsed.tables, cfg.get("percent_tolerance", 0.5)))
    issues.extend(check_figure_table_refs(revised_paragraphs))
    issues.extend(check_citations(revised_paragraphs, _reference_count(revised_paragraphs)))

    score, mismatches = check_abstract_consistency(revised_paragraphs)
    consistency = ConsistencyResult(score=score, mismatches=mismatches)

    Path(outdir).mkdir(parents=True, exist_ok=True)
    save_docx(parsed.document, str(Path(outdir) / "edited.docx"))

    changes_md, diff_html = make_changes_markdown(parsed.paragraphs, revised_paragraphs)
    write_changes(changes_md, outdir)
    Path(outdir, "diff.html").write_text(diff_html, encoding="utf-8")

    report = Report(
        style=options.style,
        input_file=input_path,
        issues=issues,
        changes=changes,
        consistency=consistency,
        stats={
            "paragraphs": len(revised_paragraphs),
            "tables": len(parsed.tables),
            "issues": len(issues),
            "changes": len(changes),
        },
    )
    write_report_files(report, outdir)
    return report
