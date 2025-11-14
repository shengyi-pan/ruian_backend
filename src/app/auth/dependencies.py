"""
FastAPI 依赖注入
用于认证和授权
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.config import get_config
from app.database import get_db
from app.exceptions import AuthenticationError, AuthorizationError
from app.model.user import User, UserDB

config = get_config()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    从 Authorization header 中获取当前用户

    Args:
        authorization: Authorization header 值（格式：Bearer <token>）
        db: 数据库会话

    Returns:
        User: 当前用户

    Raises:
        AuthenticationError: 如果认证失败
    """
    if not authorization:
        raise AuthenticationError("缺少认证信息")

    # 提取 token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("认证方案必须是 Bearer")
    except ValueError:
        raise AuthenticationError("认证信息格式错误，应为: Bearer <token>")

    # 解码 token
    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationError("无效的 token")

    # 从 payload 中获取用户名
    username: str = payload.get("sub")
    if username is None:
        raise AuthenticationError("token 中缺少用户信息")

    # 从数据库获取用户
    user_db = db.query(UserDB).filter(UserDB.username == username).first()
    if user_db is None:
        raise AuthenticationError("用户不存在")

    return User.model_validate(user_db)


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    验证 API Key（用于某些需要 API Key 的接口）

    Args:
        x_api_key: API Key header 值

    Returns:
        bool: 验证结果

    Raises:
        AuthorizationError: 如果 API Key 无效
    """
    if not x_api_key:
        raise AuthorizationError("缺少 API Key")

    if x_api_key != config.api.api_key:
        raise AuthorizationError("无效的 API Key")

    return True

