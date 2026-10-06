# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 甲的任务（其一）：新财富最佳分析师名单

从公开页面抓 2017-2024 年「新财富最佳分析师」名单，统一成
    年份 | 行业代码 | 研究领域 | 名次 | 所属机构 | 分析师 | 是否有效
存成 data/ref_newfortune_list.csv。一个分析师一行（团队会被拆开）。

「是否有效」标记该行能否用于 star 变量，为 False 的只有两种情形：
  · 2018 年整年：站内那份是 15 周年特别奖合辑，不是年度行业榜
  · 机构类与个人特别荣誉：最佳研究团队、白金分析师、钻石分析师等，本来就没有名次
全表名次为空的只有 41 行，全部属于第二种，这是正常的，它们是荣誉而不是排名。

来源：慧博投研 wwws.hibor.org（主），另两个镜像作兜底。
页面不需登录、无分页，直接抓 HTML 用 pandas 解析。

用法：
    chcp 65001
    python "D:\\Desktop\\FIN4080资料\\Project\\pull_newfortune_list.py"

注意：2018 年评选因舆论事件暂停、2024 年因侵权风波中断，
      这两年可能没有完整榜单，脚本会把实情打印出来。
"""
import io
import os
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'data')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
# 2017 是给 2018 年做替补用的：2018 年度评选暂停，当年在位榜单是 2017 年那份。
YEARS = list(range(2017, 2025))
MIRRORS = [
    'http://wwws.hibor.org/author.html?year={y}&bigtype=2',
    'http://eww.hibor.com.cn/author_new.asp?year={y}&bigtype=2',
    'http://hqq.microbell.com/author_new.asp?year={y}&bigtype=2',
]
WANT = ['研究领域', '名次', '所属机构', '分析师']


def fetch(u):
    r = requests.get(u, timeout=30, headers=HEADERS)
    r.encoding = r.apparent_encoding or 'gbk'
    return r.text


def pick_table(html):
    """找出那张名单表（研究领域 / 名次 / 所属机构 / 分析师）。"""
    try:
        tabs = pd.read_html(io.StringIO(html))
    except Exception:
        return None
    for t in tabs:
        cols = [str(c).strip() for c in t.columns]
        if '研究领域' in cols and '分析师' in cols:
            return t
        if t.shape[1] >= 4 and t.shape[0] > 50:
            first = [str(v).strip() for v in t.iloc[0].tolist()]
            if '研究领域' in first and '分析师' in first:
                t2 = t.iloc[1:].copy()
                t2.columns = first
                return t2
    return None


def normalize(t, year):
    t = t.copy()
    t.columns = [str(c).strip() for c in t.columns]
    keep = {}
    for c in t.columns:
        for w in WANT:
            if c == w and w not in keep:
                keep[c] = w
    if '研究领域' not in keep.values() or '分析师' not in keep.values():
        return None
    t = t[list(keep.keys())].rename(columns=keep)
    t['研究领域'] = t['研究领域'].ffill().astype(str).str.strip()
    t['分析师'] = t['分析师'].astype(str).str.strip()
    t = t[~t['分析师'].isin(['', 'nan', 'None'])]

    rows = []
    for _, r in t.iterrows():
        field = str(r['研究领域']).strip()
        m = re.match(r'^[（(]([^）)]{1,6})[）)]\s*(.*)$', field)
        code, name = (m.group(1), m.group(2)) if m else ('', field)
        names = [p for p in re.split(r'[，,、;；/|\s]+', str(r['分析师']))
                 if p and p not in ('nan', 'None')]
        for nm in names:
            rows.append({
                '年份': year,
                '行业代码': code,
                '研究领域': name,
                '名次': str(r.get('名次', '')).strip(),
                '所属机构': str(r.get('所属机构', '')).strip(),
                '分析师': nm,
            })
    df = pd.DataFrame(rows)
    # 标记能否用于 star 变量：2018 整年不可用；机构类与个人特别荣誉没有行业排名，也不可用。
    SPECIAL = ['最佳研究团队', '最具影响力', '最具潜力', '进步最快', '本土最佳研究团队',
               '产业研究', '可持续发展', '研究飞跃', '最佳ESG', '最佳港股', '最佳北交所',
               '黄金分析师', '巨匠分析师', '百星分析师', '新财富白金', '新财富杰出',
               '新财富钻石', '新财富双钻', '钻石分析师', '证券研究行业杰出',
               '海外市场研究', '最佳新三板', '港股及海外']
    special = df['研究领域'].astype(str).str.contains('|'.join(SPECIAL), na=False)
    df['是否有效'] = (~special) & (year != 2018)
    return df


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    frames, log = [], {}
    for y in YEARS:
        got = None
        for m in MIRRORS:
            u = m.format(y=y)
            try:
                html = fetch(u)
            except Exception as e:
                print('%d  %-52s ERR %s' % (y, u[:52], str(e)[:60]))
                continue
            t = pick_table(html)
            if t is not None and len(t) > 0:
                got = (u, t)
                break
        if got is None:
            print('%d  [X] 三个镜像都没解析出名单表' % y)
            log[y] = {'status': 'FAILED'}
            continue
        u, t = got
        df = normalize(t, y)
        if df is None or df.empty:
            print('%d  [X] 表结构不符，需人工查看' % y)
            log[y] = {'status': 'BAD_TABLE'}
            continue
        frames.append(df)
        src = u.split('?')[0].split('//')[-1]
        print('%d  原始行=%-5d 行业=%-4d 上榜人次=%-5d 来源=%s'
              % (y, len(t), df['研究领域'].nunique(), len(df), src))
        print('      样例: %s | %s' % ('、'.join(df.head(3)['分析师']),
                                       df.head(1)['所属机构'].iloc[0]))
        log[y] = {'status': 'OK', 'rows_raw': int(len(t)),
                  'rows_people': int(len(df)),
                  'industries': int(df['研究领域'].nunique()), 'source': u}
        time.sleep(1)

    if frames:
        out = pd.concat(frames, ignore_index=True)
        p = os.path.join(OUTDIR, 'ref_newfortune_list.csv')
        out.to_csv(p, index=False, encoding='utf-8-sig')
        print('=' * 70)
        print('合计 %d 行 -> %s' % (len(out), p))
        print(out.groupby('年份').size().to_string())
        print('唯一分析师姓名数 =', out['分析师'].nunique())
    print('done')


if __name__ == '__main__':
    main()
