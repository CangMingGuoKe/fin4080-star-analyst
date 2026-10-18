# -*- coding: utf-8 -*-
"""Limit-hit and ST-proxy robustness for the event study.

Reads the market panel and the event-level CAR file, marks daily limit-up /
limit-down days by board, then re-estimates the star-versus-non-star mean
difference after dropping events whose window contains a limit day. A second
block repeats the exercise for an ST proxy built from 5 percent moves on the
main board.

Board thresholds (applied per stock-day, return in percent):
  .BJ                     30
  300/301                 20 from 2020-08-24, 10 before
  688/689                 20
  everything else         10
A day counts as a limit hit when the return is within 0.2 pp below the
threshold. An upper guard of +1.0 pp keeps IPO / resumption days (returns far
above any legal limit) from being labelled as limit hits. The first five panel
rows of every stock are never labelled, because STAR/ChiNext/BSE IPOs and
main-board registration-reform IPOs have no daily limit in their first days.

ST proxy (the data do not identify historical ST status):
  literal_mainboard   main board, |return| in [4.5, 5.5]
  literal_all_boards  any board, |return| in [4.5, 5.5]
  strict_regime       main board, |return| in [4.8, 5.2], the stock's centred
                      31-trading-day window has max |return| <= 5.5 and at
                      least 3 such days, and at least 25 valid returns
The strict variant is a secondary, much tighter proxy added because the
literal band fires on roughly 3 percent of main-board stock-days and would
drop almost every long-window event.

Outputs:
  data/limit_st_robustness.csv
  data/st_proxy_robustness.csv

Console output is ASCII only.
"""
import os
import time

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

METRICS = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5), ('CAR_m5_p5', -5, 5),
           ('CAR_0_p120', 0, 120), ('CAR_0_p250', 0, 250)]
TOL = 0.2          # pp below the nominal limit still counts as a hit
GUARD = 1.0        # pp above the nominal limit: beyond this is IPO / resumption
MIN_GROUP = 30     # minimum observations per star group for a t test


def num(s):
    return pd.to_numeric(s, errors='coerce')


