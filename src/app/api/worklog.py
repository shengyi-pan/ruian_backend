"""
员工工作量查询 API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.model.employee_worklog import EmployeeWorklog, EmployeeWorklogDB
from app.model.user import User

router = APIRouter(prefix="/api/worklog", tags=["worklog"])


class EmployeeWorklogResponse(BaseModel):
    """员工工作量响应模型"""

    id: int
    order_no: str
    model: Optional[str]
    brand_no: Optional[str]
    employee_id: str
    employee_name: Optional[str]
    job_type: str
    quantity: int
    performance_factor: float
    performance_amount: float
    work_date: datetime
    upload_date: datetime
    validation_result: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeWorklogListResponse(BaseModel):
    """员工工作量列表响应模型"""

    total: int
    page: int
    page_size: int
    items: List[EmployeeWorklogResponse]


@router.get("", response_model=EmployeeWorklogListResponse)
async def get_employee_worklog(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    order_no: Optional[str] = Query(None, description="订单号（模糊匹配）"),
    start_date: Optional[datetime] = Query(
        None, description="开始日期（基于 work_date）"
    ),
    end_date: Optional[datetime] = Query(
        None, description="结束日期（基于 work_date）"
    ),
    employee_id: Optional[str] = Query(None, description="员工工号"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询员工工作量（支持分页、订单号、日期、员工工号过滤）

    Args:
        page: 页码
        page_size: 每页数量
        order_no: 订单号（可选，模糊匹配）
        start_date: 开始日期（可选，基于 work_date）
        end_date: 结束日期（可选，基于 work_date）
        employee_id: 员工工号（可选）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        EmployeeWorklogListResponse: 员工工作量列表
    """
    # 构建查询
    query = db.query(EmployeeWorklogDB)

    # 订单号过滤
    if order_no:
        query = query.filter(EmployeeWorklogDB.order_no.contains(order_no))

    # 日期范围过滤
    if start_date:
        query = query.filter(EmployeeWorklogDB.work_date >= start_date)
    if end_date:
        query = query.filter(EmployeeWorklogDB.work_date <= end_date)

    # 员工工号过滤
    if employee_id:
        query = query.filter(EmployeeWorklogDB.employee_id == employee_id)

    # 获取总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = (
        query.order_by(EmployeeWorklogDB.work_date.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return EmployeeWorklogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EmployeeWorklogResponse.model_validate(item) for item in items],
    )


@router.get("/{order_no}", response_model=List[EmployeeWorklogResponse])
async def get_employee_worklog_by_order_no(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按订单号查询员工工作量

    Args:
        order_no: 订单号
        current_user: 当前用户
        db: 数据库会话

    Returns:
        List[EmployeeWorklogResponse]: 员工工作量列表
    """
    items = (
        db.query(EmployeeWorklogDB)
        .filter(EmployeeWorklogDB.order_no == order_no)
        .order_by(EmployeeWorklogDB.work_date.desc())
        .all()
    )

    return [EmployeeWorklogResponse.model_validate(item) for item in items]
