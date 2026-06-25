"""
配置加载模块 - 负责读取和验证配置文件
"""
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml


class Config:
    """配置管理类"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = "config.yaml") -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        self._validate_config()
        self._create_directories()

        return self._config

    def _validate_config(self) -> None:
        """验证配置文件的完整性"""
        required_sections = ['llm', 'server', 'storage']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"配置文件缺少必要配置节: {section}")

        # 验证 LLM 配置
        llm_config = self._config.get('llm', {})
        if not llm_config.get('api_key'):
            raise ValueError("LLM API 密钥未配置")
        if not llm_config.get('base_url'):
            raise ValueError("LLM API 基础 URL 未配置")

        # 验证存储配置
        storage_config = self._config.get('storage', {})
        if not storage_config.get('upload_dir'):
            raise ValueError("上传目录未配置")
        if not storage_config.get('output_dir'):
            raise ValueError("输出目录未配置")

    def _create_directories(self) -> None:
        """创建必要的目录"""
        storage_config = self._config.get('storage', {})

        directories = [
            storage_config.get('upload_dir', 'uploads'),
            storage_config.get('output_dir', 'outputs')
        ]

        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，如 'llm.api_key'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_llm_config(self) -> Dict[str, Any]:
        """获取 LLM 配置"""
        return self._config.get('llm', {})

    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self._config.get('server', {})

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self._config.get('storage', {})


def load_config(config_path: str = "config.yaml") -> Config:
    """
    加载配置的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config 实例
    """
    config = Config()
    config.load(config_path)
    return config
