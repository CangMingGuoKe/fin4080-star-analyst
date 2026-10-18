# Do Investors Follow Authority? Market Reactions to Star Analyst Recommendations in China, 2018-2024

FIN4080 Behavioral Finance, The Chinese University of Hong Kong, Shenzhen

Group project, two members. Preliminary version, 18 October 2026.

## Abstract

This paper examines whether investors follow star analysts because stars are more accurate or because their status commands attention. Using 20,980 recommendation revisions for Chinese A-shares from 2018 to 2024, it compares announcement returns and abnormal volume, post-announcement drift, and ex post accuracy between star and non-star analysts. Star upgrades generate a larger market-adjusted announcement return (0.37 percentage points over [-1,+1], t = 2.17) and higher abnormal volume; star downgrades do not. The upgrade premium is concentrated in events with a price-limit hit. Star downgrades are followed by short-run underperformance (1.64 percentage points over +2 to +60, p = 0.002) and later reversal, whereas star upgrades show no differential drift. Holding-period returns favour stars only at short horizons, and star analysts' absolute earnings forecast errors are larger. The evidence is more consistent with influence than with a stable information advantage.

## 1. Introduction

Authority can shape decisions against private information (Milgram, 1963). This paper asks whether the same mechanism operates in financial markets. When a star analyst changes a recommendation, does the market respond to the information in the revision, or to the analyst's status? The distinction matters because sell-side research is valuable only if reputation tracks accuracy. If star status generates a price response that is not matched by superior forecasts, investors are paying for status rather than information.

China provides a suitable setting. Retail investors account for a large share of turnover, price limits and T+1 trading constrain arbitrage, and the New Fortune ranking supplies an annually updated, widely recognised definition of star status. These features make authority effects easier to detect than in a market dominated by institutional trading.

The paper answers the four questions posed by the assignment. It first tests whether star recommendation changes generate larger announcement returns and abnormal volume. It then examines post-announcement drift and reversal, compares ex post accuracy, and tests whether the authority premium differs between upgrades and downgrades and across brokerage tiers.

## 2. Literature and hypotheses

The information explanation holds that star analysts have better access, larger teams and stronger skills. Their revisions should convey more news, produce larger announcement reactions, and be followed by returns in the recommended direction. The influence explanation holds that status itself is the source of authority. Investors react to the label, not only to the content, so the announcement reaction can be large even when the forecast is not more accurate. Because attention is temporary, the initial price impact may later reverse.

Both explanations predict a larger announcement reaction, so announcement-window tests alone cannot separate them. Prior work uses three additional margins. Stickel (1992) relates reputation to forecast accuracy and market impact. Bonner, Hugon and Walther (2007) show that celebrity status affects the reaction to earnings forecast revisions. Loh and Stulz (2011) ask when recommendation changes are influential, while Fang and Yasuda (2009, 2014) examine whether reputation disciplines research and whether star opinions are worth more. Chinese evidence in 李勇、王莉、王满仓 (2015) points in a similar direction. Milgram (1963) provides the behavioural foundation for treating authority as a separate source of influence.

The hypotheses follow directly:

- **H1.** Star recommendation changes produce larger announcement-window abnormal returns and abnormal volume than non-star changes.
- **H2.** If stars convey information, returns continue in the recommended direction; if investors over-follow authority, the initial reaction reverses.
- **H3.** If stars are more accurate, their recommendations and earnings forecasts perform better ex post; if they are merely influential, accuracy is similar or worse.
- **H4.** The authority premium differs between upgrades and downgrades and across brokerage tiers.

The hypotheses are diagnostic rather than mutually exclusive. Larger announcement effects without an accuracy advantage are consistent with influence, but they do not prove that no information is conveyed. The analysis therefore reports economic magnitudes and several accuracy metrics rather than relying on a single test.

## 3. Data and sample

### 3.1 Source

Analyst data were extracted from iFinD (同花顺) through its natural-language query interface (`THS_iwencai`). The annual rating detail covers 2018-2024 and was pulled on 5 October 2026. Query wording is sensitive to spaces: `2023年机构评级明细` returns nothing, whereas `2023年 机构评级明细` returns 102,273 rows. Each annual pull therefore uses several wordings, and the first non-empty result is retained.

