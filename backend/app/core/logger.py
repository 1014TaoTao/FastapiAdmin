# -*- coding: utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import re

from app.config.setting import settings


class AppLogger:
    """应用级日志管理器：一次性配置 + 获取。"""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._configured = False

    def _create_file_handler(self, stem: str, level: int, log_dir: Path, formatter: logging.Formatter) -> TimedRotatingFileHandler:
        file_path = log_dir / f"{stem}.log"
        handler = TimedRotatingFileHandler(
            filename=str(file_path),
            when=settings.WHEN,
            interval=settings.INTERVAL,
            backupCount=settings.BACKUPCOUNT,
            encoding=settings.ENCODING,
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.suffix = "_%Y-%m-%d.log"  # 设置正确的后缀格式

        def namer(default_name: str) -> str:
            # 统一处理轮转后的文件名，确保格式为stem_YYYY-MM-DD.log
            file_name = Path(default_name).name
            # 提取日期部分
            base_name = file_name.split('.')[0]  # 获取基本名称（不包含扩展名）
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', base_name)
            if date_match:
                date_part = date_match.group(1)
                return f"{stem}_{date_part}.log"
            
            # 如果没有找到日期部分，返回原始名称
            return default_name

        def rotator(source: str, dest: str) -> None:
            # 确保目录存在
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            # 重命名文件
            Path(source).rename(dest)
        
        handler.namer = namer
        handler.rotator = rotator
        return handler

    def configure(self) -> logging.Logger:
        if self._configured:
            return self._logger

        # 基础设置
        self._logger.setLevel(settings.LOGGER_LEVEL)
        self._logger.handlers.clear()
        self._logger.propagate = False

        # 目录与格式
        log_dir = Path(settings.LOGGER_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter(settings.LOGGER_FORMAT)

        # 文件处理器
        self._logger.addHandler(self._create_file_handler("info", logging.INFO, log_dir, formatter))
        self._logger.addHandler(self._create_file_handler("error", logging.ERROR, log_dir, formatter))

        # 控制台处理器
        console = logging.StreamHandler()
        console.setLevel(settings.LOGGER_LEVEL)
        console.setFormatter(formatter)
        self._logger.addHandler(console)

        self._configured = True
        return self._logger

    def get_logger(self) -> logging.Logger:
        return self.configure()

def get_logger() -> logging.Logger:
    AL = AppLogger()
    return AL.get_logger()


# 模块级兼容实例
logger = get_logger()
