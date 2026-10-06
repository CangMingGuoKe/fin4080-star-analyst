# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 分析师从业年限（资历）的底稿

问题：先前算「资历」用的是分析师在 2018-2024 数据里第一次出现的年份，那不是他真实的
首篇研报。2018 年就在岗的人，起点被硬顶到 2018，于是「资历」与事件年份的相关系数高达
0.759，基本只是在数日历。学术上的标准做法是：以分析师第一篇报告的日期作为职业生涯
起点，算到事件日的天数再折成年，最后在全部分析师里排分位。

要把首报日做真，必须把评级明细往前拉。早年数据只保留「每位分析师的最早日期、最早
机构与报告条数」，原始明细不落盘；2018-2024 的明细本地已有，直接读。

**措辞阶梯是本脚本的关键。** 问财的自然语言解析极不稳定，同一个年份换个说法结果就不同：
实测 2013 年用「2013年 机构评级明细」返回空，加「全部A股」后缀后返回 107,092 行；
2016、2017 年整年查询会因响应过大报 JSON 截断，拆成半年或季度就正常。
所以脚本按固定顺序逐条试，第一条出数就停，并把命中的措辞记下来。

覆盖范围：2009 至 2024。2009 是实测的数据下限，2008 及更早取不到。2010 年之前就入行的人，首报日会被记成 2010 年，属右端截断。
输出里「触到覆盖起点」一列专门标出这类人，写数据附录时要说明。

输出：data/analyst_tenure.csv
      分析师 | 首报日 | 首报年份 | 首报机构 | 报告数 | 触到覆盖起点