CSMAR and Wind were not used. On this campus they are available only on the TA209 laboratory machines, without personal accounts, remote access or an application programming interface. Manual export of 20,980 events across seven years is not feasible. iFinD provides the same analyst-level information through an API and is the source used throughout. Appendix B documents the extraction in detail.

### 3.2 Sample construction

The unit of observation is an analyst's recommendation revision for a stock, not a research report. A report may cover several stocks or be signed by several analysts, so it can generate zero, one or several events. Only upgrades (调高) and downgrades (调低) enter the sample. Reiterations (维持) are excluded because the rating does not change. Initiations of coverage are excluded because there is no previous rating to revise; iFinD labels them as unknown, and they are stored separately (42,276 records).

| Step | Rows remaining | Removed |
|---|---:|---:|
| Raw analyst rating records | 520,567 | |
| Exact duplicates removed | 517,871 | 2,696 |
| Rating revisions only | 21,471 | 496,400 |
| Drop first six months after IPO | 21,310 | 161 |
| Drop currently ST or \*ST | 20,980 | 330 |

The final sample contains 20,980 events for 2,683 stocks and 2,171 analysts, with 108 broker short names and 107 distinct legal names. It includes 12,131 upgrades and 8,849 downgrades. The buy skew is consistent with the documented optimism of sell-side ratings, so the two directions are analysed separately.

### 3.3 Authority variables

**Star.** `star` equals one if the analyst appears in the New Fortune Best Analyst list for the event year. The 2018 vote was suspended, and the page labelled 2018 is a compilation of anniversary awards rather than an annual industry ranking. It is excluded, and 2018 events inherit the 2017 list, which was the list in force during 2018. The evidence is that 34.7% of the 2018 page's names appear in no other year, against 8.1-17.7% for 2019-2023; its name overlap with 2019 is Jaccard 0.10, against 0.42-0.52 for other adjacent pairs; and it matches only 4.0% of that year's events under the name-and-broker rule, against 12.1-14.0% for other list years. The in-force rule restores 2018 to 13.4%. Across the sample, 2,774 events (13.2%) have `star = 1`.

**Seniority.** Seniority is the number of years from the analyst's first report to the event date, divided by 365.25. The first-report date comes from a separate iFinD pull that reaches back to June 2009, the source floor. For analysts whose first report falls at that floor (18.8%), the value is a lower bound and a flag records the censoring. The variable is keyed on analyst name, so namesakes share a first-report date.

**Broker tier.** No official research-department tier list exists. The CSRC classification rates the securities firm as a whole, and the New Fortune list is already used for `star`, so neither is suitable. The tier is a proxy built from research output. Each rating record is assigned to a stable broker identity, with renames and mergers resolved into one entity named after the name in force at the start of the sample. For example, 国泰君安 remains the identity until the 2025 merger with 海通证券, after which the entity becomes 国泰海通; 安信证券 remains the identity until its 2024 rename to 国投证券. Event-level display uses the name in force in that year, so a 2018 国泰君安 report is never written as 国泰海通.

Within each identity, all rating records from 2018 to 2024 are counted. Houses are sorted by this count and cut on the cumulative share of records: the top tier contains houses whose cumulative share, including themselves, does not exceed 50%; the middle tier continues to 90%; the remainder forms the small tier. The result is 13 / 26 / 85 houses out of 124, covering 48.0%, 41.4% and 10.6% of records. Equal thirds are not used because the distribution is highly skewed: the top 42 houses, one third of 124, already account for 91.8% of records. Subsidiaries such as 海通国际 and 华泰金融(HK) remain separate identities for the tier but are excluded from star matching, because ranked analysts sit at the parent firm.

| Year | Events | Star share |
|---|---:|---:|
| 2018 | 3,808 | 13.4% |
| 2019 | 3,486 | 14.5% |
| 2020 | 2,904 | 13.5% |
| 2021 | 2,400 | 13.6% |
| 2022 | 2,760 | 13.6% |
| 2023 | 2,896 | 11.9% |
| 2024 | 2,726 | 11.7% |
| Total | 20,980 | 13.2% |

