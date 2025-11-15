"""
文件上传 API
支持本地存储和阿里云 OSS 两种方式
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import ValidationError
from app.model.user import User
from app.schemas.error import (
    AuthenticationErrorResponse,
    InternalServerErrorResponse,
    ValidationErrorResponse,
)
from app.services.oss_service import get_oss_service
from app.services.upload_service import get_upload_service

router = APIRouter(prefix="/api/upload", tags=["upload"])
security = HTTPBearer()


# ==================== 请求模型 ====================
class ProductionOSSUploadRequest(BaseModel):
    """生产信息 OSS 上传请求"""

    object_key: str = Field(
        ...,
        description="OSS 对象键(文件路径)",
        example="uploads/production/2025/01/production_info.xlsx",
    )
    filter_month: Optional[str] = Field(
        None, description="月份过滤,格式:yyyyMM", example="202501"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "object_key": "uploads/production/2025/01/production_info.xlsx",
                "filter_month": "202501",
            }
        }
    }


class WorklogOSSUploadRequest(BaseModel):
    """员工工作量 OSS 上传请求"""

    object_key: str = Field(
        ...,
        description="OSS 对象键(文件路径)",
        example="uploads/worklog/2025/01/worklog_202501.xlsx",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "object_key": "uploads/worklog/2025/01/worklog_202501.xlsx",
            }
        }
    }


@router.post(
    "/production/local",
    summary="本地方式上传生产信息",
    description="通过表单上传 Excel 文件到本地存储，并解析保存到数据库。需要 Bearer Token 认证。",
    response_description="返回上传结果，包含文件名、保存路径和处理记录数",
    responses={
        200: {
            "description": "上传成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "上传成功",
                        "filename": "production_info.xlsx",
                        "saved_path": "uploads/production_info_20250101_123456.xlsx",
                        "records_processed": 150,
                    }
                }
            },
        },
        400: {
            "description": "文件类型不支持或文件格式错误",
            "model": ValidationErrorResponse,
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def upload_production_local(
    file: UploadFile = File(..., description="Excel 文件（.xlsx 或 .xls 格式）"),
    filter_month: Optional[str] = Form(
        None, description="月份过滤,格式:yyyyMM", example="202501"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    本地存储方式上传生产信息 Excel

    上传 Excel 文件到本地存储目录，解析文件内容并保存到数据库。
    支持月份过滤，只处理指定月份的数据。

    Args:
        file: 上传的 Excel 文件，必须是 .xlsx 或 .xls 格式
        filter_month: 月份过滤参数（可选），格式：yyyyMM，例如：202501
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        dict: 包含以下字段：
            - message (str): 操作结果消息
            - filename (str): 原始文件名
            - saved_path (str): 保存的文件路径
            - records_processed (int): 处理的记录数
    """
    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise ValidationError("只支持 Excel 文件(.xlsx, .xls)")

    upload_service = get_upload_service()

    # 读取文件内容
    file_content = await file.read()

    # 保存文件
    saved_path = upload_service.save_uploaded_file(file_content, file.filename)

    # 解析并保存到数据库
    count, _ = upload_service.parse_and_save_production_info(
        saved_path, db, filter_month
    )

    return {
        "message": "上传成功",
        "filename": file.filename,
        "saved_path": saved_path,
        "records_processed": count,
    }


