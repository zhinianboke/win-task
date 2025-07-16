#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务执行线程模块

提供后台执行任务的线程类
"""

import logging
from PyQt5.QtCore import QThread, pyqtSignal


class TaskExecutionThread(QThread):
    """任务执行线程类"""
    
    # 定义信号
    taskFinished = pyqtSignal(object)  # 任务完成信号，参数为任务结果
    taskError = pyqtSignal(str)        # 任务错误信号，参数为错误消息
    
    def __init__(self, scheduler, task_id):
        """
        初始化任务执行线程
        
        参数:
            scheduler: 任务调度器
            task_id: 要执行的任务ID
        """
        super().__init__()
        self.scheduler = scheduler
        self.task_id = task_id
        self.logger = logging.getLogger("task_thread")
    
    def run(self):
        """执行线程的主方法"""
        try:
            # 执行任务
            self.logger.debug(f"开始在线程中执行任务: {self.task_id}")
            result = self.scheduler.run_task_now(self.task_id)
            
            # 发送完成信号
            self.taskFinished.emit(result)
            
        except Exception as e:
            # 记录错误
            error_msg = f"任务执行线程异常: {str(e)}"
            self.logger.error(error_msg)
            
            # 发送错误信号
            self.taskError.emit(error_msg)
            
            # 发送完成信号，结果为None
            self.taskFinished.emit(None) 