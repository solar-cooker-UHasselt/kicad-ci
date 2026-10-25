# KiBot

Runs KiBot in the board repo, with the board's own `config.kibot.yml`, or
[`default.kibot.yml`](default.kibot.yml) when there is none. Called by the reusable
workflow `.github/workflows/kibot.yml`, inside the KiBot image. No inputs.

## The default config

ERC and DRC, a schematic and board PDF, PNGs of the top and bottom side (a PcbDraw
drawing and a 3D render each, with a transparent background), a bill of materials as
CSV with the Eurocircuits columns (Reference, Qty, Manufacturer, MPN, Supplier, SPN,
Component package type, Description), sorted by supplier, and an interactive BOM. The
CSV holds only the table, with semicolons between the columns and every field quoted,
so it uploads to Eurocircuits as it is. The interactive BOM
([InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom)) is one
HTML file: click a row and its parts light up on the board, for hand soldering.

## A board's own config

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
and `ibom`, so a board's own output needs a new name. KiBot stops with "Output
name … already defined" otherwise. To replace a default output, import the others by
name and define it again:

```yaml
import:
  - file: "@KICAD_CI_DEFAULT@"
    outputs: [schematic-pdf, board-pdf, pcbdraw-top, pcbdraw-bottom, render-bottom, bom-csv, ibom]

outputs:
  - name: render-top
    type: render_3d
```

The preflights (ERC and DRC) are still imported.

## The KiBot image

KiBot runs in a Docker image, `ghcr.io/inti-cmnb/kicad10_auto`, not in the
`INTI-CMNB/KiBot` action, whose pinned tags lag behind the images. The tag is pinned:
`1.9.1-1_k10.0.4_d13.2` is KiBot 1.9.1 build 1, KiCad 10.0.4, Debian 13.2, and always
the same image, while a tag like `1.9.1` changes with every rebuild. So a run today and
in a year use the same tools, and a newer KiCad only arrives when the tag changes.

The tag is set in the container of `.github/workflows/kibot.yml` and in
`cli/kicad_ci/kibot.py`. Renovate updates both. Newer tags are listed on the
[image's package page](https://github.com/INTI-CMNB/kicad_auto/pkgs/container/kicad10_auto).

`kicad10_auto` is enough for everything above. `kicad10_auto_full` adds Blender and
LaTeX, for Blender renders and PDF reports, and is much larger.
