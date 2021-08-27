# *_* coding : UTF-8 *_*
# Auth  :   Aubree.Li
# Time  :   2021/8/20  16:11
# File  :   main.PY
# IDE   :   PyCharm

# import matplotlib.pyplot as plt
from ps_tool_kit import pd, datetime, np
from ps_tool_kit.connect_to_database import connect_sqlite
from ps_tool_kit.date_N_time import gen_trade_date

import os, time, random
from datetime import timedelta


# Get daily data
def get_ob_data(exchange, symbol, days_ls, is_maker):
    """
    get ask1 and bid1 price, size from tables of days in order book db
    return df_all and tables in db
    """
    path = 'C:/Users/Aubree/OneDrive - KuCoin/文档 - 铂石量化分析组/DataBase/tick_orderbook/' + exchange + '_' + symbol + '.db'
    cursor_contract = connect_sqlite(path)
    # table_names = tables_in_sqlite_db(cursor_contract)
    list_of_dataframes = []
    ex = "m" if is_maker else "t"
    if is_maker:
        for table_name in days_ls:
            cursor_contract.execute(
                "SELECT datetime, ask1_price, bid1_price, ask1_size, bid1_size  FROM '%s'" % table_name)
            con_df = pd.DataFrame(cursor_contract.fetchall(), columns=(['datetime'] + [ex + x for x in
                                                                                       ['_ask1_price', '_bid1_price',
                                                                                        '_ask1_size',
                                                                                        '_bid1_size']])).set_index(
                'datetime')
            list_of_dataframes.append(con_df)
    else:
        for table_name in days_ls:
            cursor_contract.execute("SELECT datetime, ask1_price, bid1_price  FROM '%s'" % table_name)
            con_df = pd.DataFrame(cursor_contract.fetchall(),
                                  columns=(['datetime'] + [ex + x for x in ['_ask1_price', '_bid1_price']])).set_index(
                'datetime')
            list_of_dataframes.append(con_df)

    con_df = pd.concat(list_of_dataframes)
    con_df.dropna(inplace=True)
    con_df[ex + '_mid'] = 0.5 * (con_df[ex + '_ask1_price'] + con_df[ex + '_bid1_price'])
    list_of_dataframes.append(con_df)
    df = pd.concat(list_of_dataframes).dropna()
    # cursor.close()
    return df.copy()


def get_2ex_spread(maker_ex, taker_ex, symbol, days):
    df1 = get_ob_data(maker_ex, symbol, days, is_maker=True)
    df2 = get_ob_data(taker_ex, symbol, days, is_maker=False)
    df = pd.merge(df1, df2, left_index=True, right_index=True)
    df['mid_spread'] = df['m_mid'] - df['t_mid']
    df.index = pd.to_datetime(df.index.tolist(), format='%Y-%m-%d %H:%M:%S.%f')
    df.drop(columns=['m_mid', 't_mid'], inplace=True)
    return df


def add_rolling_window(df, window_width, update_interval_s):
    df['window'] = df.index.floor(str(update_interval_s) + 'S')
    win_statistics = df['mid_spread'].shift().rolling(str(window_width) + "s", min_periods=1).agg({np.mean, np.std})
    # win_statistics = win_statistics[win_statistics.index.isin(df.window.unique()[int(window_width/update_interval_s):])]
    win_statistics = win_statistics[
        win_statistics.index.isin(df.window.unique())]
    df = pd.merge(df, win_statistics, left_on='window', right_index=True)
    return df


def get_new_spread(df, k):
    df['spread'] = df['mid_spread']
    upper = df['mean'] + k * df['std']
    lower = df['mean'] - k * df['std']
    low_con = df['mid_spread'] <= lower
    up_con = df['mid_spread'] >= upper

    df.loc[low_con, "spread"] = df.m_ask1_price - df.t_ask1_price
    df.loc[up_con, "spread"] = df.m_bid1_price - df.t_bid1_price

    df["signal"] = 0
    df.loc[df.spread <= lower, "signal"] = -1
    df.loc[df.spread >= upper, "signal"] = 1
    return df


