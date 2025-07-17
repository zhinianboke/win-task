#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件操作任务模块

实现文件复制、移动、删除、备份等操作
"""

import os
import shutil
import logging
import datetime
import zipfile
from pathlib import Path

from src.core.task import BaseTask, TaskStatus, TaskResult


class FileOperationType:
    """文件操作类型枚举"""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    BACKUP = "backup"
    ZIP = "zip"
    UNZIP = "unzip"


class FileTask(BaseTask):
    """文件操作任务类"""
    
    def __init__(self, name, description="", operation=None, source_path=None, 
                 target_path=None, overwrite=False, include_pattern=None, exclude_pattern=None):
        """
        初始化文件操作任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
            operation (str, optional): 操作类型，参见FileOperationType
            source_path (str, optional): 源文件/目录路径
            target_path (str, optional): 目标文件/目录路径
            overwrite (bool, optional): 是否覆盖已存在的文件
            include_pattern (str, optional): 包含的文件模式，如"*.txt"
            exclude_pattern (str, optional): 排除的文件模式，如"*.tmp"
        """
        super().__init__(name, description)
        
        # 操作参数
        self.operation = operation
        self.source_path = source_path
        self.target_path = target_path
        self.overwrite = overwrite
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        
        # 高级选项
        self.create_target_dir = True
        self.preserve_metadata = True
        self.follow_symlinks = True
    
    def run(self):
        """
        执行文件操作任务
        
        返回:
            TaskResult: 任务执行结果
        """
        result = TaskResult()
        result.start()
        
        # 日志记录
        self.logger.info(f"执行文件操作: {self.operation} - 源: {self.source_path}, 目标: {self.target_path}")
        
        if not self.source_path:
            error_msg = "源路径未设置"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        try:
            # 检查源路径是否存在
            if not os.path.exists(self.source_path):
                error_msg = f"源路径不存在: {self.source_path}"
                self.logger.error(error_msg)
                result.complete(TaskStatus.FAILED, -1, "", error_msg)
                return result
            
            # 根据操作类型执行相应操作
            if self.operation == FileOperationType.COPY:
                success, message = self._copy_operation()
            elif self.operation == FileOperationType.MOVE:
                success, message = self._move_operation()
            elif self.operation == FileOperationType.DELETE:
                success, message = self._delete_operation()
            elif self.operation == FileOperationType.BACKUP:
                success, message = self._backup_operation()
            elif self.operation == FileOperationType.ZIP:
                success, message = self._zip_operation()
            elif self.operation == FileOperationType.UNZIP:
                success, message = self._unzip_operation()
            else:
                error_msg = f"不支持的操作类型: {self.operation}"
                self.logger.error(error_msg)
                result.complete(TaskStatus.FAILED, -1, "", error_msg)
                return result
            
            # 处理操作结果
            if success:
                result.complete(TaskStatus.SUCCESS, 0, message)
                self.logger.info(f"文件操作成功: {message}")
            else:
                result.complete(TaskStatus.FAILED, -1, "", message)
                self.logger.error(f"文件操作失败: {message}")
            
            return result
            
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
    
    def _copy_operation(self):
        """
        执行复制操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        if not self.target_path:
            return False, "目标路径未设置"
        
        try:
            # 确保目标目录存在
            if self.create_target_dir:
                target_dir = os.path.dirname(self.target_path) if os.path.isfile(self.source_path) else self.target_path
                os.makedirs(target_dir, exist_ok=True)
            
            # 如果源是目录
            if os.path.isdir(self.source_path):
                return self._copy_directory()
            else:
                # 源是文件
                return self._copy_file()
        
        except Exception as e:
            return False, f"复制操作异常: {str(e)}"
    
    def _copy_file(self):
        """
        复制单个文件
        
        返回:
            tuple: (成功标志, 消息)
        """
        # 检查文件是否匹配包含/排除模式
        if not self._is_file_included(self.source_path):
            return True, f"文件 {self.source_path} 被排除"
        
        # 检查目标文件是否存在
        if os.path.exists(self.target_path) and not self.overwrite:
            return False, f"目标文件已存在且未设置覆盖: {self.target_path}"
        
        # 复制文件
        shutil.copy2(self.source_path, self.target_path) if self.preserve_metadata else shutil.copy(self.source_path, self.target_path)
        
        return True, f"复制文件 {self.source_path} 到 {self.target_path}"
    
    def _copy_directory(self):
        """
        复制目录
        
        返回:
            tuple: (成功标志, 消息)
        """
        # 统计信息
        copied_files = 0
        skipped_files = 0
        
        # 如果目标存在且不覆盖
        if os.path.exists(self.target_path) and not self.overwrite:
            return False, f"目标目录已存在且未设置覆盖: {self.target_path}"
        
        # 如果目标路径是文件
        if os.path.exists(self.target_path) and os.path.isfile(self.target_path):
            return False, f"目标路径是文件，无法复制目录到文件: {self.target_path}"
        
        # 确保目标目录存在
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
        
        # 遍历源目录
        for root, dirs, files in os.walk(self.source_path):
            # 计算相对路径
            rel_path = os.path.relpath(root, self.source_path)
            target_dir = os.path.join(self.target_path, rel_path) if rel_path != '.' else self.target_path
            
            # 创建目标子目录
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # 复制文件
            for file in files:
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_dir, file)
                
                # 检查文件是否匹配包含/排除模式
                if not self._is_file_included(source_file):
                    skipped_files += 1
                    continue
                
                # 检查目标文件是否存在
                if os.path.exists(target_file) and not self.overwrite:
                    skipped_files += 1
                    continue
                
                # 复制文件
                shutil.copy2(source_file, target_file) if self.preserve_metadata else shutil.copy(source_file, target_file)
                copied_files += 1
        
        return True, f"复制目录完成，复制了 {copied_files} 个文件，跳过了 {skipped_files} 个文件"
    
    def _move_operation(self):
        """
        执行移动操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        if not self.target_path:
            return False, "目标路径未设置"
        
        try:
            # 确保目标目录存在
            if self.create_target_dir:
                target_dir = os.path.dirname(self.target_path) if os.path.isfile(self.source_path) else self.target_path
                os.makedirs(target_dir, exist_ok=True)
            
            # 检查目标是否存在
            if os.path.exists(self.target_path) and not self.overwrite:
                return False, f"目标已存在且未设置覆盖: {self.target_path}"
            
            # 执行移动
            shutil.move(self.source_path, self.target_path)
            
            return True, f"移动 {self.source_path} 到 {self.target_path}"
            
        except Exception as e:
            return False, f"移动操作异常: {str(e)}"
    
    def _delete_operation(self):
        """
        执行删除操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            # 如果是目录
            if os.path.isdir(self.source_path):
                shutil.rmtree(self.source_path)
                return True, f"删除目录 {self.source_path}"
            else:
                # 如果是文件
                os.remove(self.source_path)
                return True, f"删除文件 {self.source_path}"
                
        except Exception as e:
            return False, f"删除操作异常: {str(e)}"
    
    def _backup_operation(self):
        """
        执行备份操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            # 如果没有指定目标路径，创建带时间戳的备份文件名
            if not self.target_path:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.basename(self.source_path)
                self.target_path = f"{self.source_path}.{timestamp}.bak"
            
            # 创建ZIP备份
            if self.source_path.endswith('/') or self.source_path.endswith('\\'):
                self.source_path = self.source_path[:-1]
                
            zip_name = self.target_path if self.target_path.endswith('.zip') else f"{self.target_path}.zip"
            
            # 确保目标目录存在
            if self.create_target_dir:
                target_dir = os.path.dirname(zip_name)
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
            
            # 创建ZIP文件
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 如果源是目录
                if os.path.isdir(self.source_path):
                    # 记录原始当前目录并切换到源目录的父目录
                    base_name = os.path.basename(self.source_path)
                    parent_dir = os.path.dirname(self.source_path)
                    
                    # 遍历目录
                    for root, dirs, files in os.walk(self.source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            # 检查文件是否匹配包含/排除模式
                            if not self._is_file_included(file_path):
                                continue
                            
                            # 计算归档内的路径
                            if parent_dir:
                                archive_path = os.path.join(base_name, os.path.relpath(file_path, self.source_path))
                            else:
                                archive_path = os.path.relpath(file_path, os.path.dirname(self.source_path))
                            
                            # 添加到ZIP
                            zipf.write(file_path, archive_path)
                else:
                    # 源是文件
                    zipf.write(self.source_path, os.path.basename(self.source_path))
            
            return True, f"备份 {self.source_path} 到 {zip_name}"
            
        except Exception as e:
            return False, f"备份操作异常: {str(e)}"
    
    def _zip_operation(self):
        """
        执行压缩操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            # 如果没有指定目标路径，创建默认zip文件名
            if not self.target_path:
                self.target_path = f"{self.source_path}.zip"
            
            # 确保目标目录存在
            if self.create_target_dir:
                target_dir = os.path.dirname(self.target_path)
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)
            
            # 创建ZIP文件
            with zipfile.ZipFile(self.target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 如果源是目录
                if os.path.isdir(self.source_path):
                    # 遍历目录
                    for root, dirs, files in os.walk(self.source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            # 检查文件是否匹配包含/排除模式
                            if not self._is_file_included(file_path):
                                continue
                            
                            # 计算归档内的路径
                            archive_path = os.path.relpath(file_path, os.path.dirname(self.source_path))
                            
                            # 添加到ZIP
                            zipf.write(file_path, archive_path)
                else:
                    # 源是文件
                    zipf.write(self.source_path, os.path.basename(self.source_path))
            
            return True, f"压缩 {self.source_path} 到 {self.target_path}"
            
        except Exception as e:
            return False, f"压缩操作异常: {str(e)}"
    
    def _unzip_operation(self):
        """
        执行解压缩操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            if not self.target_path:
                # 如果没有指定目标路径，解压到当前目录
                self.target_path = os.path.dirname(self.source_path)
            
            # 确保目标目录存在
            if self.create_target_dir:
                os.makedirs(self.target_path, exist_ok=True)
            
            # 解压ZIP文件
            with zipfile.ZipFile(self.source_path, 'r') as zipf:
                # 获取所有文件列表
                file_list = zipf.namelist()
                
                # 解压所有文件
                for file in file_list:
                    # 检查文件是否匹配包含/排除模式
                    if not self._is_path_included(file):
                        continue
                    
                    zipf.extract(file, self.target_path)
            
            return True, f"解压 {self.source_path} 到 {self.target_path}"
            
        except Exception as e:
            return False, f"解压操作异常: {str(e)}"
    
    def _is_file_included(self, filepath):
        """
        检查文件是否应该被包含（基于包含/排除模式）
        
        参数:
            filepath (str): 文件路径
            
        返回:
            bool: 是否包含该文件
        """
        filename = os.path.basename(filepath)
        
        # 如果有排除模式，检查是否被排除
        if self.exclude_pattern:
            import fnmatch
            if fnmatch.fnmatch(filename, self.exclude_pattern):
                return False
        
        # 如果有包含模式，检查是否被包含
        if self.include_pattern:
            import fnmatch
            return fnmatch.fnmatch(filename, self.include_pattern)
        
        # 默认包含所有文件
        return True
    
    def _is_path_included(self, path):
        """
        检查路径是否应该被包含（基于包含/排除模式）
        
        参数:
            path (str): 路径
            
        返回:
            bool: 是否包含该路径
        """
        basename = os.path.basename(path)
        
        # 如果有排除模式，检查是否被排除
        if self.exclude_pattern:
            import fnmatch
            if fnmatch.fnmatch(basename, self.exclude_pattern) or fnmatch.fnmatch(path, self.exclude_pattern):
                return False
        
        # 如果有包含模式，检查是否被包含
        if self.include_pattern:
            import fnmatch
            return fnmatch.fnmatch(basename, self.include_pattern) or fnmatch.fnmatch(path, self.include_pattern)
        
        # 默认包含所有路径
        return True
    
    def to_dict(self):
        """
        将任务转换为字典用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        data = super().to_dict()
        
        # 添加文件任务特有字段
        data.update({
            'operation': self.operation,
            'source_path': self.source_path,
            'target_path': self.target_path,
            'overwrite': self.overwrite,
            'include_pattern': self.include_pattern,
            'exclude_pattern': self.exclude_pattern,
            'create_target_dir': self.create_target_dir,
            'preserve_metadata': self.preserve_metadata,
            'follow_symlinks': self.follow_symlinks
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            FileTask: 任务对象
        """
        task = super().from_dict(data)
        
        # 设置文件任务特有字段
        task.operation = data.get('operation')
        task.source_path = data.get('source_path')
        task.target_path = data.get('target_path')
        task.overwrite = data.get('overwrite', False)
        task.include_pattern = data.get('include_pattern')
        task.exclude_pattern = data.get('exclude_pattern')
        task.create_target_dir = data.get('create_target_dir', True)
        task.preserve_metadata = data.get('preserve_metadata', True)
        task.follow_symlinks = data.get('follow_symlinks', True)
        
        return task 