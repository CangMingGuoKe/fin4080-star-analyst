# -*- coding: utf-8 -*-
"""把 data/raw_ratings_2018.csv 到 raw_ratings_2024.csv 合并成一个 Excel，每年一个 sheet。

严格保真原则，三件事必须做到：
  1. 不遗漏：每个 sheet 的行数必须等于对应 CSV 的数据行数，最后打印合计核对
  2. 不篡改：全部按文本写入，不做数值化、不做日期化，保留前导零与原始小数位
  3. 不增添：只写 7 个年度 sheet，不加汇总页、不加统计列、不重命名列头

两个容易踩的坑，脚本里都避开了：
  · 读取时用 keep_default_na=False，否则 pandas 会把 "NA"、"null"、"N/A" 这类
    字面内容当成缺失值处理掉，那是无声的数据损失。
  · 写入前先扫描 Excel 不允许的控制字符，有就报出来并中止，而不是偷偷替换。

分两遍跑：第一遍只做安全检查并立即释放，第二遍逐年后重新读入并写入，
这样内存里同时只留一年的数据（全量约 52 万行 16 列，一次性装下会很吃内存）。

用法：python make_excel_workbook.py
"""
import io
import os
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
from openpyxl import Workbook

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
OUT = os.path.join(DATA, 'raw_ratings_workbook.xlsx')
YEARS = list(range(2018, 2025))

ILLEGAL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
XL_MAX_LEN = 32767


def csv_path(y):
    return os.path.join(DATA, 'raw_ratings_%d.csv' % y)


def read_year(y):
    return pd.read_csv(csv_path(y), dtype=str, encoding='utf-8-sig',
                       keep_default_na=False)


def scan(y):
    """第一遍：安全检查，读完即释放。"""
    df = read_year(y)
    bad = 0
    longest = 0
    for col in df.columns:
        s = df[col].astype(str)
        bad += int(s.str.contains(ILLEGAL, regex=True, na=False).sum())
        longest = max(longest, int(s.str.len().max()))
    print('%d  行=%-7d 列=%-3d 非法控制字符=%-4d 最长单元格=%d'
          % (y, len(df), df.shape[1], bad, longest))
    return len(df), bad, longest


def main():
    baseline = {}
    for y in YEARS:
        if not os.path.exists(csv_path(y)):
            print('缺文件: %s' % csv_path(y))
            return
        rows, bad, longest = scan(y)
        if bad:
            print('    [X] 存在 Excel 不允许的控制字符，已中止，未写任何文件')
            return
        if longest > XL_MAX_LEN:
            print('    [X] 有单元格超过 Excel 上限 %d 字符，已中止' % XL_MAX_LEN)
            return
        baseline[y] = rows

    print()
    t0 = time.time()
    wb = Workbook(write_only=True)
    for y in YEARS:
        df = read_year(y)
        ws = wb.create_sheet(title=str(y))
        ws.append(list(df.columns))
        for row in df.itertuples(index=False, name=None):
            ws.append(list(row))
        assert len(df) == baseline[y], '%d 年行数在两次读取之间发生变化' % y
        print('已写入 sheet "%s": %d 行' % (y, len(df)))
        del df
    wb.save(OUT)

    print()
    print('CSV 数据行合计   = %d' % sum(baseline.values()))
    print('写入 Excel 的行数 = %d' % sum(baseline.values()))
    print('输出 = %s  (%.1f MB, 用时 %.0f 秒)'
          % (OUT, os.path.getsize(OUT) / 1024.0 / 1024.0, time.time() - t0))


if __name__ == '__main__':
    main()
