# Project 10 四个 Findings 的底层逻辑与口播底稿

FIN4080 Behavioral Finance，2026 年 10 月 27 日陈述。

版本：2026-10-19。对应幻灯片：`Project10_Star_Analyst_Deck_20261027.pptx`。

## 0. 一页逻辑流

```text
Q1 公告日收益与成交量
  -> Q1 边界：CAR 溢价集中在涨跌停事件
  -> Q2 公告后漂移与反转
  -> Q3 持有收益与预测误差
  -> Q4 方向与券商层级
  -> 合起来：影响力为主，短期信息为辅
```

一句话主线：明星标签带来更大的公告日冲击，但没有稳定的预测优势。短期可能有一点信息成分，长期更像影响力。

四个 finding 不是四篇平行的小论文，而是一条诊断链。Q1 建立现象，Q2 和 Q3 区分信息与影响力，Q4 说明这个溢价的边界。每回答完一个问题，都要回到这条主线上。

## 1. 这份底稿怎么用

这份底稿不是逐字稿，而是每个 finding 的“底层逻辑 + 口播要点 + 不能说的话”。准备时按三层用：

1. 先记住每个问题的子部分。问题不是一个指标，而是两到三个子部分。少回答一个，老师就会追问。
2. 再记住每个子部分的数字和符号。数字要能脱稿说出三个：Q1 的 0.37 和 0.053，Q2 的 -1.64，Q3 的 +0.94。
3. 最后记住每个回答的边界。哪些话不能说，比哪些话能说更重要。

## 2. 四个问题为什么这样排

| 问题 | 它在诊断链里的作用 | 回答什么 | 页 |
|---|---|---|---|
| Q1 公告日收益与成交量 | 建立现象 | 明星评级调整是否带来更大的价格和成交量反应 | 7 至 8 |
| Q2 公告后漂移与反转 | 第一个区分检验 | 反应之后是继续，还是回头 | 9 |
| Q3 事后准确度 | 第二个区分检验 | 明星是否更准，还是只是在影响市场 | 10 |
| Q4 方向与券商层级 | 边界条件 | 这个溢价是否对所有方向、所有券商都一样 | 11 |

Q1 不能单独区分信息与影响力，因为两种解释都预测更大的公告日反应。Q2 和 Q3 才是区分检验。Q4 不是第五个机制，它回答的是“这个溢价在哪里成立”。

## 3. Q1：公告日收益与成交量

### 3.1 问题原文

Do star analyst recommendation changes generate larger announcement returns and abnormal trading volume?

### 3.2 问题真正问什么

Q1 有两个维度，四个格子：

- 维度一：价格反应 CAR，和成交量反应 AV。
- 维度二：上调，和下调。

只回答 CAR，或者只回答上调，都不算回答 Q1。成交量不是附带结果，它衡量的是注意力和交易行为。价格动、成交量不动，可能只是流动性或估值修正；价格和成交量一起动，才更像“权威标签吸引了交易”。

### 3.3 我们的回答

幻灯片标题：

**Star upgrades move both price and volume. Star downgrades move neither.**

中文：明星上调同时带来更大的公告日收益和更高的异常成交量；明星下调两个都没有。

### 3.4 四个格子

|  | CAR[-1,+1] | Abnormal volume |
|---|---|---|
| Upgrade | +0.37 pp，t = 2.17 | +0.053 log points，t = 2.85 |
| Downgrade | +0.06，t = 0.35，n.s. | -0.011，t = -0.53，n.s. |

补充数字：

- 上调 CAR[-1,+5] +0.54，p = 0.021；CAR[-5,+5] +0.99，p = 0.0004。
- 下调 CAR[-1,+5] -0.19，p = 0.398；CAR[-5,+5] -0.21，p = 0.458。
- 同股同日先取均值：上调 +0.43 / +0.61 / +1.06；AV +0.059。说明不是同日重复事件堆出来的。
- +0.053 个对数点约等于成交量高 5%。

### 3.5 底层逻辑

第一，价格和成交量回答不同问题。CAR 是价格反应，AV 是交易反应。明星标签如果只是改变估值，价格会动；如果还改变注意力，成交量也会动。我们同时看到两者，说明 Q1 的答案不是“价格溢价”一个词，而是“价格和成交量一起动”。

第二，方向不对称是第一个线索。上调多、下调少，上调更像例行确认，下调更像真信息。如果权威是一个对所有消息都一样的溢价，下调也应该有反应。但下调的四个格子全部为零，说明权威溢价不是对称的。

