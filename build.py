#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Win-Task 打包脚本

使用PyInstaller将程序打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    print("清理构建目录...")
    
    # 要清理的目录
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除 {dir_name} 目录")
    
    # 删除 .spec 文件
    for spec_file in Path('.').glob('*.spec'):
        os.remove(spec_file)
        print(f"已删除 {spec_file}")


def create_version_file():
    """创建版本信息文件"""
    print("创建版本信息文件...")
    
    version = "1.0.0"
    try:
        # 尝试使用UTF-8解码
        build_time = subprocess.check_output(
            "echo %date% %time%", shell=True
        ).decode('utf-8').strip()
    except UnicodeDecodeError:
        # 如果失败，尝试使用系统默认编码（中文Windows通常是GBK）
        build_time = subprocess.check_output(
            "echo %date% %time%", shell=True
        ).decode('gbk', errors='replace').strip()
    
    with open('version.txt', 'w', encoding='utf-8') as f:
        f.write(f"Version: {version}\n")
        f.write(f"Build time: {build_time}\n")
    
    print(f"已创建版本信息文件，版本号: {version}")


def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # PyInstaller 命令行参数
    cmd = [
        'pyinstaller',
        '--clean',
        '--name=WinTask',
        '--noconsole',  # 无控制台窗口
        '--onefile',    # 单文件模式
        # '--icon=assets/icons/app_icon.ico',  # 暂时注释掉图标
        '--add-data=config.ini;.',
        '--add-data=version.txt;.',
        '--add-data=assets;assets',
        'main.py'
    ]
    
    # 执行打包命令
    subprocess.call(cmd)
    
    print("可执行文件构建完成！")


def copy_additional_files():
    """复制额外文件到发布目录"""
    print("复制额外文件...")
    
    # 创建发布目录
    release_dir = os.path.join('dist', 'release')
    os.makedirs(release_dir, exist_ok=True)
    
    # 复制可执行文件
    shutil.copy(
        os.path.join('dist', 'WinTask.exe'), 
        os.path.join(release_dir, 'WinTask.exe')
    )
    
    # 复制README和许可证文件
    shutil.copy('README.md', os.path.join(release_dir, 'README.md'))
    
    # 创建空的data目录
    data_dirs = ['tasks', 'logs', 'backups']
    for dir_name in data_dirs:
        os.makedirs(os.path.join(release_dir, 'data', dir_name), exist_ok=True)
    
    print(f"额外文件已复制到 {release_dir} 目录")


def main():
    """主函数"""
    print("Win-Task 打包脚本")
    print("=" * 50)
    
    # 清理旧的构建目录
    clean_build_dirs()
    
    # 创建版本信息文件
    create_version_file()
    
    # 构建可执行文件
    build_executable()
    
    # 复制额外文件
    copy_additional_files()
    
    print("=" * 50)
    print("打包完成！")


if __name__ == "__main__":
    main() 