#!/bin/sh
# Create a draft release of a board order, with the files to order attached.
#
# Usage: sh draft.sh <tag> <outputs dir>, from the board repo's root, with gh
# installed and GH_TOKEN set. Example: sh draft.sh v1.1 outputs
#
# Attaches the board file and four KiBot outputs, the tag in each name:
# DS3231-v1.1.kicad_pcb, -bom.csv, -ibom.html, -schematic.pdf, -board.pdf.
# The text is notes.md: the maintainer fills in the order and publishes the draft.

tag="$1"
outputs="$2"
if [ -z "$tag" ] || [ -z "$outputs" ]; then
  echo "Usage: sh draft.sh <tag> <outputs dir>" >&2
  exit 2
fi

set -- *.kicad_pro
if [ "$#" -ne 1 ] || [ ! -e "$1" ]; then
  echo "::error::Expected one .kicad_pro in the repo root, found: $*"
  exit 1
fi
board="${1%.kicad_pro}"

# GitHub allows several drafts on one tag, so a rerun would add a second one
existing=$(gh release list --json tagName --jq ".[] | select(.tagName == \"$tag\")") || exit 1
if [ -n "$existing" ]; then
  echo "::error::A release or draft for $tag already exists, delete it first to make a new one"
  exit 1
fi

# The files under their release names, in a folder of their own
dist=$(mktemp -d)
attach() {
  if [ ! -f "$1" ]; then
    echo "::error::$1 is missing, no release made"
    exit 1
  fi
  cp "$1" "$dist/$2"
}
attach "$board.kicad_pcb" "$board-$tag.kicad_pcb"
for suffix in bom.csv ibom.html schematic.pdf board.pdf; do
  attach "$outputs/$board-$suffix" "$board-$tag-$suffix"
done

# The text from notes.md, next to this script, with the commit filled in
sha="${GITHUB_SHA:-$(git rev-parse HEAD)}"
short=$(printf '%.7s' "$sha")
commit="https://github.com/${GITHUB_REPOSITORY}/commit/$sha"
notes="$dist.md"
sed -e "s|{short}|$short|g" -e "s|{commit}|$commit|g" \
  "$(dirname "$0")/notes.md" > "$notes"

url=$(gh release create "$tag" "$dist"/* --draft --verify-tag \
  --title "Order $tag" --notes-file "$notes") || exit 1
echo "Draft release: $url"
printf '**Draft release:** [Order %s](%s), fill in the order and publish it\n' \
  "$tag" "$url" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
