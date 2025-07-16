#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务执行器模块

负责执行各类任务并返回执行结果
"""

import time
import logging
import threading
from datetime import datetime

from src.core.task import BaseTask, TaskStatus, TaskResult


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        """初始化任务执行器"""
        self.logger = logging.getLogger("executor")
        self.logger.info("初始化任务执行器")
        
        # 当前执行中的任务
        self.running_tasks = {}
        
        # 任务执行锁
        self.task_lock = threading.Lock()
    
    def execute(self, task):
        """
        执行任务
        
        参数:
            task (BaseTask): 要执行的任务
            
        返回:
            TaskResult: 任务执行结果
        """
        if not isinstance(task, BaseTask):
            raise TypeError("任务必须是BaseTask的子类")
        
        self.logger.info(f"开始执行任务: {task.name} [{task.id}]")
        
        # 添加到运行中的任务
        with self.task_lock:
            self.running_tasks[task.id] = {
                'task': task,
                'start_time': datetime.now()
            }
        
        # 使用线程来支持超时控制
        result = TaskResult()
        result_container = {'result': None}
        
        # 创建执行线程
        execution_thread = threading.Thread(
            target=self._execute_task_thread,
            args=(task, result_container)
        )
        execution_thread.daemon = True
        
        try:
            # 开始执行
            result.start()
            execution_thread.start()
            
            # 等待执行完成或超时
            if task.timeout > 0:
                execution_thread.join(task.timeout)
                if execution_thread.is_alive():
                    # 任务超时
                    self.logger.warning(f"任务超时: {task.name} [{task.id}] (超时: {task.timeout}秒)")
                    result.complete(TaskStatus.TIMEOUT, -1, "", "任务执行超时")
            else:
                # 如果没有超时设置，等待任务完成
                execution_thread.join()
            
            # 获取结果
            if result_container['result'] is not None and result.status != TaskStatus.TIMEOUT:
                result = result_container['result']
            
        except Exception as e:
            # 捕获异常
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(f"任务 {task.name} [{task.id}] 执行出错: {str(e)}")
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
        
        finally:
            # 从运行中的任务移除
            with self.task_lock:
                if task.id in self.running_tasks:
                    # 计算执行时间
                    start_time = self.running_tasks[task.id]['start_time']
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.logger.info(f"任务 {task.name} [{task.id}] 执行完成，耗时: {execution_time:.2f}秒")
                    del self.running_tasks[task.id]
        
        return result
    
    def _execute_task_thread(self, task, result_container):
        """
        在线程中执行任务
        
        参数:
            task (BaseTask): 要执行的任务
            result_container (dict): 用于存储结果的容器
        """
        try:
            # 调用任务的执行方法
            result = task.execute()
            result_container['result'] = result
        except Exception as e:
            # 捕获任务执行异常
            self.logger.exception(f"任务线程异常: {str(e)}")
            result = TaskResult()
            result.complete(TaskStatus.FAILED, -1, "", f"任务执行线程异常: {str(e)}")
            result_container['result'] = result
    
    def get_running_tasks(self):
        """
        获取当前正在运行的任务
        
        返回:
            dict: 运行中的任务字典
        """
        with self.task_lock:
            return {task_id: info['task'] for task_id, info in self.running_tasks.items()}
    
    def cancel_task(self, task_id):
        """
        取消正在执行的任务
        
        注意：由于 Python 线程的限制，这个方法并不能真正强制终止一个正在执行的任务，
        而是标记它为已取消，依赖于任务实现中的合作式取消检查。
        
        参数:
            task_id (str): 任务ID
            
        返回:
            bool: 操作是否成功
        """
        with self.task_lock:
            if task_id not in self.running_tasks:
                return False
            
            task_info = self.running_tasks[task_id]
            task = task_info['task']
            
            # 标记任务为已取消
            task.status = TaskStatus.CANCELED
            
            self.logger.info(f"取消任务: {task.name} [{task.id}]")
            
            return True 