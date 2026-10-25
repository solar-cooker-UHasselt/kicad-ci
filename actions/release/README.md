# Release revision

Checks that a release tag matches the board revision, before a draft release is made.
Called by the reusable workflow `.github/workflows/release.yml`, first.

Tag `v1.1` needs revision `1.1` in the three places KiCad keeps it: the schematic and
board title blocks (File, Page Settings) and `sch_revision` in the `.kicad_pro` (Board
Setup). The job fails naming each place that differs.

| Input | Default        | What it is                          |
| ----- | -------------- | ----------------------------------- |
| `tag` | the pushed tag | The release tag, for example `v1.1` |

The script is [`check-revision.sh`](check-revision.sh). Run it from a board's root,
`sh check-revision.sh v1.1`, to check before tagging.
