import logging
import os
import sys
from pathlib import Path
from typing import Optional

from src.drawflow_client import load_connection

from .log_capture import MemoryLogHandler, SecretMaskingFilter

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def drawflow_tokens() -> list[str]:
    connection = load_connection()
    return [connection.token] if connection else []


class Logger:
    """全局日志管理类
    
    使用单例模式实现的日志管理器，提供统一的日志记录接口。
    可以在应用的任何位置使用该类记录日志。
    """
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    _memory_handler: Optional[MemoryLogHandler] = None
    _secret_filter: Optional[SecretMaskingFilter] = None
    _log_file: Optional[Path] = None
    
    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._setup_logger()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """获取Logger单例实例
        
        Returns:
            Logger实例
        """
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    @classmethod
    def _setup_logger(cls):
        """设置日志记录器

        配置日志记录器的输出格式、日志级别和输出文件。
        """
        if cls._logger is None:
            cls._logger = logging.getLogger('StreamDock')
            cls._logger.setLevel(logging.INFO)
            cls._memory_handler = MemoryLogHandler()
            cls._secret_filter = SecretMaskingFilter(drawflow_tokens)
            cls._add_handler(cls._memory_handler)
            cls._add_handler(logging.StreamHandler())

            # 获取日志目录路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                base_path = os.path.join(os.path.dirname(sys.executable), 'logs')
            else:
                # 如果是开发环境
                base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

            log_file = os.path.join(base_path, 'plugin.log')
            try:
                os.makedirs(base_path, exist_ok=True)
                cls._add_handler(logging.FileHandler(log_file, encoding='utf-8'))
                cls._log_file = Path(log_file)
            except OSError as e:
                cls._logger.error(f"Failed to setup file handler: {e}")

    @classmethod
    def _add_handler(cls, handler: logging.Handler) -> None:
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.addFilter(cls._secret_filter)
        cls._logger.addHandler(handler)

    @classmethod
    def memory(cls) -> MemoryLogHandler:
        cls.get_logger()
        return cls._memory_handler

    @classmethod
    def log_file(cls) -> Optional[Path]:
        cls.get_logger()
        return cls._log_file

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """获取日志记录器实例
        
        Returns:
            配置好的日志记录器实例
        """
        if cls._logger is None:
            cls._setup_logger()
        return cls._logger
    
    @classmethod
    def info(cls, message: str):
        """记录INFO级别的日志
        
        Args:
            message: 日志消息
        """
        cls.get_instance().get_logger().info(message)
    
    @classmethod
    def error(cls, message: str):
        """记录ERROR级别的日志
        
        Args:
            message: 日志消息
        """
        cls.get_instance().get_logger().error(message)
    
    @classmethod
    def warning(cls, message: str):
        """记录WARNING级别的日志
        
        Args:
            message: 日志消息
        """
        cls.get_instance().get_logger().warning(message)
    
    @classmethod
    def debug(cls, message: str):
        """记录DEBUG级别的日志
        
        Args:
            message: 日志消息
        """
        cls.get_instance().get_logger().debug(message)