"""
文件上传 API
支持本地存储和阿里云 OSS 两种方式
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import ValidationError
from app.model.user import User
from app.services.oss_service import get_oss_service
from app.services.upload_service import get_upload_service

router = APIRouter(prefix="/api/upload", tags=["upload"])


# ==================== 请求模型 ====================
class ProductionOSSUploadRequest(BaseModel):
    """生产信息 OSS 上传请求"""

    object_key: str = Field(..., description="OSS 对象键(文件路径)")
    filter_month: Optional[str] = Field(None, description="月份过滤,格式:yyyyMM")


class WorklogOSSUploadRequest(BaseModel):
    """员工工作量 OSS 上传请求"""

    object_key: str = Field(..., description="OSS 对象键(文件路径)")


@router.post("/production/local")
async def upload_production_local(
    file: UploadFile = File(...),
    filter_month: Optional[str] = Form(None, description="月份过滤,格式:yyyyMM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    本地存储方式上传生产信息 Excel

    Args:
        file: 上传的 Excel 文件
        filter_month: 月份过滤参数(可选)
        current_user: 当前用户
        db: 数据库会话

    Returns:
        dict: 上传结果
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


@router.post("/production/oss")
async def upload_production_oss(
    request: ProductionOSSUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    阿里云 OSS 方式上传生产信息 Excel(前端已上传到 OSS,后端处理入库)

    Args:
        request: OSS 上传请求(包含 object_key 和 filter_month)
        current_user: 当前用户
        db: 数据库会话

    Returns:
        dict: 处理结果
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


@router.post("/worklog/local")
async def upload_worklog_local(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    本地存储方式上传员工工作量 Excel

    Args:
        file: 上传的 Excel 文件
        current_user: 当前用户
        db: 数据库会话

    Returns:
        dict: 上传结果
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


@router.post("/worklog/oss")
async def upload_worklog_oss(
    request: WorklogOSSUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    阿里云 OSS 方式上传员工工作量 Excel(前端已上传到 OSS,后端处理入库)

    Args:
        request: OSS 上传请求(包含 object_key)
        current_user: 当前用户
        db: 数据库会话

    Returns:
        dict: 处理结果
    """
    upload_service = get_upload_service()

    # 处理 OSS 文件(下载、解析、入库)
    _, count = upload_service.handle_oss_upload(request.object_key, "worklog", db)

    return {
        "message": "处理成功",
        "object_key": request.object_key,
        "records_processed": count,
    }


@router.get("/oss/presigned-url")
async def get_presigned_url(
    object_key: str,
    expires: int = 3600,
    method: str = "PUT",
    current_user: User = Depends(get_current_user),
):
    """
    获取 OSS 预签名 URL(用于前端直传)

    Args:
        object_key: OSS 对象键(文件路径)
        expires: 过期时间(秒),默认 1 小时
        method: HTTP 方法,默认 PUT
        current_user: 当前用户

    Returns:
        dict: 预签名 URL
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
