import logging
import os
from datetime import datetime
from .path_tool import get_abs_path

# 日志保存的根目录
LOG_PATH = get_abs_path("log")

# 确保日志目录存在
os.makedirs(LOG_PATH, exist_ok=True)

# 日志的格式配置 error info debug
DEFAULT_LOG_FORMAT = logging.Formatter("%(asctime)s- %(name)s- %(levelname)s - %(filename)s:%(lineno)d - %(message)s")

def get_logger(

    name:str = "agent",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file = None,
) -> logging.Logger:
    logger = logging.getLogger (name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加Handler

    if logger.handlers:
        return logger

    #控制台Handler

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)

    # 日志handler
    if not log_file:
        log_file = os.path.join(LOG_PATH, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)
    return logger

logger = get_logger()


