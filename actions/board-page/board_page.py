"""Write index.html, a page that shows a board's KiBot outputs.

Usage: python3 board_page.py <outputs dir>

The page shows the 3D renders and drawings of the default KiBot config
and links its PDFs. Outputs that are missing are left out. A folder with
none of them gets no page. When GITHUB_REPOSITORY and GITHUB_SHA are
set, as in GitHub Actions, the page links the commit it was built from.
"""

import argparse
import html
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from string import Template

TEMPLATE = Path(__file__).with_name("template.html")
PAGE_NAME = "index.html"


@dataclass(frozen=True)
class Output:
    """An output file of the default KiBot config: <board>-<suffix>."""

    suffix: str
    label: str

    def file_name(self, board: str) -> str:
        """Return this output's file name for board."""
        return f"{board}-{self.suffix}"


# In page order. The suffixes match the outputs in default.kibot.yml.
IMAGES = (
    Output("render-top.png", "Top, 3D render"),
    Output("render-bottom.png", "Bottom, 3D render"),
    Output("pcbdraw-top.png", "Top, drawing"),
    Output("pcbdraw-bottom.png", "Bottom, drawing"),
)
DOCUMENTS = (
    Output("schematic.pdf", "Schematic (PDF)"),
    Output("board.pdf", "Board layers (PDF)"),
)


@dataclass(frozen=True)
class Source:
    """The GitHub repository and commit a page was built from."""

    repo: str
    sha: str

    @property
    def repo_url(self) -> str:
        """Return the repository's GitHub URL."""
        return f"https://github.com/{self.repo}"

    @property
    def commit_url(self) -> str:
        """Return the commit's GitHub URL."""
        return f"{self.repo_url}/commit/{self.sha}"


def source_from_env(env: Mapping[str, str]) -> Source | None:
    """Return the source GitHub Actions describes in env, if any."""
    repo = env.get("GITHUB_REPOSITORY")
    sha = env.get("GITHUB_SHA")
    if repo and sha:
        return Source(repo, sha)
    return None


def find_board(folder: Path) -> str | None:
    """Return the board name of the first known output in folder."""
    for output in IMAGES + DOCUMENTS:
        matches = sorted(folder.glob(f"*-{output.suffix}"))
        if matches:
            return matches[0].name.removesuffix(f"-{output.suffix}")
    return None


def present(
    folder: Path, board: str, outputs: Sequence[Output]
) -> list[Output]:
    """Return the outputs whose file exists in folder, in order."""
    return [o for o in outputs if (folder / o.file_name(board)).is_file()]


def new_tab_link(href: str, content: str) -> str:
    """Return a link that opens in a new tab. content is HTML."""
    return (
        f'<a href="{html.escape(href)}" target="_blank" rel="noopener">'
        f"{content}</a>"
    )


def render_source(source: Source | None) -> str:
    """Return the line under the title: the commit, or a local build."""
    if source is None:
        return "Local build"
    short_sha = html.escape(source.sha[:7])
    return f"Built from {new_tab_link(source.commit_url, short_sha)}"


def render_links(
    board: str, documents: Sequence[Output], source: Source | None
) -> str:
    """Return the list items: the documents, then the repository."""
    links = [
        new_tab_link(d.file_name(board), html.escape(d.label))
        for d in documents
    ]
    if source is not None:
        links.append(new_tab_link(source.repo_url, "Source on GitHub"))
    return "\n".join(f"<li>{link}</li>" for link in links)


def render_figure(board: str, image: Output) -> str:
    """Return a captioned image that opens full size in a new tab."""
    name = image.file_name(board)
    alt = html.escape(f"{board}, {image.label.lower()}")
    img = f'<img src="{html.escape(name)}" alt="{alt}">'
    caption = html.escape(image.label)
    return (
        f"<figure>{new_tab_link(name, img)}"
        f"<figcaption>{caption}</figcaption></figure>"
    )


def render_page(
    board: str,
    images: Sequence[Output],
    documents: Sequence[Output],
    source: Source | None,
) -> str:
    """Return the page HTML: TEMPLATE filled in for this board."""
    template = Template(TEMPLATE.read_text(encoding="utf-8"))
    return template.substitute(
        title=html.escape(board),
        source=render_source(source),
        links=render_links(board, documents, source),
        figures="\n".join(render_figure(board, i) for i in images),
    )


def write_page(folder: Path, source: Source | None) -> Path | None:
    """Write the page into folder. Return its path, None if not written."""
    board = find_board(folder)
    if board is None:
        return None
    page = render_page(
        board,
        present(folder, board, IMAGES),
        present(folder, board, DOCUMENTS),
        source,
    )
    path = folder / PAGE_NAME
    path.write_text(page, encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    """Write the page for the folder named on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "outputs", type=Path, help="folder with the KiBot outputs"
    )
    args = parser.parse_args(argv)
    if not args.outputs.is_dir():
        parser.error(f"not a folder: {args.outputs}")

    path = write_page(args.outputs, source_from_env(os.environ))
    if path is None:
        print(f"No known outputs in {args.outputs}, no page written")
    else:
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
