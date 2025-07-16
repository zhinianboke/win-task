#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
路径工具模块

提供应用程序路径相关的工具函数
"""

import os

def get_app_data_dir():
    """
    获取应用数据目录
    
    返回:
        str: 应用数据目录路径
    """
    if os.name == 'nt':  # Windows
        app_data = os.path.join(os.environ['APPDATA'], 'WinTask')
    else:  # Linux/Mac
        app_data = os.path.join(os.path.expanduser('~'), '.wintask')
    
    if not os.path.exists(app_data):
        os.makedirs(app_data)
    return app_data
