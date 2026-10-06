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
| `data/analysis_table.csv`, the analysis table | the analyst side, after each pipeline run |
| `data/market_panel*.csv`, `data/index_panel*.csv` | the market side |

Not tracked, on purpose:

- `data/raw_ratings_*.csv`, 213 MB of raw iFinD extracts, and `data/raw_ratings_workbook.xlsx`,
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
## What each file is

**Documents**

| File | What it is |
|---|---|
| `Project10_Star_Analyst_Research_Plan_EN.md` and its `.docx` | the written plan, this is the graded deliverable |
| `Project10_明星分析师_研究方案.md` and its `.docx` | the same plan in Chinese, a working record; the English one governs |
| `README_pipeline.md` | the data pipeline, the cleaning funnel and the data limitations |
| `data_dictionary.md` | every column of the analysis table |
| `给乙_行情数据交付说明.md` | what the market side delivers, and the API traps already found |

**Code**

| File | What it does |
|---|---|
| `pull_ifind_ratings.py` | pulls the annual analyst rating detail from iFinD |
| `pull_newfortune_list.py` | scrapes the New Fortune best-analyst list |
| `pull_listing_dates.py` | pulls listing dates for the A-share and Beijing exchange universe |
| `pull_analyst_tenure.py` | pulls each analyst's first report date |
| `clean_event_table.py` | the cleaning funnel that builds the event sample |
| `build_star_variable.py` | the star indicator and its timing variants |
| `build_broker_tier.py` | the broker tier |
| `broker_names.py` | the shared broker identity map used by the two scripts above |
| `event_study.py` | CAR and abnormal volume, once the market data arrives |
| `ifind_probe.py` | one-off, checks that the iFinD account can reach the API |
| `make_excel_workbook.py` | builds the seven-sheet workbook of the raw extracts |
| `md2docx.py`, `refresh_toc.ps1` | build the Word version and fill in its contents page |

**Data, all under `data/`**

| File | What it is | In the repository |
|---|---|---|
| `raw_ratings_2018.csv` through `raw_ratings_2024.csv` | raw iFinD extracts, untouched | no, local only |
| `raw_ratings_workbook.xlsx` | the same extracts as one workbook with seven sheets | no, local only |
| `ref_newfortune_list.csv` | the scraped list, every year the source serves | no, local only |
| `ref_listing_dates.csv`, `ref_analyst_tenure.csv` | the reference tables from pipeline steps 4 and 5 | no, local only |
| `events_1_all_revisions.csv`, `events_2_clean_sample.csv`, `events_3_initiations.csv` | intermediate event tables | no, local only |
| `analysis_table.csv` | **the analysis table**, 20,980 rows by 32 columns | yes |
| `handover_newfortune_missing_tenure.csv` | the market side's cross-check: ranked analysts with no seniority record | yes |
| `market_panel*.csv`, `index_panel*.csv` | the market data, still to arrive | yes, once added |
| `raw_pull_manifest.json` | the wording and row count of every iFinD query | no, local only |

**In the folder but deliberately not in the repository**: the instructor's handouts
(`Topic details.pdf`, `FIN4080_CSMAR.pdf`, `FIN4080_TA_Data.pdf`, `FIN4080_demo_project.pdf`,
`Coding_For_Momentum_4080.pdf`) and the class sign-up sheet, `FIN 4080 Group and topic sign
up.xlsx`, which carries the whole class's names. They stay on disk and are ignored by git.

**Do not save these files from Excel or WPS.** Opening them is fine; saving rewrites the
encoding to GBK and reformats dates and numbers, so `2018-01-01` becomes `2018/1/1` and
`84.0` becomes `84`. Every script that reads them then fails. This happened on 2026-10-06
to `analysis_table.csv` and `ref_analyst_tenure.csv`; both were restored, a re-run
reproduced the committed table byte for byte, and no data was lost.

If it happens anyway, `python repair_encoding.py` audits every file in `data/` and
restores the affected ones from git or from `Project.zip`, backing up the originals
first. `python repair_encoding.py --check` only reports.

