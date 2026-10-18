# -*- coding: utf-8 -*-
"""Robustness: backward-looking rolling broker tiers and Q4 re-estimation.

For an event in year t, the tier uses rating records in t-3 to t-1 only, so no
future information enters the classification. 2018 has no prior year in the data,
so its tier uses 2018 records and is flagged as such. Cut points stay at 50/90
of cumulative records. Outputs:
  data/broker_tier_rolling.csv
  data/heterogeneity_rolling_summary.csv
"""
import os
import glob
import re
import sys
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
sys.path.insert(0, HERE)
from broker_names import canonical_broker
from heterogeneity_test import fit_cluster, lin_test, design, wins, num


def yearly_counts():
    frames = []
    for f in sorted(glob.glob(os.path.join(DATA, 'raw_ratings_*.csv'))):
        y = int(re.search(r'(\d{4})', os.path.basename(f)).group(1))
        d = pd.read_csv(f, dtype=str, encoding='utf-8-sig', usecols=['研究机构简称'])
        c = d['研究机构简称'].dropna().map(
            lambda n: canonical_broker(n, y)).value_counts()
        x = c.rename_axis('机构').reset_index(name='n')
        x['year'] = y
        frames.append(x)
    return pd.concat(frames, ignore_index=True)


def rolling_tiers(Y):
    rows = []
    for t in range(2018, 2025):
        if t == 2018:
            win = Y[Y['year'] == 2018]
            note = 'same_year'
        else:
            win = Y[(Y['year'] >= max(2018, t - 3)) & (Y['year'] <= t - 1)]
            note = 'prior_3y'
        agg = win.groupby('机构')['n'].sum().sort_values(ascending=False)
        cum = agg.cumsum() / agg.sum()
        for k, v in agg.items():
            tier = '头部' if cum[k] <= 0.50 else ('中部' if cum[k] <= 0.90 else '中小')
            rows.append({'年份': t, '机构': k, '窗口记录数': int(v),
                         '累计份额': round(float(cum[k]), 4), '层级_滚动': tier,
                         '窗口': note})
    return pd.DataFrame(rows)


def main():
    Y = yearly_counts()
    R = rolling_tiers(Y)
    R.to_csv(os.path.join(DATA, 'broker_tier_rolling.csv'), index=False, encoding='utf-8-sig')
    print('rolling tiers rows', len(R))

    c = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                    dtype={'股票代码': str, '报告日': str}, encoding='utf-8-sig',
                    low_memory=False)
    c['star'] = num(c['star'])
    c['down'] = (c['评级调整方向'].astype(str).str.strip() == '调低').astype(int)
    c['tenure'] = num(c['资历'])
    c['year'] = c['报告日'].astype(str).str[:4].astype(int)
    c['机构'] = [canonical_broker(n, y)
                 for n, y in zip(c['研究机构简称'].astype(str).str.strip(), c['year'])]
    c = c.merge(R[['年份', '机构', '层级_滚动']], left_on=['year', '机构'],
                right_on=['年份', '机构'], how='left')
    miss = int(c['层级_滚动'].isna().sum())
    print('events without rolling tier', miss)
    print('fixed vs rolling crosstab')
    print(pd.crosstab(c['券商层级'], c['层级_滚动'], dropna=False))
    both = c.dropna(subset=['层级_滚动'])
    changed = 100 * (both['券商层级'].astype(str) != both['层级_滚动'].astype(str)).mean()
    print('events changed tier %.1f%%' % changed)

    c['tier'] = c['层级_滚动'].map({'头部': 'top', '中部': 'mid', '中小': 'small'})
    c['mid'] = (c['tier'] == 'mid').astype(int)
    a = pd.read_csv(os.path.join(DATA, 'analysis_table.csv'),
                    dtype={'股票代码': str, '最新报告日期': str}, encoding='utf-8-sig',
                    usecols=['股票代码', '最新报告日期', '上市天数'])
    a['k'] = a['股票代码'].str.strip() + '|' + a['最新报告日期'].str.strip()
    a = a.drop_duplicates('k')[['k', '上市天数']]
    c['k'] = c['股票代码'].str.strip() + '|' + c['报告日'].str.strip()
    c = c.merge(a, on='k', how='left')
    c['loglist'] = np.log1p(num(c['上市天数']))

    rows = []
    for y in ['CAR_m1_p1', 'CAR_m1_p5', 'AV', 'CAR_p2_p120']:
        c['y'] = wins(num(c[y]))
        d = c.dropna(subset=['y', 'star', 'tenure', 'loglist', 'year', 'tier']).copy()
        X, names = design(d, tier=False)
        b, V, G = fit_cluster(d['y'].values, X, names, d['股票代码'].values)
        for term, label in [('star', 'star_upgrade'), ('star_down', 'star_x_downgrade')]:
            i = names.index(term)
            rows.append({'model': 'pooled_rolling', 'metric': y, 'term': label,
                         'coef': round(float(b[i]), 4),
                         'p': round(float(2 * stats.t.sf(abs(b[i] / np.sqrt(V[i, i])), G - 1)), 4),
                         'n': int(len(d))})
        eff, t, p = lin_test(b, V, G, names, ['star', 'star_down'])
        rows.append({'model': 'pooled_rolling', 'metric': y, 'term': 'star_downgrade_total',
                     'coef': round(eff, 4), 'p': round(p, 4), 'n': int(len(d))})

        for di, dd in [('up', d[d['down'] == 0]), ('down', d[d['down'] == 1])]:
            dd = dd[dd['tier'].isin(['top', 'mid'])].copy()
            X, names = design(dd, tier=True)
            b, V, G = fit_cluster(dd['y'].values, X, names, dd['股票代码'].values)
            for term, label in [('star', 'star_top'), ('star_mid', 'star_x_mid')]:
                i = names.index(term)
                rows.append({'model': 'tier_' + di + '_rolling', 'metric': y, 'term': label,
                             'coef': round(float(b[i]), 4),
                             'p': round(float(2 * stats.t.sf(abs(b[i] / np.sqrt(V[i, i])), G - 1)), 4),
                             'n': int(len(dd))})
            eff, t, p = lin_test(b, V, G, names, ['star', 'star_mid'])
            rows.append({'model': 'tier_' + di + '_rolling', 'metric': y, 'term': 'star_mid_total',
                         'coef': round(eff, 4), 'p': round(p, 4), 'n': int(len(dd))})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA, 'heterogeneity_rolling_summary.csv'), index=False, encoding='utf-8-sig')
    print(out.to_string(index=False))


if __name__ == '__main__':
    main()
