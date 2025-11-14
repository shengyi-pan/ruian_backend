"""
生产信息查询 API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.model.production_info import ProductionInfo
from app.model.production_info import ProductionInfoDB
from app.model.user import User

router = APIRouter(prefix="/api/production", tags=["production"])


class ProductionInfoResponse(BaseModel):
    """生产信息响应模型"""

    id: int
    order_no: str
    model: str
    brand_no: str
    quantity: int
    job_type: str
    performance_factor: float
    upload_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductionInfoListResponse(BaseModel):
    """生产信息列表响应模型"""

    total: int
    page: int
    page_size: int
    items: List[ProductionInfoResponse]


@router.get("", response_model=ProductionInfoListResponse)
async def get_production_info(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    order_no: Optional[str] = Query(None, description="订单号（模糊匹配）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询生产信息（支持分页、订单号、日期过滤）

    Args:
        page: 页码
        page_size: 每页数量
        order_no: 订单号（可选，模糊匹配）
        start_date: 开始日期（可选，基于 upload_date）
        end_date: 结束日期（可选，基于 upload_date）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ProductionInfoListResponse: 生产信息列表
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
    items = query.order_by(ProductionInfoDB.upload_date.desc()).offset(offset).limit(page_size).all()

    return ProductionInfoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProductionInfoResponse.model_validate(item) for item in items],
    )


@router.get("/{order_no}", response_model=List[ProductionInfoResponse])
async def get_production_info_by_order_no(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按订单号查询生产信息

    Args:
        order_no: 订单号
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[ProductionInfoResponse]: 生产信息列表
    """
    items = (
        db.query(ProductionInfoDB)
        .filter(ProductionInfoDB.order_no == order_no)
        .order_by(ProductionInfoDB.upload_date.desc())
        .all()
    )

    return [ProductionInfoResponse.model_validate(item) for item in items]

