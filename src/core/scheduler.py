#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务调度器模块

负责任务的调度、执行和管理
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from croniter import croniter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from src.core.task import BaseTask, TaskStatus, TaskPriority
from src.core.executor import TaskExecutor
from src.utils.notifier import Notifier
from src.utils.path_utils import get_app_data_dir

import random
import re


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.logger = logging.getLogger("scheduler")
        self.logger.info("初始化任务调度器")
        
        # 任务存储
        self.tasks = {}
        
        # 创建APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        
        # 监听任务事件
        self.scheduler.add_listener(self._job_event_listener, 
                                    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
        
        # 任务执行器
        self.executor = TaskExecutor()
        
        # 通知管理器
        self.notifier = Notifier()
        
        # 任务执行锁
        self.task_lock = threading.Lock()
        
        # 运行中的任务
        self.running_tasks = {}
        
        # 配置参数
        self.max_concurrent_tasks = 5
        self.default_timeout = 3600
        self.max_retries = 3
        self.retry_interval = 60
        
        # 获取应用数据目录
        app_data_dir = get_app_data_dir()
        
        # 存储路径
        self.data_dir = os.path.join(app_data_dir, 'tasks')
        self.backup_dir = os.path.join(app_data_dir, 'backups/tasks')
        self.log_dir = os.path.join(app_data_dir, 'logs')
        
        # 确保目录存在
        for directory in [self.data_dir, self.backup_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"创建目录: {directory}")
    
    def start(self):
        """启动调度器"""
        self.logger.info("启动任务调度器")
        
        # 先启动调度器
        self.scheduler.start()
        self.logger.info("调度器已启动")
        
        # 再加载任务
        self.load_tasks()
        
        # 已禁用自动备份任务
        # self.scheduler.add_job(
        #     self.backup_tasks,
        #     trigger=CronTrigger(hour=3, minute=0),  # 每天凌晨3点
        #     id='backup_tasks',
        #     name='自动备份任务',
        #     replace_existing=True
        # )
    
    def shutdown(self):
        """关闭调度器"""
        self.logger.info("关闭任务调度器")
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.save_tasks()
        # 备份功能已禁用
        # self.backup_tasks()
    
    def add_task(self, task):
        """
        添加新任务
        
        参数:
            task (BaseTask): 要添加的任务
            
        返回:
            str: 任务ID
        """
        if not isinstance(task, BaseTask):
            raise TypeError("任务必须是BaseTask的子类")
        
        # 设置默认值
        if task.timeout == 0:
            task.timeout = self.default_timeout
        if task.max_retries == 0:
            task.max_retries = self.max_retries
        if task.retry_interval == 60:
            task.retry_interval = self.retry_interval
        
        # 添加到任务字典
        self.tasks[task.id] = task
        
        # 如果任务有调度表达式并且已启用，则调度任务
        if task.schedule and task.enabled:
            self._schedule_task(task)
        
        self.logger.info(f"添加任务: {task.name} [{task.id}]")
        
        # 保存任务
        self.save_tasks()
        
        return task.id
    
    def update_task(self, task_id, **kwargs):
        """
        更新现有任务
        
        参数:
            task_id (str): 任务ID
            **kwargs: 要更新的任务属性
            
        返回:
            bool: 更新是否成功
        """
        if task_id not in self.tasks:
            self.logger.warning(f"尝试更新不存在的任务: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        # 更新任务属性
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # 更新时间戳
        task.updated_at = datetime.now()
        
        # 如果调度信息更新了，需要重新调度
        if 'schedule' in kwargs or 'enabled' in kwargs:
            # 移除现有的调度
            self._remove_schedule(task_id)
            
            # 如果任务启用并且有调度表达式，则重新调度
            if task.enabled and task.schedule:
                self._schedule_task(task)
        
        self.logger.info(f"更新任务: {task.name} [{task.id}]")
        
        # 保存任务
        self.save_tasks()
        
        return True
    
    def remove_task(self, task_id):
        """
        删除任务
        
        参数:
            task_id (str): 任务ID
            
        返回:
            bool: 删除是否成功
        """
        if task_id not in self.tasks:
            self.logger.warning(f"尝试删除不存在的任务: {task_id}")
            return False
        
        # 先移除调度
        self._remove_schedule(task_id)
        
        # 从字典中删除
        task = self.tasks.pop(task_id)
        
        self.logger.info(f"删除任务: {task.name} [{task.id}]")
        
        # 保存任务
        self.save_tasks()
        
        return True
    
    def get_task(self, task_id):
        """
        获取任务
        
        参数:
            task_id (str): 任务ID
            
        返回:
            BaseTask: 任务对象，如果不存在则返回None
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """
        获取所有任务
        
        返回:
            list: 所有任务对象的列表
        """
        return list(self.tasks.values())
    
    def get_tasks_by_group(self, group):
        """
        获取指定分组的任务
        
        参数:
            group (str): 分组名称
            
        返回:
            list: 该分组下的任务列表
        """
        return [task for task in self.tasks.values() if task.group == group]
    
    def get_tasks_by_status(self, status):
        """
        获取指定状态的任务
        
        参数:
            status (TaskStatus): 任务状态
            
        返回:
            list: 该状态的任务列表
        """
        if isinstance(status, str):
            status = TaskStatus(status)
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_tag(self, tag):
        """
        获取包含指定标签的任务
        
        参数:
            tag (str): 标签名称
            
        返回:
            list: 包含该标签的任务列表
        """
        return [task for task in self.tasks.values() if tag in task.tags]
    
    def run_task_now(self, task_id):
        """
        立即执行任务
        
        参数:
            task_id (str): 任务ID
            
        返回:
            TaskResult: 任务执行结果，如果任务不存在则返回None
        """
        if task_id not in self.tasks:
            self.logger.warning(f"尝试执行不存在的任务: {task_id}")
            return None
        
        task = self.tasks[task_id]
        
        # 检查依赖任务是否都已完成
        if not self._check_dependencies(task):
            self.logger.warning(f"任务 {task.name} [{task.id}] 的依赖任务未完成，不能执行")
            return None
        
        # 执行任务
        self.logger.info(f"手动执行任务: {task.name} [{task.id}]")
        return self._execute_task(task)
    
    def pause_task(self, task_id):
        """
        暂停任务
        
        参数:
            task_id (str): 任务ID
            
        返回:
            bool: 操作是否成功
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 更新状态
        task.status = TaskStatus.PAUSED
        task.enabled = False
        task.updated_at = datetime.now()
        
        # 移除调度
        self._remove_schedule(task_id)
        
        self.logger.info(f"暂停任务: {task.name} [{task.id}]")
        
        # 保存任务
        self.save_tasks()
        
        return True
    
    def resume_task(self, task_id):
        """
        恢复任务
        
        参数:
            task_id (str): 任务ID
            
        返回:
            bool: 操作是否成功
        """
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 更新状态
        if task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.PENDING
        task.enabled = True
        task.updated_at = datetime.now()
        
        # 添加调度
        if task.schedule:
            self._schedule_task(task)
        
        self.logger.info(f"恢复任务: {task.name} [{task.id}]")
        
        # 保存任务
        self.save_tasks()
        
        return True
    
    def load_tasks(self, auto_restore_from_backup=True):
        """
        加载保存的任务
        
        参数:
            auto_restore_from_backup (bool): 如果加载失败，是否自动从备份恢复
        """
        self.logger.info("加载保存的任务")
        
        # 确保目录存在
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                self.logger.info(f"创建任务数据目录: {self.data_dir}")
            except Exception as e:
                self.logger.error(f"创建任务数据目录失败: {str(e)}")
            return
        
        # 删除临时文件
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.tmp'):
                try:
                    os.remove(os.path.join(self.data_dir, filename))
                    self.logger.debug(f"删除临时文件: {filename}")
                except Exception as e:
                    self.logger.error(f"删除临时文件 {filename} 失败: {str(e)}")
        
        # 清空现有任务
        self.tasks = {}
        
        # 动态导入所有任务类型
        try:
            import src.tasks
            task_classes = getattr(src.tasks, 'TASK_CLASSES', {})
        except ImportError:
            task_classes = {}
            self.logger.error("无法导入任务模块")
        
        # 遍历任务目录下的所有文件
        successful_loads = 0
        failed_loads = 0
        
        for filename in os.listdir(self.data_dir):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.data_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        task_data = json.load(f)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"任务文件 {filename} JSON解析失败: {str(e)}")
                        failed_loads += 1
                        continue

                # 任务数据完整性检查
                required_fields = ['id', 'name', 'type', 'created_at', 'updated_at']
                if not all(field in task_data for field in required_fields):
                    self.logger.error(f"任务文件 {filename} 缺少必要字段")
                    failed_loads += 1
                    continue

                # 导入任务类型
                try:
                    task_type = task_data.get('type', 'BaseTask')

                    # 先从注册的任务类型中查找
                    if task_type in task_classes:
                        task_class = task_classes[task_type]
                    else:
                        # 尝试从 src.tasks 模块动态导入
                        try:
                            task_module = __import__('src.tasks', fromlist=['tasks'])
                            if hasattr(task_module, task_type):
                                task_class = getattr(task_module, task_type)
                            else:
                                # 尝试通过模块名导入
                                module_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', task_type).lower()
                                task_module = __import__(f'src.tasks.{module_name}', fromlist=[task_type])
                                task_class = getattr(task_module, task_type)
                        except (ImportError, AttributeError) as e:
                            raise ImportError(f"无法导入任务类型 {task_type}: {str(e)}")

                except (ImportError, AttributeError) as e:
                    self.logger.error(f"导入任务类型 {task_type} 失败: {str(e)}")
                    failed_loads += 1
                    continue

                # 创建任务对象
                try:
                    task = task_class.from_dict(task_data)
                    # 添加到任务字典
                    self.tasks[task.id] = task

                    # 如果任务启用并且有调度表达式，则调度任务
                    if task.enabled and task.schedule:
                        try:
                            self._schedule_task(task)
                        except Exception as e:
                            self.logger.warning(f"调度任务 {task.name} [{task.id}] 失败: {str(e)}")

                    self.logger.info(f"加载任务: {task.name} [{task.id}]")
                    successful_loads += 1

                except Exception as e:
                    self.logger.error(f"从数据创建任务对象失败: {str(e)}")
                    failed_loads += 1
                    continue

            except Exception as e:
                self.logger.error(f"加载任务文件 {filename} 失败: {str(e)}")
                failed_loads += 1
        
        self.logger.info(f"任务加载完成: 成功 {successful_loads}, 失败 {failed_loads}")
        
        # 自动备份恢复功能已禁用
        # if auto_restore_from_backup and failed_loads > 0 and successful_loads == 0 and os.path.exists(self.backup_dir):
        #     self.logger.warning("所有任务加载失败，尝试从最近备份恢复")
        #     self.restore_tasks_from_backup()
    
    def save_tasks(self):
        """保存所有任务到文件"""
        self.logger.info("保存任务数据")
        
        # 确保目录存在
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                self.logger.info(f"创建任务数据目录: {self.data_dir}")
            except Exception as e:
                self.logger.error(f"创建任务数据目录失败: {str(e)}")
                return
        
        # 如果没有任务，删除所有现有任务文件
        if not self.tasks:
            try:
                for filename in os.listdir(self.data_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.data_dir, filename))
                self.logger.info("没有任务，清空任务目录")
            except Exception as e:
                self.logger.error(f"清空任务目录失败: {str(e)}")
            return
            
        saved_task_ids = set()
        for task_id, task in self.tasks.items():
            try:
                # 将任务序列化为字典
                task_data = task.to_dict()
                
                # 使用临时文件保存，避免写入时中断导致文件损坏
                file_path = os.path.join(self.data_dir, f"{task_id}.json")
                temp_file_path = file_path + ".tmp"
                
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump(task_data, f, ensure_ascii=False, indent=2)
                
                # 如果写入成功，替换原文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                os.rename(temp_file_path, file_path)
                
                saved_task_ids.add(task_id)
                self.logger.debug(f"保存任务: {task.name} [{task.id}]")
            except Exception as e:
                self.logger.error(f"保存任务 {task.name} [{task.id}] 失败: {str(e)}")
        
        # 删除不存在的任务文件
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    file_id = filename.split('.')[0]
                    if file_id not in saved_task_ids:
                        os.remove(os.path.join(self.data_dir, filename))
                        self.logger.debug(f"删除不存在的任务文件: {filename}")
        except Exception as e:
            self.logger.error(f"清理过期任务文件失败: {str(e)}")
    
    def _schedule_task(self, task):
        """
        调度任务
        
        参数:
            task (BaseTask): 要调度的任务
        """
        try:
            # 解析调度表达式
            if task.schedule.startswith('cron:'):
                # Cron 表达式
                cron_expr = task.schedule[5:]
                trigger = CronTrigger.from_crontab(cron_expr)
                
                # 计算下次运行时间
                cron = croniter(cron_expr, datetime.now())
                task.next_run = cron.get_next(datetime)
                
            elif task.schedule.startswith('interval:'):
                # 间隔表达式，格式为 interval:n(s|m|h|d)
                interval_expr = task.schedule[9:]
                interval_value = int(interval_expr[:-1])
                interval_unit = interval_expr[-1]
                
                # 根据单位转换为秒
                if interval_unit == 's':
                    seconds = interval_value
                elif interval_unit == 'm':
                    seconds = interval_value * 60
                elif interval_unit == 'h':
                    seconds = interval_value * 3600
                elif interval_unit == 'd':
                    seconds = interval_value * 86400
                else:
                    raise ValueError(f"不支持的间隔单位: {interval_unit}")
                
                trigger = IntervalTrigger(seconds=seconds)
                
                # 计算下次运行时间
                task.next_run = datetime.now() + timedelta(seconds=seconds)
                
            elif task.schedule.startswith('date:'):
                # 指定日期时间，格式为 date:YYYY-MM-DD HH:MM:SS
                date_str = task.schedule[5:]
                run_date = datetime.fromisoformat(date_str)
                trigger = DateTrigger(run_date=run_date)
                
                # 设置下次运行时间
                task.next_run = run_date
                
            else:
                self.logger.error(f"不支持的调度表达式: {task.schedule}")
                return
            
            # 添加到调度器
            self.scheduler.add_job(
                self._run_scheduled_task,
                trigger=trigger,
                args=[task.id],
                id=task.id,
                name=task.name,
                replace_existing=True
            )
            
            # 更新任务状态
            task.status = TaskStatus.SCHEDULED
            task.updated_at = datetime.now()
            
            self.logger.info(f"调度任务: {task.name} [{task.id}], 下次执行: {task.next_run}")
            
        except Exception as e:
            self.logger.error(f"调度任务 {task.name} [{task.id}] 失败: {str(e)}")
    
    def _remove_schedule(self, task_id):
        """
        移除任务调度
        
        参数:
            task_id (str): 任务ID
        """
        try:
            self.scheduler.remove_job(task_id)
            self.logger.debug(f"移除任务调度: {task_id}")
        except Exception:
            # 如果任务没有被调度，会抛出异常，可以忽略
            pass
    
    def _run_scheduled_task(self, task_id):
        """
        执行调度任务的回调函数
        
        参数:
            task_id (str): 任务ID
        """
        if task_id not in self.tasks:
            self.logger.warning(f"调度了不存在的任务: {task_id}")
            return
        
        task = self.tasks[task_id]
        
        # 检查依赖任务是否都已完成
        if not self._check_dependencies(task):
            self.logger.warning(f"任务 {task.name} [{task.id}] 的依赖任务未完成，跳过执行")
            return
        
        # 检查是否达到最大并发数
        with self.task_lock:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                self.logger.warning(f"达到最大并发任务数，延迟执行任务: {task.name} [{task.id}]")
                
                # 稍后重试
                retry_seconds = 30
                threading.Timer(retry_seconds, self._run_scheduled_task, [task_id]).start()
                return
        
        # 执行任务
        self.logger.info(f"执行调度任务: {task.name} [{task.id}]")
        
        # 在新线程中执行任务，避免阻塞调度线程
        thread = threading.Thread(
            target=self._execute_task_and_handle_result,
            args=(task,)
        )
        thread.daemon = True
        thread.start()
        
        # 更新下次执行时间
        if task.schedule and task.schedule.startswith('cron:'):
            cron_expr = task.schedule[5:]
            cron = croniter(cron_expr, datetime.now())
            task.next_run = cron.get_next(datetime)
        elif task.schedule and task.schedule.startswith('interval:'):
            interval_expr = task.schedule[9:]
            interval_value = int(interval_expr[:-1])
            interval_unit = interval_expr[-1]
            
            # 根据单位转换为秒
            if interval_unit == 's':
                seconds = interval_value
            elif interval_unit == 'm':
                seconds = interval_value * 60
            elif interval_unit == 'h':
                seconds = interval_value * 3600
            elif interval_unit == 'd':
                seconds = interval_value * 86400
            else:
                seconds = 3600  # 默认1小时
            
            task.next_run = datetime.now() + timedelta(seconds=seconds)
    
    def _execute_task(self, task):
        """
        执行任务
        
        参数:
            task (BaseTask): 要执行的任务
            
        返回:
            TaskResult: 任务执行结果
        """
        # 添加到运行中的任务
        with self.task_lock:
            self.running_tasks[task.id] = task
        
        # 执行任务
        result = self.executor.execute(task)
        
        # 从运行中的任务移除
        with self.task_lock:
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
        
        return result
    
    def _execute_task_and_handle_result(self, task):
        """
        执行任务并处理结果
        
        参数:
            task (BaseTask): 要执行的任务
        """
        result = self._execute_task(task)
        
        # 处理执行结果
        if result.status == TaskStatus.FAILED:
            # 处理任务失败，考虑重试
            if task.retries < task.max_retries:
                # 增加重试次数
                task.retries += 1
                self.logger.info(f"任务 {task.name} [{task.id}] 失败，将在 {task.retry_interval} 秒后重试 "
                                 f"({task.retries}/{task.max_retries})")
                
                # 延迟重试
                threading.Timer(task.retry_interval, self._run_scheduled_task, [task.id]).start()
            else:
                # 达到最大重试次数，发送通知
                self.logger.warning(f"任务 {task.name} [{task.id}] 达到最大重试次数，不再重试")
                
                # 发送通知
                self.notifier.send_task_notification(
                    task,
                    "任务执行失败",
                    f"任务 {task.name} 执行失败，已重试 {task.retries} 次。\n错误信息：{result.error}"
                )
        elif result.status == TaskStatus.SUCCESS:
            # 任务成功，重置重试次数
            task.retries = 0
            
            # 发送成功通知
            self.notifier.send_task_notification(
                task,
                "任务执行成功",
                f"任务 {task.name} 执行成功，耗时 {result.execution_time:.2f} 秒。"
            )
        elif result.status == TaskStatus.TIMEOUT:
            # 任务超时
            self.logger.warning(f"任务 {task.name} [{task.id}] 执行超时")
            
            # 发送通知
            self.notifier.send_task_notification(
                task,
                "任务执行超时",
                f"任务 {task.name} 执行超时，超过了 {task.timeout} 秒。"
            )
        
        # 保存任务状态
        self.save_tasks()
    
    def _check_dependencies(self, task):
        """
        检查任务依赖是否满足
        
        参数:
            task (BaseTask): 要检查的任务
            
        返回:
            bool: 是否所有依赖任务都已完成
        """
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                self.logger.warning(f"任务 {task.name} [{task.id}] 依赖不存在的任务: {dep_id}")
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.SUCCESS:
                return False
        
        return True
    
    def _job_event_listener(self, event):
        """
        APScheduler 任务事件监听器
        
        参数:
            event: 事件对象
        """
        if event.exception:
            self.logger.error(f"调度任务异常: {event.job_id} - {event.exception}")
            
            # 更新任务状态
            if event.job_id in self.tasks:
                task = self.tasks[event.job_id]
                task.status = TaskStatus.FAILED
                task.updated_at = datetime.now()
                
                # 发送通知
                self.notifier.send_task_notification(
                    task,
                    "任务调度异常",
                    f"任务 {task.name} 调度发生异常。\n错误信息：{str(event.exception)}"
                )
        elif hasattr(event, 'code') and event.code == EVENT_JOB_MISSED:
            self.logger.warning(f"任务错过执行时间: {event.job_id}")
            
            # 更新任务状态
            if event.job_id in self.tasks:
                task = self.tasks[event.job_id]
                task.status = TaskStatus.PENDING
                task.updated_at = datetime.now() 
    
    def backup_tasks(self):
        """备份所有任务 (已禁用)"""
        # 直接返回，不进行任何备份
        return
    
    def restore_tasks_from_backup(self, backup_dir=None):
        """
        从备份恢复任务
        
        参数:
            backup_dir (str, optional): 备份目录路径，如果为None则使用最新的备份
            
        返回:
            bool: 恢复是否成功
        """
        try:
            # 如果没有指定备份目录，使用最新的备份
            if backup_dir is None:
                backup_dirs = [d for d in os.listdir(self.backup_dir) 
                              if os.path.isdir(os.path.join(self.backup_dir, d))]
                if not backup_dirs:
                    self.logger.warning("没有可用的备份")
                    return False
                
                # 按名称排序，最新的备份在最后
                backup_dirs.sort()
                backup_dir = os.path.join(self.backup_dir, backup_dirs[-1])
            
            # 确认备份目录存在
            if not os.path.exists(backup_dir):
                self.logger.warning(f"备份目录不存在: {backup_dir}")
                return False
            
            # 检查调度器是否正在运行
            scheduler_running = self.scheduler.running
            
            # 如果调度器正在运行，停止所有任务
            if scheduler_running:
                try:
                    self.scheduler.pause()
                except Exception as e:
                    self.logger.warning(f"暂停调度器失败，可能调度器尚未完全启动: {str(e)}")
            
            # 清空当前任务
            self.tasks.clear()
            
            # 从备份加载任务
            task_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            
            if not task_files:
                self.logger.warning(f"备份目录中没有任务文件: {backup_dir}")
                # 只有在之前已经运行的情况下才尝试恢复
                if scheduler_running:
                    try:
                        self.scheduler.resume()
                    except Exception as e:
                        self.logger.warning(f"恢复调度器失败: {str(e)}")
                return False
            
            # 复制备份文件到任务目录
            for filename in task_files:
                src_path = os.path.join(backup_dir, filename)
                dst_path = os.path.join(self.data_dir, filename)
                
                with open(src_path, 'r', encoding='utf-8') as src_file:
                    task_data = json.load(src_file)
                    with open(dst_path, 'w', encoding='utf-8') as dst_file:
                        json.dump(task_data, dst_file, ensure_ascii=False, indent=2)
            
            # 重新加载任务，关闭自动恢复功能，防止递归恢复
            self.load_tasks(auto_restore_from_backup=False)
            
            # 如果调度器之前是运行的，尝试恢复
            if scheduler_running:
                try:
                    self.scheduler.resume()
                except Exception as e:
                    self.logger.warning(f"恢复调度器失败: {str(e)}")

                # 尝试重新调度所有任务
                for task_id, task in self.tasks.items():
                    if task.enabled and task.schedule:
                        try:
                            self._schedule_task(task)
                        except Exception as ex:
                            self.logger.warning(f"手动调度任务 {task.name} [{task.id}] 失败: {str(ex)}")
            
            self.logger.info(f"成功从 {backup_dir} 恢复 {len(task_files)} 个任务")
            return True
            
        except Exception as e:
            self.logger.error(f"从备份恢复任务失败: {str(e)}")
            # 只有在调度器正在运行的情况下才尝试恢复
            try:
                if hasattr(self, 'scheduler') and self.scheduler.running:
                    self.scheduler.resume()
            except Exception:
                pass
            return False
    
    def _cleanup_old_backups(self):
        """清理旧备份，只保留最近10个"""
        try:
            backup_dirs = [d for d in os.listdir(self.backup_dir) 
                          if os.path.isdir(os.path.join(self.backup_dir, d))]
            
            if len(backup_dirs) <= 10:
                return
            
            # 按名称排序，最旧的备份在前面
            backup_dirs.sort()
            
            # 删除旧备份
            for old_dir in backup_dirs[:-10]:
                old_path = os.path.join(self.backup_dir, old_dir)
                for filename in os.listdir(old_path):
                    file_path = os.path.join(old_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(old_path)
                self.logger.debug(f"删除旧备份: {old_path}")
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {str(e)}") 