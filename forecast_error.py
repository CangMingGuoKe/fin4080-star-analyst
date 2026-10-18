# -*- coding: utf-8 -*-
"""Q3 third metric: earnings forecast error, star versus non-star.

For each event, match the analyst's own EPS forecast in the same report on
(stock, report date, analyst, broker), then compare it with the realised annual
basic EPS. Error is |forecast - actual| / closing price on the event day, in
percentage points of price. FY0 is the report's fiscal year, FY1 the next one.

Outputs: data/forecast_error_event.csv, data/forecast_error_summary.csv
"""
import os
import glob
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
import sys
sys.path.insert(0, HERE)
from broker_names import canonical_broker, canonical_analyst


def num(s):
    return pd.to_numeric(s, errors='coerce')


def main():
    ev = pd.read_csv(os.path.join(DATA, 'analysis_table.csv'),
                     dtype={'股票代码': str}, encoding='utf-8-sig', low_memory=False)
    fs = sorted(glob.glob(os.path.join(DATA, 'raw_forecast_*.csv')))
    F = pd.concat([pd.read_csv(f, dtype=str, encoding='utf-8-sig', low_memory=False)
                   for f in fs], ignore_index=True)
    F = F[['股票代码', '盈利预测研报报告日期', '盈利预测研究机构简称',
           '盈利预测研究人员姓名', '预测每股收益_今年', '预测每股收益_明年']].copy()
    F.columns = ['股票代码', '报告日期', '机构', '分析师', 'eps0', 'eps1']
    F['eps0'] = num(F['eps0'])
    F['eps1'] = num(F['eps1'])
    F['k_code'] = F['股票代码'].astype(str).str.strip()
    F['k_date'] = F['报告日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    F['k_an'] = F['分析师'].astype(str).str.strip().map(canonical_analyst)
    F['k_br'] = F['机构'].astype(str).str.strip().map(canonical_broker)

    # one row per report; duplicated keys are folded by the mean forecast
    Fg = F.groupby(['k_code', 'k_date', 'k_an', 'k_br'], as_index=False).agg(
        {'eps0': 'mean', 'eps1': 'mean'})
    print('forecast rows %d, unique report keys %d' % (len(F), len(Fg)))

    ev['k_code'] = ev['股票代码'].astype(str).str.strip()
    ev['k_date'] = ev['最新报告日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    ev['k_an'] = ev['研究员姓名'].astype(str).str.strip().map(canonical_analyst)
    ev['k_br'] = ev['研究机构简称'].astype(str).str.strip().map(canonical_broker)
    m = ev.merge(Fg, on=['k_code', 'k_date', 'k_an', 'k_br'], how='inner')
    print('matched events %d of %d' % (len(m), len(ev)))

    # realised annual EPS
    eps = pd.read_csv(os.path.join(DATA, 'ref_actual_eps.csv'), dtype=str, encoding='utf-8-sig')
    eps['k_code'] = eps['股票代码'].astype(str).str.strip()
    eps['fy'] = num(eps['会计年度'])
    eps['actual'] = num(eps['基本每股收益'])
    eps = eps.dropna(subset=['fy']).drop_duplicates(['k_code', 'fy'])[['k_code', 'fy', 'actual']]
    m['fy0'] = num(m['年份'])
    m['fy1'] = m['fy0'] + 1
    m = m.merge(eps.rename(columns={'fy': 'fy0', 'actual': 'actual0'}), on=['k_code', 'fy0'], how='left')
    m = m.merge(eps.rename(columns={'fy': 'fy1', 'actual': 'actual1'}), on=['k_code', 'fy1'], how='left')

    # price on the event trading day; attach by stock and report date, because
    # non-trading-day reports have an event day shifted away from the report date
    ce = pd.read_csv(os.path.join(DATA, 'car_event_level.csv'),
                     dtype={'股票代码': str, '报告日': str, '事件交易日': str},
                     encoding='utf-8-sig',
                     usecols=['股票代码', '报告日', '事件交易日'])
    ce['k_code'] = ce['股票代码'].astype(str).str.strip()
    ce['k_rdate'] = pd.to_datetime(ce['报告日'], errors='coerce').dt.strftime('%Y%m%d')
    ce['k_day'] = ce['事件交易日'].astype(str).str.strip()
    mp = pd.read_csv(os.path.join(DATA, 'market_panel.csv'),
                     dtype={'股票代码': str, '日期': str}, encoding='utf-8-sig',
                     usecols=['股票代码', '日期', '收盘价'], low_memory=False)
    mp['k_code'] = mp['股票代码'].astype(str).str.strip()
    mp['k_day'] = mp['日期'].astype(str).str.strip()
    mp['price'] = num(mp['收盘价'])
    px = mp[['k_code', 'k_day', 'price']].drop_duplicates(['k_code', 'k_day'])
    ce = ce.merge(px, on=['k_code', 'k_day'], how='left')
    m = m.merge(ce[['k_code', 'k_rdate', 'price']].drop_duplicates(['k_code', 'k_rdate']),
                left_on=['k_code', 'k_date'], right_on=['k_code', 'k_rdate'], how='left')

    m['e0'] = (m['eps0'] - m['actual0']).abs() / m['price'] * 100
    m['e1'] = (m['eps1'] - m['actual1']).abs() / m['price'] * 100
    m['s0'] = (m['eps0'] - m['actual0']) / m['price'] * 100
    m['s1'] = (m['eps1'] - m['actual1']) / m['price'] * 100

    out = m[['股票代码', '最新报告日期', '研究员姓名', '研究机构简称', '评级调整方向',
             'star', '年份', 'eps0', 'eps1', 'actual0', 'actual1', 'price',
             'e0', 'e1', 's0', 's1', '券商层级', '资历']].copy()
    out.to_csv(os.path.join(DATA, 'forecast_error_event.csv'), index=False, encoding='utf-8-sig')

    rows = []
    for metric, label in [('e0', 'FY0_abs'), ('e1', 'FY1_abs'),
                          ('s0', 'FY0_signed'), ('s1', 'FY1_signed')]:
        for direction in ['调高', '调低']:
            sub = out[(out['评级调整方向'].astype(str).str.strip() == direction)]
            s1 = num(sub.loc[num(sub['star']) == 1, metric]).dropna()
            s0 = num(sub.loc[num(sub['star']) == 0, metric]).dropna()
            if len(s1) < 30 or len(s0) < 30:
                continue
            # winsorise at 1/99 for the mean test; medians are reported unadjusted
            lo, hi = np.nanpercentile(pd.concat([s1, s0]), [1, 99])
            w1 = s1.clip(lo, hi)
            w0 = s0.clip(lo, hi)
            t, p = stats.ttest_ind(w1, w0, equal_var=False)
            rows.append({'metric': label, 'direction': direction,
                         'n_star': len(s1), 'n_nonstar': len(s0),
                         'mean_star': round(float(w1.mean()), 4),
                         'mean_nonstar': round(float(w0.mean()), 4),
                         'diff': round(float(w1.mean() - w0.mean()), 4),
                         'median_star': round(float(s1.median()), 4),
                         'median_nonstar': round(float(s0.median()), 4),
                         't': round(float(t), 2), 'p': round(float(p), 4)})
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(DATA, 'forecast_error_summary.csv'), index=False, encoding='utf-8-sig')
    print(res.to_string(index=False))
    print('matched with price %d, with FY0 actual %d, with FY1 actual %d'
          % (int(m['price'].notna().sum()), int(m['e0'].notna().sum()), int(m['e1'].notna().sum())))


if __name__ == '__main__':
    main()
