#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Time ：2021/6/25 11:21
# Auth ：shana.li
# File ：date_N_time
# IDE ：PyCharm

from ps_tool_kit import datetime, timedelta


def gen_trade_time(s_time='', e_time='', freq=0):
    """
    指定开始时间和结束时间，生成一段时间的交易时间列表
    :param s_time: 开始日期，str，"%Y-%m-%d %H:%M:%S.%f"
    :param e_time: 结束日期，str，"%Y-%m-%d %H:%M:%S.%f"
    :param freq: 频率，int，以秒为单位计算间隔
    :return: 交易时间列表，list，元素是交易时间，str，"%Y-%m-%d %H:%M:%S.%f"
    """
    trade_time_ls = []
    i = 0
    format_s_time = datetime.strptime(s_time, '%Y-%m-%d %H:%M:%S.%f')
    format_e_time = datetime.strptime(e_time, '%Y-%m-%d %H:%M:%S.%f')
    while 1:
        current_time = format_s_time + timedelta(seconds=freq*i)
        if current_time <= format_e_time:
            trade_time_ls.append(datetime.strftime(current_time, '%Y-%m-%d %H:%M:%S.%f')[:-3])
            i += 1
        else:
            break
    return trade_time_ls


def gen_trade_date(s_date='', e_date='', freq=1):
    """
    指定开始日期和结束日期，生成一段时间的交易日期列表
    :param s_date: 开始日期，str，"%Y-%m-%d"
    :param e_date: 结束日期，str，"%Y-%m-%d"
    :param freq: 频率，int，以天为单位计算间隔
    :return: 交易日期列表，list，元素是交易日期，str，"%Y-%m-%d"
    """
    trade_date_ls = []
    i = 0
    format_s_date = datetime.strptime(s_date, '%Y-%m-%d')
    format_e_date = datetime.strptime(e_date, '%Y-%m-%d')
    while 1:
        current_time = format_s_date + timedelta(days=freq*i)
        if current_time <= format_e_date:
            trade_date_ls.append(datetime.strftime(current_time, '%Y-%m-%d'))
            i += 1
        else:
            break
    return trade_date_ls


def shift_time(t_time='', seconds=0, direction='pre'):
    """
    时间追溯，生成由指定时间向前或者向后追溯一定时间长度后得到的日期
    :param t_time: 指定时间，str，"%Y-%m-%d %H:%M:%S.%f"
    :param seconds: 追溯时间长度，以秒为单位，int
    :param direction: 追溯方向，str，pre是向过去追溯，post是向未来追溯
    :return: 得到的追溯后目标日期，str，%Y-%m-%d"
    """
    if direction == 'pre':
        target_time = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S.%f") - timedelta(seconds=seconds)
    else:
        target_time = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S.%f") + timedelta(seconds=seconds)
    return datetime.strftime(target_time, "%Y-%m-%d %H:%M:%S.%f")[:-3]


def shift_date(t_date='', days=0, direction='pre'):
    """
    日期追溯，生成由指定日期向前或者向后追溯一定时间长度后得到的日期
    :param t_date: 指定日期，str，"%Y-%m-%d"
    :param days: 追溯日期长度，以天为单位，int
    :param direction: 追溯方向，str，pre是向过去追溯，post是向未来追溯
    :return: 得到的追溯后目标日期，str，%Y-%m-%d"
    """
    if direction == 'pre':
        target_date = datetime.strptime(t_date, "%Y-%m-%d") - timedelta(days=days)
    else:
        target_date = datetime.strptime(t_date, "%Y-%m-%d") + timedelta(days=days)
    return datetime.strftime(target_date, "%Y-%m-%d")


def gen_hour_time(t_time, direction='pre'):
    """
    根据指定时间在指定方向上生成整点时间
    :param t_time: 指定时间，str，"%Y-%m-%d %H:%M:%S.%f"
    :param direction: 追溯方向，str，pre是向过去追溯，post是向未来追溯
    :return: 指定时间在指定方向上生成整点时间，str，"%Y-%m-%d %H:%M:%S.%f"。如果指定时间是整点时间，则返回原始值
    """
    t_time1 = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%S.%f")
    if direction == 'pre':
        target_time = t_time1.replace(minute=0, second=0, microsecond=0)
    else:
        if t_time1.minute == 0 & t_time1.second == 0 & t_time1.microsecond == 0:
            target_time = t_time1
        else:
            target_time = t_time1.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return datetime.strftime(target_time, "%Y-%m-%d %H:%M:%S.%f")
