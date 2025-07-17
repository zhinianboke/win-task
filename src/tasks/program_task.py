#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
程序执行任务模块

实现可执行程序、脚本和命令的执行
"""

import os
import sys
import time
import logging
import subprocess
import threading

from src.core.task import BaseTask, TaskStatus, TaskResult


class ProgramTask(BaseTask):
    """程序执行任务类"""
    
    def __init__(self, name, description="", command=None, working_directory=None,
                 shell=True, environment=None, capture_output=True):
        """
        初始化程序执行任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
            command (str, optional): 要执行的命令
            working_directory (str, optional): 工作目录
            shell (bool, optional): 是否使用shell执行命令
            environment (dict, optional): 环境变量
            capture_output (bool, optional): 是否捕获输出
        """
        super().__init__(name, description)
        
        # 执行参数
        self.command = command
        self.working_directory = working_directory
        self.shell = shell
        self.environment = environment
        self.capture_output = capture_output
        
        # 高级选项
        self.run_as_admin = False
        self.wait_for_completion = True
        self.success_codes = [0]  # 表示成功的返回码
        self.encoding = 'utf-8'
        self.run_detached = False  # 是否作为独立进程运行
    
    def run(self):
        """
        执行程序任务
        
        返回:
            TaskResult: 任务执行结果
        """
        result = TaskResult()
        result.start()
        
        # 日志记录
        self.logger.info(f"执行命令: {self.command}")
        if self.working_directory:
            self.logger.info(f"工作目录: {self.working_directory}")
        
        if not self.command:
            error_msg = "命令未设置"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        try:
            # 准备环境变量
            env = os.environ.copy()
            if self.environment:
                env.update(self.environment)
            
            # Windows系统中以管理员权限运行
            if self.run_as_admin and os.name == 'nt':
                from ctypes import windll
                if windll.shell32.IsUserAnAdmin() == 0:
                    self.logger.warning("请求管理员权限，但当前进程不是以管理员身份运行")
            
            # 创建进程
            kwargs = {
                'args': self.command,
                'shell': self.shell,
                'cwd': self.working_directory,
                'env': env,
            }
            
            if self.capture_output:
                kwargs.update({
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.PIPE,
                    'universal_newlines': True,
                    'encoding': self.encoding
                })
            
            # 如果是Windows并且要求分离运行
            if self.run_detached and os.name == 'nt':
                kwargs.update({
                    'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                })
            
            # 启动进程
            process = subprocess.Popen(**kwargs)
            
            # 是否等待完成
            if self.wait_for_completion:
                # 使用线程读取输出，避免阻塞
                stdout_data = ""
                stderr_data = ""
                
                if self.capture_output:
                    stdout_thread = threading.Thread(
                        target=self._read_output_stream,
                        args=(process.stdout, lambda x: stdout_data + x)
                    )
                    stderr_thread = threading.Thread(
                        target=self._read_output_stream,
                        args=(process.stderr, lambda x: stderr_data + x)
                    )
                    
                    stdout_thread.daemon = True
                    stderr_thread.daemon = True
                    
                    stdout_thread.start()
                    stderr_thread.start()
                
                # 等待进程完成
                return_code = process.wait()
                
                # 等待输出线程完成
                if self.capture_output:
                    stdout_thread.join(1)
                    stderr_thread.join(1)
                
                # 处理结果
                if return_code in self.success_codes:
                    status = TaskStatus.SUCCESS
                else:
                    status = TaskStatus.FAILED
                
                result.complete(status, return_code, stdout_data, stderr_data)
                
                # 日志记录
                if status == TaskStatus.SUCCESS:
                    self.logger.info(f"命令执行成功，返回码: {return_code}")
                else:
                    self.logger.error(f"命令执行失败，返回码: {return_code}")
                    if stderr_data:
                        self.logger.error(f"错误输出: {stderr_data}")
                
                return result
            else:
                # 不等待完成，直接返回
                self.logger.info(f"启动命令 (PID: {process.pid}) 并不等待完成")
                result.complete(TaskStatus.SUCCESS, 0, f"进程已启动，PID: {process.pid}")
                return result
            
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
    
    def _read_output_stream(self, stream, append_func):
        """
        读取输出流
        
        参数:
            stream: 流对象
            append_func: 追加数据的函数
        """
        for line in iter(stream.readline, ''):
            append_func(line)
    
    def to_dict(self):
        """
        将任务转换为字典用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        data = super().to_dict()
        
        # 添加程序任务特有字段
        data.update({
            'command': self.command,
            'working_directory': self.working_directory,
            'shell': self.shell,
            'environment': self.environment,
            'capture_output': self.capture_output,
            'run_as_admin': self.run_as_admin,
            'wait_for_completion': self.wait_for_completion,
            'success_codes': self.success_codes,
            'encoding': self.encoding,
            'run_detached': self.run_detached
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            ProgramTask: 任务对象
        """
        task = super().from_dict(data)
        
        # 设置程序任务特有字段
        task.command = data.get('command')
        task.working_directory = data.get('working_directory')
        task.shell = data.get('shell', True)
        task.environment = data.get('environment')
        task.capture_output = data.get('capture_output', True)
        task.run_as_admin = data.get('run_as_admin', False)
        task.wait_for_completion = data.get('wait_for_completion', True)
        task.success_codes = data.get('success_codes', [0])
        task.encoding = data.get('encoding', 'utf-8')
        task.run_detached = data.get('run_detached', False)
        
        return task 