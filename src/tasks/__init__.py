"""
Win-Task 任务类型模块
"""

import importlib
import inspect
import logging
import pkgutil
from types import ModuleType
from typing import Dict, Type
from src.core.task import BaseTask

logger = logging.getLogger("tasks")

# 存储所有任务类型
TASK_CLASSES: Dict[str, Type[BaseTask]] = {}

def _load_task_modules():
    """通过 pkgutil 遍历子模块，注册任务类型。

    采用 pkgutil.iter_modules(__path__) 而不是 os.listdir，
    以便在 PyInstaller 等打包环境中也能正常工作。
    """
    for module_info in pkgutil.iter_modules(__path__):
        name = module_info.name  # 模块名（不含包前缀）
        if not name.endswith("_task"):
            continue  # 只加载 *_task.py 模块
        full_module_name = f"{__name__}.{name}"
        try:
            module: ModuleType = importlib.import_module(full_module_name)
            # 查找模块中的 BaseTask 子类
            for attr_name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseTask) and obj is not BaseTask and obj.__module__ == full_module_name:
                    TASK_CLASSES[attr_name] = obj
                    globals()[attr_name] = obj  # 导出到当前命名空间
                    logger.debug("已注册任务类型: %s (%s)", attr_name, full_module_name)
        except Exception as exc:
            logger.error("加载任务模块 %s 失败: %s", full_module_name, exc)

# 执行加载
_load_task_modules()

# 导出所有任务类名，供 * 号导入
__all__ = list(TASK_CLASSES.keys()) 