# Project 10: Do Investors Follow Authority?

Market reactions to star analyst recommendations, China A-shares, 2018-2024.

FIN4080 Behavioral Finance group project, two-person group.

- **`Project10_Star_Analyst_Research_Plan_EN.md`** is the written plan: research
  question, event sample, authority variables, empirical design, robustness, and
  the limitations we disclose. A Word version sits beside it.
- **`README_pipeline.md`** documents the data pipeline, the cleaning funnel and the
  known data limitations. Start here for the data audit.
- **`data_dictionary.md`** documents every column of the analysis table.
- The `*.py` files are the pipeline, in the order listed in `README_pipeline.md`.

Raw data extracts are not in this repository: they are large and are covered by the
data vendor's terms. The pipeline rebuilds them from iFinD. Course materials and the
class sign-up sheet are likewise not redistributed here.

## Repository layout, and how the two of us work in it

**Keep this repository private.** It carries tables derived from iFinD data, which may
not be redistributed, so it must not be made public.

Tracked, because the other person needs it:

| Path | Who puts it there |
|---|---|
| The written plan, `README_pipeline.md`, `data_dictionary.md`, the pipeline scripts | the analyst side |
| `data/events_with_star.csv`, the analysis table | the analyst side, after each pipeline run |
| `data/market_panel*.csv`, `data/index_panel*.csv` | the market side |

Not tracked, on purpose:

- `data/ratings_*.csv`, 213 MB of raw iFinD extracts, and `data/ratings_2018_2024.xlsx`,
  77 MB. Both are large and are rebuilt by the pipeline, and the market side does not
  need them.
- Course materials and the class sign-up sheet.

**Market data size.** The full panel comes to about 4.6 million rows, which is close to
200 MB as a single CSV, and GitHub rejects files over 100 MB. Split it by year,
`market_panel_2018.csv` through `market_panel_2024.csv`, at roughly 30 MB each. The file
name has to match `market_panel*.csv`, otherwise `.gitignore` keeps it out.

**Working rhythm.** Pull before starting. The analyst side commits the analysis table
after each pipeline run and the market side adds panels under `data/`. Neither edits the
other's files, so the two never collide on the same file.
