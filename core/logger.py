"""
Logger - 日志系统

提供统一的日志记录功能，支持多级别、多输出。
"""

import logging
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path
import json


class AgentOSLogger:
    """
    Agent OS 日志系统
    
    提供统一的日志记录，支持控制台和文件输出。
    """
    
    _instance: Optional['AgentOSLogger'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if AgentOSLogger._initialized:
            return
        
        self.loggers = {}
        self.log_dir = Path("./logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self._setup_root_logger()
        AgentOSLogger._initialized = True
    
    def _setup_root_logger(self) -> None:
        """设置根日志记录器"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        file_handler = logging.FileHandler(
            self.log_dir / f"agent_os_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 记录器名称
            
        Returns:
            日志记录器
        """
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def set_level(self, level: str) -> None:
        """
        设置日志级别
        
        Args:
            level: 级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        logging.getLogger().setLevel(getattr(logging, level.upper()))
    
    def add_file_handler(self, logger_name: str, filename: str) -> None:
        """
        添加文件处理器
        
        Args:
            logger_name: 日志记录器名称
            filename: 文件名
        """
        logger = self.get_logger(logger_name)
        handler = logging.FileHandler(
            self.log_dir / filename,
            encoding='utf-8'
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentOS")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 名称
        
    Returns:
        日志记录器
    """
    return logging.getLogger(name)
