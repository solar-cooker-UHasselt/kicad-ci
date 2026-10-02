"""Tests for the kicad-ci command line.

Run from the repo root: python3 -m unittest discover -s cli/tests -t cli
"""

import contextlib
import io
import unittest

from kicad_ci import __version__
from kicad_ci.cli import main


def run(*args):
    """Run kicad-ci with the arguments, return the exit code and output."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            code = main(list(args))
        except SystemExit as error:
            code = error.code
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def test_version_prints_name_and_version(self):
        code, out = run("--version")
        self.assertEqual(code, 0)
        self.assertEqual(out, f"kicad-ci {__version__}\n")

    def test_no_arguments_prints_help(self):
        code, out = run()
        self.assertEqual(code, 0)
        self.assertIn("usage: kicad-ci", out)

    def test_unknown_option_fails(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = run("--no-such-option")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
