# -*- coding: utf-8 -*-
"""券商名称规范化：全项目共用一套机构身份映射。

为什么要单独一个模块：star 匹配（build_star_variable.py）和券商层级
（build_broker_tier.py）都要判断「两家机构是不是同一家」。两边各写一份映射，
迟早会不一致，而一次不一致就让 87 条明星分析师的研报被判成非明星。

两类映射，目标名是同一个空间：
  TABLE_VARIANTS  评级表内部的多种写法（改名、后缀变体）-> 规范名
  LIST_ALIAS      新财富名单的写法 -> 规范名

顺序有讲究：子公司排除（EXCLUDE_SUB，见 build_star_variable.py）必须在规范化
之前做，否则「中银国际证券」这种含「国际」二字的正常券商名会被当成子公司排掉。
"""

TABLE_VARIANTS = {
    '中信建投证券': '中信建投',    # 评级表两种写法并存，记录被拆成 10266 + 4512
    '中国银河证券': '中国银河',
    '中银国际证券': '中银国际',    # 与「中银证券」是同一家（601696）
    '中银证券': '中银国际',
    '太平洋证券': '太平洋',
    '联讯证券': '粤开证券',        # 2020 年改名，旧名仍留在历史记录里
    '财富证券': '财信证券',        # 同上
}

LIST_ALIAS = {
    '中金公司': None,              # 评级表里一条记录都没有，无法匹配
    '银河证券': '中国银河',        # 名单写「银河证券」，评级表写「中国银河」
    '国联民生证券': '国联民生',
    '国泰海通证券': '国泰海通',
    '申万宏源证券': '申万宏源',
}


def canonical_broker(name):
    """评级表侧：把同一家券商的不同写法并到规范名。"""
    n = str(name).strip()
    return TABLE_VARIANTS.get(n, n)


def from_list(name):
    """名单侧：新财富写法 -> 规范名。返回 None 表示该机构在评级表里不存在。"""
    n = str(name).strip()
    n = LIST_ALIAS.get(n, n)
    return None if n is None else canonical_broker(n)

# 分析师姓名也偶有字符差错（抓榜单页面时极少数名字写错）。
# 实测一处：榜单把海通证券机械行业的佘炜超写成「余炜超」，
# 而评级明细里 641 条记录全是「佘炜超」、0 条「余炜超」，以评级明细为准。
ANALYST_ALIASES = {
    '余炜超': '佘炜超',
}


def canonical_analyst(name):
    """分析师姓名规范化：榜单侧的差错写法并到评级明细的写法。"""
    n = str(name).strip()
    return ANALYST_ALIASES.get(n, n)
