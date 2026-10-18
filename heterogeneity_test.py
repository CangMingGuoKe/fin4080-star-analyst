# -*- coding: utf-8 -*-
"""Q4: authority premium by direction and broker tier, with formal interactions.

OLS with stock-clustered standard errors, implemented with numpy so the pipeline
does not depend on statsmodels. Returns and abnormal volume are winsorised at
1/99. The pooled model tests the upgrade-versus-downgrade asymmetry through
star x downgrade; the tier models test star x tier inside each direction.
Output: data/heterogeneity_summary.csv
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
WIN = 0.01


def num(s):
    return pd.to_numeric(s, errors='coerce')


def wins(s):
    lo, hi = np.nanpercentile(s, [100 * WIN, 100 * (1 - WIN)])
    return s.clip(lo, hi)


def fit_cluster(y, X, names, groups):
    """OLS with one-way cluster-robust covariance."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in np.unique(groups):
        idx = groups == g
        s = X[idx].T @ u[idx]
        meat += np.outer(s, s)
    G = int(len(np.unique(groups)))
    N, K = X.shape
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((N - 1) / (N - K))
    return b, V, G


def lin_test(b, V, G, names, terms):
    c = np.zeros(len(names))
    for t in terms:
        c[names.index(t)] = 1.0
    eff = float(c @ b)
    se = float(np.sqrt(c @ V @ c))
    t = eff / se if se > 0 else np.nan
    p = float(2 * stats.t.sf(abs(t), G - 1)) if np.isfinite(t) else np.nan
    return eff, t, p


def design(d, tier=False):
    cols = {'const': np.ones(len(d)), 'star': d['star'].values,
            'tenure': d['tenure'].values, 'loglist': d['loglist'].values}
    if tier:
        cols['mid'] = d['mid'].values
        cols['star_mid'] = (d['star'] * d['mid']).values
    else:
        cols['down'] = d['down'].values
        cols['star_down'] = (d['star'] * d['down']).values
    yr = pd.get_dummies(d['year'].astype(str), prefix='y', drop_first=True).astype(float)
    for c in yr.columns:
        cols[c] = yr[c].values
    names = list(cols.keys())
    X = np.column_stack([cols[n] for n in names])
    return X, names


def main():
    c = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                    dtype={'股票代码': str, '报告日': str}, encoding='utf-8-sig',
                    low_memory=False)
    c['star'] = num(c['star'])
    c['down'] = (c['评级调整方向'].astype(str).str.strip() == '调低').astype(int)
    c['tenure'] = num(c['资历'])
    c['year'] = c['报告日'].astype(str).str[:4]
    c['tier'] = c['券商层级'].astype(str).str.strip().map(
        {'头部': 'top', '中部': 'mid', '中小': 'small'})
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
        d = c.dropna(subset=['y', 'star', 'tenure', 'loglist', 'year']).copy()

        X, names = design(d, tier=False)
        b, V, G = fit_cluster(d['y'].values, X, names, d['股票代码'].values)
        for term, label in [('star', 'star_upgrade'), ('star_down', 'star_x_downgrade')]:
            i = names.index(term)
            rows.append({'model': 'pooled', 'metric': y, 'term': label,
                         'coef': round(float(b[i]), 4),
                         'p': round(float(2 * stats.t.sf(abs(b[i] / np.sqrt(V[i, i])), G - 1)), 4),
                         'n': int(len(d))})
        eff, t, p = lin_test(b, V, G, names, ['star', 'star_down'])
        rows.append({'model': 'pooled', 'metric': y, 'term': 'star_downgrade_total',
                     'coef': round(eff, 4), 'p': round(p, 4), 'n': int(len(d))})

        for di, dd in [('up', d[d['down'] == 0]), ('down', d[d['down'] == 1])]:
            dd = dd[dd['tier'].isin(['top', 'mid'])].copy()
            X, names = design(dd, tier=True)
            b, V, G = fit_cluster(dd['y'].values, X, names, dd['股票代码'].values)
            for term, label in [('star', 'star_top'), ('star_mid', 'star_x_mid')]:
                i = names.index(term)
                rows.append({'model': 'tier_' + di, 'metric': y, 'term': label,
                             'coef': round(float(b[i]), 4),
                             'p': round(float(2 * stats.t.sf(abs(b[i] / np.sqrt(V[i, i])), G - 1)), 4),
                             'n': int(len(dd))})
            eff, t, p = lin_test(b, V, G, names, ['star', 'star_mid'])
            rows.append({'model': 'tier_' + di, 'metric': y, 'term': 'star_mid_total',
                         'coef': round(eff, 4), 'p': round(p, 4), 'n': int(len(dd))})

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DATA, 'heterogeneity_summary.csv'), index=False, encoding='utf-8-sig')
    print(out.to_string(index=False))
    print('\nstar x tier cross-tab')
    print(pd.crosstab([c['tier'], c['down']], c['star']))


if __name__ == '__main__':
    main()
