"""
用户模型
包括 Pydantic 模型和 SQLAlchemy ORM 模型
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


# ==================== SQLAlchemy ORM 模型 ====================
class UserDB(Base):
    """用户数据库模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ==================== Pydantic 模型 ====================
class UserBase(BaseModel):
    """用户基础模型"""

    username: str = Field(..., min_length=1, max_length=50)


class UserCreate(UserBase):
    """创建用户模型"""

    password: str = Field(..., min_length=6)


class UserInDB(UserBase):
    """数据库中的用户模型（包含敏感信息）"""

    id: int
    password_hash: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class User(UserBase):
    """用户响应模型（不包含敏感信息）"""

    id: int = Field(..., description="用户 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "admin",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        },
    }


class UserLogin(BaseModel):
    """用户登录模型"""

    username: str = Field(..., description="用户名", min_length=1, max_length=50)
    password: str = Field(..., description="密码", min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "admin",
                "password": "password123",
            }
        }
    }
