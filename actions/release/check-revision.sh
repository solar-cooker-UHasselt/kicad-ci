#!/bin/sh
# Check that a release tag matches the board revision.
#
# Usage: sh check-revision.sh <tag>, from the board repo's root. Example: v1.1.
#
# Tag v1.1 needs revision 1.1 in the three places KiCad keeps it: the schematic
# and board title blocks (File, Page Settings) and sch_revision in the .kicad_pro
# (Board Setup, used by the IPC-2581 export). Each place that differs is named.

tag="$1"
if [ -z "$tag" ]; then
  echo "Usage: sh check-revision.sh <tag>" >&2
  exit 2
fi
want="${tag#v}"

set -- *.kicad_pro
if [ "$#" -ne 1 ] || [ ! -e "$1" ]; then
  echo "::error::Expected one .kicad_pro in the repo root, found: $*"
  exit 1
fi
board="${1%.kicad_pro}"

# The first (rev "…") in a file is the one in its title block.
title_rev() {
  sed -n 's/^[[:space:]]*(rev "\(.*\)")$/\1/p' "$1" | head -n 1
}

failed=0
check() {
  file="$1"
  got="$2"
  if [ "$got" = "$want" ]; then
    echo "$file: revision $got"
  else
    echo "::error file=$file::$file has revision '${got}', tag $tag needs $want"
    failed=1
  fi
}

check "$board.kicad_sch" "$(title_rev "$board.kicad_sch")"
check "$board.kicad_pcb" "$(title_rev "$board.kicad_pcb")"
check "$board.kicad_pro" "$(sed -n 's/^[[:space:]]*"sch_revision": "\(.*\)",\{0,1\}$/\1/p' "$board.kicad_pro" | head -n 1)"

exit "$failed"
