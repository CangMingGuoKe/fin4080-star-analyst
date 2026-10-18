# -*- coding: utf-8 -*-
"""Independent replication check for the FIN4080 Project 10 outputs.

This script deliberately does not import or call any function from the existing
pipeline. It rebuilds the trading calendar, the event-day map, the CAR windows,
the holding-period returns and the forecast match from the raw inputs.

Reads (never writes):
    data/analysis_table.csv
    data/market_panel.csv
    data/index_panel.csv
    data/car_event_level.csv          (reference)
    data/accuracy_summary.csv         (reference)
    data/raw_forecast_2018..2024.csv
    data/ref_actual_eps.csv
    data/forecast_error_event.csv     (reference)

Writes:
    data/replication_check.csv

Definitions used here:
  * trading calendar = sorted unique dates in index_panel.csv
  * event day = first trading day >= report date
  * abnormal return = stock pct change - index pct change, both in percent
  * CAR = arithmetic sum of daily abnormal returns in the window
  * window valid if event day is valid and >=80% of positions are valid
  * holding return = arithmetic sum of daily pct changes from event day close
    to h trading days later; market adjustment subtracts the summed index return
  * direction adjustment = +1 for upgrade, -1 for downgrade
  * forecast error = |forecast EPS - realised EPS| / event-day close * 100

Console output is ASCII only.
"""
import os
import glob
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data')
OUT_CSV = os.path.join(DATA, 'replication_check.csv')

MIN_SHARE = 0.80
CAR_WINDOWS = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5),
               ('CAR_m5_p5', -5, 5), ('CAR_p2_p120', 2, 120)]
HORIZONS = (63, 126, 252)
TOL = 1e-6


def log(msg):
    print(msg, flush=True)


def read_csv(path, **kwargs):
    return pd.read_csv(path, encoding='utf-8-sig', low_memory=False, **kwargs)


def to_num(s):
    return pd.to_numeric(s, errors='coerce')


def compare_arrays(reference, replication):
    """Compare two float vectors. NaN==NaN counts as agreement."""
    p = np.asarray(reference, dtype='float64')
    r = np.asarray(replication, dtype='float64')
    if p.shape != r.shape:
        raise ValueError('shape mismatch: %s vs %s' % (p.shape, r.shape))
    pn = np.isnan(p)
    rn = np.isnan(r)
    both = ~(pn | rn)
    d = np.abs(p[both] - r[both])
    return {
        'n_compared': int(both.sum()),
        'n_nan_mismatch': int((pn ^ rn).sum()),
        'max_abs_diff': float(d.max()) if d.size else float('nan'),
        'mean_abs_diff': float(d.mean()) if d.size else float('nan'),
        'n_over_tol': int((d > TOL).sum()),
    }