第三，Q1 只能建立现象，不能区分机制。信息解释和影响力解释都预测更大的公告日反应。所以 Q1 的结论要停在“有反应”，不能跳成“是影响力”。

第四，Q1 的边界是涨跌停。剔除窗口内出现涨跌停的事件后，CAR[-1,+1] 从 0.37 降到 0.21，p = 0.134；CAR[-1,+5] 从 0.54 降到 0.20，p = 0.310；CAR[-5,+5] 从 0.99 降到 0.65，p = 0.008。短窗口 CAR 溢价不再显著，只有 11 日窗口还站得住。这个检验只覆盖 CAR，没有单独拆分 AV。

### 3.6 口播

**English:** Q1 has two halves: returns and volume, and each half has to be split into upgrades and downgrades. Star upgrades earn 0.37 percentage points over the three-day window, with a t-statistic of 2.17. Their abnormal volume is 0.053 log points higher, which is about 5%. Star downgrades show neither: the CAR difference is 0.06 with a t-statistic of 0.35, and the volume difference is minus 0.011 with a t-statistic of minus 0.53. So the answer to Q1 is a two-by-two matrix: only the two upgrade cells move.

**中文提示：** 先说“两个维度、四个格子”，再报数字。不要把成交量说成“顺便也显著”，它是 Q1 的一半。

### 3.7 不能说的话

- 不能说“成交量对涨跌停稳健”。涨跌停检验只做了 CAR，没有拆分 AV。
- 不能说“明星对所有评级都有溢价”。下调四个格子都不显著。
- 不能说 Q1 证明了影响力。Q1 只建立现象，区分要靠 Q2 和 Q3。

## 4. Q2：公告后漂移与反转

### 4.1 问题原文

Do investors over-follow authority, leading to post-recommendation drift or reversal?

### 4.2 问题真正问什么

Q2 有两个方向，每个方向有三个时间窗口：

- 上调：+2 至 +60、+2 至 +120、+2 至 +250。
- 下调：同样三个窗口。

只讲下调，或者只讲一个窗口，都不算回答 Q2。Q2 的关键不是“有没有漂移”，而是“漂移之后有没有反转”。如果信息解释成立，价格应该继续朝推荐方向走；如果影响力解释成立，初始反应之后应该回头。

### 4.3 我们的回答

幻灯片标题：

**Star downgrades drift down, then reverse. Star upgrades do not drift.**

中文：明星下调后继续跑输，随后部分反转；明星上调没有差异化漂移。

### 4.4 数字

| Window | Downgrade | Upgrade |
|---|---|---|
| +2 to +60 | -1.64 pp，p = 0.002 | -0.07，p = 0.90 |
| +2 to +120 | -0.76，p = 0.32 | +0.98，p = 0.16 |
| +2 to +250 | +1.53，p = 0.18 | +0.76，p = 0.48 |

读法：下调在前 60 个交易日继续跑输 1.64 个百分点，统计显著；到 120 日缩小到 0.76，不显著；到 250 日变成正 1.53，也不显著。上调三个窗口都不显著。

### 4.5 底层逻辑

第一，漂移从 +2 开始算，公告日反应已经被排除。所以这不是“公告日反应本身”，而是公告日之后的路径。

第二，Q2 的形态不是典型的过度反应。典型过度反应是公告日反应太大，然后反转。我们的下调公告日反应本身并不比非明星大，之后却继续下跌，再部分反转。这更像延迟反应或缓慢扩散，不是“先过度、后修正”。

第三，反转不显著。+1.53 的 p 值是 0.18，不能把“反转”说成已经证实。只能说“方向与部分反转一致”，不能说“我们证明了反转”。

第四，方向上仍然不对称。上调没有漂移，下调有短期漂移。这和 Q1 的“只有上调有公告日溢价”形成一个有意思的对照：价格在公告日对上调反应更大，但在公告后对下调反应更持久。解释时要承认这个不对称，不要强行统一成一个故事。

### 4.6 口播

**English:** Q2 starts at +2, so the announcement reaction is already excluded. Star downgrades continue to underperform by 1.64 percentage points over the next 60 trading days, with a p-value of 0.002. The gap narrows to 0.76 by 120 days and turns positive by 250 days, but neither of those later estimates is significant. Star upgrades show no differential drift at any horizon. The pattern is consistent with delayed following and partial reversal. It is not proof of over-following, because the downgrade announcement reaction itself is not larger.

**中文提示：** 先说“从 +2 开始，公告日反应已排除”，再说“下调 1.64，之后缩小并转正，但反转不显著”。最后主动说“这不是过度反应的证明”，显示你知道边界。