@router.post(
    "/production/oss",
    summary="OSS 方式上传生产信息",
    description="处理已上传到阿里云 OSS 的生产信息 Excel 文件，下载并解析保存到数据库。需要 Bearer Token 认证。",
    response_description="返回处理结果，包含 OSS 对象键和处理记录数",
    responses={
        200: {
            "description": "处理成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "处理成功",
                        "object_key": "uploads/production/2025/01/production_info.xlsx",
                        "records_processed": 150,
                    }
                }
            },
        },
        400: {
            "description": "OSS 文件不存在或文件格式错误",
            "model": ValidationErrorResponse,
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def upload_production_oss(
    request: ProductionOSSUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    阿里云 OSS 方式上传生产信息 Excel

    前端已上传文件到 OSS，后端根据 object_key 下载文件，解析并保存到数据库。
    支持月份过滤，只处理指定月份的数据。

    Args:
        request: OSS 上传请求，包含：
            - object_key (str): OSS 对象键（文件路径）
            - filter_month (str, optional): 月份过滤，格式：yyyyMM
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        dict: 包含以下字段：
            - message (str): 操作结果消息
            - object_key (str): OSS 对象键
            - records_processed (int): 处理的记录数
    """
    upload_service = get_upload_service()

    # 处理 OSS 文件(下载、解析、入库)
    count, _ = upload_service.handle_oss_upload(
        request.object_key, "production", db, request.filter_month
    )

    return {
        "message": "处理成功",
        "object_key": request.object_key,
        "records_processed": count,
    }


@router.post(
    "/worklog/local",
    summary="本地方式上传员工工作量",
    description="通过表单上传 Excel 文件到本地存储，并解析保存到数据库。需要 Bearer Token 认证。",
    response_description="返回上传结果，包含文件名、保存路径和处理记录数",
    responses={
        200: {
            "description": "上传成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "上传成功",
                        "filename": "worklog_202501.xlsx",
                        "saved_path": "uploads/worklog_202501_20250101_123456.xlsx",
                        "records_processed": 200,
                    }
                }
            },
        },
        400: {
            "description": "文件类型不支持或文件格式错误",
            "model": ValidationErrorResponse,
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def upload_worklog_local(
    file: UploadFile = File(..., description="Excel 文件（.xlsx 或 .xls 格式）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    本地存储方式上传员工工作量 Excel

    上传 Excel 文件到本地存储目录，解析文件内容并保存到数据库。

    Args:
        file: 上传的 Excel 文件，必须是 .xlsx 或 .xls 格式
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        dict: 包含以下字段：
            - message (str): 操作结果消息
            - filename (str): 原始文件名
            - saved_path (str): 保存的文件路径
            - records_processed (int): 处理的记录数
    """
    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise ValidationError("只支持 Excel 文件(.xlsx, .xls)")

    upload_service = get_upload_service()

    # 读取文件内容
    file_content = await file.read()

    # 保存文件
    saved_path = upload_service.save_uploaded_file(file_content, file.filename)

    # 解析并保存到数据库
    count, _ = upload_service.parse_and_save_employee_worklog(saved_path, db)

    return {
        "message": "上传成功",
        "filename": file.filename,
        "saved_path": saved_path,
        "records_processed": count,
    }


@router.post(
    "/worklog/oss",
    summary="OSS 方式上传员工工作量",
    description="处理已上传到阿里云 OSS 的员工工作量 Excel 文件，下载并解析保存到数据库。需要 Bearer Token 认证。",
    response_description="返回处理结果，包含 OSS 对象键和处理记录数",
    responses={
        200: {
            "description": "处理成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "处理成功",
                        "object_key": "uploads/worklog/2025/01/worklog_202501.xlsx",
                        "records_processed": 200,
                    }
                }
            },
        },
        400: {
            "description": "OSS 文件不存在或文件格式错误",
            "model": ValidationErrorResponse,
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def upload_worklog_oss(
    request: WorklogOSSUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    阿里云 OSS 方式上传员工工作量 Excel

    前端已上传文件到 OSS，后端根据 object_key 下载文件，解析并保存到数据库。

    Args:
        request: OSS 上传请求，包含：
            - object_key (str): OSS 对象键（文件路径）
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        dict: 包含以下字段：
            - message (str): 操作结果消息
            - object_key (str): OSS 对象键
            - records_processed (int): 处理的记录数
    """
    upload_service = get_upload_service()

    # 处理 OSS 文件(下载、解析、入库)
    _, count = upload_service.handle_oss_upload(request.object_key, "worklog", db)

    return {
        "message": "处理成功",
        "object_key": request.object_key,
        "records_processed": count,
    }


@router.get(
    "/oss/presigned-url",
    summary="获取 OSS 预签名 URL",
    description="生成阿里云 OSS 的预签名 URL，用于前端直接上传文件到 OSS。需要 Bearer Token 认证。",
    response_description="返回预签名 URL 和相关参数",
    responses={
        200: {
            "description": "获取成功",
            "content": {
                "application/json": {
                    "example": {
                        "presigned_url": "https://bucket.oss-cn-hangzhou.aliyuncs.com/uploads/file.xlsx?Expires=1234567890&OSSAccessKeyId=xxx&Signature=xxx",
                        "object_key": "uploads/file.xlsx",
                        "expires": 3600,
                        "method": "PUT",
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
    dependencies=[Depends(security)],
)
async def get_presigned_url(
    object_key: str = Query(
        ...,
        description="OSS 对象键(文件路径)",
        example="uploads/production/2025/01/file.xlsx",
    ),
    expires: int = Query(
        3600,
        ge=1,
        le=86400,
        description="过期时间(秒),范围 1-86400，默认 1 小时",
        example=3600,
    ),
    method: str = Query("PUT", description="HTTP 方法,默认 PUT", example="PUT"),
    current_user: User = Depends(get_current_user),
):
    """
    获取 OSS 预签名 URL

    生成阿里云 OSS 的预签名 URL，前端可以使用此 URL 直接上传文件到 OSS，无需经过后端服务器。

    Args:
        object_key: OSS 对象键（文件路径），例如：uploads/production/2025/01/file.xlsx
        expires: 过期时间（秒），范围 1-86400，默认 3600（1 小时）
        method: HTTP 方法，默认 PUT，用于上传文件
        current_user: 当前用户（通过依赖注入获取）

    Returns:
        dict: 包含以下字段：
            - presigned_url (str): 预签名 URL
            - object_key (str): OSS 对象键
            - expires (int): 过期时间（秒）
            - method (str): HTTP 方法
    """
    oss_service = get_oss_service()

    # 生成预签名 URL
    url = oss_service.generate_presigned_url(object_key, expires, method)

    return {
        "presigned_url": url,
        "object_key": object_key,
        "expires": expires,
        "method": method,
    }
