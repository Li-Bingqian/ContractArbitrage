# *_* coding : UTF-8 *_*
# Auth  :   Aubree.Li
# Time  :   2021/8/12  16:53
# File  :   utilities.PY
# IDE   :   PyCharm

import matplotlib.pyplot as plt
from ps_tool_kit import pd, datetime, np
from ps_tool_kit.connect_to_database import connect_sqlite
from ps_tool_kit.date_N_time import gen_trade_date
from datetime import timedelta


# Get all tables' name in db
# def tables_in_sqlite_db(conn):
#     """
#     find all tables in db
#     para: connection.cursor
#     return: table names list
#     """
#     cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     table_names = [
#         v[0] for v in cursor.fetchall()
#         if v[0] != "sqlite_sequence"
#     ]
#     # cursor.close()
#     return table_names


# Get daily data
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


def plot_spread(df, symbol, maker_ex, taker_ex, result_path):
    """
    plot ts spread
    save the plot to result path
    """
    plt.plot(pd.to_datetime(df.index.tolist(), format='%Y-%m-%d %H:%M:%S.%f'), df['spread'].to_list())
    plt.ylabel("Spread")
    plt.xticks(rotation=20)
    plt.title('%s_%s %s Spread' % (maker_ex, taker_ex, symbol))
    plt.savefig(result_path + '%s_%s_%s_spread.png' % (maker_ex, taker_ex, symbol))


def add_window(df, window_width):
    """
    window split
    calculate mean and std
    """
    df['window'] = (df.index - df.index[0]).total_seconds() // window_width
    window_stats = df.groupby("window")['spread'].agg([np.mean, np.std])
    return df, window_stats


def add_rolling_window(df, window_width):
    df['window'] = df.index.floor('H')
    win_statistics = df['spread'].shift().rolling(str(window_width) + "s", min_periods=1).agg({np.mean, np.std})
    win_statistics = win_statistics[win_statistics.index.isin(df.window.unique()[int(window_width/3600):])]
    return df, win_statistics


# valid times to profit, need a closing opportunity, pass through mean
def valid_calculator(df_w, direction, ref_mean):
    """
    calculate valid break number during one period
    """
    break_index = df_w.index[df_w[direction + '_signal'] == 1].to_list()
    break_index.append(df_w.index[-1])
    valid_num = 0
    valid_duration = 0
    best_spread = 0
    for i in range(len(break_index[:-1])):
        df_t = df_w[(df_w.index > break_index[i]) & (df_w.index < break_index[i + 1])]

        if len(df_t[df_t[direction + '_through_avg'] == 1]) != 0:
            valid_num += 1
            duration = (df_t[df_t[direction + '_through_avg'] == 1].index[0] - break_index[i]).seconds
            valid_duration += duration
            # best_spread = max(df_t['spread']) if direction == "up" else min(df_t("spread"))
            if direction == 'up':
                best_spread += max(df_t['spread']) - ref_mean
            else:
                best_spread += ref_mean - min(df_t['spread'])
        else:
            continue
    return valid_num, valid_duration, best_spread


