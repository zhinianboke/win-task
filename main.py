#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Win-Task - Windows 定时任务管理系统
主程序入口文件
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from dotenv import load_dotenv

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 加载环境变量
load_dotenv()

# 创建 utils 目录和 path_utils.py 文件
def create_utils_module():
    """创建 utils 模块和 path_utils.py 文件"""
    utils_dir = os.path.join(current_dir, 'src', 'utils')
    if not os.path.exists(utils_dir):
        os.makedirs(utils_dir)
    
    # 创建 __init__.py
    init_file = os.path.join(utils_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('"""Utility modules"""')
    
    # 创建 path_utils.py
    path_utils_file = os.path.join(utils_dir, 'path_utils.py')
    if not os.path.exists(path_utils_file):
        with open(path_utils_file, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python
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
''')

# 确保 utils 模块已创建
create_utils_module()

from src.utils.path_utils import get_app_data_dir

# 创建必要的目录
def create_directories():
    """
    创建项目必要的目录结构
    """
    # 获取应用数据目录
    app_data_dir = get_app_data_dir()
    
    directories = [
        os.path.join(app_data_dir, 'tasks'),
        os.path.join(app_data_dir, 'logs')
        # 不再创建备份目录
        # os.path.join(app_data_dir, 'backups/tasks'),
    ]
    
    # 创建资源目录 (相对路径)
    resource_directories = [
        'assets/icons',
        'assets/themes'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"创建目录: {directory}")
    
    # 资源目录使用相对路径
    for directory in resource_directories:
        path = os.path.join(current_dir, directory)
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"创建资源目录: {path}")

# 配置日志
def setup_logging():
    """
    配置日志系统
    """
    # 获取应用数据目录
    app_data_dir = get_app_data_dir()
    log_dir = os.path.join(app_data_dir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'win-task.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logging.info("日志系统初始化完成")
    logging.info(f"应用数据目录: {app_data_dir}")

def main():
    """
    主程序入口函数
    """
    # 设置日志
    setup_logging()
    
    # 创建必要的目录
    create_directories()
    
    # 导入核心组件
    from src.core.settings import Settings
    from src.core.scheduler import TaskScheduler
    from src.ui.main_window import MainWindow
    
    # 初始化应用
    app = QApplication(sys.argv)
    app.setApplicationName("Win-Task")
    app.setOrganizationName("Win-Task")
    
    # 加载应用图标
    icon_path = os.path.join(current_dir, 'assets/icons/app_icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 加载设置
    settings = Settings()
    
    # 初始化任务调度器
    scheduler = TaskScheduler()
    
    # 启动调度器
    scheduler.start()
    
    # 创建并显示主窗口
    main_window = MainWindow(scheduler, settings)
    main_window.show()
    
    # 应用退出清理
    exit_code = app.exec_()
    scheduler.shutdown()
    
    logging.info("应用程序正常退出")
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 