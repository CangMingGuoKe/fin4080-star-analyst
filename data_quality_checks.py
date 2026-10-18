# -*- coding: utf-8 -*-
"""Data-quality diagnostics for the market panel.

Covers three questions raised in the 2026-10-18 hand-off note:
  1. What are the 43,830 rows with StateCode=1 / Filling=1: suspension rows or
     holiday fill rows?
  2. Where does the 1273.938 percent return come from, and what rule should the
     event study use for such rows?
  3. What does the panel look like for a data-source paragraph: coverage,
     fields, adjustment, missing values, known gaps.

The script only reads existing files and prints ASCII diagnostics. It writes
no files.
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

HOLIDAYS = [
    '20170102', '20170127', '20170130', '20171002', '20180215', '20180405',
    '20181001', '20190204', '20191001', '20200101', '20200124', '20201001',
    '20210101', '20210211', '20211001', '20220103', '20220201', '20221003',
    '20230102', '20230123', '20230929', '20231002', '20240101', '20240212',
    '20240501', '20241001', '20250101', '20250128', '20250501', '20251001',
    '20260101', '20260216', '20260501', '20261001',
]


def main():
    mp = pd.read_csv(os.path.join(DATA, 'market_panel.csv'),
                     usecols=['股票代码', '日期', '收盘价', '涨跌幅', '成交量',
                              'StateCode', 'Filling'],
                     dtype={'股票代码': str, '日期': str},
                     encoding='utf-8-sig', low_memory=False)
    mp.columns = ['code', 'date', 'close', 'ret', 'vol', 'state', 'fill']
    mp['ret'] = pd.to_numeric(mp['ret'], errors='coerce')
    mp['vol'] = pd.to_numeric(mp['vol'], errors='coerce')
    mp['close'] = pd.to_numeric(mp['close'], errors='coerce')
    mp = mp.sort_values(['code', 'date'], kind='mergesort').reset_index(drop=True)
    mp['rank'] = mp.groupby('code', sort=False).cumcount()
    flag = (mp['state'] == 1) | (mp['fill'] == 1)
    f = mp[flag].copy()

    print('=== PANEL ===')
    print('rows %d, codes %d, dates %d, %s to %s'
          % (len(mp), mp['code'].nunique(), mp['date'].nunique(),
             mp['date'].min(), mp['date'].max()))
    print('duplicate code-date rows: %d' % int(mp.duplicated(['code', 'date']).sum()))

    print('\n=== 1. FLAGGED ROWS ===')
    print('flag rows %d; codes %d; dates %d' %
          (len(f), f['code'].nunique(), f['date'].nunique()))
    print('state=1 and fill=1 %d; state only %d; fill only %d'
          % (int(((mp['state'] == 1) & (mp['fill'] == 1)).sum()),
             int(((mp['state'] == 1) & (mp['fill'] != 1)).sum()),
             int(((mp['state'] != 1) & (mp['fill'] == 1)).sum())))
    print('missing ret %d; missing vol %d; missing close %d'
          % (int(f['ret'].isna().sum()), int(f['vol'].isna().sum()),
             int(f['close'].isna().sum())))
    print('\nflag rows by year:')
    print(f['date'].str[:4].value_counts().sort_index().to_string())

    wd_f = pd.to_datetime(f['date'], format='%Y%m%d').dt.dayofweek.value_counts().sort_index()
    wd_a = pd.to_datetime(mp['date'], format='%Y%m%d').dt.dayofweek.value_counts().sort_index()
    wd = pd.DataFrame({'flag_rows': wd_f, 'all_rows': wd_a})
    wd['flag_share'] = (wd['flag_rows'] / wd['flag_rows'].sum()).round(4)
    wd['all_share'] = (wd['all_rows'] / wd['all_rows'].sum()).round(4)
    wd.index = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    print('\nweekday distribution:')
    print(wd.to_string())

    print('\nflag rows on known exchange holidays: %d'
          % int(f['date'].isin(HOLIDAYS).sum()))
    ix = pd.read_csv(os.path.join(DATA, 'index_panel.csv'), dtype=str,
                     encoding='utf-8-sig')
    cal = set(ix['日期'].astype(str).str.strip())
    print('flag dates not in index trading calendar: %d'
          % len(set(f['date']) - cal))

    # close carried forward from the last non-flag row
    last_valid_close = mp['close'].where(~flag).groupby(
        mp['code'], sort=False).ffill()
    eq = np.isclose(f['close'].values, last_valid_close[flag].values)
    print('flag close equals last non-flag close: %d of %d (%.1f%%)'
          % (int(eq.sum()), len(f), 100.0 * eq.mean()))

    # contiguous trading-day runs within each stock
    indices = mp.groupby('code', sort=False).indices
    runs, rows_in60, rows_in120 = [], 0, 0
    for c, g in f.groupby('code', sort=False):
        pos_all = indices[c]
        dts = mp['date'].values[pos_all]
        ii = np.searchsorted(dts, g['date'].values)
        breaks = np.where(np.diff(ii) > 1)[0]
        for seg in np.split(ii, breaks + 1):
            runs.append(len(seg))
    runs = np.array(runs)
    rows_in60 = int(runs[runs >= 60].sum())
    rows_in120 = int(runs[runs >= 120].sum())
    print('\ncontiguous flag runs: %d; median %d; p90 %d; max %d'
          % (len(runs), int(np.median(runs)), int(np.percentile(runs, 90)),
             int(runs.max())))
    print('flag rows in runs >=60 days: %d; >=120 days: %d'
          % (rows_in60, rows_in120))
    print('top flagged stocks:')
    print(f['code'].value_counts().head(10).to_string())

    fv = mp.loc[~flag & mp['ret'].notna()].groupby('code')['date'].min()
    merged = f[['code', 'date']].merge(fv.rename('first_valid'), on='code',
                                       how='left')
    pre = int((merged['date'] < merged['first_valid']).sum())
    post = int((merged['date'] > merged['first_valid']).sum())
    print('flag rows before first valid return %d; on/after %d' % (pre, post))
    print('stocks whose every flag precedes first valid return: %d'
          % int((merged.groupby('code')['date'].max() <
                 merged.groupby('code')['first_valid'].first()).sum()))

    ld = pd.read_csv(os.path.join(DATA, 'ref_listing_dates.csv'), dtype=str,
                     encoding='utf-8-sig')
    ld_code = ld.iloc[:, 0].astype(str).str.strip()
    ld_date = ld.iloc[:, 3].astype(str).str.strip()
    ldm = dict(zip(ld_code, ld_date))
    fl = f[['code', 'date']].copy()
    fl['listing'] = fl['code'].map(ldm)
    before_listing = fl['date'] < fl['listing']
    print('flag rows before listing date: %d; on/after listing: %d'
          % (int(before_listing.sum()), int((~before_listing).sum())))
    print('\nexamples (flag span, first valid, listing date):')
    for c in ['002739.SZ', '000629.SZ', '000792.SZ']:
        g = f[f['code'] == c]
        print('%s flags %d span %s..%s first_valid %s listing %s'
              % (c, len(g), g['date'].min(), g['date'].max(),
                 fv.get(c, 'NA'), ldm.get(c, 'NA')))

    print('\n=== 2. EXTREME RETURNS ===')
    absret = mp['ret'].abs()
    first = mp['rank'] == 0
    print('max return %.3f on %s %s (rank %d)'
          % (mp['ret'].max(), mp.loc[mp['ret'].idxmax(), 'code'],
             mp.loc[mp['ret'].idxmax(), 'date'],
             int(mp.loc[mp['ret'].idxmax(), 'rank'])))
    print('second max %.3f on %s %s (rank %d)'
          % (mp['ret'].nlargest(2).iloc[1],
             mp.loc[mp['ret'].nlargest(2).index[1], 'code'],
             mp.loc[mp['ret'].nlargest(2).index[1], 'date'],
             int(mp.loc[mp['ret'].nlargest(2).index[1], 'rank'])))
    for t in [21, 30, 50, 100, 500]:
        print('first-row |ret|>%d: %d; mid-panel |ret|>%d: %d'
              % (t, int((absret[first] > t).sum()),
                 t, int((absret[~first] > t).sum())))

    hit = np.isclose(mp['ret'].values, 1273.938, atol=1e-3)
    h = mp[hit]
    print('\n1273.938 rows: %d' % len(h))
    for _, r in h.iterrows():
        implied = r['close'] / (1.0 + r['ret'] / 100.0)
        pos_all = indices[r['code']]
        loc = np.searchsorted(pos_all, r.name)
        nxt = mp.iloc[pos_all[loc + 1]] if loc + 1 < len(pos_all) else None
        print('code %s date %s rank %d close %.3f ret %.3f vol %.0f'
              % (r['code'], r['date'], int(r['rank']), r['close'],
                 r['ret'], r['vol']))
        print('implied pre-close %.4f; listing date %s'
              % (implied, ldm.get(r['code'], 'NA')))
        if nxt is not None:
            print('next trading day %s close %.3f ret %.3f'
                  % (nxt['date'], nxt['close'], nxt['ret']))

    mid = mp[(~first) & (absret > 30)].sort_values('ret', ascending=False)
    print('\nmid-panel |ret|>30 rows: %d' % len(mid))
    print(mid[['code', 'date', 'close', 'ret', 'rank']].head(8).to_string(index=False))

    print('\n=== event windows containing extreme rows ===')
    ev = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                     dtype={'股票代码': str, '事件交易日': str},
                     encoding='utf-8-sig', low_memory=False)
    ev['股票代码'] = ev['股票代码'].astype(str).str.strip()
    ev['事件交易日'] = ev['事件交易日'].astype(str).str.strip()
    cal_list = sorted(cal)
    pos = {d: i for i, d in enumerate(cal_list)}
    ev_code = ev['股票代码'].values
    ev_date = ev['事件交易日'].values
    anom = set(zip(mp.loc[absret > 30, 'code'], mp.loc[absret > 30, 'date']))
    firstday = set(zip(mp.loc[first, 'code'], mp.loc[first, 'date']))
    metrics = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5),
               ('CAR_m5_p5', -5, 5), ('CAR_0_p120', 0, 120),
               ('CAR_0_p250', 0, 250)]
    for nm, lo, hi in metrics:
        na = nf = 0
        for i in range(len(ev)):
            p = pos.get(ev_date[i])
            if p is None:
                continue
            dts = cal_list[max(0, p + lo):min(len(cal_list), p + hi + 1)]
            if any((ev_code[i], d) in anom for d in dts):
                na += 1
            if any((ev_code[i], d) in firstday for d in dts):
                nf += 1
        print('%s: events with |ret|>30 in window %d; with first-day row %d'
              % (nm, na, nf))
    n688 = int((ev['股票代码'] == '688690.SH').sum())
    print('events for 688690.SH: %d; earliest event date %s'
          % (n688, ev.loc[ev['股票代码'] == '688690.SH', '事件交易日'].min()
             if n688 else 'NA'))

    print('\n=== 3. LIMIT-HIT DIAGNOSTICS ===')
    c3 = mp['code'].str[:3]
    is_bj = mp['code'].str.endswith('.BJ').values
    is_cy = c3.isin(['300', '301']).values
    is_star = c3.isin(['688', '689']).values
    is_main = ~(is_bj | is_cy | is_star)
    thr = np.full(len(mp), 10.0)
    thr[is_cy & (mp['date'].values >= '20200824')] = 20.0
    thr[is_star] = 20.0
    thr[is_bj] = 30.0
    ret = mp['ret'].values
    rk = mp['rank'].values
    first5 = rk < 5
    lim = (((ret >= thr - 0.2) & (ret <= thr + 1.0)) |
           ((ret <= -(thr - 0.2)) & (ret >= -(thr + 1.0)))) & ~first5
    raw = (((ret >= thr - 0.2)) | ((ret <= -(thr - 0.2)))) & ~first5
    print('limit hits with +1.0 pp guard and first-five exclusion: %d' % int(lim.sum()))
    print('without guard: %d; removed by guard: %d'
          % (int(raw.sum()), int(raw.sum() - lim.sum())))
    for nm, m in (('Main', is_main), ('ChiNext', is_cy), ('STAR', is_star),
                  ('BJ', is_bj)):
        print('%-8s rows %8d hits %7d share %.3f%%'
              % (nm, int(m.sum()), int(lim[m].sum()), 100.0 * lim[m].mean()))
    print('\nfive-percent band, main board: rows %d (%.2f%%), codes %d'
          % (int((is_main & (absret >= 4.5) & (absret <= 5.5)).sum()),
             100.0 * (is_main & (absret >= 4.5) & (absret <= 5.5)).sum() / is_main.sum(),
             mp.loc[is_main & (absret >= 4.5) & (absret <= 5.5), 'code'].nunique()))
    print('five-percent band, all boards: rows %d (%.2f%%)'
          % (int(((absret >= 4.5) & (absret <= 5.5)).sum()),
             100.0 * ((absret >= 4.5) & (absret <= 5.5)).mean()))


if __name__ == '__main__':
    main()
