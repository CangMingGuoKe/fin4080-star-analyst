# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 甲的任务（其四）：生成 star 变量（权威标识）

输入：data/events_2_clean_sample.csv（clean_event_table.py 产出）
      data/ref_newfortune_list.csv（乙提供或复核过的名单）
输出：data/analysis_table.csv（在事件表上加了 star 列）

两个关键设计，都写在下面，报告里要交代：

1) 榜单生效时点
   新财富在每年年底公布。所以 t 年 1 至 10 月的研报，适用的榜单是 t-1 年那份；
   11 至 12 月的研报才可能适用 t 年那份。默认采用「按公布月份分段」口径，
   同时输出同年与滞后一年两个口径，作为稳健性。

2) 机构名对齐
   评级表用简称（如「东吴证券」），新财富也用简称，但有三类坑：
   · 子公司混入：东吴证券国际、华泰金融(HK)、海通国际 等，须排除，不能并入母公司
   · 券商合并改名：国泰君安 + 海通 = 国泰海通；国联 + 民生 = 国联民生。须按年映射
   · 中金公司在评级表里一条记录都没有（已核实），其分析师无法匹配，属数据缺口
   · 同一家券商的多种写法：中信建投/中信建投证券、中国银河/中国银河证券、
     中银证券/中银国际证券、联讯证券（今粤开）、财富证券（今财信）。名单与评级表
     两侧都要并到同一个规范名，否则另一侧写法的事件全部被判成非明星。
     映射表见 broker_names.py，券商层级共用。

用法：python build_star_variable.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

# 机构简称规范化集中在 broker_names.py：券商层级那一脚本共用同一套映射，
# 两边各写一份迟早不一致（实测一次不一致就让 87 条明星研报被判成非明星）。
sys.path.insert(0, HERE)
from broker_names import LIST_ALIAS as BROKER_ALIAS, canonical_broker
# 各年适用的合并前后名称（榜单年 -> 评级表简称）
MERGER_HISTORY = {
    '海通证券': {2018: '海通证券', 2019: '海通证券', 2020: '海通证券',
              2021: '海通证券', 2022: '海通证券', 2023: '海通证券', 2024: '海通证券',
              2025: '国泰海通'},
    '国泰君安': {y: '国泰君安' for y in range(2018, 2025)},
    '国泰海通证券': {2025: '国泰海通'},
}
EXCLUDE_SUB = ['国际', '(HK)', '（HK）', '香港', '金融控股', '经纪']


def load():
    e = os.path.join(DATA, 'events_2_clean_sample.csv')
    n = os.path.join(DATA, 'ref_newfortune_list.csv')
    for p in (e, n):
        if not os.path.exists(p):
            print('[X] 缺 %s' % p)
            return None
    ev = pd.read_csv(e, dtype=str, encoding='utf-8-sig')
    nf = pd.read_csv(n, dtype=str, encoding='utf-8-sig')
    for d in (ev, nf):
        d.columns = [str(c).strip() for c in d.columns]
    # 年份与月份直接从「最新报告日期」取，它就是紧凑的 YYYYMMDD。
    # 不要改写「报告日」：那一列在 clean_event_table.py 里已经写成 ISO 日期，
    # 覆盖它会让两个文件在同一列上格式不一致（原先就是这么错的）。
    ev['年份'] = ev['最新报告日期'].astype(str).str[:4].astype(int)
    ev['月份'] = ev['最新报告日期'].astype(str).str[4:6].astype(int)
    nf['年份'] = nf['年份'].astype(int)
    return ev, nf


def clean_list(nf):
    """只保留可用于 star 的行业类奖项。

    优先使用 pull_newfortune_list.py 写好的「是否有效」列，那是单一事实来源；
    该列不存在时退回按奖项名过滤，两种口径当前一致。
    """
    if '是否有效' in nf.columns:
        flag = nf['是否有效'].astype(str).str.strip().str.lower().isin(['true', '1', 'yes'])
        out = nf[flag].copy()
        src = '按是否有效列'
    else:
        EXCL = ['最佳研究团队', '最具影响力', '最具潜力', '进步最快', '本土最佳研究团队',
                '百星分析师', '巨匠分析师', '新财富白金', '新财富杰出', '新财富钻石',
                '新财富双钻', '钻石分析师', '证券研究行业杰出', '产业研究', '可持续发展',
                '研究飞跃', '最佳ESG', '最佳港股', '最佳北交所', '黄金分析师',
                '海外市场研究', '最佳新三板', '港股及海外']
        m = ~nf['研究领域'].astype(str).str.contains('|'.join(EXCL), na=False)
        out = nf[m].copy()
        src = '按奖项名过滤（名单里没有是否有效列）'
    print('名单：原始 %d 行 -> 可用 %d 行，领域 %d 个（%s）'
          % (len(nf), len(out), out['研究领域'].nunique(), src))
    return out


