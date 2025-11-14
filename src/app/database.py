"""
Author: sy.pan
Date: 2025-11-14 11:20:44
LastEditors: sy.pan
LastEditTime: 2025-11-14 14:45:12
FilePath: /ruian_backend/src/app/database.py
Description:

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

"""
数据库连接模块
使用 SQLAlchemy 管理数据库连接和会话
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_config

config = get_config()

# 创建数据库引擎
engine = create_engine(
    config.database.database_url,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    pool_timeout=config.database.pool_timeout,
    echo=config.app.debug,  # 在调试模式下打印 SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类，所有 ORM 模型都继承自此类
Base = declarative_base()


def get_db():
    """
    获取数据库会话（依赖注入）

    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库（创建所有表）
    """
    Base.metadata.create_all(bind=engine)


def main():
    """
    测试数据库连接
    """
    try:
        # 尝试连接数据库
        with engine.connect() as connection:
            # 执行一个简单的查询来测试连接
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("✓ 数据库连接成功！")
            print(
                f"  数据库URL: {config.database.database_url.split('@')[1] if '@' in config.database.database_url else '已配置'}"
            )

            # 获取数据库版本信息
            if engine.dialect.name == "postgresql":
                version_result = connection.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                print(f"  数据库版本: {version.split(',')[0]}")

    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        raise


if __name__ == "__main__":
    main()
