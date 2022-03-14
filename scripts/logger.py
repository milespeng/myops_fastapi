import os
import time
from loguru import logger

basedir = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

# print(f"log basedir{basedir}")  # /xxx/python_code/FastAdmin/backend/app
# 定位到log日志文件
log_path = os.path.join(basedir, 'logs')

if not os.path.exists(log_path):
    os.mkdir(log_path)

log_path_error = os.path.join(
    log_path, f'{time.strftime("%Y-%m-%d")}_error.log')

# 日志简单配置
# 具体其他配置 可自行参考 https://github.com/Delgan/loguru
logger.add(log_path_error, rotation="12:00", retention="5 days", enqueue=True)