### 4.7 不能说的话

- 不能说“投资者过度反应”。我们的公告日下调反应并不更大，形态更像延迟反应。
- 不能说“反转显著”。+250 的 p 值是 0.18。
- 不能只说下调。上调三个窗口也要报，否则 Q2 只回答了一半。

## 5. Q3：更准，还是只是影响市场

### 5.1 问题原文

Are star analysts' recommendations more accurate ex post, or are they just influencing markets?

### 5.2 问题真正问什么

Q3 有两个准确度指标，必须同时回答：

- 持有收益：跟着推荐方向持有 63、126、252 个交易日，市场调整后是否更赚钱。
- 预测误差：分析师自己的 EPS 预测，和实际 EPS 的绝对误差，是否更小。

持有收益衡量“市场事后是否兑现”，预测误差衡量“分析师本人是否更准”。两个指标都支持明星，才叫稳定的信息优势。一个支持、一个反对，就是混合结论。

### 5.3 我们的回答

幻灯片标题：

**Stars show a short-lived return edge, not better forecasts.**

中文：明星只在短期有持有收益优势，没有更好的预测准确度。

### 5.4 数字

持有收益，明星减非明星，市场调整：

| Horizon | Upgrade | Downgrade |
|---|---|---|
| 3 months | +0.41 pp，p = 0.47 | +1.78，p = 0.001 |
| 6 months | +1.51，p = 0.048 | +1.04，p = 0.19 |
| 12 months | +1.20，p = 0.28 | -1.39，p = 0.23 |

预测误差，明星减非明星，绝对误差：

| Horizon | Upgrade | Downgrade |
|---|---|---|
| FY0 | +0.28，p = 0.002 | +0.46，p = 0.002 |
| FY1 | +0.40，p = 0.009 | +0.94，p < 0.001 |

符号误差没有显著差异：FY0 上调 +0.15，p = 0.12；FY0 下调 +0.18，p = 0.24；FY1 上调 +0.25，p = 0.12；FY1 下调 +0.18，p = 0.46。

### 5.5 底层逻辑

第一，持有收益短期支持明星，但只在特定窗口。上调在 6 个月多 1.51，p = 0.048，刚好在 5% 边界；下调在 3 个月多 1.78，p = 0.001。到 12 个月都不显著，下调甚至转负。这个优势不持续。

第二，预测误差方向相反。四个格子里明星的绝对误差都更大，FY1 下调差 0.94，p < 0.001。如果明星有稳定的信息优势，预测应该更准，而不是更差。

第三，符号误差没有差异，说明不是明星更乐观，而是预测更分散。一个可能的解释是明星覆盖的股票更难、更波动。这个选择效应我们控制不了，所以预测误差只能当描述性证据，不能直接说明星能力更差。

第四，合起来，Q3 的答案是混合的：短期持有收益可能反映一点信息，也可能反映价格压力或注意力；长期没有稳定准确度优势。所以不能说明星“只是影响市场”，也不能说明星“更准”。最准确的表述是“短期有一点优势，长期没有”。

### 5.6 口播

**English:** Q3 has two accuracy metrics, and they point in different directions. Holding returns favor stars at short horizons: plus 1.51 percentage points at six months for upgrades, with a p-value of 0.048, and plus 1.78 at three months for downgrades, with a p-value of 0.001. But neither survives to twelve months. Forecast errors go the other way: star analysts' absolute errors are larger in all four cells, including plus 0.94 at FY1 for downgrades, with a p-value below 0.001. Signed errors do not differ, so this is dispersion, not optimism. The answer is a short-lived return edge, not a stable accuracy advantage.

**中文提示：** 先承认持有收益短期支持明星，再转折到预测误差。不要一上来就说明星更差，否则老师会问“那 6 个月的正收益怎么解释”。

### 5.7 不能说的话

- 不能说明星“更不准”。预测误差更大是描述性的，覆盖难度没有控制。
- 不能说明星“只是影响市场”。短期持有收益确实存在，不能忽略。
- 不能把 6 个月上调的 p = 0.048 说成强结果。聚类后 p = 0.050，刚好在边界。

## 6. Q4：方向与券商层级

### 6.1 问题原文

Does the authority premium differ between upgrades and downgrades, and across broker tiers?

### 6.2 问题真正问什么

Q4 有两个维度：

- 方向：上调与下调的溢价是否一样。
- 券商层级：头部、中部、中小是否一样。

Q4 不是问“有没有溢价”，而是问“溢价在哪里成立”。它是边界条件，不是第五个机制。

### 6.3 我们的回答

