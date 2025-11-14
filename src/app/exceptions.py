"""
自定义异常类
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """应用基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """认证错误"""

    def __init__(self, message: str = "认证失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, detail=detail)


class AuthorizationError(AppException):
    """授权错误"""

    def __init__(self, message: str = "权限不足", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, detail=detail)


class NotFoundError(AppException):
    """资源未找到错误"""

    def __init__(self, message: str = "资源未找到", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, detail=detail)


class ValidationError(AppException):
    """验证错误"""

    def __init__(self, message: str = "数据验证失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, detail=detail)


class DatabaseError(AppException):
    """数据库错误"""

    def __init__(self, message: str = "数据库操作失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)


class FileUploadError(AppException):
    """文件上传错误"""

    def __init__(self, message: str = "文件上传失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, detail=detail)

