# kicad-ci

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
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/kibot.yml@v1
```

No `config.kibot.yml` is needed. Without one, KiBot runs with
[`actions/kibot/default.kibot.yml`](actions/kibot/default.kibot.yml): ERC and DRC, a
schematic and board PDF, and PNGs of the top and bottom side (a PcbDraw drawing and a 3D
render each).

A board that needs more adds its own `config.kibot.yml` that imports the default:

```yaml
kibot:
  version: 1

import:
  - file: "@KICAD_CI_DEFAULT@"

outputs:
  - name: render-top
    type: render_3d
```

[kicad-adafruit-ds3231](https://github.com/solar-cooker-UHasselt/kicad-adafruit-ds3231)
is the reference repo.

## Publish the board page

Each run writes `index.html` next to the outputs: the 3D renders and drawings, with
links to the PDFs. A board can publish it on GitHub Pages, at
`https://solar-cooker-uhasselt.github.io/<repo>/`, so the images can be shown in its
README without committing them. Only pushes to `main` publish.

Opt-in, in two steps. Turn Pages on once, with GitHub Actions as its source:

```bash
gh api -X POST repos/solar-cooker-UHasselt/<repo>/pages -f build_type=workflow
```

Then add a second job to the board's `.github/workflows/kibot.yml`:

```yaml
  pages:
    needs: check
    permissions:
      pages: write
      id-token: write
    uses: solar-cooker-UHasselt/kicad-ci/.github/workflows/pages.yml@v1
```

A README shows an image with its full URL, for example
`https://solar-cooker-uhasselt.github.io/kicad-adafruit-ds3231/DS3231-render-top.png`.

## What is here

| Path | What it does |
| --- | --- |
| `.github/workflows/kibot.yml` | Reusable workflow: KiBot in `kicad10_auto`, board page, uploads, summary |
| `.github/workflows/check.yml` | This repo's own CI: actionlint, unit tests, ruff and Prettier |
| `.github/workflows/pages.yml` | Reusable workflow, opt-in: publishes the `outputs` artifact to Pages |
| `actions/kibot/` | Composite action: runs KiBot with the board config or the default |
| `actions/board-page/` | Composite action: writes the board page, `index.html`, into `outputs/` |
| `actions/report-summary/` | Composite action: KiCad ERC/DRC JSON to a Markdown summary |

Each run uploads two artifacts: `reports` (ERC and DRC as HTML and JSON) and `outputs`
(the PDFs, PNGs and `index.html`). They and the job summary are only visible when
signed in to GitHub.

The outputs are made in CI. Locally, the board repos make the schematic and board PDF
with `kicad-cli` through `just pdf`, into `outputs/`. The content is the same, the look
is not: local PDFs use your own KiCad color theme and KiCad version, and your unpushed
changes.

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
