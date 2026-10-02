"""Tests for kibot.py.

Run from the repo root: python3 -m unittest discover -s cli/tests -t cli
"""

import re
import unittest
from pathlib import Path

from kicad_ci import kibot

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "kibot.yml"


class KibotTest(unittest.TestCase):
    def test_image_is_the_image_of_the_ci_workflow(self):
        match = re.search(r"container: (\S+)", WORKFLOW.read_text())
        self.assertIsNotNone(match, f"no container: line in {WORKFLOW}")
        self.assertEqual(kibot.IMAGE, match.group(1))

    def test_diff_config_takes_the_old_commit_in_a_worktree(self):
        text = kibot.config("diff.kibot.yml").read_text()
        self.assertIn('old: "@OLD@"', text)
        self.assertIn("git_diff_strategy: worktree", text)


if __name__ == "__main__":
    unittest.main()
