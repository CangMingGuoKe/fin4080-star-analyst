# Project 10: Do Investors Follow Authority?
## Market Reactions to Star Analyst Recommendations

FIN4080 Behavioral Finance · The Chinese University of Hong Kong, Shenzhen
Sign-up sheet: **Topic 15** (the Project Bank calls it Project 10)
Group size: **2** · Presentation: **27 October 2026**, 15 min + 5 min Q&A · Max 15 slides
Status as of: 6 October 2026

> Note on numbering: this topic is "Project 10" in `Topic details.pdf` but "Topic 15" in
> `FIN 4080 Group and topic sign up.xlsx`. The sign-up sheet governs grading.

---

## 1. Research question

Milgram's obedience experiments show that people comply with authority even against
their own judgement. This project measures the market footprint of authority rather
than surveying investors: how do prices, volume and subsequent returns respond to
recommendation changes made by **star** (high-authority) versus ordinary analysts?

The assignment poses four questions that must each be answered:

1. Do rating changes by star analysts produce larger announcement returns and abnormal volume?
2. Do investors over-follow authority, i.e. is there drift or reversal after star recommendations?
3. Are star analysts actually more accurate ex post, or merely more influential?
4. Does the authority premium differ between upgrades and downgrades, and across brokerage tiers?

Question 3 is the hinge: it puts the **information hypothesis** and the **influence
hypothesis** side by side, so descriptive statistics alone cannot settle it.

| | Information / ability | Authority / influence |
|---|---|---|
| Source of authority | better access, better skill | status itself commands compliance |
| Announcement reaction | larger, because the news is real | larger, because investors follow blindly |
| Returns 6-12 months after | continue in the recommended direction | reverse |
| Ex post accuracy | stars are better | no difference |

## 2. Deliverables required by the course

Presentation slides (PDF), raw data files, reproducible analysis code, at least one
original visualization, a one-page data provenance statement, and at least three
academic papers or news items not on the syllabus. The TA audits the raw data and
the code. Everything for the course is produced in English.

## 3. Data sources

**Primary source: iFinD (同花顺).** All analyst data and market data are pulled through
the natural-language query interface (`THS_iwencai`, the "问财" endpoint of `iFinDPy`).

- The iFinD terminal must be running and logged in; the API returns error `-208`
  otherwise. An open terminal alone is not enough.
- **CSMAR and Wind are not used.** On this campus they are available only on the
  TA209 lab machines, with no personal account, no remote access and no API.
- **WRDS is not used.** Its CRSP / Compustat / I-B-E-S holdings are US-market data and
  contain no Chinese star-ranking information. Making the project a US study would
  mean giving up the China-specific contribution.

Analyst rating detail was retrieved for 2018-2024 with the following fields:
`股票代码, 股票简称, 最新报告日期, 最新研究机构原始评级, 最新同花顺评级,
上次同花顺评级, 评级调整方向, 研报目标价, 研究机构简称, 研究机构名称, 研究员姓名,
研报标题, 研报标题链接`. The last two names are misleading: `研报标题` holds a serialised
report object that carries the PDF URL and the publish timestamp, while `研报标题链接`
holds the title text. `data_dictionary.md` records this. iFinD already standardises the
rating scale, so no broker-by-broker manual mapping is needed.

## 4. Event sample

Unit of observation: one **rating revision**, i.e. a rating change by the same analyst
for the same stock. `评级调整方向` takes `调高` / `调低` / `维持`; only the first two
are events. The report date, not the database entry date, defines the event day.

| Step | Rows | Removed |
|---|---:|---:|
| Raw analyst rating records | 520,567 | |
| Exact duplicates | 517,871 | 2,696 |
| Rating revisions only | 21,471 | 496,400 |
| Drop first 6 months after IPO | 21,310 | 161 |
| Drop currently ST / \*ST | **20,980** | 330 |

Final sample: **20,980 events**, 2,683 stocks, 2,171 analysts, 108 broker short names (107 distinct legal names),
2018-2024. Upgrades 12,131; downgrades 8,849. The buy skew is expected and matches the
documented optimism bias of sell-side research.

## 5. Authority variables

Three proxies, all stored as columns on the analysis table:

| Variable | Definition | Source |
|---|---|---|
| `star` | 1 if the analyst is in the New Fortune Best Analyst list of the event year, with 2018 inheriting the 2017 list | external list |
| `资历` (seniority) | years from the first report by the analyst to the event date | iFinD, back to June 2009 |
| `券商层级` (broker tier) | 头部 / 中部 / 中小, cut on the cumulative share of rating records after broker names are canonicalised | own data |

