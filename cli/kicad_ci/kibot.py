"""The KiBot image and configs the CLI runs, the same as kicad-ci's CI."""

from importlib.resources import files
from importlib.resources.abc import Traversable

# The image of .github/workflows/kibot.yml, so local runs use the same KiCad
# as CI. A test checks the two are equal, Renovate updates both in one PR.
IMAGE = "ghcr.io/inti-cmnb/kicad10_auto:1.9.1-1_k10.0.4_d13.2"


def config(name: str) -> Traversable:
    """Return the KiBot config shipped with the CLI, e.g. diff.kibot.yml."""
    return files("kicad_ci") / "configs" / name
