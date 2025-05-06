import logging
import subprocess
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

# 尝试导入配置文件，如果不存在则使用默认值
try:
    import config
    SCHEDULER_CONFIG = config.SCHEDULER_CONFIG
except ImportError:
    print("警告: 未找到config.py，使用默认配置")
    SCHEDULER_CONFIG = {
        'FIRST_RUN_HOUR': 12,
        'FIRST_RUN_MINUTE': 0,
        'SECOND_RUN_HOUR': 17,
        'SECOND_RUN_MINUTE': 0,
        'CHECK_RUN_INTERVAL': 1
    }

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def run_stats(today=False):
    logging.info("开始执行统计任务")
    if today:
        subprocess.run([sys.executable, "stats.py", "--dingtalk", "--today"])
        logging.info("执行今日统计任务")
        logging.info(f"执行命令: {sys.executable} stats.py --dingtalk --today")
    else:
        subprocess.run([sys.executable, "stats.py", "--dingtalk"])
        logging.info("执行统计任务")
        logging.info(f"执行命令: {sys.executable} stats.py --dingtalk")

    logging.info("统计任务执行完成")


def run_api_check():
    logging.info("开始执行API健康检查")
    subprocess.run([sys.executable, "stats.py", "--api-check", "--dingtalk"])
    logging.info("API健康检查执行完成")

# 立即运行1次
# logging.info("立即运行1次")
# run_stats(today=True)


scheduler = BlockingScheduler()

# 按照配置时间运行
scheduler.add_job(
    run_stats,
    'cron',
    hour=SCHEDULER_CONFIG['FIRST_RUN_HOUR'],
    minute=SCHEDULER_CONFIG['FIRST_RUN_MINUTE'],
    args=[True]
)
scheduler.add_job(
    run_stats,
    'cron',
    hour=SCHEDULER_CONFIG['SECOND_RUN_HOUR'],
    minute=SCHEDULER_CONFIG['SECOND_RUN_MINUTE'],
    args=[True]
)

# 添加每小时运行一次的任务
scheduler.add_job(
    run_api_check,
    'interval',
    hours=SCHEDULER_CONFIG['CHECK_RUN_INTERVAL']
)

try:
    logging.info(f"定时器已启动，每天{SCHEDULER_CONFIG['FIRST_RUN_HOUR']}:{SCHEDULER_CONFIG['FIRST_RUN_MINUTE']}和"
                 f"{SCHEDULER_CONFIG['SECOND_RUN_HOUR']}:{SCHEDULER_CONFIG['SECOND_RUN_MINUTE']}执行统计任务")
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    logging.info("定时器已停止")
