# Data Dictionary: `data/analysis_table.csv`

The analysis table. One row = one analyst recommendation revision.
20,980 rows × 32 columns, covering 2018-2024, 2,683 stocks, 2,171 analysts
and 108 broker short names (107 distinct legal names).

Built by `clean_event_table.py` → `build_star_variable.py` → `build_broker_tier.py`.
Raw extracts are kept unchanged in `data/ratings_20XX.csv` so the funnel can be
re-run step by step.

## Identifiers and event timing

| Column | Meaning |
|---|---|
| `股票代码` | Stock code with exchange suffix, e.g. `000001.SZ`. Six-digit string; leading zeros must be preserved. |
| `股票简称` | Stock name at the time of extraction (current name, not the historical one). |
| `最新报告日期` | **Event date**, `YYYYMMDD`. This is the research report's publication date, which defines day 0 of the event window. |
| `报告日` | Same date parsed to a datetime. |
| `年份`, `月份` | Year and month of the event date, used for matching and for fixed effects. |
| `数据年份` | The annual file the row came from; equals `年份`. |

## Rating content

| Column | Meaning |
|---|---|
| `最新研究机构原始评级` | The rating as worded by the broker, e.g. 买入 / 增持 / 中性 / 减持 / 卖出. Wording differs across brokers. |
| `最新同花顺评级` | The same rating after iFinD's standardisation to the five-level scale. **Use this one.** |
| `上次同花顺评级` | The analyst's previous standardised rating for the same stock. |
| `上次研究机构原始评级` | The previous rating in the broker's own wording. |
| `评级调整方向` | `调高` (upgrade), `调低` (downgrade) or `维持` (reiterated). Only the first two enter the sample. |
| `研报目标价` | Target price stated in the report. Non-missing for only 25.3% of records, and the missingness reflects a broker convention rather than random attrition: 华泰证券 94.9%, 国泰君安 76.7%, 中信证券 51.9%, 天风证券 26.1%, against 国信证券 2.8%, 民生证券 1.7%, 中泰证券 0.6% and 兴业证券 0.0%. Any test using this variable therefore selects on broker identity, so it should not be used as a broad control. |
| `研报标题` | The research report object, serialised as an `OrderedDict` string. Parse it to reach `URL` (a PDF snapshot link), `PublishTime` (epoch seconds, which converts to Beijing time equal to `报告日` on every row sampled) and `PageRawTitle`. **The name is misleading: the plain title is not in this column.** The naming comes from the iFinD response itself rather than from the cleaning step, so it is left unchanged for traceability to the raw extract. |
| `研报标题链接` | **The report title as plain text.** Despite its name it contains no URL, and it matches `PageRawTitle` in the column above on all 3,000 rows sampled. Use this column when a title is needed. Note that URLs are not unique per row: a 3,000-row sample holds 2,715 distinct ones, because a single report can carry ratings for several stocks or by several analysts. Events are therefore clustered within reports, which is a reason to cluster standard errors. |
Not a column of this table: the raw extract also carries `研报`, which repeats the same
web label on every row and is therefore dropped during cleaning.

## Analyst and broker identity

| Column | Meaning |
|---|---|
| `研究员姓名` | Analyst name. Used with broker and year to match the New Fortune list. |
| `研究机构简称` | Broker short name, e.g. `中信证券`, kept exactly as iFinD reported it. **Use it for matching, but map it through `canonical_broker` in `broker_names.py` first**: one firm appears under several spellings (中信建投 / 中信建投证券, 中国银河 / 中国银河证券, 中银证券 / 中银国际证券, plus the renames 联讯证券 to 粤开证券 and 财富证券 to 财信证券). Matching on the raw string discards real observations. |
| `研究机构名称` | Broker full legal name, e.g. `中信证券股份有限公司`. Do not match on this; use the short name. |

## Authority variables (the three proxies)

| Column | Meaning |
|---|---|
| `star` | **Default authority indicator.** 1 if the analyst is in the New Fortune list of the event year, with 2018 inheriting the 2017 list, else 0. Uses `star_inforce`. |
| `star_inforce` | Star under the "list in force" rule: use the list of the event year, except 2018, which inherits the 2017 list because the 2018 vote was suspended. |
| `star_same` | Same-year convention. Missing for 2018 because the 2018 list is invalid. Robustness only. |
| `star_month` | Convention where reports in January-October use the previous year's list. Robustness only. |
| `star_lag1` | Always the previous year's list. Robustness only. |
| `首报日` | Date of the first report by the analyst, `YYYY-MM-DD`, from `ref_analyst_tenure.csv`. |
| `首报年份` | Year of the first report by the analyst, taken from `ref_analyst_tenure.csv`. Coverage starts June 2009, the earliest the source provides. |
| `资历` | **Seniority in years**: days from the first report by the analyst to the event date, divided by 365.25. Correlation with the event year is 0.130, so it carries genuine cross-sectional information rather than counting calendar time. The analyst name is the only key in `ref_analyst_tenure.csv`, so an analyst who shares a name with a veteran inherits that veteran's first report date and their seniority is overstated. |
| `报告数` | Number of rating records under this analyst name across 2009-2024. **A rough size indicator only.** The largest values run into the thousands, which no one person files, so a single name collects several people and the count is not a per-person measure. |
| `触到覆盖起点` | 1 when the first report by the analyst falls at the coverage floor (June 2009), so their tenure can only be bounded from below, not measured. 18.8% of analysts. |
| `资历分位` | Percentile rank of `资历` among events in the same year, the rank form of the seniority measure. |
| `券商层级` | Broker tier: 头部 / 中部 / 中小, cut on the cumulative share of rating records after broker names are canonicalised, giving 13 / 27 / 91 of the 131 distinct houses. The two cut points are 50% and 90% of all 520,567 rating records. |

## Sample-construction flags

| Column | Meaning |
|---|---|
| `上市日` | Listing date, `YYYYMMDD`, from `ref_listing_dates.csv`. |
| `上市天数` | Days between listing and the event. Events with fewer than 183 days were dropped. |

## Counting convention

The rating scale is 1 = 买入, 2 = 增持, 3 = 中性, 4 = 减持, 5 = 卖出.
`评级调整方向` already encodes the direction, so no manual comparison is needed.
Upgrades 12,131 and downgrades 8,849 make up the 20,980 events; the buy skew
matches the documented optimism bias of sell-side research.
