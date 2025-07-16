#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cron表达式解析器模块

提供Cron表达式的解析、验证和计算下次执行时间功能
"""

import re
import logging
from datetime import datetime, timedelta
from croniter import croniter


class CronParser:
    """Cron表达式解析器"""
    
    def __init__(self):
        """初始化Cron解析器"""
        self.logger = logging.getLogger("cron_parser")
    
    def validate(self, cron_expression):
        """
        验证Cron表达式是否有效
        
        参数:
            cron_expression (str): Cron表达式
            
        返回:
            bool: 表达式是否有效
        """
        try:
            # 尝试创建croniter对象进行验证
            croniter(cron_expression)
            return True
        except ValueError as e:
            self.logger.warning(f"无效的Cron表达式 '{cron_expression}': {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"验证Cron表达式出错 '{cron_expression}': {str(e)}")
            return False
    
    def get_next_execution_time(self, cron_expression, start_time=None):
        """
        计算下次执行时间
        
        参数:
            cron_expression (str): Cron表达式
            start_time (datetime, optional): 开始时间，默认为当前时间
            
        返回:
            datetime: 下次执行时间，如果表达式无效则返回None
        """
        if not start_time:
            start_time = datetime.now()
        
        try:
            cron = croniter(cron_expression, start_time)
            return cron.get_next(datetime)
        except Exception as e:
            self.logger.error(f"计算下次执行时间出错 '{cron_expression}': {str(e)}")
            return None
    
    def get_next_n_execution_times(self, cron_expression, n=5, start_time=None):
        """
        计算接下来n次执行时间
        
        参数:
            cron_expression (str): Cron表达式
            n (int): 要计算的执行次数
            start_time (datetime, optional): 开始时间，默认为当前时间
            
        返回:
            list: 接下来n次执行时间的列表，如果表达式无效则返回空列表
        """
        if not start_time:
            start_time = datetime.now()
        
        try:
            cron = croniter(cron_expression, start_time)
            return [cron.get_next(datetime) for _ in range(n)]
        except Exception as e:
            self.logger.error(f"计算多次执行时间出错 '{cron_expression}': {str(e)}")
            return []
    
    def get_previous_execution_time(self, cron_expression, start_time=None):
        """
        计算上次执行时间
        
        参数:
            cron_expression (str): Cron表达式
            start_time (datetime, optional): 开始时间，默认为当前时间
            
        返回:
            datetime: 上次执行时间，如果表达式无效则返回None
        """
        if not start_time:
            start_time = datetime.now()
        
        try:
            cron = croniter(cron_expression, start_time)
            return cron.get_prev(datetime)
        except Exception as e:
            self.logger.error(f"计算上次执行时间出错 '{cron_expression}': {str(e)}")
            return None
    
    def get_human_readable_description(self, cron_expression):
        """
        获取Cron表达式的可读描述
        
        参数:
            cron_expression (str): Cron表达式
            
        返回:
            str: 可读描述，如果表达式无效则返回错误信息
        """
        if not self.validate(cron_expression):
            return "无效的Cron表达式"
        
        try:
            # 解析Cron表达式各个部分
            parts = cron_expression.split()
            if len(parts) != 5:
                return "无效的Cron表达式格式"
            
            minute, hour, day_of_month, month, day_of_week = parts
            
            # 分钟部分描述
            minute_desc = self._describe_field(minute, "分钟", 0, 59)
            
            # 小时部分描述
            hour_desc = self._describe_field(hour, "小时", 0, 23)
            
            # 日期部分描述
            if day_of_month == "*" and day_of_week == "*":
                day_desc = "每天"
            else:
                dom_desc = self._describe_field(day_of_month, "日", 1, 31)
                dow_desc = self._describe_day_of_week(day_of_week)
                
                if day_of_month == "*":
                    day_desc = dow_desc
                elif day_of_week == "*":
                    day_desc = dom_desc
                else:
                    day_desc = f"{dom_desc}或{dow_desc}"
            
            # 月份部分描述
            month_desc = self._describe_month(month)
            
            # 组合描述
            if month == "*":
                if day_of_month == "*" and day_of_week == "*":
                    return f"每天{hour_desc}{minute_desc}"
                else:
                    return f"{month_desc}{day_desc}{hour_desc}{minute_desc}"
            else:
                return f"{month_desc}{day_desc}{hour_desc}{minute_desc}"
                
        except Exception as e:
            self.logger.error(f"生成Cron表达式描述出错 '{cron_expression}': {str(e)}")
            return "无法解析Cron表达式"
    
    def _describe_field(self, field, name, min_val, max_val):
        """
        描述Cron表达式的单个字段
        
        参数:
            field (str): 字段值
            name (str): 字段名称
            min_val (int): 最小值
            max_val (int): 最大值
            
        返回:
            str: 字段描述
        """
        if field == "*":
            return f"每{name}"
        
        if "," in field:
            values = field.split(",")
            return f"在{name} {', '.join(values)}时"
        
        if "-" in field:
            start, end = field.split("-")
            return f"在{name} {start}至{end}之间的每{name}"
        
        if "/" in field:
            base, step = field.split("/")
            if base == "*":
                return f"每隔{step}{name}"
            else:
                return f"从{base}开始每隔{step}{name}"
        
        return f"在{name} {field}时"
    
    def _describe_day_of_week(self, day_of_week):
        """
        描述星期字段
        
        参数:
            day_of_week (str): 星期字段值
            
        返回:
            str: 星期描述
        """
        # 星期映射
        day_names = {
            "0": "星期日", 
            "1": "星期一", 
            "2": "星期二", 
            "3": "星期三", 
            "4": "星期四", 
            "5": "星期五", 
            "6": "星期六",
            "7": "星期日"
        }
        
        if day_of_week == "*":
            return "每天"
        
        if "," in day_of_week:
            days = day_of_week.split(",")
            day_names_list = [day_names.get(d, d) for d in days]
            return f"在 {', '.join(day_names_list)}"
        
        if "-" in day_of_week:
            start, end = day_of_week.split("-")
            start_name = day_names.get(start, start)
            end_name = day_names.get(end, end)
            return f"在{start_name}至{end_name}之间的每天"
        
        if "/" in day_of_week:
            base, step = day_of_week.split("/")
            if base == "*":
                return f"每隔{step}天"
            else:
                base_name = day_names.get(base, base)
                return f"从{base_name}开始每隔{step}天"
        
        return f"在{day_names.get(day_of_week, day_of_week)}"
    
    def _describe_month(self, month):
        """
        描述月份字段
        
        参数:
            month (str): 月份字段值
            
        返回:
            str: 月份描述
        """
        # 月份映射
        month_names = {
            "1": "一月", "2": "二月", "3": "三月", "4": "四月", 
            "5": "五月", "6": "六月", "7": "七月", "8": "八月", 
            "9": "九月", "10": "十月", "11": "十一月", "12": "十二月"
        }
        
        if month == "*":
            return "每月"
        
        if "," in month:
            months = month.split(",")
            month_names_list = [month_names.get(m, m) for m in months]
            return f"在 {', '.join(month_names_list)}"
        
        if "-" in month:
            start, end = month.split("-")
            start_name = month_names.get(start, start)
            end_name = month_names.get(end, end)
            return f"在{start_name}至{end_name}之间的每月"
        
        if "/" in month:
            base, step = month.split("/")
            if base == "*":
                return f"每隔{step}个月"
            else:
                base_name = month_names.get(base, base)
                return f"从{base_name}开始每隔{step}个月"
        
        return f"在{month_names.get(month, month)}"
    
    def create_cron_expression(self, minute="*", hour="*", day_of_month="*", month="*", day_of_week="*"):
        """
        创建Cron表达式
        
        参数:
            minute (str): 分钟 (0-59)
            hour (str): 小时 (0-23)
            day_of_month (str): 日期 (1-31)
            month (str): 月份 (1-12)
            day_of_week (str): 星期 (0-6, 0=星期日)
            
        返回:
            str: Cron表达式
        """
        cron_expression = f"{minute} {hour} {day_of_month} {month} {day_of_week}"
        
        # 验证表达式
        if not self.validate(cron_expression):
            self.logger.warning(f"创建了无效的Cron表达式: {cron_expression}")
        
        return cron_expression 