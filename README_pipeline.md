# FIN4080 Project 10: Data Pipeline README

**Topic (sign-up sheet Topic 15 / Project Bank Project 10):**
Do Investors Follow Authority? Market Reactions to Star Analyst Recommendations

**Group size:** 2. **Presentation:** 27 October 2026, 15 min + 5 min Q&A.

This README documents the data pipeline used to build the event sample and the
authority variables. It is written for the group and for the TA's data audit.

---

## 1. Data source

All analyst data comes from **iFinD (同花顺)**, queried through the natural-language
interface (`THS_iwencai`, the "问财" endpoint of the `iFinDPy` package).

- The iFinD **terminal must be running and logged in** before any script is executed.
- Credentials are read from `C:\Users\59330\.ifind_secret` (two lines: account, password).
  If that file is absent, the scripts prompt for them interactively. Passwords are
  never printed or written to any output file.
- CSMAR and Wind are **not used**. On this campus they are available only on the
  TA209 lab machines, with no personal account, no remote access and no API.

## 2. Environment

```
pip install pandas requests lxml statsmodels seaborn
```

`iFinDPy` must already be installed and the iFinD terminal must be open.

## 3. Pipeline: run in this order

| # | Script | Input | Output |
|---|--------|-------|--------|
| 1 | `ifind_probe.py` | n/a | none. Run once to verify the account can reach the API; not needed on a normal re-run. |
| 2 | `pull_ifind_ratings.py` | iFinD | `data/raw_ratings_2018.csv` … `data/raw_ratings_2024.csv`, `data/raw_pull_manifest.json` |
| 3 | `pull_newfortune_list.py` | hibor.org | `data/ref_newfortune_list.csv` |
| 4 | `pull_listing_dates.py` | iFinD | `data/ref_listing_dates.csv` (A-share plus Beijing exchange; the A-share universe alone omits the BSE) |
| 5 | `pull_analyst_tenure.py` | iFinD | `data/ref_analyst_tenure.csv` (each analyst's first report date, back to the 2009 data floor) |
| 6 | `clean_event_table.py` | steps 2, 4, 5 | `data/events_1_all_revisions.csv`, `data/events_2_clean_sample.csv`, `data/events_3_initiations.csv` |
| 7 | `build_star_variable.py` | steps 3, 6 | `data/analysis_table.csv` |
| 8 | `build_broker_tier.py` | step 7 | updates `data/analysis_table.csv` (adds `券商层级`) |
| 9 | `event_study.py` | step 8 + market data | `data/car_event_level.csv`, `data/car_summary.csv` |

Step 9 is **blocked**: it needs `data/market_panel.csv` and `data/index_panel.csv`
from the teammate responsible for market data. The required format is specified in
the docstring of `event_study.py`.

**`broker_names.py` is a shared module, not a pipeline step.** Steps 7 and 8 both have to
decide whether two broker names denote the same firm, so the mapping lives in one file
rather than in each script. Item 6 of section 6 explains why this matters.

**About `data/ref_newfortune_list.csv`.** This file is the scrape of the public
source, one analyst per row, and it keeps every year the source serves, including
rows that are not usable. Two kinds of row carry `是否有效 = False`: the whole of
2018 (the page labelled 2018 is a compilation of anniversary special awards, not
an annual industry ranking) and the institution-level or individual honorary
categories (best research team, platinum analyst, diamond analyst and similar),
which have no industry rank at all. The 41 rows with an empty `名次` are all of the
second kind, so the blank is correct rather than missing data. `build_star_variable.py`
drops both kinds before building the star indicator, and for 2018 events it looks up
the 2017 list instead.

## 4. Event sample construction

Unit of observation: one **analyst recommendation revision** (a rating change by the
same analyst for the same stock). Source column `评级调整方向` takes values
`调高` / `调低` / `维持`; only the first two are events.

Cleaning funnel (printed by `clean_event_table.py` and reproducible):

| Step | Rows remaining | Removed |
|------|---------------|---------|
| Raw analyst rating records | 520,567 | |
| Exact duplicates removed | 517,871 | 2,696 |
| Keep rating revisions only | 21,471 | 496,400 |
| Drop first 6 months after IPO | 21,310 | 161 |
| Drop currently ST / \*ST | 20,980 | 330 |

Final sample: **20,980 events** covering 2,683 stocks, 2,171 analysts and
108 broker short names (107 distinct legal names), 2018-2024.

Initiation records, that is recommendations with no previous rating, are a separate
category and are **not** part of the funnel above. iFinD labels them `未知` rather
than as an upgrade or downgrade, so they never reach the event sample. The 42,276 of
them (after de-duplication) are saved separately in `data/events_3_initiations.csv`.

## 5. Authority variables

Three proxies for analyst authority, all stored as columns on `analysis_table.csv`:

| Variable | Definition | Source |
|----------|-----------|--------|
| `star` | 1 if the analyst appears in the New Fortune Best Analyst list for that year | external list |
| `资历` | years from the first report by the analyst to the event date, back to the June 2009 source floor | own data |
| `券商层级` | 头部 / 中部 / 中小: 13 / 27 / 91 houses, cut on the cumulative share of rating records | own data |

`star` is defined for all 20,980 events; 2,772 of them (13.2%) are `star = 1`.
The per-year star share is stable: 13.4%, 14.5%, 13.5%, 13.6%, 13.6%, 11.8%, 11.6%
for 2018-2024. Alternative timing conventions are kept as separate columns
(`star_same`, `star_month`, `star_lag1`) for robustness; the default reported in
`star` is `star_inforce`, defined in section 6.

## 6. Known data limitations (must go into the report)

1. **The New Fortune list labelled 2018 is not a valid annual industry ranking.**
   The 2018 vote was suspended after a scandal, and the page labelled 2018 is a
   compilation of anniversary special awards. Evidence: 36% of its names appear in
   no other year (versus 8-23% for other years), its name overlap with 2019 is
   Jaccard 0.10 (versus 0.40-0.52 for adjacent pairs), and it matches the rating
   data at only 3.6% versus 10-17% for every other list-year. It is the weakest
   column in the whole event-year × list-year match matrix.
   It is therefore **excluded from the star definition**, and 2018 events inherit the
   **2017** list, which is the most recent list actually in force during 2018. This
   is the same "list in force" rule applied to every year (`star_inforce`), so no
   special-casing and no look-ahead are involved. The rule restores 2018 to the
   normal range: 2018 events match the 2017 list at 13.4%, in line with the
   11.6%-14.5% observed for the other years, so the full 2018-2024 sample is usable.
   This spell without an annual list is itself usable as a discontinuity test.
2. **CICC (中金公司) has no records at all** in the iFinD rating detail, so its
   analysts can never be matched. Data gap, not a coding error.
3. **Historical ST status is not obtainable** from iFinD: every phrasing returns the
   current snapshot. The ST filter above is an approximation. The clean solution is
   to infer ST spells from daily price limits (ST stocks have a 5% band) using the
   market data.
4. **`资历` is censored at the source floor.** The analyst rating detail begins in June
   2009, so the 18.8% of analysts whose first report sits at that boundary cannot be
   ranked against one another, and December 2012 is missing. Neither can be closed from
   this source. Measured as years from the first report by the analyst, its correlation
   with the event year is 0.130, so year fixed effects remain advisable.
5. **Rating revisions are heavily buy-skewed**: 12,131 upgrades against 8,849
   downgrades over 2018-2024, consistent with the known optimism bias in sell-side
   ratings. Upgrades and downgrades should therefore be reported separately rather
   than pooled.
6. **A broker short name is not a unique identifier in the raw data, and the authority
   variables have to agree on how to treat that.** The same firm appears under several
   names: 中信建投 and 中信建投证券 (10,266 and 4,512 records), 中国银河 and 中国银河证券,
   中银证券 and 中银国际证券, plus two renames, 联讯证券 to 粤开证券 and 财富证券 to
   财信证券. `broker_names.py` merges each set into one identity and both steps 7 and 8
   use it. Before the merge the star match compared names literally, so the 4,512
   中信建投证券 records could never match a list that writes 中信建投, and 87 events were
   coded `star = 0` that should have been `star = 1`; the merge also moves 中信建投 from
   中部 to 头部 and 广发证券 out of 头部, changing the tier counts from 13 / 29 / 96 to
   13 / 27 / 91 and moving 1,370 of the 20,980 events (6.5%) to a different tier. The
   event table keeps each broker name exactly as iFinD reported it, and canonicalisation
   happens only at match time.
7. **Events at a subsidiary can never be `star = 1` by construction.** The rating table
   carries subsidiary names such as 华泰金融(HK) (1,916 records), 海通国际 (1,654) and
   群益证券(香港) (1,442). The ranked analysts sit at the parent firm, so these events are
   coded 0. That is the intended reading of the variable rather than a matching failure,
   but it should be stated rather than left implicit.
8. **Twenty events carry no analyst name in the source.** The raw extracts contain rows
   where `研究员姓名` is empty: 527 in 2018 and 876 across the seven years, of which all
   but 20 are reiterations that never enter the event sample. These 20 events keep their
   broker but can be neither matched to the list nor dated, so `star = 0` is forced rather
   than observed and `资历` is empty. They are 0.1% of the sample. An analyst-level
   specification may prefer to drop them, which would make the sample 20,960.
9. **The seniority table is keyed on the analyst name alone.** `ref_analyst_tenure.csv` merges
   into the event table on `研究员姓名`, so two analysts who share a name share one
   first-report date and one report count, and the later of them inherits the earlier
   one's seniority. The report counts show that such shared names exist: the largest reach
   6,805 records, which no single person files, and one name carrying 5,135 records has
   only 56 in the whole 2018-2024 rating detail. Seniority is therefore overstated for
   the namesakes of veteran analysts. Tightening it means matching on name and broker,
   and falling back to name alone only when that fails.
10. **585 ranked analysts have no first-report date at all.** They hold an industry ranking
   in some year but file no stock ratings in the iFinD rating detail, mostly strategy,
   macro and financial engineering directions, plus the CICC analysts, whose firm has no
   records there at all. The market side cross-checked the seniority table and returned
   the list as `data/handover_newfortune_missing_tenure.csv`; it holds 630 names once the award
   categories are counted too. None of them appears in the event table, so the event
   sample is unaffected either way.

## 7. Data provenance

- Extracted: 2026-10-05. iFinD query wording is brittle: a single space changes the
  parse. `2023年机构评级明细` returns nothing; `2023年 机构评级明细` returns 102,273
  rows. Each annual pull is therefore attempted with several wordings.
- Raw extracts are kept unchanged as `data/ratings_20XX.csv`; all cleaning happens
  in step 6, so the funnel can be re-run and audited step by step.
- Column names in the raw files carry a window suffix such as
  `最新报告日期[20180101-20181231]`; the cleaning step strips it.
- The scraped list misspelled one analyst name: the 海通证券 machinery analyst 佘炜超
  appears as 余炜超. The rating detail writes 佘炜超 in all 641 of his records and
  余炜超 in none, so the list-side spelling is corrected through `canonical_analyst`
  in `broker_names.py`. The market side's roster cross-check surfaced it, and the
  correction moves five 2019 events from `star = 0` to `star = 1`.

## 8. Building the report documents

The written deliverables are built from Markdown, so the text lives in one place and the
Word file is never hand-edited:

1. `python md2docx.py <src.md> <dst.docx> en` writes the Word file, using Word Heading
   styles and inserting a table-of-contents field.
2. `powershell -ExecutionPolicy Bypass -File refresh_toc.ps1` opens it once through Word
   COM to fill in the contents entries and the page numbers.

Step 2 is required: without it the reader opens the file to an empty contents page. It
goes through PowerShell COM rather than `win32com` because pywin32 is not installed here.
Close the file in Word or WPS before running it, or the save fails on a lock.
