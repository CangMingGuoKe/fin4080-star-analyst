# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 事件表清洗

输入：data/raw_ratings_20XX.csv（pull_ifind_ratings.py 抓的原始表）
      data/ref_listing_dates.csv（上市日期，判断 IPO 后六个月）
输出：data/events_1_all_revisions.csv    全部评级调整（调高 + 调低），未做剔除
      data/events_2_clean_sample.csv  按规则剔除后的最终事件样本
      data/events_3_initiations.csv  首次覆盖记录（旁路抽取，不进事件漏斗）

清洗规则（顺序固定，每一步都打印输入/输出/剔除行数，这份日志要写进数据附录）：
  1. 代码与日期规范化
  2. 精确去重
  3. 抽出首次覆盖记录（没有上一次评级），单独存盘，不进事件样本
  4. 剔除上市未满 6 个月
  5. 剔除当前为 ST / *ST 的股票（见下方限制说明）
  6. 生成资历变量（以该分析师首篇报告日为职业生涯起点，算到报告日的年数）

已知限制（写进报告的局限部分，不要藏）：
  · 历史 ST 状态取不到。iFinD 问财对「20XX年ST股票名单」一律返回当前快照，
    基础数据的 ST 指标名也试不通。所以这里只能用当前简称含 ST 的股票做近似剔除，
    会同时误伤（曾 ST 现已摘帽）和漏掉（当时 ST 现已改名）。
    正确做法是用日行情反推：ST 股涨跌停是 5%，从日涨跌幅即可识别 ST 期间。
  · 「上市未满 6 个月」用上市日期加 183 天近似，不另查交易日历。