def test(df_all, k, window_width, update_interval_s, max_position, i):
    print('Run task %s (%s)...' % (i, os.getpid()))
    start = time.time()
    df_group = add_rolling_window(df_all, window_width, update_interval_s)
    df_group = get_new_spread(df_group, k)
    df = df_group[df_group['signal'] != 0]
    # i = 0
    # df['pos_increment'] = 0
    total_position = 0
    pos_increment = {}

    for i in range(len(df)):
        df_temp = df.iloc[i, :]
        # print (i/len(df))
        price = df_temp.m_ask1_price if df_temp.signal == -1 else df_temp.m_bid1_price
        if df_temp.signal * total_position > int(max_position / price):
            # print("pass")
            continue
        else:
            if df_temp.signal == -1:  # maker buy, taker sell. (spread < lower)
                multiplier = 0 if total_position >= 0 else -1
                pos = min((max_position / df_temp.m_ask1_price - multiplier * total_position), df_temp.m_ask1_size)
                # df_temp['pos_increment'] = round(pos)
                total_position -= round(pos)
                cost_per_size = (- df_temp.m_ask1_price * 1.8 + df_temp.m_ask1_price * 4.9) / 1e4
                pos_increment[df_temp.name] = [df_temp.signal * round(pos), total_position, cost_per_size]
            else:  # maker buy, taker sell. (spread < lower)
                multiplier = 0 if total_position <= 0 else 1
                pos = min((max_position / df_temp.m_bid1_price - multiplier * total_position), df_temp.m_bid1_size)
                # df_temp['pos_increment'] = round(pos)
                total_position += round(pos)
                cost_per_size = (- df_temp.m_ask1_price * 1.8 + df_temp.m_ask1_price * 4.9) / 1e4
                pos_increment[df_temp.name] = [df_temp.signal * round(pos), total_position, cost_per_size]

    test = pd.DataFrame(pos_increment.values(), index=pos_increment.keys(),
                        columns=['pos_increment', 'total_pos', "cost_per_size"])
    test['k'] = k
    test['window_width'] = window_width
    test['update_interval_s'] = update_interval_s

    test = pd.merge(test, df[['m_ask1_size', 'm_bid1_size', 'spread', 'signal']], left_index=True, right_index=True)
    end = time.time()
    print('Task %s runs %0.2f seconds.' % (i, (end - start)))
    test.to_csv("../data/stra_simulation/" + str(start_date) + "_" + str(end_date) + "/" + "mp_" + str(
        int(max_position / 1e4)) + "/" + str(window_width) + "_" + str(k) + '_' + str(update_interval_s) + ".csv")
    return test


start_date = "2021-07-21"
end_date = "2021-07-27"
days = gen_trade_date(start_date, end_date)
take_e = 'binance'
make_e = "kumex"
pair = 'XBTUSDTM'
df_all = get_2ex_spread(make_e, take_e, pair, days)
max_position = 1000 * 1e4

print(1)

# df_re = test(df_all, 0.5, 7200, 3600, max_position)


update_interval = [1800, 3600]
window_widths = [1800, 3600, 7200, 14400]
# update_interval = [3600]
# window_widths = [3600]
# ks = [0.01, 0.05, 0.2, 0.3]
ks = [1, 1.5, 2.0, 2.5, 3]

# para_list = []
# for u in update_interval:
#     for w in window_widths:
#         for k in ks:
#             para_list.append([k, w, u])
#
#
#
# #######################
# from multiprocessing import Pool
# import os, time, random
#
# print(1)
# if __name__ == '__main__':
#
#     print ('Parent process %s.' % os.getpid())
#     p = Pool(5)
#     for i in range(len(para_list)):
#         param = [df_all, para_list[i][0], para_list[i][1], para_list[i][2], max_position, i]
#         p.apply_async(test, args=(param,))
#     print ('Waiting for all subprocesses done...')
#     p.close()
#     p.join()
#     print ('All subprocesses done.')
#
#     #
# # print (start_date)
# #
a = []
result = pd.DataFrame(
    columns=["k", "window_width", "update_interval", "total_profit", "valid_break_num", "max_position",
             "total_trade_size"])
for w in window_widths:
    for k in ks:
        for u in update_interval:
            if u > w:
                continue
            print(k, w, u)
            df = test(df_all, k, w, u, max_position, 418)
            a.append(df)

            temp = pd.DataFrame({"k": [k], "window_width": [w], "update_interval": [u], "total_profit": [sum(
                df.pos_increment * df.spread) - sum(abs(df.pos_increment) * df.cost_per_size)], "valid_break_num": [sum(df.pos_increment != 0)],
                                 "max_position": max_position, "total_trade_size": sum(abs(df.pos_increment))})
            result = pd.concat([result, temp])
            # profit[[w, k, update_interval]] = [sum(df.pos_increment * df.spread), sum(df.pos_increment!=0)]
            # df.to_csv("../data/stra_simulation/"+str(start_date)+"_" + str(end_date) +"_"+str(w)+"_"+str(k)+".csv")

all = pd.concat(a)
result.to_csv("0721-0727_result_3000.csv")
all.to_csv("0721-0727_record_3000.csv")


print("done!")

# # 1. If only keep the record of trade, namely the list a[]
# result = pd.DataFrame(
#     columns=["k", "window_width", "update_interval", "total_profit", "valid_break_num", "max_position"])
#
# for w in window_widths:
#     for k in ks:
#         for u in update_interval:
#             print(k, u, w)
#             cond = (all['k'] == k) & (all['window_width'] == w) & (all['update_interval_s'] == u)
#             a_temp = all[cond]
#             if len(a_temp) == 0: continue
#             temp = pd.DataFrame({"k": a_temp.k[0], "window_width": a_temp.window_width[0],
#                                  "update_interval": a_temp.update_interval_s[0], "total_profit": [sum(
#                     a_temp.pos_increment * a_temp.spread) - sum(abs(a_temp.pos_increment) * a_temp.cost_per_size)],
#                                  "valid_break_num": [sum(a_temp.pos_increment != 0)],
#                                  "max_position": max_position})
#             result = pd.concat([result, temp])


# # 2. If forget to summarize trade size in result
# trade_size = []
# for i in range(len(result)):
#     k = result.k.values[i]
#     w = result.window_width.values[i]
#     u = result.update_interval.values[i]
#     cond = (all['k'] == k) & (all['window_width'] == w) & (all['update_interval_s'] == u)
#     temp = all[cond]
#     trade_size.append(sum(abs(temp.pos_increment)))
