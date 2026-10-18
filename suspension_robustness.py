# -*- coding: utf-8 -*-
"""Suspension robustness: drop events with any suspension day in the window.

The main specification keeps suspension events and requires 80% valid returns.
This script identifies suspension days from StateCode / Filling in the market
panel, then re-estimates the star-versus-non-star difference after dropping any
event whose window contains a suspension day. Output: data/suspension_robustness.csv
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
WINDOWS = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5), ('CAR_m5_p5', -5, 5),
           ('CAR_0_p120', 0, 120), ('CAR_0_p250', 0, 250)]


def num(s):
    return pd.to_numeric(s, errors='coerce')


def diff_p(a, b):
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) < 30 or len(b) < 30:
        return np.nan, np.nan
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(a.mean() - b.mean()), float(p)


def main():
    ev = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                     dtype={'股票代码': str, '报告日': str, '事件交易日': str},
                     encoding='utf-8-sig', low_memory=False)
    ev['star'] = num(ev['star'])
    ev['事件交易日'] = ev['事件交易日'].astype(str).str.strip()
    ev['股票代码'] = ev['股票代码'].astype(str).str.strip()

    mp = pd.read_csv(os.path.join(DATA, 'market_panel.csv'),
                     dtype={'股票代码': str, '日期': str}, encoding='utf-8-sig',
                     usecols=['股票代码', '日期', 'StateCode', 'Filling'],
                     low_memory=False)
    mp['股票代码'] = mp['股票代码'].astype(str).str.strip()
    mp['日期'] = mp['日期'].astype(str).str.strip()
    susp = set(zip(mp.loc[(mp['StateCode'].astype(str) == '1') |
                          (mp['Filling'].astype(str) == '1'), '股票代码'],
                   mp.loc[(mp['StateCode'].astype(str) == '1') |
                          (mp['Filling'].astype(str) == '1'), '日期']))
    print('suspension pairs', len(susp))

    ix = pd.read_csv(os.path.join(DATA, 'index_panel.csv'), dtype=str, encoding='utf-8-sig')
    cal = sorted(ix['日期'].astype(str).str.strip().unique())
    pos = {d: i for i, d in enumerate(cal)}

    rows = []
    for metric, start, end in WINDOWS:
        keep = []
        dropped = 0
        for _, r in ev.iterrows():
            p = pos.get(r['事件交易日'])
            if p is None:
                keep.append(False)
                continue
            lo, hi = p + start, p + end
            if lo < 0 or hi >= len(cal):
                keep.append(False)
                continue
            days = cal[lo:hi + 1]
            hit = any((r['股票代码'], d) in susp for d in days)
            if hit:
                dropped += 1
            keep.append(not hit)
        keep = np.array(keep)
        full = num(ev[metric]).values
        star = (ev['star'] == 1).values
        dirs = ev['评级调整方向'].astype(str).str.strip().values
        for direction in ['调高', '调低', 'both']:
            dm = np.ones(len(ev), dtype=bool) if direction == 'both' else (dirs == direction)
            n_full_d = int(dm.sum())
            n_kept_d = int((dm & keep).sum())
            n_drop_d = n_full_d - n_kept_d
            d_full, p_full = diff_p(full[star & dm], full[(~star) & dm])
            d_keep, p_keep = diff_p(full[star & dm & keep], full[(~star) & dm & keep])
            rows.append({'direction': direction, 'window': metric,
                         'n_full': n_full_d, 'n_kept': n_kept_d, 'n_dropped': n_drop_d,
                         'pct_dropped': round(100 * n_drop_d / n_full_d, 1) if n_full_d else np.nan,
                         'diff_full': round(d_full, 4) if np.isfinite(d_full) else np.nan,
                         'p_full': round(p_full, 4) if np.isfinite(p_full) else np.nan,
                         'diff_kept': round(d_keep, 4) if np.isfinite(d_keep) else np.nan,
                         'p_kept': round(p_keep, 4) if np.isfinite(p_keep) else np.nan})
            print(rows[-1])

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA, 'suspension_robustness.csv'), index=False, encoding='utf-8-sig')
    print('written', os.path.join(DATA, 'suspension_robustness.csv'))


if __name__ == '__main__':
    main()
