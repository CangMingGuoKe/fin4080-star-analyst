# -*- coding: utf-8 -*-
"""Cluster-robust standard errors for the FIN4080 rating project.

Three analyses, all of the form  y = a + b * star + e  estimated by OLS with
one-way cluster-robust standard errors:

  1. Event study: CAR_m1_p1, CAR_m1_p5, CAR_m5_p5, CAR_p2_p120 and AV,
     by rating direction; clustered by stock, plus a stock-day robustness
     version.
  2. Post-recommendation holding returns at 63/126/252 trading days,
     recomputed with the exact rules of accuracy_test.py (event-day close as
     the starting point, direction adjustment, market adjustment, 80% valid
     trading days); clustered by stock.
  3. Absolute EPS forecast errors FY0/FY1 from forecast_error_event.csv,
     by rating direction; clustered by stock.

statsmodels is not used. OLS and the cluster sandwich are implemented in numpy.
Finite-sample correction is the usual  G/(G-1) * (N-1)/(N-K); p-values use a
t distribution with G-1 degrees of freedom. For two-group models the slope is
exactly the difference in group means.

Output: data/cluster_robustness.csv
Console: ASCII-only comparison checks against the existing summaries.

Usage:  python cluster_robustness.py [--selftest]
"""
import io
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
HORIZONS = (63, 126, 252)
MIN_SHARE = 0.80

EVENT_METRICS = ['CAR_m1_p1', 'CAR_m1_p5', 'CAR_m5_p5', 'CAR_p2_p120', 'AV']


# ----------------------------------------------------------------------------
# OLS + one-way cluster-robust covariance
# ----------------------------------------------------------------------------
def ols_core(y, X):
    """Return (beta, residual, inv(X'X), n, k)."""
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    return beta, e, XtX_inv, n, k


def cluster_vcov(X, e, XtX_inv, groups):
    """One-way cluster sandwich with the G/(G-1)*(N-1)/(N-K) correction."""
    codes, uniq = pd.factorize(pd.Series(np.asarray(groups)), sort=False)
    G = int(len(uniq))
    n, k = X.shape
    scores = X * e[:, None]
    S = np.zeros((G, k))
    np.add.at(S, codes, scores)
    meat = S.T @ S
    V = XtX_inv @ meat @ XtX_inv
    if G > 1 and n > k:
        V = V * (G / (G - 1.0)) * ((n - 1.0) / (n - k))
    return V, G


def unclustered_vcov(X, e, XtX_inv):
    n, k = X.shape
    if n <= k:
        return np.full((k, k), np.nan)
    sigma2 = float(e @ e) / (n - k)
    return sigma2 * XtX_inv


