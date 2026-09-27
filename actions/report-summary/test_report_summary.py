"""Tests for report_summary.py.

Run from the repo root: python3 -m unittest discover -s actions/report-summary
"""

import json
import tempfile
import unittest
from pathlib import Path

import report_summary
from report_summary import MAX_ERRORS, Report


def violation(severity, kind="some_type", excluded=False, **fields):
    """Return a violation as KiCad writes it."""
    return {"severity": severity, "type": kind, "excluded": excluded, **fields}


def erc(*violations):
    """Return an ERC report with the violations on one sheet."""
    return Report("DS3231", {"sheets": [{"violations": list(violations)}]})


def drc(violations=(), unconnected=(), parity=()):
    """Return a DRC report with the three kinds of violations."""
    return Report(
        "DS3231",
        {
            "violations": list(violations),
            "unconnected_items": list(unconnected),
            "schematic_parity": list(parity),
        },
    )


class RenderSummaryTest(unittest.TestCase):
    def test_clean_board(self) -> None:
        summary = report_summary.render_summary(erc(), drc())
        self.assertIn("### DS3231: ERC and DRC, ✅ no errors", summary)
        self.assertIn("| ERC | 0 | 0 | 0 |", summary)
        self.assertNotIn("**Errors**", summary)

    def test_counts_errors_warnings_and_exclusions_per_check(self) -> None:
        summary = report_summary.render_summary(
            erc(
                violation("error"),
                violation("warning"),
                violation("error", excluded=True),
            ),
            drc(unconnected=[violation("error")]),
        )
        self.assertIn("❌ 2 error(s)", summary)
        self.assertIn("| ERC | 1 | 1 | 1 |", summary)
        self.assertIn("| Unconnected | 1 | 0 | 0 |", summary)

    def test_excluded_error_is_not_listed(self) -> None:
        summary = report_summary.render_summary(
            erc(violation("error", "hidden", excluded=True)), drc()
        )
        self.assertIn("✅ no errors", summary)
        self.assertNotIn("hidden", summary)

    def test_missing_report_is_not_run(self) -> None:
        summary = report_summary.render_summary(erc(), None)
        self.assertIn("⚠️ report missing", summary)
        self.assertIn("| DRC | not run | not run | not run |", summary)

    def test_no_reports_at_all(self) -> None:
        summary = report_summary.render_summary(None, None)
        self.assertIn("### Board: ERC and DRC, ⚠️ report missing", summary)

    def test_lists_only_the_first_errors(self) -> None:
        errors = [violation("error", f"e{i}") for i in range(MAX_ERRORS + 5)]
        summary = report_summary.render_summary(erc(*errors), drc())
        self.assertIn(f"`e{MAX_ERRORS - 1}`", summary)
        self.assertNotIn(f"`e{MAX_ERRORS}`", summary)
        self.assertIn("- … and 5 more, see the HTML reports", summary)

    def test_error_line_names_the_parts(self) -> None:
        error = violation(
            "error",
            "pin_not_connected",
            description="Pin not connected",
            items=[{"description": "R1"}, {"description": "U1"}],
        )
        summary = report_summary.render_summary(erc(error), drc())
        self.assertIn(
            "- `pin_not_connected`: Pin not connected (R1, U1)", summary
        )

    def test_warnings_per_type_most_common_first(self) -> None:
        summary = report_summary.render_summary(
            erc(violation("warning", "rare")),
            drc([violation("warning", "common")] * 2),
        )
        self.assertLess(
            summary.index("- `common`: 2"), summary.index("- `rare`: 1")
        )

    def test_links_only_the_artifacts_given(self) -> None:
        summary = report_summary.render_summary(erc(), drc(), "https://r")
        self.assertIn("[reports](https://r)", summary)
        self.assertNotIn("[outputs]", summary)

    def test_outputs_link_names_its_contents(self) -> None:
        summary = report_summary.render_summary(
            erc(), drc(), outputs_url="https://o"
        )
        self.assertIn(
            "Schematic and board PDFs, renders and board page:"
            " [outputs](https://o)",
            summary,
        )


class EscapeMarkdownTest(unittest.TestCase):
    def test_markdown_characters_show_as_written(self) -> None:
        self.assertEqual(
            report_summary.escape_markdown("*a* `b` [c]_d~"),
            r"\*a\* \`b\` \[c\]\_d\~",
        )

    def test_html_is_escaped(self) -> None:
        self.assertEqual(
            report_summary.escape_markdown("<0.2mm>"), "&lt;0.2mm&gt;"
        )


class LoadReportTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def test_reads_board_name_and_data(self) -> None:
        data = {"sheets": []}
        (self.folder / "DS3231-erc.json").write_text(json.dumps(data))
        report = report_summary.load_report(self.folder, "erc")
        self.assertEqual(report, Report("DS3231", data))

    def test_missing_report(self) -> None:
        self.assertIsNone(report_summary.load_report(self.folder, "drc"))


if __name__ == "__main__":
    unittest.main()
