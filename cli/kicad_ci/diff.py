"""kicad-ci diff: compare a board's schematic and PCB with an older commit.

Runs KiBot's diff output in the image of kibot.py, so the PDFs show only the
sheets and layers that changed, as kicad-ci's CI would draw them.
"""

import os
import shutil
import subprocess
import sys
from importlib.resources import as_file
from pathlib import Path

from kicad_ci import kibot

OUTPUT_DIR = Path("outputs") / "diff"
INTERRUPTED = 130  # exit code of a command stopped with Ctrl+C (SIGINT)


class DiffError(Exception):
    """A problem the user can fix, shown without a traceback."""


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in cwd and return the result, without raising on failure."""
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def find_board(board_dir: Path) -> str:
    """Return the name of the one KiCad project in board_dir."""
    projects = sorted(board_dir.glob("*.kicad_pro"))
    if not projects:
        raise DiffError(
            f"no KiCad project (*.kicad_pro) in {board_dir}, "
            "run kicad-ci diff in a board's folder"
        )
    if len(projects) > 1:
        names = ", ".join(p.name for p in projects)
        raise DiffError(f"more than one KiCad project in {board_dir}: {names}")
    return projects[0].stem


def repo_root(board_dir: Path) -> Path:
    """Return the root of the git repository board_dir is in."""
    result = git(board_dir, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise DiffError(f"{board_dir} is not in a git repository")
    return Path(result.stdout.strip())


def fetch(board_dir: Path) -> None:
    """Fetch origin, or warn and go on with what was fetched before."""
    result = git(board_dir, "fetch", "--quiet", "origin")
    if result.returncode != 0:
        print(
            "kicad-ci: warning: could not fetch origin, "
            "comparing with what was fetched before",
            file=sys.stderr,
        )


def resolve(board_dir: Path, ref: str) -> str:
    """Return the commit hash ref points to."""
    result = git(
        board_dir, "rev-parse", "--verify", "--quiet", ref + "^{commit}"
    )
    if result.returncode != 0:
        raise DiffError(f"unknown commit, tag or branch: {ref}")
    return result.stdout.strip()


def board_changed(board_dir: Path, name: str, commit: str) -> bool:
    """Return whether the schematic or PCB differ from commit."""
    result = git(
        board_dir,
        "diff",
        "--quiet",
        commit,
        "--",
        "*.kicad_sch",
        f"{name}.kicad_pcb",
    )
    return result.returncode != 0


def kibot_command(
    root: Path, board_dir: Path, name: str, commit: str, config: Path
) -> list[str]:
    """Return the docker command that runs KiBot's diff on the board."""
    workdir = Path("/work") / board_dir.relative_to(root)
    # One flag and its value per line, as in a shell command
    # fmt: off
    docker = [
        "docker", "run", "--rm",
        "--init",                                  # so Ctrl+C stops KiBot
        "--user", f"{os.getuid()}:{os.getgid()}",  # outputs owned by you
        "--env", "HOME=/tmp",
        "--volume", f"{root}:/work:Z",             # the repo, :Z for SELinux
        "--volume", f"{config}:/cfg/diff.kibot.yml:ro,Z",
        "--workdir", str(workdir),
        kibot.IMAGE,
    ]
    kibot_args = [
        "kibot",
        "--plot-config", "/cfg/diff.kibot.yml",
        "--schematic", f"{name}.kicad_sch",
        "--board-file", f"{name}.kicad_pcb",
        "--out-dir", str(OUTPUT_DIR),
        "--define", f"OLD={commit}",               # the commit to compare
    ]
    # fmt: on
    return docker + kibot_args


def run_kibot(command: list[str]) -> int:
    """Run the docker command and return its exit code."""
    return subprocess.run(command, check=False).returncode


def diff(ref: str, *, fetch_first: bool = True, board_dir: Path) -> int:
    """Compare the board in board_dir with ref, return the exit code."""
    board_dir = board_dir.resolve()
    name = find_board(board_dir)
    root = repo_root(board_dir)
    if fetch_first:
        fetch(board_dir)
    commit = resolve(board_dir, ref)

    if not board_changed(board_dir, name, commit):
        print(f"No changes in {name} against {ref}.")
        return 0

    if shutil.which("docker") is None:
        raise DiffError(
            "Docker is needed to run KiBot: "
            "https://docs.docker.com/engine/install/"
        )

    print(
        f"Comparing {name} with {ref} ({commit[:7]}) in KiBot...", flush=True
    )
    try:
        with as_file(kibot.config("diff.kibot.yml")) as config:
            code = run_kibot(
                kibot_command(root, board_dir, name, commit, config)
            )
    finally:
        # KiBot removes its worktrees, unless it was stopped halfway
        git(board_dir, "worktree", "prune")

    if code == INTERRUPTED:
        raise KeyboardInterrupt
    if code != 0:
        raise DiffError(f"KiBot failed with exit code {code}, see above")

    print("Only the sheets and layers that changed:")
    for kind in ("sch", "pcb"):
        print(f"  {OUTPUT_DIR / f'{name}-diff_{kind}.pdf'}")
    return 0
