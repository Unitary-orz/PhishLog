import argparse
import csv
import datetime
import json
import re
from collections import defaultdict

import pandas as pd
import requests

# 尝试导入配置文件，如果不存在则使用默认值
try:
    import config
    IGNORE_USERS = config.IGNORE_USERS
    DEFAULT_WEBHOOK = config.DINGTALK_CONFIG['WEBHOOK_URL']
    DEFAULT_LOG_PATH = config.LOG_CONFIG['LOG_FILE']
    DEFAULT_MESSAGE_TITLE = config.DINGTALK_CONFIG['MESSAGE_TITLE']
    API_CHECK_URL = config.API_CONFIG['CHECK_URL']  # 添加API检查URL配置
except ImportError:
    print("[!] 未找到config.py，使用默认配置")
    # 退出
    exit(1)



def normalize_username(username):
    """标准化用户名，使相似用户名能够被识别为同一用户
    
    规则:
    1. 移除邮箱域名部分
    2. 移除常见前缀和后缀
    3. 转换为小写
    
    Args:
        username: 原始用户名
        
    Returns:
        标准化后的用户名
    """
    if not username:
        return username

    # 转换为小写
    normalized = username.lower()

    # 移除邮箱域名部分
    normalized = normalized.split('@')[0]

    # 移除特殊字符和数字后缀 (如 username_123 -> username)
    normalized = re.sub(r'[_\.-][0-9]+$', '', normalized)

    return normalized


def parse_log_line(line):
    """解析日志行并提取JSON数据"""
    try:
        # 分离时间戳和JSON部分
        parts = line.strip().split(' - 登录尝试: ', 1)
        if len(parts) != 2:
            return None

        log_json = json.loads(parts[1].replace("'", '"'))
        return log_json
    except Exception as e:
        print(f"解析错误: {e}")
        return None


