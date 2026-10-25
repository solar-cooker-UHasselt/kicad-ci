# Release draft

Creates a draft release of a board order, titled `Order <tag>`, with the files it was
ordered from. Called by the reusable workflow `.github/workflows/release.yml`, after
the revision check and KiBot passed.

Five files are attached, each named with the tag:

- `<board>-v1.1.kicad_pcb` and `<board>-v1.1-bom.csv`, the files to order from
- `<board>-v1.1-ibom.html`, the interactive BOM, for assembly
- `<board>-v1.1-schematic.pdf` and `<board>-v1.1-board.pdf`

The draft's text is [`notes.md`](notes.md), with the commit filled in. The maintainer
fills in the order and the changes, and publishes the draft after ordering. The run
stops when a release or draft for the tag exists already: delete that one first to make
a new draft.

| Input     | Default        | What it is                                         |
| --------- | -------------- | -------------------------------------------------- |
| `tag`     | the pushed tag | The release tag, for example `v1.1`                |
| `outputs` | `outputs`      | Folder with the KiBot outputs                      |
| `token`   | `github.token` | Token that may create releases (`contents: write`) |

The script is [`draft.sh`](draft.sh).