### 3.4 Market data

Daily total returns come from `stock_returns_dretwd.csv`: 2,683 stocks, 5,605,500 rows, and the period from 3 January 2017 to 30 September 2026. The return `Dretwd` is in decimals. The market return is the CSI 300 total-return index `H00300` in `market_returns_h00300.csv`, which covers 2,367 trading days over the same period. `market_data_adapter.py` converts both to percentage points. Suspension days are absent rather than filled with zero, holiday filler rows have been removed, and old and new stock codes are unified. Volume for abnormal volume and event-day closing prices for the forecast-error test come from the earlier `market_panel.csv`; returns do not use that panel.

## 4. Empirical design

**Event day and windows.** The event day is the first trading day at or after the report date, because 3,857 reports (18.4%) are not filed on a trading day. The market calendar defines day zero. If the stock is suspended on that day, the event-day return is missing and the validity rule below applies; the event is not shifted to a later stock-specific trading day.

**Announcement returns and volume.** Abnormal returns are market-adjusted total returns: the stock's `Dretwd` minus the `H00300` market total return, with both converted from decimals to percentage points. No alpha or beta is estimated, so the design is a market-adjusted event study rather than a market-model regression. Cumulative abnormal returns (CAR) are sums of daily abnormal returns over [-1,+1], [-1,+5], [-5,+5], [0,+60], [0,+120] and [0,+250]. Abnormal volume is log volume on the event day minus the mean log volume over [-120,-11], with at least 60 valid positions.

A CAR is reported only if the event-day return is valid and at least 80% of the trading days in the window have valid returns. Suspended days remain in the calendar as missing observations, never as zero returns, and the reason for a missing CAR is recorded. This avoids both treating a suspension as a zero return and deleting the day, which would shift the window.

**Post-announcement drift.** Drift windows start at +2 rather than zero, so the announcement reaction is excluded. CAR is measured over +2 to +60, +2 to +120 and +2 to +250.

**Ex post accuracy.** Two metrics are used. The first is the direction-adjusted holding-period return: the market-adjusted cumulative total return from the event-day close to the close after 63, 126 or 252 trading days, with upgrades held long and downgrades held short. A positive value indicates that following the recommendation would have been profitable. A window requires at least 80% valid trading days. The second is the analyst's earnings forecast error. Each event is matched to the analyst's own earnings-per-share forecast in the same report on stock, report date, analyst and broker. The error is the absolute difference between the forecast and realised annual basic EPS, divided by the event-day closing price and multiplied by 100. Errors are computed for the report's fiscal year (FY0) and the next fiscal year (FY1), winsorised at the 1st and 99th percentiles, and the signed error is also reported to distinguish optimism from dispersion. The matched sample contains 20,248 events (96.5%); FY0 actual EPS is available for 20,067 events and FY1 for 17,024, because 2024 events require 2025 realised EPS.

**Heterogeneity models.** The fourth question is estimated with OLS models using winsorised CAR or abnormal volume as the dependent variable. The pooled model includes `star`, a downgrade indicator, their interaction, seniority, log listing age and year fixed effects. Tier models estimate the same specification separately for upgrades and downgrades, with a middle-tier indicator and a `star` × middle-tier interaction; the top tier is the reference group. Standard errors are clustered by stock. The small tier contains only two star upgrades and no star downgrades, so it is reported descriptively and excluded from the interaction models.

The event-study and accuracy tables report unclustered two-sample tests, with a same-stock-same-day collapsed variant for the event study. Section 6 reports the same estimates with standard errors clustered by stock; the conclusions are unchanged.

## 5. Results

### 5.1 Announcement returns and abnormal volume

Star upgrades generate larger announcement effects; star downgrades do not.

| Window | Upgrades: difference | t | Downgrades: difference | t |
|---|---:|---:|---:|---:|
| CAR[-1,+1] | +0.37 pp | 2.17 | +0.06 pp | 0.35 |
| CAR[-1,+5] | +0.54 pp | 2.30 | -0.19 pp | -0.85 |
| CAR[-5,+5] | +0.99 pp | 3.55 | -0.21 pp | -0.74 |
| Abnormal volume | +0.053 | 2.85 | -0.011 | -0.53 |

