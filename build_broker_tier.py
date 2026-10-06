# -*- coding: utf-8 -*-
"""FIN4080 Project 10 · 甲的任务（其五）：券商层级变量

老师的「按权威分类」要三个口径：新财富上榜、资历、券商层级。
前两个已经在 events_with_star.csv 里（star、资历 两列），这一脚本补第三个。

机构身份先经 broker_names.py 规范化（同一家券商的改名与后缀变体并成一个），
再按规模排序，否则同一家被拆成两行会低估其累计份额。

口径说明：券商层级没有现成官方名单可以白拿。这里用「研究产出规模」做代理，
即该机构在 2018-2024 全样本评级记录里的条数，按**累计记录份额**切成
头部（累计到 50%）/ 中部（50% 至 90%）/ 中小（其余）。

为什么不用等份三分位：机构记录数极度偏斜，等份切会让「头部」装进 92% 的记录、
「中小」只剩 0.1%，事件样本几乎全落在头部，层级就失去了区分力。
按累计份额切，头部才是真正的少数大所。

如果想改用别的口径（例如只看覆盖股票数、或直接采用新财富机构级奖项），
改下面的 TIER_KEY 与 CUTS 即可。

输出：就地更新 data/events_with_star.csv，新增一列 券商层级。
"""
import glob
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

from broker_names import canonical_broker

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
TIER_KEY = '记录数'          # 可换成 覆盖股票数
TIERS = ['头部', '中部', '中小']
CUTS = (0.50, 0.90)          # 累计记录份额的两个切点


def main():
    files = sorted(glob.glob(os.path.join(DATA, 'ratings_*.csv')))
    raw = pd.concat([pd.read_csv(f, dtype=str, encoding='utf-8-sig') for f in files],
                    ignore_index=True)

    # 同一家券商在评级表里有多种写法（改名与后缀变体）。不归并会把它的记录数拆开，
    # 累计份额因此被低估：中信建投的真实记录数是 10266 + 4512，拆开后曾被划进中部。
    raw = raw.assign(机构=raw['研究机构简称'].map(canonical_broker))
    g = raw.groupby('机构').agg(
        记录数=('股票代码', 'size'),
        覆盖股票数=('股票代码', 'nunique'),
        分析师数=('研究员姓名', 'nunique')).reset_index()
    g = g.sort_values(TIER_KEY, ascending=False).reset_index(drop=True)

    total = g[TIER_KEY].sum()
    g['累计份额'] = g[TIER_KEY].cumsum() / total
    g['券商层级'] = TIERS[2]
    g.loc[g['累计份额'] <= CUTS[0], '券商层级'] = TIERS[0]
    g.loc[(g['累计份额'] > CUTS[0]) & (g['累计份额'] <= CUTS[1]), '券商层级'] = TIERS[1]

    print('机构总数 = %d，记录总数 = %d' % (len(g), int(total)))
    print()
    for t in TIERS:
        s = g[g['券商层级'] == t]
        print('%-4s 机构 %-3d 家   记录 %7d 条   %s'
              % (t, len(s), int(s[TIER_KEY].sum()),
                 '、'.join(s['机构'].head(6))))
    print()

    ev = pd.read_csv(os.path.join(DATA, 'events_with_star.csv'), dtype=str, encoding='utf-8-sig')
    m = dict(zip(g['机构'], g['券商层级']))
    ev['券商层级'] = ev['研究机构简称'].map(canonical_broker).map(m)
    miss = int(ev['券商层级'].isna().sum())

    out = os.path.join(DATA, 'events_with_star.csv')
    ev.to_csv(out, index=False, encoding='utf-8-sig')
    print('事件表已更新，总列数 = %d，券商层级缺失 = %d' % (len(ev.columns), miss))
    print()
    print('按 券商层级 x star 的事件分布:')
    print(pd.crosstab(ev['券商层级'], ev['star'].fillna('缺失')).to_string())
    print()
    print('已写出 %s' % out)
    print('done')


if __name__ == '__main__':
    main()
