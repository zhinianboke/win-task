#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
URL请求任务模块

实现HTTP/HTTPS请求任务
"""

import json
import logging
import requests
from requests.exceptions import RequestException

from src.core.task import BaseTask, TaskStatus, TaskResult


class URLTask(BaseTask):
    """URL请求任务类"""
    
    def __init__(self, name, description="", url=None, method="GET", headers=None, 
                 body=None, auth=None, timeout=30, verify_ssl=True):
        """
        初始化URL请求任务
        
        参数:
            name (str): 任务名称
            description (str, optional): 任务描述
            url (str, optional): 请求的URL
            method (str, optional): 请求方法，如GET、POST、PUT、DELETE等
            headers (dict, optional): 请求头
            body (str/dict, optional): 请求体
            auth (tuple, optional): 认证信息，格式为(username, password)
            timeout (int, optional): 请求超时时间（秒），0表示无限制
            verify_ssl (bool, optional): 是否验证SSL证书
        """
        super().__init__(name, description)
        
        # 请求参数
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.auth = auth
        self.request_timeout = timeout
        self.verify_ssl = verify_ssl
        
        # 返回结果处理
        self.expected_status_code = 200
        self.follow_redirects = True
        self.extract_response_json = False
        self.extract_json_path = None
    
    def run(self):
        """
        执行URL请求任务
        
        返回:
            TaskResult: 任务执行结果
        """
        result = TaskResult()
        result.start()
        
        # 日志记录
        self.logger.info(f"执行URL请求: {self.method} {self.url}")
        self.logger.debug(f"请求头: {self.headers}")
        
        if not self.url:
            error_msg = "URL未设置"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        try:
            # 准备请求参数
            request_kwargs = {
                'url': self.url,
                'headers': self.headers,
                'verify': self.verify_ssl,
                'allow_redirects': self.follow_redirects,
            }
            
            # 设置超时，0表示无限制（不设置超时）
            if self.request_timeout > 0:
                request_kwargs['timeout'] = self.request_timeout
            
            # 添加认证信息
            if self.auth:
                request_kwargs['auth'] = self.auth
            
            # 添加请求体
            if self.method in ('POST', 'PUT', 'PATCH') and self.body:
                if isinstance(self.body, dict):
                    # 如果是字典，假设是JSON数据
                    request_kwargs['json'] = self.body
                    self.logger.debug(f"JSON请求体: {json.dumps(self.body)}")
                elif isinstance(self.body, str):
                    # 如果是字符串，尝试解析为JSON，如果失败则当作普通文本
                    try:
                        json_data = json.loads(self.body)
                        request_kwargs['json'] = json_data
                        self.logger.debug(f"JSON请求体(从字符串解析): {json.dumps(json_data)}")
                    except json.JSONDecodeError:
                        # 非JSON字符串，当作普通文本
                        request_kwargs['data'] = self.body
                        self.logger.debug(f"文本请求体: {self.body}")
                else:
                    # 其他类型，转为字符串
                    request_kwargs['data'] = str(self.body)
                    self.logger.debug(f"其他类型请求体: {str(self.body)}")
            
            # 发送请求
            response = requests.request(self.method, **request_kwargs)
            
            # 处理响应
            status_code = response.status_code
            self.logger.info(f"请求完成，状态码: {status_code}")
            
            # 提取响应内容
            try:
                response_content = response.text
                
                # 尝试解析为JSON
                try:
                    response_json = response.json()
                    
                    # 如果需要提取JSON路径
                    if self.extract_response_json and self.extract_json_path:
                        try:
                            # 简单的路径提取实现
                            value = self._extract_json_path(response_json, self.extract_json_path)
                            response_content = json.dumps(value, ensure_ascii=False)
                        except Exception as e:
                            self.logger.warning(f"提取JSON路径失败: {str(e)}")
                    else:
                        # 格式化JSON输出
                        response_content = json.dumps(response_json, indent=2, ensure_ascii=False)
                
                except ValueError:
                    # 不是JSON，使用原始文本
                    pass
                
            except Exception as e:
                response_content = f"无法读取响应内容: {str(e)}"
                self.logger.warning(response_content)
            
            # 检查状态码
            if self.expected_status_code and status_code != self.expected_status_code:
                result.complete(
                    TaskStatus.FAILED,
                    status_code,
                    response_content,
                    f"状态码 {status_code} 不符合预期 {self.expected_status_code}"
                )
            else:
                result.complete(TaskStatus.SUCCESS, status_code, response_content)
            
            return result
            
        except RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            self.logger.error(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
        
        except Exception as e:
            error_msg = f"任务执行异常: {str(e)}"
            self.logger.exception(error_msg)
            result.complete(TaskStatus.FAILED, -1, "", error_msg)
            return result
    
    def _extract_json_path(self, json_data, path):
        """
        从JSON中提取指定路径的值
        
        参数:
            json_data (dict/list): JSON数据
            path (str): 路径表达式，如 "data.user.name"
            
        返回:
            任何值: 指定路径的值
            
        抛出:
            KeyError: 如果路径不存在
        """
        if not path:
            return json_data
        
        parts = path.split('.')
        value = json_data
        
        for part in parts:
            # 处理数组索引，如 "items[0]"
            if '[' in part and part.endswith(']'):
                key, index_str = part.split('[', 1)
                index = int(index_str[:-1])
                
                value = value[key]
                value = value[index]
            else:
                value = value[part]
        
        return value
    
    def to_dict(self):
        """
        将任务转换为字典用于序列化
        
        返回:
            dict: 任务的字典表示
        """
        data = super().to_dict()
        
        # 添加URL任务特有字段
        data.update({
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'body': self.body,
            'auth': self.auth,
            'request_timeout': self.request_timeout,
            'verify_ssl': self.verify_ssl,
            'expected_status_code': self.expected_status_code,
            'follow_redirects': self.follow_redirects,
            'extract_response_json': self.extract_response_json,
            'extract_json_path': self.extract_json_path
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建任务对象
        
        参数:
            data (dict): 任务的字典表示
            
        返回:
            URLTask: 任务对象
        """
        task = super().from_dict(data)
        
        # 设置URL任务特有字段
        task.url = data.get('url')
        task.method = data.get('method', 'GET')
        task.headers = data.get('headers', {})
        task.body = data.get('body')
        task.auth = data.get('auth')
        task.request_timeout = data.get('request_timeout', 30)
        task.verify_ssl = data.get('verify_ssl', True)
        task.expected_status_code = data.get('expected_status_code', 200)
        task.follow_redirects = data.get('follow_redirects', True)
        task.extract_response_json = data.get('extract_response_json', False)
        task.extract_json_path = data.get('extract_json_path')
        
        return task 