The upgrade premium is modest but precisely estimated: 0.37 percentage points over the three-day window and 0.99 over the eleven-day window. Abnormal volume is 0.053 log points higher for star upgrades. The same-stock-same-day collapsed variant yields 0.43 (t = 2.51), 0.61 (t = 2.58) and 1.06 (t = 3.81), with abnormal volume at 0.059 (t = 3.19), so the result is not driven by multiple events on the same stock-day. No downgrade window is statistically significant. The upgrade premium is concentrated in events whose window contains a price-limit hit. Excluding those events, the [-1,+1] difference falls from 0.37 to 0.21 (p = 0.134) and the [-1,+5] difference from 0.54 to 0.20 (p = 0.310); the [-5,+5] difference remains 0.65 (p = 0.008).

[[FIGURE1]]

**Figure 1.** Star minus non-star announcement effects. Bars are differences in market-adjusted CAR (left) and abnormal volume (right); whiskers are 95% confidence intervals; stars denote *** p < 0.01, ** p < 0.05, * p < 0.10.

### 5.2 Post-announcement drift

The drift pattern differs by direction.

| Window | Upgrades: difference | p | Downgrades: difference | p |
|---|---:|---:|---:|---:|
| +2 to +60 | -0.07 pp | 0.90 | -1.64 pp | 0.002 |
| +2 to +120 | +0.98 pp | 0.16 | -0.76 pp | 0.32 |
| +2 to +250 | +0.76 pp | 0.48 | +1.53 pp | 0.18 |

Star downgrades are followed by 1.64 percentage points of additional underperformance over the first 60 trading days. The difference then narrows and changes sign by +250 days (+1.53, p = 0.18). The pattern is an initial reaction followed by partial reversal, which is consistent with over-following, but the long-horizon estimate is not statistically significant. Star upgrades show no differential drift.

[[FIGURE2]]

**Figure 2.** Post-announcement drift. Bars are star-minus-non-star market-adjusted CAR from +2 to the stated horizon; whiskers are 95% confidence intervals.

### 5.3 Ex post accuracy

The accuracy evidence is mixed and does not support a stable advantage.

| Horizon | Upgrades: star minus non-star | p | Downgrades: star minus non-star | p |
|---|---:|---:|---:|---:|
| Holding return, 3 months | +0.41 pp | 0.47 | +1.78 pp | 0.001 |
| Holding return, 6 months | +1.51 pp | 0.048 | +1.04 pp | 0.19 |
| Holding return, 12 months | +1.20 pp | 0.28 | -1.39 pp | 0.23 |

For upgrades, the advantage appears at six months (+1.51 percentage points, p = 0.048) but not at three or twelve months. For downgrades, it is concentrated at three months (+1.78, p = 0.001) and disappears by six months; at twelve months the sign reverses. Hit rates move in the same direction: 54.1% versus 50.9% for six-month upgrades and 56.3% versus 53.1% for three-month downgrades.

Forecast errors point in the opposite direction. Star analysts' absolute errors are larger in all four cells: FY0 upgrades 2.18 versus 1.89 (difference 0.28, p = 0.002), FY0 downgrades 3.07 versus 2.61 (0.46, p = 0.002), FY1 upgrades 4.60 versus 4.20 (0.40, p = 0.014) and FY1 downgrades 5.60 versus 4.64 (0.96, p < 0.001). Signed errors, which measure optimism, do not differ significantly (0.15 and 0.18, p = 0.12 and 0.24). Stars are therefore not more optimistic; their forecasts are more dispersed. One explanation is that stars cover harder or more volatile stocks, an uncontrolled selection difference that should not be read as direct evidence of lower ability.

[[FIGURE3]]

**Figure 3.** Direction-adjusted holding-period returns, market-adjusted. Bars are star-minus-non-star differences; whiskers are 95% confidence intervals.

### 5.4 Direction and broker tier

