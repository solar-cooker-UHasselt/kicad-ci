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

## What is here

| Path | What it does |
| --- | --- |
| `.github/workflows/kibot.yml` | Reusable workflow: KiBot in `kicad10_auto`, uploads, summary |
| `actions/kibot/` | Composite action: runs KiBot with the board config or the default |
| `actions/report-summary/` | Composite action: KiCad ERC/DRC JSON to a Markdown summary |

Each run uploads two artifacts: `reports` (ERC and DRC as HTML and JSON) and `outputs`
(the PDFs and PNGs). They and the job summary are only visible when signed in to GitHub.

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
