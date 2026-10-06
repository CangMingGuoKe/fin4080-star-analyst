# -*- coding: utf-8 -*-
"""FIN4080 Project 10  数据抓取脚本（第一步：机构评级明细 = 事件表）

作用：从 iFinD 问财取 2018-2024 全市场「机构评级明细」，逐年存成 CSV。
数据源：iFinD 问财（自然语言取数），只读查询，不修改任何数据。

怎么跑：
    1. 打开并登录 iFinD 终端
    2. PowerShell 里执行：
           chcp 65001
           python "D:\\Desktop\\FIN4080资料\\Project\\pull_ifind_ratings.py"
    3. 结果落在同目录的 data\\ 下，逐年一个 CSV，另有一份 manifest.json

为什么逐年拉：一次性拉 2018-2024 会返回「数据为空」（问财对超长区间不稳定）。
为什么每种措辞都试：问财是自然语言解析，加不加空格结果会不一样，
    实测 2023 年必须写成「2023年 机构评级明细」（中间有空格）才出数。

账号：优先读 C:\\Users\\59330\\.ifind_secret（两行：账号、密码）；
      读不到则交互式询问。密码不打印、不写入输出。
"""

import io
import json
import os
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from iFinDPy import THS_iFinDLogin, THS_iFinDLogout, THS_iwencai

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'data')
SECRET = r'C:\Users\59330\.ifind_secret'
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
DOMAIN = 'stock'

# 每种措辞依次尝试，第一个出数的就用它
PHRASINGS = ['{y}年 机构评级明细', '{y}年机构评级明细', '{y}年度 机构评级明细']
# 每年行数的合理下界（实测 6 万到 10 万），低于此值视为被截断，需要检查
MIN_ROWS = 30000


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


def clean(df, year):
    df = df.copy()
    df.columns = [strip_suffix(c) for c in df.columns]
    df['数据年份'] = year
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: '' if v is None else str(v))
    return df


def date_col(df):
    for c in df.columns:
        if '报告日期' in c:
            return c
    return None


def main():
    if not login():
        print('[X] 登录失败，退出。')
        return
    os.makedirs(OUTDIR, exist_ok=True)

    manifest = {'source': 'iFinD 问财 · 机构评级明细', 'domain': DOMAIN,
                'years': {}, 'outdir': OUTDIR}
    grand = 0

    for y in YEARS:
        print('=' * 72)
        print('年份 %d' % y)
        got = None
        for ph in PHRASINGS:
            q = ph.format(y=y)
            t0 = time.time()
            try:
                info = as_dict(THS_iwencai(q, DOMAIN, 0))
            except Exception as e:
                print('   %-24s EXC %s' % (q, str(e)[:80]))
                continue
            dt = time.time() - t0
            if info.get('errorcode') not in (0, None):
                print('   %-24s ec=%r %s' % (q, info.get('errorcode'),
                                             str(info.get('errmsg'))[:40]))
                continue
            df = to_df(info)
            if df is None or len(df) == 0:
                print('   %-24s 空表' % q)
                continue
            print('   %-24s 成功 rows=%d 耗时=%.1fs' % (q, len(df), dt))
            got = (q, df)
            break

        if got is None:
            print('   [X] 该年所有措辞都没出数，需要人工排查')
            manifest['years'][str(y)] = {'status': 'FAILED'}
            continue

        q, df = got
        df = clean(df, y)
        dc = date_col(df)
        rng = ''
        if dc:
            ds = df[dc].astype(str).str.replace(r'\.0$', '', regex=True)
            rng = '%s ~ %s' % (ds.min(), ds.max())

        path = os.path.join(OUTDIR, 'ratings_%d.csv' % y)
        df.to_csv(path, index=False, encoding='utf-8-sig')
        grand += len(df)

        warn = '' if len(df) >= MIN_ROWS else '  <== 行数偏低，检查是否被截断'
        print('   保存 %s  rows=%d  日期 %s%s' % (os.path.basename(path), len(df), rng, warn))
        manifest['years'][str(y)] = {
            'status': 'OK', 'query': q, 'rows': int(len(df)),
            'date_range': rng, 'file': os.path.basename(path),
            'columns': list(df.columns)}

    mpath = os.path.join(OUTDIR, 'pull_manifest.json')
    with open(mpath, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print('=' * 72)
    print('合计 %d 行，明细见 %s' % (grand, mpath))
    THS_iFinDLogout()
    print('已登出。')


if __name__ == '__main__':
    main()
