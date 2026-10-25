# Design rules

Checks that the board's `<board>.kicad_dru` is a current copy of a rule set in
`kicad-common/design-rules/`, before KiBot runs. Called by the reusable workflow
`.github/workflows/kibot.yml`. No inputs.

KiCad only reads the `.kicad_dru` next to the `.kicad_pro`, so a board keeps a copy,
made by `just rules`. The check passes when the copy matches one of the rule sets, and
the job summary names it.

A copy that matches none fails the job with "out of date, run: just rules", for
example after a kicad-common update, and ERC and DRC do not run. A board without a
`.kicad_dru` is skipped, and the summary says only the board setup minimums apply.

The script is [`check.sh`](check.sh). Run it from a board's root to check locally.
