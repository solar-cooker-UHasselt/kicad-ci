# Commit conventions

This repo's commit rules. The shared procedure is the `propose-commit` skill, which
reads this file first and follows it where the two differ.

## Check

The board repos call this repo's workflow and action, so every commit is tested from
one of them before it is tagged:

```bash
actionlint .github/workflows/*.yml
python3 -m py_compile actions/report-summary/report-summary.py
python3 -m unittest discover -s actions/board-page
pipx run ruff check --line-length 79 actions/board-page
npx --yes prettier@3 --check actions/board-page/template.html
```

Then, in `kicad-adafruit-ds3231` (the reference repo), `just ci`, and after the tag a
real run on GitHub with its job summary and `reports` artifact.

## Types

Choose by the change's *nature*, not by copying past messages.

| Type       | When to use                                                     |
| ---------- | --------------------------------------------------------------- |
| `feat`     | A new step, output or input the board repos can use             |
| `fix`      | Corrects wrong behaviour: a failing step, a wrong summary       |
| `build`    | The pinned KiBot image or an action version changes             |
| `refactor` | Restructured, same behaviour for the board repos                |
| `docs`     | README and other documentation                                  |
| `chore`    | `.gitignore`, agent files, other maintenance                    |

## Scope

Optional. In use: `workflow` (`.github/workflows/kibot.yml`), `kibot`
(`actions/kibot/`, including the default config), `summary` (`actions/report-summary/`).
Leave the scope out when a commit spans several.

## Versions

The board repos call `@v1`, a tag the maintainer moves after each tested release:

```bash
git tag -f v1 && git push -f origin v1
```

The workflow calls the action at the same tag, so both always move together. A change
that breaks the board repos (a new required input, a renamed file they must have) gets
`!` and a `BREAKING CHANGE:` footer, and goes out as a new tag `v2`.

## Well-formed examples

```
feat: add a reusable KiBot workflow
build: pin KiBot 1.9.2 with KiCad 10.0.5
fix(summary): count excluded violations apart
chore: add commit conventions and ignore tmp/
```
