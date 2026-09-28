#!/bin/sh
# Check that the board's .kicad_dru is a current copy of a rule set in kicad-common.
#
# Usage: sh check.sh, from the board repo's root.
#
# A board keeps a copy of kicad-common/design-rules/<rules>.kicad_dru, made by
# `just rules`. KiCad only reads <board>.kicad_dru, so the copy is what DRC uses.
# A board without one is skipped, so boards not yet migrated keep passing.
# Each outcome also writes one line to the job summary, before ERC and DRC.
# Outside GitHub Actions there is no summary, and that line is dropped.

summary() {
  printf '**Design rules:** %s\n\n' "$1" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
}

set -- *.kicad_dru
if [ ! -e "$1" ]; then
  echo "::notice::No .kicad_dru, the design rules check is skipped"
  summary "no \`.kicad_dru\`, only the board setup minimums apply"
  exit 0
fi

for dru in "$@"; do
  match=""
  for src in kicad-common/design-rules/*.kicad_dru; do
    if cmp -s "$dru" "$src"; then
      match="$src"
      break
    fi
  done
  if [ -z "$match" ]; then
    echo "::error file=$dru::$dru is out of date, run: just rules"
    summary "\`$dru\` is out of date, run \`just rules\` and commit it. ERC and DRC did not run."
    exit 1
  fi
  echo "$dru matches $match"
  summary "\`$dru\` matches \`$(basename "$match" .kicad_dru)\` from kicad-common"
done
