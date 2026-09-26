"""Turn KiCad ERC and DRC JSON reports into a Markdown job summary.

Usage: python3 report-summary.py <report dir> >> "$GITHUB_STEP_SUMMARY"
Reads <board>-erc.json and <board>-drc.json, as written by KiBot or kicad-cli.
If REPORTS_URL or OUTPUTS_URL is set, the summary links to those artifacts.
Report format: https://schemas.kicad.org/erc.v1.json and drc.v1.json
"""

import html
import json
import os
import sys
from collections import Counter
from pathlib import Path

MAX_ERRORS = 25


def load(report_dir, kind):
    """Return (board, report) for <board>-<kind>.json, or (None, None) if missing."""
    path = next(iter(sorted(Path(report_dir).glob(f"*-{kind}.json"))), None)
    if path is None:
        return None, None
    board = path.name.removesuffix(f"-{kind}.json")
    return board, json.loads(path.read_text())


def checks(erc, drc):
    """Return (name, violations) per check, violations is None if its report is missing."""
    erc_violations = None
    if erc is not None:
        erc_violations = [v for sheet in erc.get("sheets", []) for v in sheet.get("violations", [])]
    rows = [("ERC", erc_violations)]
    for name, key in [("DRC", "violations"), ("Unconnected", "unconnected_items"),
                      ("Schematic parity", "schematic_parity")]:
        rows.append((name, None if drc is None else drc.get(key, [])))
    return rows


def md(text):
    """Escape text so Markdown shows it as written."""
    text = html.escape(text, quote=False)
    for char in "\\`*_[]~":
        text = text.replace(char, "\\" + char)
    return text


def describe(violation):
    """One line per violation: type, description and the parts it concerns."""
    items = ", ".join(md(i.get("description", "")) for i in violation.get("items", []))
    line = f"`{violation.get('type', '?')}`: {md(violation.get('description', ''))}"
    return f"{line} ({items})" if items else line


def main(report_dir):
    board_erc, erc = load(report_dir, "erc")
    board_drc, drc = load(report_dir, "drc")
    rows = checks(erc, drc)

    active = []
    for _, violations in rows:
        for v in violations or []:
            if not v.get("excluded", False):
                active.append(v)
    errors = [v for v in active if v.get("severity") == "error"]
    warnings = Counter(v.get("type", "?") for v in active if v.get("severity") == "warning")

    if any(violations is None for _, violations in rows):
        status = "⚠️ report missing"
    elif errors:
        status = f"❌ {len(errors)} error(s)"
    else:
        status = "✅ no errors"
    print(f"### {board_erc or board_drc or 'Board'}: ERC and DRC, {status}\n")

    print("| Check | Errors | Warnings | Excluded |")
    print("| --- | --: | --: | --: |")
    for name, violations in rows:
        if violations is None:
            print(f"| {name} | not run | not run | not run |")
            continue
        counts = Counter("excluded" if v.get("excluded", False) else v.get("severity")
                         for v in violations)
        print(f"| {name} | {counts['error']} | {counts['warning']} | {counts['excluded']} |")

    if errors:
        print("\n**Errors**\n")
        for v in errors[:MAX_ERRORS]:
            print(f"- {describe(v)}")
        if len(errors) > MAX_ERRORS:
            print(f"- … and {len(errors) - MAX_ERRORS} more, see the HTML reports")
    if warnings:
        print("\n**Warnings per type**\n")
        for kind, count in warnings.most_common():
            print(f"- `{kind}`: {count}")

    reports_url = os.environ.get("REPORTS_URL")
    if reports_url:
        print(f"\nFull HTML and JSON reports: [reports]({reports_url})")
    outputs_url = os.environ.get("OUTPUTS_URL")
    if outputs_url:
        print(f"\nSchematic and board PDFs: [outputs]({outputs_url})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "reports")
