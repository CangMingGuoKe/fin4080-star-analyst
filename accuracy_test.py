# -*- coding: utf-8 -*-
"""Q3: post-recommendation accuracy, star versus non-star.

Holding periods of 63, 126 and 252 trading days after the event day. Returns are
computed from the close of the event day, so the announcement reaction is excluded.
Both raw and market-adjusted returns are reported, direction-adjusted (short for
downgrades). A window needs 80% valid trading days, the same rule as event_study_v2.

Output: data/accuracy_summary.csv
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
import sys
sys.path.insert(0, HERE)
from market_data_adapter import load_returns
HORIZONS = (63, 126, 252)
MIN_SHARE = 0.80


def main():
    ev = pd.read_csv(os.path.join(DATA, 'analysis_table.csv'),
                     dtype={'股票代码': str}, encoding='utf-8-sig', low_memory=False)
    mp, ix, source = load_returns(DATA)
    print('行情来源', source)

    cal = sorted(ix['日期'].astype(str).str.strip().unique())
    cal_np = np.array(cal)
    ix = ix.sort_values('日期').drop_duplicates('日期')
    mkt_s = pd.Series(pd.to_numeric(ix['市场收益率'], errors='coerce').values, index=ix['日期'])
    mkt = mkt_s.reindex(pd.Index(cal)).fillna(0).values
    mkt_cum0 = np.concatenate([[0.0], np.cumsum(mkt)])

    mp['涨跌幅'] = pd.to_numeric(mp['涨跌幅'], errors='coerce')
    piv = mp.pivot_table(index='股票代码', columns='日期', values='涨跌幅', aggfunc='first')
    stocks = list(piv.index)
    sidx = {s: i for i, s in enumerate(stocks)}
    R = piv.reindex(columns=cal).values.astype(float)
    print('events %d, stocks %d, calendar %d, missing %.2f%%'
          % (len(ev), len(stocks), len(cal), 100 * np.isnan(R).mean()))

    valid = ~np.isnan(R)
    CS = np.cumsum(np.where(valid, R, 0.0), axis=1)
    CN = np.cumsum(valid, axis=1)
    CS = np.hstack([np.zeros((CS.shape[0], 1)), CS])
    CN = np.hstack([np.zeros((CN.shape[0], 1)), CN])

    report = ev['最新报告日期'].astype(str).str.strip().values
    ed = np.searchsorted(cal_np, report, side='left')
    sign = np.where(ev['评级调整方向'].astype(str).str.strip().values == '调高', 1.0, -1.0)
    star = pd.to_numeric(ev['star'], errors='coerce').values
    rows_i = np.array([sidx.get(s, -1) for s in ev['股票代码'].astype(str).str.strip().values])

    out = []
    for h in HORIZONS:
        start = ed + 1
        end = ed + h + 1
        ok = (rows_i >= 0) & (end <= len(cal))
        cum = np.full(len(ev), np.nan)
        nval = np.zeros(len(ev))
        ii = np.where(ok)[0]
        r = rows_i[ii]
        cum[ii] = CS[r, end[ii]] - CS[r, start[ii]]
        nval[ii] = CN[r, end[ii]] - CN[r, start[ii]]
        raw = np.where(nval / h >= MIN_SHARE, cum, np.nan)
        mk = np.where(ok, mkt_cum0[end] - mkt_cum0[start], np.nan)
        d_raw = sign * raw
        d_adj = sign * (raw - mk)
        for label, series in [('raw', d_raw), ('mktadj', d_adj)]:
            for direction in ['调高', '调低']:
                m = ev['评级调整方向'].astype(str).str.strip().values == direction
                s1 = series[m & (star == 1)]
                s0 = series[m & (star == 0)]
                s1 = s1[~np.isnan(s1)]
                s0 = s0[~np.isnan(s0)]
                if len(s1) < 30 or len(s0) < 30:
                    continue
                t, p = stats.ttest_ind(s1, s0, equal_var=False)
                out.append({
                    'horizon': h, 'measure': label, 'direction': direction,
                    'n_star': len(s1), 'n_nonstar': len(s0),
                    'mean_star': round(float(s1.mean()), 4),
                    'mean_nonstar': round(float(s0.mean()), 4),
                    'diff': round(float(s1.mean() - s0.mean()), 4),
                    'median_star': round(float(np.median(s1)), 4),
                    'median_nonstar': round(float(np.median(s0)), 4),
                    'hit_star': round(float((s1 > 0).mean() * 100), 1),
                    'hit_nonstar': round(float((s0 > 0).mean() * 100), 1),
                    't': round(float(t), 2), 'p': round(float(p), 4),
                })

    res = pd.DataFrame(out)
    path = os.path.join(DATA, 'accuracy_summary.csv')
    res.to_csv(path, index=False, encoding='utf-8-sig')
    print(res.to_string(index=False))
    print('written', path)


if __name__ == '__main__':
    main()
