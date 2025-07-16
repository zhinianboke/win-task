#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务对话框模块

实现任务创建和编辑对话框
"""

import os
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, 
    QCheckBox, QSpinBox, QTimeEdit, QDateTimeEdit, QDialogButtonBox,
    QGroupBox, QRadioButton, QFileDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QDateTime

from src.core.task import TaskStatus, TaskPriority
from src.tasks.url_task import URLTask
from src.tasks.file_task import FileTask, FileOperationType
from src.tasks.program_task import ProgramTask
from src.tasks.system_task import SystemTask, SystemOperationType
from src.tasks.db_task import DBTask, DBOperationType, DBType
from src.utils.cron_parser import CronParser


class TaskDialog(QDialog):
    """任务创建和编辑对话框"""
    
    def __init__(self, scheduler, task=None, parent=None):
        """
        初始化任务对话框
        
        参数:
            scheduler: 任务调度器
            task: 要编辑的任务，如果为None则创建新任务
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.scheduler = scheduler
        self.task = task
        self.logger = logging.getLogger("task_dialog")
        
        # 设置对话框属性
        self.setWindowTitle("创建任务" if task is None else "编辑任务")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # 创建界面
        self._create_ui()
        
        # 如果是编辑现有任务，填充表单
        if task:
            self._populate_form()
    
    def _create_ui(self):
        """创建用户界面"""
        # 主布局
        layout = QVBoxLayout(self)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 创建基本信息选项卡
        self._create_basic_tab()
        
        # 创建计划选项卡
        self._create_schedule_tab()
        
        # 创建任务类型选项卡
        self._create_task_type_tab()
        
        # 创建高级选项卡
        self._create_advanced_tab()
        
        # 对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_basic_tab(self):
        """创建基本信息选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 任务名称
        self.name_edit = QLineEdit()
        layout.addRow("任务名称:", self.name_edit)
        
        # 任务描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addRow("任务描述:", self.description_edit)
        
        # 任务类型
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems([
            "URL请求", "文件操作", "程序执行", "系统操作", "数据库操作"
        ])
        self.task_type_combo.currentIndexChanged.connect(self._on_task_type_changed)
        layout.addRow("任务类型:", self.task_type_combo)
        
        # 任务分组
        self.group_edit = QLineEdit()
        layout.addRow("任务分组:", self.group_edit)
        
        # 任务标签
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("用逗号分隔多个标签")
        layout.addRow("任务标签:", self.tags_edit)
        
        # 任务优先级
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([
            "低", "正常", "高", "关键"
        ])
        self.priority_combo.setCurrentIndex(1)  # 默认为"正常"
        layout.addRow("任务优先级:", self.priority_combo)
        
        # 启用任务
        self.enabled_check = QCheckBox("启用任务")
        self.enabled_check.setChecked(True)
        layout.addRow("", self.enabled_check)
        
        # 添加到选项卡
        self.tab_widget.addTab(tab, "基本信息")
    
    def _create_schedule_tab(self):
        """创建计划选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 调度类型分组
        schedule_group = QGroupBox("调度类型")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # 调度类型选择
        self.schedule_type_manual = QRadioButton("手动运行")
        self.schedule_type_once = QRadioButton("单次运行")
        self.schedule_type_interval = QRadioButton("定时运行")
        self.schedule_type_cron = QRadioButton("Cron表达式")
        
        self.schedule_type_manual.setChecked(True)
        
        schedule_layout.addWidget(self.schedule_type_manual)
        schedule_layout.addWidget(self.schedule_type_once)
        schedule_layout.addWidget(self.schedule_type_interval)
        schedule_layout.addWidget(self.schedule_type_cron)
        
        # 连接信号
        self.schedule_type_manual.toggled.connect(self._on_schedule_type_changed)
        self.schedule_type_once.toggled.connect(self._on_schedule_type_changed)
        self.schedule_type_interval.toggled.connect(self._on_schedule_type_changed)
        self.schedule_type_cron.toggled.connect(self._on_schedule_type_changed)
        
        # 添加调度类型分组
        layout.addWidget(schedule_group)
        
        # 创建调度设置框
        self.schedule_stack = QGroupBox("调度设置")
        self.schedule_stack_layout = QFormLayout(self.schedule_stack)
        
        # 单次运行设置
        self.once_datetime = QDateTimeEdit()
        self.once_datetime.setDateTime(QDateTime.currentDateTime())
        self.once_datetime.setCalendarPopup(True)
        self.schedule_stack_layout.addRow("运行时间:", self.once_datetime)
        
        # 定时运行设置
        self.interval_value = QSpinBox()
        self.interval_value.setRange(1, 1000000)
        self.interval_value.setValue(1)
        
        self.interval_unit = QComboBox()
        self.interval_unit.addItems(["分钟", "小时", "天"])
        self.interval_unit.setCurrentIndex(1)  # 默认为小时
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_value)
        interval_layout.addWidget(self.interval_unit)
        
        self.schedule_stack_layout.addRow("运行间隔:", interval_layout)
        
        # Cron表达式设置
        self.cron_expr = QLineEdit()
        self.cron_expr.setPlaceholderText("* * * * *")
        
        self.cron_description = QLabel("每分钟运行一次")
        self.cron_description.setWordWrap(True)
        
        self.cron_expr.textChanged.connect(self._on_cron_expr_changed)
        
        self.schedule_stack_layout.addRow("Cron表达式:", self.cron_expr)
        self.schedule_stack_layout.addRow("", self.cron_description)
        
        # 添加调度设置框
        layout.addWidget(self.schedule_stack)
        self.schedule_stack.setVisible(False)
        
        # 超时设置
        timeout_group = QGroupBox("超时设置")
        timeout_layout = QHBoxLayout(timeout_group)
        
        self.timeout_check = QCheckBox("启用超时")
        self.timeout_value = QSpinBox()
        self.timeout_value.setRange(1, 86400)
        self.timeout_value.setValue(3600)
        self.timeout_value.setSuffix(" 秒")
        self.timeout_value.setEnabled(False)
        
        self.timeout_check.toggled.connect(self.timeout_value.setEnabled)
        
        timeout_layout.addWidget(self.timeout_check)
        timeout_layout.addWidget(self.timeout_value)
        
        # 添加超时设置
        layout.addWidget(timeout_group)
        
        # 重试设置
        retry_group = QGroupBox("重试设置")
        retry_layout = QFormLayout(retry_group)
        
        self.retry_check = QCheckBox("启用重试")
        retry_layout.addRow("", self.retry_check)
        
        self.retry_times = QSpinBox()
        self.retry_times.setRange(1, 10)
        self.retry_times.setValue(3)
        self.retry_times.setEnabled(False)
        retry_layout.addRow("重试次数:", self.retry_times)
        
        self.retry_interval = QSpinBox()
        self.retry_interval.setRange(1, 3600)
        self.retry_interval.setValue(60)
        self.retry_interval.setSuffix(" 秒")
        self.retry_interval.setEnabled(False)
        retry_layout.addRow("重试间隔:", self.retry_interval)
        
        self.retry_check.toggled.connect(self.retry_times.setEnabled)
        self.retry_check.toggled.connect(self.retry_interval.setEnabled)
        
        # 添加重试设置
        layout.addWidget(retry_group)
        
        # 添加到选项卡
        self.tab_widget.addTab(tab, "计划")
    
    def _create_task_type_tab(self):
        """创建任务类型选项卡"""
        self.task_type_tab = QTabWidget()
        
        # 创建URL请求选项卡
        self._create_url_tab()
        
        # 创建文件操作选项卡
        self._create_file_tab()
        
        # 创建程序执行选项卡
        self._create_program_tab()
        
        # 创建系统操作选项卡
        self._create_system_tab()
        
        # 创建数据库操作选项卡
        self._create_db_tab()
        
        # 添加到主选项卡
        self.tab_widget.addTab(self.task_type_tab, "任务参数")
    
    def _create_url_tab(self):
        """创建URL请求选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        layout.addRow("URL:", self.url_edit)
        
        # 请求方法
        self.http_method = QComboBox()
        self.http_method.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
        layout.addRow("请求方法:", self.http_method)
        
        # 请求头
        self.headers_edit = QTextEdit()
        self.headers_edit.setPlaceholderText("Content-Type: application/json\nAuthorization: Bearer token")
        self.headers_edit.setMaximumHeight(80)
        layout.addRow("请求头:", self.headers_edit)
        
        # 请求体
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText('{"key": "value"}')
        layout.addRow("请求体:", self.body_edit)
        
        # 预期状态码
        self.status_code = QSpinBox()
        self.status_code.setRange(100, 599)
        self.status_code.setValue(200)
        layout.addRow("预期状态码:", self.status_code)
        
        # 超时设置
        self.url_timeout = QSpinBox()
        self.url_timeout.setRange(0, 3600)  # 0表示无限制，最大值设为1小时
        self.url_timeout.setValue(30)
        self.url_timeout.setSuffix(" 秒 (0表示无限制)")
        layout.addRow("请求超时:", self.url_timeout)
        
        # 添加到任务类型选项卡
        self.task_type_tab.addTab(tab, "URL请求")
    
    def _create_file_tab(self):
        """创建文件操作选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 操作类型
        self.file_operation = QComboBox()
        self.file_operation.addItems(["复制", "移动", "删除", "备份", "压缩", "解压"])
        layout.addRow("操作类型:", self.file_operation)
        
        # 源路径
        source_layout = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_browse = QPushButton("浏览...")
        self.source_browse.clicked.connect(self._browse_source_path)
        source_layout.addWidget(self.source_path)
        source_layout.addWidget(self.source_browse)
        layout.addRow("源路径:", source_layout)
        
        # 目标路径
        target_layout = QHBoxLayout()
        self.target_path = QLineEdit()
        self.target_browse = QPushButton("浏览...")
        self.target_browse.clicked.connect(self._browse_target_path)
        target_layout.addWidget(self.target_path)
        target_layout.addWidget(self.target_browse)
        layout.addRow("目标路径:", target_layout)
        
        # 文件选项
        self.overwrite_check = QCheckBox("覆盖已存在的文件")
        layout.addRow("", self.overwrite_check)
        
        # 包含模式
        self.include_pattern = QLineEdit()
        self.include_pattern.setPlaceholderText("*.txt,*.doc")
        layout.addRow("包含模式:", self.include_pattern)
        
        # 排除模式
        self.exclude_pattern = QLineEdit()
        self.exclude_pattern.setPlaceholderText("*.tmp,*.bak")
        layout.addRow("排除模式:", self.exclude_pattern)
        
        # 添加到任务类型选项卡
        self.task_type_tab.addTab(tab, "文件操作")
    
    def _create_program_tab(self):
        """创建程序执行选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 命令
        command_layout = QHBoxLayout()
        self.command_edit = QLineEdit()
        self.command_browse = QPushButton("浏览...")
        self.command_browse.clicked.connect(self._browse_command)
        command_layout.addWidget(self.command_edit)
        command_layout.addWidget(self.command_browse)
        layout.addRow("命令:", command_layout)
        
        # 工作目录
        dir_layout = QHBoxLayout()
        self.work_dir = QLineEdit()
        self.work_dir_browse = QPushButton("浏览...")
        self.work_dir_browse.clicked.connect(self._browse_work_dir)
        dir_layout.addWidget(self.work_dir)
        dir_layout.addWidget(self.work_dir_browse)
        layout.addRow("工作目录:", dir_layout)
        
        # 执行选项
        self.shell_check = QCheckBox("使用shell执行")
        self.shell_check.setChecked(True)
        layout.addRow("", self.shell_check)
        
        self.capture_check = QCheckBox("捕获输出")
        self.capture_check.setChecked(True)
        layout.addRow("", self.capture_check)
        
        self.wait_check = QCheckBox("等待完成")
        self.wait_check.setChecked(True)
        layout.addRow("", self.wait_check)
        
        # 环境变量
        self.env_edit = QTextEdit()
        self.env_edit.setPlaceholderText("KEY=value\nANOTHER_KEY=another_value")
        self.env_edit.setMaximumHeight(80)
        layout.addRow("环境变量:", self.env_edit)
        
        # 添加到任务类型选项卡
        self.task_type_tab.addTab(tab, "程序执行")
    
    def _create_system_tab(self):
        """创建系统操作选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 操作类型
        self.system_operation = QComboBox()
        self.system_operation.addItems(["关机", "重启", "休眠", "睡眠", "锁定", "注销"])
        layout.addRow("操作类型:", self.system_operation)
        
        # 延迟时间
        self.delay_seconds = QSpinBox()
        self.delay_seconds.setRange(0, 3600)
        self.delay_seconds.setValue(0)
        self.delay_seconds.setSuffix(" 秒")
        layout.addRow("延迟时间:", self.delay_seconds)
        
        # 操作选项
        self.force_check = QCheckBox("强制执行")
        layout.addRow("", self.force_check)
        
        self.admin_check = QCheckBox("使用管理员权限")
        self.admin_check.setChecked(True)
        layout.addRow("", self.admin_check)
        
        # 消息
        self.system_message = QLineEdit()
        self.system_message.setPlaceholderText("系统将在一分钟后关机，请保存您的工作")
        layout.addRow("显示消息:", self.system_message)
        
        # 添加到任务类型选项卡
        self.task_type_tab.addTab(tab, "系统操作")
    
    def _create_db_tab(self):
        """创建数据库操作选项卡"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 数据库类型
        self.db_type = QComboBox()
        self.db_type.addItems(["MySQL", "PostgreSQL", "SQLite", "SQL Server"])
        layout.addRow("数据库类型:", self.db_type)
        
        # 操作类型
        self.db_operation = QComboBox()
        self.db_operation.addItems(["查询", "备份", "恢复", "执行脚本"])
        layout.addRow("操作类型:", self.db_operation)
        
        # 连接字符串
        self.connection_string = QLineEdit()
        self.connection_string.setPlaceholderText("mysql://user:password@localhost:3306/dbname")
        layout.addRow("连接字符串:", self.connection_string)
        
        # 查询/脚本
        self.sql_query = QTextEdit()
        self.sql_query.setPlaceholderText("SELECT * FROM users WHERE status = 'active'")
        layout.addRow("SQL查询:", self.sql_query)
        
        # 脚本文件
        script_layout = QHBoxLayout()
        self.script_path = QLineEdit()
        self.script_browse = QPushButton("浏览...")
        self.script_browse.clicked.connect(self._browse_script)
        script_layout.addWidget(self.script_path)
        script_layout.addWidget(self.script_browse)
        layout.addRow("脚本文件:", script_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_file = QLineEdit()
        self.output_browse = QPushButton("浏览...")
        self.output_browse.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_file)
        output_layout.addWidget(self.output_browse)
        layout.addRow("输出文件:", output_layout)
        
        # 压缩备份
        self.compress_check = QCheckBox("压缩备份")
        self.compress_check.setChecked(True)
        layout.addRow("", self.compress_check)
        
        # 添加到任务类型选项卡
        self.task_type_tab.addTab(tab, "数据库操作")
    
    def _create_advanced_tab(self):
        """创建高级选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 通知设置
        notify_group = QGroupBox("通知设置")
        notify_layout = QFormLayout(notify_group)
        
        self.notify_on_success = QCheckBox("成功时通知")
        self.notify_on_failure = QCheckBox("失败时通知")
        self.notify_on_timeout = QCheckBox("超时时通知")
        
        self.notify_on_failure.setChecked(True)
        self.notify_on_timeout.setChecked(True)
        
        notify_layout.addRow("", self.notify_on_success)
        notify_layout.addRow("", self.notify_on_failure)
        notify_layout.addRow("", self.notify_on_timeout)
        
        # 依赖任务
        depend_group = QGroupBox("任务依赖")
        depend_layout = QVBoxLayout(depend_group)
        
        depend_info = QLabel("依赖任务功能尚未实现")
        depend_info.setAlignment(Qt.AlignCenter)
        depend_layout.addWidget(depend_info)
        
        # 添加分组到布局
        layout.addWidget(notify_group)
        layout.addWidget(depend_group)
        layout.addStretch(1)
        
        # 添加到选项卡
        self.tab_widget.addTab(tab, "高级")
    
    def _on_task_type_changed(self, index):
        """
        任务类型改变时的处理函数
        
        参数:
            index: 当前索引
        """
        self.task_type_tab.setCurrentIndex(index)
    
    def _on_schedule_type_changed(self):
        """调度类型改变时的处理函数"""
        self.schedule_stack.setVisible(not self.schedule_type_manual.isChecked())
        
        # 根据选择的调度类型更新UI
        try:
            # 首先隐藏所有控件
            for i in range(self.schedule_stack_layout.rowCount()):
                label_item = self.schedule_stack_layout.itemAt(i, QFormLayout.LabelRole)
                field_item = self.schedule_stack_layout.itemAt(i, QFormLayout.FieldRole)
                
                if label_item and label_item.widget():
                    label_item.widget().setVisible(False)
                
                if field_item and field_item.widget():
                    field_item.widget().setVisible(False)
            
            # 根据选择的调度类型显示相应控件
            if self.schedule_type_once.isChecked():
                # 显示单次运行设置
                label_item = self.schedule_stack_layout.itemAt(0, QFormLayout.LabelRole)
                field_item = self.schedule_stack_layout.itemAt(0, QFormLayout.FieldRole)
                
                if label_item and label_item.widget():
                    label_item.widget().setVisible(True)
                
                if field_item and field_item.widget():
                    field_item.widget().setVisible(True)
                
            elif self.schedule_type_interval.isChecked():
                # 显示定时运行设置
                label_item = self.schedule_stack_layout.itemAt(1, QFormLayout.LabelRole)
                field_item = self.schedule_stack_layout.itemAt(1, QFormLayout.FieldRole)
                
                if label_item and label_item.widget():
                    label_item.widget().setVisible(True)
                
                if field_item and field_item.widget():
                    field_item.widget().setVisible(True)
                
            elif self.schedule_type_cron.isChecked():
                # 显示Cron表达式设置
                for i in range(2, 4):
                    label_item = self.schedule_stack_layout.itemAt(i, QFormLayout.LabelRole)
                    field_item = self.schedule_stack_layout.itemAt(i, QFormLayout.FieldRole)
                    
                    if label_item and label_item.widget():
                        label_item.widget().setVisible(True)
                    
                    if field_item and field_item.widget():
                        field_item.widget().setVisible(True)
        except Exception as e:
            self.logger.error(f"更新调度设置UI失败: {str(e)}")
    
    def _on_cron_expr_changed(self, text):
        """
        Cron表达式改变时的处理函数
        
        参数:
            text: 当前表达式文本
        """
        if not text:
            self.cron_description.setText("请输入Cron表达式")
            return
        
        try:
            cron_parser = CronParser()
            if cron_parser.validate(text):
                description = cron_parser.get_human_readable_description(text)
                next_run = cron_parser.get_next_execution_time(text)
                
                if next_run:
                    next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
                    self.cron_description.setText(f"{description}\n下次运行时间: {next_run_str}")
                else:
                    self.cron_description.setText(description)
            else:
                self.cron_description.setText("无效的Cron表达式")
        except Exception as e:
            self.logger.error(f"解析Cron表达式出错: {str(e)}")
            self.cron_description.setText("解析Cron表达式出错")
    
    def _browse_source_path(self):
        """浏览源文件/目录"""
        path, _ = QFileDialog.getOpenFileName(self, "选择源文件")
        if path:
            self.source_path.setText(path)
    
    def _browse_target_path(self):
        """浏览目标文件/目录"""
        path = QFileDialog.getExistingDirectory(self, "选择目标目录")
        if path:
            self.target_path.setText(path)
    
    def _browse_command(self):
        """浏览命令/程序"""
        path, _ = QFileDialog.getOpenFileName(self, "选择程序")
        if path:
            self.command_edit.setText(path)
    
    def _browse_work_dir(self):
        """浏览工作目录"""
        path = QFileDialog.getExistingDirectory(self, "选择工作目录")
        if path:
            self.work_dir.setText(path)
    
    def _browse_script(self):
        """浏览脚本文件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择脚本文件", "", "SQL文件 (*.sql);;所有文件 (*)")
        if path:
            self.script_path.setText(path)
    
    def _browse_output(self):
        """浏览输出文件"""
        path, _ = QFileDialog.getSaveFileName(self, "选择输出文件", "", "所有文件 (*)")
        if path:
            self.output_file.setText(path)
    
    def _populate_form(self):
        """填充表单数据"""
        # 基本信息
        self.name_edit.setText(self.task.name)
        self.description_edit.setText(self.task.description)
        
        if self.task.group:
            self.group_edit.setText(self.task.group)
        
        if self.task.tags:
            self.tags_edit.setText(", ".join(self.task.tags))
        
        self.priority_combo.setCurrentIndex(self.task.priority.value)
        self.enabled_check.setChecked(self.task.enabled)
        
        # 设置任务类型
        if isinstance(self.task, URLTask):
            self.task_type_combo.setCurrentIndex(0)
            self._populate_url_task()
        elif isinstance(self.task, FileTask):
            self.task_type_combo.setCurrentIndex(1)
            self._populate_file_task()
        elif isinstance(self.task, ProgramTask):
            self.task_type_combo.setCurrentIndex(2)
            self._populate_program_task()
        elif isinstance(self.task, SystemTask):
            self.task_type_combo.setCurrentIndex(3)
            self._populate_system_task()
        elif isinstance(self.task, DBTask):
            self.task_type_combo.setCurrentIndex(4)
            self._populate_db_task()
        
        # 调度设置
        self._populate_schedule()
        
        # 超时设置
        if self.task.timeout > 0:
            self.timeout_check.setChecked(True)
            self.timeout_value.setValue(self.task.timeout)
        
        # 重试设置
        if self.task.max_retries > 0:
            self.retry_check.setChecked(True)
            self.retry_times.setValue(self.task.max_retries)
            self.retry_interval.setValue(self.task.retry_interval)
    
    def _populate_url_task(self):
        """填充URL任务表单"""
        task = self.task
        
        if task.url:
            self.url_edit.setText(task.url)
        
        # 请求方法
        method_index = self.http_method.findText(task.method)
        if method_index >= 0:
            self.http_method.setCurrentIndex(method_index)
        
        # 请求头
        if task.headers:
            headers_text = "\n".join([f"{k}: {v}" for k, v in task.headers.items()])
            self.headers_edit.setText(headers_text)
        
        # 请求体
        if task.body:
            if isinstance(task.body, dict):
                import json
                self.body_edit.setText(json.dumps(task.body, indent=2))
            else:
                self.body_edit.setText(str(task.body))
        
        # 预期状态码
        self.status_code.setValue(task.expected_status_code)
        
        # 超时设置
        self.url_timeout.setValue(task.request_timeout)
    
    def _populate_file_task(self):
        """填充文件任务表单"""
        task = self.task
        
        # 操作类型
        op_map = {
            "copy": 0,
            "move": 1,
            "delete": 2,
            "backup": 3,
            "zip": 4,
            "unzip": 5
        }
        if task.operation in op_map:
            self.file_operation.setCurrentIndex(op_map[task.operation])
        
        # 源路径和目标路径
        if task.source_path:
            self.source_path.setText(task.source_path)
        
        if task.target_path:
            self.target_path.setText(task.target_path)
        
        # 文件选项
        self.overwrite_check.setChecked(task.overwrite)
        
        if task.include_pattern:
            self.include_pattern.setText(task.include_pattern)
        
        if task.exclude_pattern:
            self.exclude_pattern.setText(task.exclude_pattern)
    
    def _populate_program_task(self):
        """填充程序任务表单"""
        task = self.task
        
        if task.command:
            self.command_edit.setText(task.command)
        
        if task.working_directory:
            self.work_dir.setText(task.working_directory)
        
        self.shell_check.setChecked(task.shell)
        self.capture_check.setChecked(task.capture_output)
        self.wait_check.setChecked(task.wait_for_completion)
        
        if task.environment:
            env_text = "\n".join([f"{k}={v}" for k, v in task.environment.items()])
            self.env_edit.setText(env_text)
    
    def _populate_system_task(self):
        """填充系统任务表单"""
        task = self.task
        
        # 操作类型
        op_map = {
            "shutdown": 0,
            "restart": 1,
            "hibernate": 2,
            "sleep": 3,
            "lock": 4,
            "logoff": 5
        }
        if task.operation in op_map:
            self.system_operation.setCurrentIndex(op_map[task.operation])
        
        self.delay_seconds.setValue(task.delay_seconds)
        self.force_check.setChecked(task.force)
        self.admin_check.setChecked(task.run_as_admin)
        
        if task.message:
            self.system_message.setText(task.message)
    
    def _populate_db_task(self):
        """填充数据库任务表单"""
        task = self.task
        
        # 数据库类型
        db_type_map = {
            "mysql": 0,
            "postgresql": 1,
            "sqlite": 2,
            "sqlserver": 3
        }
        if task.db_type in db_type_map:
            self.db_type.setCurrentIndex(db_type_map[task.db_type])
        
        # 操作类型
        op_map = {
            "query": 0,
            "backup": 1,
            "restore": 2,
            "execute_script": 3
        }
        if task.operation in op_map:
            self.db_operation.setCurrentIndex(op_map[task.operation])
        
        if task.connection_string:
            self.connection_string.setText(task.connection_string)
        
        if task.query:
            self.sql_query.setText(task.query)
        
        if task.query and os.path.isfile(task.query):
            self.script_path.setText(task.query)
        
        if task.output_file:
            self.output_file.setText(task.output_file)
        
        self.compress_check.setChecked(task.compress_backup)
    
    def _populate_schedule(self):
        """填充调度设置"""
        if not self.task.schedule:
            self.schedule_type_manual.setChecked(True)
            return
        
        schedule = self.task.schedule
        
        if schedule.startswith('date:'):
            # 单次运行
            self.schedule_type_once.setChecked(True)
            try:
                dt = datetime.fromisoformat(schedule[5:])
                self.once_datetime.setDateTime(QDateTime(dt.year, dt.month, dt.day, 
                                                        dt.hour, dt.minute, dt.second))
            except:
                self.logger.warning(f"无法解析日期时间: {schedule[5:]}")
                
        elif schedule.startswith('interval:'):
            # 定时运行
            self.schedule_type_interval.setChecked(True)
            try:
                interval_expr = schedule[9:]
                interval_value = int(interval_expr[:-1])
                interval_unit = interval_expr[-1]
                
                self.interval_value.setValue(interval_value)
                
                if interval_unit == 'm':
                    self.interval_unit.setCurrentIndex(0)  # 分钟
                elif interval_unit == 'h':
                    self.interval_unit.setCurrentIndex(1)  # 小时
                elif interval_unit == 'd':
                    self.interval_unit.setCurrentIndex(2)  # 天
            except:
                self.logger.warning(f"无法解析间隔表达式: {schedule[9:]}")
                
        elif schedule.startswith('cron:'):
            # Cron表达式
            self.schedule_type_cron.setChecked(True)
            self.cron_expr.setText(schedule[5:])
        
        # 触发调度类型变更事件以更新UI
        self._on_schedule_type_changed()
    
    def _validate_input(self):
        """
        验证输入数据
        
        返回:
            bool: 是否有效
        """
        # 检查必填字段
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入任务名称")
            return False
        
        # 检查任务类型特定字段
        task_type_index = self.task_type_combo.currentIndex()
        
        if task_type_index == 0:  # URL请求
            if not self.url_edit.text().strip():
                QMessageBox.warning(self, "输入错误", "请输入URL")
                return False
        
        elif task_type_index == 1:  # 文件操作
            if not self.source_path.text().strip():
                QMessageBox.warning(self, "输入错误", "请输入源文件路径")
                return False
                
            op_idx = self.file_operation.currentIndex()
            if op_idx not in [2]:  # 除了删除操作外，都需要目标路径
                if not self.target_path.text().strip():
                    QMessageBox.warning(self, "输入错误", "请输入目标路径")
                    return False
        
        elif task_type_index == 2:  # 程序执行
            if not self.command_edit.text().strip():
                QMessageBox.warning(self, "输入错误", "请输入命令")
                return False
        
        elif task_type_index == 4:  # 数据库操作
            if not self.connection_string.text().strip():
                QMessageBox.warning(self, "输入错误", "请输入数据库连接字符串")
                return False
                
            op_idx = self.db_operation.currentIndex()
            if op_idx == 0:  # 查询
                if not self.sql_query.toPlainText().strip():
                    QMessageBox.warning(self, "输入错误", "请输入SQL查询")
                    return False
            elif op_idx == 3:  # 执行脚本
                if not self.script_path.text().strip():
                    QMessageBox.warning(self, "输入错误", "请选择SQL脚本文件")
                    return False
        
        return True
    
    def accept(self):
        """确认对话框"""
        # 验证输入
        if not self._validate_input():
            return
        
        try:
            # 创建或更新任务
            if self.task is None:
                self._create_task()
            else:
                self._update_task()
            
            super().accept()
        except Exception as e:
            self.logger.exception("保存任务失败")
            QMessageBox.critical(self, "错误", f"保存任务失败: {str(e)}")
    
    def _create_task(self):
        """创建新任务"""
        # 根据任务类型创建任务
        task_type_index = self.task_type_combo.currentIndex()
        
        if task_type_index == 0:  # URL请求
            task = self._create_url_task()
        elif task_type_index == 1:  # 文件操作
            task = self._create_file_task()
        elif task_type_index == 2:  # 程序执行
            task = self._create_program_task()
        elif task_type_index == 3:  # 系统操作
            task = self._create_system_task()
        elif task_type_index == 4:  # 数据库操作
            task = self._create_db_task()
        else:
            raise ValueError(f"不支持的任务类型: {task_type_index}")
        
        # 设置共同属性
        self._set_common_properties(task)
        
        # 添加到调度器
        self.scheduler.add_task(task)
        
        self.logger.info(f"创建任务成功: {task.name} [{task.id}]")
    
    def _update_task(self):
        """更新现有任务"""
        task = self.task
        
        # 设置共同属性
        self._set_common_properties(task)
        
        # 根据任务类型更新任务属性
        task_type_index = self.task_type_combo.currentIndex()
        
        if task_type_index == 0:  # URL请求
            self._update_url_task(task)
        elif task_type_index == 1:  # 文件操作
            self._update_file_task(task)
        elif task_type_index == 2:  # 程序执行
            self._update_program_task(task)
        elif task_type_index == 3:  # 系统操作
            self._update_system_task(task)
        elif task_type_index == 4:  # 数据库操作
            self._update_db_task(task)
        
        # 更新调度器中的任务
        self.scheduler.update_task(task.id)
        
        self.logger.info(f"更新任务成功: {task.name} [{task.id}]")
    
    def _set_common_properties(self, task):
        """设置任务共同属性"""
        # 基本信息
        task.name = self.name_edit.text().strip()
        task.description = self.description_edit.toPlainText()
        task.group = self.group_edit.text().strip()
        
        # 标签
        tags_text = self.tags_edit.text().strip()
        if tags_text:
            task.tags = [tag.strip() for tag in tags_text.split(',')]
        else:
            task.tags = []
        
        # 优先级
        priority_index = self.priority_combo.currentIndex()
        task.priority = TaskPriority(priority_index)
        
        # 启用状态
        task.enabled = self.enabled_check.isChecked()
        
        # 调度设置
        if self.schedule_type_manual.isChecked():
            task.schedule = None
        elif self.schedule_type_once.isChecked():
            dt = self.once_datetime.dateTime().toPyDateTime()
            task.schedule = f"date:{dt.isoformat()}"
        elif self.schedule_type_interval.isChecked():
            interval_value = self.interval_value.value()
            interval_unit_index = self.interval_unit.currentIndex()
            interval_unit = ''
            if interval_unit_index == 0:
                interval_unit = 'm'  # 分钟
            elif interval_unit_index == 1:
                interval_unit = 'h'  # 小时
            else:
                interval_unit = 'd'  # 天
            task.schedule = f"interval:{interval_value}{interval_unit}"
        elif self.schedule_type_cron.isChecked():
            cron_expr = self.cron_expr.text().strip()
            if cron_expr:
                task.schedule = f"cron:{cron_expr}"
        
        # 超时设置
        if self.timeout_check.isChecked():
            task.timeout = self.timeout_value.value()
        else:
            task.timeout = 0
        
        # 重试设置
        if self.retry_check.isChecked():
            task.max_retries = self.retry_times.value()
            task.retry_interval = self.retry_interval.value()
        else:
            task.max_retries = 0
            task.retry_interval = 60
    
    def _create_url_task(self):
        """创建URL任务"""
        url = self.url_edit.text().strip()
        method = self.http_method.currentText()
        
        # 解析请求头
        headers = {}
        headers_text = self.headers_edit.toPlainText().strip()
        if headers_text:
            for line in headers_text.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
        
        # 解析请求体
        body = self.body_edit.toPlainText().strip()
        if body:
            try:
                # 尝试解析为JSON
                import json
                body = json.loads(body)
            except:
                # 解析失败，保持为文本
                pass
        else:
            body = None
        
        # 创建任务
        task = URLTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText(),
            url=url,
            method=method,
            headers=headers,
            body=body,
            timeout=self.url_timeout.value(),
        )
        
        # 设置预期状态码
        task.expected_status_code = self.status_code.value()
        
        return task
    
    def _update_url_task(self, task):
        """更新URL任务"""
        task.url = self.url_edit.text().strip()
        task.method = self.http_method.currentText()
        
        # 解析请求头
        headers = {}
        headers_text = self.headers_edit.toPlainText().strip()
        if headers_text:
            for line in headers_text.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
        task.headers = headers
        
        # 解析请求体
        body = self.body_edit.toPlainText().strip()
        if body:
            try:
                # 尝试解析为JSON
                import json
                body = json.loads(body)
            except:
                # 解析失败，保持为文本
                pass
        else:
            body = None
        task.body = body
        
        # 更新预期状态码
        task.expected_status_code = self.status_code.value()
        
        # 更新超时设置
        task.request_timeout = self.url_timeout.value()
    
    def _create_file_task(self):
        """创建文件任务"""
        # 解析操作类型
        operation_map = [
            "copy", "move", "delete", "backup", "zip", "unzip"
        ]
        operation = operation_map[self.file_operation.currentIndex()]
        
        # 创建任务
        task = FileTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText(),
            operation=operation,
            source_path=self.source_path.text().strip(),
            target_path=self.target_path.text().strip(),
            overwrite=self.overwrite_check.isChecked()
        )
        
        # 设置文件模式
        task.include_pattern = self.include_pattern.text().strip()
        task.exclude_pattern = self.exclude_pattern.text().strip()
        
        return task
    
    def _update_file_task(self, task):
        """更新文件任务"""
        # 解析操作类型
        operation_map = [
            "copy", "move", "delete", "backup", "zip", "unzip"
        ]
        task.operation = operation_map[self.file_operation.currentIndex()]
        
        # 更新路径
        task.source_path = self.source_path.text().strip()
        task.target_path = self.target_path.text().strip()
        
        # 更新选项
        task.overwrite = self.overwrite_check.isChecked()
        task.include_pattern = self.include_pattern.text().strip()
        task.exclude_pattern = self.exclude_pattern.text().strip()
    
    def _create_program_task(self):
        """创建程序执行任务"""
        # 创建任务
        task = ProgramTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText(),
            command=self.command_edit.text().strip(),
            working_directory=self.work_dir.text().strip(),
            shell=self.shell_check.isChecked(),
            capture_output=self.capture_check.isChecked()
        )
        
        # 设置等待完成选项
        task.wait_for_completion = self.wait_check.isChecked()
        
        # 解析环境变量
        env = {}
        env_text = self.env_edit.toPlainText().strip()
        if env_text:
            for line in env_text.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
        task.environment = env
        
        return task
    
    def _update_program_task(self, task):
        """更新程序执行任务"""
        # 更新基本属性
        task.command = self.command_edit.text().strip()
        task.working_directory = self.work_dir.text().strip()
        
        # 更新选项
        task.shell = self.shell_check.isChecked()
        task.capture_output = self.capture_check.isChecked()
        task.wait_for_completion = self.wait_check.isChecked()
        
        # 解析环境变量
        env = {}
        env_text = self.env_edit.toPlainText().strip()
        if env_text:
            for line in env_text.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
        task.environment = env
    
    def _create_system_task(self):
        """创建系统操作任务"""
        # 解析操作类型
        operation_map = [
            "shutdown", "restart", "hibernate", "sleep", "lock", "logoff"
        ]
        operation = operation_map[self.system_operation.currentIndex()]
        
        # 创建任务
        task = SystemTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText(),
            operation=operation,
            force=self.force_check.isChecked(),
            delay_seconds=self.delay_seconds.value()
        )
        
        # 设置选项
        task.run_as_admin = self.admin_check.isChecked()
        task.message = self.system_message.text().strip()
        
        return task
    
    def _update_system_task(self, task):
        """更新系统操作任务"""
        # 解析操作类型
        operation_map = [
            "shutdown", "restart", "hibernate", "sleep", "lock", "logoff"
        ]
        task.operation = operation_map[self.system_operation.currentIndex()]
        
        # 更新选项
        task.force = self.force_check.isChecked()
        task.delay_seconds = self.delay_seconds.value()
        task.run_as_admin = self.admin_check.isChecked()
        task.message = self.system_message.text().strip()
    
    def _create_db_task(self):
        """创建数据库任务"""
        # 解析数据库类型
        db_type_map = ["mysql", "postgresql", "sqlite", "sqlserver"]
        db_type = db_type_map[self.db_type.currentIndex()]
        
        # 解析操作类型
        operation_map = ["query", "backup", "restore", "execute_script"]
        operation = operation_map[self.db_operation.currentIndex()]
        
        # 获取查询或脚本
        query = None
        if operation == "query":
            query = self.sql_query.toPlainText().strip()
        elif operation == "execute_script":
            query = self.script_path.text().strip()
        
        # 创建任务
        task = DBTask(
            name=self.name_edit.text().strip(),
            description=self.description_edit.toPlainText(),
            operation=operation,
            db_type=db_type,
            connection_string=self.connection_string.text().strip(),
            query=query,
            output_file=self.output_file.text().strip()
        )
        
        # 设置选项
        task.compress_backup = self.compress_check.isChecked()
        
        return task
    
    def _update_db_task(self, task):
        """更新数据库任务"""
        # 解析数据库类型
        db_type_map = ["mysql", "postgresql", "sqlite", "sqlserver"]
        task.db_type = db_type_map[self.db_type.currentIndex()]
        
        # 解析操作类型
        operation_map = ["query", "backup", "restore", "execute_script"]
        task.operation = operation_map[self.db_operation.currentIndex()]
        
        # 更新连接字符串
        task.connection_string = self.connection_string.text().strip()
        
        # 获取查询或脚本
        if task.operation == "query":
            task.query = self.sql_query.toPlainText().strip()
        elif task.operation == "execute_script":
            task.query = self.script_path.text().strip()
        
        # 更新输出文件
        task.output_file = self.output_file.text().strip()
        
        # 更新选项
        task.compress_backup = self.compress_check.isChecked()