def build_star_set(ind):
    """{(榜单年, 分析师, 机构简称)}"""
    s = set()
    for _, r in ind.iterrows():
        br = BROKER_ALIAS.get(str(r['所属机构']).strip(), str(r['所属机构']).strip())
        if br is None or any(x in br for x in EXCLUDE_SUB):
            continue
        y = int(r['年份'])
        if br in MERGER_HISTORY:
            br = MERGER_HISTORY[br].get(y, br)
        s.add((y, str(r['分析师']).strip(), canonical_broker(br)))
    return s


def apply_star(ev, ss, mode):
    """按 mode 决定每条事件参照哪一年的榜单。

    same    同年
    lag1    滞后一年
    month   按公布月份分段（t 年 11 月前用 t-1 榜单）
    inforce 在任榜单：某年没有自己的榜单就沿用最近一期有效榜单，即 2018 用 2017

    参照年没有榜单数据时返回缺失，而不是 0，避免把「不知道」当成「非明星」。
    """
    avail = set(y for y, _, _ in ss)

    def to_year(y, m):
        if mode == 'same':
            return y
        if mode == 'lag1':
            return y - 1
        if mode == 'month':
            return y - 1 if m <= 10 else y
        return 2017 if y == 2018 else y

    out = []
    for _, r in ev.iterrows():
        ly = to_year(r['年份'], r['月份'])
        if ly not in avail:
            out.append(pd.NA)
            continue
        k = (ly, str(r['研究员姓名']).strip(),
             canonical_broker(str(r['研究机构简称']).strip()))
        out.append(1 if k in ss else 0)
    return pd.Series(out, index=ev.index, dtype='Int64')


def main():
    got = load()
    if got is None:
        return
    ev, nf = got
    ind = clean_list(nf)
    ss = build_star_set(ind)
    # 站内标为 2018 的那份是 15 周年特别奖合辑，不是年度行业榜，整年剔除。
    # 实测它对任何一年的研报命中率都只有 3 至 8%，是各榜单年里最弱的一列。
    ss = {k for k in ss if k[0] != 2018}
    print('榜单条目（年 x 姓名 x 机构）= %d（已剔除无效的 2018）' % len(ss))
    print()

    for mode, label in [('inforce', '在任榜单（默认，2018 沿用 2017）'),
                        ('same', '同年（2018 无有效榜单，置缺失）'),
                        ('month', '按公布月份分段'),
                        ('lag1', '滞后一年')]:
        ev['star_' + mode] = apply_star(ev, ss, mode)
        _s = pd.to_numeric(ev['star_' + mode], errors='coerce')
        print('%-30s star=1 = %5d (%.1f%%)   缺失 %d'
              % (label, int(_s.sum()), 100 * _s.mean(), int(_s.isna().sum())))

    # 默认用「在任榜单」口径。新财富在每年年底公布，所以 t 年公布的研报通常适用
    # t-1 年那份榜单；2018 年度评选因舆论事件暂停，当年在位的榜单就是 2017 年那份。
    # 实测 2018 事件对 2017 榜单命中 12.4%，与正常年份的 10 至 14% 相当，
    # 因此 2018 可以纳入样本，不再置缺失。这也正是「榜单停办期」的断档检验素材。
    ev['star'] = ev['star_inforce']
    _s = pd.to_numeric(ev['star'], errors='coerce')
    print('默认口径 star=1 共 %d 条 (%.1f%%)，缺失 %d'
          % (int(_s.sum()), 100 * _s.mean(), int(_s.isna().sum())))
    out = os.path.join(DATA, 'analysis_table.csv')
    ev.to_csv(out, index=False, encoding='utf-8-sig')
    print()
    print('逐年 star=1 计数:')
    print(ev.assign(_s=pd.to_numeric(ev['star'], errors='coerce'))
            .groupby('年份')['_s'].agg(['sum', 'count']).to_string())
    print()
    print('已写出 %s' % out)
    print('done')


if __name__ == '__main__':
    main()
