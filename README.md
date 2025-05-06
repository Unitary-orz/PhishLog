# PhishLog

PhishLog是一个用于记录和分析钓鱼网站登录尝试的工具，帮助安全研究人员收集和统计潜在攻击者的行为数据。

## 功能特点

- 模拟登录接口，记录用户名、密码和IP信息
- 自动统计分析登录尝试数据
- 支持标准化用户名匹配相似账号
- 生成CSV格式报告
- 通过钉钉机器人发送统计报告
- 支持定时任务自动执行统计分析

## 系统组件

- `back_api.py` - Flask后端服务，提供模拟登录API
- `stats.py` - 统计分析脚本，处理日志数据并生成报告
- `dd_run.py` - 定时任务调度器，定期执行统计分析
- `login_attempts.log` - 记录所有登录尝试的日志文件
- `stats.csv` - 统计结果输出文件
- `config.template.py` - 配置文件模板
- `config.py` - 本地配置文件(需自行创建，不提交到版本控制)

## 安装说明

1. 下载项目到本地


2. 安装依赖
   ```
   pip install -r requirements.txt
   ```

3. 创建配置文件
   ```
   cp config.template.py config.py
   ```
   然后根据需要编辑 `config.py` 文件，填入正确的配置信息。

## 使用方法

### 配置说明

项目使用配置文件 `config.py` 管理所有敏感配置，包括：

- API服务配置（端口、地址、CORS设置等）
- 日志配置
- 钉钉机器人配置（webhook地址）
- 定时任务配置

**注意**：`config.py` 文件包含敏感信息，已被添加到 `.gitignore` 中，不会被提交到版本控制系统。每次部署时需要手动创建。

### 钉钉机器人配置

要使用钉钉机器人功能，请按照以下步骤操作：

1. 在钉钉群中添加自定义机器人：
   - 打开钉钉群聊
   - 点击群设置 > 智能群助手 > 添加机器人 > 自定义
   - 设置机器人名称和头像
   - 安全设置中选择"加签"（推荐）或"自定义关键词"
   - 若选择关键词，请添加"PhishLog"作为关键词
   - 复制生成的Webhook地址和选择“加签”

2. 配置项目文件：
   - 打开`config.py`文件
   - 设置`DINGTALK_WEBHOOK`为刚才获取的Webhook地址
   
3. 测试配置是否正确：
   ```
   python stats.py --dingtalk
   ```

配置示例参考图：

![钉钉机器人配置](img/rebotset.jpg)

### 启动API服务

运行以下命令启动模拟登录API服务：

```
python back_api.py
```

服务默认在8090端口运行，可以通过浏览器访问 `http://your-server-ip:8090/` 。

### 手动执行统计分析

```
# 基本分析
python stats.py

# 发送报告到钉钉
python stats.py --dingtalk

# 仅分析今天的数据
python stats.py --today
```

### 启动定时任务

```
python dd_run.py
```

定时任务默认会在每天12:00和17:00自动执行统计分析并发送到钉钉群，可以在 `config.py` 中修改执行时间。

## 参数说明

### stats.py 参数

- `--dingtalk`: 将统计结果发送到钉钉
- `--today`: 仅统计今天的登录尝试
- `--verbose`: 生成详细统计信息
- `--ignore-user USER`: 排除特定用户名
- `--webhook URL`: 指定自定义钉钉webhook地址
- `--log-file PATH`: 指定自定义日志文件路径

## 输出示例

统计结果将以CSV格式输出到 `stats.csv` 文件，包含以下字段：

- 用户名（标准化后）
- 原始用户名（可能多个）
- 尝试次数
- 首次尝试时间
- 最近尝试时间
- IP地址列表
- 使用的密码列表

## 安全注意事项

- 本工具仅用于安全研究和教育目的
- 请勿用于非法活动
- 请遵守相关法律法规和网络安全政策

## 许可证

[MIT License](LICENSE) 