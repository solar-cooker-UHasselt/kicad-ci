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

`config.kibot.yml` at the repo root:

```yaml
kibot:
  version: 1

preflight:
  check_zone_fills: true
  erc:
    format: JSON,HTML
    dir: reports
  drc:
    format: JSON,HTML
    dir: reports
```

[kicad-adafruit-ds3231](https://github.com/solar-cooker-UHasselt/kicad-adafruit-ds3231)
is the reference repo.

## What is here

| Path | What it does |
| --- | --- |
| `.github/workflows/kibot.yml` | Reusable workflow: KiBot in `kicad10_auto`, upload, summary |
| `actions/report-summary/` | Composite action: KiCad ERC/DRC JSON to a Markdown summary |

The job summary and the `reports` artifact are only visible when signed in to GitHub.

## Versions

Board repos call `@v1`. The tag moves after each tested change, so they get fixes
without editing their workflow. A change that needs edits in the board repos becomes
`v2`.
