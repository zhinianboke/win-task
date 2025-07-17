#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统操作任务模块

实现系统操作如关机、重启、休眠等
"""

import os
import time
import logging
import subprocess
import ctypes

from src.core.task import BaseTask, TaskStatus, TaskResult


class SystemOperationType:
    """系统操作类型枚举"""
    SHUTDOWN = "shutdown"
    RESTART = "restart"
    HIBERNATE = "hibernate"
    SLEEP = "sleep"
    LOCK = "lock"
    LOGOFF = "logoff"


class SystemTask(BaseTask):
    """系统操作任务类"""
    
    def __init__(self, name, description="", operation=None, force=False, delay_seconds=0):
        """
        初始化系统操作任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
            operation (str, optional): 操作类型，参见SystemOperationType
            force (bool, optional): 是否强制执行，不等待应用关闭
            delay_seconds (int, optional): 执行延迟（秒）
        """
        super().__init__(name, description)
        
        # 操作参数
        self.operation = operation
        self.force = force
        self.delay_seconds = delay_seconds
        
        # 高级选项
        self.message = None  # 关机/重启前显示的消息
        self.run_as_admin = True  # 是否以管理员权限运行
    
    def run(self):
        """
        执行系统操作任务
        
        返回:
            TaskResult: 任务执行结果
        """
        result = TaskResult()
        result.start()
        
        # 日志记录
        self.logger.info(f"执行系统操作: {self.operation}, 强制: {self.force}, 延迟: {self.delay_seconds}秒")
        
        if not self.operation:
            error_msg = "操作类型未设置"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        try:
            # 检查是否需要等待
            if self.delay_seconds > 0:
                self.logger.info(f"等待 {self.delay_seconds} 秒后执行操作")
                time.sleep(self.delay_seconds)
            
            # 执行系统操作
            if os.name == 'nt':  # Windows 系统
                success, message = self._windows_system_operation()
            else:  # Linux/macOS 系统
                success, message = self._unix_system_operation()
            
            # 处理操作结果
            if success:
                result.complete(TaskStatus.SUCCESS, 0, message)
                self.logger.info(f"系统操作成功: {message}")
            else:
                result.complete(TaskStatus.FAILED, -1, "", message)
                self.logger.error(f"系统操作失败: {message}")
            
            return result
            
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
    
    def _windows_system_operation(self):
        """
        执行Windows系统操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        # 检查管理员权限
        if self.run_as_admin and not self._is_admin():
            return False, "需要管理员权限执行系统操作"
        
        try:
            if self.operation == SystemOperationType.SHUTDOWN:
                # 关机命令
                cmd = ["shutdown", "/s"]
                if self.force:
                    cmd.append("/f")
                if self.delay_seconds > 0:
                    cmd.extend(["/t", str(self.delay_seconds)])
                if self.message:
                    cmd.extend(["/c", f'"{self.message}"'])
                
            elif self.operation == SystemOperationType.RESTART:
                # 重启命令
                cmd = ["shutdown", "/r"]
                if self.force:
                    cmd.append("/f")
                if self.delay_seconds > 0:
                    cmd.extend(["/t", str(self.delay_seconds)])
                if self.message:
                    cmd.extend(["/c", f'"{self.message}"'])
                
            elif self.operation == SystemOperationType.HIBERNATE:
                # 休眠命令
                return self._windows_power_operation(7)  # 7 = HIBERNATE
                
            elif self.operation == SystemOperationType.SLEEP:
                # 睡眠命令
                return self._windows_power_operation(4)  # 4 = SUSPEND
                
            elif self.operation == SystemOperationType.LOCK:
                # 锁定屏幕
                ctypes.windll.user32.LockWorkStation()
                return True, "锁定工作站成功"
                
            elif self.operation == SystemOperationType.LOGOFF:
                # 注销命令
                cmd = ["shutdown", "/l"]
                if self.force:
                    cmd.append("/f")
                
            else:
                return False, f"不支持的操作类型: {self.operation}"
            
            # 执行命令
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return True, f"系统{self.operation}命令已发送"
            else:
                return False, f"执行系统命令失败: {stderr}"
                
        except Exception as e:
            return False, f"Windows系统操作异常: {str(e)}"
    
    def _windows_power_operation(self, operation_code):
        """
        执行Windows电源操作
        
        参数:
            operation_code (int): 操作代码
            
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            # 导入Windows API
            import ctypes
            import ctypes.wintypes
            
            # 定义所需的常量
            PHANDLE = ctypes.wintypes.HANDLE
            DWORD = ctypes.wintypes.DWORD
            LPTSTR = ctypes.wintypes.LPWSTR
            
            # 权限相关常量
            TOKEN_QUERY = 0x0008
            TOKEN_ADJUST_PRIVILEGES = 0x0020
            SE_PRIVILEGE_ENABLED = 0x00000002
            
            # 获取进程token
            token_handle = ctypes.wintypes.HANDLE()
            res = ctypes.windll.advapi32.OpenProcessToken(
                ctypes.windll.kernel32.GetCurrentProcess(),
                TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES,
                ctypes.byref(token_handle)
            )
            if not res:
                return False, "无法获取进程令牌"
            
            # 设置权限结构
            class LUID(ctypes.Structure):
                _fields_ = [
                    ("LowPart", DWORD),
                    ("HighPart", ctypes.c_long)
                ]
                
            class LUID_AND_ATTRIBUTES(ctypes.Structure):
                _fields_ = [
                    ("Luid", LUID),
                    ("Attributes", DWORD)
                ]
                
            class TOKEN_PRIVILEGES(ctypes.Structure):
                _fields_ = [
                    ("PrivilegeCount", DWORD),
                    ("Privileges", LUID_AND_ATTRIBUTES * 1)
                ]
                
            # 查找关机权限
            luid = LUID()
            res = ctypes.windll.advapi32.LookupPrivilegeValueW(
                None,
                "SeShutdownPrivilege",
                ctypes.byref(luid)
            )
            if not res:
                return False, "无法查找关机权限值"
            
            # 设置权限
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
            
            # 调整token权限
            res = ctypes.windll.advapi32.AdjustTokenPrivileges(
                token_handle,
                False,
                ctypes.byref(tp),
                ctypes.sizeof(tp),
                None,
                None
            )
            if not res:
                return False, "无法调整令牌权限"
            
            # 设置系统电源状态
            if operation_code == 7:  # HIBERNATE
                res = ctypes.windll.powrprof.SetSuspendState(True, self.force, False)
            else:  # SUSPEND/SLEEP
                res = ctypes.windll.powrprof.SetSuspendState(False, self.force, False)
                
            if res:
                return True, f"系统{self.operation}命令已发送"
            else:
                return False, f"执行系统电源操作失败"
        
        except Exception as e:
            return False, f"Windows电源操作异常: {str(e)}"
    
    def _unix_system_operation(self):
        """
        执行Unix系统操作
        
        返回:
            tuple: (成功标志, 消息)
        """
        try:
            if self.operation == SystemOperationType.SHUTDOWN:
                # 关机命令
                if os.path.exists('/sbin/shutdown'):
                    shutdown_cmd = '/sbin/shutdown'
                else:
                    shutdown_cmd = 'shutdown'
                
                cmd = [shutdown_cmd]
                if self.force:
                    cmd.append("-f")
                
                # 添加延迟
                if self.delay_seconds > 0:
                    delay_minutes = max(1, int(self.delay_seconds / 60))  # 转换为分钟，最少1分钟
                    cmd.extend([f"+{delay_minutes}"])
                else:
                    cmd.extend(["now"])
                
                # 添加消息
                if self.message:
                    cmd.append(f'"{self.message}"')
                
            elif self.operation == SystemOperationType.RESTART:
                # 重启命令
                if os.path.exists('/sbin/shutdown'):
                    shutdown_cmd = '/sbin/shutdown'
                else:
                    shutdown_cmd = 'shutdown'
                
                cmd = [shutdown_cmd, "-r"]
                if self.force:
                    cmd.append("-f")
                
                # 添加延迟
                if self.delay_seconds > 0:
                    delay_minutes = max(1, int(self.delay_seconds / 60))  # 转换为分钟，最少1分钟
                    cmd.extend([f"+{delay_minutes}"])
                else:
                    cmd.extend(["now"])
                
                # 添加消息
                if self.message:
                    cmd.append(f'"{self.message}"')
                
            elif self.operation == SystemOperationType.HIBERNATE:
                # 休眠命令（systemd系统）
                cmd = ["systemctl", "hibernate"]
                
            elif self.operation == SystemOperationType.SLEEP:
                # 睡眠命令（systemd系统）
                cmd = ["systemctl", "suspend"]
                
            elif self.operation == SystemOperationType.LOCK:
                # 尝试不同的锁屏命令
                if os.environ.get('DISPLAY'):
                    for lock_cmd in ["gnome-screensaver-command --lock", "xdg-screensaver lock", "i3lock", "slock"]:
                        try:
                            if subprocess.call(lock_cmd, shell=True) == 0:
                                return True, "锁定屏幕成功"
                        except:
                            pass
                return False, "无法锁定屏幕，未找到适用的锁屏命令"
                
            elif self.operation == SystemOperationType.LOGOFF:
                # 根据桌面环境选择注销命令
                desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
                
                if 'gnome' in desktop:
                    cmd = ["gnome-session-quit", "--logout", "--no-prompt"]
                elif 'kde' in desktop:
                    cmd = ["qdbus", "org.kde.ksmserver", "/KSMServer", "logout", "0", "0", "0"]
                else:
                    # 尝试通用方法
                    cmd = ["pkill", "-u", os.environ.get('USER', '')]
                
            else:
                return False, f"不支持的操作类型: {self.operation}"
            
            # 执行命令
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                return True, f"系统{self.operation}命令已发送"
            else:
                return False, f"执行系统命令失败: {stderr}"
                
        except Exception as e:
            return False, f"Unix系统操作异常: {str(e)}"
    
    def _is_admin(self):
        """
        检查是否具有管理员权限
        
        返回:
            bool: 是否具有管理员权限
        """
        try:
            if os.name == 'nt':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Unix系统检查是否为root
                return os.geteuid() == 0
        except:
            return False
    
    def to_dict(self):
        """
        将任务转换为字典用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        data = super().to_dict()
        
        # 添加系统任务特有字段
        data.update({
            'operation': self.operation,
            'force': self.force,
            'delay_seconds': self.delay_seconds,
            'message': self.message,
            'run_as_admin': self.run_as_admin
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            SystemTask: 任务对象
        """
        task = super().from_dict(data)
        
        # 设置系统任务特有字段
        task.operation = data.get('operation')
        task.force = data.get('force', False)
        task.delay_seconds = data.get('delay_seconds', 0)
        task.message = data.get('message')
        task.run_as_admin = data.get('run_as_admin', True)
        
        return task 