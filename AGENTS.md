# AGENTS.md

Guidance for AI coding agents working in this repository. `CLAUDE.md` is a symlink to
this file.

Make sure to also read [`README.md`](README.md) for the human-facing docs.

## Project overview

The shared CI of the solar-cooker-UHasselt KiCad boards: reusable GitHub workflows and
composite actions that run KiBot (ERC, DRC, outputs) in a pinned KiCad 10 image, write
a job summary, build and publish a board page, and draft a release per order. Board
repos call it at the `v1` tag. Also a small Python command line tool, `kicad-ci diff`,
in `cli/`.

Every board runs this code, so a change is tested here and on the reference board,
[kicad-adafruit-ds3231](https://github.com/solar-cooker-UHasselt/kicad-adafruit-ds3231),
before `v1` moves.

## Repository map

```
.github/workflows/    # kibot, lint, pages, release: reusable, check: this repo's own CI
actions/              # composite actions the workflows call, each with a README
  kibot/              #   KiBot run, default.kibot.yml is the config boards get
  board-page/         #   board page (board_page.py, template.html), with unit tests
  report-summary/     #   ERC/DRC JSON to the job summary, with unit tests
  design-rules/       #   the board's .kicad_dru against kicad-common
  release/            #   release tag against the board revision
  release-draft/      #   the draft release and its text (notes.md)
cli/                  # kicad-ci command line tool (Python package kicad_ci, tests)
justfile              # just ci, just test
ruff.toml             # ruff rules for all Python here
renovate.json         # pinned versions: KiBot image, actions, lint tools
.agents/              # commit and documentation conventions
```

The full table, with what each workflow and action does, is the README's "What is here".

## Where things live

| To change…                              | Edit                                              |
| --------------------------------------- | ------------------------------------------------- |
| What KiBot makes for every board        | `actions/kibot/default.kibot.yml`                 |
| The KiBot image (KiCad version)         | Renovate: `kibot.yml` and `cli/kicad_ci/kibot.py` |
| The board page                          | `actions/board-page/`                             |
| The ERC/DRC job summary                 | `actions/report-summary/`                         |
| The release check or draft text         | `actions/release/`, `actions/release-draft/`      |
| Which jobs a board run has              | `.github/workflows/kibot.yml`                     |
| This repo's own CI and its pinned tools | `.github/workflows/check.yml`                     |
| The diff tool                           | `cli/kicad_ci/`                                   |

## Setup

Needs Python 3.13 (as in the KiBot image) and just. `just ci` also needs act and
Docker. The CLI install: [cli/README.md](cli/README.md).

## Checks

```bash
just test   # unit tests of both scripts and the CLI, no Docker, while working
just ci     # check.yml with act: actionlint, unit tests, ruff, Prettier, must pass
```

Then test on ds3231 before `v1` moves: the commit conventions' Check. Tool versions
are pinned in `check.yml` only.

Before finishing, re-read the diff and check it follows existing patterns, is minimal
(nothing unrelated touched), and passes `just ci`. (Our convention.)

## Code style

- Python: ruff lint and format, rules in `ruff.toml`. Unit tests with `unittest`, next
  to the script (`test_<script>.py`) or in `cli/tests/`.
- Shell (`*.sh`): POSIX `sh`, called from the `action.yml` next to it. Logic lives in
  the script, not inline in `action.yml`.
- `template.html`: Prettier.
- Pin every action and image to an exact version. Renovate updates them.

## Tools

- **GitHub Actions.** The reusable workflows' inputs and the jobs a board sees are the
  public interface: a change a board must follow up on is a breaking change, `v2`.
- **KiBot.** The image is `ghcr.io/inti-cmnb/kicad10_auto`, pinned in the container of
  `.github/workflows/kibot.yml` and in `cli/kicad_ci/kibot.py`. Change both together.
- **Renovate.** Dashboard in issue #2. Its PRs need the same approval as any other.

## Security

- The workflows use only the `GITHUB_TOKEN`. `pages.yml` needs `pages: write` and
  `id-token: write`, `release.yml` `contents: write`, each on its own job only.
- Never commit `tmp/`. `.gitignore` covers it.

## Commit & PR guidelines

**Never commit. Propose the message only**, and the maintainer reviews and commits
manually. Do not run `git commit` / `git push` / `git add` unless explicitly told to.
Never move the `v1` tag: the maintainer does, after the test on ds3231. (Our
convention.)

Use the `propose-commit` skill: Conventional Commits, one concern per commit, the
message handed over in `tmp/`. This repo's types, scopes, check and versions:
[.agents/commit_conventions.md](.agents/commit_conventions.md). **Never use em dashes or
semicolons** in commit messages or any written output. (Our convention.)

Pull requests follow the org's
[CONTRIBUTING.md](https://github.com/solar-cooker-UHasselt/.github/blob/main/.github/CONTRIBUTING.md),
enforced by the org's
[rulesets](https://github.com/solar-cooker-UHasselt/.github/tree/main/rulesets).

## Documentation

Use the `check-docs` skill when writing or reshaping a README or an agent file: one
Diátaxis type per file, the README shape, naming. This repo's doc map, exceptions and
link check: [.agents/documentation_conventions.md](.agents/documentation_conventions.md).
(Our convention.)

## Deployment

- No deploy of its own. A board repo gets a change once the maintainer moves `v1`
  (`git tag -f v1 && git push -f origin v1`). `just ci` in a board caches `v1` under
  `~/.cache/act/`, clear it after the tag moves.

## References

- agents.md spec: <https://agents.md/>
- KiBot docs: <https://kibot.readthedocs.io/>
- Reusable workflows: <https://docs.github.com/en/actions/sharing-automations/reusing-workflows>
