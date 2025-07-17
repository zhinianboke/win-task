#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库操作任务模块

实现数据库查询、备份等操作
"""

import os
import time
import logging
import datetime
import subprocess
from pathlib import Path

from src.core.task import BaseTask, TaskStatus, TaskResult


class DBOperationType:
    """数据库操作类型枚举"""
    QUERY = "query"
    BACKUP = "backup"
    RESTORE = "restore"
    EXECUTE_SCRIPT = "execute_script"


class DBType:
    """数据库类型枚举"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"


class DBTask(BaseTask):
    """数据库操作任务类"""
    
    def __init__(self, name, description="", operation=None, db_type=None, 
                 connection_string=None, query=None, output_file=None):
        """
        初始化数据库操作任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
            operation (str, optional): 操作类型，参见DBOperationType
            db_type (str, optional): 数据库类型，参见DBType
            connection_string (str, optional): 连接字符串
            query (str, optional): SQL查询或脚本文件路径
            output_file (str, optional): 输出文件路径
        """
        super().__init__(name, description)
        
        # 操作参数
        self.operation = operation
        self.db_type = db_type
        self.connection_string = connection_string
        self.query = query
        self.output_file = output_file
        
        # 连接参数（用于命令行工具）
        self.host = "localhost"
        self.port = None
        self.database = None
        self.username = None
        self.password = None
        
        # 高级选项
        self.timeout = 3600  # 数据库操作超时时间（秒）
        self.compress_backup = True  # 是否压缩备份
    
    def run(self):
        """
        执行数据库操作任务
        
        返回:
            TaskResult: 任务执行结果
        """
        result = TaskResult()
        result.start()
        
        # 日志记录
        self.logger.info(f"执行数据库操作: {self.operation}, 数据库类型: {self.db_type}")
        
        if not self.operation or not self.db_type:
            error_msg = "操作类型或数据库类型未设置"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        try:
            # 解析连接字符串（如果有）
            if self.connection_string:
                self._parse_connection_string()
            
            # 根据操作类型执行相应操作
            if self.operation == DBOperationType.QUERY:
                success, message, output = self._execute_query()
            elif self.operation == DBOperationType.BACKUP:
                success, message, output = self._execute_backup()
            elif self.operation == DBOperationType.RESTORE:
                success, message, output = self._execute_restore()
            elif self.operation == DBOperationType.EXECUTE_SCRIPT:
                success, message, output = self._execute_script()
            else:
                error_msg = f"不支持的操作类型: {self.operation}"
                self.logger.error(error_msg)
                result.complete(TaskStatus.FAILED, -1, "", error_msg)
                return result
            
            # 处理操作结果
            if success:
                result.complete(TaskStatus.SUCCESS, 0, output)
                self.logger.info(f"数据库操作成功: {message}")
                
                # 保存输出到文件（如果指定了输出文件）
                if self.output_file and output:
                    self._save_output_to_file(output)
            else:
                result.complete(TaskStatus.FAILED, -1, "", message)
                self.logger.error(f"数据库操作失败: {message}")
            
            return result
            
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
    
    def _parse_connection_string(self):
        """解析连接字符串"""
        try:
            if self.db_type == DBType.MYSQL:
                # 格式: mysql://username:password@host:port/database
                if self.connection_string.startswith("mysql://"):
                    conn_str = self.connection_string[8:]
                    
                    # 解析用户名和密码
                    if "@" in conn_str:
                        auth, conn_str = conn_str.split("@", 1)
                        if ":" in auth:
                            self.username, self.password = auth.split(":", 1)
                        else:
                            self.username = auth
                    
                    # 解析主机和端口
                    if "/" in conn_str:
                        host_port, self.database = conn_str.split("/", 1)
                        if ":" in host_port:
                            self.host, port_str = host_port.split(":", 1)
                            self.port = int(port_str)
                        else:
                            self.host = host_port
                
            elif self.db_type == DBType.POSTGRESQL:
                # 格式: postgresql://username:password@host:port/database
                if self.connection_string.startswith("postgresql://"):
                    conn_str = self.connection_string[13:]
                    
                    # 解析用户名和密码
                    if "@" in conn_str:
                        auth, conn_str = conn_str.split("@", 1)
                        if ":" in auth:
                            self.username, self.password = auth.split(":", 1)
                        else:
                            self.username = auth
                    
                    # 解析主机和端口
                    if "/" in conn_str:
                        host_port, self.database = conn_str.split("/", 1)
                        if ":" in host_port:
                            self.host, port_str = host_port.split(":", 1)
                            self.port = int(port_str)
                        else:
                            self.host = host_port
            
            elif self.db_type == DBType.SQLITE:
                # 格式: sqlite:///path/to/database.db 或 sqlite:///:memory:
                if self.connection_string.startswith("sqlite:///"):
                    self.database = self.connection_string[10:]
            
            elif self.db_type == DBType.SQLSERVER:
                # 格式: sqlserver://username:password@host:port/database
                if self.connection_string.startswith("sqlserver://"):
                    conn_str = self.connection_string[12:]
                    
                    # 解析用户名和密码
                    if "@" in conn_str:
                        auth, conn_str = conn_str.split("@", 1)
                        if ":" in auth:
                            self.username, self.password = auth.split(":", 1)
                        else:
                            self.username = auth
                    
                    # 解析主机和端口
                    if "/" in conn_str:
                        host_port, self.database = conn_str.split("/", 1)
                        if ":" in host_port:
                            self.host, port_str = host_port.split(":", 1)
                            self.port = int(port_str)
                        else:
                            self.host = host_port
        
        except Exception as e:
            self.logger.warning(f"解析连接字符串失败: {str(e)}")
    
    def _execute_query(self):
        """
        执行数据库查询
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if self.db_type == DBType.MYSQL:
                return self._mysql_query()
            elif self.db_type == DBType.POSTGRESQL:
                return self._postgresql_query()
            elif self.db_type == DBType.SQLITE:
                return self._sqlite_query()
            elif self.db_type == DBType.SQLSERVER:
                return self._sqlserver_query()
            else:
                return False, f"不支持的数据库类型: {self.db_type}", ""
                
        except Exception as e:
            return False, f"执行查询异常: {str(e)}", ""
    
    def _mysql_query(self):
        """
        执行MySQL查询
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            # 构建MySQL命令
            cmd = ["mysql"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-h", self.host])
            
            if self.port:
                cmd.extend(["-P", str(self.port)])
            
            if self.username:
                cmd.extend(["-u", self.username])
            
            if self.password:
                cmd.extend(["-p" + self.password])
            
            if self.database:
                cmd.extend(["-D", self.database])
            
            # 添加其他参数
            cmd.extend(["--batch", "--silent"])  # 批处理模式，无表格边框
            
            # 添加查询
            cmd.extend(["-e", self.query])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                return True, "MySQL查询执行成功", stdout
            else:
                return False, f"MySQL查询执行失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"MySQL查询执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"MySQL查询异常: {str(e)}", ""
    
    def _postgresql_query(self):
        """
        执行PostgreSQL查询
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            # 构建PostgreSQL命令
            cmd = ["psql"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-h", self.host])
            
            if self.port:
                cmd.extend(["-p", str(self.port)])
            
            if self.username:
                cmd.extend(["-U", self.username])
            
            if self.database:
                cmd.extend(["-d", self.database])
            
            # 设置PGPASSWORD环境变量（PostgreSQL不接受命令行密码）
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password
            
            # 添加其他参数
            cmd.extend(["-t", "-A"])  # 仅元组，无对齐
            
            # 添加查询
            cmd.extend(["-c", self.query])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                return True, "PostgreSQL查询执行成功", stdout
            else:
                return False, f"PostgreSQL查询执行失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"PostgreSQL查询执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"PostgreSQL查询异常: {str(e)}", ""
    
    def _sqlite_query(self):
        """
        执行SQLite查询
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.database:
                return False, "未指定SQLite数据库文件", ""
            
            # 检查数据库文件是否存在（除非是内存数据库）
            if self.database != ":memory:" and not os.path.exists(self.database):
                return False, f"SQLite数据库文件不存在: {self.database}", ""
            
            # 构建SQLite命令
            cmd = ["sqlite3"]
            
            # 添加数据库文件
            cmd.append(self.database)
            
            # 添加其他参数
            cmd.extend(["-csv", "-header"])  # CSV输出格式
            
            # 添加查询
            cmd.extend([self.query])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                return True, "SQLite查询执行成功", stdout
            else:
                return False, f"SQLite查询执行失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"SQLite查询执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"SQLite查询异常: {str(e)}", ""
    
    def _sqlserver_query(self):
        """
        执行SQL Server查询
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            # 构建SQL Server命令
            cmd = ["sqlcmd"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-S", self.host])
                if self.port:
                    cmd[-1] = f"{cmd[-1]},{self.port}"
            
            if self.username:
                cmd.extend(["-U", self.username])
            
            if self.password:
                cmd.extend(["-P", self.password])
            
            if self.database:
                cmd.extend(["-d", self.database])
            
            # 添加其他参数
            cmd.extend(["-h", "-1"])  # 无表头，去除结果集中的破折号
            
            # 添加查询
            cmd.extend(["-Q", self.query])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                return True, "SQL Server查询执行成功", stdout
            else:
                return False, f"SQL Server查询执行失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"SQL Server查询执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"SQL Server查询异常: {str(e)}", ""
    
    def _execute_backup(self):
        """
        执行数据库备份
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if self.db_type == DBType.MYSQL:
                return self._mysql_backup()
            elif self.db_type == DBType.POSTGRESQL:
                return self._postgresql_backup()
            elif self.db_type == DBType.SQLITE:
                return self._sqlite_backup()
            elif self.db_type == DBType.SQLSERVER:
                return self._sqlserver_backup()
            else:
                return False, f"不支持的数据库类型: {self.db_type}", ""
                
        except Exception as e:
            return False, f"执行备份异常: {str(e)}", ""
    
    def _mysql_backup(self):
        """
        执行MySQL备份
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.database:
                return False, "未指定数据库名称", ""
            
            # 生成备份文件名
            if not self.output_file:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.output_file = f"{self.database}_{timestamp}.sql"
                
                # 如果启用压缩，添加.gz后缀
                if self.compress_backup:
                    self.output_file += ".gz"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 构建MySQL备份命令
            cmd = ["mysqldump"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-h", self.host])
            
            if self.port:
                cmd.extend(["-P", str(self.port)])
            
            if self.username:
                cmd.extend(["-u", self.username])
            
            if self.password:
                cmd.extend(["-p" + self.password])
            
            # 添加其他参数
            cmd.extend(["--single-transaction", "--routines", "--triggers", "--events"])
            
            # 添加数据库名称
            cmd.append(self.database)
            
            # 如果启用压缩
            if self.compress_backup:
                cmd = f"{' '.join(cmd)} | gzip > {self.output_file}"
                # 使用shell执行命令
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            else:
                # 添加输出文件
                cmd.extend(["-r", self.output_file])
                # 不使用shell执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                file_size = os.path.getsize(self.output_file)
                file_size_mb = file_size / (1024 * 1024)
                return True, f"MySQL备份成功，文件大小: {file_size_mb:.2f} MB", f"备份文件: {self.output_file}"
            else:
                return False, f"MySQL备份失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"MySQL备份执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"MySQL备份异常: {str(e)}", ""
    
    def _postgresql_backup(self):
        """
        执行PostgreSQL备份
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.database:
                return False, "未指定数据库名称", ""
            
            # 生成备份文件名
            if not self.output_file:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.output_file = f"{self.database}_{timestamp}.sql"
                
                # 如果启用压缩，添加.gz后缀
                if self.compress_backup:
                    self.output_file += ".gz"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 构建PostgreSQL备份命令
            cmd = ["pg_dump"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-h", self.host])
            
            if self.port:
                cmd.extend(["-p", str(self.port)])
            
            if self.username:
                cmd.extend(["-U", self.username])
            
            # 设置PGPASSWORD环境变量
            env = os.environ.copy()
            if self.password:
                env["PGPASSWORD"] = self.password
            
            # 添加其他参数
            cmd.extend(["-F", "p"])  # 纯文本格式
            
            # 添加数据库名称
            cmd.append(self.database)
            
            # 如果启用压缩
            if self.compress_backup:
                cmd = f"{' '.join(cmd)} | gzip > {self.output_file}"
                # 使用shell执行命令
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    env=env
                )
            else:
                # 添加输出文件
                cmd.extend(["-f", self.output_file])
                # 不使用shell执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    env=env
                )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                file_size = os.path.getsize(self.output_file)
                file_size_mb = file_size / (1024 * 1024)
                return True, f"PostgreSQL备份成功，文件大小: {file_size_mb:.2f} MB", f"备份文件: {self.output_file}"
            else:
                return False, f"PostgreSQL备份失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"PostgreSQL备份执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"PostgreSQL备份异常: {str(e)}", ""
    
    def _sqlite_backup(self):
        """
        执行SQLite备份
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.database:
                return False, "未指定数据库文件", ""
            
            # 检查数据库文件是否存在
            if not os.path.exists(self.database):
                return False, f"SQLite数据库文件不存在: {self.database}", ""
            
            # 生成备份文件名
            if not self.output_file:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                db_name = os.path.basename(self.database)
                self.output_file = f"{os.path.splitext(db_name)[0]}_{timestamp}.sqlite"
                
                # 如果启用压缩，添加.gz后缀
                if self.compress_backup:
                    self.output_file += ".gz"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            if self.compress_backup:
                # 使用gzip压缩
                cmd = f"sqlite3 {self.database} '.backup /dev/stdout' | gzip > {self.output_file}"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            else:
                # 直接备份
                cmd = ["sqlite3", self.database, f".backup {self.output_file}"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                file_size = os.path.getsize(self.output_file)
                file_size_mb = file_size / (1024 * 1024)
                return True, f"SQLite备份成功，文件大小: {file_size_mb:.2f} MB", f"备份文件: {self.output_file}"
            else:
                return False, f"SQLite备份失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"SQLite备份执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"SQLite备份异常: {str(e)}", ""
    
    def _sqlserver_backup(self):
        """
        执行SQL Server备份
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.database:
                return False, "未指定数据库名称", ""
            
            # 生成备份文件名
            if not self.output_file:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.output_file = f"{self.database}_{timestamp}.bak"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 构建SQL Server备份命令
            backup_sql = f"BACKUP DATABASE [{self.database}] TO DISK = N'{self.output_file}' WITH NOFORMAT, NOINIT, NAME = N'{self.database}-Full Database Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10"
            
            cmd = ["sqlcmd"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-S", self.host])
                if self.port:
                    cmd[-1] = f"{cmd[-1]},{self.port}"
            
            if self.username:
                cmd.extend(["-U", self.username])
            
            if self.password:
                cmd.extend(["-P", self.password])
            
            # 添加查询
            cmd.extend(["-Q", backup_sql])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                file_size = os.path.getsize(self.output_file)
                file_size_mb = file_size / (1024 * 1024)
                return True, f"SQL Server备份成功，文件大小: {file_size_mb:.2f} MB", f"备份文件: {self.output_file}"
            else:
                return False, f"SQL Server备份失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"SQL Server备份执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"SQL Server备份异常: {str(e)}", ""
    
    def _execute_restore(self):
        """
        执行数据库恢复
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            if not self.output_file or not os.path.exists(self.output_file):
                return False, f"备份文件不存在: {self.output_file}", ""
            
            if self.db_type == DBType.MYSQL:
                return self._mysql_restore()
            elif self.db_type == DBType.POSTGRESQL:
                return self._postgresql_restore()
            elif self.db_type == DBType.SQLITE:
                return self._sqlite_restore()
            elif self.db_type == DBType.SQLSERVER:
                return self._sqlserver_restore()
            else:
                return False, f"不支持的数据库类型: {self.db_type}", ""
                
        except Exception as e:
            return False, f"执行恢复异常: {str(e)}", ""
    
    def _execute_script(self):
        """
        执行SQL脚本
        
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            # 检查脚本文件是否存在
            script_path = self.query
            if not os.path.exists(script_path):
                return False, f"脚本文件不存在: {script_path}", ""
            
            if self.db_type == DBType.MYSQL:
                return self._mysql_execute_script(script_path)
            elif self.db_type == DBType.POSTGRESQL:
                return self._postgresql_execute_script(script_path)
            elif self.db_type == DBType.SQLITE:
                return self._sqlite_execute_script(script_path)
            elif self.db_type == DBType.SQLSERVER:
                return self._sqlserver_execute_script(script_path)
            else:
                return False, f"不支持的数据库类型: {self.db_type}", ""
                
        except Exception as e:
            return False, f"执行脚本异常: {str(e)}", ""
    
    def _mysql_execute_script(self, script_path):
        """
        执行MySQL脚本
        
        参数:
            script_path (str): 脚本文件路径
            
        返回:
            tuple: (成功标志, 消息, 输出)
        """
        try:
            # 构建MySQL命令
            cmd = ["mysql"]
            
            # 添加连接参数
            if self.host:
                cmd.extend(["-h", self.host])
            
            if self.port:
                cmd.extend(["-P", str(self.port)])
            
            if self.username:
                cmd.extend(["-u", self.username])
            
            if self.password:
                cmd.extend(["-p" + self.password])
            
            if self.database:
                cmd.extend(["-D", self.database])
            
            # 添加脚本文件
            cmd.extend(["-e", f"source {script_path}"])
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            
            if process.returncode == 0:
                return True, "MySQL脚本执行成功", stdout
            else:
                return False, f"MySQL脚本执行失败: {stderr}", ""
                
        except subprocess.TimeoutExpired:
            return False, f"MySQL脚本执行超时（{self.timeout}秒）", ""
            
        except Exception as e:
            return False, f"MySQL脚本执行异常: {str(e)}", ""
    
    def _save_output_to_file(self, output):
        """
        保存输出到文件
        
        参数:
            output (str): 要保存的输出
        """
        try:
            if not self.output_file:
                return
            
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 写入文件
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            self.logger.info(f"输出已保存到文件: {self.output_file}")
            
        except Exception as e:
            self.logger.error(f"保存输出到文件失败: {str(e)}")
    
    def to_dict(self):
        """
        将任务转换为字典用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        data = super().to_dict()
        
        # 添加数据库任务特有字段
        data.update({
            'operation': self.operation,
            'db_type': self.db_type,
            'connection_string': self.connection_string,
            'query': self.query,
            'output_file': self.output_file,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            # 注意：不存储密码，仅保留是否有密码的标志
            'has_password': bool(self.password),
            'timeout': self.timeout,
            'compress_backup': self.compress_backup
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            DBTask: 任务对象
        """
        task = super().from_dict(data)
        
        # 设置数据库任务特有字段
        task.operation = data.get('operation')
        task.db_type = data.get('db_type')
        task.connection_string = data.get('connection_string')
        task.query = data.get('query')
        task.output_file = data.get('output_file')
        task.host = data.get('host', 'localhost')
        task.port = data.get('port')
        task.database = data.get('database')
        task.username = data.get('username')
        # 注意：密码需要单独设置
        task.timeout = data.get('timeout', 3600)
        task.compress_backup = data.get('compress_backup', True)
        
        return task 