The direction asymmetry is robust. In the pooled interaction model, the star premium on upgrades is +0.39 percentage points at [-1,+1] (p = 0.021), and the interaction with the downgrade indicator is -0.29 (p = 0.197). At [-1,+5] the upgrade premium is +0.58 (p = 0.014) and the interaction is -0.70 (p = 0.025). For abnormal volume, the upgrade premium is +0.049 (p = 0.009) and the interaction is -0.057 (p = 0.041). The asymmetry is therefore statistically clear at the five-day window and for volume, and marginal at the three-day window and at +2 to +120.

Tier results are suggestive but not stable. For upgrades, the top-tier star premium is +0.55 at [-1,+1] (p = 0.017), the top-versus-middle difference is -0.63 (p = 0.072), and the middle-tier total effect is -0.08 (p = 0.761). For abnormal volume, the top-tier premium is +0.064 (p = 0.013). For downgrades, the middle-tier total effect is +0.62 (p = 0.007), while the top-tier effect is -0.14 (p = 0.536). The signs differ from the upgrade side, which makes the tier result difficult to interpret as a single authority premium.

Two caveats apply. First, `star` and tier are highly collinear: the small tier contains only two star upgrades and no star downgrades. Second, a backward-looking rolling tier, built from records in the three years before each event, reclassifies 23.1% of events; the asymmetry survives, but the tier coefficients become unstable: the top-tier upgrade premium is +0.49 (p = 0.046), its volume premium +0.042 (p = 0.099), and the middle-tier downgrade effect +0.33 (p = 0.129). Tier results are therefore descriptive, not a separate causal channel.

## 6. Robustness

**Suspension.** The main specification keeps suspension events and requires 80% valid observations. A second specification drops any event whose window contains a suspension day, identified from `StateCode` and `Filling` (43,830 stock-date pairs).

| Window | Upgrades: share dropped | Upgrades: difference, full to dropped | Upgrades: p, full to dropped |
|---|---:|---:|---:|
| [-1,+1] | 0.6% | +0.37 to +0.37 | 0.030 to 0.030 |
| [-1,+5] | 0.7% | +0.54 to +0.59 | 0.021 to 0.013 |
| [-5,+5] | 0.9% | +0.99 to +0.99 | 0.0004 to 0.0004 |
| [0,+120] | 3.3% | +1.37 to +1.46 | 0.061 to 0.049 |
| [0,+250] | 5.6% | +0.90 to +0.83 | 0.40 to 0.44 |

Downgrades remain insignificant in every window. Point estimates change by much less than their standard errors, and the upgrade premium survives. Suspension is not driving the result.

**Alternative star definitions.** The analysis table stores same-year (`star_same`), month-based (`star_month`) and one-year lag (`star_lag1`) conventions. The default `star_inforce` is the in-force list, with 2018 inheriting 2017. The 2018 page is excluded as documented in Section 3.3.

**Clustered inference.** All three analyses are re-estimated with standard errors clustered by stock. The star premium remains significant where it was significant: CAR[-1,+1] 0.37 (p = 0.035), CAR[-1,+5] 0.54 (p = 0.028), CAR[-5,+5] 0.99 (p = 0.0006) and abnormal volume 0.053 (p = 0.006); six-month upgrades 1.51 (p = 0.050) and three-month downgrades 1.78 (p = 0.002); forecast errors FY0 0.28 (p = 0.003) and 0.46 (p = 0.001), FY1 0.40 (p = 0.017) and 0.96 (p < 0.001). No 5% significance conclusion changes. A stock-day clustered variant yields similar results. One caveat: the FY1 upgrade error is significant only after winsorisation (raw p = 0.079). The clustered tests are not adjusted for multiple specifications. A Bonferroni correction across 30 main specifications (threshold 0.0017) leaves five results significant: upgrade CAR[-5,+5], downgrade three-month holding returns in both raw and market-adjusted form, FY0 downgrade errors and FY1 downgrade errors. Clustering is one-way by stock; a two-way stock-by-date variant is not reported.

**Price limits.** Price-limit hits are identified from daily returns and board-specific thresholds (10% main board, 20% ChiNext and STAR, 30% BSE), excluding the first five trading days and capping at the threshold plus 1.0 percentage point. Dropping events with a limit hit in the window leaves upgrade CAR[-1,+1] at 0.21 (p = 0.134), [-1,+5] at 0.20 (p = 0.310) and [-5,+5] at 0.65 (p = 0.008); downgrades remain insignificant. The premium is concentrated in limit-hit events, and the short-window result should not be described as robust to price limits.

