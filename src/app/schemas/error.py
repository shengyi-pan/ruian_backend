"""
统一错误响应模型
用于 API 文档中的错误响应示例
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """统一错误响应模型"""

    error: bool = Field(True, description="是否为错误响应")
    message: str = Field(..., description="错误消息")
    detail: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": True,
                    "message": "认证失败",
                    "detail": {},
                },
                {
                    "error": True,
                    "message": "数据验证失败",
                    "detail": {"field": "order_no", "reason": "订单号不能为空"},
                },
            ]
        }
    }


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应模型"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": True,
                "message": "数据验证失败",
                "detail": {"field": "order_no", "reason": "订单号不能为空"},
            }
        }
    }


class AuthenticationErrorResponse(ErrorResponse):
    """认证错误响应模型"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": True,
                "message": "认证失败",
                "detail": {},
            }
        }
    }


class NotFoundErrorResponse(ErrorResponse):
    """资源未找到错误响应模型"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": True,
                "message": "资源未找到",
                "detail": {"resource": "order", "id": "12345"},
            }
        }
    }


class InternalServerErrorResponse(ErrorResponse):
    """服务器内部错误响应模型"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": True,
                "message": "服务器内部错误",
                "detail": {"type": "DatabaseError", "message": "Connection timeout"},
            }
        }
    }

