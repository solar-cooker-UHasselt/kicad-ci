"""The kicad-ci command.

Usage: kicad-ci [--version]
"""

import argparse
from collections.abc import Sequence

from kicad_ci import __version__


def build_parser() -> argparse.ArgumentParser:
    """Return the parser for the kicad-ci command line."""
    parser = argparse.ArgumentParser(
        prog="kicad-ci",
        description="Run kicad-ci's KiCad checks on a board locally.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run kicad-ci with the given arguments and return the exit code."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
