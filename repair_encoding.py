# -*- coding: utf-8 -*-
"""体检并修复 data/ 下被 Excel/WPS 另存过的 CSV。

背景：把管线里的中文 CSV 用 Excel 或 WPS 保存，编码会变成 GBK，日期会从
2018-01-01 写成 2018/1/1、84.0 写成 84，读它们的脚本当场报错（2026-10-06 中过两次）。

修复来源：仓库里跟踪的文件从 git 恢复；其余本地文件从 Project.zip 里的旧名副本恢复。
两者都拿不到时只报告，不动文件。改之前会先把原文件备份到
D:/Desktop/FIN4080资料/_gbk备份_<日期>/。

用法：
    python repair_encoding.py           体检并修复
    python repair_encoding.py --check   只体检，不动文件

注意：检测是把整个文件试着按 UTF-8 解码，不用截断的前缀——前缀会把多字节字符切一半，
造成误判（这个坑当天踩过一次，导致整批文件被无谓覆盖）。
"""
import io
import os
import shutil
import subprocess
import sys
import time
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
ZIP = os.path.join(os.path.dirname(HERE), 'Project.zip')
BAK = os.path.join(os.path.dirname(HERE), '_gbk备份_%s' % time.strftime('%Y%m%d'))

# 现名 -> 压缩包里的旧名
NEW2OLD = {
    'ref_newfortune_list.csv': 'newfortune_list.csv',
    'ref_analyst_tenure.csv': 'analyst_tenure.csv',
    'ref_listing_dates.csv': 'listing_dates.csv',
    'analysis_table.csv': 'events_with_star.csv',
    'events_1_all_revisions.csv': 'events_all.csv',
    'events_2_clean_sample.csv': 'events_clean.csv',
    'events_3_initiations.csv': 'events_first_coverage.csv',
    'ref_newfortune_missing_tenure.csv': 'newfortune_missing_tenure.csv',
    'raw_pull_manifest.json': 'pull_manifest.json',
}
for _y in range(2018, 2025):
    NEW2OLD['raw_ratings_%d.csv' % _y] = 'ratings_%d.csv' % _y


def decodes_as_utf8(path):
    """整个文件试解码，不截断。小文件直接读，大文件分块并处理块边界。"""
    import codecs
    dec = codecs.getincrementaldecoder('utf-8')()
    with open(path, 'rb') as f:
        first = True
        while True:
            chunk = f.read(4 << 20)
            if not chunk:
                break
            if first:
                chunk = chunk.lstrip(b'\xef\xbb\xbf') if chunk.startswith(b'\xef\xbb\xbf') else chunk
                first = False
            try:
                dec.decode(chunk)
            except UnicodeDecodeError:
                return False
    try:
        dec.decode(b'', True)
    except UnicodeDecodeError:
        return False
    return True


def main():
    check_only = '--check' in sys.argv
    tracked = set(subprocess.run(['git', '-C', HERE, 'ls-files'], capture_output=True,
                                 text=True, encoding='utf-8').stdout.split())
    zf = zipfile.ZipFile(ZIP) if os.path.exists(ZIP) else None
    znames = set(zf.namelist()) if zf else set()
    if zf is None:
        print('提示：找不到 %s，本地文件将只能靠 git 恢复' % ZIP)

    bad = []
    print('=== data/ 体检 ===')
    for f in sorted(os.listdir(DATA)):
        p = os.path.join(DATA, f)
        if not os.path.isfile(p) or f.lower().endswith(('.xlsx', '.xls', '.zip')):
            continue
        ok = decodes_as_utf8(p)
        print('  %-42s %-4s %10s' % (f, 'OK' if ok else 'GBK', os.path.getsize(p)))
        if not ok:
            bad.append(f)

    print()
    if not bad:
        print('全部正常，无需修复')
        return
    print('发现 %d 个非 UTF-8 文件：%s' % (len(bad), '、'.join(bad)))
    if check_only:
        print('（--check 模式，未改动任何文件）')
        return

    os.makedirs(BAK, exist_ok=True)
    print('原文件备份到 %s' % BAK)
    for f in bad:
        p = os.path.join(DATA, f)
        shutil.copy2(p, os.path.join(BAK, f))
        how = None
        if ('data/' + f) in tracked:
            subprocess.run(['git', '-C', HERE, 'checkout', '--', 'data/' + f])
            if decodes_as_utf8(p):
                how = 'git'
        if how is None and zf is not None:
            old = NEW2OLD.get(f)
            zp = 'Project/data/' + old if old else None
            if zp and zp in znames:
                with open(p, 'wb') as out:
                    out.write(zf.read(zp))
                if decodes_as_utf8(p):
                    how = 'Project.zip'
        print('  %-42s %s' % (f, ('已用 %s 恢复' % how) if how else '!! 没有可用来源，未改动'))
    print()
    print('修复后请重跑：clean_event_table.py -> build_star_variable.py -> build_broker_tier.py')


if __name__ == '__main__':
    main()