`star = 1` for 2,772 of 20,980 events (13.2%), and the share is stable across years:
13.4%, 14.5%, 13.5%, 13.6%, 13.6%, 11.8%, 11.6% for 2018-2024.

**How the star variable handles the 2018 gap.** The New Fortune vote was suspended in
2018, and the page labelled 2018 on the public source is a compilation of anniversary
special awards, not an annual industry ranking. Evidence: 36% of its names appear in
no other year (versus 8-23% elsewhere), its name overlap with 2019 is Jaccard 0.10
(versus 0.40-0.52 for adjacent pairs), and it matches the rating data at only 3.6%
versus 10-17% for every other list-year. It is therefore excluded, and 2018 events
inherit the **2017** list, which is the most recent list actually in force during 2018.
This is the same "list in force" rule applied to every year, so there is no
special-casing and no look-ahead. The rule restores 2018 to the normal range (13.4%),
which is why the full 2018-2024 sample is usable.

## 6. Empirical design

**Step 1, announcement reaction.** Market-adjusted returns over [-1,+1], with
[-1,+5] and [-5,+5] as robustness. Dependent variables are CAR and abnormal volume.
Controls: size of the rating change, whether an EPS forecast moved at the same time,
firm size, pre-event momentum, turnover, institutional ownership, ownership type,
board. Industry × month fixed effects.

**Step 2, post-event drift.** Buy-and-hold abnormal returns over 6 and 12 months,
signed by the direction of the recommendation. This is where information and
influence separate: reversal implies investors over-followed.

**Step 3, ex post accuracy.** Return to the recommended direction over 3/6/12 months;
absolute EPS forecast error scaled by price; hit rate. If stars are larger in step 1
but indistinguishable here, the conclusion is "merely more influential".

**Step 4, heterogeneity.** Upgrades vs downgrades; broker tier; main board vs ChiNext
and STAR.

**Step 5, mechanism (extension, only if time permits).** Small-trade vs large-trade net
buying in the event window; the subsample of events that hit the daily price limit.

## 7. China-specific issues the design must address

1. **Price limits censor CARs.** The course notes warn explicitly that limit-hits inside
   event windows truncate CARs. Limit-hits must be flagged and the share reported, with
   a robustness run excluding them.
2. **Suspensions.** Flagged, not deleted from the panel, so event windows keep their
   trading-day alignment.
3. **Look-ahead.** Merges use announcement dates, never report periods.
4. **Rating labels differ across brokers.** Handled by using iFinD's standardised field.
5. **Analyst name collisions.** Matching uses name plus broker plus year.
6. **Historical ST status is not obtainable.** Every iFinD phrasing returns the current
   snapshot, so the ST filter is an approximation. The clean solution is to infer ST
   spells from daily price limits (ST stocks have a 5% band) once market data exist.

## 8. Robustness plan

Sample period with and without 2020 and 2022; alternative authority measures (star,
seniority, broker tier); alternative windows; excluding limit-hit and suspended events;
main board versus ChiNext and STAR; excluding events that coincide with an earnings
announcement. Alternative timing conventions for the star variable are already stored
as `star_same`, `star_month` and `star_lag1`.

Standard errors should be clustered. The 2,715 distinct report URLs behind a 3,000-event
sample show that one report can carry ratings for several stocks or for several analysts,
so observations are not independent within a report. Clustering at the report level, and
reporting the unclustered version beside it, is the honest way to present these tests. The cluster key is the report URL held inside `研报标题`; stock and date work as a fallback.

## 9. Division of labour (2 people)

| Step | Owner |
|---|---|
| 1 Collect recommendation revisions | A |
| 2 Classify by authority | B collects the list and broker tier; A does the matching and seniority |
| 3 Event study, CAR and abnormal volume | A leads, B independently replicates |
| 4 Six to twelve month post-revision returns | B leads, A independently replicates |
| 5 Visualization and discussion | split by slide |

B also delivers the market data (daily returns, volume, turnover, market cap) and the
index series. The required file format is specified in `event_study.py`.

## 10. Timeline

The presentation is on 27 October 2026 and roughly one effective week is available, so
the work is split into a scatter phase and a sprint week.

Before 19 October, four half-hour tasks that unblock everything else: confirm the iFinD
interface, install the missing Python packages, start collecting the New Fortune list,
confirm the written-report deadline with the TA.

Sprint week 20-26 October: pull and clean the data (20-21), main results (22-23),
robustness and heterogeneity (24), slides (25), rehearsal with timing (26).

Survival rules: main results must exist by 23 October, or the sample is cut to 20 stocks
until the pipeline runs end to end; slides freeze on 25 October; rehearse twice with a
timer and cut content rather than speed up delivery.