幻灯片标题：

**The premium is one-sided. Tier differences are not stable.**

中文：溢价是单边的；券商层级差异不稳定。

### 6.4 数字

方向，带控制的回归：

| 指标 | Upgrade premium | Interaction with downgrade |
|---|---|---|
| CAR[-1,+1] | +0.39，p = 0.021 | -0.29，p = 0.197 |
| CAR[-1,+5] | +0.58，p = 0.014 | -0.70，p = 0.025 |
| Abnormal volume | +0.049，p = 0.009 | -0.057，p = 0.041 |

券商层级：

- 头部明星上调 +0.55，p = 0.017；头部对中部 -0.63，p = 0.072。
- 中部明星下调 +0.62，p = 0.007。
- 滚动层级：23.1% 的事件换层；头部上调 +0.49，p = 0.046；中部下调 +0.33，p = 0.129。
- 小层级只有 2 条明星上调、0 条明星下调，无法估计，排除在交互模型外。

### 6.5 底层逻辑

第一，方向不对称是稳定的。五日窗口和成交量的交互项都显著，说明上调的溢价明显大于下调。三日窗口的交互项 p = 0.197，边际，不要说得太满。

第二，层级看起来有故事，但不稳定。固定层级下，头部上调更大，中部下调更大；滚动层级后，头部上调还在，中部下调掉到 0.33，不显著。层级系数对测量方式敏感，只能当描述。

第三，star 和层级高度共线。小层级几乎没有明星事件，无法把层级和 star 分开。所以不能把层级解释为独立的因果渠道。

第四，Q4 的结论要落在“边界”上：溢价是单边的，层级差异是提示性的，不是稳定结论。

### 6.6 口播

**English:** Q4 asks where the premium lives. On direction, the answer is clear: the premium is one-sided. At the five-day window, the upgrade premium is 0.58, and the interaction with downgrade is minus 0.70, with a p-value of 0.025. Abnormal volume shows the same pattern. On broker tier, the results are suggestive but not stable. The top-tier upgrade premium is 0.55, but a rolling tier reclassifies 23.1% of events, and the mid-tier downgrade effect falls from 0.62 to 0.33 and loses significance. The small tier has only two star upgrades and no star downgrades, so it cannot be estimated. Tier is descriptive, not causal.

**中文提示：** 先说方向稳定，再说层级不稳定。主动说小层级只有 2 条上调、0 条下调，老师就不会追问“为什么没有小层级”。

### 6.7 不能说的话

- 不能说“头部券商更强”。层级是描述性的，滚动后中部下调不显著。
- 不能把小层级当作零效应。它是无法估计，不是没有效应。
- 不能把层级和 star 当成两个独立渠道。两者高度共线。

## 7. 四个回答合起来

| 问题 | 如果信息解释成立 | 如果影响力解释成立 | 我们看到什么 |
|---|---|---|---|
| Q1 公告日 | 更大的价格和成交量反应 | 更大的价格和成交量反应 | 上调两者都更大，下调都没有 |
| Q2 漂移 | 继续朝推荐方向走 | 初始反应后反转 | 下调先继续跑输，再部分反转；上调无漂移 |
| Q3 准确度 | 持有收益和预测都更好 | 没有稳定准确度优势 | 短期持有收益占优，预测误差更大 |
| Q4 边界 | 溢价应对称、跨层级稳定 | 溢价可能单边、层级不稳定 | 单边；层级不稳定 |

合起来：Q1 建立现象，Q2 和 Q3 说明没有稳定信息优势，Q4 说明溢价是单边的、层级的解释不稳定。结论是“影响力为主，短期信息为辅”，不是“纯影响力”，也不是“纯信息”。

## 8. 每页一句话与过渡

| 页 | 一句话 | 过渡到下一页 |
|---|---|---|
| 7 | Q1 是 2x2：价格和成交量一起动，而且只对上调动 | 这个 CAR 溢价是不是全样本都成立？ |
| 8 | CAR 溢价集中在涨跌停事件，短窗口不稳健；成交量没有做同样拆分 | 公告日之后，价格是继续还是回头？ |
| 9 | 下调先继续跑输再部分反转，上调没有漂移 | 如果明星有信息优势，他们的预测应该更准 |
| 10 | 短期持有收益有一点优势，但没有稳定的预测准确度 | 这个溢价是不是对所有方向、所有券商都一样？ |
| 11 | 溢价是单边的，层级差异不稳定 | 这些结果经不经得起换样本和换标准误？ |
| 12 | 停牌、聚类、ST 通过，涨跌停是 CAR 的边界 | 怎么解释这一切？ |
| 13 | 市场跟着标签走，比跟着预测走得更远 | 三句话收束 |

