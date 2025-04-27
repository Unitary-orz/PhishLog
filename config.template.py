#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置模板文件
复制此文件为 config.py 并填入实际配置信息
确保 config.py 不会被提交到版本控制系统中
"""

# API服务配置
API_CONFIG = {
    # 服务绑定地址和端口
    'HOST': '0.0.0.0',
    'PORT': 8090,

    # CORS配置
    'CORS_ORIGINS': 'http://example.com:8081',

    # 登录成功后重定向URL
    'REDIRECT_URL': 'https://example.com/success',

    # 静态文件
    'INDEX_FILE': 'index.html'
}

# 日志配置
LOG_CONFIG = {
    # 日志文件路径
    'LOG_FILE': 'login_attempts.log',

    # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    'LOG_LEVEL': 'INFO'
}

# 钉钉机器人配置
DINGTALK_CONFIG = {
    # 钉钉Webhook地址
    'WEBHOOK_URL': 'https://oapi.dingtalk.com/robot/send?access_token=your_token_here',

    # 钉钉消息标题
    'MESSAGE_TITLE': '登录尝试统计'
}

# 忽略的用户名列表
IGNORE_USERS = ['test', 'admin', 'guest']

# 定时任务配置
SCHEDULER_CONFIG = {
    # 执行时间（24小时制）
    'FIRST_RUN_HOUR': 12,
    'FIRST_RUN_MINUTE': 0,
    'SECOND_RUN_HOUR': 17,
    'SECOND_RUN_MINUTE': 0
}