**ST proxy.** Historical ST status is unavailable. A strict proxy (main-board returns between 4.8% and 5.2%, sustained over 31 days, at least 25 valid returns) flags 4,915 stock-days; dropping these events leaves the short-window results unchanged, while the 120-day upgrade p-value moves from 0.061 to 0.080. A literal 5% rule is too noisy and is not used.

**Independent replication.** A separate implementation, which does not reuse the project's functions, reproduces the event-study CAR, the holding-period group means and the forecast-error outputs. `文档/replication_note.md` records the maximum differences and keeps the first-run audit trail. The only definitional difference concerns events with a missing event-day return in windows that exclude day 0: a strict event-day rule returns NaN, while the reference engine reports a value. The difference does not change the sign of any group comparison.

**Remaining checks.** The FY1 forecast-error sample ends with 2023 events; extending it requires 2025 realised EPS.

## 7. Discussion

The pattern is consistent with influence, with a short-run information component. Stars generate a larger announcement reaction and more volume, which both explanations predict. The reaction is not followed by a persistent accuracy advantage: star upgrades are better only at six months, star downgrades only at three months, and both advantages disappear by twelve months. Most importantly, star analysts' earnings forecasts are less accurate in absolute terms. If star status primarily signalled superior information, the opposite would be expected.

The short-run accuracy results prevent a pure influence interpretation. A star upgrade outperforms for six months, and a star downgrade underperforms for three months. Authority may therefore amplify a genuine short-run signal, while the long-run price path is driven by other forces. The evidence indicates market impact and a short-lived accuracy edge, not a stable ability premium.

Career concerns are an alternative mechanism. Analysts who fear damaging their reputation may avoid bold forecasts, herd toward consensus, or issue recommendations that are easy to defend. The data contain two observable proxies, seniority and broker tier. Seniority is censored at the 2009 source floor, and the tier is collinear with star status, so neither supports a clean test. The tier pattern, with the upgrade premium concentrated in top-tier brokers, is consistent with career concerns, but also with larger research teams and better distribution. Career concerns are therefore discussed rather than tested.

The asymmetry between upgrades and downgrades may reflect the optimism of sell-side ratings. Downgrades are relatively rare (8,849 against 12,131 upgrades), so a downgrade is more likely to be a genuine information event, while an upgrade can be a routine affirmation. Short-sale constraints and limited attention also make negative recommendations harder to trade. Authority is therefore not a single premium that applies equally to good and bad news.

## 8. Limitations

Three limitations qualify the interpretation. First, star status is not randomly assigned, and the broker tier is a descriptive proxy constructed from rating records and highly collinear with star; the estimates describe associations, not causal effects. Second, standard errors are clustered by stock for the main tests, but the tests are not adjusted for multiple specifications and a two-way stock-by-date variant is not reported; the announcement premium is concentrated in price-limit events, and historical ST status is proxied rather than observed. Third, the data have known gaps: iFinD provides neither historical ST status nor research-line revenue; the 2018 New Fortune page is not an annual ranking, so 2018 inherits the 2017 list; and the FY1 forecast-error sample ends with 2023 events because 2025 realised EPS is outside the current pull.

## 9. Conclusion

Star analyst recommendations have market impact, but the impact is not matched by a stable accuracy advantage. Star upgrades generate larger announcement returns and abnormal volume; star downgrades do not, and the upgrade premium is concentrated in price-limit events. Star downgrades are followed by short-run underperformance and later reversal, while star upgrades show no differential drift. Holding returns favour stars only at short horizons, and star earnings forecasts are less accurate in absolute terms. The evidence is closer to the influence explanation than to a stable information explanation, with a short-run information component that does not persist.

## References

