#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Time ：2021/6/24 16:00
# Auth ：shana.li
# File ：utility_tool
# IDE ：PyCharm

from ps_tool_kit.connect_to_database import connect_sqlite

def gen_universe(s_date, e_date, ex_code):
    """
    生成一段时间内的标的池
    :param s_date: 开始日期，str，"%Y-%m-%d"
    :param e_date: 结束日期，str，"%Y-%m-%d"
    :param ex_code: 交易所代码，str，"%Y-%m-%d"
    :return: 标的列表，list，元素是标的代码，str
    """
    cursor0 = eval("%s['spot_snapshot'].distinct('symbol', {'date': {'$gte': '%s', '$lte': '%s'}})" % (
        ex_code, s_date, e_date))
    coin_universe = sorted(list(cursor0))
    return coin_universe


def gen_universe_db(db_path=''):
    """
    生成某个数据库的标的池
    :param db_path: 数据库文件路径，str
    :return: 标的列表，list，元素是标的代码，str
    """
    cursor = connect_sqlite(db_path)
    cursor.execute("SELECT name FROM main.sqlite_master WHERE type='table'")
    coin_universe = cursor.fetchall()
    coin_universe = [s[0] for s in coin_universe]
    return coin_universe
