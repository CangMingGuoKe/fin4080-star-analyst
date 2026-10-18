# Project 10: Do Investors Follow Authority?

Market reactions to star analyst recommendations, China A-shares, 2018-2024.

FIN4080 Behavioral Finance group project, two-person group.

- **`Project10_Star_Analyst_Research_Plan_EN.md`** is the written plan: research
  question, event sample, authority variables, empirical design, robustness, and
  the limitations we disclose. A Word version sits beside it.
- **`文档/data_pipeline.md`** documents the data pipeline, the cleaning funnel and the
  known data limitations. Start here for the data audit.
- **`文档/data_dictionary.md`** documents every column of the analysis table.
- The pipeline scripts run in the order listed in `data_pipeline.md`; document-build
  and repair tools are listed separately in the code table below.

Raw data extracts are not in this repository: they are large and are covered by the
data vendor's terms. The pipeline rebuilds them from iFinD. Course materials and the
class sign-up sheet are likewise not redistributed here.

## Where the project stands

The project asks whether investors follow star analyst recommendations because
stars are more accurate (the information explanation) or because investors defer
to their status (the influence explanation). The event sample and the authority
variables are built, the market panel has arrived, and the first-pass results for
all four assigned questions are in.

1. **Announcement day.** Star upgrades draw a larger market-adjusted reaction and
   more abnormal volume than non-star upgrades (CAR[-1,+1] +0.38 pp, t=2.19;
   abnormal volume +0.053, t=2.85; both hold when events are collapsed to
   stock-day). Star downgrades show no such difference.
2. **After the announcement.** Star downgraded stocks underperform non-star ones by
   1.6 pp over the next 60 trading days (p=0.002), but the difference disappears by
   120 days and reverses sign by 250 days. Star upgrades show no differential drift.
3. **Ex post accuracy, holding returns.** Star recommendations are modestly more
   profitable to follow at short horizons (downgrades at 3 months, upgrades at
   6 months), but the advantage is gone by 12 months.
4. **Ex post accuracy, earnings forecasts.** Star analysts' absolute EPS forecast
   errors are larger, not smaller: FY0 upgrades 2.18 versus 1.89 percentage points
   of price (p=0.001), FY0 downgrades 3.07 versus 2.61 (p=0.002), with larger gaps
   at FY1. Signed errors, which measure optimism, do not differ.

Read together, stars move prices and are modestly more profitable to follow at short
horizons, but their earnings forecasts are not more accurate. The evidence is closer
to the influence explanation, although it does not rule out an information component.

5. **Asymmetry and broker tier.** Formal interaction models with stock-clustered
   standard errors show that the star premium differs between upgrades and
   downgrades at CAR[-1,+5] (p=0.023) and abnormal volume (p=0.041). The upgrade
   premium is concentrated in top-tier brokers; the top-versus-mid difference is
   marginal (p=0.070) rather than significant at 5%. The small-tier group has almost
   no star events (2 upgrades, 0 downgrades), so it cannot be estimated.

**The one-sentence story.** Stars move the market, but the evidence does not show that
they are better forecasters; the pattern fits influence better than information.

**What remains before 27 October.** Clustered standard errors; limit-hit, suspension
and ST robustness; the three main figures; and a decision on whether to extend the FY1
forecast-error sample beyond 2023. These are univariate first-pass results, so the
significance levels should not be quoted as final until the clustering is done.

## Repository layout and file ownership

**Keep this repository private.** It carries tables derived from iFinD data, which may
not be redistributed, so it must not be made public.

Tracked, because the other person needs it:

| Path | Owner |
|---|---|
| The written plan, `data_pipeline.md`, `data_dictionary.md`, the pipeline scripts | the analyst side |
| `data/analysis_table.csv`, the analysis table | the analyst side, after each pipeline run |
| `data/market_panel*.csv`, `data/index_panel*.csv` | the market side |

Not tracked, on purpose:

- `data/raw_ratings_*.csv`, 213 MB of raw iFinD extracts. Large and rebuilt by the
  pipeline, and the market side does not need them. `make_excel_workbook.py` can fold
  them into one seven-sheet workbook on demand; that workbook is not kept on disk.
- Course materials and the class sign-up sheet.

**Market data size.** The full panel comes to about 4.6 million rows, which is close to
200 MB as a single CSV, and GitHub rejects files over 100 MB. Split it by year,
`market_panel_2018.csv` through `market_panel_2024.csv`, at roughly 30 MB each. The file
name has to match `market_panel*.csv`, otherwise `.gitignore` keeps it out. The unsplit
panel, `data/market_panel.csv`, stays local: it is about 659 MB, above the 100 MB limit.

**Working rhythm.** Pull before starting. The analyst side commits the analysis table
after each pipeline run and the market side adds panels under `data/`. Neither edits the
other's files, so the two never collide on the same file.
## What each file is

Documents sit in `文档/`, course materials in `课程材料/`. Everything else, including all
scripts and the `data/` directory, is in the repository root.

**Documents**

