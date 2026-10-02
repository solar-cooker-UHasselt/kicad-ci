# kicad-ci command line tool

Compare a board's schematic and PCB between versions on your own machine, in the
same KiBot image as CI.

## Install

Needs Python 3.13+, [Docker](https://docs.docker.com/engine/install/) and
[uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/).

```bash
uv tool install "git+https://github.com/solar-cooker-UHasselt/kicad-ci@v1#subdirectory=cli"
# or
pipx install "git+https://github.com/solar-cooker-UHasselt/kicad-ci@v1#subdirectory=cli"
```

After `v1` moves, reinstall: `uv tool install --reinstall …` or `pipx reinstall kicad-ci`.

## Use

In a board's folder:

```bash
kicad-ci diff              # the board on disk against origin/main
kicad-ci diff v1.0         # against any commit, tag or branch
kicad-ci diff v1.0 v1.1    # two commits, tags or branches against each other
```

```console
$ kicad-ci diff
No changes in DS3231 against origin/main.

$ kicad-ci diff                       # after editing the PCB
Comparing DS3231 with origin/main (8812a9f) in KiBot...
...
Only the sheets and layers that changed:
  outputs/diff/DS3231-diff_sch.pdf
  outputs/diff/DS3231-diff_pcb.pdf
```

In the PDFs, green is added and red is removed. Uncommitted and unpushed changes count,
and your working tree is never touched. `kicad-ci diff --help` lists the options.

## Contributing

From the repo root:

```bash
pipx install --force --editable ./cli    # kicad-ci runs this checkout
just test
```
