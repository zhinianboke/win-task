#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主窗口模块

实现应用程序的主窗口界面
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QAction, QMenu, QToolBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSystemTrayIcon,
    QStyle, QSplitter, QFrame, QComboBox, QLineEdit, QFormLayout, QSpinBox, QCheckBox,
    QGroupBox, QCalendarWidget, QProgressDialog
)
from PyQt5.QtCore import Qt, QSize, QTimer, QSettings, pyqtSignal, pyqtSlot, QDate
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor

from src.core.task import TaskStatus, TaskPriority
from src.core.scheduler import TaskScheduler
from src.core.settings import Settings
from src.ui.task_dialog import TaskDialog
from src.core.task_execution_thread import TaskExecutionThread
from src.utils.path_utils import get_app_data_dir


class MainWindow(QMainWindow):
    """应用程序主窗口"""
    
    def __init__(self, scheduler, settings, parent=None):
        """
        初始化主窗口
        
        参数:
            scheduler (TaskScheduler): 任务调度器
            settings (Settings): 设置管理器
            parent (QWidget, optional): 父窗口
        """
        super().__init__(parent)
        
        # 保存传入的对象
        self.scheduler = scheduler
        self.settings = settings
        
        # 日志记录器
        self.logger = logging.getLogger("main_window")
        
        # 创建系统托盘
        self.tray_icon = None
        
        # 初始化UI
        self._init_ui()
        
        # 创建定时器，用于定期更新任务状态
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_tasks_view)
        self.update_timer.start(5000)  # 每5秒更新一次
        
        # 创建定时器，用于定期保存任务数据
        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self._auto_save_tasks)
        self.save_timer.start(60000)  # 每60秒保存一次
        
        # 初始加载任务列表
        self.update_tasks_view()
        
        self.logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化UI界面"""
        # 设置窗口属性
        self.setWindowTitle("Win-Task - Windows 定时任务管理系统")
        self.setMinimumSize(900, 600)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), 'assets/icons/app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建主窗口部件
        self._create_central_widget()
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建状态栏
        self._create_status_bar()
        
        # 创建系统托盘
        self._create_system_tray()
    
    def _create_central_widget(self):
        """创建中央窗口部件"""
        # 创建中央窗口
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建任务选项卡
        self._create_tasks_tab()
        
        # 创建日历选项卡
        self._create_calendar_tab()
        
        # 创建日志选项卡
        self._create_logs_tab()
        
        # 创建仪表盘选项卡
        self._create_dashboard_tab()
        
        # 创建设置选项卡
        self._create_settings_tab()
    
    def _create_tasks_tab(self):
        """创建任务选项卡"""
        tasks_tab = QWidget()
        layout = QVBoxLayout(tasks_tab)
        
        # 顶部操作区域
        top_layout = QHBoxLayout()
        
        # 添加按钮
        self.btn_add_task = QPushButton("新建任务")
        self.btn_add_task.clicked.connect(self.add_task)
        top_layout.addWidget(self.btn_add_task)
        
        # 编辑按钮
        self.btn_edit_task = QPushButton("编辑任务")
        self.btn_edit_task.clicked.connect(self.edit_task)
        top_layout.addWidget(self.btn_edit_task)
        
        # 删除按钮
        self.btn_delete_task = QPushButton("删除任务")
        self.btn_delete_task.clicked.connect(self.delete_task)
        top_layout.addWidget(self.btn_delete_task)
        
        # 立即运行按钮
        self.btn_run_task = QPushButton("立即运行")
        self.btn_run_task.clicked.connect(self.run_task)
        top_layout.addWidget(self.btn_run_task)
        
        # 启用/禁用按钮
        self.btn_toggle_task = QPushButton("启用/禁用")
        self.btn_toggle_task.clicked.connect(self.toggle_task)
        top_layout.addWidget(self.btn_toggle_task)
        
        # 搜索框
        top_layout.addStretch()
        search_label = QLabel("搜索:")
        top_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入任务名称或ID")
        self.search_input.textChanged.connect(self.filter_tasks)
        top_layout.addWidget(self.search_input)
        
        # 添加顶部布局
        layout.addLayout(top_layout)
        
        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(8)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "名称", "状态", "类型", "计划", "上次运行", "下次运行", "描述"
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tasks_table.itemDoubleClicked.connect(self.edit_task)
        
        # 设置ID列宽度
        self.tasks_table.setColumnWidth(0, 80)  # ID
        self.tasks_table.setColumnWidth(1, 150)  # 名称
        self.tasks_table.setColumnWidth(2, 80)  # 状态
        self.tasks_table.setColumnWidth(3, 100)  # 类型
        self.tasks_table.setColumnWidth(4, 100)  # 计划
        self.tasks_table.setColumnWidth(5, 150)  # 上次运行
        self.tasks_table.setColumnWidth(6, 150)  # 下次运行
        
        layout.addWidget(self.tasks_table)
        
        # 添加到选项卡
        self.tab_widget.addTab(tasks_tab, "任务管理")
    
    def _create_calendar_tab(self):
        """创建日历选项卡"""
        calendar_tab = QWidget()
        layout = QVBoxLayout(calendar_tab)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧日历部分
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        
        # 添加日历控件
        from PyQt5.QtWidgets import QCalendarWidget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        calendar_layout.addWidget(self.calendar)
        
        # 添加当前月份任务统计
        stats_group = QGroupBox("当月任务统计")
        stats_layout = QFormLayout(stats_group)
        
        self.month_total_tasks = QLabel("0")
        stats_layout.addRow("总任务数:", self.month_total_tasks)
        
        self.month_completed_tasks = QLabel("0")
        stats_layout.addRow("已完成:", self.month_completed_tasks)
        
        self.month_failed_tasks = QLabel("0")
        stats_layout.addRow("失败:", self.month_failed_tasks)
        
        self.month_pending_tasks = QLabel("0")
        stats_layout.addRow("待执行:", self.month_pending_tasks)
        
        calendar_layout.addWidget(stats_group)
        
        # 添加左侧部件到分割器
        splitter.addWidget(calendar_widget)
        
        # 右侧任务列表部分
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        
        # 添加日期标签
        self.selected_date_label = QLabel("选择的日期: 无")
        self.selected_date_label.setAlignment(Qt.AlignCenter)
        self.selected_date_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        tasks_layout.addWidget(self.selected_date_label)
        
        # 添加任务表格
        self.calendar_tasks_table = QTableWidget()
        self.calendar_tasks_table.setColumnCount(5)
        self.calendar_tasks_table.setHorizontalHeaderLabels(["ID", "名称", "时间", "状态", "类型"])
        self.calendar_tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.calendar_tasks_table.horizontalHeader().setStretchLastSection(True)
        self.calendar_tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.calendar_tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.calendar_tasks_table.itemDoubleClicked.connect(self.edit_task)
        
        # 设置列宽
        self.calendar_tasks_table.setColumnWidth(0, 80)   # ID
        self.calendar_tasks_table.setColumnWidth(1, 150)  # 名称
        self.calendar_tasks_table.setColumnWidth(2, 150)  # 时间
        self.calendar_tasks_table.setColumnWidth(3, 80)   # 状态
        
        tasks_layout.addWidget(self.calendar_tasks_table)
        
        # 添加按钮区域
        button_layout = QHBoxLayout()
        
        # 添加任务按钮
        add_task_btn = QPushButton("新建任务")
        add_task_btn.clicked.connect(self._add_task_on_date)
        button_layout.addWidget(add_task_btn)
        
        # 查看全部按钮
        view_all_btn = QPushButton("查看全部")
        view_all_btn.clicked.connect(self._view_all_tasks)
        button_layout.addWidget(view_all_btn)
        
        tasks_layout.addLayout(button_layout)
        
        # 添加右侧部件到分割器
        splitter.addWidget(tasks_widget)
        
        # 设置分割器初始大小
        splitter.setSizes([300, 500])
        
        # 添加到选项卡
        self.tab_widget.addTab(calendar_tab, "日历视图")
        
        # 初始化日历视图
        self._update_calendar()
    
    def _create_logs_tab(self):
        """创建日志选项卡"""
        logs_tab = QWidget()
        layout = QVBoxLayout(logs_tab)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 日志级别选择
        level_label = QLabel("日志级别:")
        top_layout.addWidget(level_label)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["全部", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.log_level_combo.currentIndexChanged.connect(self._filter_logs)
        top_layout.addWidget(self.log_level_combo)
        
        # 日志组件选择
        component_label = QLabel("组件:")
        top_layout.addWidget(component_label)
        
        self.log_component_combo = QComboBox()
        self.log_component_combo.addItems(["全部", "scheduler", "executor", "task", "settings", "main_window"])
        self.log_component_combo.currentIndexChanged.connect(self._filter_logs)
        top_layout.addWidget(self.log_component_combo)
        
        # 搜索框
        search_label = QLabel("搜索:")
        top_layout.addWidget(search_label)
        
        self.log_search_input = QLineEdit()
        self.log_search_input.setPlaceholderText("输入搜索关键词")
        self.log_search_input.textChanged.connect(self._filter_logs)
        top_layout.addWidget(self.log_search_input)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_logs)
        top_layout.addWidget(refresh_btn)
        
        # 清空按钮
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self._clear_logs)
        top_layout.addWidget(clear_btn)
        
        layout.addLayout(top_layout)
        
        # 日志表格
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["时间", "级别", "组件", "消息"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.logs_table.setSortingEnabled(True)
        
        # 设置列宽
        self.logs_table.setColumnWidth(0, 180)  # 时间
        self.logs_table.setColumnWidth(1, 80)   # 级别
        self.logs_table.setColumnWidth(2, 120)  # 组件
        
        layout.addWidget(self.logs_table)
        
        # 添加到选项卡
        self.tab_widget.addTab(logs_tab, "日志查看")
        
        # 加载日志
        self._load_logs()
    
    def _load_logs(self):
        """加载日志文件"""
        try:
            app_data_dir = get_app_data_dir()
            log_path = os.path.join(app_data_dir, 'logs/win-task.log')
            
            if not os.path.exists(log_path):
                self.logs_table.setRowCount(0)
                QMessageBox.warning(self, "错误", "日志文件不存在")
                return
            
            # 清空表格
            self.logs_table.setRowCount(0)
            
            # 尝试不同的编码读取日志文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936']
            log_lines = []
            
            for encoding in encodings:
                try:
                    with open(log_path, 'r', encoding=encoding) as f:
                        log_lines = f.readlines()
                    break  # 如果成功读取，跳出循环
                except UnicodeDecodeError:
                    continue  # 如果解码错误，尝试下一种编码
            
            if not log_lines:
                # 如果所有编码都失败，使用二进制模式读取并使用errors='replace'
                with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_lines = f.readlines()
            
            # 解析日志行
            for line in log_lines:
                try:
                    # 解析日志行: 2025-07-11 13:46:06,472 - executor - INFO - 任务 11 [46ff1a72-5fac-48b3-af9a-6e5435cbf1df] 执行完成，耗时: 1.74秒
                    parts = line.strip().split(' - ', 3)
                    if len(parts) < 4:
                        continue
                    
                    timestamp = parts[0]
                    component = parts[1]
                    level = parts[2]
                    message = parts[3]
                    
                    # 添加到表格
                    row = self.logs_table.rowCount()
                    self.logs_table.insertRow(row)
                    
                    # 时间
                    self.logs_table.setItem(row, 0, QTableWidgetItem(timestamp))
                    
                    # 级别
                    level_item = QTableWidgetItem(level)
                    if "ERROR" in level:
                        level_item.setBackground(QColor(255, 200, 200))  # 浅红色
                    elif "WARNING" in level:
                        level_item.setBackground(QColor(255, 255, 200))  # 浅黄色
                    elif "INFO" in level:
                        level_item.setBackground(QColor(200, 255, 200))  # 浅绿色
                    self.logs_table.setItem(row, 1, level_item)
                    
                    # 组件
                    self.logs_table.setItem(row, 2, QTableWidgetItem(component))
                    
                    # 消息
                    self.logs_table.setItem(row, 3, QTableWidgetItem(message))
                except Exception as e:
                    self.logger.error(f"解析日志行失败: {str(e)}")
            
            # 应用过滤器
            self._filter_logs()
            
            # 滚动到底部
            self.logs_table.scrollToBottom()
            
        except Exception as e:
            self.logger.error(f"加载日志失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"加载日志失败: {str(e)}")
    
    def _filter_logs(self):
        """根据选择的过滤条件过滤日志"""
        level = self.log_level_combo.currentText()
        component = self.log_component_combo.currentText()
        search_text = self.log_search_input.text().lower()
        
        # 遍历所有行
        for row in range(self.logs_table.rowCount()):
            show_row = True
            
            # 过滤级别
            if level != "全部":
                row_level = self.logs_table.item(row, 1).text()
                if level not in row_level:
                    show_row = False
            
            # 过滤组件
            if component != "全部" and show_row:
                row_component = self.logs_table.item(row, 2).text()
                if component not in row_component:
                    show_row = False
            
            # 过滤搜索文本
            if search_text and show_row:
                found = False
                for col in range(self.logs_table.columnCount()):
                    item = self.logs_table.item(row, col)
                    if item and search_text in item.text().lower():
                        found = True
                        break
                if not found:
                    show_row = False
            
            # 显示或隐藏行
            self.logs_table.setRowHidden(row, not show_row)
    
    def _clear_logs(self):
        """清空日志文件"""
        reply = QMessageBox.question(self, "确认", "确定要清空日志文件吗？此操作不可恢复。",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                app_data_dir = get_app_data_dir()
                log_path = os.path.join(app_data_dir, 'logs/win-task.log')
                
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("")
                
                self.logs_table.setRowCount(0)
                QMessageBox.information(self, "成功", "日志文件已清空")
            except Exception as e:
                self.logger.error(f"清空日志失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"清空日志失败: {str(e)}")
    
    def _create_dashboard_tab(self):
        """创建仪表盘选项卡"""
        dashboard_tab = QWidget()
        layout = QVBoxLayout(dashboard_tab)
        
        # 创建刷新按钮
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新仪表盘")
        refresh_btn.clicked.connect(self._update_dashboard)
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_btn)
        layout.addLayout(refresh_layout)
        
        # 创建统计卡片布局
        cards_layout = QHBoxLayout()
        
        # 总任务数卡片
        total_tasks_card = QGroupBox("总任务数")
        total_tasks_layout = QVBoxLayout(total_tasks_card)
        self.total_tasks_label = QLabel("0")
        self.total_tasks_label.setAlignment(Qt.AlignCenter)
        self.total_tasks_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        total_tasks_layout.addWidget(self.total_tasks_label)
        cards_layout.addWidget(total_tasks_card)
        
        # 运行中任务卡片
        running_tasks_card = QGroupBox("运行中")
        running_tasks_layout = QVBoxLayout(running_tasks_card)
        self.running_tasks_label = QLabel("0")
        self.running_tasks_label.setAlignment(Qt.AlignCenter)
        self.running_tasks_label.setStyleSheet("font-size: 24px; font-weight: bold; color: blue;")
        running_tasks_layout.addWidget(self.running_tasks_label)
        cards_layout.addWidget(running_tasks_card)
        
        # 成功任务卡片
        success_tasks_card = QGroupBox("成功")
        success_tasks_layout = QVBoxLayout(success_tasks_card)
        self.success_tasks_label = QLabel("0")
        self.success_tasks_label.setAlignment(Qt.AlignCenter)
        self.success_tasks_label.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")
        success_tasks_layout.addWidget(self.success_tasks_label)
        cards_layout.addWidget(success_tasks_card)
        
        # 失败任务卡片
        failed_tasks_card = QGroupBox("失败")
        failed_tasks_layout = QVBoxLayout(failed_tasks_card)
        self.failed_tasks_label = QLabel("0")
        self.failed_tasks_label.setAlignment(Qt.AlignCenter)
        self.failed_tasks_label.setStyleSheet("font-size: 24px; font-weight: bold; color: red;")
        failed_tasks_layout.addWidget(self.failed_tasks_label)
        cards_layout.addWidget(failed_tasks_card)
        
        layout.addLayout(cards_layout)
        
        # 创建图表区域
        charts_layout = QHBoxLayout()
        
        # 任务类型分布图表
        task_types_group = QGroupBox("任务类型分布")
        task_types_layout = QVBoxLayout(task_types_group)
        
        # 创建任务类型表格
        self.task_types_table = QTableWidget()
        self.task_types_table.setColumnCount(2)
        self.task_types_table.setHorizontalHeaderLabels(["任务类型", "数量"])
        self.task_types_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_types_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        task_types_layout.addWidget(self.task_types_table)
        
        charts_layout.addWidget(task_types_group)
        
        # 任务状态分布图表
        task_status_group = QGroupBox("任务状态分布")
        task_status_layout = QVBoxLayout(task_status_group)
        
        # 创建任务状态表格
        self.task_status_table = QTableWidget()
        self.task_status_table.setColumnCount(2)
        self.task_status_table.setHorizontalHeaderLabels(["状态", "数量"])
        self.task_status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_status_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        task_status_layout.addWidget(self.task_status_table)
        
        charts_layout.addWidget(task_status_group)
        
        layout.addLayout(charts_layout)
        
        # 最近执行任务表格
        recent_group = QGroupBox("最近执行的任务")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_tasks_table = QTableWidget()
        self.recent_tasks_table.setColumnCount(5)
        self.recent_tasks_table.setHorizontalHeaderLabels(["ID", "名称", "执行时间", "状态", "耗时(秒)"])
        self.recent_tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.recent_tasks_table.horizontalHeader().setStretchLastSection(True)
        self.recent_tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent_tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 设置列宽
        self.recent_tasks_table.setColumnWidth(0, 80)   # ID
        self.recent_tasks_table.setColumnWidth(1, 150)  # 名称
        self.recent_tasks_table.setColumnWidth(2, 150)  # 执行时间
        self.recent_tasks_table.setColumnWidth(3, 80)   # 状态
        
        recent_layout.addWidget(self.recent_tasks_table)
        
        layout.addWidget(recent_group)
        
        # 添加到选项卡
        self.tab_widget.addTab(dashboard_tab, "仪表盘")
        
        # 初始化仪表盘数据
        self._update_dashboard()
    
    def _update_dashboard(self):
        """更新仪表盘数据"""
        try:
            # 获取所有任务
            tasks = self.scheduler.get_all_tasks()
            
            # 更新总任务数
            total_tasks = len(tasks)
            self.total_tasks_label.setText(str(total_tasks))
            
            # 统计任务状态
            running_tasks = 0
            success_tasks = 0
            failed_tasks = 0
            
            # 任务类型统计
            task_types = {}
            
            # 任务状态统计
            task_status = {}
            
            # 最近执行的任务
            recent_tasks = []
            
            for task in tasks:
                # 统计任务状态
                if task.status == TaskStatus.RUNNING:
                    running_tasks += 1
                elif task.status == TaskStatus.SUCCESS:
                    success_tasks += 1
                elif task.status == TaskStatus.FAILED:
                    failed_tasks += 1
                
                # 统计任务类型
                task_type = task.__class__.__name__
                if task_type in task_types:
                    task_types[task_type] += 1
                else:
                    task_types[task_type] = 1
                
                # 统计任务状态
                status = task.status.value
                if status in task_status:
                    task_status[status] += 1
                else:
                    task_status[status] = 1
                
                # 收集最近执行的任务
                if task.history and len(task.history) > 0:
                    for history in task.history:
                        recent_tasks.append((task, history))
            
            # 更新状态卡片
            self.running_tasks_label.setText(str(running_tasks))
            self.success_tasks_label.setText(str(success_tasks))
            self.failed_tasks_label.setText(str(failed_tasks))
            
            # 更新任务类型表格
            self.task_types_table.setRowCount(0)
            for task_type, count in task_types.items():
                row = self.task_types_table.rowCount()
                self.task_types_table.insertRow(row)
                self.task_types_table.setItem(row, 0, QTableWidgetItem(task_type))
                self.task_types_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            # 更新任务状态表格
            self.task_status_table.setRowCount(0)
            for status, count in task_status.items():
                row = self.task_status_table.rowCount()
                self.task_status_table.insertRow(row)
                self.task_status_table.setItem(row, 0, QTableWidgetItem(status))
                self.task_status_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            # 按执行时间排序最近执行的任务
            recent_tasks.sort(key=lambda x: x[1]['time'] if isinstance(x[1]['time'], datetime) else datetime.min, reverse=True)
            
            # 更新最近执行任务表格
            self.recent_tasks_table.setRowCount(0)
            for i, (task, history) in enumerate(recent_tasks[:10]):  # 只显示最近10条
                row = self.recent_tasks_table.rowCount()
                self.recent_tasks_table.insertRow(row)
                
                # ID
                item = QTableWidgetItem(task.id[:8])
                item.setToolTip(task.id)
                self.recent_tasks_table.setItem(row, 0, item)
                
                # 名称
                self.recent_tasks_table.setItem(row, 1, QTableWidgetItem(task.name))
                
                # 执行时间
                exec_time = history['time']
                time_str = exec_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(exec_time, datetime) else str(exec_time)
                self.recent_tasks_table.setItem(row, 2, QTableWidgetItem(time_str))
                
                # 状态
                status_item = QTableWidgetItem(history['status'])
                if history['status'] == TaskStatus.SUCCESS.value:
                    status_item.setBackground(QColor(200, 255, 200))  # 浅绿色
                elif history['status'] == TaskStatus.FAILED.value:
                    status_item.setBackground(QColor(255, 200, 200))  # 浅红色
                elif history['status'] == TaskStatus.RUNNING.value:
                    status_item.setBackground(QColor(200, 200, 255))  # 浅蓝色
                self.recent_tasks_table.setItem(row, 3, status_item)
                
                # 耗时
                self.recent_tasks_table.setItem(row, 4, QTableWidgetItem(f"{history['execution_time']:.2f}"))
            
        except Exception as e:
            self.logger.error(f"更新仪表盘失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"更新仪表盘失败: {str(e)}")
    
    def _create_settings_tab(self):
        """创建设置选项卡"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # 创建选项卡部件
        settings_tabs = QTabWidget()
        layout.addWidget(settings_tabs)
        
        # 常规设置
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        # 自启动设置
        self.auto_start_check = QCheckBox("程序启动时自动运行任务调度器")
        self.auto_start_check.setChecked(self.settings.auto_start)
        general_layout.addRow("自启动:", self.auto_start_check)
        
        # 最小化到托盘设置
        self.minimize_tray_check = QCheckBox("关闭窗口时最小化到系统托盘")
        self.minimize_tray_check.setChecked(self.settings.minimize_to_tray)
        general_layout.addRow("最小化到托盘:", self.minimize_tray_check)
        
        # 主题设置
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色"])
        self.theme_combo.setCurrentIndex(0 if self.settings.theme == "light" else 1)
        general_layout.addRow("主题:", self.theme_combo)
        
        settings_tabs.addTab(general_tab, "常规")
        
        # 调度器设置
        scheduler_tab = QWidget()
        scheduler_layout = QFormLayout(scheduler_tab)
        
        # 检查间隔
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 3600)
        self.check_interval_spin.setValue(self.settings.get('Scheduler', 'check_interval', 10, int))
        self.check_interval_spin.setSuffix(" 秒")
        scheduler_layout.addRow("检查间隔:", self.check_interval_spin)
        
        # 默认超时时间
        self.default_timeout_spin = QSpinBox()
        self.default_timeout_spin.setRange(0, 86400)
        self.default_timeout_spin.setValue(self.settings.get('Scheduler', 'default_timeout', 3600, int))
        self.default_timeout_spin.setSuffix(" 秒")
        scheduler_layout.addRow("默认超时时间:", self.default_timeout_spin)
        
        # 最大并发任务数
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 20)
        self.max_concurrent_spin.setValue(self.settings.get('Scheduler', 'max_concurrent_tasks', 5, int))
        scheduler_layout.addRow("最大并发任务数:", self.max_concurrent_spin)
        
        # 最大重试次数
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(self.settings.get('Scheduler', 'max_retries', 3, int))
        scheduler_layout.addRow("最大重试次数:", self.max_retries_spin)
        
        # 重试间隔
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setRange(1, 3600)
        self.retry_interval_spin.setValue(self.settings.get('Scheduler', 'retry_interval', 60, int))
        self.retry_interval_spin.setSuffix(" 秒")
        scheduler_layout.addRow("重试间隔:", self.retry_interval_spin)
        
        settings_tabs.addTab(scheduler_tab, "调度器")
        
        # 日志设置
        logging_tab = QWidget()
        logging_layout = QFormLayout(logging_tab)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        current_level = self.settings.get('Logging', 'level', 'INFO')
        level_index = self.log_level_combo.findText(current_level)
        self.log_level_combo.setCurrentIndex(level_index if level_index >= 0 else 1)
        logging_layout.addRow("日志级别:", self.log_level_combo)
        
        # 日志保留天数
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setValue(self.settings.get('Logging', 'retention_days', 30, int))
        self.log_retention_spin.setSuffix(" 天")
        logging_layout.addRow("日志保留天数:", self.log_retention_spin)
        
        # 详细日志
        self.verbose_log_check = QCheckBox("记录详细日志")
        self.verbose_log_check.setChecked(self.settings.get('Logging', 'verbose', True, bool))
        logging_layout.addRow("详细日志:", self.verbose_log_check)
        
        settings_tabs.addTab(logging_tab, "日志")
        
        # 通知设置
        notification_tab = QWidget()
        notification_layout = QFormLayout(notification_tab)
        
        # 启用通知
        self.notification_check = QCheckBox("启用任务通知")
        self.notification_check.setChecked(self.settings.get('Notification', 'enable', True, bool))
        notification_layout.addRow("通知:", self.notification_check)
        
        # 通知类型
        self.notification_type_combo = QComboBox()
        self.notification_type_combo.addItems(["桌面通知", "邮件通知"])
        current_type = self.settings.get('Notification', 'type', 'desktop')
        self.notification_type_combo.setCurrentIndex(0 if current_type == 'desktop' else 1)
        notification_layout.addRow("通知类型:", self.notification_type_combo)
        
        # 邮件设置
        self.email_group = QGroupBox("邮件设置")
        email_layout = QFormLayout(self.email_group)
        
        self.smtp_server = QLineEdit(self.settings.get('Notification', 'smtp_server', ''))
        email_layout.addRow("SMTP服务器:", self.smtp_server)
        
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(self.settings.get('Notification', 'smtp_port', 587, int))
        email_layout.addRow("SMTP端口:", self.smtp_port)
        
        self.smtp_user = QLineEdit(self.settings.get('Notification', 'smtp_user', ''))
        email_layout.addRow("SMTP用户名:", self.smtp_user)
        
        self.smtp_password = QLineEdit(self.settings.get('Notification', 'smtp_password', ''))
        self.smtp_password.setEchoMode(QLineEdit.Password)
        email_layout.addRow("SMTP密码:", self.smtp_password)
        
        self.email_recipient = QLineEdit(self.settings.get('Notification', 'email_recipient', ''))
        email_layout.addRow("收件人:", self.email_recipient)
        
        self.email_subject_prefix = QLineEdit(self.settings.get('Notification', 'email_subject_prefix', '[Win-Task]'))
        email_layout.addRow("邮件主题前缀:", self.email_subject_prefix)
        
        notification_layout.addRow("", self.email_group)
        
        # 连接通知类型变更事件
        self.notification_type_combo.currentIndexChanged.connect(self._on_notification_type_changed)
        self._on_notification_type_changed()  # 初始化状态
        
        settings_tabs.addTab(notification_tab, "通知")
        
        # 安全设置
        security_tab = QWidget()
        security_layout = QFormLayout(security_tab)
        
        # 加密敏感数据
        self.encrypt_check = QCheckBox("加密敏感数据")
        self.encrypt_check.setChecked(self.settings.get('Security', 'encrypt_sensitive_data', True, bool))
        security_layout.addRow("数据加密:", self.encrypt_check)
        
        # 备份频率
        self.backup_freq_spin = QSpinBox()
        self.backup_freq_spin.setRange(1, 30)
        self.backup_freq_spin.setValue(self.settings.get('Security', 'backup_frequency', 7, int))
        self.backup_freq_spin.setSuffix(" 天")
        security_layout.addRow("备份频率:", self.backup_freq_spin)
        
        # 最大备份数
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 100)
        self.max_backups_spin.setValue(self.settings.get('Security', 'max_backups', 10, int))
        security_layout.addRow("最大备份数:", self.max_backups_spin)
        
        settings_tabs.addTab(security_tab, "安全")
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置设置")
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        
        # 添加到选项卡
        self.tab_widget.addTab(settings_tab, "设置")
    
    def _on_notification_type_changed(self):
        """通知类型变更处理函数"""
        is_email = self.notification_type_combo.currentIndex() == 1
        self.email_group.setEnabled(is_email)
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 常规设置
            self.settings.auto_start = self.auto_start_check.isChecked()
            self.settings.minimize_to_tray = self.minimize_tray_check.isChecked()
            self.settings.theme = "light" if self.theme_combo.currentIndex() == 0 else "dark"
            
            # 调度器设置
            self.settings.set('Scheduler', 'check_interval', self.check_interval_spin.value())
            self.settings.set('Scheduler', 'default_timeout', self.default_timeout_spin.value())
            self.settings.set('Scheduler', 'max_concurrent_tasks', self.max_concurrent_spin.value())
            self.settings.set('Scheduler', 'max_retries', self.max_retries_spin.value())
            self.settings.set('Scheduler', 'retry_interval', self.retry_interval_spin.value())
            
            # 日志设置
            self.settings.set('Logging', 'level', self.log_level_combo.currentText())
            self.settings.set('Logging', 'retention_days', self.log_retention_spin.value())
            self.settings.set('Logging', 'verbose', self.verbose_log_check.isChecked())
            
            # 通知设置
            self.settings.set('Notification', 'enable', self.notification_check.isChecked())
            self.settings.set('Notification', 'type', 'desktop' if self.notification_type_combo.currentIndex() == 0 else 'email')
            self.settings.set('Notification', 'smtp_server', self.smtp_server.text())
            self.settings.set('Notification', 'smtp_port', self.smtp_port.value())
            self.settings.set('Notification', 'smtp_user', self.smtp_user.text())
            self.settings.set('Notification', 'smtp_password', self.smtp_password.text())
            self.settings.set('Notification', 'email_recipient', self.email_recipient.text())
            self.settings.set('Notification', 'email_subject_prefix', self.email_subject_prefix.text())
            
            # 安全设置
            self.settings.set('Security', 'encrypt_sensitive_data', self.encrypt_check.isChecked())
            self.settings.set('Security', 'backup_frequency', self.backup_freq_spin.value())
            self.settings.set('Security', 'max_backups', self.max_backups_spin.value())
            
            QMessageBox.information(self, "成功", "设置已保存")
            
            # 提示需要重启应用以应用某些设置
            QMessageBox.information(self, "提示", "某些设置需要重启应用程序才能生效")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {str(e)}")
            QMessageBox.warning(self, "错误", f"保存设置失败: {str(e)}")
    
    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(self, "确认", "确定要重置所有设置为默认值吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 创建默认配置
                self.settings._create_default_config()
                
                # 重新加载设置选项卡
                index = self.tab_widget.indexOf(self.tab_widget.currentWidget())
                self.tab_widget.removeTab(index)
                self._create_settings_tab()
                self.tab_widget.setCurrentIndex(index)
                
                QMessageBox.information(self, "成功", "设置已重置为默认值")
                
            except Exception as e:
                self.logger.error(f"重置设置失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"重置设置失败: {str(e)}")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        # 导入/导出
        import_action = QAction("导入任务", self)
        import_action.triggered.connect(self.import_tasks)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出任务", self)
        export_action.triggered.connect(self.export_tasks)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction(QIcon.fromTheme("application-exit"), "退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = self.menuBar().addMenu("视图")
        
        # 刷新
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.update_tasks_view)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # 显示/隐藏工具栏
        toggle_toolbar_action = QAction("显示工具栏", self)
        toggle_toolbar_action.setCheckable(True)
        toggle_toolbar_action.setChecked(True)
        toggle_toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toggle_toolbar_action)
        
        # 显示/隐藏状态栏
        toggle_statusbar_action = QAction("显示状态栏", self)
        toggle_statusbar_action.setCheckable(True)
        toggle_statusbar_action.setChecked(True)
        toggle_statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(toggle_statusbar_action)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """创建工具栏"""
        # 主工具栏
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # 新建任务
        new_task_action = QAction(QIcon.fromTheme("document-new"), "新建任务", self)
        new_task_action.triggered.connect(self.add_task)
        self.toolbar.addAction(new_task_action)
        
        # 运行任务
        run_task_action = QAction(QIcon.fromTheme("media-playback-start"), "立即运行", self)
        run_task_action.triggered.connect(self.run_task)
        self.toolbar.addAction(run_task_action)
        
        # 编辑任务
        edit_task_action = QAction(QIcon.fromTheme("document-edit"), "编辑任务", self)
        edit_task_action.triggered.connect(self.edit_task)
        self.toolbar.addAction(edit_task_action)
        
        # 删除任务
        delete_task_action = QAction(QIcon.fromTheme("edit-delete"), "删除任务", self)
        delete_task_action.triggered.connect(self.delete_task)
        self.toolbar.addAction(delete_task_action)
        
        # 刷新任务
        refresh_task_action = QAction(QIcon.fromTheme("view-refresh"), "刷新", self)
        refresh_task_action.triggered.connect(self.update_tasks_view)
        self.toolbar.addAction(refresh_task_action)
        
        # 启用/禁用任务
        toggle_task_action = QAction(QIcon.fromTheme("dialog-ok-apply"), "启用/禁用", self)
        toggle_task_action.triggered.connect(self.toggle_task)
        self.toolbar.addAction(toggle_task_action)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)
        
        # 任务统计标签
        self.task_stats_label = QLabel()
        self.statusbar.addPermanentWidget(self.task_stats_label)
        
        # 更新任务统计
        self._update_task_stats()
    
    def _create_system_tray(self):
        """创建系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("系统托盘不可用")
            return
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("Win-Task - Windows 定时任务管理系统")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏窗口
        show_action = QAction("显示/隐藏窗口", self)
        show_action.triggered.connect(self._toggle_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        # 设置菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击显示窗口
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def _tray_icon_activated(self, reason):
        """
        托盘图标被激活的处理函数
        
        参数:
            reason (QSystemTrayIcon.ActivationReason): 激活原因
        """
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def update_tasks_view(self):
        """更新任务视图"""
        try:
            # 记录当前选中的任务ID列表
            selected_ids = []
            for idx in self.tasks_table.selectionModel().selectedRows():
                item = self.tasks_table.item(idx.row(), 0)
                if item:
                    selected_ids.append(item.toolTip())
            
            # 获取所有任务
            tasks = self.scheduler.get_all_tasks()
            
            # 清空表格
            self.tasks_table.setRowCount(0)
            
            # 填充表格
            for i, task in enumerate(tasks):
                self.tasks_table.insertRow(i)
                
                # ID
                item = QTableWidgetItem(task.id[:8])
                item.setToolTip(task.id)
                self.tasks_table.setItem(i, 0, item)
                
                # 名称
                self.tasks_table.setItem(i, 1, QTableWidgetItem(task.name))
                
                # 状态
                status_item = QTableWidgetItem(task.status.value)
                # 根据状态设置颜色
                if task.status == TaskStatus.SUCCESS:
                    status_item.setBackground(QColor(200, 255, 200))  # 浅绿色
                elif task.status == TaskStatus.FAILED:
                    status_item.setBackground(QColor(255, 200, 200))  # 浅红色
                elif task.status == TaskStatus.RUNNING:
                    status_item.setBackground(QColor(200, 200, 255))  # 浅蓝色
                self.tasks_table.setItem(i, 2, status_item)
                
                # 类型
                self.tasks_table.setItem(i, 3, QTableWidgetItem(task.__class__.__name__))
                
                # 计划
                schedule = task.schedule if task.schedule else "手动运行"
                self.tasks_table.setItem(i, 4, QTableWidgetItem(schedule))
                
                # 上次运行
                last_run = task.last_run.strftime("%Y-%m-%d %H:%M:%S") if task.last_run else "从未运行"
                self.tasks_table.setItem(i, 5, QTableWidgetItem(last_run))
                
                # 下次运行
                next_run = task.next_run.strftime("%Y-%m-%d %H:%M:%S") if task.next_run else "未调度"
                self.tasks_table.setItem(i, 6, QTableWidgetItem(next_run))
                
                # 描述
                self.tasks_table.setItem(i, 7, QTableWidgetItem(task.description))
            
            # 恢复选中行
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, 0)
                if item and item.toolTip() in selected_ids:
                    self.tasks_table.selectRow(row)
            
            # 更新任务统计
            self._update_task_stats()
            
            # 更新状态栏
            self.status_label.setText(f"上次更新: {datetime.now().strftime('%H:%M:%S')}")
        
        except Exception as e:
            self.logger.exception("更新任务视图失败")
            self.status_label.setText(f"更新失败: {str(e)}")
    
    def _update_task_stats(self):
        """更新任务统计信息"""
        # 获取所有任务
        tasks = self.scheduler.get_all_tasks()
        
        # 统计不同状态的任务数量
        total = len(tasks)
        running = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        success = len([t for t in tasks if t.status == TaskStatus.SUCCESS])
        failed = len([t for t in tasks if t.status == TaskStatus.FAILED])
        
        # 更新统计标签
        self.task_stats_label.setText(
            f"总计: {total} | 运行中: {running} | 成功: {success} | 失败: {failed}"
        )
    
    def add_task(self):
        """添加新任务"""
        self.status_label.setText("正在创建新任务...")
        
        # 这里应该显示任务创建对话框
        task_dialog = TaskDialog(self.scheduler, parent=self)
        if task_dialog.exec_():
            self.update_tasks_view()
            self.status_label.setText("新任务已创建")
    
    def edit_task(self):
        """编辑选中的任务"""
        # 获取选中的行
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        # 获取任务ID
        row = selected_rows[0].row()
        task_id_item = self.tasks_table.item(row, 0)
        task_id = task_id_item.toolTip()  # 完整ID存储在工具提示中
        
        # 获取任务对象
        task = self.scheduler.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "警告", f"找不到任务: {task_id}")
            return
        
        self.status_label.setText(f"正在编辑任务: {task.name}")
        
        # 显示任务编辑对话框
        task_dialog = TaskDialog(self.scheduler, task, parent=self)
        if task_dialog.exec_():
            self.update_tasks_view()
            self.status_label.setText(f"任务已更新: {task.name}")
    
    def delete_task(self):
        """删除选中的任务"""
        # 获取选中的行
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        # 确认删除
        ret = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 个任务吗？",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if ret == QMessageBox.No:
            return
        
        # 执行删除操作
        deleted_count = 0
        for row_idx in sorted([idx.row() for idx in selected_rows], reverse=True):
            task_id_item = self.tasks_table.item(row_idx, 0)
            task_id = task_id_item.toolTip()
            
            if self.scheduler.remove_task(task_id):
                deleted_count += 1
        
        # 更新视图
        self.update_tasks_view()
        self.status_label.setText(f"已删除 {deleted_count} 个任务")
    
    def run_task(self):
        """立即运行选中的任务"""
        # 获取选中的行
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        # 获取任务ID
        row = selected_rows[0].row()
        task_id_item = self.tasks_table.item(row, 0)
        task_id = task_id_item.toolTip()
        
        # 获取任务对象
        task = self.scheduler.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "警告", f"找不到任务: {task_id}")
            return
        
        self.status_label.setText(f"正在运行任务: {task.name}")
        
        # 创建进度对话框
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog(f"正在执行任务: {task.name}", "取消", 0, 0, self)
        progress.setWindowTitle("任务执行中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.setAutoClose(True)
        progress.setCancelButton(None)  # 禁用取消按钮，因为我们不能中断任务执行
        
        # 在后台线程中执行任务
        self.task_thread = TaskExecutionThread(self.scheduler, task_id)
        self.task_thread.taskFinished.connect(lambda result: self._handle_task_result(task_id, result))
        self.task_thread.taskError.connect(self._handle_task_error)
        self.task_thread.taskFinished.connect(progress.close)
        self.task_thread.start()
        
        # 显示进度对话框
        progress.exec_()
    
    @pyqtSlot(str)
    def _handle_task_error(self, error_msg):
        """处理任务执行错误"""
        self.logger.error(f"任务执行错误: {error_msg}")
        self.status_label.setText(f"任务执行错误: {error_msg}")
        QMessageBox.critical(self, "任务执行错误", f"执行任务时发生错误:\n{error_msg}")
    
    @pyqtSlot(str, object)
    def _handle_task_result(self, task_id, result):
        """处理任务执行结果（在主线程中调用）"""
        task = self.scheduler.get_task(task_id)
        if not task:
            return
            
        if result:
            status_text = "成功" if result.is_successful else "失败"
            self.status_label.setText(f"任务执行{status_text}: {task.name}")
            
            # 更新视图
            self.update_tasks_view()
        else:
            self.status_label.setText(f"任务执行失败: {task.name}")
    
    def toggle_task(self):
        """启用或禁用选中的任务"""
        # 获取选中的行
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择一个任务")
            return
        
        # 获取任务ID
        row = selected_rows[0].row()
        task_id_item = self.tasks_table.item(row, 0)
        task_id = task_id_item.toolTip()
        
        # 获取任务对象
        task = self.scheduler.get_task(task_id)
        if not task:
            QMessageBox.warning(self, "警告", f"找不到任务: {task_id}")
            return
        
        # 切换启用状态
        if task.enabled:
            self.scheduler.pause_task(task_id)
            self.status_label.setText(f"已禁用任务: {task.name}")
        else:
            self.scheduler.resume_task(task_id)
            self.status_label.setText(f"已启用任务: {task.name}")
        
        # 更新视图
        self.update_tasks_view()
    
    def import_tasks(self):
        """导入任务"""
        self.status_label.setText("导入任务功能尚未实现")
    
    def export_tasks(self):
        """导出任务"""
        self.status_label.setText("导出任务功能尚未实现")
    
    def backup_tasks(self):
        """手动备份任务"""
        try:
            backup_dir = self.scheduler.backup_tasks()
            if backup_dir:
                QMessageBox.information(
                    self, 
                    "备份成功", 
                    f"成功备份任务到:\n{backup_dir}"
                )
            else:
                QMessageBox.warning(self, "备份失败", "任务备份失败，请查看日志了解详情")
        except Exception as e:
            self.logger.error(f"手动备份任务失败: {str(e)}")
            QMessageBox.critical(self, "备份失败", f"任务备份失败: {str(e)}")
    
    def restore_tasks(self):
        """从备份恢复任务"""
        try:
            # 获取备份目录列表
            app_data_dir = get_app_data_dir()
            backup_dir = os.path.join(app_data_dir, 'backups/tasks')
            
            if not os.path.exists(backup_dir):
                QMessageBox.warning(self, "恢复失败", "没有找到备份目录")
                return
            
            backup_dirs = [d for d in os.listdir(backup_dir) 
                          if os.path.isdir(os.path.join(backup_dir, d))]
            
            if not backup_dirs:
                QMessageBox.warning(self, "恢复失败", "没有可用的备份")
                return
            
            # 按名称排序，最新的备份在前面
            backup_dirs.sort(reverse=True)
            
            # 创建备份选择对话框
            from PyQt5.QtWidgets import QInputDialog
            selected_backup, ok = QInputDialog.getItem(
                self,
                "选择备份",
                "请选择要恢复的备份:",
                backup_dirs,
                0,  # 默认选择最新的备份
                False
            )
            
            if not ok or not selected_backup:
                return
            
            # 确认恢复
            reply = QMessageBox.question(
                self,
                "确认恢复",
                f"确定要从备份 {selected_backup} 恢复任务吗？\n当前的任务将被覆盖！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 执行恢复
            selected_path = os.path.join(backup_dir, selected_backup)
            success = self.scheduler.restore_tasks_from_backup(selected_path)
            
            if success:
                QMessageBox.information(
                    self, 
                    "恢复成功", 
                    f"成功从备份 {selected_backup} 恢复任务"
                )
                # 刷新任务视图
                self.update_tasks_view()
            else:
                QMessageBox.warning(
                    self, 
                    "恢复失败", 
                    "从备份恢复任务失败，请查看日志了解详情"
                )
                
        except Exception as e:
            self.logger.error(f"从备份恢复任务失败: {str(e)}")
            QMessageBox.critical(self, "恢复失败", f"从备份恢复任务失败: {str(e)}")
    
    def toggle_toolbar(self, visible):
        """
        显示或隐藏工具栏
        
        参数:
            visible (bool): 是否可见
        """
        self.toolbar.setVisible(visible)
    
    def toggle_statusbar(self, visible):
        """
        显示或隐藏状态栏
        
        参数:
            visible (bool): 是否可见
        """
        self.statusbar.setVisible(visible)
    
    def filter_tasks(self, text):
        """
        根据文本过滤任务列表
        
        参数:
            text (str): 过滤文本
        """
        text = text.lower()
        
        for row in range(self.tasks_table.rowCount()):
            hidden = True
            for col in range(self.tasks_table.columnCount()):
                item = self.tasks_table.item(row, col)
                if item and text in item.text().lower():
                    hidden = False
                    break
            
            self.tasks_table.setRowHidden(row, hidden)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 Win-Task",
            "Win-Task - Windows 定时任务管理系统\n\n"
            "版本: 1.0.0\n"
            "Win-Task是一个功能强大的Windows定时任务管理工具，\n"
            "提供直观的图形界面，让用户轻松创建、管理和监控各种定时任务。\n\n"
            "© 2025 Win-Task Team. 保留所有权利。"
        )
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        
        参数:
            event: 关闭事件
        """
        if self.settings.minimize_to_tray and self.tray_icon:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Win-Task",
                "程序已最小化到系统托盘，双击图标可恢复窗口",
                QSystemTrayIcon.Information,
                3000
            )
        else:
            # 确保保存所有任务数据
            try:
                self.logger.info("程序关闭，保存任务数据...")
                self.scheduler.save_tasks()
                self.scheduler.backup_tasks()
            except Exception as e:
                self.logger.error(f"保存任务数据失败: {str(e)}")
                
            event.accept()
            QApplication.quit() 

    def _toggle_window(self):
        """切换窗口显示/隐藏状态"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow() 

    def _update_calendar(self):
        """更新日历视图"""
        try:
            # 获取所有任务
            tasks = self.scheduler.get_all_tasks()
            
            # 获取当前选中的日期
            selected_date = self.calendar.selectedDate().toPyDate()
            
            # 获取当前月份
            current_month = self.calendar.monthShown()
            current_year = self.calendar.yearShown()
            
            # 统计当月任务
            month_tasks = []
            month_completed = 0
            month_failed = 0
            month_pending = 0
            
            # 按日期分组任务
            date_tasks = {}
            
            for task in tasks:
                # 获取任务的执行时间
                last_run = task.last_run
                next_run = task.next_run
                
                # 如果有上次运行时间，添加到对应日期
                if last_run:
                    date_str = last_run.strftime("%Y-%m-%d")
                    if date_str not in date_tasks:
                        date_tasks[date_str] = []
                    date_tasks[date_str].append(task)
                    
                    # 检查是否为当月任务
                    if last_run.month == current_month and last_run.year == current_year:
                        month_tasks.append(task)
                        if task.status == TaskStatus.SUCCESS:
                            month_completed += 1
                        elif task.status == TaskStatus.FAILED:
                            month_failed += 1
                
                # 如果有下次运行时间，添加到对应日期
                if next_run:
                    date_str = next_run.strftime("%Y-%m-%d")
                    if date_str not in date_tasks:
                        date_tasks[date_str] = []
                    date_tasks[date_str].append(task)
                    
                    # 检查是否为当月任务
                    if next_run.month == current_month and next_run.year == current_year:
                        if task not in month_tasks:
                            month_tasks.append(task)
                            month_pending += 1
            
            # 更新当月任务统计
            self.month_total_tasks.setText(str(len(month_tasks)))
            self.month_completed_tasks.setText(str(month_completed))
            self.month_failed_tasks.setText(str(month_failed))
            self.month_pending_tasks.setText(str(month_pending))
            
            # 更新选中日期的任务列表
            self._on_date_selected()
            
        except Exception as e:
            self.logger.error(f"更新日历视图失败: {str(e)}")
    
    def _on_date_selected(self):
        """日期选择变更处理函数"""
        try:
            # 获取选中的日期
            date = self.calendar.selectedDate()
            date_str = date.toString("yyyy-MM-dd")
            
            # 更新日期标签
            self.selected_date_label.setText(f"选择的日期: {date_str}")
            
            # 获取所有任务
            tasks = self.scheduler.get_all_tasks()
            
            # 清空表格
            self.calendar_tasks_table.setRowCount(0)
            
            # 筛选当天的任务
            selected_date = date.toPyDate()
            day_tasks = []
            
            for task in tasks:
                # 检查上次运行时间
                if task.last_run and task.last_run.date() == selected_date:
                    day_tasks.append((task, task.last_run, "已执行"))
                
                # 检查下次运行时间
                if task.next_run and task.next_run.date() == selected_date:
                    day_tasks.append((task, task.next_run, "待执行"))
            
            # 按时间排序
            day_tasks.sort(key=lambda x: x[1])
            
            # 填充表格
            for task, run_time, run_type in day_tasks:
                row = self.calendar_tasks_table.rowCount()
                self.calendar_tasks_table.insertRow(row)
                
                # ID
                item = QTableWidgetItem(task.id[:8])
                item.setToolTip(task.id)
                self.calendar_tasks_table.setItem(row, 0, item)
                
                # 名称
                self.calendar_tasks_table.setItem(row, 1, QTableWidgetItem(task.name))
                
                # 时间
                time_str = run_time.strftime("%H:%M:%S")
                self.calendar_tasks_table.setItem(row, 2, QTableWidgetItem(f"{time_str} ({run_type})"))
                
                # 状态
                status_item = QTableWidgetItem(task.status.value)
                # 根据状态设置颜色
                if task.status == TaskStatus.SUCCESS:
                    status_item.setBackground(QColor(200, 255, 200))  # 浅绿色
                elif task.status == TaskStatus.FAILED:
                    status_item.setBackground(QColor(255, 200, 200))  # 浅红色
                elif task.status == TaskStatus.RUNNING:
                    status_item.setBackground(QColor(200, 200, 255))  # 浅蓝色
                self.calendar_tasks_table.setItem(row, 3, status_item)
                
                # 类型
                self.calendar_tasks_table.setItem(row, 4, QTableWidgetItem(task.__class__.__name__))
            
        except Exception as e:
            self.logger.error(f"更新日期任务列表失败: {str(e)}")
    
    def _add_task_on_date(self):
        """在选中日期添加任务"""
        # 获取选中的日期
        date = self.calendar.selectedDate()
        
        # 创建新任务，并设置初始日期
        self.add_task(date.toPyDate())
    
    def _view_all_tasks(self):
        """查看所有任务"""
        # 切换到任务管理选项卡
        self.tab_widget.setCurrentIndex(0) 

    def _auto_save_tasks(self):
        """自动保存任务数据"""
        try:
            self.scheduler.save_tasks()
            self.logger.debug("自动保存任务数据完成")
        except Exception as e:
            self.logger.error(f"自动保存任务数据失败: {str(e)}") 