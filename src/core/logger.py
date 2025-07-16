#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理器模块

负责系统日志的配置和管理
"""

import os
import time
import logging
import logging.handlers
from datetime import datetime, timedelta

from src.core.settings import Settings


class LogManager:
    """日志管理器类"""
    
    def __init__(self, settings=None):
        """
        初始化日志管理器
        
        参数:
            settings (Settings, optional): 设置对象，如果为None则创建新实例
        """
        # 如果没有传入设置对象，则创建一个
        self.settings = settings or Settings()
        
        # 获取程序根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        
        # 日志目录
        self.log_dir = os.path.join(base_dir, 'data', 'logs')
        
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 日志文件
        self.main_log_file = os.path.join(self.log_dir, 'win-task.log')
        self.task_log_file = os.path.join(self.log_dir, 'task-execution.log')
        self.error_log_file = os.path.join(self.log_dir, 'error.log')
        
        # 配置主日志
        self.configure_main_logger()
        
        # 配置任务日志
        self.configure_task_logger()
        
        # 配置错误日志
        self.configure_error_logger()
        
        # 清理旧日志文件
        self.clean_old_logs()
        
        logging.info("日志管理器初始化完成")
    
    def configure_main_logger(self):
        """配置主日志记录器"""
        # 获取日志级别
        log_level_str = self.settings.log_level.upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        # 创建主日志记录器
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # 清除现有的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        
        # 文件处理器
        file_handler = logging.handlers.TimedRotatingFileHandler(
            self.main_log_file, 
            when='midnight', 
            interval=1,
            backupCount=self.settings.log_retention_days,
            encoding='utf-8'  # 明确指定UTF-8编码
        )
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        logging.info(f"主日志配置完成，级别: {log_level_str}, 文件: {self.main_log_file}")
    
    def configure_task_logger(self):
        """配置任务日志记录器"""
        # 创建任务日志记录器
        task_logger = logging.getLogger('task')
        task_logger.setLevel(logging.INFO)
        task_logger.propagate = False  # 不传递到父记录器
        
        # 清除现有的处理器
        for handler in task_logger.handlers[:]:
            task_logger.removeHandler(handler)
        
        # 文件处理器
        task_handler = logging.handlers.TimedRotatingFileHandler(
            self.task_log_file, 
            when='midnight', 
            interval=1,
            backupCount=self.settings.log_retention_days,
            encoding='utf-8'  # 明确指定UTF-8编码
        )
        task_handler.setLevel(logging.INFO)
        task_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        task_handler.setFormatter(task_format)
        
        # 添加处理器
        task_logger.addHandler(task_handler)
        
        logging.info(f"任务日志配置完成，文件: {self.task_log_file}")
    
    def configure_error_logger(self):
        """配置错误日志记录器"""
        # 创建错误日志记录器
        error_logger = logging.getLogger('error')
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = True  # 传递到父记录器
        
        # 清除现有的处理器
        for handler in error_logger.handlers[:]:
            error_logger.removeHandler(handler)
        
        # 文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # 明确指定UTF-8编码
        )
        error_handler.setLevel(logging.ERROR)
        error_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(exc_text)s\n'
        )
        error_handler.setFormatter(error_format)
        
        # 添加处理器
        error_logger.addHandler(error_handler)
        
        logging.info(f"错误日志配置完成，文件: {self.error_log_file}")
    
    def clean_old_logs(self):
        """清理过期的日志文件"""
        try:
            # 获取日志保留天数
            retention_days = self.settings.log_retention_days
            
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_timestamp = cutoff_date.timestamp()
            
            # 遍历日志目录
            for filename in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, filename)
                
                # 检查是否是文件
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    file_mtime = os.path.getmtime(file_path)
                    
                    # 如果文件修改时间早于截止日期，则删除
                    if file_mtime < cutoff_timestamp:
                        os.remove(file_path)
                        logging.debug(f"删除过期日志文件: {file_path}")
            
            logging.info(f"清理完成，删除超过 {retention_days} 天的日志文件")
        except Exception as e:
            logging.error(f"清理日志文件失败: {str(e)}")
    
    def get_task_logger(self, task_id):
        """
        获取特定任务的日志记录器
        
        参数:
            task_id (str): 任务ID
            
        返回:
            logging.Logger: 任务专用的日志记录器
        """
        # 创建任务专用的日志文件
        task_log_file = os.path.join(self.log_dir, f'task-{task_id}.log')
        
        # 创建任务专用的日志记录器
        task_logger = logging.getLogger(f'task.{task_id}')
        task_logger.setLevel(logging.INFO)
        
        # 清除现有的处理器
        for handler in task_logger.handlers[:]:
            task_logger.removeHandler(handler)
        
        # 添加文件处理器
        task_handler = logging.FileHandler(task_log_file, encoding='utf-8')  # 明确指定UTF-8编码
        task_handler.setLevel(logging.INFO)
        task_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        task_handler.setFormatter(task_format)
        task_logger.addHandler(task_handler)
        
        # 设置为不传递到父记录器，避免日志重复
        task_logger.propagate = False
        
        return task_logger
    
    def get_log_files(self):
        """
        获取所有日志文件
        
        返回:
            list: 所有日志文件的路径列表
        """
        log_files = []
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(self.log_dir, filename)
                log_files.append(file_path)
        
        return log_files
    
    def get_log_content(self, log_file, lines=100):
        """
        获取日志文件的内容
        
        参数:
            log_file (str): 日志文件路径
            lines (int): 要读取的行数
            
        返回:
            str: 日志内容
        """
        if not os.path.exists(log_file):
            return f"日志文件不存在: {log_file}"
        
        try:
            # 使用tail命令的逻辑，读取文件最后N行
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                # 使用循环缓冲区，只保留最后N行
                buffer = []
                for line in f:
                    buffer.append(line)
                    if len(buffer) > lines:
                        buffer.pop(0)
            
            # 拼接结果
            return ''.join(buffer)
        except Exception as e:
            return f"读取日志文件失败: {str(e)}" 