def fit_cluster(y, x, groups):
    """OLS of y on [1, x]; return slope and both clustered/unclustered SEs."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    X = np.column_stack([np.ones(len(y)), x])
    beta, e, XtX_inv, n, k = ols_core(y, X)
    V, G = cluster_vcov(X, e, XtX_inv, groups)
    se_c = float(np.sqrt(V[1, 1]))
    t_c = float(beta[1] / se_c) if se_c > 0 else np.nan
    p_c = float(2 * stats.t.sf(abs(t_c), G - 1)) if np.isfinite(t_c) else np.nan
    V0 = unclustered_vcov(X, e, XtX_inv)
    se_u = float(np.sqrt(V0[1, 1]))
    t_u = float(beta[1] / se_u) if se_u > 0 else np.nan
    p_u = float(2 * stats.t.sf(abs(t_u), n - k)) if np.isfinite(t_u) else np.nan
    return {
        'coef': float(beta[1]), 'se_cluster': se_c, 't': t_c, 'p': p_c,
        'n': int(n), 'n_clusters': G,
        'unclustered_coef': float(beta[1]), 'se_unclustered': se_u,
        'unclustered_p': p_u,
    }


def row(analysis, metric, direction, res, horizon='', cluster_var='股票代码',
        ref_coef=np.nan, ref_p=np.nan, ref_n='', note=''):
    return {
        'analysis': analysis, 'metric': metric, 'direction': direction,
        'horizon': horizon,
        'coef': res['coef'], 'se_cluster': res['se_cluster'],
        't': res['t'], 'p': res['p'], 'n': res['n'],
        'n_clusters': res['n_clusters'], 'cluster_var': cluster_var,
        'unclustered_coef': res['unclustered_coef'],
        'se_unclustered': res['se_unclustered'],
        'unclustered_p': res['unclustered_p'],
        'ref_coef': ref_coef, 'ref_p': ref_p, 'ref_n': ref_n, 'note': note,
    }


# ----------------------------------------------------------------------------
# 1. Event study
# ----------------------------------------------------------------------------
def run_event_study(ev, cs):
    rows = []
    checks = []
    star = pd.to_numeric(ev['star'], errors='coerce')
    for direction in ['调高', '调低']:
        dm = ev['评级调整方向'].astype(str).str.strip() == direction
        for metric in EVENT_METRICS:
            y = pd.to_numeric(ev[metric], errors='coerce')
            keep = dm & y.notna() & star.isin([0, 1])
            sub = ev.loc[keep, ['股票代码', '事件交易日']].copy()
            sub['y'] = y[keep].values
            sub['star'] = star[keep].values
            ref = cs[(cs['检验'] == '组间t(明星-非明星)') &
                     (cs['方向'] == direction) & (cs['指标'] == metric)]
            if len(ref):
                ref = ref.iloc[0]
                rn = str(ref['N']).split('/')
                ref_coef, ref_p = float(ref['均值']), float(ref['p'])
                ref_n = str(ref['N'])
                n_star_ref, n_non = int(rn[0]), int(rn[1])
            else:
                ref_coef = ref_p = np.nan
                ref_n = ''
                n_star_ref = n_non = -1

            res = fit_cluster(sub['y'].values, sub['star'].values,
                              sub['股票代码'].values)
            rows.append(row('event_study', metric, direction, res,
                            ref_coef=ref_coef, ref_p=ref_p, ref_n=ref_n))

            n1 = int((sub['star'] == 1).sum())
            n0 = int((sub['star'] == 0).sum())
            checks.append({
                'analysis': 'event_study', 'metric': metric,
                'direction': direction, 'n': res['n'],
                'n1': n1, 'n0': n0, 'ref_n1': n_star_ref, 'ref_n0': n_non,
                'coef': res['coef'], 'ref_coef': ref_coef,
                'n_ok': (n1 == n_star_ref and n0 == n_non),
                'coef_absdiff': abs(res['coef'] - ref_coef),
            })

            key = sub['股票代码'].astype(str) + '|' + \
                sub['事件交易日'].astype(str)
            res_sd = fit_cluster(sub['y'].values, sub['star'].values, key.values)
            rows.append(row('event_study_stockday', metric, direction, res_sd,
                            cluster_var='股票代码+事件交易日',
                            note='robustness: stock-day clusters, same N and coef'))
    return rows, checks


# ----------------------------------------------------------------------------
# 2. Holding returns, exact rules of accuracy_test.py
# ----------------------------------------------------------------------------
def load_holding_returns(ev):
    """Return dict horizon -> (d_raw, d_adj) aligned with ev rows."""
    codes = set(ev['股票代码'].astype(str).str.strip())
    ix = pd.read_csv(os.path.join(DATA, 'index_panel.csv'), dtype=str,
                     encoding='utf-8-sig')
    cal = sorted(ix['日期'].astype(str).str.strip().unique())
    cal_int = np.array([int(d) for d in cal], dtype=np.int64)
    ix['收盘价'] = pd.to_numeric(ix['收盘价'], errors='coerce')
    ix['日期'] = ix['日期'].astype(str).str.strip()
    ix = ix.sort_values('日期').drop_duplicates('日期')
    mkt_s = pd.Series((ix['收盘价'].pct_change() * 100).values, index=ix['日期'])
    mkt = mkt_s.reindex(pd.Index(cal)).fillna(0).values
    mkt_cum0 = np.concatenate([[0.0], np.cumsum(mkt)])

    parts = []
    n_raw = 0
    for ch in pd.read_csv(os.path.join(DATA, 'market_panel.csv'),
                          dtype={'股票代码': str, '日期': 'int64', '涨跌幅': 'float64'},
                          encoding='utf-8-sig',
                          usecols=['股票代码', '日期', '涨跌幅'],
                          chunksize=1_000_000):
        n_raw += len(ch)
        ch = ch[ch['股票代码'].isin(codes)]
        if len(ch):
            ch['股票代码'] = ch['股票代码'].astype('category')
            parts.append(ch)
    mp = pd.concat(parts, ignore_index=True)
    del parts
    print('  market_panel rows read %d, kept %d for %d event stocks'
          % (n_raw, len(mp), len(codes)))

    piv = mp.pivot_table(index='股票代码', columns='日期', values='涨跌幅',
                         aggfunc='first')
    stocks = list(piv.index)
    sidx = {s: i for i, s in enumerate(stocks)}
    R = piv.reindex(columns=cal_int).values.astype(float)
    del mp, piv

    valid = ~np.isnan(R)
    CS = np.cumsum(np.where(valid, R, 0.0), axis=1)
    CN = np.cumsum(valid, axis=1)
    CS = np.hstack([np.zeros((CS.shape[0], 1)), CS])
    CN = np.hstack([np.zeros((CN.shape[0], 1)), CN])

    report = ev['最新报告日期'].astype(str).str.strip().values
    report_int = np.array([int(s) for s in report], dtype=np.int64)
    ed = np.searchsorted(cal_int, report_int, side='left')
    sign = np.where(ev['评级调整方向'].astype(str).str.strip().values == '调高',
                    1.0, -1.0)
    rows_i = np.array([sidx.get(s, -1)
                       for s in ev['股票代码'].astype(str).str.strip().values])

    out = {}
    n_oob = 0
    for h in HORIZONS:
        start = ed + 1
        end = ed + h + 1
        ok = (rows_i >= 0) & (end <= len(cal))
        n_oob += int(((rows_i >= 0) & (end > len(cal))).sum())
        cum = np.full(len(ev), np.nan)
        nval = np.zeros(len(ev))
        ii = np.where(ok)[0]
        r = rows_i[ii]
        cum[ii] = CS[r, end[ii]] - CS[r, start[ii]]
        nval[ii] = CN[r, end[ii]] - CN[r, start[ii]]
        raw = np.where(nval / h >= MIN_SHARE, cum, np.nan)
        mk = np.full(len(ev), np.nan)
        mk[ii] = mkt_cum0[end[ii]] - mkt_cum0[start[ii]]
        out[h] = (sign * raw, sign * (raw - mk))
    if n_oob:
        print('  WARNING: %d event-horizons extend past the calendar' % n_oob)
    return out


def run_holding(holding, ev, acc):
    rows, checks = [], []
    star = pd.to_numeric(ev['star'], errors='coerce').values
    direction = ev['评级调整方向'].astype(str).str.strip().values
    for h in HORIZONS:
        for measure, series in [('raw', holding[h][0]),
                                ('mktadj', holding[h][1])]:
            for d in ['调高', '调低']:
                m1 = (direction == d) & (star == 1)
                m0 = (direction == d) & (star == 0)
                s1 = series[m1]
                s0 = series[m0]
                v1 = ~np.isnan(s1)
                v0 = ~np.isnan(s0)
                s1 = s1[v1]
                s0 = s0[v0]
                g1 = ev.loc[m1, '股票代码'].values[v1]
                g0 = ev.loc[m0, '股票代码'].values[v0]
                ref = acc[(acc['horizon'] == h) & (acc['measure'] == measure) &
                          (acc['direction'] == d)]
                if len(ref):
                    ref = ref.iloc[0]
                    ref_coef, ref_p = float(ref['diff']), float(ref['p'])
                    ref_n = '%d/%d' % (int(ref['n_star']), int(ref['n_nonstar']))
                    ref_ms, ref_mn = float(ref['mean_star']), float(ref['mean_nonstar'])
                else:
                    ref_coef = ref_p = ref_ms = ref_mn = np.nan
                    ref_n = ''
                yy = np.concatenate([s1, s0])
                xx = np.concatenate([np.ones(len(s1)), np.zeros(len(s0))])
                gg = np.concatenate([g1, g0])
                res = fit_cluster(yy, xx, gg)
                rows.append(row('holding_return', measure, d, res,
                                horizon=h, ref_coef=ref_coef,
                                ref_p=ref_p, ref_n=ref_n))
                checks.append({
                    'analysis': 'holding_return', 'metric': measure,
                    'direction': d, 'horizon': h,
                    'n1': len(s1), 'n0': len(s0),
                    'ref_n1': int(ref['n_star']) if len(ref) else -1,
                    'ref_n0': int(ref['n_nonstar']) if len(ref) else -1,
                    'mean1': float(s1.mean()), 'mean0': float(s0.mean()),
                    'ref_mean1': ref_ms, 'ref_mean0': ref_mn,
                    'coef': float(s1.mean() - s0.mean()),
                    'ref_coef': ref_coef,
                    'diff_star': abs(float(s1.mean()) - ref_ms),
                    'diff_nonstar': abs(float(s0.mean()) - ref_mn),
                    'coef_absdiff': abs(float(s1.mean() - s0.mean()) - ref_coef),
                    'n_ok': (len(s1) == (int(ref['n_star']) if len(ref) else -1)
                             and len(s0) == (int(ref['n_nonstar']) if len(ref) else -1)),
                })
    return rows, checks


# ----------------------------------------------------------------------------
# 3. Forecast errors
# ----------------------------------------------------------------------------
def run_forecast(fe, fs):
    rows, checks = [], []
    star = pd.to_numeric(fe['star'], errors='coerce')
    for metric, label in [('e0', 'FY0_abs'), ('e1', 'FY1_abs')]:
        y_all = pd.to_numeric(fe[metric], errors='coerce')
        for d in ['调高', '调低']:
            dm = fe['评级调整方向'].astype(str).str.strip() == d
            keep = dm & y_all.notna() & star.isin([0, 1])
            sub = fe.loc[keep, ['股票代码']].copy()
            sub['y'] = y_all[keep].values
            sub['star'] = star[keep].values
            ref = fs[(fs['metric'] == label) & (fs['direction'] == d)]
            if len(ref):
                ref = ref.iloc[0]
                ref_coef, ref_p = float(ref['diff']), float(ref['p'])
                ref_n = '%d/%d' % (int(ref['n_star']), int(ref['n_nonstar']))
            else:
                ref_coef = ref_p = np.nan
                ref_n = ''

            # (a) raw errors
            res = fit_cluster(sub['y'].values, sub['star'].values,
                              sub['股票代码'].values)
            rows.append(row('forecast_error', label, d, res,
                            ref_coef=np.nan, ref_p=np.nan,
                            note='raw absolute error, no winsorisation'))

            # (b) winsorised at 1/99 within metric-direction, as in
            # forecast_error.py, so the unclustered coefficient reproduces the
            # existing summary exactly
            s1 = sub.loc[sub['star'] == 1, 'y'].values
            s0 = sub.loc[sub['star'] == 0, 'y'].values
            lo, hi = np.nanpercentile(np.concatenate([s1, s0]), [1, 99])
            yw = np.clip(sub['y'].values, lo, hi)
            resw = fit_cluster(yw, sub['star'].values, sub['股票代码'].values)
            rows.append(row('forecast_error', label + '_w1_99', d, resw,
                            ref_coef=ref_coef, ref_p=ref_p, ref_n=ref_n,
                            note='winsorised 1/99 within metric-direction, '
                                 'matches forecast_error.py'))
            checks.append({
                'analysis': 'forecast_error', 'metric': label, 'direction': d,
                'n1': int((sub['star'] == 1).sum()),
                'n0': int((sub['star'] == 0).sum()),
                'ref_n1': int(ref['n_star']) if len(ref) else -1,
                'ref_n0': int(ref['n_nonstar']) if len(ref) else -1,
                'raw_coef': res['coef'],
                'w_coef': resw['coef'], 'ref_coef': ref_coef,
                'raw_absdiff': abs(res['coef'] - ref_coef),
                'w_absdiff': abs(resw['coef'] - ref_coef),
                'n_ok': (int((sub['star'] == 1).sum()) ==
                         (int(ref['n_star']) if len(ref) else -1) and
                         int((sub['star'] == 0).sum()) ==
                         (int(ref['n_nonstar']) if len(ref) else -1)),
            })
    return rows, checks


# ----------------------------------------------------------------------------
# Self-test of the covariance implementation
# ----------------------------------------------------------------------------
def selftest():
    rng = np.random.default_rng(20261018)
    G, m = 40, 30
    g = np.repeat(np.arange(G), m)
    x = rng.integers(0, 2, size=G * m).astype(float)
    u = rng.normal(0, 1.0, G)[g]
    y = 1.0 + 2.0 * x + u + rng.normal(0, 0.5, G * m)
    res = fit_cluster(y, x, g)
    X = np.column_stack([np.ones(len(y)), x])
    beta, e, XtX_inv, n, k = ols_core(y, X)
    # loop-based meat, independent of the vectorised path
    meat = np.zeros((2, 2))
    for j in range(G):
        mj = g == j
        s = X[mj].T @ e[mj]
        meat += np.outer(s, s)
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1.0)) * ((n - 1.0) / (n - k))
    se = np.sqrt(V[1, 1])
    # pooled two-sample t should reproduce the unclustered OLS t
    t_pool, _ = stats.ttest_ind(y[x == 1], y[x == 0], equal_var=True)
    ok1 = abs(se - res['se_cluster']) < 1e-10
    ok2 = abs(abs(t_pool) - abs(res['coef'] / res['se_unclustered'])) < 1e-8
    ok3 = abs(res['coef'] - (y[x == 1].mean() - y[x == 0].mean())) < 1e-12
    print('selftest cluster SE vs loop: %s' % ('PASS' if ok1 else 'FAIL'))
    print('selftest pooled t vs OLS t: %s' % ('PASS' if ok2 else 'FAIL'))
    print('selftest coef = mean diff: %s' % ('PASS' if ok3 else 'FAIL'))
    return ok1 and ok2 and ok3


# ----------------------------------------------------------------------------
def main():
    print('== event study ==')
    ev = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                     dtype={'股票代码': str, '报告日': str, '事件交易日': str},
                     encoding='utf-8-sig', low_memory=False)
    cs = pd.read_csv(os.path.join(DATA, 'car_summary.csv'), encoding='utf-8-sig')
    ev_rows, ev_checks = run_event_study(ev, cs)
    bad = [c for c in ev_checks if not c['n_ok'] or c['coef_absdiff'] > 0.0002]
    print('  comparisons %d, N/coef mismatches %d, max |coef-ref| %.6f'
          % (len(ev_checks), len(bad),
             max(c['coef_absdiff'] for c in ev_checks if np.isfinite(c['coef_absdiff']))))
    for c in bad:
        print('  CHECK FAIL %s %s n=%d/%d ref_n=%d/%d coef=%.6f ref=%.6f'
              % (c['metric'], 'UP' if c['direction'] == '调高' else 'DOWN',
                 c['n1'], c['n0'], c['ref_n1'], c['ref_n0'],
                 c['coef'], c['ref_coef']))
    del ev

    print('== holding returns ==')
    at = pd.read_csv(os.path.join(DATA, 'analysis_table.csv'),
                     dtype={'股票代码': str, '最新报告日期': str},
                     encoding='utf-8-sig', low_memory=False,
                     usecols=['股票代码', '最新报告日期', '评级调整方向', 'star'])
    acc = pd.read_csv(os.path.join(DATA, 'accuracy_summary.csv'),
                      encoding='utf-8-sig')
    holding = load_holding_returns(at)
    h_rows, h_checks = run_holding(holding, at, acc)
    bad_h = [c for c in h_checks
             if (not c['n_ok']) or c['diff_star'] > 0.01 or
             c['diff_nonstar'] > 0.01 or c['coef_absdiff'] > 0.01]
    print('  comparisons %d, mismatches > 0.01pp or N %d, max |mean_star-ref| %.6f,'
          ' max |mean_nonstar-ref| %.6f'
          % (len(h_checks), len(bad_h),
             max(c['diff_star'] for c in h_checks),
             max(c['diff_nonstar'] for c in h_checks)))
    for c in bad_h:
        print('  CHECK FAIL h=%d %s %s n=%d/%d ref_n=%d/%d mean1=%.4f ref=%.4f '
              'mean0=%.4f ref=%.4f'
              % (c['horizon'], c['metric'],
                 'UP' if c['direction'] == '调高' else 'DOWN',
                 c['n1'], c['n0'], c['ref_n1'], c['ref_n0'],
                 c['mean1'], c['ref_mean1'], c['mean0'], c['ref_mean0']))
    del at

    print('== forecast errors ==')
    fe = pd.read_csv(os.path.join(DATA, 'forecast_error_event.csv'),
                     dtype={'股票代码': str}, encoding='utf-8-sig')
    fs = pd.read_csv(os.path.join(DATA, 'forecast_error_summary.csv'),
                     encoding='utf-8-sig')
    f_rows, f_checks = run_forecast(fe, fs)
    bad_f = [c for c in f_checks
             if (not c['n_ok']) or c['w_absdiff'] > 0.0002]
    print('  comparisons %d, N/winsorised-coef mismatches %d, max |w-ref| %.6f'
          % (len(f_checks), len(bad_f),
             max(c['w_absdiff'] for c in f_checks)))
    for c in bad_f:
        print('  CHECK FAIL %s %s n=%d/%d ref_n=%d/%d w=%.6f ref=%.6f'
              % (c['metric'], 'UP' if c['direction'] == '调高' else 'DOWN',
                 c['n1'], c['n0'], c['ref_n1'], c['ref_n0'],
                 c['w_coef'], c['ref_coef']))

    all_rows = ev_rows + h_rows + f_rows
    out = pd.DataFrame(all_rows)
    path = os.path.join(DATA, 'cluster_robustness.csv')
    out.to_csv(path, index=False, encoding='utf-8-sig', float_format='%.10g')
    print('written %s (%d rows)' % (path, len(out)))

    print('\n== key clustered results ==')
    for _, r in out.iterrows():
        if r['analysis'] == 'event_study' or r['analysis'] == 'forecast_error' \
                or (r['analysis'] == 'holding_return' and r['metric'] == 'mktadj'):
            print('%-22s %-14s %-18s h=%-3s coef=%8.4f se_c=%6.4f t=%6.2f '
                  'p=%.4f n=%d G=%d unc_p=%.4f'
                  % (r['analysis'], r['metric'], r['direction'],
                     str(r['horizon']), r['coef'], r['se_cluster'], r['t'],
                     r['p'], r['n'], r['n_clusters'], r['unclustered_p']))


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(0 if selftest() else 1)
    main()