def diff_p(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < MIN_GROUP or len(b) < MIN_GROUP:
        return np.nan, np.nan
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(a.mean() - b.mean()), float(p)


def r4(x):
    return round(float(x), 4) if np.isfinite(x) else np.nan


def main():
    t0 = time.time()
    ix = pd.read_csv(os.path.join(DATA, 'index_panel.csv'), dtype=str,
                     encoding='utf-8-sig')
    cal = sorted(ix['日期'].astype(str).str.strip().unique())
    pos = {d: i for i, d in enumerate(cal)}
    print('[info] trading calendar: %d days' % len(cal))

    mp = pd.read_csv(os.path.join(DATA, 'market_panel.csv'),
                     usecols=['股票代码', '日期', '涨跌幅'],
                     dtype={'股票代码': str, '日期': str},
                     encoding='utf-8-sig', low_memory=False)
    mp.columns = ['code', 'date', 'ret']
    mp['ret'] = num(mp['ret'])
    mp = mp.sort_values(['code', 'date'], kind='mergesort').reset_index(drop=True)
    code = mp['code'].values
    date = mp['date'].values
    ret = mp['ret'].values
    absret = np.abs(ret)
    rank = mp.groupby('code', sort=False).cumcount().values

    c3 = mp['code'].str[:3]
    is_bj = mp['code'].str.endswith('.BJ').values
    is_cy = c3.isin(['300', '301']).values
    is_star = c3.isin(['688', '689']).values
    is_main = ~(is_bj | is_cy | is_star)

    thr = np.full(len(mp), 10.0)
    after_reform = date >= '20200824'
    thr[is_cy & after_reform] = 20.0
    thr[is_star] = 20.0
    thr[is_bj] = 30.0

    first5 = rank < 5
    up = (ret >= thr - TOL) & (ret <= thr + GUARD) & ~first5
    dn = (ret <= -(thr - TOL)) & (ret >= -(thr + GUARD)) & ~first5
    lim = up | dn

    # diagnostics on the guard and the first-five exclusion
    raw_up = (ret >= thr - TOL) & ~first5
    raw_dn = (ret <= -(thr - TOL)) & ~first5
    raw = raw_up | raw_dn
    print('[info] rows %d, codes %d, dates %d'
          % (len(mp), mp['code'].nunique(), mp['date'].nunique()))
    print('[info] limit hits with guard: %d (%.3f%% of stock-days)'
          % (int(lim.sum()), 100.0 * lim.mean()))
    print('[info] hits without upper guard: %d; guard removes %d'
          % (int(raw.sum()), int(raw.sum() - lim.sum())))
    print('[info] first-five rows near threshold not labelled: %d'
          % int((((ret >= thr - TOL) & (ret <= thr + GUARD)) |
                 ((ret <= -(thr - TOL)) & (ret >= -(thr + GUARD))))[first5].sum()))
    for nm, m in (('Main', is_main), ('ChiNext', is_cy), ('STAR', is_star),
                  ('BJ', is_bj)):
        print('[info] limit hits %-8s %7d (%.3f%% of board rows)'
              % (nm, int(lim[m].sum()), 100.0 * lim[m].mean()))

    # ST proxy flags
    st_lit_main = is_main & (absret >= 4.5) & (absret <= 5.5)
    st_lit_all = (absret >= 4.5) & (absret <= 5.5)
    cand = pd.Series(((absret >= 4.8) & (absret <= 5.2)).astype(float))
    gcode = mp['code']
    rollmax = pd.Series(absret).groupby(gcode, sort=False).transform(
        lambda s: s.rolling(31, center=True, min_periods=25).max()).values
    candcnt = cand.groupby(gcode, sort=False).transform(
        lambda s: s.rolling(31, center=True, min_periods=25).sum()).values
    validcnt = pd.Series(np.isfinite(absret).astype(float)).groupby(
        gcode, sort=False).transform(
        lambda s: s.rolling(31, center=True, min_periods=25).sum()).values
    st_strict = (is_main & (cand.values > 0) & (rollmax <= 5.5) &
                 (candcnt >= 3) & (validcnt >= 25))

    for nm, m in (('ST literal mainboard', st_lit_main),
                  ('ST literal all boards', st_lit_all),
                  ('ST strict mainboard', st_strict)):
        print('[info] %-24s %7d stock-days, %4d codes'
              % (nm, int(m.sum()), mp.loc[m, 'code'].nunique()))

    def pairs(mask):
        return set(zip(code[mask], date[mask]))

    sets = {'limit': pairs(lim),
            'st_lit_main': pairs(st_lit_main),
            'st_lit_all': pairs(st_lit_all),
            'st_strict': pairs(st_strict)}
    for k, v in sets.items():
        print('[info] pair set %-12s %d' % (k, len(v)))

    ev = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                     dtype={'股票代码': str, '事件交易日': str},
                     encoding='utf-8-sig', low_memory=False)
    ev['股票代码'] = ev['股票代码'].astype(str).str.strip()
    ev['事件交易日'] = ev['事件交易日'].astype(str).str.strip()
    star = num(ev['star']).values
    dirs = ev['评级调整方向'].astype(str).str.strip().values
    n_ev = len(ev)
    ec = ev['股票代码'].values
    ed = ev['事件交易日'].values
    print('[info] events %d' % n_ev)

    hits = {k: np.zeros((n_ev, len(METRICS)), dtype=bool) for k in sets}
    miss = 0
    for i in range(n_ev):
        p = pos.get(ed[i])
        if p is None:
            miss += 1
            continue
        s0 = max(0, p - 5)
        e0 = min(len(cal) - 1, p + 250)
        if e0 < s0:
            continue
        dts = cal[s0:e0 + 1]
        for k, S in sets.items():
            arr = np.fromiter(((ec[i], d) in S for d in dts), dtype=bool,
                              count=len(dts))
            cs = np.zeros(len(arr) + 1, dtype=np.int32)
            np.cumsum(arr, out=cs[1:])
            for j, (nm, lo, hi) in enumerate(METRICS):
                wl = max(p + lo, s0)
                wh = min(p + hi, e0)
                if wh >= wl and cs[wh - s0 + 1] - cs[wl - s0] > 0:
                    hits[k][i, j] = True
    print('[info] event dates not in calendar: %d' % miss)
    print('[info] window scan done at %.0fs' % (time.time() - t0))

    limit_rows, st_rows = [], []
    for j, (nm, lo, hi) in enumerate(METRICS):
        car = num(ev[nm]).values
        valid = np.isfinite(car)
        for dname in ('调高', '调低', 'both'):
            dm = np.ones(n_ev, dtype=bool) if dname == 'both' else (dirs == dname)
            base = valid & dm
            n_full = int(base.sum())
            d_full, p_full = diff_p(car[base & (star == 1)],
                                    car[base & (star == 0)])
            for k, label in (('limit', None),
                             ('st_lit_main', 'literal_mainboard'),
                             ('st_lit_all', 'literal_all_boards'),
                             ('st_strict', 'strict_regime_mainboard')):
                keep = base & ~hits[k][:, j]
                drop = base & hits[k][:, j]
                n_keep = int(keep.sum())
                n_drop = int(drop.sum())
                d_keep, p_keep = diff_p(car[keep & (star == 1)],
                                        car[keep & (star == 0)])
                row = {'metric': nm, 'direction': dname,
                       'n_full': n_full, 'n_kept': n_keep,
                       'n_dropped': n_drop,
                       'pct_dropped': round(100.0 * n_drop / n_full, 1)
                       if n_full else np.nan,
                       'diff_full': r4(d_full), 'p_full': r4(p_full),
                       'diff_kept': r4(d_keep), 'p_kept': r4(p_keep)}
                if label is None:
                    limit_rows.append(row)
                else:
                    row = dict(row)
                    row['proxy'] = label
                    st_rows.append(row)

    cols = ['metric', 'direction', 'n_full', 'n_kept', 'n_dropped',
            'pct_dropped', 'diff_full', 'p_full', 'diff_kept', 'p_kept']
    lim_out = pd.DataFrame(limit_rows)[cols]
    st_out = pd.DataFrame(st_rows)[['proxy'] + cols]
    lp = os.path.join(DATA, 'limit_st_robustness.csv')
    sp = os.path.join(DATA, 'st_proxy_robustness.csv')
    lim_out.to_csv(lp, index=False, encoding='utf-8-sig')
    st_out.to_csv(sp, index=False, encoding='utf-8-sig')

    print('\n[limit] metric direction n_full n_keep n_drop pct diff_full '
          'p_full diff_keep p_keep')
    for r in limit_rows:
        print('%-10s %-5s %6d %6d %6d %5.1f %8.4f %7.4f %8.4f %7.4f'
              % (r['metric'], 'UP' if r['direction'] == '调高'
                 else ('DOWN' if r['direction'] == '调低' else 'BOTH'),
                 r['n_full'], r['n_kept'], r['n_dropped'], r['pct_dropped'],
                 r['diff_full'], r['p_full'], r['diff_kept'], r['p_kept']))
    print('\n[st proxy] metric proxy direction n_full n_keep n_drop pct '
          'diff_full p_full diff_keep p_keep')
    for r in st_rows:
        print('%-10s %-22s %-5s %6d %6d %6d %5.1f %8.4f %7.4f %8.4f %7.4f'
              % (r['metric'], r['proxy'], 'UP' if r['direction'] == '调高'
                 else ('DOWN' if r['direction'] == '调低' else 'BOTH'),
                 r['n_full'], r['n_kept'], r['n_dropped'], r['pct_dropped'],
                 r['diff_full'], r['p_full'], r['diff_kept'], r['p_kept']))
    print('\n[out] %s' % lp)
    print('[out] %s' % sp)
    print('[done] %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
