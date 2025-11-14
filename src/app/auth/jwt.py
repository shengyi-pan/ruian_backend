"""
JWT token 生成和验证
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import get_config

config = get_config()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间增量，如果为 None 则使用配置中的默认值

    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=config.jwt.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.jwt.secret_key, algorithm=config.jwt.algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码访问令牌

    Args:
        token: JWT token

    Returns:
        Optional[dict]: 解码后的数据，如果解码失败则返回 None
    """
    try:
        payload = jwt.decode(
            token, config.jwt.secret_key, algorithms=[config.jwt.algorithm]
        )
        return payload
    except JWTError:
        return None

