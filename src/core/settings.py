#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设置管理器模块

负责程序配置的加载、保存和访问
"""

import os
import logging
import configparser
from datetime import datetime

from src.utils.path_utils import get_app_data_dir

class Settings:
    """设置管理器类"""
    
    def __init__(self, config_file=None):
        """
        初始化设置管理器
        
        参数:
            config_file (str, optional): 配置文件路径，默认为应用数据目录下的config.ini
        """
        self.logger = logging.getLogger("settings")
        
        # 如果没有指定配置文件，使用应用数据目录
        if config_file is None:
            app_data_dir = get_app_data_dir()
            config_file = os.path.join(app_data_dir, 'config.ini')
        
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 确保配置文件所在目录存在
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 加载配置
        self.load()
        self.logger.info(f"设置管理器初始化完成，配置文件: {config_file}")
    
    def load(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
                self.logger.info("成功加载配置文件")
            except Exception as e:
                self.logger.error(f"加载配置文件失败: {str(e)}")
                self._create_default_config()
        else:
            self.logger.warning("配置文件不存在，创建默认配置")
            self._create_default_config()
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            self.logger.info("配置保存成功")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, section, key, default=None, type_=str):
        """
        获取配置项
        
        参数:
            section (str): 配置节名称
            key (str): 配置项名称
            default: 默认值，如果配置不存在则返回此值
            type_ (type): 配置值的类型
            
        返回:
            配置项的值，经过类型转换
        """
        try:
            if section not in self.config:
                return default
            
            if key not in self.config[section]:
                return default
            
            value = self.config[section][key]
            
            if type_ == bool:
                return value.lower() in ('true', 'yes', 'y', '1')
            elif type_ == int:
                return int(value)
            elif type_ == float:
                return float(value)
            elif type_ == list:
                return [item.strip() for item in value.split(',')]
            else:
                return value
        except Exception as e:
            self.logger.error(f"获取配置项 [{section}]{key} 失败: {str(e)}")
            return default
    
    def set(self, section, key, value):
        """
        设置配置项
        
        参数:
            section (str): 配置节名称
            key (str): 配置项名称
            value: 配置值
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 确保section存在
            if section not in self.config:
                self.config[section] = {}
            
            # 转换value为字符串
            if isinstance(value, bool):
                str_value = 'true' if value else 'false'
            elif isinstance(value, list):
                str_value = ', '.join(str(item) for item in value)
            else:
                str_value = str(value)
            
            # 设置值
            self.config[section][key] = str_value
            
            # 保存配置
            return self.save()
        except Exception as e:
            self.logger.error(f"设置配置项 [{section}]{key} 失败: {str(e)}")
            return False
    
    def get_sections(self):
        """
        获取所有配置节
        
        返回:
            list: 所有配置节的列表
        """
        return list(self.config.sections())
    
    def get_options(self, section):
        """
        获取指定配置节下的所有配置项
        
        参数:
            section (str): 配置节名称
            
        返回:
            list: 配置项名称列表，如果节不存在则返回空列表
        """
        if section in self.config:
            return list(self.config[section].keys())
        return []
    
    def get_section_dict(self, section):
        """
        获取指定配置节的所有配置项为字典
        
        参数:
            section (str): 配置节名称
            
        返回:
            dict: 配置项的字典，如果节不存在则返回空字典
        """
        if section in self.config:
            return dict(self.config[section])
        return {}
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config['General'] = {
            'version': '1.0.0',
            'auto_start': 'false',
            'minimize_to_tray': 'false',
            'theme': 'light'
        }
        
        self.config['Scheduler'] = {
            'check_interval': '10',
            'default_timeout': '3600',
            'max_concurrent_tasks': '5',
            'max_retries': '3',
            'retry_interval': '60'
        }
        
        self.config['Logging'] = {
            'level': 'INFO',
            'retention_days': '30',
            'verbose': 'true'
        }
        
        self.config['Notification'] = {
            'enable': 'true',
            'type': 'desktop',
            'smtp_server': 'smtp.example.com',
            'smtp_port': '587',
            'smtp_user': 'user@example.com',
            'smtp_password': '',
            'email_recipient': '',
            'email_subject_prefix': '[Win-Task]'
        }
        
        self.config['Security'] = {
            'encrypt_sensitive_data': 'true',
            'backup_frequency': '7',
            'max_backups': '10'
        }
        
        # 保存默认配置
        self.save()
    
    @property
    def version(self):
        """获取应用版本"""
        return self.get('General', 'version', '1.0.0')
    
    @property
    def auto_start(self):
        """获取是否自启动"""
        return self.get('General', 'auto_start', False, bool)
    
    @auto_start.setter
    def auto_start(self, value):
        """设置是否自启动"""
        self.set('General', 'auto_start', value)
    
    @property
    def minimize_to_tray(self):
        """获取是否最小化到托盘"""
        return self.get('General', 'minimize_to_tray', False, bool)
    
    @minimize_to_tray.setter
    def minimize_to_tray(self, value):
        """设置是否最小化到托盘"""
        self.set('General', 'minimize_to_tray', value)
    
    @property
    def theme(self):
        """获取主题"""
        return self.get('General', 'theme', 'light')
    
    @theme.setter
    def theme(self, value):
        """设置主题"""
        self.set('General', 'theme', value)
    
    @property
    def check_interval(self):
        """获取任务检查间隔"""
        return self.get('Scheduler', 'check_interval', 10, int)
    
    @property
    def default_timeout(self):
        """获取默认任务超时时间"""
        return self.get('Scheduler', 'default_timeout', 3600, int)
    
    @property
    def max_concurrent_tasks(self):
        """获取最大并发任务数"""
        return self.get('Scheduler', 'max_concurrent_tasks', 5, int)
    
    @property
    def max_retries(self):
        """获取最大重试次数"""
        return self.get('Scheduler', 'max_retries', 3, int)
    
    @property
    def retry_interval(self):
        """获取重试间隔"""
        return self.get('Scheduler', 'retry_interval', 60, int)
    
    @property
    def log_level(self):
        """获取日志级别"""
        return self.get('Logging', 'level', 'INFO')
    
    @property
    def log_retention_days(self):
        """获取日志保留天数"""
        return self.get('Logging', 'retention_days', 30, int)
    
    @property
    def notification_enabled(self):
        """获取是否启用通知"""
        return self.get('Notification', 'enable', True, bool)
    
    @property
    def notification_type(self):
        """获取通知类型"""
        return self.get('Notification', 'type', 'desktop')
    
    @property
    def encrypt_sensitive_data(self):
        """获取是否加密敏感数据"""
        return self.get('Security', 'encrypt_sensitive_data', True, bool)
    
    @property
    def backup_frequency(self):
        """获取备份频率（天）"""
        return self.get('Security', 'backup_frequency', 7, int)
    
    @property
    def max_backups(self):
        """获取最大备份数量"""
        return self.get('Security', 'max_backups', 10, int) 