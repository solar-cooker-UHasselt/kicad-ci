# kicad-ci

[![Renovate](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fsolar-cooker-UHasselt%2Fkicad-ci%2Fissues%2F2&search=currently%20has%20%28no%20open%20or%20pending%29%20branches%7C%23%23%20%28Pending%20Approval%7CAwaiting%20Schedule%7CRate-Limited%7CErrored%7COpen%29&replace=%241%242&label=renovate&logo=renovatebot)](https://github.com/solar-cooker-UHasselt/kicad-ci/issues/2)

Shared KiBot CI for the KiCad board repos of
[solar-cooker-UHasselt](https://github.com/solar-cooker-UHasselt). One run checks a
board with ERC and DRC in a pinned KiCad 10 image, uploads the HTML and JSON reports
and writes a job summary with the errors and warnings. It also makes the board's
outputs (PDFs, renders, the BOM CSV and an interactive BOM) and a board page, which a
board can publish on GitHub Pages. A tag makes a draft release of an order.

## Installation

Needs a board repo in the solar-cooker-UHasselt organization, with its KiCad 10 project
in the root. Nothing to install: add `.github/workflows/kibot.yml` to the board, and it
calls this repo at `v1`:

```yaml
name: KiBot automation

on:
  push:
    branches: [ main ]
    paths-ignore: [ "**.md" ]
  # Every pull request, docs too: main requires this check before a merge
  pull_request:
  workflow_dispatch:

jobs:
  check:
    name: kicad-ci
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/kibot.yml@v1
```

The run shows as `kicad-ci / ERC, DRC and outputs`. It fetches the board's submodules
([kicad-common](https://github.com/solar-cooker-UHasselt/kicad-common)), checks its
`.kicad_dru`, and runs KiBot with the default config: ERC, DRC, PDFs, drawings, 3D
renders, the Eurocircuits BOM CSV and an interactive BOM.
[kicad-adafruit-ds3231](https://github.com/solar-cooker-UHasselt/kicad-adafruit-ds3231)
is the reference repo.

## Usage

Each part is opt-in. Open one for its setup, its own README has the details.

<details>
<summary><b>KiBot outputs and a board's own config</b></summary>

No `config.kibot.yml` is needed. A board that wants more outputs adds one that imports
the default. What the default makes, how to add or replace an output, and the pinned
KiBot image: [actions/kibot](actions/kibot/README.md).

</details>

<details>
<summary><b>Design rules</b></summary>

A board with a `<board>.kicad_dru`, copied from `kicad-common/design-rules/` by
`just rules`, gets it checked before KiBot. A copy that is out of date fails the run.
See [actions/design-rules](actions/design-rules/README.md).

</details>

<details>
<summary><b>Publish the board page</b></summary>

Every run writes a board page next to the outputs
([actions/board-page](actions/board-page/README.md)). To publish it at
`https://solar-cooker-uhasselt.github.io/<repo>/`, from `main` only, turn Pages on once
with GitHub Actions as its source:

```bash
gh api -X POST repos/solar-cooker-UHasselt/<repo>/pages -f build_type=workflow
```

Then add a second job to the board's `.github/workflows/kibot.yml`:

```yaml
  pages:
    name: kicad-ci
    needs: check
    permissions:
      pages: write
      id-token: write
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/pages.yml@v1
```

A README then shows a render by its full URL, for example
`https://solar-cooker-uhasselt.github.io/kicad-adafruit-ds3231/DS3231-render-top.png`.

</details>

<details>
<summary><b>Release an order</b></summary>

A pushed tag like `v1.1` makes a draft release with the files the board was ordered
from. The tag must match the board revision
([actions/release](actions/release/README.md)), and ERC and DRC must pass. What the
draft holds: [actions/release-draft](actions/release-draft/README.md).

Add `.github/workflows/release.yml` to the board:

```yaml
name: Release

on:
  push:
    tags: [ "v*" ]

jobs:
  release:
    name: kicad-ci
    permissions:
      contents: write
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/release.yml@v1
```

To release an order:

1. Set the new revision, `1.1`, in KiCad: Page Settings in the schematic and in the
   board, and the revision in Board Setup. Commit and push.
2. Tag and push the tag:

   ```bash
   git tag v1.1 && git push origin v1.1
   ```

3. Open the draft from the run's job summary, fill in the order and the changes, and
   publish it after ordering.

A failed run makes no release. Fix the cause, then move the tag and push it again:

```bash
git tag -f v1.1 && git push -f origin v1.1
```

</details>

<details>
<summary><b>Lint the board's workflows</b></summary>

Add `.github/workflows/lint.yml` to run
[actionlint](https://github.com/rhysd/actionlint) on the board's own workflows, only
when they change. It shows as `kicad-ci / actionlint`.

```yaml
name: Lint

on:
  push:
    branches: [ main ]
    paths: [ ".github/workflows/**" ]
  pull_request:
    paths: [ ".github/workflows/**" ]
  workflow_dispatch:

jobs:
  lint:
    name: kicad-ci
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/lint.yml@v1
```

</details>

<details>
<summary><b>Compare versions locally</b></summary>

`kicad-ci diff` compares a board's schematic and PCB with another commit, on your own
machine, in the same KiBot image as CI: [cli/README.md](cli/README.md).

</details>

## Contributing

Branches, pull requests, approval and commits work as in every repo of the org, see
[CONTRIBUTING.md](https://github.com/solar-cooker-UHasselt/.github/blob/main/.github/CONTRIBUTING.md).
Types, scopes and the tag for commits are in
[.agents/commit_conventions.md](.agents/commit_conventions.md).

### What is here

| Path | What it does |
| --- | --- |
| `.github/workflows/kibot.yml` | Reusable workflow: KiBot in `kicad10_auto`, board page, uploads, summary |
| `.github/workflows/lint.yml` | Reusable workflow: actionlint on the calling repo's workflows |
| `.github/workflows/check.yml` | This repo's own CI: actionlint, unit tests, ruff and Prettier |
| `.github/workflows/pages.yml` | Reusable workflow, opt-in: publishes the `outputs` artifact to Pages |
| `.github/workflows/release.yml` | Reusable workflow, opt-in: a draft release of an order, on a tag |
| [`actions/design-rules/`](actions/design-rules/README.md) | Composite action: checks the board's `.kicad_dru` against kicad-common |
| [`actions/kibot/`](actions/kibot/README.md) | Composite action: runs KiBot with the board config or the default |
| [`actions/board-page/`](actions/board-page/README.md) | Composite action: writes the board page, `index.html`, into `outputs/` |
| [`actions/report-summary/`](actions/report-summary/README.md) | Composite action: KiCad ERC/DRC JSON to a Markdown summary |
| [`actions/release/`](actions/release/README.md) | Composite action: checks the release tag against the board revision |
| [`actions/release-draft/`](actions/release-draft/README.md) | Composite action: the draft release with the order's files |
| [`cli/`](cli/README.md) | The `kicad-ci diff` command line tool, a Python package with its tests |
| `justfile` | `just ci` and `just test`, see [Checks](#checks) |

Each run uploads two artifacts: `reports` (ERC and DRC as HTML and JSON) and `outputs`
(the PDFs, PNGs, the BOM CSV, the interactive BOM and `index.html`). They and the job
summary are only visible when signed in to GitHub.

The outputs are made in CI. Locally, the board repos make the schematic and board PDF
with `kicad-cli` through `just pdf`, into `outputs/`. The content is the same, the look
is not: local PDFs use your own KiCad color theme and KiCad version, and your unpushed
changes.

### Checks

Needs [just](https://just.systems), and for `just ci` also
[act](https://github.com/nektos/act) and Docker.

This repo's own CI, locally: actionlint, the unit tests, ruff and Prettier, with the
versions pinned in `.github/workflows/check.yml`:

```bash
just ci
```

The jobs run one after another, so their logs do not mix. One job only, by its id in
`check.yml` (`actionlint`, `python` or `prettier`):

```bash
just ci -j python
```

Only the unit tests, in a second and without Docker:

```bash
just test
```

### Versions

Board repos call `@v1`. The tag moves after each tested change, so they get fixes
without editing their workflow. A change that needs edits in the board repos becomes
`v2`.

### Test a change before pushing

From a board repo, run the whole workflow with [act](https://github.com/nektos/act),
with `@v1` pointed at your local kicad-ci clone, uncommitted changes included:

```bash
act push -W .github/workflows/kibot.yml \
  --local-repository solar-cooker-UHasselt/kicad-ci@v1=/path/to/kicad-ci
```

act runs in a copy of the repo, so the outputs stay in the container. To look at them,
run KiBot directly on the board, with the local config mounted:

```bash
docker run --rm -v "$PWD":/w -v /path/to/kicad-ci/actions/kibot:/ci:ro -w /w \
  ghcr.io/inti-cmnb/kicad10_auto:1.9.1-1_k10.0.4_d13.2 kibot -c /ci/default.kibot.yml
```
