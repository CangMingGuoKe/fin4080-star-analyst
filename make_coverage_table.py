# -*- coding: utf-8 -*-
"""生成 data/ref_newfortune_coverage.xlsx：每个上榜姓名在我们项目里是否可用、不可用是什么原因。

姓名经 broker_names.canonical_analyst 归一，所以同一个人的两种写法会合成一行
（例如榜单把海通证券机械行业的佘炜超写成「余炜超」，现在合成 佘炜超 一行）。

用法：python make_coverage_table.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
sys.path.insert(0, HERE)
from broker_names import from_list, canonical_broker, canonical_analyst

EXCL = ['国际', '(HK)', '（HK）', '香港', '金融控股', '经纪']
NON_EQ = ['金融工程', '固定收益', '策略研究', '宏观经济', '海外市场', '港股', '债券', '量化', '基金']


def read(name):
    return pd.read_csv(os.path.join(DATA, name), dtype=str,
                       encoding='utf-8-sig', keep_default_na=False)


def main():
    nf, tn, ev = read('ref_newfortune_list.csv'), read('ref_analyst_tenure.csv'), \
        read('analysis_table.csv')

    nf['_br'] = [from_list(n, y) for n, y in zip(nf['所属机构'], nf['年份'])]
    use = nf[nf['是否有效'].astype(str).str.strip().str.lower().isin(['true', '1', 'yes'])]
    use = use[use['年份'].astype(str) != '2018'].copy()
    use = use[use['_br'].notna()]
    use = use[~use['_br'].astype(str).apply(lambda x: any(k in x for k in EXCL))]
    use['_a'] = use['分析师'].map(canonical_analyst)

    tenure = {canonical_analyst(r['分析师']): r['首报日'] for _, r in tn.iterrows()}
    evn = ev['研究员姓名'].map(canonical_analyst).value_counts().to_dict()
    tn_names = set(tenure)

    by_team = {}
    for _, r in use.iterrows():
        by_team.setdefault((r['年份'], r['所属机构'].strip(), r['研究领域'].strip()),
                           set()).add(r['_a'])

    rows = []
    for name, g in use.groupby('_a'):
        fields = ';'.join(sorted(set(g['研究领域'].astype(str).str.strip())))
        in_tn, n_ev = name in tenure, int(evn.get(name, 0))
        reasons = []
        if not in_tn:
            if all(any(k in f for k in NON_EQ) for f in fields.split(';')):
                reasons.append('所在方向不写个股评级')
            else:
                mate = any((by_team.get((r['年份'], r['所属机构'].strip(),
                                         r['研究领域'].strip()), set()) - {name}) & tn_names
                           for _, r in g.iterrows())
                reasons.append('团队写了评级但署名未保留在他名下' if mate
                               else '所在方向不写个股评级')
        elif n_ev == 0:
            reasons.append('有资历，但样本期内没有调高或调低事件')
        rows.append([name,
                     ';'.join(sorted(set(g['年份'].astype(str)))),
                     ';'.join(sorted(set(g['_br'].astype(str)))),
                     fields,
                     '有' if in_tn else '无',
                     tenure.get(name, ''), n_ev,
                     '可用' if n_ev > 0 else '不可用',
                     '；'.join(reasons)])

    out = pd.DataFrame(rows, columns=['分析师', '上榜年份', '上榜机构', '研究领域',
                                      '在资历表', '首篇报告日', '事件条数',
                                      '是否可用于分析', '不可用的原因'])
    out = out.sort_values(['是否可用于分析', '事件条数', '分析师'],
                          ascending=[True, False, True])
    path = os.path.join(DATA, 'ref_newfortune_coverage.xlsx')
    out.to_excel(path, index=False)

    print('已写出 %s：%d 行 × %d 列' % (os.path.basename(path), len(out), len(out.columns)))
    print('可用 %d，不可用 %d' % (out['是否可用于分析'].eq('可用').sum(),
                                  out['是否可用于分析'].eq('不可用').sum()))
    print('在资历表 %d，有事件 %d，事件合计 %d'
          % (out['在资历表'].eq('有').sum(), out['事件条数'].gt(0).sum(),
             out['事件条数'].sum()))
    print('不可用原因：')
    print(out.loc[out['是否可用于分析'] == '不可用', '不可用的原因'].value_counts().to_string())
    chk = out[out['分析师'] == '佘炜超']
    if len(chk):
        print('抽查 佘炜超：%s' % chk.iloc[0].to_dict())


if __name__ == '__main__':
    main()
