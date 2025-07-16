#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务基类模块

定义所有任务的基础接口和通用功能
"""

import time
import uuid
import logging
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "待执行"       # 待执行
    RUNNING = "执行中"       # 执行中
    SUCCESS = "成功"       # 执行成功
    FAILED = "失败"         # 执行失败
    TIMEOUT = "超时"       # 执行超时
    CANCELED = "已取消"     # 已取消
    PAUSED = "已暂停"         # 已暂停
    SCHEDULED = "已调度"   # 已调度


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskResult:
    """任务执行结果"""
    
    def __init__(self):
        self.start_time = None        # 开始时间
        self.end_time = None          # 结束时间
        self.status = TaskStatus.PENDING  # 执行状态
        self.return_code = None       # 返回代码
        self.output = ""              # 输出信息
        self.error = ""               # 错误信息
        self.execution_time = 0       # 执行耗时(秒)
    
    def start(self):
        """开始任务计时"""
        self.start_time = datetime.now()
        self.status = TaskStatus.RUNNING
    
    def complete(self, status, return_code=0, output="", error=""):
        """完成任务"""
        self.end_time = datetime.now()
        self.status = status
        self.return_code = return_code
        self.output = output
        self.error = error
        
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
    
    @property
    def is_successful(self):
        """任务是否执行成功"""
        return self.status == TaskStatus.SUCCESS
    
    def __str__(self):
        """字符串表示"""
        return (
            f"状态: {self.status.value}, "
            f"返回码: {self.return_code}, "
            f"执行时间: {self.execution_time:.2f}秒"
        )


class BaseTask(ABC):
    """任务基类"""
    
    def __init__(self, name, description=""):
        """
        初始化任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
        """
        self.id = str(uuid.uuid4())               # 任务唯一ID
        self.name = name                          # 任务名称
        self.description = description            # 任务描述
        self.status = TaskStatus.PENDING          # 任务状态
        self.priority = TaskPriority.NORMAL       # 任务优先级
        self.schedule = None                      # 任务调度表达式
        self.timeout = 0                          # 超时时间(秒)，0表示无超时
        self.group = None                         # 任务分组
        self.tags = []                            # 任务标签
        self.retries = 0                          # 已重试次数
        self.max_retries = 0                      # 最大重试次数
        self.retry_interval = 60                  # 重试间隔(秒)
        self.dependencies = []                    # 依赖任务ID列表
        self.created_at = datetime.now()          # 创建时间
        self.updated_at = datetime.now()          # 更新时间
        self.last_run = None                      # 上次运行时间
        self.next_run = None                      # 下次运行时间
        self.history = []                         # 执行历史记录
        self.enabled = True                       # 是否启用
        
        self.logger = logging.getLogger(f"task.{self.__class__.__name__}")
    
    @abstractmethod
    def run(self):
        """
        执行任务的具体逻辑，由子类实现
        
        返回:
            TaskResult: 任务执行结果
        """
        pass
    
    def execute(self):
        """
        执行任务并处理结果
        
        返回:
            TaskResult: 任务执行结果
        """
        # 创建结果对象
        result = TaskResult()
        
        # 更新任务状态
        self.status = TaskStatus.RUNNING
        self.last_run = datetime.now()
        self.updated_at = datetime.now()
        
        # 开始计时
        result.start()
        self.logger.info(f"开始执行任务 {self.name} [{self.id}]")
        
        try:
            # 设置超时处理
            if self.timeout > 0:
                # 这里可以使用signal或线程实现超时控制
                # 简单实现
                start_time = time.time()
            
            # 执行任务实现
            task_result = self.run()
            
            # 检查超时
            if self.timeout > 0 and time.time() - start_time > self.timeout:
                result.complete(TaskStatus.TIMEOUT, -1, "", "任务执行超时")
                self.logger.warning(f"任务 {self.name} [{self.id}] 执行超时")
            else:
                # 合并结果
                if isinstance(task_result, TaskResult):
                    result = task_result
                else:
                    # 如果子类没有返回TaskResult对象，则包装结果
                    result.complete(TaskStatus.SUCCESS, 0, str(task_result))
                
                self.logger.info(f"任务 {self.name} [{self.id}] 执行完成: {result}")
        
        except Exception as e:
            # 捕获异常并记录
            error_msg = f"任务执行异常: {str(e)}"
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            self.logger.exception(f"任务 {self.name} [{self.id}] 执行失败: {str(e)}")
        
        # 更新任务状态和历史
        self.status = result.status
        self.updated_at = datetime.now()
        
        # 添加到执行历史
        execution_record = {
            'time': result.start_time,
            'status': result.status.value,
            'execution_time': result.execution_time,
            'return_code': result.return_code,
            'output': result.output,
            'error': result.error
        }
        self.history.append(execution_record)
        
        # 只保留最近的50条历史记录
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        return result
    
    def to_dict(self):
        """
        将任务转换为字典格式用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        # 处理历史记录中的datetime对象
        processed_history = []
        for record in self.history:
            processed_record = record.copy()
            if 'time' in processed_record and isinstance(processed_record['time'], datetime):
                processed_record['time'] = processed_record['time'].isoformat()
            processed_history.append(processed_record)
            
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'schedule': self.schedule,
            'timeout': self.timeout,
            'group': self.group,
            'tags': self.tags,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'retry_interval': self.retry_interval,
            'dependencies': self.dependencies,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'history': processed_history,
            'enabled': self.enabled,
            'type': self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            BaseTask: 任务对象
        """
        task = cls(data['name'], data.get('description', ''))
        task.id = data['id']
        task.status = TaskStatus(data['status'])
        task.priority = TaskPriority(data['priority'])
        task.schedule = data['schedule']
        task.timeout = data['timeout']
        task.group = data['group']
        task.tags = data['tags']
        task.retries = data['retries']
        task.max_retries = data['max_retries']
        task.retry_interval = data['retry_interval']
        task.dependencies = data['dependencies']
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.updated_at = datetime.fromisoformat(data['updated_at'])
        
        if data['last_run']:
            task.last_run = datetime.fromisoformat(data['last_run'])
        if data['next_run']:
            task.next_run = datetime.fromisoformat(data['next_run'])
            
        # 处理历史记录
        task.history = []
        for record in data.get('history', []):
            processed_record = record.copy()
            if 'time' in processed_record and isinstance(processed_record['time'], str):
                try:
                    processed_record['time'] = datetime.fromisoformat(processed_record['time'])
                except (ValueError, TypeError):
                    # 如果解析失败，保留字符串格式
                    pass
            task.history.append(processed_record)
            
        task.enabled = data.get('enabled', True)
        
        return task
    
    def __str__(self):
        """字符串表示"""
        return f"{self.name} [{self.id[:8]}] ({self.status.value})"
    
    def __repr__(self):
        """详细表示"""
        return f"<{self.__class__.__name__} id={self.id[:8]} name='{self.name}' status={self.status.value}>" 