1. Bonner, S. E., Hugon, A., & Walther, B. R. (2007). Investor Reaction to Celebrity Analysts: The Case of Earnings Forecast Revisions. *Journal of Accounting Research*, 45(3), 481-513.
2. Fang, L. H., & Yasuda, A. (2009). The Effectiveness of Reputation as a Disciplinary Mechanism in Sell-Side Research. *Review of Financial Studies*, 22(9), 3735-3777.
3. Fang, L. H., & Yasuda, A. (2014). Are Stars' Opinions Worth More? The Relation Between Analyst Reputation and Recommendation Values. *Journal of Financial Services Research*, 46(3), 235-269.
4. Loh, R. K., & Stulz, R. M. (2011). When Are Analyst Recommendation Changes Influential? *Review of Financial Studies*, 24(2), 593-627.
5. Milgram, S. (1963). Behavioral Study of Obedience. *Journal of Abnormal and Social Psychology*, 67(4), 371-378.
6. Stickel, S. E. (1992). Reputation and Performance Among Security Analysts. *Journal of Finance*, 47(5), 1811-1836.
7. 李勇, 王莉, 王满仓 (2015). 明星分析师的推荐评级更具价值吗. 《投资研究》, 34(5), 143-160.

## Appendix A. Variable definitions

| Variable | Definition |
|---|---|
| `star` | 1 if the analyst is in the New Fortune list of the event year, with 2018 inheriting the 2017 in-force list |
| `资历` | Years from the analyst's first report to the event date, with a flag for the June 2009 floor |
| `券商层级` | 头部 / 中部 / 中小, cut on the cumulative share of rating records at 50% and 90%; 13 / 26 / 85 of 124 houses |
| `CAR` | Sum of daily market-adjusted returns over the stated window, in percentage points |
| `AV` | Log volume on the event day minus mean log volume over [-120,-11], requiring 60 valid positions |
| Holding return | Market-adjusted cumulative return from the event-day close to +63, +126 or +252 trading days, direction-adjusted |
| Forecast error | Absolute difference between the analyst's EPS forecast and realised EPS, divided by the event-day price and multiplied by 100 |

## Appendix B. Data provenance statement

All data were extracted from iFinD (同花顺). The analyst rating detail was pulled on 5 October 2026 for each year from 2018 to 2024 through `THS_iwencai`. Query wording is sensitive to spaces; each year was attempted with several phrasings, and the first non-empty result was retained. The seven annual files contain 520,567 raw records and are stored unchanged. Cleaning removes exact duplicates, keeps upgrades and downgrades, drops events within six months of listing, and drops currently ST stocks. The final analysis table contains 20,980 events and is documented in `data_dictionary.md`.

Analyst earnings forecasts and realised annual EPS were pulled on 18 October 2026. The forecast extraction uses `2023年 机构盈利预测明细`, returning 96,399 rows for 2023 and 528,477 rows over 2018-2024, with report date, institution, analyst and EPS forecasts for the previous, current, next and following fiscal years. The realised EPS extraction uses `2023年 基本每股收益 全部A股`, returning 5,226 stocks per year and 36,582 rows over 2018-2024.

The cleaned market data were delivered on 18 October 2026. `stock_returns_dretwd.csv` contains 5,605,500 rows for 2,683 stocks from 3 January 2017 to 30 September 2026, with stock code, date and the decimal total return `Dretwd`. `market_returns_h00300.csv` contains 2,367 trading days of the CSI 300 total-return index `H00300` and its decimal market return. Suspension rows are omitted rather than filled with zero, holiday filler rows are removed, and old and new stock codes are unified. Volume and event-day closing prices come from the earlier `market_panel.csv`, which also carries `StateCode` and `Filling` for the suspension robustness check.

The analysis code is in the project repository. `event_study_v2.py` builds the calendar-aligned CAR and abnormal volume; `accuracy_test.py` builds holding-period returns; `forecast_error.py` matches each analyst's forecast to realised EPS; `heterogeneity_test.py` and `heterogeneity_rolling.py` estimate the direction and tier models; `suspension_robustness.py` runs the suspension check. The repository is private because it contains data derived from iFinD. Raw extracts and the full market panel are kept locally and are not redistributed.

Known gaps are documented in Section 8. In brief, iFinD does not provide historical ST status or a research-line revenue panel, the 2018 New Fortune page is not an annual ranking, 34 event stocks lack realised EPS, and the FY1 forecast-error sample ends with 2023 events.
