# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 事件研究引擎 v2

相对 v1（event_study.py）的改动，来源是 2026-10-07 的脚本核查：

  1. 事件窗口按**市场交易日历**定位，不按个股表的行位置切片。v1 遇到停牌、缺失、
     节假日填充行时，行位置就不再等于交易日。
  2. 事件日 = 首个不早于报告日的交易日；原报告日保留另存。可用 --align exact
     切回「只保留报告日即交易日」的严格口径做稳健性。
  3. CAR 先校验有效观测：事件日当天必须有收益，窗口内有效占比低于 MIN_AR_SHARE
     时返回缺失并记录原因，**不把缺失当零回报**。v1 的 .sum() 会跳过缺失，
     极端情况下全缺失也返回 0。
  4. 成交量基准同样记录有效个数，低于 MIN_BASE 时返回缺失。
  5. 事件级输出带上 star、资历、资历分位、券商层级，并保留可回溯的事件序号。
  6. 汇总除单样本 t 外，加明星与非明星的组间检验，并给出「同股同日先取均值」的
     聚类稳健版本。同股同日的事件并不独立。
  7. 删掉「用单日涨跌幅反推 ST」的说法。本版不做 ST 识别，如实说明。

用法：
    python event_study_v2.py                 正式跑
    python event_study_v2.py --align exact   只保留报告日即交易日的事件
    python event_study_v2.py --selftest      用合成数据自测，不读真实行情

