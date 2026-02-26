from __future__ import annotations

import argparse

from editor_autopilot.models import ProcessingOptions
from editor_autopilot.pipeline import process_docx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Journal Editor Autopilot")
    parser.add_argument("--input", required=True, help="input .docx path")
    parser.add_argument("--outdir", required=True, help="output directory")
    parser.add_argument("--style", default="nursing_cn", help="style name")
    parser.add_argument("--track-changes", default="false", choices=["true", "false"])
    parser.add_argument("--aggressive", action="store_true")
    parser.add_argument("--config", default=None, help="rule config path")
    parser.add_argument("--citation-style", default="bracket", choices=["bracket", "paren", "superscript"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    options = ProcessingOptions(
        style=args.style,
        aggressive=args.aggressive,
        track_changes=(args.track_changes == "true"),
        citation_style=args.citation_style,
    )
    report = process_docx(args.input, args.outdir, options, config_path=args.config)
    print(f"Done. issues={len(report.issues)} changes={len(report.changes)}")


if __name__ == "__main__":
    main()
