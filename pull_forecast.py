# -*- coding: utf-8 -*-
"""FIN4080 Project 10  数据抓取脚本（第二步：分析师级盈利预测 + 实际基本每股收益）

作用：
  1. 从 iFinD 问财逐年拉取 2018-2024 全市场「机构盈利预测明细」（分析师级），
     每年一个 CSV，原始行不做任何改动，只去掉列名的 [YYYYMMDD-YYYYMMDD] 窗口后缀。
  2. 探测并拉取同一区间的实际「基本每股收益」，合并成 ref_actual_eps.csv。

怎么跑：
  1. 打开并登录 iFinD 终端
  2. PowerShell 里执行：
         chcp 65001
         python "D:\\Desktop\\FIN4080资料\\Project\\pull_forecast.py"
  3. 结果落在同目录 data\\ 下。

账号：优先读 C:\\Users\\59330\\.ifind_secret（两行：账号、密码）；
      读不到则交互式询问。密码不打印、不写入任何输出。
"""

import io
import json
import os
import re
import sys
import time
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from iFinDPy import THS_iFinDLogin, THS_iFinDLogout, THS_iwencai

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'data')
SECRET = r'C:\Users\59330\.ifind_secret'
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
DOMAIN = 'stock'

# 每年措辞依次尝试，第一个出数的就用
FORECAST_PHRASINGS = [
    '{y}年 机构盈利预测明细',
    '{y}年机构盈利预测明细',
    '{y}年度 机构盈利预测明细',
]

# 实际基本每股收益的探测措辞
EPS_PHRASINGS = [
    '{y}年 基本每股收益 全部A股',
    '{y}年 每股收益 全部A股',
    '{y}年 基本每股收益',
]

EPS_TARGET = ['股票代码', '股票简称', '会计年度', '基本每股收益']


def login():
    u = p = None
    if os.path.exists(SECRET):
        lines = open(SECRET, encoding='utf-8').read().strip().splitlines()
        if len(lines) >= 2:
            u, p = lines[0].strip(), lines[1].strip()
    if not u:
        import getpass
        u = input('iFinD 账号: ').strip()
        p = getpass.getpass('iFinD 密码（不回显）: ')
    ret = THS_iFinDLogin(u, p)
    print('login_ret =', ret)
    return ret == 0


def as_dict(r):
    if isinstance(r, dict):
        return r
    return {k: getattr(r, k) for k in
            ('errorcode', 'errmsg', 'tables', 'dataVol') if hasattr(r, k)}


def to_df(info):
    ts = info.get('tables')
    if not ts:
        return None
    if isinstance(ts, dict):
        ts = [ts]
    t0 = ts[0]
    tb = t0.get('table') if isinstance(t0, dict) and 'table' in t0 else t0
    if isinstance(tb, dict):
        return pd.DataFrame(tb)
    return tb if hasattr(tb, 'to_dict') else None


def strip_suffix(name):
    """列名带 [20180101-20181231] 这样的窗口后缀，去掉以后才能逐年拼表。"""
    return re.sub(r'\[[^\]]*\]\s*$', '', str(name)).strip()


def query(q):
    """执行一次问财查询，返回 (df, errcode, errmsg, elapsed)。"""
    t0 = time.time()
    try:
        info = as_dict(THS_iwencai(q, DOMAIN, 0))
    except Exception as e:
        return None, 'EXC', str(e), time.time() - t0
    dt = time.time() - t0
    ec = info.get('errorcode')
    em = info.get('errmsg')
    if ec not in (0, None):
        return None, ec, em, dt
    df = to_df(info)
    if df is None or len(df) == 0:
        return None, 'EMPTY', em, dt
    return df, ec, em, dt


def pick_col(cols, target):
    """从列名里找目标列：先精确匹配，再含目标名的列。"""
    if target in cols:
        return target
    for c in cols:
        if target in str(c):
            return c
    return None


