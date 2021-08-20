# *_* coding : UTF-8 *_*
# Auth  :   Aubree.Li
# Time  :   2021/8/18  16:46
# File  :   show.PY
# IDE   :   PyCharm

import matplotlib.pyplot as plt
from ps_tool_kit import pd, datetime, np
from ps_tool_kit.connect_to_database import connect_sqlite
from ps_tool_kit.date_N_time import gen_trade_date
from datetime import timedelta

# Final summary
index_21_27 = pd.read_csv("./index_summary_roll_trade_07-21_07-27.csv", index_col=0)
index_25_27 = pd.read_csv("./index_summary_roll_trade_07-25_07-27.csv", index_col=0)
index_21_24 = pd.read_csv("./index_summary_roll_trade_07-21_07-24.csv", index_col=0)
index_18 = pd.read_csv("./index_summary_roll_trade_07-18_07-18.csv", index_col=0)

# No rolling
index_no_roll_17_27 = pd.read_csv("./noroll/index_summary_trade_0717_0727.csv", index_col=0)

# No trade No rolling
index_no_trade_no_roll = pd.read_csv("./noroll/index_summary_no_trade.csv", index_col=0)

print(1)