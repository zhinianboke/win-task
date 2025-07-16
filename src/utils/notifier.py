#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通知管理器模块

负责发送各类通知（桌面通知、邮件通知等）
"""

import os
import logging
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

from src.core.settings import Settings


class Notifier:
    """通知管理器类"""
    
    def __init__(self, settings=None):
        """
        初始化通知管理器
        
        参数:
            settings (Settings, optional): 设置对象，如果为None则创建新实例
        """
        # 如果没有传入设置对象，则创建一个
        self.settings = settings or Settings()
        
        # 日志记录器
        self.logger = logging.getLogger("notifier")
        
        # 程序根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        
        # 检查是否支持桌面通知
        self.has_desktop_notify = self._check_desktop_notify()
    
    def _check_desktop_notify(self):
        """
        检查是否支持桌面通知
        
        返回:
            bool: 是否支持桌面通知
        """
        try:
            # 尝试导入PyQt5通知模块
            from PyQt5.QtWidgets import QSystemTrayIcon
            return QSystemTrayIcon.isSystemTrayAvailable()
        except ImportError:
            self.logger.warning("无法加载PyQt5通知模块，桌面通知功能不可用")
            return False
    
    def send_desktop_notification(self, title, message, icon=None, timeout=5000):
        """
        发送桌面通知
        
        参数:
            title (str): 通知标题
            message (str): 通知内容
            icon (str, optional): 通知图标路径
            timeout (int, optional): 通知显示时间(毫秒)
            
        返回:
            bool: 是否发送成功
        """
        if not self.has_desktop_notify:
            self.logger.warning("桌面通知功能不可用")
            return False
        
        try:
            from PyQt5.QtWidgets import QSystemTrayIcon
            from PyQt5.QtGui import QIcon
            
            # 从任何现有的 QApplication 实例获取系统托盘
            import PyQt5.QtWidgets
            app = PyQt5.QtWidgets.QApplication.instance()
            if app is None:
                self.logger.warning("无法发送桌面通知：QApplication实例不存在")
                return False
            
            # 获取系统托盘图标
            tray_icons = [obj for obj in app.children() if isinstance(obj, QSystemTrayIcon)]
            if not tray_icons:
                self.logger.warning("无法发送桌面通知：未找到系统托盘图标")
                return False
            
            tray_icon = tray_icons[0]
            
            # 设置图标
            if icon:
                tray_icon.setIcon(QIcon(icon))
            
            # 显示通知
            tray_icon.showMessage(title, message, QSystemTrayIcon.Information, timeout)
            
            self.logger.debug(f"已发送桌面通知：{title}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送桌面通知失败: {str(e)}")
            return False
    
    def send_email_notification(self, subject, message, recipient=None):
        """
        发送邮件通知
        
        参数:
            subject (str): 邮件主题
            message (str): 邮件内容
            recipient (str, optional): 收件人，如果为None则使用配置中的收件人
            
        返回:
            bool: 是否发送成功
        """
        # 如果没有指定收件人，使用配置中的收件人
        if recipient is None:
            recipient = self.settings.get('Notification', 'email_recipient')
            if not recipient:
                self.logger.warning("邮件通知失败：未配置收件人")
                return False
        
        # 获取SMTP配置
        smtp_server = self.settings.get('Notification', 'smtp_server')
        smtp_port = self.settings.get('Notification', 'smtp_port', 587, int)
        smtp_user = self.settings.get('Notification', 'smtp_user')
        smtp_password = self.settings.get('Notification', 'smtp_password')
        
        # 检查配置是否完整
        if not all([smtp_server, smtp_user, smtp_password]):
            self.logger.warning("邮件通知失败：SMTP配置不完整")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient
            
            # 添加主题前缀
            email_subject_prefix = self.settings.get('Notification', 'email_subject_prefix', '[Win-Task]')
            msg['Subject'] = Header(f"{email_subject_prefix} {subject}", 'utf-8')
            
            # 添加正文
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 发送邮件
            # 在新线程中发送邮件，避免阻塞主线程
            threading.Thread(
                target=self._send_email_thread,
                args=(smtp_server, smtp_port, smtp_user, smtp_password, recipient, msg)
            ).start()
            
            self.logger.info(f"邮件通知已加入发送队列：{subject} -> {recipient}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建邮件通知失败: {str(e)}")
            return False
    
    def _send_email_thread(self, smtp_server, smtp_port, smtp_user, smtp_password, recipient, msg):
        """
        在线程中发送邮件
        
        参数:
            smtp_server (str): SMTP服务器地址
            smtp_port (int): SMTP服务器端口
            smtp_user (str): SMTP用户名
            smtp_password (str): SMTP密码
            recipient (str): 收件人
            msg (MIMEMultipart): 邮件消息
        """
        try:
            # 连接SMTP服务器
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # 启用TLS加密
            server.login(smtp_user, smtp_password)
            
            # 发送邮件
            server.sendmail(smtp_user, recipient, msg.as_string())
            
            # 关闭连接
            server.quit()
            
            self.logger.debug(f"邮件通知发送成功：{msg['Subject']} -> {recipient}")
        
        except Exception as e:
            self.logger.error(f"发送邮件通知失败: {str(e)}")
    
    def send_task_notification(self, task, subject, message):
        """
        发送任务相关的通知
        
        参数:
            task (BaseTask): 任务对象
            subject (str): 通知主题
            message (str): 通知内容
            
        返回:
            bool: 是否发送成功
        """
        if not self.settings.notification_enabled:
            return False
        
        # 构建完整的消息
        full_message = (
            f"任务: {task.name}\n"
            f"ID: {task.id}\n"
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"--------------------\n"
            f"{message}"
        )
        
        # 根据通知类型发送
        notification_type = self.settings.notification_type
        success = False
        
        if notification_type == 'desktop' or notification_type == 'both':
            # 发送桌面通知
            icon_path = os.path.join(self.base_dir, 'assets/icons/task_icon.png')
            success = self.send_desktop_notification(subject, full_message, icon_path)
        
        if notification_type == 'email' or notification_type == 'both':
            # 发送邮件通知
            email_success = self.send_email_notification(subject, full_message)
            success = success or email_success
        
        return success 