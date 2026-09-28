"""Tests for board_page.py.

Run from the repo root: python3 -m unittest discover -s actions/board-page
"""

import tempfile
import unittest
from pathlib import Path

import board_page
from board_page import Source

SOURCE = Source("solar-cooker-UHasselt/kicad-example", "0123456789abcdef")


class BoardPageTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)

    def add(self, *names: str) -> None:
        for name in names:
            (self.folder / name).touch()

    def write(self, source: Source | None = SOURCE) -> str:
        path = board_page.write_page(self.folder, source)
        self.assertIsNotNone(path)
        return path.read_text(encoding="utf-8")

    def test_no_known_outputs_writes_no_page(self) -> None:
        self.add("notes.txt")
        self.assertIsNone(board_page.write_page(self.folder, SOURCE))
        self.assertFalse((self.folder / "index.html").exists())

    def test_board_name_from_any_known_output(self) -> None:
        self.add("DS3231-schematic.pdf")
        self.assertEqual(board_page.find_board(self.folder), "DS3231")

    def test_shows_only_outputs_that_exist(self) -> None:
        self.add("DS3231-render-top.png", "DS3231-board.pdf")
        page = self.write()
        self.assertIn('src="DS3231-render-top.png"', page)
        self.assertIn('href="DS3231-board.pdf"', page)
        self.assertNotIn("render-bottom", page)
        self.assertNotIn("schematic.pdf", page)

    def test_links_the_bom(self) -> None:
        self.add("DS3231-bom.html", "DS3231-bom.csv")
        page = self.write()
        self.assertIn('href="DS3231-bom.html"', page)
        self.assertIn('href="DS3231-bom.csv"', page)

    def test_every_link_opens_in_a_new_tab(self) -> None:
        self.add("DS3231-render-top.png", "DS3231-schematic.pdf")
        page = self.write()
        self.assertEqual(page.count("<a "), page.count('target="_blank"'))

    def test_links_the_commit_and_repo(self) -> None:
        self.add("DS3231-render-top.png")
        page = self.write()
        self.assertIn(f"{SOURCE.commit_url}", page)
        self.assertIn(">0123456<", page)
        self.assertIn(f'href="{SOURCE.repo_url}"', page)

    def test_local_build_has_no_github_links(self) -> None:
        self.add("DS3231-render-top.png")
        page = self.write(source=None)
        self.assertIn("Local build", page)
        self.assertNotIn("github.com", page)

    def test_board_name_is_escaped(self) -> None:
        self.add("A&B-render-top.png")
        page = self.write()
        self.assertIn("<title>A&amp;B</title>", page)
        self.assertNotIn("A&B", page)


class SourceFromEnvTest(unittest.TestCase):
    def test_both_variables_set(self) -> None:
        env = {"GITHUB_REPOSITORY": "org/repo", "GITHUB_SHA": "abc"}
        self.assertEqual(
            board_page.source_from_env(env), Source("org/repo", "abc")
        )

    def test_missing_variable(self) -> None:
        env = {"GITHUB_REPOSITORY": "org/repo"}
        self.assertIsNone(board_page.source_from_env(env))


if __name__ == "__main__":
    unittest.main()
