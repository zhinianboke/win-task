#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Win-Task 打包配置文件
"""

import os
from setuptools import setup, find_packages

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 读取requirements.txt
with open(os.path.join(ROOT_DIR, 'requirements.txt'), 'r') as f:
    requirements = f.read().splitlines()

setup(
    name="win-task",
    version="1.0.0",
    author="Win-Task Team",
    author_email="example@example.com",
    description="Windows 定时任务管理系统",
    long_description=open(os.path.join(ROOT_DIR, 'README.md'), 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/win-task",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires='>=3.7',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'win-task=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.ini', '*.png', '*.ico'],
    },
) 