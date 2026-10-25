# Documentation conventions

This repo's documentation rules. The shared conventions are the `check-docs` skill,
which reads this file first and follows it where the two differ.

## Doc map

Each document and the one type it is:

| File                                   | Type      |
| -------------------------------------- | --------- |
| `README.md`                            | how-to    |
| `cli/README.md`                        | how-to    |
| `actions/board-page/README.md`         | reference |
| `actions/design-rules/README.md`       | reference |
| `actions/kibot/README.md`              | reference |
| `actions/release/README.md`            | reference |
| `actions/release-draft/README.md`      | reference |
| `actions/report-summary/README.md`     | reference |
| `AGENTS.md`                            | reference |
| `.agents/commit_conventions.md`        | reference |
| `.agents/documentation_conventions.md` | reference |

`actions/release-draft/notes.md` is not a document: it is the text of every draft
release, filled in by `draft.sh`.

## Where things go

- **`actions/<name>/README.md`**: what that action does, its inputs and what fails it.
  The top README keeps what a board repo adds to opt in, and links there.
- **`docs/`**: none yet. A guide that outgrows the README goes there.
- **`.agents/`**: `commit_conventions.md` (types, scopes, the check, the `v1` tag),
  `documentation_conventions.md` (this file).

## Exceptions

- **`cli/kicad_ci/`.** The Python package uses an underscore: Python cannot import a
  name with a hyphen.
- **Names a tool looks for.** `action.yml` (GitHub Actions), `pyproject.toml`,
  `ruff.toml`, `renovate.json`, and the `.kibot.yml` ending KiBot's configs use.
- **`check-revision.sh`.** Has a hyphen, against the file rule. Not renamed yet:
  `actions/release/action.yml` calls it by name, so a rename is a code change.

## Check

Every relative link in the repo's own Markdown resolves: the fallback link check in the
`check-docs` skill.
