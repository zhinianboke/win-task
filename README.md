# Windows 定时任务管理系统 (Win-Task)

<div align="center">

![Win-Task Logo](assets/icons/app_icon.png)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)

**一个功能强大、界面友好的 Windows 定时任务管理工具**

[功能特性](#核心功能) • [快速开始](#安装与使用) • [文档](#使用文档) • [贡献](#贡献指南) • [许可证](#许可证)

</div>

## 📖 项目简介

Win-Task 是一个专为 Windows 平台设计的现代化定时任务管理系统，采用 Python + PyQt5 开发。它提供直观的图形界面，让用户轻松创建、管理和监控各种定时任务，无需复杂的命令行操作。

### ✨ 主要特点

- 🎯 **简单易用** - 直观的图形界面，零学习成本
- 🔄 **功能强大** - 支持多种任务类型和调度方式
- 📊 **实时监控** - 任务执行状态实时跟踪
- 🔒 **安全可靠** - 数据加密存储，自动备份
- 🎨 **界面美观** - 现代化UI设计，支持主题切换
- 📱 **系统集成** - 系统托盘运行，开机自启动

## 🚀 核心功能

### 📅 任务调度与管理
- **🕐 灵活的时间设置** - 支持一次性任务、周期性任务(每小时、每天、每周、每月、自定义间隔)
- **⚙️ Cron 表达式支持** - 高级用户可使用 Cron 表达式灵活配置复杂的执行计划
- **📁 任务分组管理** - 将相关任务组织到不同的分组中，便于分类管理
- **🔝 任务优先级** - 设置任务的重要程度和执行优先级
- **🔗 任务依赖关系** - 设置任务间的依赖关系，确保按正确顺序执行
- **📦 一键打包** - 支持打包成独立的exe文件，无需安装Python环境

### 🎯 多样化任务类型
- **🌐 HTTP请求任务** - 支持 GET、POST、PUT、DELETE 等方法，可配置请求头和请求体
- **💻 程序执行任务** - 运行可执行文件、批处理脚本或 PowerShell 命令
- **📂 文件操作任务** - 定时备份、复制、移动、删除文件和文件夹
- **🖥️ 系统操作任务** - 关机、重启、休眠、锁定等系统控制命令
- **🗄️ 数据库操作任务** - 执行 SQL 查询、数据库备份和恢复操作

### 🎨 用户友好的界面
- **✨ 现代化 UI 设计** - 美观直观的用户界面，支持浅色/深色主题切换
- **🖱️ 拖拽操作** - 通过拖拽轻松安排和调整任务执行顺序
- **📆 日历视图** - 直观查看任务计划安排和执行历史
- **🔔 系统托盘集成** - 最小化到系统托盘后台运行，不干扰正常工作
- **🔍 快速搜索** - 支持按名称、类型、状态等条件快速定位任务
- **📊 自定义仪表盘** - 根据个人需求定制监控视图和统计图表

### 📈 任务监控与日志
- **⚡ 实时状态监控** - 查看任务的运行状态、进度和执行结果
- **📋 执行历史记录** - 完整记录所有任务的历史执行情况
- **📝 详细日志系统** - 提供任务执行的详细日志记录和错误信息
- **📊 性能统计分析** - 任务执行时间、成功率、失败原因等统计信息
- **📈 图表可视化** - 以图表形式直观展示任务执行趋势和状态分布

### 🔔 智能通知系统
- **📧 多渠道通知** - 支持邮件、桌面通知等多种通知方式
- **⚙️ 自定义触发条件** - 灵活设置通知触发条件（成功、失败、超时等）
- **📝 通知模板** - 自定义通知内容格式和样式
- **🏷️ 通知分级** - 根据任务重要性设置不同级别的通知策略

### 🔒 数据安全与备份
- **📤 配置导入导出** - 方便在不同环境间迁移和同步任务配置
- **💾 自动备份机制** - 定期自动备份任务配置数据，防止数据丢失
- **🔐 敏感信息加密** - 对API密钥、密码等敏感信息进行加密存储
- **🛡️ 数据完整性校验** - 确保任务数据的完整性和一致性

### 🔧 高级功能特性
- **🔄 智能重试机制** - 任务失败后自动重试，支持自定义重试策略
- **⚖️ 并发控制** - 限制同时执行的任务数量，避免系统资源过载
- **⏱️ 超时控制** - 设置任务执行的最长时间，防止任务无限期运行
- **📊 资源监控** - 监控任务执行时的CPU、内存等系统资源使用情况
- **🔌 扩展支持** - 支持插件开发，可根据需要扩展新的任务类型

## 🏗️ 技术架构

Win-Task 采用现代化的 Python 技术栈构建，确保高性能和可扩展性：

### 核心技术栈
- **🖼️ PyQt5 5.15.9** - 跨平台桌面GUI应用框架，提供原生界面体验
- **⚡ APScheduler 3.10.4** - 高级Python任务调度库，支持多种调度方式和触发器
- **⏰ Croniter 2.0.1** - 强大的Cron表达式解析和计算库
- **🗃️ SQLAlchemy 2.0.20** - Python SQL工具包和ORM框架
- **📝 Loguru 0.7.0** - 现代化的日志记录库，提供结构化日志
- **📦 PyInstaller 5.13.0** - 将Python应用打包成独立可执行文件

### 支持库
- **🌐 Requests 2.31.0** - 优雅的HTTP请求库
- **🔒 Cryptography 41.0.3** - 现代加密库，保护敏感数据
- **🖥️ PyWin32 306** - Windows API访问库
- **📊 Psutil 5.9.5** - 系统和进程监控库
- **⚙️ Python-dotenv 1.0.0** - 环境变量管理

### 架构设计原则
- **🎯 模块化设计** - 清晰的模块分离，便于维护和扩展
- **🔌 插件化架构** - 支持动态加载任务类型和功能扩展
- **🛡️ 异常安全** - 完善的错误处理和恢复机制
- **⚡ 高性能** - 多线程任务执行，支持并发处理
- **🔄 可扩展性** - 易于添加新的任务类型和功能模块

## 📁 项目结构

```
win-task/
├── 📁 assets/                    # 🎨 资源文件目录
│   ├── 📁 icons/                 #   应用图标和界面图标
│   └── 📁 themes/                #   UI主题和样式文件
├── 📁 data/                      # 💾 数据存储目录（运行时创建）
│   ├── 📁 tasks/                 #   任务配置JSON文件
│   ├── 📁 logs/                  #   应用日志文件
│   └── 📁 backups/               #   配置备份文件
├── 📁 src/                       # 💻 源代码目录
│   ├── 📁 core/                  #   🔧 核心功能模块
│   │   ├── 📄 __init__.py        #     模块初始化
│   │   ├── 📄 executor.py        #     任务执行器
│   │   ├── 📄 logger.py          #     日志管理系统
│   │   ├── 📄 scheduler.py       #     任务调度器核心
│   │   ├── 📄 settings.py        #     配置管理器
│   │   ├── 📄 task.py            #     任务基类定义
│   │   └── 📄 task_execution_thread.py  # 任务执行线程
│   ├── 📁 tasks/                 #   🎯 具体任务类型实现
│   │   ├── 📄 __init__.py        #     任务模块初始化和注册
│   │   ├── 📄 db_task.py         #     数据库操作任务
│   │   ├── 📄 file_task.py       #     文件操作任务
│   │   ├── 📄 program_task.py    #     程序执行任务
│   │   ├── 📄 system_task.py     #     系统操作任务
│   │   └── 📄 url_task.py        #     HTTP请求任务
│   ├── 📁 ui/                    #   🖼️ 用户界面模块
│   │   ├── 📄 __init__.py        #     UI模块初始化
│   │   ├── 📄 main_window.py     #     主窗口界面
│   │   └── 📄 task_dialog.py     #     任务配置对话框
│   └── 📁 utils/                 #   🛠️ 工具函数模块
│       ├── 📄 __init__.py        #     工具模块初始化
│       ├── 📄 cron_parser.py     #     Cron表达式解析器
│       ├── 📄 notifier.py        #     通知服务管理
│       └── 📄 path_utils.py      #     路径工具函数
├── 📄 .gitignore                 # 🚫 Git忽略文件配置
├── 📄 build.py                   # 📦 应用打包构建脚本
├── 📄 config.ini                 # ⚙️ 应用配置文件模板
├── 📄 main.py                    # 🚀 程序主入口文件
├── 📄 README.md                  # 📖 项目说明文档
├── 📄 requirements.txt           # 📋 Python依赖库列表
└── 📄 setup.py                   # 📦 Python包安装配置
```

### 🗂️ 目录说明

- **`src/core/`** - 应用核心逻辑，包含任务调度、执行、配置管理等核心功能
- **`src/tasks/`** - 各种任务类型的具体实现，采用插件化设计，易于扩展
- **`src/ui/`** - PyQt5图形用户界面，包含主窗口和各种对话框
- **`src/utils/`** - 通用工具函数，如Cron解析、通知服务、路径处理等
- **`assets/`** - 静态资源文件，包含图标、主题等UI资源
- **`data/`** - 运行时数据目录，存储用户任务、日志和备份文件

## 🚀 安装与使用

### 📋 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Windows 7 SP1 | Windows 10/11 |
| **Python版本** | Python 3.8+ | Python 3.10+ |
| **内存** | 2GB RAM | 4GB+ RAM |
| **磁盘空间** | 50MB | 200MB |
| **显示器** | 1024x768 | 1920x1080 |

### 📦 方法一：使用预编译可执行文件（推荐）

1. **下载程序**
   ```
   从 Releases 页面下载最新版本的 WinTask.exe
   https://github.com/zhinianboke/win-task/releases
   ```

2. **运行程序**
   - 双击 `WinTask.exe` 启动程序
   - 首次运行会自动创建必要的目录结构
   - 无需安装Python环境，开箱即用

3. **开始使用**
   - 程序启动后会显示主界面
   - 点击"新建任务"开始创建您的第一个定时任务

### 💻 方法二：从源码运行（开发者）

1. **克隆仓库**
   ```bash
   git clone https://github.com/zhinianboke/win-task.git
   cd win-task
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行程序**
   ```bash
   python main.py
   ```

5. **打包成可执行文件**
   ```bash
   python build.py
   ```
   打包后的文件位于 `dist/release/WinTask.exe`

### 🔧 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 安装代码质量工具
pip install flake8 black isort pytest-cov

# 运行代码格式化
black src/
isort src/

# 运行代码检查
flake8 src/

# 运行测试
pytest tests/ --cov=src/
```

## 📚 使用文档

### 🎯 快速入门

#### 创建您的第一个任务

1. **启动程序** - 双击运行 WinTask.exe 或执行 `python main.py`

2. **新建任务** - 点击主界面的 "➕ 新建任务" 按钮

3. **选择任务类型**
   - 🌐 **HTTP请求** - 定时访问网页或API接口
   - 💻 **程序执行** - 运行批处理、PowerShell或可执行文件
   - 📂 **文件操作** - 自动备份、清理或同步文件
   - 🖥️ **系统操作** - 定时关机、重启或休眠
   - 🗄️ **数据库操作** - 执行SQL查询或数据库备份

4. **配置任务参数**
   - 📝 设置任务名称和描述
   - ⚙️ 配置具体的执行参数
   - 🏷️ 添加标签和分组（可选）

5. **设置执行计划**
   - ⏰ **一次性任务** - 指定具体的执行时间
   - 🔄 **周期性任务** - 每小时/天/周/月执行
   - 📅 **Cron表达式** - 使用高级调度表达式

6. **保存并启动**
   - 💾 点击"保存"按钮保存任务配置
   - ▶️ 任务将自动按计划执行，也可手动触发

#### 界面导航

- **📊 仪表盘** - 查看任务执行统计和系统状态
- **📋 任务列表** - 管理所有任务，查看状态和历史
- **📅 日历视图** - 直观查看任务计划安排
- **📈 执行历史** - 查看详细的任务执行记录
- **⚙️ 系统设置** - 配置应用参数和通知设置

### ⚙️ 配置文件说明

配置文件 `config.ini` 采用标准INI格式，包含以下主要配置节：

#### 📋 配置节详解

| 配置节 | 说明 | 主要参数 |
|--------|------|----------|
| **[General]** | 通用设置 | `version`, `theme`, `auto_start`, `minimize_to_tray` |
| **[Scheduler]** | 调度器设置 | `check_interval`, `max_concurrent_tasks`, `default_timeout` |
| **[Logging]** | 日志设置 | `level`, `retention_days`, `verbose` |
| **[Notification]** | 通知设置 | `enable`, `type`, `smtp_server`, `email_recipient` |
| **[Security]** | 安全设置 | `encrypt_sensitive_data`, `backup_frequency` |

#### 🔧 常用配置示例

```ini
[General]
version = 1.0.0
theme = light                    # light/dark 主题
auto_start = false              # 开机自启动
minimize_to_tray = true         # 启动时最小化到托盘

[Scheduler]
check_interval = 10             # 任务检查间隔（秒）
max_concurrent_tasks = 5        # 最大并发任务数
default_timeout = 3600          # 默认任务超时时间（秒）
max_retries = 3                 # 最大重试次数

[Logging]
level = INFO                    # 日志级别
retention_days = 30             # 日志保留天数
verbose = true                  # 详细日志

[Notification]
enable = true                   # 启用通知
type = desktop                  # 通知类型：desktop/email/both
smtp_server = smtp.gmail.com    # 邮件服务器
smtp_port = 587                 # 邮件端口
```

#### 📝 配置修改方式

1. **图形界面** - 通过程序的"⚙️ 设置"选项卡修改（推荐）
2. **直接编辑** - 编辑 `config.ini` 文件（需重启程序生效）
3. **命令行** - 使用 `--config` 参数指定配置文件路径

## 🎓 高级使用技巧

### ⏰ Cron表达式详解

Cron表达式提供了强大而灵活的时间调度能力：

#### 📝 基本格式
```
* * * * * (分 时 日 月 周)
│ │ │ │ │
│ │ │ │ └─── 星期几 (0-7, 0和7都表示周日)
│ │ │ └───── 月份 (1-12)
│ │ └─────── 日期 (1-31)
│ └───────── 小时 (0-23)
└─────────── 分钟 (0-59)
```

#### 🔥 常用表达式示例

| 表达式 | 说明 | 使用场景 |
|--------|------|----------|
| `0 12 * * *` | 每天中午12点 | 午间数据同步 |
| `0 9 * * 1-5` | 工作日上午9点 | 工作日报告生成 |
| `*/15 * * * *` | 每15分钟 | 系统监控检查 |
| `0 0 1 * *` | 每月1号午夜 | 月度数据备份 |
| `0 2 * * 0` | 每周日凌晨2点 | 周度系统维护 |
| `30 14 * * 1,3,5` | 周一三五下午2:30 | 定期报告发送 |

#### 🎯 特殊字符说明

- `*` - 匹配任意值
- `?` - 不指定值（仅用于日期和星期）
- `-` - 范围，如 `1-5` 表示1到5
- `,` - 列表，如 `1,3,5` 表示1、3、5
- `/` - 步长，如 `*/2` 表示每2个单位
- `L` - 最后，如 `L` 表示月末最后一天
- `W` - 工作日，如 `15W` 表示15号最近的工作日

### 🔗 任务依赖关系

#### 设置任务依赖
1. **创建主任务** - 先创建需要首先执行的任务
2. **创建依赖任务** - 创建依赖于主任务的任务
3. **配置依赖关系** - 在依赖任务的"高级设置"中添加主任务ID
4. **执行顺序** - 系统确保主任务成功完成后才执行依赖任务

#### 依赖关系类型
- **成功依赖** - 仅当前置任务成功完成时执行
- **完成依赖** - 无论前置任务成功或失败都执行
- **失败依赖** - 仅当前置任务失败时执行

### 🏷️ 任务分组和标签

#### 分组管理
- **按功能分组** - 如"数据备份"、"系统维护"、"报告生成"
- **按时间分组** - 如"每日任务"、"每周任务"、"每月任务"
- **按重要性分组** - 如"关键任务"、"普通任务"、"可选任务"

#### 标签系统
- **快速筛选** - 使用标签快速找到相关任务
- **批量操作** - 选择相同标签的任务进行批量操作
- **状态标记** - 使用标签标记任务状态或类型

### 💡 性能优化建议

#### 任务调度优化
- **合理设置并发数** - 根据系统性能调整最大并发任务数
- **避免资源冲突** - 避免多个任务同时访问相同资源
- **错峰执行** - 将资源密集型任务安排在不同时间段

#### 系统资源管理
- **监控资源使用** - 定期检查CPU、内存使用情况
- **设置超时时间** - 为长时间运行的任务设置合理超时
- **日志管理** - 定期清理旧日志文件，避免磁盘空间不足

## 🤝 贡献指南

我们热烈欢迎社区贡献！无论是功能建议、Bug报告、代码贡献还是文档改进，都是对项目的宝贵支持。

### 🐛 提交Bug报告

在提交Bug报告前，请：

1. **🔍 搜索现有Issue** - 确保该Bug尚未被报告
2. **📝 使用Bug模板** - 按照Issue模板提供详细信息
3. **📋 包含以下信息**：
   - 操作系统版本和Python版本
   - 详细的复现步骤
   - 预期行为和实际行为
   - 错误日志和截图（如有）
   - 相关的配置文件内容

### 💡 功能请求

提交功能请求时，请：

1. **🎯 明确需求** - 清楚描述想要的功能
2. **📖 说明用例** - 解释为什么需要这个功能
3. **🔄 考虑替代方案** - 是否有其他解决方案
4. **📊 评估影响** - 功能对现有用户的影响

### 🔧 代码贡献

#### 开发流程

1. **🍴 Fork仓库**
   ```bash
   git clone https://github.com/zhinianboke/win-task.git
   cd win-task
   ```

2. **🌿 创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **💻 开发和测试**
   ```bash
   # 安装开发依赖
   pip install -r requirements.txt

   # 运行测试
   pytest tests/

   # 代码格式化
   black src/
   isort src/

   # 代码检查
   flake8 src/
   ```

4. **📝 提交更改**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **🚀 推送和PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在GitHub上创建Pull Request

#### 📏 代码规范

- **🐍 遵循PEP 8** - Python代码风格指南
- **📚 文档字符串** - 为所有公共函数和类添加docstring
- **🧪 单元测试** - 为新功能添加相应的测试用例
- **🔍 类型注解** - 使用类型提示提高代码可读性
- **📝 提交信息** - 使用[约定式提交](https://conventionalcommits.org/)格式

#### 🧪 测试要求

- 所有新功能必须包含单元测试
- 测试覆盖率应保持在80%以上
- 确保所有测试通过后再提交PR

### 📖 文档贡献

- **📝 改进README** - 修正错误、添加示例
- **📚 API文档** - 完善代码文档和注释
- **🎓 教程指南** - 编写使用教程和最佳实践
- **🌍 国际化** - 帮助翻译界面和文档

### 🏆 贡献者认可

- 所有贡献者将在README中获得认可
- 重要贡献者将获得项目维护者权限
- 优秀贡献将在Release Notes中特别感谢

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

```
MIT License

Copyright (c) 2024 Win-Task Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 致谢

感谢所有为Win-Task项目做出贡献的开发者和用户！

### 🌟 主要贡献者

- **项目创始人** - 项目架构设计和核心功能开发
- **UI设计师** - 界面设计和用户体验优化
- **测试工程师** - 质量保证和测试用例编写
- **文档维护者** - 文档编写和维护

### 📚 第三方库

本项目使用了以下优秀的开源库：

- [PyQt5](https://pypi.org/project/PyQt5/) - GUI框架
- [APScheduler](https://pypi.org/project/APScheduler/) - 任务调度
- [Requests](https://pypi.org/project/requests/) - HTTP请求
- [SQLAlchemy](https://pypi.org/project/SQLAlchemy/) - 数据库ORM
- [Loguru](https://pypi.org/project/loguru/) - 日志系统

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐ Star！**

[🐛 报告Bug](https://github.com/zhinianboke/win-task/issues) •
[💡 功能建议](https://github.com/zhinianboke/win-task/issues) •
[📖 查看文档](https://github.com/zhinianboke/win-task/wiki) •
[💬 加入讨论](https://github.com/zhinianboke/win-task/discussions)

</div>