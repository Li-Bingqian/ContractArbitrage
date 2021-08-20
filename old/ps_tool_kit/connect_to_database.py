#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Time ：2021/6/17 11:17
# Auth ：shana.li
# File ：connect_to_database
# IDE ：PyCharm

import sqlite3
import paramiko
import pymysql
from pymongo import MongoClient
from sqlalchemy import create_engine


def connect_mongo(host='', db_name='', name='', pwd=''):
    """
    连接mongodb数据库，返回数据库变量
    :param host: 数据库ip地址，str
    :param db_name: 数据库名称，str
    :param name: 用户名，str
    :param pwd: 密码，str
    :return: 如果db_name是None，则返回MongoClient实例对象，否则返回Database实例对象，指向db_name数据库
    """
    client = MongoClient(host=host, port=27017, username=name, password=pwd)
    if db_name is None:
        return client
    else:
        return client[db_name]


def connect_sqlite(db_path=''):
    """
    连接sqlite数据库，返回connection.cursor实例
    :param db_path: sqlite数据库文件路径，str
    :return: connection.cursor实例对象
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    return cursor


def create_sqlite_engine(dbpath=''):
    """
    创建sqlite引擎
    :param dbpath: 数据文件路径，str
    :return: 引擎实例对象，sqlalchemy.engine.Engine()
    """
    eng = create_engine('sqlite:///' + dbpath)
    return eng


def connect_dell_host(host='', name=''):
    """
    连接dell服务器
    :param host: 服务器地址，str
    :param name: 用户名，str
    :return: paramiko.sftp_client.SFTPClient实例对象
    """
    tran = paramiko.Transport((host, 22))
    pwd = input('dell server pwd:')
    tran.connect(username=name, password=pwd)
    sftp = paramiko.SFTPClient.from_transport(tran)
    return sftp


def connect_mysql(host='', user=''):
    """
    连接mysql
    :return: pymysql.Cursor实例对象
    """
    pwd = input('dell mysql pwd:')
    conn = pymysql.connect(host=host, port=3306, user=user, password=pwd, database='market')
    return conn.cursor(cursor=pymysql.cursors.DictCursor)