def single_win_index_calculator(w, win_interval, n_std, df_g, win_statistics, df_re):
    df_w = df_g[df_g['window'] == w].copy()
    ref_mean, ref_std = win_statistics.loc[w, :]
    upper_bound = ref_mean + ref_std * n_std
    lower_bound = ref_mean - ref_std * n_std
    df_w['greater_than_up'] = np.where(df_w['spread'] > upper_bound, 1, 0)
    df_w['less_than_low'] = np.where(df_w['spread'] < lower_bound, 1, 0)
    df_w['up_through_avg'] = np.where((df_w['spread'] <= ref_mean) & (df_w['spread'].shift() > ref_mean), 1, 0)
    df_w['low_through_avg'] = np.where((df_w['spread'] >= ref_mean) & (df_w['spread'].shift() < ref_mean), 1, 0)

    df_w['up_signal'] = np.where((df_w['greater_than_up'] == 1) & (df_w['greater_than_up'].shift() == 0), 1, 0)
    df_w['low_signal'] = np.where((df_w['less_than_low'] == 1) & (df_w['less_than_low'].shift() == 0), 1, 0)

    # evaluation index
    # divide spread into 3 parts using upper, mean and lower bound
    up_proportion = sum(df_w['greater_than_up']) / len(df_w)
    low_proportion = sum(df_w['less_than_low']) / len(df_w)
    mid_proportion = 1 - up_proportion - low_proportion

    # times of passing through upper and lower bound
    break_up = sum(df_w['up_signal'])
    break_low = sum(df_w['low_signal'])

    # valid times of passing through upper and lower bound
    # valid duration
    # best profit
    valid_break_up, valid_up_duration, best_profit_up = valid_calculator(df_w, 'up', ref_mean)
    valid_break_low, valid_low_duration, best_profit_low = valid_calculator(df_w, 'low', ref_mean)
    # profit
    profit_up = valid_break_up * ref_std * n_std
    profit_low = valid_break_low * ref_std * n_std

    df_re = df_re.append(pd.DataFrame(
        [[w, win_interval, n_std, profit_up, profit_low, best_profit_up, best_profit_low, break_up, break_low,
          valid_break_up, valid_break_low, valid_up_duration, valid_low_duration,
          up_proportion, low_proportion]], columns=df_re.columns))
    return df_re


def index_calculator(n_std_list, win_interval, df_all):
    if win_interval/3600 >= 1:
        df_group, win_stat = add_rolling_window(df_all, win_interval)
    else:
        df_group, win_stat = add_window(df_all, win_interval)
    col = ["window", "win_interval", "n_std", "profit_up", "profit_low", "best_profit_up", "best_profit_low",
           "break_up", "break_low", "valid_break_up",
           "valid_break_low", "valid_up_duration", "valid_low_duration", "up_proportion", "low_proportion"]
    df_result = pd.DataFrame(columns=col)
    for n_std in n_std_list:
        print(str(win_interval), str(n_std))
        for w in win_stat.index:
            df_result = single_win_index_calculator(w, win_interval, n_std, df_group, win_stat, df_result)
    return df_result


# basic info
start_date = "2021-07-18"
end_date = "2021-07-18"
days = gen_trade_date(start_date, end_date)
take_e = 'binance'
make_e = "kumex"
pair = 'XBTUSDTM'
df_all = get_spread(make_e, take_e, pair, days)
df_all = trade_condition(df_all, pair, days)

n_std_ls = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6]
win_interval_ls = [3600, 7200, 14400, 28800, 43200, 86400]

dict_re = {}

print(1)
for win_interval in win_interval_ls:
    df_temp = index_calculator(n_std_ls, win_interval, df_all)
    # df_temp.to_csv("./index_re_" + start_date[-5:] + "_" + end_date[-5:] + "/" +str(win_interval) + ".csv")
    dict_re[win_interval] = df_temp
print("done")

df_index = pd.concat([x for x in dict_re.values()])
index_summary = df_index.groupby(["win_interval", "n_std"]).agg(
    {"profit_up": "sum", "profit_low": "sum", "best_profit_up": "sum", "best_profit_low": "sum", "break_up": "sum",
     "break_low": "sum", "valid_break_up": "sum",
     "valid_break_low": "sum", "valid_up_duration": "sum", "valid_low_duration": "sum", "up_proportion": "mean",
     "low_proportion": "mean"}).reset_index()

index_summary['daily_profit'] = (index_summary.profit_up + index_summary.profit_low) / len(days)
index_summary = index_summary[
    ["win_interval", "n_std", "daily_profit", "profit_up", "profit_low", "best_profit_up", "best_profit_low",
     "break_up", "break_low", "valid_break_up",
     "valid_break_low", "valid_up_duration", "valid_low_duration", "up_proportion", "low_proportion"]].copy()

index_summary.to_csv("./index_summary_roll_trade_" + start_date[-5:] + "_" + end_date[-5:] + ".csv")

print(1)