def analyze_login_attempts(log_file_path, ignore_users=None, normalize=True):
    """分析登录尝试日志
    
    Args:
        log_file_path: 日志文件路径
        ignore_users: 忽略的用户名列表，默认为None
        normalize: 是否对用户名进行标准化，默认为True
    """
    # 如果ignore_users为None，初始化为空列表
    if ignore_users is None:
        ignore_users = []

    # 用于映射原始用户名到标准化用户名
    username_mapping = {}

    # 存储用户统计信息
    user_stats = defaultdict(lambda: {
        "usernames": set(),  # 存储原始用户名集合
        "passwords": set(),
        "ips": set(),
        "user_agents": set(),
        "first_attempt": None,
        "last_attempt": None,
        "count": 0
    })

    # 读取日志文件
    with open(log_file_path, 'r') as file:
        for line in file:
            if '登录尝试' not in line:
                continue

            log_data = parse_log_line(line)
            if not log_data:
                continue

            original_username = log_data.get('username')
            if not original_username:
                continue

            # 如果启用标准化，使用标准化后的用户名作为键
            if normalize:
                normalized_username = normalize_username(original_username)
                # 记录原始用户名到标准化用户名的映射
                username_mapping[original_username] = normalized_username
                key_username = normalized_username
            else:
                key_username = original_username

            # 如果用户在忽略列表中，跳过处理
            if key_username in ignore_users or original_username in ignore_users:
                continue

            # 更新用户统计信息
            stats = user_stats[key_username]
            stats["usernames"].add(original_username)
            stats["passwords"].add(log_data.get('password', ''))
            stats["ips"].add(log_data.get('ip', ''))
            stats["user_agents"].add(log_data.get('user_agent', ''))
            stats["count"] += 1

            # 更新时间统计
            timestamp = datetime.datetime.strptime(
                log_data.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
            if stats["first_attempt"] is None or timestamp < stats["first_attempt"]:
                stats["first_attempt"] = timestamp
            if stats["last_attempt"] is None or timestamp > stats["last_attempt"]:
                stats["last_attempt"] = timestamp

    # 转换为可序列化的格式
    result = []
    for key_username, stats in user_stats.items():
        result.append({
            "normalized_username": key_username,
            "usernames": list(stats["usernames"]),  # 原始用户名列表
            "passwords": list(stats["passwords"]),
            "ips": list(stats["ips"]),
            "user_agents": list(stats["user_agents"]),
            "first_attempt": stats["first_attempt"].strftime('%Y-%m-%d %H:%M:%S') if stats["first_attempt"] else None,
            "last_attempt": stats["last_attempt"].strftime('%Y-%m-%d %H:%M:%S') if stats["last_attempt"] else None,
            "count": stats["count"]
        })

    return result


def generate_csv_output(stats):
    """生成CSV格式的输出"""
    # 准备CSV数据
    csv_data = []

    # 添加表头
    headers = ['用户名', '原始用户名', '尝试次数', '首次尝试时间', '最近尝试时间', 'IP地址', '使用的密码']
    csv_data.append(headers)

    # 添加数据行
    for user in stats:
        row = [
            user.get('normalized_username', ''),
            '; '.join(user.get('usernames', [])),
            user.get('count', ''),
            user.get('first_attempt', ''),
            user.get('last_attempt', ''),
            '; '.join(user.get('ips', [])),
            '; '.join(user.get('passwords', []))
        ]
        csv_data.append(row)

    # 将数据转换为CSV字符串
    csv_output = []
    for row in csv_data:
        csv_output.append(','.join([f'"{str(item)}"' for item in row]))

    return '\n'.join(csv_output)


def generate_markdown_output(title, stats, verbose=False):
    """生成Markdown格式的输出，使用与控制台打印相似的简洁风格"""
    if not stats:
        return f"### {title}\n\n未发现登录尝试记录。"

    markdown = f"### {title}\n\n"
    markdown += f"**总计发现 {len(stats)} 个账号的登录尝试**\n\n"

    # 使用简洁风格，类似打印简要统计信息的格式
    for user in stats:
        # 显示所有原始用户名，或使用标准化用户名
        display_name = user.get('normalized_username', '')

        # 处理用户名显示

        markdown += f"- **{display_name}** "

        # 添加尝试次数和IP数量
        markdown += f"\n\n  - 尝试次数: {user['count']}"
        markdown += f"\n  - 登陆IP: {'、'.join(user['ips'])}"
        # 尝试过的用户名
        if 'usernames' in user and user['usernames']:
            if len(user['usernames']) > 1:
                markdown += f"\n  - 尝试过的用户名: {', '.join(user['usernames'])}"
        # 最近尝试时间
        if user['last_attempt']:
            markdown += f"\n  - 最近尝试时间: {user['last_attempt']}"

        markdown += "\n\n"

    if verbose:
        markdown += "\n### 详细信息\n\n"

        for user in stats:
            display_name = user.get('normalized_username', '')

            markdown += f"#### 用户: {display_name}\n\n"

            if 'usernames' in user and len(user['usernames']) > 1:
                markdown += f"- **原始用户名**: {', '.join(user['usernames'])}\n"

            markdown += f"- **尝试次数**: {user['count']}\n"
            markdown += f"- **首次尝试**: {user['first_attempt']}\n"
            markdown += f"- **最近尝试**: {user['last_attempt']}\n"
            markdown += f"- **使用的密码**: {', '.join(user['passwords'])}\n"
            markdown += f"- **IP地址**: {', '.join(user['ips'])}\n"
            markdown += f"- **用户代理**: {', '.join(list(user['user_agents'])[:3])}{'...' if len(user['user_agents']) > 3 else ''}\n\n"

    return markdown


def send_dingtalk_message(webhook_url, title, content):
    """发送钉钉消息
    
    Args:
        webhook_url: 钉钉机器人Webhook地址
        title: 消息标题
        content: Markdown格式的消息内容
    
    Returns:
        bool: 发送是否成功
    """
    if not webhook_url:
        print("未提供钉钉Webhook地址，跳过发送")
        return False

    try:
        headers = {
            'Content-Type': 'application/json'
        }

        message = {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': content
            }
        }

        response = requests.post(
            webhook_url,
            headers=headers,
            data=json.dumps(message)
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print(f"[+]【{title}】钉钉消息发送成功")
                return True
            else:
                print(f"[-]【{title}】钉钉消息发送失败 {result.get('errmsg')}")
        else:
            print(f"[-]【{title}】钉钉消息发送失败，状态码: {response.status_code}")

        return False
    except Exception as e:
        print(f"发送钉钉消息时出错: {e}")
        return False


def filter_today_records(stats):
    """筛选出今日的登录尝试记录
    
    Args:
        stats: 登录尝试统计记录列表
        
    Returns:
        只包含今日记录的统计列表
    """
    today = datetime.datetime.now().date()
    today_stats = []

    for user in stats:
        # 检查最后尝试时间是否为今天
        if user['last_attempt']:
            last_attempt_date = datetime.datetime.strptime(
                user['last_attempt'], '%Y-%m-%d %H:%M:%S').date()
            if last_attempt_date == today:
                today_stats.append(user)

    return today_stats


def generate_brief_output(title, stats):
    print(f"[+] 生成统计简述")
    print(f"--------------------------------")
    print(f"{title}")
    print(f"总计发现 {len(stats)} 个账号的登录尝试")
    for user in stats:
        display_name = user.get('normalized_username', '')
        if 'usernames' in user and user['usernames']:
            if len(user['usernames']) > 1:
                user_list = ', '.join(user['usernames'])
                print(
                    f"用户名: {display_name} ({user_list}), 尝试次数: {user['count']}, IP数量: {len(user['ips'])}")
            else:
                print(
                    f"用户名: {user['usernames'][0]}, 尝试次数: {user['count']}, IP数量: {len(user['ips'])}")
        else:
            print(
                f"用户名: {display_name}, 尝试次数: {user['count']}, IP数量: {len(user['ips'])}")
    print(f"--------------------------------")


def check_api_health(url=None):
    """检查API的是否存在
    
    Args:
        url: API健康检查的URL，如果未提供则使用配置中的默认值
        
    Returns:
        tuple: (bool, str) - (是否健康, 状态信息)
    """
    check_url = url if url else API_CHECK_URL

    try:
        response = requests.get(check_url, timeout=5)
        if response.status_code == 200:
            return True, "API 运行正常"
        else:
            return False, f"API 返回异常状态码: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"API 连接失败: {str(e)}"


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='分析登录尝试日志')
    parser.add_argument('--log', default=DEFAULT_LOG_PATH, help='日志文件路径')
    parser.add_argument('--ignore', nargs='+',
                        default=IGNORE_USERS, help='要忽略的用户名列表，多个用户以空格分隔')
    parser.add_argument('--dingtalk', action='store_true', help='开启钉钉消息推送功能')
    parser.add_argument('--webhook', help='自定义钉钉机器人Webhook地址，不提供则使用默认地址')
    parser.add_argument(
        '--title', default=DEFAULT_MESSAGE_TITLE, help='发送到钉钉的消息标题')
    parser.add_argument('--no-normalize', action='store_true', help='禁用用户名标准化')
    parser.add_argument('--verbose', action='store_true', help='钉钉输出中显示详细信息')
    parser.add_argument('--print', action='store_true',
                        default=True, help='在输出中显示详细信息')
    parser.add_argument('--csv', action='store_true',
                        default=True, help='生成CSV格式结果')
    parser.add_argument('--today', action='store_true', help='只显示今日的登录尝试记录')
    parser.add_argument('--check-api', action='store_true', help='检查API健康状态')
    parser.add_argument('--api-url', help='自定义API健康检查URL')
    args = parser.parse_args()

    # 检查API健康状态
    if args.check_api:
        is_healthy, status_message = check_api_health(args.api_url)
        if is_healthy:
            print(f"[+] {status_message}")
        else:
            print(f"[!] {status_message}")
            if args.dingtalk:
                # 如果API不健康，发送告警到钉钉
                alert_title = "API 状态检测"
                alert_content = f"### {alert_title}\n\n{status_message}"
                webhook_url = args.webhook if args.webhook else DEFAULT_WEBHOOK
                send_dingtalk_message(webhook_url, alert_title, alert_content)
            return

    # 忽略列表
    ignore_users = set(args.ignore)
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')

    if ignore_users:
        print(f"[+] 忽略以下用户: {', '.join(ignore_users)}")

    # 是否标准化用户名
    normalize = not args.no_normalize

    stats = analyze_login_attempts(args.log, ignore_users, normalize)

    # 输出CSV格式
    if args.csv:
        csv_output = generate_csv_output(stats)
        with open('stats.csv', 'w', encoding='utf-8') as f:
            f.write(csv_output)
            print(f"[+] CSV格式结果已保存到 stats.csv")

    # 如果需要筛选今日记录
    if args.today:
        title = f"{args.title}({today_date}当天)"
        display_stats = filter_today_records(stats)
        if not display_stats:
            print(f"\n[-] 今日的登录尝试记录为空")
            args.dingtalk = False
    else:
        title = f"{args.title}(截止{today_date})"
        display_stats = stats

    # 生成Markdown格式输出并发送到钉钉
    if args.dingtalk:
        markdown_output = generate_markdown_output(
            title, display_stats, args.verbose)

        # 设置webhook地址，如果未提供则使用默认地址
        webhook_url = args.webhook if args.webhook else DEFAULT_WEBHOOK

        # 设置标题
        title = args.title

        # 发送到钉钉
        send_dingtalk_message(webhook_url, title, markdown_output)

    # 打印简要统计信息
    if args.print:
        generate_brief_output(title, display_stats)


if __name__ == "__main__":
    main()