| File | What it is |
|---|---|
| `文档/Project10_Star_Analyst_Research_Plan_EN.md` and its `.docx` | the written plan, this is the graded deliverable |
| `文档/Project10_明星分析师_研究方案.md` and its `.docx` | the same plan in Chinese, a working record; the English one governs |
| `文档/data_pipeline.md` | the data pipeline, the cleaning funnel and the data limitations |
| `文档/data_dictionary.md` | every column of the analysis table |
| `文档/行情数据交付说明.md` | the market data spec: what the panel must contain, and the API traps already found (internal hand-off note) |
| `文档/event_study_核查记录_20261007.md` | the event-study script review (internal review record) |
| `文档/event_study_核查回应_20261011.md` | the written reply to the event-study review (internal record) |
| `文档/项目进度与技术备忘_20261018.md` and its `.docx` | a running recap of progress, decisions and technical notes, in Chinese (internal working record) |

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
| `event_study.py`, `event_study_v2.py` | CAR and abnormal volume; run v2, the original stays as the reviewed record |
| `accuracy_test.py` | 3/6/12-month direction-adjusted returns and hit rates after each event |
| `pull_forecast.py` | pulls analyst-level EPS forecasts and realised annual EPS from iFinD |
| `forecast_error.py` | matches each event's own EPS forecast to realised EPS and tests star versus non-star |
| `heterogeneity_test.py` | interaction models for direction and broker tier, with stock-clustered errors |
| `heterogeneity_rolling.py` | rebuilds the tier from prior years only and re-estimates the same interactions |
| `ifind_probe.py` | one-off, checks that the iFinD account can reach the API |
| `make_excel_workbook.py` | builds the seven-sheet workbook of the raw extracts |
| `make_coverage_table.py` | builds the New Fortune coverage table, `data/ref_newfortune_coverage.xlsx` |
| `repair_encoding.py` | audits the `data/` CSVs for GBK damage and restores them from git or `../Project.zip` |
| `md2docx.py`, `refresh_toc.ps1` | build the Word version and fill in its contents page |

**Data, all under `data/`**

| File | What it is | In the repository |
|---|---|---|
| `raw_ratings_2018.csv` through `raw_ratings_2024.csv` | raw iFinD extracts, untouched | no, local only |
| `ref_newfortune_list.csv` | the scraped list, every year the source serves | yes, tracked for reproducibility |
| `ref_listing_dates.csv`, `ref_analyst_tenure.csv` | the reference tables from pipeline steps 4 and 5 | yes, tracked for reproducibility |
| `events_1_all_revisions.csv`, `events_2_clean_sample.csv`, `events_3_initiations.csv` | intermediate event tables | no, local only |
| `analysis_table.csv` | **the analysis table**, 20,980 rows by 32 columns | yes |
| `ref_newfortune_roster_2018_2024.csv` | the New Fortune roster 2018-2024, each ranked analyst with seniority and broker tier | yes |
| `ref_newfortune_missing_tenure.csv` | New Fortune ranked analysts with no seniority record, 630 names | yes |
| `ref_newfortune_coverage.xlsx` | every ranked analyst name, with which ones the sample can use and why the rest cannot | yes |
| `market_panel_YYYY.csv`, `index_panel.csv` | the market data, split by year for sharing | yes |
| `market_panel.csv` | the unsplit panel, about 659 MB | no, local only |
| `raw_pull_manifest.json` | the wording and row count of every iFinD query | yes, tracked for reproducibility |
| `car_summary.csv`, `car_event_level.csv` | event-study output: window summary and one row per event | yes |
| `accuracy_summary.csv` | post-recommendation accuracy by horizon and direction | yes |
| `raw_forecast_2018.csv` through `raw_forecast_2024.csv` | analyst-level EPS forecasts, 528,477 rows | no, local only |
| `ref_actual_eps.csv` | realised annual basic EPS, 2018-2024 | yes |
| `forecast_error_event.csv`, `forecast_error_summary.csv` | earnings forecast error, event level and summary | yes |
| `forecast_pull_manifest.json` | query wording and row counts for the forecast pull | yes |
| `heterogeneity_summary.csv` | direction and tier interaction estimates | yes |
| `broker_tier_rolling.csv`, `heterogeneity_rolling_summary.csv` | backward-looking tier assignment and the re-estimated interactions | yes |

**In the folder but deliberately not in the repository**: the instructor's handouts
them all sit in `课程材料/` (`Topic details.pdf`, `FIN4080_CSMAR.pdf`, `FIN4080_TA_Data.pdf`,
`FIN4080_demo_project.pdf`, `Coding_For_Momentum_4080.pdf`) together with the class sign-up
sheet, `FIN 4080 Group and topic sign up.xlsx`, which carries the whole class's names. They stay on disk and are ignored by git.

**Do not save these files from Excel or WPS.** Opening them is fine; saving rewrites the
encoding to GBK and reformats dates and numbers, so `2018-01-01` becomes `2018/1/1` and
`84.0` becomes `84`. Every script that reads them then fails. This happened on 2026-10-06
to `analysis_table.csv` and `ref_analyst_tenure.csv`; both were restored, a re-run
reproduced the committed table byte for byte, and no data was lost.

If it happens anyway, `python repair_encoding.py` audits every file in `data/` and
restores the affected ones from git or from `../Project.zip`, backing up the originals
first. `python repair_encoding.py --check` only reports.