## 11. Slide outline (maximum 15)

Hook with a concrete case; institutional background on why China; the Milgram-to-market
mechanism; the four research questions and the two competing hypotheses; **the mapping
from each hypothesis to the data that can test it**; **the research pipeline as a flow
chart**; data sources and sample construction rules; three results slides; heterogeneity;
robustness; conclusion; extensions; appendix and Q&A backup.

Two hard requirements from the instructor's feedback on earlier groups: **no limitations
on the slides** (they belong in the written report), and **show the process and the logic
chain, not only the final result**.

## 12. Anticipated questions

1. *Endogeneity*: star analysts may pick stocks that would have risen anyway. Response:
   the 2018 spell without a list, "just outside the list" comparisons, and pre-event
   controls.
2. *Sample selection*: the list covers only analysts who were voted on. Response: state
   that the iFinD analyst universe and the voted universe differ, and drop analysts with
   very few reports.
3. *Non-behavioural explanations*: liquidity shocks, index inclusion, media coverage.
   Response: control turnover and size, test whether reversal survives transaction costs.
4. *The link between data and topic*: be ready to show the mapping slide and explain how
   each variable proxies what it claims to proxy.

## 13. References

1. Stickel, S. E. (1992). Reputation and Performance Among Security Analysts. *Journal of Finance*, 47(5), 1811-1836.
2. Bonner, S. E., Hugon, A., & Walther, B. R. (2007). Investor Reaction to Celebrity Analysts: The Case of Earnings Forecast Revisions. *Journal of Accounting Research*, 45(3), 481-513.
3. Loh, R. K., & Stulz, R. M. (2011). When Are Analyst Recommendation Changes Influential? *Review of Financial Studies*, 24(2), 593-627.
4. Fang, L. H., & Yasuda, A. (2009). The Effectiveness of Reputation as a Disciplinary Mechanism in Sell-Side Research. *Review of Financial Studies*, 22(9), 3735-3777.
5. Fang, L. H., & Yasuda, A. (2014). Are Stars' Opinions Worth More? The Relation Between Analyst Reputation and Recommendation Values. *Journal of Financial Services Research*, 46(3), 235-269.
6. Milgram, S. (1963). Behavioral Study of Obedience. *Journal of Abnormal and Social Psychology*, 67(4), 371-378.
7. 李勇, 王莉, 王满仓 (2015). 明星分析师的推荐评级更具价值吗. 《投资研究》, 34(5), 143-160.

## 14. Known limitations to disclose

- The 2018 New Fortune list had to be reconstructed from the 2017 ranking; it is an
  inference, not a published 2018 list.
- CICC (中金公司) has no records at all in the iFinD rating detail, so its analysts can
  never be matched. The 237 hits for 中金公司 across the extracts are all the stock
  601995.SH, not the broker. Its ranked entries are all fixed income, ranked 1st in
  2017, 3rd in 2019 and 4th in 2020, and those teams file no stock recommendations.
- The ST filter is an approximation because historical ST status is unobtainable.
- `资历` is censored at the source floor. The analyst rating detail begins in June 2009,
  so the 18.8% of analysts whose first report sits at that boundary cannot be ranked
  against one another, and December 2012 is absent from the source. Neither gap can be
  closed with this data. Correlation with the event year is 0.130, so year fixed effects
  remain advisable but the variable no longer merely counts calendar time. For the censored
  group the value is a lower bound on true tenure, so the seniority coefficient is
  attenuated rather than inflated. A robustness run drops that cohort, which is 2,674
  events (12.7% of the sample) and 18.5% of all star events.
- The broker tier is a self-constructed proxy based on research output, not an external
  ranking.
- Broker names needed canonicalising before matching (中信建投 / 中信建投证券, 中国银河 /
  中国银河证券, 中银证券 / 中银国际证券, and the renames 联讯证券 to 粤开证券 and 财富证券
  to 财信证券). Matching on the raw string understated `star = 1` by 87 events, and it
  split 中信建投's record count, which had placed the firm in the wrong tier. Merging
   the names moves 1,370 events (6.5%) to a different tier.
- Events tagged to a subsidiary (华泰金融(HK), 海通国际, 群益证券(香港) and similar) can
  never be `star = 1`, because the ranked analysts sit at the parent firm.
- Twenty events (0.1%) have no analyst name in the source, so they can be neither matched
  to the list nor dated. They keep their broker and are coded `star = 0`.
- `资历` is keyed on the analyst name alone, so an analyst who shares a name with a veteran
  inherits that veteran's first report date and the seniority is overstated. The report
  counts show such names exist: the largest reach 6,805 records, which no one person files.
