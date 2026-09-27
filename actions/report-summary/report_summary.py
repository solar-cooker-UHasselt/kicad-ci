"""Write a Markdown job summary of KiCad's ERC and DRC reports.

Usage: python3 report_summary.py [reports dir] >> "$GITHUB_STEP_SUMMARY"

Reads <board>-erc.json and <board>-drc.json, as KiBot and kicad-cli write
them (https://schemas.kicad.org/erc.v1.json and drc.v1.json). A missing
report shows as "not run". When REPORTS_URL or OUTPUTS_URL is set, the
summary links to those artifacts.
"""

import argparse
import html
import json
import os
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# A violation as KiCad writes it: severity, type, description, items
Violation = Mapping[str, Any]

MAX_ERRORS = 25  # errors listed one by one, the rest are only counted
MARKDOWN_SPECIAL = "\\`*_[]~"

# The DRC report's rows in the table: (row name, key in the report)
DRC_CHECKS = (
    ("DRC", "violations"),
    ("Unconnected", "unconnected_items"),
    ("Schematic parity", "schematic_parity"),
)


@dataclass(frozen=True)
class Report:
    """A loaded <board>-<kind>.json."""

    board: str
    data: Mapping[str, Any]


@dataclass(frozen=True)
class Check:
    """A row of the table. violations is None when its report is missing."""

    name: str
    violations: Sequence[Violation] | None


def load_report(folder: Path, kind: str) -> Report | None:
    """Return the first <board>-<kind>.json in folder, None if none."""
    matches = sorted(folder.glob(f"*-{kind}.json"))
    if not matches:
        return None
    path = matches[0]
    board = path.name.removesuffix(f"-{kind}.json")
    return Report(board, json.loads(path.read_text(encoding="utf-8")))


def collect_checks(erc: Report | None, drc: Report | None) -> list[Check]:
    """Return the table rows: ERC, then the three parts of the DRC."""
    erc_violations = None
    if erc is not None:
        erc_violations = [
            violation
            for sheet in erc.data.get("sheets", [])
            for violation in sheet.get("violations", [])
        ]
    checks = [Check("ERC", erc_violations)]
    for name, key in DRC_CHECKS:
        violations = None if drc is None else drc.data.get(key, [])
        checks.append(Check(name, violations))
    return checks


def is_excluded(violation: Violation) -> bool:
    """Return whether the violation was excluded in KiCad."""
    return bool(violation.get("excluded", False))


def active_violations(checks: Sequence[Check]) -> list[Violation]:
    """Return the violations of all checks that are not excluded."""
    return [
        violation
        for check in checks
        for violation in check.violations or []
        if not is_excluded(violation)
    ]


def escape_markdown(text: str) -> str:
    """Escape text so Markdown shows it as written."""
    text = html.escape(text, quote=False)
    for char in MARKDOWN_SPECIAL:
        text = text.replace(char, "\\" + char)
    return text


def describe(violation: Violation) -> str:
    """Return one line: type, description and the parts it concerns."""
    kind = violation.get("type", "?")
    description = escape_markdown(violation.get("description", ""))
    line = f"`{kind}`: {description}"
    items = ", ".join(
        escape_markdown(item.get("description", ""))
        for item in violation.get("items", [])
    )
    return f"{line} ({items})" if items else line


def render_status(checks: Sequence[Check], errors: Sequence[Violation]) -> str:
    """Return the status in the heading."""
    if any(check.violations is None for check in checks):
        return "⚠️ report missing"
    if errors:
        return f"❌ {len(errors)} error(s)"
    return "✅ no errors"


def render_table(checks: Sequence[Check]) -> list[str]:
    """Return the table: errors, warnings and exclusions per check."""
    lines = [
        "| Check | Errors | Warnings | Excluded |",
        "| --- | --: | --: | --: |",
    ]
    for check in checks:
        if check.violations is None:
            lines.append(f"| {check.name} | not run | not run | not run |")
            continue
        counts = Counter(
            "excluded" if is_excluded(v) else v.get("severity")
            for v in check.violations
        )
        lines.append(
            f"| {check.name} | {counts['error']} | {counts['warning']}"
            f" | {counts['excluded']} |"
        )
    return lines


def render_errors(errors: Sequence[Violation]) -> list[str]:
    """Return the error list, the first MAX_ERRORS one by one."""
    if not errors:
        return []
    lines = ["", "**Errors**", ""]
    lines += [f"- {describe(v)}" for v in errors[:MAX_ERRORS]]
    if len(errors) > MAX_ERRORS:
        more = len(errors) - MAX_ERRORS
        lines.append(f"- … and {more} more, see the HTML reports")
    return lines


def render_warnings(active: Sequence[Violation]) -> list[str]:
    """Return the warning count per type, most common first."""
    warnings = Counter(
        v.get("type", "?") for v in active if v.get("severity") == "warning"
    )
    if not warnings:
        return []
    lines = ["", "**Warnings per type**", ""]
    lines += [f"- `{kind}`: {n}" for kind, n in warnings.most_common()]
    return lines


def render_links(
    reports_url: str | None, outputs_url: str | None
) -> list[str]:
    """Return the links to the uploaded artifacts that exist."""
    lines = []
    if reports_url:
        lines += ["", f"Full HTML and JSON reports: [reports]({reports_url})"]
    if outputs_url:
        lines += ["", f"Schematic and board PDFs: [outputs]({outputs_url})"]
    return lines


def render_summary(
    erc: Report | None,
    drc: Report | None,
    reports_url: str | None = None,
    outputs_url: str | None = None,
) -> str:
    """Return the whole summary as Markdown."""
    checks = collect_checks(erc, drc)
    active = active_violations(checks)
    errors = [v for v in active if v.get("severity") == "error"]
    report = erc or drc
    board = report.board if report else "Board"

    lines = [
        f"### {board}: ERC and DRC, {render_status(checks, errors)}",
        "",
        *render_table(checks),
        *render_errors(errors),
        *render_warnings(active),
        *render_links(reports_url, outputs_url),
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Print the summary for the folder named on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "reports",
        nargs="?",
        default="reports",
        type=Path,
        help="folder with the JSON reports (default: reports)",
    )
    args = parser.parse_args(argv)

    summary = render_summary(
        load_report(args.reports, "erc"),
        load_report(args.reports, "drc"),
        os.environ.get("REPORTS_URL"),
        os.environ.get("OUTPUTS_URL"),
    )
    sys.stdout.write(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
