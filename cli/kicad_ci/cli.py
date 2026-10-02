"""The kicad-ci command.

Usage: kicad-ci [--version] {diff} ...
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from kicad_ci import __version__
from kicad_ci.diff import DiffError, diff


def build_parser() -> argparse.ArgumentParser:
    """Return the parser for the kicad-ci command line."""
    parser = argparse.ArgumentParser(
        prog="kicad-ci",
        description="Run kicad-ci's KiCad checks on a board locally.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    commands = parser.add_subparsers(dest="command", title="commands")

    diff_parser = commands.add_parser(
        "diff",
        help="show what changed in the schematic and PCB",
        description=(
            "Compare the board in this folder, as it is now, with an older "
            "commit. Writes PDFs with only the sheets and layers that "
            "changed to outputs/diff/. Needs Docker."
        ),
    )
    diff_parser.add_argument(
        "ref",
        nargs="?",
        default="origin/main",
        help="commit, tag or branch to compare with (default: origin/main)",
    )
    diff_parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="do not fetch origin first",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run kicad-ci with the given arguments and return the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return diff(args.ref, fetch_first=not args.no_fetch, board_dir=Path())
    except DiffError as error:
        print(f"kicad-ci: error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("kicad-ci: stopped", file=sys.stderr)
        return 130
