import logging
import sys
import os
from datetime import datetime

def setup_logging():
    # 1. 确定日志文件存放路径（EXE 所在的文件夹）
    # 如果是打包环境，使用 sys.executable 获取 exe 路径
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(base_dir) # 回到项目根目录

    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d')}.log")

    # 2. 配置日志格式
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 3. 创建文件处理器（输出到文件）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(log_format)

    # 4. 创建控制台处理器（开发时在终端可见）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    # 5. 设置全局 Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 6. 【核心】捕获所有未处理的系统异常
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    return logger

# 初始化并导出记录器对象
logger = setup_logging()