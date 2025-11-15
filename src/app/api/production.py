"""
生产信息查询 API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.model.production_info import ProductionInfo, ProductionInfoDB
from app.model.user import User
from app.schemas.error import (
    AuthenticationErrorResponse,
    InternalServerErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
)

router = APIRouter(prefix="/api/production", tags=["production"])
security = HTTPBearer()


class ProductionInfoResponse(BaseModel):
    """生产信息响应模型"""

    id: int = Field(..., description="记录 ID")
    order_no: str = Field(..., description="订单号")
    model: str = Field(..., description="型号")
    brand_no: str = Field(..., description="品牌编号")
    quantity: int = Field(..., description="数量")
    job_type: str = Field(..., description="作业类型")
    worklog_no: str = Field(..., description="工作量编号")
    performance_factor: float = Field(..., description="绩效系数")
    upload_date: datetime = Field(..., description="上传日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "order_no": "ORD20250101001",
                "model": "MODEL-A",
                "brand_no": "BRAND-001",
                "quantity": 100,
                "job_type": "组装",
                "worklog_no": "WL001",
                "performance_factor": 1.2,
                "upload_date": "2025-01-01T00:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        },
    }


class ProductionInfoListResponse(BaseModel):
    """生产信息列表响应模型"""

    total: int
    page: int
    page_size: int
    items: List[ProductionInfoResponse]


@router.get(
    "",
    response_model=ProductionInfoListResponse,
    summary="查询生产信息列表",
    description="分页查询生产信息，支持按订单号、日期范围等条件过滤。需要 Bearer Token 认证。",
    response_description="返回生产信息列表，包含总数和分页信息",
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "example": {
                        "total": 100,
                        "page": 1,
                        "page_size": 10,
                        "items": [
                            {
                                "id": 1,
                                "order_no": "ORD20250101001",
                                "model": "MODEL-A",
                                "brand_no": "BRAND-001",
                                "quantity": 100,
                                "job_type": "组装",
                                "worklog_no": "WL001",
                                "performance_factor": 1.2,
                                "upload_date": "2025-01-01T00:00:00Z",
                                "created_at": "2025-01-01T00:00:00Z",
                                "updated_at": "2025-01-01T00:00:00Z",
                            }
                        ],
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
async def get_production_info(
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(
        10, ge=1, le=100, description="每页数量，最大 100", example=10
    ),
    order_no: Optional[str] = Query(
        None, description="订单号（模糊匹配）", example="ORD20250101"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="开始日期（基于 upload_date），格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-01T00:00:00",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="结束日期（基于 upload_date），格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-31T23:59:59",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询生产信息列表

    支持分页查询和多种过滤条件：
    - 分页：通过 page 和 page_size 参数控制
    - 订单号过滤：支持模糊匹配
    - 日期范围过滤：基于 upload_date 字段

    Args:
        page: 页码，从 1 开始，默认 1
        page_size: 每页数量，范围 1-100，默认 10
        order_no: 订单号（可选），支持模糊匹配
        start_date: 开始日期（可选），基于 upload_date 字段
        end_date: 结束日期（可选），基于 upload_date 字段
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        ProductionInfoListResponse: 包含以下字段：
            - total (int): 总记录数
            - page (int): 当前页码
            - page_size (int): 每页数量
            - items (List[ProductionInfoResponse]): 生产信息列表
    """
    # 构建查询
    query = db.query(ProductionInfoDB)

    # 订单号过滤
    if order_no:
        query = query.filter(ProductionInfoDB.order_no.contains(order_no))

    # 日期范围过滤
    if start_date:
        query = query.filter(ProductionInfoDB.upload_date >= start_date)
    if end_date:
        query = query.filter(ProductionInfoDB.upload_date <= end_date)

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = (
        query.order_by(ProductionInfoDB.upload_date.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return ProductionInfoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductionInfoResponse.model_validate(item) for item in items],
    )


@router.get(
    "/{order_no}",
    response_model=List[ProductionInfoResponse],
    summary="按订单号查询生产信息",
    description="根据订单号精确查询所有相关的生产信息记录。需要 Bearer Token 认证。",
    response_description="返回该订单号下的所有生产信息记录",
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "order_no": "ORD20250101001",
                            "model": "MODEL-A",
                            "brand_no": "BRAND-001",
                            "quantity": 100,
                            "job_type": "组装",
                            "worklog_no": "WL001",
                            "performance_factor": 1.2,
                            "upload_date": "2025-01-01T00:00:00Z",
                            "created_at": "2025-01-01T00:00:00Z",
                            "updated_at": "2025-01-01T00:00:00Z",
                        }
                    ]
                }
            },
        },
        401: {
            "description": "认证失败",
            "model": AuthenticationErrorResponse,
        },
        404: {
            "description": "订单号不存在",
            "model": NotFoundErrorResponse,
        },
        500: {
            "description": "服务器内部错误",
            "model": InternalServerErrorResponse,
        },
    },
    dependencies=[Depends(security)],
)
async def get_production_info_by_order_no(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按订单号查询生产信息

    根据订单号精确查询所有相关的生产信息记录，按上传日期倒序排列。

    Args:
        order_no: 订单号（路径参数）
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        List[ProductionInfoResponse]: 该订单号下的所有生产信息记录列表
    """
    items = (
        db.query(ProductionInfoDB)
        .filter(ProductionInfoDB.order_no == order_no)
        .order_by(ProductionInfoDB.upload_date.desc())
        .all()
    )

    return [ProductionInfoResponse.model_validate(item) for item in items]
