# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 抓上市日期，合成 data/listing_dates.csv

为什么要查两次：问财的「全部A股」口径**不含北交所**。只查一次的话，36 只北证股票
拿不到上市日期，「上市未满 6 个月」这条筛子对它们就完全失效（实测漏掉 60 条事件）。
所以要额外用「北交所股票 上市日期」补一次。

注意措辞：写成「全部北交所A股 上市日期」会被解析成全部A股（返回 5,575 行的全市场），
必须用「北交所股票 上市日期」，它返回 351 只纯北证股票。

输出列：股票代码, 股票简称, 股票市场类型, 新股上市日期（YYYYMMDD）

用法：python pull_listing_dates.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from iFinDPy import THS_iFinDLogin, THS_iFinDLogout, THS_iwencai

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
SECRET = r'C:\Users\59330\.ifind_secret'
QUERIES = ['全部A股 上市日期', '北交所股票 上市日期']
KEEP = ['股票代码', '股票简称', '股票市场类型', '新股上市日期']


def as_dict(r):
    if isinstance(r, dict):
        return r
    return {k: getattr(r, k) for k in ('errorcode', 'errmsg', 'tables', 'dataVol')
            if hasattr(r, k)}


def to_df(info):
    ts = info.get('tables')
    if not ts:
        return None
    if isinstance(ts, dict):
        ts = [ts]
    t0 = ts[0]
    tb = t0.get('table', t0) if isinstance(t0, dict) and 'table' in t0 else t0
    if isinstance(tb, dict):
        return pd.DataFrame(tb)
    return tb if hasattr(tb, 'to_dict') else None


def main():
    lines = open(SECRET, encoding='utf-8').read().strip().splitlines()
    ret = THS_iFinDLogin(lines[0].strip(), lines[1].strip())
    print('login =', ret)
    if ret != 0:
        return

    frames = []
    for q in QUERIES:
        info = as_dict(THS_iwencai(q, 'stock', 0))
        df = to_df(info)
        if df is None or len(df) == 0:
            print('%-24s 失败或无数据，ec=%r' % (q, info.get('errorcode')))
            continue
        cols = [c for c in KEEP if c in df.columns]
        df = df[cols].copy()
        nb = int(df['股票代码'].astype(str).str.endswith('.BJ').sum())
        print('%-24s -> %-6d 行，其中北证 %d 只' % (q, len(df), nb))
        frames.append(df)

    out = pd.concat(frames, ignore_index=True).drop_duplicates(subset=['股票代码'])
    path = os.path.join(DATA, 'listing_dates.csv')
    out.to_csv(path, index=False, encoding='utf-8-sig')
    print()
    print('合计 %d 只（按股票代码去重）' % len(out))
    print('其中北证 %d 只' % int(out['股票代码'].astype(str).str.endswith('.BJ').sum()))
    print('已写出 %s' % path)
    THS_iFinDLogout()


if __name__ == '__main__':
    main()
