# KiCad report summary

Turns KiCad's ERC and DRC JSON reports into the run's Markdown job summary. Called by
the reusable workflow `.github/workflows/kibot.yml`, also when KiBot failed.

The summary has a status line, a table of errors, warnings and exclusions per check,
the first 25 errors one by one (the rest counted), the warnings counted per type, and
links to the `reports` and `outputs` artifacts. Violations excluded in KiCad are
counted apart and never fail the run. A missing report shows as "not run".

| Input         | Default   | What it is                                            |
| ------------- | --------- | ----------------------------------------------------- |
| `reports`     | `reports` | Folder with `<board>-erc.json` and `<board>-drc.json` |
| `reports-url` | empty     | Link to the reports artifact, at the end              |
| `outputs-url` | empty     | Link to the outputs artifact, at the end              |

The script is [`report_summary.py`](report_summary.py), its unit tests
`test_report_summary.py`, run by `just test` in the repo root.
