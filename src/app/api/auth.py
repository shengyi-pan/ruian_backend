"""
认证相关 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.config import get_config
from app.database import get_db
from app.exceptions import AuthenticationError
from app.model.user import User, UserDB, UserLogin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=dict)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db),
):
    """
    用户登录

    Args:
        user_login: 登录信息（用户名和密码）
        db: 数据库会话

    Returns:
        dict: 包含 access_token 和 token_type
    """
    # 查询用户
    user_db = db.query(UserDB).filter(UserDB.username == user_login.username).first()
    if not user_db:
        raise AuthenticationError("用户名或密码错误")

    # 验证密码
    if not verify_password(user_login.password, user_db.password_hash):
        raise AuthenticationError("用户名或密码错误")

    # 生成 token
    access_token = create_access_token(data={"sub": user_db.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    Args:
        current_user: 当前用户（通过依赖注入获取）

    Returns:
        User: 当前用户信息
    """
    return current_user

