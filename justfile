set shell := ["bash", "-euo", "pipefail", "-c"]

# List the recipes
default:
    @just --list

# Run kicad-ci's CI (check.yml) with act, one job at a time; -j <job> for one
ci *args:
    act push -W .github/workflows/check.yml --concurrent-jobs 1 {{ args }}

# Run the unit tests of both scripts and the CLI, without Docker
test:
    python3 -m unittest discover -s actions/board-page
    python3 -m unittest discover -s actions/report-summary
    python3 -m unittest discover -s cli/tests -t cli