def main():
    t0 = time.time()
    rows_out = []

    def add(section, key, metric, reference=np.nan, replication=np.nan,
            diff=np.nan, n_diff=np.nan, max_abs_diff=np.nan,
            mean_abs_diff=np.nan, n_over_tol=np.nan, n_nan_mismatch=np.nan,
            n_compared=np.nan, note=''):
        rows_out.append({
            'section': section, 'key': key, 'metric': metric,
            'reference': reference, 'replication': replication, 'diff': diff,
            'n_diff': n_diff, 'max_abs_diff': max_abs_diff,
            'mean_abs_diff': mean_abs_diff, 'n_over_tol': n_over_tol,
            'n_nan_mismatch': n_nan_mismatch, 'n_compared': n_compared,
            'note': note,
        })

    # ---------------------------------------------------------------- inputs
    log('[1/5] reading event table and index calendar')
    ev = read_csv(os.path.join(DATA, 'analysis_table.csv'),
                  dtype={'股票代码': str, '最新报告日期': 'int64'})
    ev['股票代码'] = ev['股票代码'].astype(str).str.strip()
    ev['report_day'] = ev['最新报告日期'].astype('int64')
    ev['direction'] = ev['评级调整方向'].astype(str).str.strip()
    ev['star_num'] = to_num(ev['star'])
    ev['year_num'] = to_num(ev['年份'])
    n_ev = len(ev)

    ix = read_csv(os.path.join(DATA, 'index_panel.csv'),
                  dtype={'日期': 'int64'})
    ix['日期'] = ix['日期'].astype('int64')
    ix['close'] = to_num(ix['收盘价'])
    ix = ix.sort_values('日期').drop_duplicates('日期')
    cal = ix['日期'].to_numpy(dtype='int64')
    n_days = len(cal)
    cal_arr = cal.astype('U8')

    # index return in percent; first day has no return
    ix_ret = ix['close'].pct_change() * 100.0
    ix_ret_arr = ix_ret.to_numpy(dtype='float64')
    # market series used for holding returns: first day set to zero, as in the
    # reference implementation (there are no events that need the first day)
    ix_ret_hold = np.nan_to_num(ix_ret_arr, nan=0.0)
    ix_cum_hold = np.concatenate([[0.0], np.cumsum(ix_ret_hold)])

    log('    events=%d calendar=%d (%d..%d)' %
        (n_ev, n_days, cal[0], cal[-1]))

    # ------------------------------------------------------------ market data
    log('[2/5] reading market panel (usecols: code, date, pct change, close)')
    mp = read_csv(os.path.join(DATA, 'market_panel.csv'),
                  dtype={'股票代码': str, '日期': 'int64'},
                  usecols=['股票代码', '日期', '涨跌幅', '收盘价'])
    mp['股票代码'] = mp['股票代码'].astype(str).str.strip()
    mp['日期'] = mp['日期'].astype('int64')
    mp['ret'] = to_num(mp['涨跌幅'])
    mp['close'] = to_num(mp['收盘价'])
    log('    market rows=%d stocks=%d dates=%d' %
        (len(mp), mp['股票代码'].nunique(), mp['日期'].nunique()))

    ret_df = mp.pivot(index='股票代码', columns='日期', values='ret')
    ret_df = ret_df.reindex(columns=cal)
    close_df = mp.pivot(index='股票代码', columns='日期', values='close')
    close_df = close_df.reindex(columns=cal)
    stocks = ret_df.index.tolist()
    R = ret_df.to_numpy(dtype='float64')
    P = close_df.to_numpy(dtype='float64')
    del ret_df, close_df, mp
    log('    return matrix %d x %d' % R.shape)

    sidx = pd.Series(np.arange(len(stocks)), index=stocks)
    ev_stock = sidx.reindex(ev['股票代码']).to_numpy()
    missing_stock = int(pd.isna(ev_stock).sum())
    ev_stock = np.where(pd.isna(ev_stock), -1, ev_stock).astype('int64')

    # event position: first calendar date >= report date
    pos = np.searchsorted(cal, ev['report_day'].to_numpy(dtype='int64'),
                          side='left')
    pos_ok = pos < n_days
    event_day = np.full(n_ev, '', dtype=object)
    event_day[pos_ok] = cal_arr[pos[pos_ok]].astype(object)

    # event-level close, used by the forecast error
    price_ev = np.full(n_ev, np.nan)
    pm = (ev_stock >= 0) & pos_ok
    price_ev[pm] = P[ev_stock[pm], pos[pm]]

    # ------------------------------------------------------------- event study
    log('[3/5] recomputing CARs')
    # market-adjusted abnormal return, both legs in percent
    AR = R - ix_ret_arr[None, :]
    valid = ~np.isnan(R)
    CS = np.cumsum(np.where(valid, R, 0.0), axis=1)
    CN = np.cumsum(valid.astype('int64'), axis=1)
    CS = np.hstack([np.zeros((CS.shape[0], 1)), CS])
    CN = np.hstack([np.zeros((CN.shape[0], 1)), CN])

    event_valid = np.zeros(n_ev, dtype=bool)
    okpos = (ev_stock >= 0) & pos_ok
    event_valid[okpos] = ~np.isnan(AR[ev_stock[okpos], pos[okpos]])
    n_eventday_missing = int(((~event_valid) & okpos).sum())
    add('event_study', 'EVENT_DAY', 'events_with_missing_event_day_return',
        diff=float(n_eventday_missing), n_diff=n_eventday_missing,
        n_compared=int(okpos.sum()),
        note='reference code enforces event-day validity only when day 0 is in the window')

    ce = read_csv(os.path.join(DATA, 'car_event_level.csv'),
                  dtype={'股票代码': str, '报告日': str, '事件交易日': str})
    ce['股票代码'] = ce['股票代码'].astype(str).str.strip()
    ce['报告日'] = ce['报告日'].astype(str).str.strip()
    ce['事件交易日'] = ce['事件交易日'].astype(str).str.strip()
    if len(ce) != n_ev:
        log('    WARNING: car_event_level rows=%d, events=%d' % (len(ce), n_ev))

    ce_day = ce['事件交易日'].to_numpy()
    day_mismatch = int((ce_day != event_day).sum())
    add('event_study', 'EVENT_DAY', 'alignment', diff=float(day_mismatch),
        n_diff=day_mismatch, n_compared=n_ev,
        note='events with replicated event day != car_event_level')
    add('event_study', 'STOCK_COVERAGE', 'events_without_market_row',
        diff=float(missing_stock), n_diff=missing_stock, n_compared=n_ev,
        note='events whose stock is absent from market_panel')

    car_rep = {}
    for name, lo, hi in CAR_WINDOWS:
        length = hi - lo + 1
        total = np.zeros(n_ev, dtype='float64')
        cnt = np.zeros(n_ev, dtype='int64')
        for k in range(lo, hi + 1):
            j = pos + k
            inb = (ev_stock >= 0) & (j >= 0) & (j < n_days)
            v = np.full(n_ev, np.nan)
            v[inb] = AR[ev_stock[inb], j[inb]]
            good = ~np.isnan(v)
            total += np.where(good, v, 0.0)
            cnt += good.astype('int64')
        car = np.where(event_valid & (cnt / float(length) >= MIN_SHARE),
                       total, np.nan)
        car_rep[name] = car

        ref = to_num(ce[name]).to_numpy(dtype='float64')
        cmp = compare_arrays(ref, car)
        add('event_study', name, 'event_level', n_compared=cmp['n_compared'],
            max_abs_diff=cmp['max_abs_diff'],
            mean_abs_diff=cmp['mean_abs_diff'],
            n_over_tol=cmp['n_over_tol'],
            n_nan_mismatch=cmp['n_nan_mismatch'],
            n_diff=cmp['n_over_tol'],
            note='reference=%s, task rule: event day valid for every window' % name)

        # variant that mirrors the reference code exactly: day-0 validity is
        # only checked when day 0 lies inside the window (it does not for +2,+120)
        if lo <= 0 <= hi:
            car_refrule = car
        else:
            car_refrule = np.where(cnt / float(length) >= MIN_SHARE,
                                   total, np.nan)
        cmp2 = compare_arrays(ref, car_refrule)
        add('event_study', name, 'event_level_ref_window_rule',
            n_compared=cmp2['n_compared'],
            max_abs_diff=cmp2['max_abs_diff'],
            mean_abs_diff=cmp2['mean_abs_diff'],
            n_over_tol=cmp2['n_over_tol'],
            n_nan_mismatch=cmp2['n_nan_mismatch'],
            n_diff=cmp2['n_over_tol'],
            note='event-day validity only enforced when day 0 is in the window')
        add('event_study', name, 'strict_nan_reference_not_nan',
            n_diff=int((np.isnan(car) & ~np.isnan(ref)).sum()),
            note='values set to NaN by the task rule that the reference reports')
        if name == 'CAR_p2_p120':
            car_refrule_p2 = car_refrule

    # group means under the strict task rule versus the reference window rule
    p2_strict = car_rep['CAR_p2_p120']
    dir_arr = ev['direction'].to_numpy()
    star_arr = ev['star_num'].to_numpy(dtype='float64')
    for dlabel, dval in [('up', '调高'), ('down', '调低')]:
        for sval in (1, 0):
            mm = (dir_arr == dval) & (star_arr == sval)
            a = car_refrule_p2[mm]
            b = p2_strict[mm]
            a = a[~np.isnan(a)]
            b = b[~np.isnan(b)]
            add('event_study', 'CAR_p2_p120_%s_star%d' % (dlabel, sval),
                'group_mean', reference=float(a.mean()),
                replication=float(b.mean()), diff=float(b.mean() - a.mean()),
                n_diff=int(len(b) - len(a)),
                note='n_ref_rule=%d n_strict=%d' % (len(a), len(b)))

    # --------------------------------------------------------- holding returns
    log('[4/5] recomputing 63/126/252-day holding returns')
    sign = np.where(ev['direction'].to_numpy() == '调高', 1.0, -1.0)
    star = ev['star_num'].to_numpy(dtype='float64')

    hold = {}
    for h in HORIZONS:
        start = pos + 1
        end = pos + h + 1          # cumulative boundary, sum days pos+1..pos+h
        ok = (ev_stock >= 0) & (start >= 0) & (end <= n_days)
        st = np.clip(start, 0, n_days)
        en = np.clip(end, 0, n_days)
        s = np.where(ok, ev_stock, 0)
        cum = np.where(ok, CS[s, en] - CS[s, st], np.nan)
        nval = np.where(ok, CN[s, en] - CN[s, st], 0)
        raw = np.where(ok & (nval / float(h) >= MIN_SHARE), cum, np.nan)
        mkt = np.where(ok, ix_cum_hold[en] - ix_cum_hold[st], np.nan)
        hold[h] = (sign * raw, sign * (raw - mkt))

    acc = read_csv(os.path.join(DATA, 'accuracy_summary.csv'))
    acc['horizon'] = to_num(acc['horizon']).astype('int64')
    acc['direction'] = acc['direction'].astype(str).str.strip()

    n_hold_flag = 0
    for _, a in acc.iterrows():
        h = int(a['horizon'])
        measure = str(a['measure']).strip()
        direction = str(a['direction']).strip()
        series = hold[h][0] if measure == 'raw' else hold[h][1]
        mdir = ev['direction'].to_numpy() == direction
        for label, smask, n_ref, mean_ref in [
                ('star', star == 1, a['n_star'], a['mean_star']),
                ('nonstar', star == 0, a['n_nonstar'], a['mean_nonstar'])]:
            vals = series[mdir & smask]
            vals = vals[~np.isnan(vals)]
            n_rep = int(len(vals))
            mean_rep = float(vals.mean()) if n_rep else float('nan')
            key = 'H%d_%s_%s' % (h, measure, 'up' if direction == '调高' else 'down')
            add('holding', key, 'n_' + label,
                reference=float(n_ref), replication=float(n_rep),
                diff=float(n_rep - n_ref), n_diff=int(n_rep - n_ref))
            add('holding', key, 'mean_' + label,
                reference=float(mean_ref), replication=mean_rep,
                diff=mean_rep - float(mean_ref),
                n_diff=int(abs(mean_rep - float(mean_ref)) > 0.01),
                note='flag if |diff|>0.01 pp')
        n_ref_s = float(a['n_star'])
        n_ref_n = float(a['n_nonstar'])
        rep_s = series[mdir & (star == 1)]
        rep_s = rep_s[~np.isnan(rep_s)]
        rep_n = series[mdir & (star == 0)]
        rep_n = rep_n[~np.isnan(rep_n)]
        mean_rep_s = float(rep_s.mean()) if len(rep_s) else float('nan')
        mean_rep_n = float(rep_n.mean()) if len(rep_n) else float('nan')
        flag = (len(rep_s) != int(n_ref_s)) or (len(rep_n) != int(n_ref_n)) or \
               (abs(mean_rep_s - float(a['mean_star'])) > 0.01) or \
               (abs(mean_rep_n - float(a['mean_nonstar'])) > 0.01)
        n_hold_flag += int(flag)
        add('holding', key, 'group_flag', diff=float(flag), n_diff=int(flag),
            note='1 if N mismatch or any mean differs by >0.01 pp')

    # ---------------------------------------------------------- forecast error
    log('[5/5] rematching forecasts and realised EPS')
    fs = sorted(glob.glob(os.path.join(DATA, 'raw_forecast_*.csv')))
    F = pd.concat([read_csv(f, dtype=str) for f in fs], ignore_index=True)
    F = F[['股票代码', '盈利预测研报报告日期', '盈利预测研究机构简称',
           '盈利预测研究人员姓名', '预测每股收益_今年', '预测每股收益_明年']].copy()
    F.columns = ['code', 'date', 'broker', 'analyst', 'eps0', 'eps1']
    for c in ('code', 'date', 'broker', 'analyst'):
        F[c] = F[c].astype(str).str.strip()
    F['eps0'] = to_num(F['eps0'])
    F['eps1'] = to_num(F['eps1'])
    Fk = ['code', 'date', 'analyst', 'broker']
    Fg = F.groupby(Fk, as_index=False).agg(eps0=('eps0', 'mean'),
                                           eps1=('eps1', 'mean'))
    log('    forecast rows=%d unique literal keys=%d' % (len(F), len(Fg)))

    E = pd.DataFrame({
        'code': ev['股票代码'].to_numpy(),
        'date': ev['report_day'].astype(str).to_numpy(),
        'analyst': ev['研究员姓名'].astype(str).str.strip().to_numpy(),
        'broker': ev['研究机构简称'].astype(str).str.strip().to_numpy(),
        '_eid': np.arange(n_ev),
    })
    E['year'] = ev['year_num'].to_numpy()
    E['direction'] = ev['direction'].to_numpy()
    E['star_num'] = ev['star_num'].to_numpy()
    m = E.merge(Fg, on=Fk, how='inner')
    log('    literal-key matched events=%d of %d' % (len(m), n_ev))

    eps = read_csv(os.path.join(DATA, 'ref_actual_eps.csv'), dtype=str)
    eps['code'] = eps['股票代码'].astype(str).str.strip()
    eps['fy'] = to_num(eps['会计年度'])
    eps['actual'] = to_num(eps['基本每股收益'])
    eps = eps.dropna(subset=['fy']).drop_duplicates(['code', 'fy'])
    eps = eps[['code', 'fy', 'actual']]
    m['fy0'] = m['year']
    m['fy1'] = m['fy0'] + 1
    m = m.merge(eps.rename(columns={'fy': 'fy0', 'actual': 'actual0'}),
                on=['code', 'fy0'], how='left')
    m = m.merge(eps.rename(columns={'fy': 'fy1', 'actual': 'actual1'}),
                on=['code', 'fy1'], how='left')
    m['price'] = price_ev[m['_eid'].to_numpy(dtype='int64')]
    m['e0'] = (m['eps0'] - m['actual0']).abs() / m['price'] * 100.0
    m['e1'] = (m['eps1'] - m['actual1']).abs() / m['price'] * 100.0

    fe = read_csv(os.path.join(DATA, 'forecast_error_event.csv'), dtype=str)
    for c in ('股票代码', '最新报告日期', '研究员姓名', '研究机构简称'):
        fe[c] = fe[c].astype(str).str.strip()
    fe_keys = ['股票代码', '最新报告日期', '研究员姓名', '研究机构简称']
    fe_key_df = fe[fe_keys].drop_duplicates()
    rep_key_df = m[['code', 'date', 'analyst', 'broker']].drop_duplicates()

    key_join = rep_key_df.merge(fe_key_df, left_on=['code', 'date', 'analyst', 'broker'],
                                right_on=fe_keys, how='outer', indicator=True)
    n_prod_only = int((key_join['_merge'] == 'right_only').sum())
    n_rep_only = int((key_join['_merge'] == 'left_only').sum())
    add('forecast_error', 'MATCH', 'reference_rows', reference=float(len(fe)),
        replication=float(len(m)), diff=float(len(m) - len(fe)),
        n_diff=int(len(m) - len(fe)),
        note='reference=forecast_error_event.csv; replication=literal-key match')
    add('forecast_error', 'MATCH', 'reference_only_keys', diff=float(n_prod_only),
        n_diff=n_prod_only,
        note='keys in reference but not in literal match (alias variants)')
    add('forecast_error', 'MATCH', 'replication_only_keys', diff=float(n_rep_only),
        n_diff=n_rep_only)

    common = m.merge(
        fe[fe_keys + ['eps0', 'eps1', 'actual0', 'actual1', 'price', 'e0', 'e1']],
        left_on=['code', 'date', 'analyst', 'broker'], right_on=fe_keys,
        how='inner', suffixes=('_rep', '_prod'))
    add('forecast_error', 'MATCH', 'common_rows', n_compared=len(common),
        note='rows present under both key definitions')

    for metric, ref_col, rep_col in [
            ('e0', 'e0_prod', 'e0_rep'), ('e1', 'e1_prod', 'e1_rep'),
            ('eps0', 'eps0_prod', 'eps0_rep'), ('eps1', 'eps1_prod', 'eps1_rep'),
            ('price', 'price_prod', 'price_rep')]:
        cmp = compare_arrays(to_num(common[ref_col]).to_numpy(dtype='float64'),
                             to_num(common[rep_col]).to_numpy(dtype='float64'))
        add('forecast_error', metric.upper(), 'event_level',
            n_compared=cmp['n_compared'],
            max_abs_diff=cmp['max_abs_diff'],
            mean_abs_diff=cmp['mean_abs_diff'],
            n_over_tol=cmp['n_over_tol'],
            n_nan_mismatch=cmp['n_nan_mismatch'],
            n_diff=cmp['n_over_tol'],
            note='reference=forecast_error_event.csv')
        # signed mean difference, useful for e0/e1
        if metric in ('e0', 'e1'):
            a = to_num(common[rep_col]).to_numpy(dtype='float64')
            b = to_num(common[ref_col]).to_numpy(dtype='float64')
            both = ~(np.isnan(a) | np.isnan(b))
            add('forecast_error', metric.upper(), 'mean_signed_diff',
                diff=float(np.mean(a[both] - b[both])) if both.any() else np.nan,
                n_compared=int(both.sum()),
                note='mean(replication - reference)')

    # self-consistency of the reference event file
    fe_e0 = to_num(fe['e0']).to_numpy(dtype='float64')
    fe_calc = (to_num(fe['eps0']) - to_num(fe['actual0'])).abs() / \
        to_num(fe['price']) * 100.0
    fe_calc = fe_calc.to_numpy(dtype='float64')
    cmp = compare_arrays(fe_e0, fe_calc)
    add('forecast_error', 'FE_SELF_CHECK', 'e0_formula',
        n_compared=cmp['n_compared'], max_abs_diff=cmp['max_abs_diff'],
        mean_abs_diff=cmp['mean_abs_diff'], n_over_tol=cmp['n_over_tol'],
        n_nan_mismatch=cmp['n_nan_mismatch'],
        note='reference e0 vs formula from its own eps0/actual0/price')

    # ---------------------------------------------------------------
    # Diagnostic: documented broker/analyst name normalisation.
    # The literal match above stays the primary replication. This block
    # tests whether the reference-only keys are key-normalisation
    # differences only, and reproduces the forecast-error summary.
    BMAP = {
        '中信建投证券': '中信建投', '中国银河证券': '中国银河',
        '中银国际证券': '中银国际', '中银证券': '中银国际',
        '太平洋证券': '太平洋', '粤开证券': '联讯证券',
        '财信证券': '财富证券', '国泰君安证券': '国泰君安',
        '国泰海通': '国泰君安', '国泰海通证券': '国泰君安',
        '国投证券': '安信证券', '国联民生': '国联证券',
        '国联民生证券': '国联证券', '华兴证券': '华菁证券',
        '诚通证券': '新时代证券',
    }
    AMAP = {'余炜超': '佘炜超'}

    def split_name(n):
        n = str(n).strip()
        for sep in (';', '；'):
            if sep in n:
                n = n.split(sep)[0].strip()
        return n

    def canon_broker(n):
        n = split_name(n)
        return BMAP.get(n, n)

    def canon_analyst(n):
        n = str(n).strip()
        return AMAP.get(n, n)

    Fn = F.copy()
    Fn['ca'] = Fn['analyst'].map(canon_analyst)
    Fn['cb'] = Fn['broker'].map(canon_broker)
    Fgn = Fn.groupby(['code', 'date', 'ca', 'cb'], as_index=False).agg(
        eps0=('eps0', 'mean'), eps1=('eps1', 'mean'))
    En = E.copy()
    En['ca'] = En['analyst'].map(canon_analyst)
    En['cb'] = En['broker'].map(canon_broker)
    mn = En.merge(Fgn, on=['code', 'date', 'ca', 'cb'], how='inner')
    mn['fy0'] = mn['year']
    mn['fy1'] = mn['fy0'] + 1
    mn = mn.merge(eps.rename(columns={'fy': 'fy0', 'actual': 'actual0'}),
                  on=['code', 'fy0'], how='left')
    mn = mn.merge(eps.rename(columns={'fy': 'fy1', 'actual': 'actual1'}),
                  on=['code', 'fy1'], how='left')
    mn['price'] = price_ev[mn['_eid'].to_numpy(dtype='int64')]
    mn['e0'] = (mn['eps0'] - mn['actual0']).abs() / mn['price'] * 100.0
    mn['e1'] = (mn['eps1'] - mn['actual1']).abs() / mn['price'] * 100.0

    add('forecast_error', 'CANON_MATCH', 'matched_events',
        reference=float(len(fe)), replication=float(len(mn)),
        diff=float(len(mn) - len(fe)), n_diff=int(len(mn) - len(fe)),
        note='canonical broker/analyst keys')

    common_n = mn.merge(fe[fe_keys + ['e0', 'e1']],
                        left_on=['code', 'date', 'analyst', 'broker'],
                        right_on=fe_keys, how='inner',
                        suffixes=('_rep', '_prod'))
    add('forecast_error', 'CANON_MATCH', 'common_rows', n_compared=len(common_n))
    for col in ('e0', 'e1'):
        cmp = compare_arrays(
            to_num(common_n[col + '_prod']).to_numpy(dtype='float64'),
            to_num(common_n[col + '_rep']).to_numpy(dtype='float64'))
        add('forecast_error', 'CANON_' + col.upper(), 'event_level',
            n_compared=cmp['n_compared'], max_abs_diff=cmp['max_abs_diff'],
            mean_abs_diff=cmp['mean_abs_diff'], n_over_tol=cmp['n_over_tol'],
            n_nan_mismatch=cmp['n_nan_mismatch'], n_diff=cmp['n_over_tol'],
            note='canonical match vs forecast_error_event.csv')

    lit_ids = set(m['_eid'])
    can_ids = set(mn['_eid'])
    only = sorted(can_ids - lit_ids)
    on = mn[mn['_eid'].isin(only)][
        ['_eid', 'code', 'date', 'analyst', 'broker', 'ca', 'cb']].copy()
    kinds = []
    for _, r in on.iterrows():
        g = Fn[(Fn['code'] == r['code']) & (Fn['date'] == r['date']) &
               (Fn['ca'] == r['ca']) & (Fn['cb'] == r['cb'])]
        raw = g[['analyst', 'broker']].drop_duplicates().values.tolist()
        bd = any(aa == r['analyst'] and bb != r['broker'] for aa, bb in raw)
        ad = any(aa != r['analyst'] and bb == r['broker'] for aa, bb in raw)
        if bd and ad:
            kinds.append('both')
        elif bd:
            kinds.append('broker_only')
        elif ad:
            kinds.append('analyst_only')
        elif any(aa == r['analyst'] and bb == r['broker'] for aa, bb in raw):
            kinds.append('exact')
        else:
            kinds.append('neither')
    n_missing_analyst = int(sum(
        1 for _, r in on.iterrows()
        if str(r['analyst']).strip().lower() in ('', 'nan', 'none')))
    add('forecast_error', 'ALIAS_DIAG', 'literal_unmatched_events',
        n_diff=n_ev - len(m), note='events with no literal forecast key')
    add('forecast_error', 'ALIAS_DIAG', 'canonical_only_events',
        n_diff=len(only), note='reference keys recovered by canonical keys')
    add('forecast_error', 'ALIAS_DIAG', 'broker_spelling_only',
        n_diff=kinds.count('broker_only'))
    add('forecast_error', 'ALIAS_DIAG', 'analyst_spelling_only',
        n_diff=kinds.count('analyst_only'))
    add('forecast_error', 'ALIAS_DIAG', 'broker_and_analyst_differ',
        n_diff=kinds.count('both'))
    add('forecast_error', 'ALIAS_DIAG', 'missing_analyst_events',
        n_diff=n_missing_analyst,
        note='canonical-only events with an empty analyst field')
    add('forecast_error', 'ALIAS_DIAG', 'canonical_unmatched_events',
        n_diff=n_ev - len(mn), note='events with no forecast under either key')

    unmatched_ids = set(range(n_ev)) - can_ids
    U = E[E['_eid'].isin(unmatched_ids)]
    Fcd = F[['code', 'date']].drop_duplicates()
    U2 = U.merge(Fcd.assign(_hit=1), on=['code', 'date'], how='left')
    add('forecast_error', 'ALIAS_DIAG', 'unmatched_with_same_code_date_forecast',
        n_diff=int(U2['_hit'].notna().sum()),
        note='canonical-unmatched events with some forecast on the same stock-day')

    fsum = read_csv(os.path.join(DATA, 'forecast_error_summary.csv'))
    n_sum_flags = 0
    for _, s in fsum.iterrows():
        metric = str(s['metric']).strip()
        if metric == 'FY0_abs':
            col = 'e0'
        elif metric == 'FY1_abs':
            col = 'e1'
        else:
            continue
        direction = str(s['direction']).strip()
        sub = mn[mn['direction'] == direction]
        a = to_num(sub.loc[to_num(sub['star_num']) == 1, col]).dropna()
        b = to_num(sub.loc[to_num(sub['star_num']) == 0, col]).dropna()
        lo, hi = np.nanpercentile(pd.concat([a, b]), [1, 99])
        aw = a.clip(lo, hi)
        bw = b.clip(lo, hi)
        key = 'CANON_%s_%s' % (metric, 'up' if direction == '调高' else 'down')
        add('forecast_error', key, 'n_star',
            reference=float(s['n_star']), replication=float(len(a)),
            diff=float(len(a) - s['n_star']), n_diff=int(len(a) - s['n_star']))
        add('forecast_error', key, 'n_nonstar',
            reference=float(s['n_nonstar']), replication=float(len(b)),
            diff=float(len(b) - s['n_nonstar']),
            n_diff=int(len(b) - s['n_nonstar']))
        add('forecast_error', key, 'mean_star',
            reference=float(s['mean_star']), replication=float(aw.mean()),
            diff=float(aw.mean() - s['mean_star']),
            n_diff=int(abs(aw.mean() - s['mean_star']) > 0.01))
        add('forecast_error', key, 'mean_nonstar',
            reference=float(s['mean_nonstar']), replication=float(bw.mean()),
            diff=float(bw.mean() - s['mean_nonstar']),
            n_diff=int(abs(bw.mean() - s['mean_nonstar']) > 0.01))
        add('forecast_error', key, 'median_star',
            reference=float(s['median_star']), replication=float(a.median()),
            diff=float(a.median() - s['median_star']))
        add('forecast_error', key, 'median_nonstar',
            reference=float(s['median_nonstar']), replication=float(b.median()),
            diff=float(b.median() - s['median_nonstar']))
        flag = ((len(a) != int(s['n_star'])) or (len(b) != int(s['n_nonstar']))
                or (abs(aw.mean() - s['mean_star']) > 0.01)
                or (abs(bw.mean() - s['mean_nonstar']) > 0.01))
        n_sum_flags += int(flag)
        add('forecast_error', key, 'group_flag', diff=float(flag),
            n_diff=int(flag),
            note='1 if N mismatch or any mean differs by >0.01 pp')
    log('    canonical matched=%d, forecast summary flags=%d' %
        (len(mn), n_sum_flags))

    add('audit_history', 'FIRST_RUN', 'CAR_implementation_bug',
        note='first run omitted the index-return subtraction and set event-day '
             'validity only at k=0; CAR max diffs were 18.879/29.280/30.190 pp '
             'and CAR_p2_p120 had n_compared=0. Corrected before this output.')

    # --------------------------------------------------------------- write out
    out = pd.DataFrame(rows_out)
    out.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')

    log('done in %.1fs' % (time.time() - t0))
    log('output: data/replication_check.csv')
    log('')
    log('--- key results ---')
    for _, r in out[out['section'] == 'event_study'].iterrows():
        log('%-12s %-14s n=%s max=%.3e mean=%.3e over=%s nanmis=%s' %
            (r['key'], r['metric'], r['n_compared'], r['max_abs_diff'],
             r['mean_abs_diff'], r['n_over_tol'], r['n_nan_mismatch']))
    log('holding groups flagged: %d of %d' % (n_hold_flag, len(acc)))
    sel = out[(out['section'] == 'forecast_error') &
              (out['metric'].isin(['event_level', 'mean_signed_diff']))]
    for _, r in sel.iterrows():
        log('%-8s %-17s n=%s max=%.3e mean=%.3e over=%s nanmis=%s diff=%.3e' %
            (r['key'], r['metric'], r['n_compared'], r['max_abs_diff'],
             r['mean_abs_diff'], r['n_over_tol'], r['n_nan_mismatch'],
             r['diff']))
    sel = out[(out['section'] == 'forecast_error') &
              (out['metric'].isin(['reference_rows', 'common_rows',
                                   'reference_only_keys',
                                   'unmatched_literal_events',
                                   'same_code_date_analyst_other_broker',
                                   'same_code_date_broker_other_analyst']))]
    for _, r in sel.iterrows():
        log('%-10s ref=%s rep=%s n_diff=%s' %
            (r['key'] + '/' + r['metric'], r['reference'], r['replication'],
             r['n_diff']))


if __name__ == '__main__':
    main()