"""
import io
import os
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from iFinDPy import THS_iFinDLogin, THS_iFinDLogout, THS_iwencai

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
SECRET = r'C:\Users\59330\.ifind_secret'
# 2009 是数据的真实下限，已实测：2009 年有 27,059 行完整全年；
# 2008 年只有 2 行、2003 年 1 行，2004 至 2007 全部取不到。
# 所以 2009 年以前入行的分析师，在这个数据源里无法与 2009 年入行的人区分，
# 这是数据下限造成的截断，不是口径选择。输出里用「触到覆盖起点」标出这批人。
EARLY_YEARS = list(range(2009, 2018))
LOCAL_YEARS = list(range(2018, 2025))
FIRST_YEAR = EARLY_YEARS[0]


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


def query(q, pause=2.5):
    """跑一条问财查询，返回整理后的 DataFrame 或 None。失败会重试一次：
    实测同一句问法会时好时坏（2013 年整年查询一次成功一次失败），不重试会误判为无数据。"""
    for _ in range(2):
        try:
            info = as_dict(THS_iwencai(q, 'stock', 0))
            df = to_df(info)
            if df is not None and len(df):
                d = tidy(df)
                if d is not None and len(d):
                    return d
        except Exception:
            pass
        time.sleep(pause)
    return None


def fetch_year(y):
    """取一年的评级明细。

    先用整年措辞；整年取不到就拆半年；半年还不全就拆四个季度，最后把分片拼起来。

    为什么必须「累积」而不是在第一次成功处停下：半年措辞只覆盖半年。第一版脚本就是
    在第一次成功处停，结果 2012、2013、2016、2017 四年只拿到上半年，那几年的「首篇
    报告」被系统性推迟，首报年份分布里这几年的人数明显低于邻年。
    """
    for q in ['%d年 机构评级明细 全部A股' % y,
              '%d年 机构评级明细' % y,
              '%d年机构评级明细' % y]:
        d = query(q)
        if d is not None and len(d):
            m = sorted(set(d['日期'].str[4:6]))
            if m and m[0] <= '02' and m[-1] >= '11':
                return d, q
            break

    # 分片兜底。判据用「覆盖到多少个月」，不用「拼了几片」：
    # 三个季度片看着比十二个月片少，但覆盖月份数才是真信息。
    best_parts, best_cov = [], set()
    for windows, suffix in [([(1, 6), (7, 12)], ' 全部A股'),
                            ([(1, 6), (7, 12)], ''),
                            ([(1, 3), (4, 6), (7, 9), (10, 12)], ''),
                            ([(1, 3), (4, 6), (7, 9), (10, 12)], ' 全部A股')]:
        parts = []
        for a, b in windows:
            d = query('%d年%d月至%d月 机构评级明细%s' % (y, a, b, suffix))
            if d is not None and len(d):
                parts.append(d)
        cov = set()
        for d in parts:
            cov |= set(d['日期'].str[4:6])
        if len(cov) > len(best_cov):
            best_parts, best_cov = parts, cov
        if len(cov) == 12:
            break

    # 月度兜底：季度仍缺月就逐月补。实测 2012 年 10 月、11 月可取，12 月取不到。
    if best_parts and len(best_cov) < 12:
        add = []
        for m in range(1, 13):
            if '%02d' % m in best_cov:
                continue
            d = query('%d年%d月 机构评级明细' % (y, m))
            if d is not None and len(d):
                add.append(d)
                best_cov |= set(d['日期'].str[4:6])
        best_parts += add

    if best_parts:
        return pd.concat(best_parts, ignore_index=True), '分片覆盖 %d 个月' % len(best_cov)
    return None, ''


def strip_suffix(name):
    return re.sub(r'\[[^\]]*\]\s*$', '', str(name)).strip()


def tidy(df):
    df = df.copy()
    df.columns = [strip_suffix(c) for c in df.columns]
    need = ['研究员姓名', '研究机构简称', '最新报告日期']
    if any(c not in df.columns for c in need):
        return None
    d = df[need].copy()
    d.columns = ['分析师', '机构', '日期']
    d['分析师'] = d['分析师'].astype(str).str.strip()
    d['机构'] = d['机构'].astype(str).str.strip()
    d['日期'] = d['日期'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    d = d[(d['分析师'] != '') & (d['分析师'] != 'nan') & d['日期'].str.match(r'^\d{8}$')]
    return d


def main():
    lines = open(SECRET, encoding='utf-8').read().strip().splitlines()
    ret = THS_iFinDLogin(lines[0].strip(), lines[1].strip())
    print('login =', ret)
    if ret != 0:
        return

    parts = []
    log = []
    for y in EARLY_YEARS:
        d, q = fetch_year(y)
        if d is None:
            print('%d  各种措辞都取不到，该年缺失' % y)
            log.append((y, '', 0, ''))
            continue
        print('%d  %-36s 行=%-7d  %s ~ %s'
              % (y, q[:36], len(d), d['日期'].min(), d['日期'].max()))
        log.append((y, q, len(d), '%s~%s' % (d['日期'].min(), d['日期'].max())))
        parts.append(d)

    for y in LOCAL_YEARS:
        f = os.path.join(DATA, 'ratings_%d.csv' % y)
        if not os.path.exists(f):
            print('%d  缺本地文件' % y)
            continue
        d = tidy(pd.read_csv(f, dtype=str, encoding='utf-8-sig', keep_default_na=False))
        if d is not None and len(d):
            parts.append(d)
            print('%d  读本地 ratings_%d.csv 行=%d' % (y, y, len(d)))

    allrec = pd.concat(parts, ignore_index=True)
    print()
    print('合并后记录 = %d，分析师 = %d' % (len(allrec), allrec['分析师'].nunique()))

    idx = allrec.groupby('分析师')['日期'].idxmin()
    first = allrec.loc[idx, ['分析师', '日期', '机构']].copy()
    first.columns = ['分析师', '首报日', '首报机构']
    first['首报年份'] = first['首报日'].str[:4].astype(int)
    first['报告数'] = allrec.groupby('分析师').size().reindex(first['分析师']).values
    first['触到覆盖起点'] = first['首报年份'] <= FIRST_YEAR
    first = first.sort_values(['首报年份', '分析师']).reset_index(drop=True)

    path = os.path.join(DATA, 'analyst_tenure.csv')
    first.to_csv(path, index=False, encoding='utf-8-sig')

    print()
    print('===== 逐年取数记录（写进数据附录）=====')
    for y, q, n, rng in log:
        print('  %d  %-30s 行 %-7d %s' % (y, q if q else '取不到', n, rng))
    print()
    print('首报年份分布:')
    print(first['首报年份'].value_counts().sort_index().to_string())
    print()
    print('触到覆盖起点（首报年 = %d）的分析师 = %d 人，占 %.1f%%'
          % (FIRST_YEAR, int(first['触到覆盖起点'].sum()),
             100 * first['触到覆盖起点'].mean()))
    print('已写出 %s' % path)
    THS_iFinDLogout()


if __name__ == '__main__':
    main()
