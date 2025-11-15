"""
认证相关 API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.config import get_config
from app.database import get_db
from app.exceptions import AuthenticationError
from app.model.user import User, UserDB, UserLogin
from app.schemas.error import (
    AuthenticationErrorResponse,
    InternalServerErrorResponse,
    ValidationErrorResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/login",
    response_model=dict,
    summary="用户登录",
    description="使用用户名和密码登录，获取访问令牌（JWT Token）。",
    response_description="返回包含 access_token 和 token_type 的响应",
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        422: {
            "description": "请求参数验证失败",
            "model": ValidationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db),
):
    """
    用户登录接口

    使用用户名和密码进行身份验证，成功后返回 JWT Token。
    后续请求需要在请求头中携带此 Token：`Authorization: Bearer <token>`

    Args:
        user_login: 登录信息，包含用户名和密码
        db: 数据库会话

    Returns:
        dict: 包含以下字段：
            - access_token (str): JWT 访问令牌
            - token_type (str): 令牌类型，固定为 "bearer"
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


@router.get(
    "/me",
    response_model=User,
    summary="获取当前用户信息",
    description="获取当前已认证用户的基本信息。需要 Bearer Token 认证。",
    response_description="返回当前用户的信息",
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "admin",
                        "created_at": "2025-01-01T00:00:00Z",
                        "updated_at": "2025-01-01T00:00:00Z",
                    }
                }
            },
        },
        401: {
            "description": "认证失败，Token 无效或已过期",
            "model": AuthenticationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息

    通过 JWT Token 获取当前已认证用户的基本信息。
    此接口需要认证，请在请求头中携带有效的 Bearer Token。

    Args:
        current_user: 当前用户（通过依赖注入获取，已通过认证）

    Returns:
        User: 当前用户信息，包含：
            - id (int): 用户 ID
            - username (str): 用户名
            - created_at (datetime): 创建时间
            - updated_at (datetime): 更新时间
    """
    return current_user
