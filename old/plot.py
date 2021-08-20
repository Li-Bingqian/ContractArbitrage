# *_* coding : UTF-8 *_*
# Auth  :   Aubree.Li
# Time  :   2021/8/17  14:43
# File  :   trade_condition.PY
# IDE   :   PyCharm
import xlsxwriter
import matplotlib.pyplot as plt
from ps_tool_kit import pd, datetime, np
from ps_tool_kit.connect_to_database import connect_sqlite
from ps_tool_kit.date_N_time import gen_trade_date

def get_mid_price(exchange, symbol, days_ls):
    """
    get ask1 and bid1 price from all tables in db
    return df_all and tables in db
    """
    path = 'C:/Users/Aubree/OneDrive - KuCoin/文档 - 铂石量化分析组/DataBase/tick_orderbook/' + exchange + '_' + symbol + '.db'
    cursor_contract = connect_sqlite(path)
    # table_names = tables_in_sqlite_db(cursor_contract)
    list_of_dataframes = []
    for table_name in days_ls:
        cursor_contract.execute("SELECT datetime, ask1_price, bid1_price FROM '%s'" % table_name)
        con_df = pd.DataFrame(cursor_contract.fetchall(), columns=['datetime', 'ask1_price', 'bid1_price']).set_index(
            'datetime')
        con_df.dropna(inplace=True)
        con_df[exchange + '_mid'] = 0.5 * (con_df['ask1_price'] + con_df['bid1_price'])
        list_of_dataframes.append(con_df)
    df = pd.concat(list_of_dataframes).dropna()
    # cursor.close()
    return df[[exchange + '_mid']].copy()


def get_spread(maker_ex, taker_ex, symbol, days):
    df1 = get_mid_price(maker_ex, symbol, days)
    df2 = get_mid_price(taker_ex, symbol, days)
    df = pd.merge(df1, df2, left_index=True, right_index=True)
    df['spread'] = df.iloc[:, 0] - df.iloc[:, 1]
    df.index = pd.to_datetime(df.index.tolist(), format='%Y-%m-%d %H:%M:%S.%f')
    return df


def trade_condition(df_spread, symbol, days_ls):
    """
    keep spread data only if there is trade within check interval
    return qualified spread data
    """
    # 1. Get trade time
    path = "C:/Users/Aubree/OneDrive - KuCoin/文档 - 铂石量化分析组/DataBase/all_trades_km/" + "Trades_KCM_" + symbol + '.db'
    cursor_trade = connect_sqlite(path)
    list_of_dataframes = []
    for table_name in days_ls:
        cursor_trade.execute("SELECT datetime FROM '%s'" % table_name)
        trade_df = pd.DataFrame(cursor_trade.fetchall(), columns=['datetime'])
        list_of_dataframes.append(trade_df)
    trade_df = pd.concat(list_of_dataframes).dropna()
    trade_df.datetime = pd.to_datetime(trade_df.datetime.tolist(), format='%Y-%m-%d %H:%M:%S.%f')

    # 2. compare the order book datetime and trade time
    df_spread['min_freq'] = df_spread.index.floor('T')
    trade_t = trade_df['datetime'].dt.floor('T').to_list()
    df_spread = df_spread[df_spread['min_freq'].isin(trade_t)]
    return df_spread.iloc[:, :3]


start_date = "2021-07-21"
end_date = "2021-07-27"
days = gen_trade_date(start_date, end_date)
take_e = 'binance'
make_e = "kumex"
pair = 'XBTUSDTM'
df_all_plot = get_spread(make_e, take_e, pair, days)
df_all_plot = trade_condition(df_all_plot, pair, days)



def plot_spread(df, symbol, time, result_path):
    """
    plot ts spread
    save the plot to result path
    """
    plt.figure(figsize=(12, 8))
    plt.plot(pd.to_datetime(df.index.tolist(), format='%Y-%m-%d %H:%M:%S.%f'), df['spread'].to_list())
    plt.ylabel("Spread")
    plt.xticks(rotation=20)
    plt.title('%s %s Spread' % (time, symbol))
    plt.savefig(result_path + '%s_%s_spread.png' % (time, symbol))



for i in df_all_plot['date'].unique():
    print(i)
    df_t = df_all_plot[df_all_plot['date'] == i].copy()
    plot_spread(df_t, pair, i, re_path)
    
re_path = './plot/0721_0727/'
alpha_ls = ['B', "C", 'D', 'E', 'F', 'G','H']

wb = xlsxwriter.Workbook(re_path + 'plot_summary.xlsx')
cell_format = wb.add_format()
cell_format.set_align('center')
cell_format.set_align('vcenter')

sheet = wb.add_worksheet('%s spread' % (pair))
sheet.write('A1', 'time')
sheet.write('A2', 'spread plot')
cell_height = 390
sheet.set_column('B:H', 100)
# sheet.set_column('D:D', 430)


x_scale = 0.5  # 固定宽度/要插入的原始图片宽
y_scale = 0.5  # 固定高度/要插入的原始图片高

i = 0
b = 2

for day in days:
    print(day)
    sheet.write('%s1' % alpha_ls[i], day)
    sheet.insert_image('%s2' % alpha_ls[i], re_path + '%s_%s_spread.png' % (day, pair), {'x_scale': x_scale, 'y_scale': y_scale})
    i += 1
    b +=1
    print(i)
sheet.set_row(0, cell_format=cell_format)
sheet.set_column('A:A', cell_format=cell_format)

wb.close()
