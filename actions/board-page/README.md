# Board page

Writes `index.html` into the KiBot outputs folder: the board's 3D renders and drawings,
with links to the PDFs, the interactive BOM and the BOM CSV, and above the title a link
back to the overview of all boards, <https://solar-cooker-uhasselt.github.io/>. The
page is always dark, in the interactive BOM's colours. Called by the reusable workflow
`.github/workflows/kibot.yml`, after KiBot.

| Input     | Default   | What it is                                             |
| --------- | --------- | ------------------------------------------------------ |
| `outputs` | `outputs` | Folder with the KiBot outputs, the page goes there too |

The page is [`template.html`](template.html), filled in by
[`board_page.py`](board_page.py). Its unit tests are `test_board_page.py`, run by
`just test` in the repo root. Publishing the page is the `pages.yml` workflow, see the
top README.
