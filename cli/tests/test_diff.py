"""Tests for diff.py, on real git repositories with Docker faked.

Run from the repo root: python3 -m unittest discover -s cli/tests -t cli
"""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from kicad_ci import diff, kibot
from kicad_ci.cli import main


def git(cwd, *args):
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def write_board(board_dir, name="DS3231", text="v1"):
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / f"{name}.kicad_pro").write_text("{}")
    (board_dir / f"{name}.kicad_sch").write_text(f"sch {text}")
    (board_dir / f"{name}.kicad_pcb").write_text(f"pcb {text}")


class GitRepoTest(unittest.TestCase):
    """A clone with a board at its root and an origin it was pushed to."""

    board_subdir = "."

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        tmp_path = Path(tmp.name)
        origin = tmp_path / "origin.git"
        git(tmp_path, "init", "--quiet", "--bare", "-b", "main", str(origin))

        self.root = tmp_path / "board-repo"
        git(tmp_path, "clone", "--quiet", str(origin), str(self.root))
        git(self.root, "checkout", "--quiet", "-b", "main")
        self.board = self.root / self.board_subdir
        write_board(self.board)
        (self.root / "README.md").write_text("readme")
        git(self.root, "add", ".")
        git(self.root, "commit", "--quiet", "-m", "board")
        git(self.root, "push", "--quiet", "origin", "main")

        self.kibot = mock.patch.object(diff, "run_kibot", return_value=0)
        self.run_kibot = self.kibot.start()
        self.addCleanup(self.kibot.stop)
        self.which = mock.patch.object(
            diff.shutil, "which", return_value="/usr/bin/docker"
        )
        self.which.start()
        self.addCleanup(self.which.stop)

    def run_diff(self, *args):
        """Run kicad-ci diff in the board, return code, stdout, stderr."""
        out, err = io.StringIO(), io.StringIO()
        with (
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
            contextlib.chdir(self.board),
        ):
            code = main(["diff", *args])
        return code, out.getvalue(), err.getvalue()

    def rev_parse(self, ref):
        return subprocess.run(
            ["git", "rev-parse", ref],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def docker_command(self):
        self.run_kibot.assert_called_once()
        return self.run_kibot.call_args.args[0]


class DiffTest(GitRepoTest):
    def test_no_changes_does_not_start_kibot(self):
        code, out, _ = self.run_diff()
        self.assertEqual(code, 0)
        self.assertIn("No changes in DS3231 against origin/main", out)
        self.run_kibot.assert_not_called()

    def test_change_outside_the_board_files_is_no_change(self):
        (self.root / "README.md").write_text("new readme")
        code, out, _ = self.run_diff()
        self.assertEqual(code, 0)
        self.assertIn("No changes", out)

    def test_uncommitted_pcb_change_runs_kibot_against_origin_main(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        code, out, _ = self.run_diff()
        self.assertEqual(code, 0)
        command = self.docker_command()
        origin_main = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertIn(kibot.IMAGE, command)
        self.assertIn(f"OLD={origin_main}", command)
        self.assertIn("outputs/diff/DS3231-diff_pcb.pdf", out)

    def test_command_mounts_the_repo_and_names_the_board_files(self):
        (self.board / "DS3231.kicad_sch").write_text("sch v2")
        self.run_diff()
        command = self.docker_command()
        self.assertIn(f"{self.root.resolve()}:/work:Z", command)
        self.assertEqual(command[command.index("--workdir") + 1], "/work")
        self.assertIn("DS3231.kicad_sch", command)
        self.assertIn("DS3231.kicad_pcb", command)

    def test_committed_but_unpushed_change_counts(self):
        (self.board / "DS3231.kicad_sch").write_text("sch v2")
        git(self.root, "commit", "--quiet", "-am", "change")
        code, _, _ = self.run_diff("--no-fetch")
        self.assertEqual(code, 0)
        self.run_kibot.assert_called_once()

    def test_other_ref_is_compared(self):
        git(self.root, "tag", "v1.0")
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        git(self.root, "commit", "--quiet", "-am", "change")
        code, out, _ = self.run_diff("v1.0")
        self.assertEqual(code, 0)
        self.assertIn("with v1.0", out)

    def test_files_on_disk_are_the_new_side_by_default(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        self.run_diff()
        command = self.docker_command()
        self.assertIn("NEW_TYPE=current", command)
        self.assertIn("NEW=", command)

    def test_two_commits_are_compared_with_each_other(self):
        git(self.root, "tag", "v1.0")
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        git(self.root, "commit", "--quiet", "-am", "change")
        git(self.root, "tag", "v1.1")
        (self.board / "DS3231.kicad_pcb").write_text("pcb v3, not committed")
        code, out, _ = self.run_diff("v1.0", "v1.1")
        self.assertEqual(code, 0)
        command = self.docker_command()
        self.assertIn("NEW_TYPE=git", command)
        self.assertIn(f"NEW={self.rev_parse('v1.1')}", command)
        self.assertIn(f"OLD={self.rev_parse('v1.0')}", command)
        self.assertIn("between v1.0", out)

    def test_two_commits_with_the_same_board_are_no_change(self):
        git(self.root, "tag", "v1.0")
        (self.root / "README.md").write_text("new readme")
        git(self.root, "commit", "--quiet", "-am", "readme only")
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2, not committed")
        code, out, _ = self.run_diff("v1.0", "HEAD")
        self.assertEqual(code, 0)
        self.assertIn("No changes in DS3231 between v1.0 and HEAD", out)
        self.run_kibot.assert_not_called()

    def test_unknown_new_ref_fails(self):
        code, _, err = self.run_diff("origin/main", "no-such-tag")
        self.assertEqual(code, 1)
        self.assertIn("unknown commit, tag or branch: no-such-tag", err)

    def test_unknown_ref_fails(self):
        code, _, err = self.run_diff("no-such-branch")
        self.assertEqual(code, 1)
        self.assertIn("unknown commit, tag or branch: no-such-branch", err)

    def test_fetch_failure_warns_and_goes_on(self):
        git(self.root, "remote", "set-url", "origin", "/no/such/origin")
        code, out, err = self.run_diff()
        self.assertEqual(code, 0)
        self.assertIn("could not fetch origin", err)
        self.assertIn("No changes", out)

    def test_missing_docker_fails(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        with mock.patch.object(diff.shutil, "which", return_value=None):
            code, _, err = self.run_diff()
        self.assertEqual(code, 1)
        self.assertIn("Docker is needed", err)

    def test_kibot_failure_is_reported(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        self.run_kibot.return_value = 3
        code, _, err = self.run_diff()
        self.assertEqual(code, 1)
        self.assertIn("KiBot failed with exit code 3", err)

    def test_ctrl_c_in_kibot_reports_stopped(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        self.run_kibot.return_value = diff.INTERRUPTED
        code, _, err = self.run_diff()
        self.assertEqual(code, 130)
        self.assertEqual(err, "kicad-ci: stopped\n")

    def test_leftover_worktrees_are_pruned(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        leftover = self.root.parent / "kibot-worktree"
        git(self.root, "worktree", "add", "--quiet", str(leftover), "HEAD")
        subprocess.run(["rm", "-rf", str(leftover)], check=True)
        self.run_diff()
        worktrees = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertNotIn("kibot-worktree", worktrees)


class BoardInSubfolderTest(GitRepoTest):
    board_subdir = "hardware"

    def test_workdir_is_the_board_folder_in_the_repo(self):
        (self.board / "DS3231.kicad_pcb").write_text("pcb v2")
        self.run_diff()
        command = self.docker_command()
        self.assertIn(f"{self.root.resolve()}:/work:Z", command)
        self.assertEqual(
            command[command.index("--workdir") + 1], "/work/hardware"
        )


class LabelTest(unittest.TestCase):
    def test_name_gets_its_short_hash(self):
        self.assertEqual(
            diff.label("v1.0", "a33e0f2" + "0" * 33), "v1.0 (a33e0f2)"
        )

    def test_hash_is_not_repeated(self):
        self.assertEqual(
            diff.label("a33e0f2", "a33e0f2" + "0" * 33), "a33e0f2"
        )


class FindBoardTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_no_project_fails(self):
        with self.assertRaisesRegex(diff.DiffError, "no KiCad project"):
            diff.find_board(self.dir)

    def test_two_projects_fail(self):
        write_board(self.dir, "A")
        write_board(self.dir, "B")
        with self.assertRaisesRegex(
            diff.DiffError, "A.kicad_pro, B.kicad_pro"
        ):
            diff.find_board(self.dir)

    def test_one_project_is_the_board(self):
        write_board(self.dir)
        self.assertEqual(diff.find_board(self.dir), "DS3231")


class NotARepoTest(unittest.TestCase):
    def test_board_outside_git_fails(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        board = Path(tmp.name)
        write_board(board)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.chdir(board):
            code = main(["diff"])
        self.assertEqual(code, 1)
        self.assertIn("is not in a git repository", err.getvalue())


if __name__ == "__main__":
    unittest.main()
