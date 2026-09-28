# kicad-ci

[![Renovate](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fsolar-cooker-UHasselt%2Fkicad-ci%2Fissues%2F2&search=currently%20has%20%28no%20open%20or%20pending%29%20branches%7C%23%23%20%28Pending%20Approval%7CAwaiting%20Schedule%7CRate-Limited%7CErrored%7COpen%29&replace=%241%242&label=renovate&logo=renovatebot)](https://github.com/solar-cooker-UHasselt/kicad-ci/issues/2)

Shared KiBot CI for the KiCad board repos of
[solar-cooker-UHasselt](https://github.com/solar-cooker-UHasselt). One run checks a
board with ERC and DRC in a pinned KiCad 10 image, uploads the HTML and JSON reports
and writes a job summary with the errors and warnings.

## Use it in a board repo

`.github/workflows/kibot.yml`:

```yaml
name: KiBot automation

on:
  push:
    branches: [ main ]
    paths-ignore: [ "**.md" ]
  pull_request:
    paths-ignore: [ "**.md" ]
  workflow_dispatch:

jobs:
  check:
    name: kicad-ci
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/kibot.yml@v1
```

The Actions tab then shows the job as `kicad-ci / ERC, DRC and outputs`.

The check also fetches the board's git submodules, so a board that mounts
[kicad-common](https://github.com/solar-cooker-UHasselt/kicad-common) at `kicad-common/` gets
its symbols, footprints and 3D models in CI too.

Before KiBot, the check compares the board's `<board>.kicad_dru` with the rule sets in
`kicad-common/design-rules/`. The board keeps a copy, made by `just rules`, because
KiCad only reads that file. A copy that matches none of them fails the job with "out of
date, run: just rules", for example after a kicad-common update. A board without a
`.kicad_dru` is skipped. The job summary names the rule set in use.

No `config.kibot.yml` is needed. Without one, KiBot runs with
[`actions/kibot/default.kibot.yml`](actions/kibot/default.kibot.yml): ERC and DRC, a
schematic and board PDF, PNGs of the top and bottom side (a PcbDraw drawing and a 3D
render each), and a bill of materials as CSV and HTML with the Eurocircuits columns
(Reference, Qty, Manufacturer, MPN, Supplier, SPN, Component package type,
Description), sorted by supplier. The CSV holds only the table, with semicolons between
the columns and every field quoted, so it uploads to Eurocircuits as it is.

A board that needs more adds its own `config.kibot.yml` that imports the default:

```yaml
kibot:
  version: 1

import:
  - file: "@KICAD_CI_DEFAULT@"

outputs:
  - name: render-top-flat
    comment: "3D render of the top side, straight from above"
    type: render_3d
```

An output name can only be defined once. The default already has `schematic-pdf`,
`board-pdf`, `pcbdraw-top`, `pcbdraw-bottom`, `render-top`, `render-bottom`, `bom-csv`
and `bom-html`, so a board's own output needs a new name. KiBot stops with "Output
name … already defined" otherwise. To replace a default output, import the others by
name and define it again:

```yaml
import:
  - file: "@KICAD_CI_DEFAULT@"
    outputs: [schematic-pdf, board-pdf, pcbdraw-top, pcbdraw-bottom, render-bottom, bom-csv, bom-html]

outputs:
  - name: render-top
    type: render_3d
```

The preflights (ERC and DRC) are still imported.

[kicad-adafruit-ds3231](https://github.com/solar-cooker-UHasselt/kicad-adafruit-ds3231)
is the reference repo.

## Publish the board page

Each run writes `index.html` next to the outputs: the 3D renders and drawings, with
links to the PDFs and the bill of materials. A board can publish it on GitHub Pages, at
`https://solar-cooker-uhasselt.github.io/<repo>/`, so the images can be shown in its
README without committing them. Only pushes to `main` publish.

Opt-in, in two steps. Turn Pages on once, with GitHub Actions as its source:

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

A README shows an image with its full URL, for example
`https://solar-cooker-uhasselt.github.io/kicad-adafruit-ds3231/DS3231-render-top.png`.

## Lint the board's workflows

A second workflow, `.github/workflows/lint.yml`, runs
[actionlint](https://github.com/rhysd/actionlint) on the board's own workflows,
only when they change:

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

The Actions tab shows it as `kicad-ci / actionlint`.

## What is here

| Path | What it does |
| --- | --- |
| `.github/workflows/kibot.yml` | Reusable workflow: KiBot in `kicad10_auto`, board page, uploads, summary |
| `.github/workflows/lint.yml` | Reusable workflow: actionlint on the calling repo's workflows |
| `.github/workflows/check.yml` | This repo's own CI: actionlint, unit tests, ruff and Prettier |
| `.github/workflows/pages.yml` | Reusable workflow, opt-in: publishes the `outputs` artifact to Pages |
| `actions/design-rules/` | Composite action: checks the board's `.kicad_dru` against kicad-common |
| `actions/kibot/` | Composite action: runs KiBot with the board config or the default |
| `actions/board-page/` | Composite action: writes the board page, `index.html`, into `outputs/` |
| `actions/report-summary/` | Composite action: KiCad ERC/DRC JSON to a Markdown summary |
| `justfile` | `just ci` and `just test`, see [Checks](#checks) |

Each run uploads two artifacts: `reports` (ERC and DRC as HTML and JSON) and `outputs`
(the PDFs, PNGs, the BOM and `index.html`). They and the job summary are only visible when
signed in to GitHub.

The outputs are made in CI. Locally, the board repos make the schematic and board PDF
with `kicad-cli` through `just pdf`, into `outputs/`. The content is the same, the look
is not: local PDFs use your own KiCad color theme and KiCad version, and your unpushed
changes.

## Checks

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

## Versions

Board repos call `@v1`. The tag moves after each tested change, so they get fixes
without editing their workflow. A change that needs edits in the board repos becomes
`v2`.

## Test a change before pushing

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
