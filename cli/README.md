# kicad-ci command line tool

Runs kicad-ci's KiCad checks on a board on your own machine. The GitHub actions in
[`../actions/`](../actions/) are what CI runs; this tool is the local side.

It only prints its version for now.

## Install

Needs Python 3.13 or newer and [uv](https://docs.astral.sh/uv/) or
[pipx](https://pipx.pypa.io/). Each installs the tool in its own environment and puts
the `kicad-ci` command on your `PATH`.

```bash
uv tool install "git+https://github.com/solar-cooker-UHasselt/kicad-ci@v1#subdirectory=cli"
# or
pipx install "git+https://github.com/solar-cooker-UHasselt/kicad-ci@v1#subdirectory=cli"
```

`@v1` is the same tag the boards' CI uses. After `v1` moves, reinstall to get the new
version: the same `uv tool install` line with `--reinstall`, or `pipx reinstall kicad-ci`.

## Use

```bash
kicad-ci --version
kicad-ci --help
```

## Develop

From the repo root:

```bash
pipx install --editable ./cli                         # kicad-ci runs this checkout
python3 -m unittest discover -s cli/tests -t cli      # or: just test
```
