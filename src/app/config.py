"""
配置管理模块
使用 config.yaml 文件管理所有配置
"""

import os
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """数据库配置"""

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    dbname: str = "ruian_db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    timezone: str = "Asia/Shanghai"  # 数据库时区，默认为中国标准时间（UTC+8）
    set_timezone_on_connect: bool = True  # 是否在应用层设置时区（如果数据库服务端已设置，可设为 False）

    @property
    def database_url(self) -> str:
        """生成数据库连接 URL"""
        # 时区通过 database.py 中的 event listener 设置，不需要在 URL 中指定
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"


class JWTConfig(BaseModel):
    """JWT 配置"""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class APIConfig(BaseModel):
    """API 配置"""

    api_key: str


class LocalUploadConfig(BaseModel):
    """本地文件上传配置"""

    upload_dir: str = "uploads"
    max_file_size_mb: int = 50

    @property
    def max_file_size_bytes(self) -> int:
        """最大文件大小（字节）"""
        return self.max_file_size_mb * 1024 * 1024


class OSSConfig(BaseModel):
    """阿里云 OSS 配置"""

    access_key_id: str
    access_key_secret: str
    endpoint: str
    bucket_name: str
    region: str = "cn-hangzhou"


class UploadConfig(BaseModel):
    """文件上传配置"""

    local: LocalUploadConfig
    oss: OSSConfig


class CORSConfig(BaseModel):
    """CORS 配置"""

    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class AppConfig(BaseModel):
    """应用配置"""

    name: str = "ruian-backend"
    version: str = "0.1.0"
    debug: bool = False


class Config(BaseModel):
    """全局配置"""

    app: AppConfig
    database: DatabaseConfig
    jwt: JWTConfig
    api: APIConfig
    upload: UploadConfig
    cors: CORSConfig


def load_config(config_path: str | Path | None = None) -> Config:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，如果为 None，则从项目根目录查找 config.yaml

    Returns:
        Config: 配置对象
    """
    if config_path is None:
        # 从项目根目录查找 config.yaml
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        config_path = project_root / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)


# 全局配置实例
_config: Config | None = None


def get_config() -> Config:
    """
    获取全局配置实例（单例模式）

    Returns:
        Config: 配置对象
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: str | Path | None = None) -> Config:
    """
    重新加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Config: 配置对象
    """
    global _config
    _config = load_config(config_path)
    return _config

