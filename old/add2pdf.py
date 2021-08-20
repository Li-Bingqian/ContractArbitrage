# *_* coding : UTF-8 *_*
# Auth  :   Aubree.Li
# Time  :   2021/8/17  18:07
# File  :   add2pdf.PY
# IDE   :   PyCharm

# from openpyxl.rawing.image import Image
import openpyxl

import matplotlib.pyplot as plt
from ps_tool_kit import pd, datetime, np
from ps_tool_kit.connect_to_database import connect_sqlite
from ps_tool_kit.date_N_time import gen_trade_date


from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image


start_date = "2021-07-21"
end_date = "2021-07-27"
days = gen_trade_date(start_date, end_date)
take_e = 'binance'
make_e = "kumex"
pair = 'XBTUSDTM'

time = days[0]
# result_path + '%s_%s_spread.png' % (time, symbol)
wb = load_workbook('./plot/0721_0726/0721_0727.xlsx') #加载这个工作簿
sheet =  wb['spread'] #选择你要操作的sheet表格
img = openpyxl.rawing.image.Image('C:/Users/Aubree/OneDrive - KuCoin/桌面/work/contract_arbitrage/plot/0721_0726/'+ '%s_%s_spread.png' % (time, pair)) #选择你的图片
sheet.add_image(img,'A1')
wb.save('C:/Users/Aubree/OneDrive - KuCoin/桌面/work/contract_arbitrage/plot/0721_0727.xlsx')