输出：data/car_event_level.csv、data/car_summary.csv（与 v1 同名，便于下游沿用）
"""
import bisect
import glob
import io
import os
import shutil
import sys
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from market_data_adapter import load_returns

# 事件窗口：(名称, 起, 止)，以事件日为 0，单位是交易日
CAR_WINDOWS = [('CAR_m1_p1', -1, 1), ('CAR_m1_p5', -1, 5),
               ('CAR_m5_p5', -5, 5), ('CAR_0_p60', 0, 60),
               ('CAR_0_p120', 0, 120), ('CAR_0_p250', 0, 250),
               ('CAR_p2_p60', 2, 60), ('CAR_p2_p120', 2, 120),
               ('CAR_p2_p250', 2, 250)]
EST = (-120, -11)        # 异常成交量的基准窗口
MIN_AR_SHARE = 0.80      # 窗口内有效收益占比下限
MIN_BASE = 60            # 成交量基准的有效位置下限（共 110 个位置）


def read_any(path):
    """按 UTF-8 读，失败退回 GBK：管线的 CSV 被 Excel 另存过也能读。"""
    last = None
    for enc in ('utf-8-sig', 'gbk'):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as e:
            last = e
    raise last


def panel_files(data_dir, stem):
    """单个文件优先；否则读按年拆分的 stem*.csv 并在调用处合并。"""
    one = os.path.join(data_dir, stem + '.csv')
    if os.path.exists(one):
        return [one]
    return sorted(glob.glob(os.path.join(data_dir, stem + '*.csv')))


def load(data_dir):
    evp = os.path.join(data_dir, 'analysis_table.csv')
    if not os.path.exists(evp):
        print('[X] 缺 analysis_table.csv')
        return None
    mp, ix, source = load_returns(data_dir)
    ev = read_any(evp)
    ev['股票代码'] = ev['股票代码'].astype(str).str.strip()
    for c in ('日期', '最新报告日期'):
        if c in ev.columns:
            ev[c] = ev[c].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(8)
    print('行情来源：%s；股票行 %d，交易日 %d' % (source, len(mp), len(ix)))
    return mp, ix, ev


def build_calendar(ix):
    """交易日历：按日期升序去重，返回 (列表, 日期->位置)。"""
    d = sorted(set(ix['日期'].astype(str).str.strip()))
    return d, {v: i for i, v in enumerate(d)}


def prep_market(mp, ix):
    """算市场调整异常收益与对数成交量，按 股票 -> {日期: 值} 存，不用行位置。"""
    ix = ix.sort_values('日期').drop_duplicates('日期')
    if '市场收益率' in ix.columns:
        mkt = pd.Series(pd.to_numeric(ix['市场收益率'], errors='coerce').values,
                        index=ix['日期'].astype(str).str.strip())
    else:
        mkt = pd.to_numeric(ix['收盘价'], errors='coerce').pct_change() * 100.0
        mkt = pd.Series(mkt.values, index=ix['日期'].astype(str).str.strip())
    mp = mp.copy()
    mp['日期'] = mp['日期'].astype(str).str.strip()
    mp = mp.sort_values(['股票代码', '日期']).drop_duplicates(['股票代码', '日期'], keep='first')
    ret = pd.to_numeric(mp['涨跌幅'], errors='coerce')
    mp['AR'] = ret - mp['日期'].map(mkt)
    vol = pd.to_numeric(mp['成交量'], errors='coerce')
    mp['logV'] = np.log(vol.where(vol > 0))
    out = {}
    for code, g in mp.groupby('股票代码'):
        out[code] = (dict(zip(g['日期'], g['AR'])), dict(zip(g['日期'], g['logV'])))
    return out


def event_date(cal, cal_pos, report_date, align):
    """事件日：align='next' 取首个不早于报告日的交易日；'exact' 要求报告日即交易日。"""
    if align == 'exact':
        return report_date if report_date in cal_pos else None
    i = bisect.bisect_left(cal, report_date)
    return cal[i] if i < len(cal) else None


def window_car(ar_map, cal, pos, lo, hi):
    """按日历位置取窗口。返回 (CAR, 有效个数, 窗口长度, 缺失原因)。"""
    n = hi - lo + 1
    vals = []
    for i in range(lo, hi + 1):
        j = pos + i
        if j < 0 or j >= len(cal):
            vals.append(np.nan)                      # 超出日历两端，算缺失
        else:
            vals.append(ar_map.get(cal[j], np.nan))  # 停牌或缺失，算缺失
    v = pd.Series(vals, dtype='float64')
    valid = int(v.notna().sum())
    if lo <= 0 <= hi and pd.isna(v.iloc[-lo]):
        return np.nan, valid, n, '事件日缺收益'
    if valid / n < MIN_AR_SHARE:
        return np.nan, valid, n, '有效观测不足(%d/%d)' % (valid, n)
    return float(v.sum()), valid, n, None


def abnormal_volume(lv_map, cal, pos, event_d):
    a, b = pos + EST[0], pos + EST[1]
    if a < 0 or b >= len(cal):
        return np.nan, 0
    base = pd.Series([lv_map[d] for d in cal[a:b + 1] if d in lv_map], dtype='float64').dropna()
    cur = lv_map.get(event_d, np.nan)
    if len(base) < MIN_BASE or pd.isna(cur):
        return np.nan, len(base)
    return float(cur - base.mean()), len(base)


def run(data_dir, align='next'):
    got = load(data_dir)
    if got is None:
        return None
    mp, ix, ev = got
    cal, cal_pos = build_calendar(ix)
    market = prep_market(mp, ix)
    print('交易日历 %d 天（%s 至 %s），行情股票 %d 只，事件 %d 条'
          % (len(cal), cal[0], cal[-1], len(market), len(ev)))

    rows, drop = [], {'无该股票行情': 0, '报告日无法对齐': 0}
    for idx, e in ev.iterrows():
        code = str(e['股票代码'])
        if code not in market:
            drop['无该股票行情'] += 1
            continue
        ed = event_date(cal, cal_pos, str(e['最新报告日期']), align)
        if ed is None:
            drop['报告日无法对齐'] += 1
            continue
        ar_map, lv_map = market[code]
        pos = cal_pos[ed]
        rec = {'事件序号': int(idx), '股票代码': code, '报告日': e['最新报告日期'],
               '事件交易日': ed, '对齐方式': align,
               '研究员姓名': e.get('研究员姓名'), '研究机构简称': e.get('研究机构简称'),
               '评级调整方向': e.get('评级调整方向'), 'star': e.get('star'),
               '资历': e.get('资历'), '资历分位': e.get('资历分位'),
               '券商层级': e.get('券商层级'), '触到覆盖起点': e.get('触到覆盖起点')}
        av, nb = abnormal_volume(lv_map, cal, pos, ed)
        rec['AV'] = av
        rec['AV基准有效个数'] = nb
        for nm, lo, hi in CAR_WINDOWS:
            car, valid, n, reason = window_car(ar_map, cal, pos, lo, hi)
            rec[nm] = car
            rec[nm + '_有效'] = valid
            rec[nm + '_窗口'] = n
            rec[nm + '_原因'] = reason
        rows.append(rec)

    res = pd.DataFrame(rows)
    print('可用事件 %d 条（%s）' % (len(res), '；'.join('%s %d' % kv for kv in drop.items())))
    return res


def summarize(res):
    """单样本 t + 明星与非明星组间检验；另给同股同日先取均值的聚类稳健版本。"""
    cols = [nm for nm, _, _ in CAR_WINDOWS] + ['AV']
    star1 = pd.to_numeric(res['star'], errors='coerce') == 1
    star0 = pd.to_numeric(res['star'], errors='coerce') == 0
    out = []

    def add(star, d, kind, c, n, mean, med, t, p):
        out.append({'star': star, '方向': d, '检验': kind, '指标': c, 'N': n,
                    '均值': round(float(mean), 4),
                    '中位数': (np.nan if med is None else round(float(med), 4)),
                    't': round(float(t), 2), 'p': round(float(p), 4)})

    for (s, d), g in res.groupby(['star', '评级调整方向'], dropna=False):
        for c in cols:
            v = pd.to_numeric(g[c], errors='coerce').dropna()
            if len(v) < 5:
                continue
            t, p = stats.ttest_1samp(v, 0.0)
            add(s, d, '单样本t(对0)', c, len(v), v.mean(), v.median(), t, p)

    def two_sample(mask_a, mask_b, d, kind, frame, c):
        a = pd.to_numeric(frame.loc[mask_a, c], errors='coerce').dropna()
        b = pd.to_numeric(frame.loc[mask_b, c], errors='coerce').dropna()
        if len(a) < 5 or len(b) < 5:
            return
        t, p = stats.ttest_ind(a, b, equal_var=False)
        add('1 vs 0', d, kind, c, '%d/%d' % (len(a), len(b)),
            a.mean() - b.mean(), None, t, p)

    for d, g in res.groupby('评级调整方向', dropna=False):
        for c in cols:
            two_sample(star1.loc[g.index], star0.loc[g.index], d,
                       '组间t(明星-非明星)', g, c)

    # 聚类稳健版本：同股同日先取均值，再检验
    key = ['股票代码', '事件交易日', 'star', '评级调整方向']
    col = res.groupby(key, dropna=False)[cols].mean().reset_index()
    c1 = pd.to_numeric(col['star'], errors='coerce') == 1
    c0 = pd.to_numeric(col['star'], errors='coerce') == 0
    for d, g in col.groupby('评级调整方向', dropna=False):
        for c in cols:
            two_sample(c1.loc[g.index], c0.loc[g.index], d,
                       '组间t(同股同日取均值后)', g, c)
    return pd.DataFrame(out)


def main():
    data_dir = os.path.join(HERE, 'data')
    align = 'exact' if ('--align' in sys.argv and 'exact' in sys.argv) else 'next'
    res = run(data_dir, align)
    if res is None or res.empty:
        print('[X] 没有可用事件，检查行情日期与代码格式')
        return
    res.to_csv(os.path.join(data_dir, 'car_event_level.csv'), index=False, encoding='utf-8-sig')
    summ = summarize(res)
    summ.to_csv(os.path.join(data_dir, 'car_summary.csv'), index=False, encoding='utf-8-sig')
    print('事件级 %d 行 -> car_event_level.csv；汇总 %d 行 -> car_summary.csv'
          % (len(res), len(summ)))
    print(summ.head(12).to_string(index=False) if len(summ) else '（分组样本不足）')
    print('done')


def selftest():
    """合成数据自测：对齐、窗口计数、缺失处理、组间检验。"""
    tmp = tempfile.mkdtemp(prefix='es2_')
    try:
        days = [d.strftime('%Y%m%d') for d in pd.date_range('2018-01-01', '2019-12-31')
                if d.dayofweek < 5]
        ix = pd.DataFrame({'日期': days, '收盘价': np.linspace(3000, 3300, len(days))})
        rows = []
        codes = ['000001.SZ', '000002.SZ', '000003.SZ'] + \
                ['0000%d.SZ' % i for i in range(10, 14)]
        for k, c in enumerate(codes):
            for i, d in enumerate(days):
                if c == '000002.SZ' and 82 <= i <= 91:
                    continue                       # 停牌 10 天，落在该股事件的 [-5,+5] 窗口内
                if c == '000003.SZ' and i < 130:
                    continue                       # 后段才上市
                rows.append({'股票代码': c, '日期': d, '收盘价': 10.0,
                             '涨跌幅': 1.0 + k, '成交量': 1000.0 * (i + 1)})
        mp = pd.DataFrame(rows)
        sat = [d for d in pd.date_range('2018-06-01', periods=14)
               if d.dayofweek == 5][0].strftime('%Y%m%d')
        ev = pd.DataFrame([
            {'股票代码': '000001.SZ', '最新报告日期': sat, '研究员姓名': 'analyst_A',
             '研究机构简称': '某证券', '评级调整方向': '调高', 'star': '1',
             '资历': 3.0, '资历分位': 0.5, '券商层级': '头部', '触到覆盖起点': 'False'},
            {'股票代码': '000002.SZ', '最新报告日期': days[80], '研究员姓名': 'analyst_B',
             '研究机构简称': '某证券', '评级调整方向': '调低', 'star': '0',
             '资历': 1.0, '资历分位': 0.2, '券商层级': '中部', '触到覆盖起点': 'False'},
            {'股票代码': '000003.SZ', '最新报告日期': days[3], '研究员姓名': '丙三',
             '研究机构简称': '某证券', '评级调整方向': '调高', 'star': '0',
             '资历': 0.5, '资历分位': 0.1, '券商层级': '中小', '触到覆盖起点': 'True'},
        ])
        # 再补一批样本，让分组统计真的跑起来（每组至少 5 条）
        extra = []
        for k, c in enumerate(codes[3:]):
            for j in range(10):
                extra.append({'股票代码': c, '最新报告日期': days[20 + j],
                              '研究员姓名': '研究%d' % j, '研究机构简称': '某证券',
                              '评级调整方向': '调高' if j % 2 else '调低',
                              'star': '1' if (j + k) % 2 else '0',
                              '资历': 2.0, '资历分位': 0.4, '券商层级': '头部',
                              '触到覆盖起点': 'False'})
        ev = pd.concat([ev, pd.DataFrame(extra)], ignore_index=True)
        for f, d in (('market_panel.csv', mp), ('index_panel.csv', ix),
                     ('analysis_table.csv', ev)):
            d.to_csv(os.path.join(tmp, f), index=False, encoding='utf-8-sig')

        res = run(tmp, 'next')
        nxt = min(d for d in days if d > sat)
        r0 = res[res['股票代码'] == '000001.SZ'].iloc[0]
        r1 = res[res['股票代码'] == '000002.SZ'].iloc[0]
        r2 = res[res['股票代码'] == '000003.SZ'].iloc[0]
        summ = summarize(res)
        checks = [
            ('周六报告日顺延', r0['事件交易日'] == nxt, r0['事件交易日'], nxt),
            ('窗口=3个交易日', r0['CAR_m1_p1_窗口'] == 3, r0['CAR_m1_p1_窗口'], 3),
            ('窗口=11个交易日', r1['CAR_m5_p5_窗口'] == 11, r1['CAR_m5_p5_窗口'], 11),
            ('停牌致窗口缺失', pd.isna(r1['CAR_m5_p5']) and '有效观测不足' in str(r1['CAR_m5_p5_原因']),
             r1['CAR_m5_p5_原因'], '有效观测不足(7/11)'),
            ('未上市远期窗口缺失', pd.isna(r2['CAR_0_p250']), r2['CAR_0_p250'], 'NaN'),
            ('长期窗口计数正确', r0['CAR_0_p250_窗口'] == 251, r0['CAR_0_p250_窗口'], 251),
            ('汇总含组间检验',
             bool(len(summ) and '检验' in summ.columns
                  and (summ['检验'] == '组间t(明星-非明星)').any()),
             (len(summ), sorted(set(summ['检验'])) if len(summ) and '检验' in summ.columns else []),
             '含组间t'),
        ]
        allok = True
        for name, cond, got_, want in checks:
            allok = allok and bool(cond)
            print('  %-18s %s  得到 %s，应为 %s' % (name, 'PASS' if cond else 'FAIL', got_, want))
        print('自测%s' % ('全部通过' if allok else '有失败项'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    else:
        main()
