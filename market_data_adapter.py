# -*- coding: utf-8 -*-
"""Load market data from either the old panel or the cleaned Dretwd/H00300 files.

New files:
  data/stock_returns_dretwd.csv   股票代码, 日期, 个股总回报率 (decimal)
  data/market_returns_h00300.csv 日期, 市场总回报率 (decimal)

Old files:
  data/market_panel.csv, data/index_panel.csv

The adapter returns returns in percentage points, because the event-study and
accuracy engines were written in percent. Decimal inputs are multiplied by 100.
Volume is merged from the old panel when the new return file does not carry it.
"""
import os
import numpy as np
import pandas as pd

NEW_STOCK = 'stock_returns_dretwd.csv'
NEW_MKT = 'market_returns_h00300.csv'
OLD_STOCK = 'market_panel.csv'
OLD_MKT = 'index_panel.csv'


def read_any(path, **kw):
    last = None
    for enc in ('utf-8-sig', 'gbk'):
        try:
            return pd.read_csv(path, encoding=enc, **kw)
        except UnicodeDecodeError as e:
            last = e
    raise last


def date_str(s):
    return s.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(8)


def to_percent(s):
    """Decimal returns have a median absolute value below 0.5; percent returns do not."""
    x = pd.to_numeric(s, errors='coerce')
    med = float(x.abs().median()) if x.notna().any() else 0.0
    return x * 100.0 if med < 0.5 else x


def load_returns(data_dir):
    """Return (stock, market, source). stock: 股票代码, 日期, 涨跌幅, 成交量.
    market: 日期, 市场收益率."""
    sp = os.path.join(data_dir, NEW_STOCK)
    mp = os.path.join(data_dir, NEW_MKT)
    if os.path.exists(sp) and os.path.exists(mp):
        s = read_any(sp)
        s['股票代码'] = s['股票代码'].astype(str).str.strip()
        s['日期'] = date_str(s['日期'])
        s['涨跌幅'] = to_percent(s['个股总回报率'])
        old = os.path.join(data_dir, OLD_STOCK)
        if os.path.exists(old):
            o = read_any(old, usecols=['股票代码', '日期', '成交量'])
            o['股票代码'] = o['股票代码'].astype(str).str.strip()
            o['日期'] = date_str(o['日期'])
            s = s.merge(o[['股票代码', '日期', '成交量']], on=['股票代码', '日期'], how='left')
        else:
            s['成交量'] = np.nan
        m = read_any(mp)
        m['日期'] = date_str(m['日期'])
        m['市场收益率'] = to_percent(m['市场总回报率'])
        return (s[['股票代码', '日期', '涨跌幅', '成交量']],
                m[['日期', '市场收益率']], 'dretwd_h00300')

    s = read_any(os.path.join(data_dir, OLD_STOCK))
    s['股票代码'] = s['股票代码'].astype(str).str.strip()
    s['日期'] = date_str(s['日期'])
    s['涨跌幅'] = pd.to_numeric(s['涨跌幅'], errors='coerce')
    ix = read_any(os.path.join(data_dir, OLD_MKT))
    ix['日期'] = date_str(ix['日期'])
    ix = ix.sort_values('日期').drop_duplicates('日期')
    ix['市场收益率'] = pd.to_numeric(ix['收盘价'], errors='coerce').pct_change() * 100.0
    return (s[['股票代码', '日期', '涨跌幅', '成交量']],
            ix[['日期', '市场收益率']], 'old_panel')


def load_prices(data_dir):
    """Event-day closing prices come from the old panel; the new return files have none."""
    path = os.path.join(data_dir, OLD_STOCK)
    d = read_any(path, usecols=['股票代码', '日期', '收盘价'])
    d['股票代码'] = d['股票代码'].astype(str).str.strip()
    d['日期'] = date_str(d['日期'])
    d['收盘价'] = pd.to_numeric(d['收盘价'], errors='coerce')
    return d
