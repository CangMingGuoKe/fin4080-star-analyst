# -*- coding: utf-8 -*-
"""iFinD 取数入口探测脚本（FIN4080 Project 10 用）

怎么跑：
  1. 先打开并登录 iFinD 终端（终端必须处于已登录状态）。
  2. 打开 PowerShell 或 VSCode 的终端，依次粘两行：
         chcp 65001
         python "D:\\Desktop\\FIN4080资料\\Project\\ifind_probe.py"
  3. 按提示输入 iFinD 账号回车，再输入密码回车（密码不显示是正常的）。
  4. 跑完后结果会同时存成同目录下的 ifind_probe_output.txt。

安全提示：密码只在运行时输入，不写文件、不打印。
         请不要把账号密码贴到任何聊天窗口里。
"""

import os
import sys
import getpass

sys.stdout.reconfigure(encoding='utf-8')

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'ifind_probe_output.txt')
_log = open(LOG_PATH, 'w', encoding='utf-8')


class _Tee(object):
    """把 print 的内容同时送到屏幕和日志文件。"""

    def __init__(self, screen, logfile):
        self.screen = screen
        self.logfile = logfile

    def write(self, s):
        try:
            self.screen.write(s)
        except Exception:
            pass
        self.logfile.write(s)
        return len(s)

    def flush(self):
        try:
            self.screen.flush()
        except Exception:
            pass
        self.logfile.flush()


sys.stdout = _Tee(sys.__stdout__, _log)

from iFinDPy import (          # noqa: E402
    THS_iFinDLogin,
    THS_DataStatistics,
    THS_HistoryQuotes,
    THS_iwencai,
    THS_BasicData,
    THS_DataPool,
    THS_DateSerial,
)


def show(label, fn, *args):
    print('=' * 70)
    print(label)
    try:
        r = fn(*args)
        if isinstance(r, dict):
            for k, v in list(r.items())[:12]:
                print('    %-12s %s' % (k, str(v)[:500]))
        else:
            print('    ', str(r)[:600])
    except Exception as e:
        print('    RAISED %s: %s' % (type(e).__name__, str(e)[:300]))
    _log.flush()


print('iFinD 取数入口探测  |  日志将写入: %s' % LOG_PATH)
print('')

user = input('iFinD 账号: ').strip()
try:
    pwd = getpass.getpass('iFinD 密码（输入时不显示）: ')
except Exception:
    pwd = input('iFinD 密码: ')

show('0. 登录 THS_iFinDLogin', THS_iFinDLogin, user, pwd)
show('1. 登录后自检 THS_DataStatistics', THS_DataStatistics, 0)

# 行情：与评级无关，能通说明账号链路本身没问题
show('2. 行情冒烟测试  000001.SZ 收盘价',
     THS_HistoryQuotes, '000001.SZ', 'close;volume', '2024-01-02', '2024-01-05')

# 问财：自然语言取数，最可能直通评级明细
show('3. 问财  近90天机构评级明细',
     THS_iwencai, '近90天机构评级明细', 'stock', 0)
show('4. 问财  机构盈利预测明细',
     THS_iwencai, '机构盈利预测明细', 'stock', 0)

# 基础数据：试探评级指标名（名字是猜的，报错信息本身也有用）
show('5. 基础数据  试探评级指标名',
     THS_BasicData, '000001.SZ', 'ths_investment_rating_stock', '', 0)

# 数据池：模板文件名就是最可能的池名
show('6. 数据池  个股盈利预测综合统计',
     THS_DataPool, '个股盈利预测综合统计', '', '', 0)

# 时间序列：按月取，用于后续做时间序列分析
show('7. 时间序列  试探评级指标名',
     THS_DateSerial, '000001.SZ', 'ths_investment_rating_stock', '', '',
     '2024-01-01', '2024-06-30', 0)

print('=' * 70)
print('探测结束。结果已保存到:')
print('   %s' % LOG_PATH)
print('把这句话告诉 Claude 即可，它会自己读这个文件。')

_log.flush()
_log.close()