def main():
    if not login():
        print('[X] login failed, exit.')
        return
    os.makedirs(OUTDIR, exist_ok=True)

    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    manifest = {
        'source': 'iFinD wencai',
        'query_type': 'institution earnings forecast detail (analyst level)',
        'domain': DOMAIN,
        'pulled_at': stamp,
        'years': {},
        'eps': {'pulled_at': stamp, 'years': {}},
    }
    grand = 0

    # ---------- 1. 机构盈利预测明细 ----------
    for y in YEARS:
        print('=' * 72)
        print('year %d' % y)
        got = None
        attempts = []
        for ph in FORECAST_PHRASINGS:
            q = ph.format(y=y)
            df, ec, em, dt = query(q)
            if df is None:
                print('   %-30s FAIL ec=%r msg=%r (%.1fs)' %
                      (q, ec, str(em)[:60], dt))
                attempts.append({'query': q, 'errorcode': ec,
                                 'errmsg': str(em), 'elapsed_s': round(dt, 1)})
                continue
            print('   %-30s OK rows=%d cols=%d (%.1fs)' %
                  (q, len(df), df.shape[1], dt))
            attempts.append({'query': q, 'errorcode': ec, 'errmsg': str(em),
                             'rows': int(len(df)), 'cols': int(df.shape[1]),
                             'elapsed_s': round(dt, 1), 'status': 'OK'})
            got = (q, df)
            break

        if got is None:
            print('   [X] all phrasings failed for %d' % y)
            manifest['years'][str(y)] = {'status': 'FAILED',
                                         'attempts': attempts}
            continue

        q, df = got
        n_src = len(df)
        # 原始行保持不动，只去列名后缀
        df = df.copy()
        df.columns = [strip_suffix(c) for c in df.columns]

        out = os.path.join(OUTDIR, 'raw_forecast_%d.csv' % y)
        df.to_csv(out, index=False, encoding='utf-8-sig')
        grand += len(df)

        cols = [str(c) for c in df.columns]
        checks = {
            'report_date': any('报告日期' in c for c in cols),
            'institution': any('研究机构' in c or '机构简称' in c for c in cols),
            'analyst': any('研究人员' in c or '分析师' in c for c in cols),
            'eps_cols': [c for c in cols if '每股收益' in c],
            'beyond_4_eps': len([c for c in cols if '每股收益' in c]) > 4,
        }
        print('   saved %s rows=%d cols=%d' %
              (os.path.basename(out), len(df), df.shape[1]))
        print('   has report_date=%s institution=%s analyst=%s' %
              (checks['report_date'], checks['institution'], checks['analyst']))
        print('   eps columns (%d): %s' %
              (len(checks['eps_cols']), ' | '.join(checks['eps_cols'])))
        if len(df) != n_src:
            print('   [WARN] row count changed during column rename')

        manifest['years'][str(y)] = {
            'status': 'OK',
            'query': q,
            'rows': int(len(df)),
            'cols': int(df.shape[1]),
            'columns': cols,
            'file': os.path.basename(out),
            'size_bytes': os.path.getsize(out),
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'column_checks': checks,
            'attempts': attempts,
        }

    # ---------- 2. 实际基本每股收益 ----------
    print('=' * 72)
    print('actual basic EPS')
    eps_frames = []
    for y in YEARS:
        print('year %d' % y)
        got = None
        attempts = []
        for ph in EPS_PHRASINGS:
            q = ph.format(y=y)
            df, ec, em, dt = query(q)
            if df is None:
                print('   %-30s FAIL ec=%r msg=%r (%.1fs)' %
                      (q, ec, str(em)[:60], dt))
                attempts.append({'query': q, 'errorcode': ec,
                                 'errmsg': str(em), 'elapsed_s': round(dt, 1)})
                continue
            print('   %-30s OK rows=%d cols=%d (%.1fs)' %
                  (q, len(df), df.shape[1], dt))
            attempts.append({'query': q, 'errorcode': ec, 'errmsg': str(em),
                             'rows': int(len(df)), 'cols': int(df.shape[1]),
                             'elapsed_s': round(dt, 1), 'status': 'OK'})
            got = (q, df)
            break

        if got is None:
            print('   [X] all EPS phrasings failed for %d' % y)
            manifest['eps']['years'][str(y)] = {'status': 'FAILED',
                                                'attempts': attempts}
            continue

        q, df = got
        df = df.copy()
        df.columns = [strip_suffix(c) for c in df.columns]
        raw_cols = [str(c) for c in df.columns]

        # 保证目标列存在：会计年度缺失时用查询年份补
        if '会计年度' not in df.columns:
            df['会计年度'] = y

        cols = [str(c) for c in df.columns]
        sel = []
        for t in EPS_TARGET:
            c = pick_col(cols, t)
            if c is not None and c not in sel:
                sel.append(c)
        if not sel:
            sel = cols
        sub = df[sel].copy()
        sub['查询年份'] = y
        eps_frames.append(sub)

        manifest['eps']['years'][str(y)] = {
            'status': 'OK',
            'query': q,
            'rows': int(len(df)),
            'cols': int(df.shape[1]),
            'raw_columns': raw_cols,
            'kept_columns': sel,
            'attempts': attempts,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    if eps_frames:
        eps = pd.concat(eps_frames, ignore_index=True)
        ep = os.path.join(OUTDIR, 'ref_actual_eps.csv')
        eps.to_csv(ep, index=False, encoding='utf-8-sig')
        print('saved %s rows=%d cols=%d' %
              (os.path.basename(ep), len(eps), eps.shape[1]))
        manifest['eps']['file'] = os.path.basename(ep)
        manifest['eps']['size_bytes'] = os.path.getsize(ep)
        manifest['eps']['total_rows'] = int(len(eps))
        manifest['eps']['columns'] = [str(c) for c in eps.columns]
    else:
        print('[X] actual EPS: no data from any phrasing for any year.')
        manifest['eps']['file'] = None

    mpath = os.path.join(OUTDIR, 'forecast_pull_manifest.json')
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print('=' * 72)
    print('forecast total rows %d' % grand)
    print('manifest %s' % mpath)
    THS_iFinDLogout()
    print('logged out.')


if __name__ == '__main__':
    main()