## 9. Q&A 防守

### 9.1 成交量 +0.053 有多大？

0.053 个对数点，约等于成交量高 5%。t = 2.85，同股同日先取均值后是 +0.059，t = 3.19。不是同日重复事件堆出来的。

### 9.2 成交量对涨跌停稳健吗？

没有单独做。涨跌停检验只覆盖 CAR。成交量做过停牌、聚类、同股同日取均值的稳健性，但没有按涨跌停拆分。答辩时要如实说，不能把 CAR 的边界套到 AV 上。

### 9.3 短期持有收益支持明星，为什么还说是影响力？

因为预测误差更大，而且持有收益优势到 12 个月消失。短期优势可能来自价格压力、注意力或短期信息，不是稳定的分析能力。我们的表述是“影响力为主，短期信息为辅”，不是“纯影响力”。

### 9.4 为什么不是过度反应？

下调的公告日反应本身并不比非明星大，之后才继续跑输，再部分反转。这更像延迟反应，不是先过度、后修正。反转也不显著，p = 0.18。我们只说“与部分反转一致”，不说“证明反转”。

### 9.5 为什么层级不稳定？

滚动层级用事件前三年记录重排，23.1% 的事件换层。头部上调还在，但中部下调从 0.62 掉到 0.33，不显著。小层级只有 2 条明星上调、0 条下调，无法估计。star 和层级高度共线。所以层级只能当描述。

### 9.6 多重检验怎么办？

主规格约 30 个，Bonferroni 阈值 0.0017。仍有五个结果显著：上调 CAR[-5,+5]、下调 3 个月持有收益的原始与市场调整版、FY0 下调预测误差、FY1 下调预测误差。边际结果在正文里标了，不当作强结论。

### 9.7 为什么 2018 年用 2017 年榜单？

2018 年新财富投票暂停，网站上标成 2018 的那一页是十五周年特别奖合辑，不是年度行业榜。它只匹配到当年 4.0% 的事件，其他年份是 12.1% 到 14.0%。所以 2018 年沿用 2017 年在任榜单，匹配率回到 13.4%。

## 10. 口径 checklist

- 事件：分析师对一只股票的一次评级调整，不是研报，不是首次覆盖。
- 样本：20,980 条，2,683 只股票，2,171 位分析师，12,131 条上调，8,849 条下调。
- 明星：2,774 条，13.2%。
- CAR：市场调整总收益，事件日是报告日之后第一个交易日，80% 有效观测。
- AV：事件日对数成交量减 [-120,-11] 均值，至少 60 个有效观测。
- 漂移：从 +2 开始，排除公告日反应。
- 持有收益：63、126、252 个交易日，方向调整，市场调整。
- 预测误差：绝对误差除以事件日价格乘 100，FY0 和 FY1，1/99 缩尾。
- 标准误：主表未聚类，稳健性按股票聚类；结论不变。
- 涨跌停：主板 10%，创业板与科创板 20%，北交所 30%，前五个交易日不标记。

## 11. 参考

1. Bonner, S. E., Hugon, A., & Walther, B. R. (2007). Investor Reaction to Celebrity Analysts: The Case of Earnings Forecast Revisions. Journal of Accounting Research, 45(3), 481-513.
2. Fang, L. H., & Yasuda, A. (2009). The Effectiveness of Reputation as a Disciplinary Mechanism in Sell-Side Research. Review of Financial Studies, 22(9), 3735-3777.
3. Fang, L. H., & Yasuda, A. (2014). Are Stars' Opinions Worth More? The Relation Between Analyst Reputation and Recommendation Values. Journal of Financial Services Research, 46(3), 235-269.
4. Loh, R. K., & Stulz, R. M. (2011). When Are Analyst Recommendation Changes Influential? Review of Financial Studies, 24(2), 593-627.
5. Milgram, S. (1963). Behavioral Study of Obedience. Journal of Abnormal and Social Psychology, 67(4), 371-378.
6. Stickel, S. E. (1992). Reputation and Performance Among Security Analysts. Journal of Finance, 47(5), 1811-1836.
7. 李勇, 王莉, 王满仓 (2015). 明星分析师的推荐评级更具价值吗. 投资研究, 34(5), 143-160.

数据来源：iFinD THS_iwencai，2018 至 2024 年评级明细与盈利预测；个股总回报 Dretwd，沪深 300 全收益指数 H00300。完整口径见书面报告 Appendix B。
