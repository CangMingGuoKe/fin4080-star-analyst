# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 甲的任务（其三）：事件研究引擎

这一步需要乙交来日行情。为了让两边能并行，先把**数据交付格式**定死（乙照这个格式给）：

  data/market_panel.csv  个股日行情，一只股票一天一行
      列：股票代码, 日期, 收盘价, 涨跌幅, 成交量
      说明：日期用 YYYYMMDD 字符串；涨跌幅单位是百分数（如 -1.916933 表示 -1.92%）；
            ST 股用涨跌幅反推（ST 是 5% 限制），不必单独提供 ST 标记。

  data/index_panel.csv   基准指数日行情，一天一行
      列：日期, 收盘价
      说明：建议用沪深 300（000300.SH）或中证全指。

事件表用 build_broker_tier.py 产出的 data/events_with_star.csv，它带着 star、资历与券商层级。
若表里已有 star 列（0/1），结果会按 明星 vs 非明星 分组；没有则只出全样本。

输出：
  data/car_event_level.csv  每个事件一行，各窗口的 CAR 与异常成交量
  data/car_summary.csv      按 star 与 方向 分组的均值与 t 值

用法：python event_study.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

# 事件窗口：(名称, 起, 止)，以事件日为 0
CAR_WINDOWS = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5),
               ('CAR_m5_p5', -5, 5), ('CAR_0_p60', 0, 60),
               ('CAR_0_p120', 0, 120), ('CAR_0_p250', 0, 250)]
# 估计窗口（算正常收益用）
EST = (-120, -11)


def load():
    # 必须读 events_with_star.csv：star、资历、券商层级这三列只在这一版里。
    # 早先读的是 events_clean.csv，结果永远取不到 star，一切分组都退化成全样本。
    need = ['market_panel.csv', 'index_panel.csv', 'events_with_star.csv']
    for f in need:
        p = os.path.join(DATA, f)
        if not os.path.exists(p):
            print('[X] 缺 %s，等乙把数据放进 data/ 再跑' % f)
            return None
    mp = pd.read_csv(os.path.join(DATA, 'market_panel.csv'), dtype={'股票代码': str, '日期': str})
    ix = pd.read_csv(os.path.join(DATA, 'index_panel.csv'), dtype={'日期': str})
    ev = pd.read_csv(os.path.join(DATA, 'events_with_star.csv'), dtype={'股票代码': str}, encoding='utf-8-sig')
    for _c in ('star', '资历', '券商层级'):
        if _c not in ev.columns:
            print('[*] 事件表缺 %s 列，涉及它的分组会退化为全样本' % _c)
    return mp, ix, ev


def prep(mp, ix):
    """把行情整理成 {股票代码: DataFrame(index=日期序)}，并算市场调整收益。"""
    mp = mp.copy()
    mp['涨跌幅'] = pd.to_numeric(mp['涨跌幅'], errors='coerce')
    mp['成交量'] = pd.to_numeric(mp['成交量'], errors='coerce')
    ix = ix.copy()
    ix['mkt'] = pd.to_numeric(ix['收盘价'], errors='coerce').pct_change() * 100.0
    mkt = ix.set_index('日期')['mkt']
    mp['mkt'] = mp['日期'].map(mkt)
    mp['AR'] = mp['涨跌幅'] - mp['mkt']          # 市场调整异常收益（百分点）
    mp['logV'] = np.log(mp['成交量'].where(mp['成交量'] > 0))
    mp = mp.sort_values(['股票代码', '日期'])
    return {k: g.reset_index(drop=True) for k, g in mp.groupby('股票代码')}


def window_car(g, pos, lo, hi):
    a, b = pos + lo, pos + hi
    if a < 0 or b >= len(g):
        return np.nan
    return g['AR'].iloc[a:b + 1].sum()


def abnormal_volume(g, pos):
    a, b = pos + EST[0], pos + EST[1]
    if a < 0 or b >= len(g):
        return np.nan
    base = g['logV'].iloc[a:b + 1].mean()
    cur = g['logV'].iloc[pos]
    return np.nan if (pd.isna(base) or pd.isna(cur)) else cur - base


def main():
    got = load()
    if got is None:
        return
    mp, ix, ev = got
    panel = prep(mp, ix)
    print('行情覆盖股票 = %d，事件数 = %d' % (len(panel), len(ev)))

    rows = []
    for _, e in ev.iterrows():
        g = panel.get(str(e['股票代码']))
        if g is None:
            continue
        hit = g.index[g['日期'] == str(e['最新报告日期'])]
        if len(hit) == 0:
            continue
        pos = int(hit[0])
        rec = {'股票代码': e['股票代码'], '报告日': e['最新报告日期'],
               '研究员姓名': e.get('研究员姓名'), '研究机构简称': e.get('研究机构简称'),
               '评级调整方向': e['评级调整方向'], 'star': e.get('star'),
               'AV': abnormal_volume(g, pos)}
        for nm, lo, hi in CAR_WINDOWS:
            rec[nm] = window_car(g, pos, lo, hi)
        rows.append(rec)

    res = pd.DataFrame(rows)
    if res.empty:
        print('[X] 没有一个事件能对上行情的交易日，检查日期格式与代码格式是否一致')
        return
    res.to_csv(os.path.join(DATA, 'car_event_level.csv'), index=False, encoding='utf-8-sig')
    print('事件级结果 = %d 行 -> car_event_level.csv' % len(res))

    cols = [nm for nm, _, _ in CAR_WINDOWS] + ['AV']
    out = []
    for key, grp in res.groupby(['star', '评级调整方向'], dropna=False):
        for c in cols:
            v = grp[c].dropna()
            if len(v) < 5:
                continue
            t, p = stats.ttest_1samp(v, 0.0)
            out.append({'star': key[0], '方向': key[1], '指标': c,
                        'N': len(v), '均值': round(v.mean(), 4),
                        '中位数': round(v.median(), 4), 't': round(t, 2), 'p': round(p, 4)})
    summ = pd.DataFrame(out)
    summ.to_csv(os.path.join(DATA, 'car_summary.csv'), index=False, encoding='utf-8-sig')
    print()
    print(summ.to_string(index=False) if len(summ) else '（分组样本不足）')
    print('done')


if __name__ == '__main__':
    main()