"""
import glob
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
EVENT_DIRS = ['调高', '调低']
MIN_MONTHS_AFTER_IPO = 183


def step(name, before, after, note=''):
    print('%-26s 输入 %-8d 输出 %-8d 剔除 %-7d %s'
          % (name, before, after, before - after, note))


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'raw_ratings_*.csv')))
    if not files:
        print('[X] data/ 下没有 raw_ratings_*.csv，请先跑 pull_ifind_ratings.py')
        return
    raw = pd.concat([pd.read_csv(f, dtype=str, encoding='utf-8-sig') for f in files],
                    ignore_index=True)
    print('原始评级记录 =', len(raw))

    # 丢掉「研报」列：它在原始数据里整列都是「查看」两个字，那是问财网页的按钮文字，
    # 不是数据。原始文件 raw_ratings_20XX.csv 保持原样，清洗后的表不带它。
    if '研报' in raw.columns:
        raw = raw.drop(columns=['研报'])
        print('已丢弃空壳列「研报」（整列都是网页按钮文字）')
    print()

    # 1 规范化
    n0 = len(raw)
    raw['股票代码'] = raw['股票代码'].astype(str).str.strip()
    bad_code = ~raw['股票代码'].str.match(r'^\d{6}\.(SZ|SH|BJ)$')
    raw = raw[~bad_code]
    step('1 代码格式', n0, len(raw), '剔除异常代码')

    n0 = len(raw)
    raw['报告日'] = pd.to_datetime(raw['最新报告日期'], format='%Y%m%d', errors='coerce')
    raw = raw[raw['报告日'].notna()]
    raw['年份'] = raw['报告日'].dt.year
    step('2 日期解析', n0, len(raw), '剔除日期无法解析')

    # 2 去重
    n0 = len(raw)
    key = ['股票代码', '最新报告日期', '研究员姓名', '研究机构名称', '最新同花顺评级']
    raw = raw.drop_duplicates(subset=key)
    step('3 精确去重', n0, len(raw))

    # 3 首次覆盖。iFinD 把「没有上一次评级」的记录一律标成「未知」，而不是调高或调低，
    #   所以必须在取评级调整之前就从全表里挑，否则永远挑出 0 条（最初就是这么写错的）。
    # 首次覆盖是对全表做的旁路抽取，不改变主漏斗，所以单独打印，不占漏斗步骤号
    a = raw[raw['上次同花顺评级'].isna()
            | raw['上次同花顺评级'].astype(str).str.strip().isin(['', 'nan'])].copy()
    print('（旁注）没有上一次评级的记录 %d 条，属首次覆盖，单独保存，不进事件漏斗' % len(a))

    # 事件表
    ev = raw[raw['评级调整方向'].isin(EVENT_DIRS)].copy()
    step('4 取评级调整', len(raw), len(ev), '只留调高与调低')
    ev_all = ev.copy()      # 未做任何剔除的全量评级调整，供漏斗核对与稳健性
    # 不写「首次覆盖」列：事件表只装调高与调低，而首次覆盖的记录一律被 iFinD 标成
    # 「未知」，所以这一列在事件表里结构性恒为 False，留着只会误导。首次覆盖的记录
    # 已经单独存在 events_3_initiations.csv。

    # 剔除上市未满 6 个月
    lp = os.path.join(DATA, 'ref_listing_dates.csv')
    if os.path.exists(lp):
        ld = pd.read_csv(lp, dtype=str, encoding='utf-8-sig')
        ld['代码'] = ld['股票代码'].astype(str).str.strip()
        ld['上市日'] = pd.to_datetime(ld['新股上市日期'], format='%Y%m%d', errors='coerce')
        ev = ev.merge(ld[['代码', '上市日']], left_on='股票代码', right_on='代码', how='left')
        n0 = len(ev)
        ev['上市天数'] = (ev['报告日'] - ev['上市日']).dt.days
        ev = ev[(ev['上市天数'].isna()) | (ev['上市天数'] >= MIN_MONTHS_AFTER_IPO)]
        step('5 剔除新股', n0, len(ev), '上市未满 %d 天' % MIN_MONTHS_AFTER_IPO)
        ev = ev.drop(columns=['代码'])
    else:
        print('5 剔除新股                   跳过（缺 ref_listing_dates.csv）')

    # 剔除当前 ST（近似，见文件头限制说明）
    n0 = len(ev)
    is_st = ev['股票简称'].astype(str).str.contains('ST', case=False, na=False)
    ev = ev[~is_st]
    step('6 剔除当前 ST（近似）', n0, len(ev), '历史 ST 取不到，见局限说明')

    # 生成资历变量：学术口径，以分析师首篇报告的日期为职业生涯起点，算到事件日的年数。
    # 首报日来自 pull_analyst_tenure.py 抓的 ref_analyst_tenure.csv，往前只能覆盖到
    # 数据源下限 2009 年 6 月；触及该下限的分析师由「触到覆盖起点」列标出。
    # 分位数按事件所在年份内排名，对应「所有活跃分析师按年限排名取分位」的做法。
    tp = os.path.join(DATA, 'ref_analyst_tenure.csv')
    tn = pd.DataFrame(columns=['分析师', '首报日', '报告数', '触到覆盖起点'])
    if os.path.exists(tp):
        tn = pd.read_csv(tp, dtype=str, encoding='utf-8-sig')
        tn['首报日'] = pd.to_datetime(tn['首报日'], format='%Y%m%d', errors='coerce')
        tn = tn[['分析师', '首报日', '报告数', '触到覆盖起点']]
        print('资历口径：学术版，首报日来自 ref_analyst_tenure.csv')
    else:
        print('资历口径：缺 ref_analyst_tenure.csv，资历将为空，请先跑 pull_analyst_tenure.py')
    ev = ev.merge(tn, left_on='研究员姓名', right_on='分析师', how='left').drop(columns=['分析师'])
    ev['首报年份'] = ev['首报日'].dt.year
    ev['资历'] = (ev['报告日'] - ev['首报日']).dt.days / 365.25
    ev['资历分位'] = ev.groupby('年份')['资历'].rank(pct=True).round(4)

    # 落盘
    os.makedirs(DATA, exist_ok=True)
    ev_all = ev_all.merge(tn, left_on='研究员姓名', right_on='分析师', how='left')
    ev_all = ev_all.drop(columns=['分析师'])
    ev_all['首报年份'] = ev_all['首报日'].dt.year
    ev_all['资历'] = (ev_all['报告日'] - ev_all['首报日']).dt.days / 365.25
    ev_all.to_csv(os.path.join(DATA, 'events_1_all_revisions.csv'), index=False, encoding='utf-8-sig')
    ev.to_csv(os.path.join(DATA, 'events_2_clean_sample.csv'), index=False, encoding='utf-8-sig')
    print()
    print('events_1_all_revisions.csv   = %d 行（未剔除）' % len(ev_all))
    print('events_2_clean_sample.csv = %d 行（剔除后）' % len(ev))
    if len(a):
        a.to_csv(os.path.join(DATA, 'events_3_initiations.csv'),
                 index=False, encoding='utf-8-sig')

    print()
    print('最终事件样本 = %d' % len(ev))
    print(ev.groupby(['年份', '评级调整方向']).size().to_string())
    print()
    print('分析师唯一数 = %d，机构唯一数 = %d（全称）/ %d（简称），股票唯一数 = %d'
          % (ev['研究员姓名'].nunique(), ev['研究机构名称'].nunique(),
             ev['研究机构简称'].nunique(), ev['股票代码'].nunique()))
    print('资历变量 非空 = %d，中位数 = %s'
          % (int(ev['资历'].notna().sum()), ev['资历'].median()))
    print('已写出 events_1_all_revisions.csv / events_2_clean_sample.csv')
    print('done')


if __name__ == '__main__':
    main()
