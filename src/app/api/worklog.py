"""
员工工作量查询 API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.model.employee_worklog import EmployeeWorklog, EmployeeWorklogDB
from app.model.user import User
from app.schemas.error import (
    AuthenticationErrorResponse,
    InternalServerErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
)

router = APIRouter(prefix="/api/worklog", tags=["worklog"])
security = HTTPBearer()


class EmployeeWorklogResponse(BaseModel):
    """员工工作量响应模型"""

    id: int = Field(..., description="记录 ID")
    order_no: str = Field(..., description="订单号")
    model: Optional[str] = Field(None, description="型号")
    brand_no: Optional[str] = Field(None, description="品牌编号")
    employee_id: str = Field(..., description="员工工号")
    employee_name: Optional[str] = Field(None, description="员工姓名")
    job_type: str = Field(..., description="作业类型")
    quantity: int = Field(..., description="数量")
    performance_factor: float = Field(..., description="绩效系数")
    performance_amount: float = Field(..., description="绩效金额")
    work_date: datetime = Field(..., description="工作日期")
    upload_date: datetime = Field(..., description="上传日期")
    validation_result: str = Field(..., description="核验结果")
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
                "employee_id": "EMP001",
                "employee_name": "张三",
                "job_type": "组装",
                "quantity": 50,
                "performance_factor": 1.2,
                "performance_amount": 1200.0,
                "work_date": "2025-01-01T00:00:00Z",
                "upload_date": "2025-01-01T00:00:00Z",
                "validation_result": "正常",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        },
    }


class EmployeeWorklogListResponse(BaseModel):
    """员工工作量列表响应模型"""

    total: int
    page: int
    page_size: int
    items: List[EmployeeWorklogResponse]


@router.get(
    "",
    response_model=EmployeeWorklogListResponse,
    summary="查询员工工作量列表",
    description="分页查询员工工作量，支持按订单号、日期范围、员工工号等条件过滤。需要 Bearer Token 认证。",
    response_description="返回员工工作量列表，包含总数和分页信息",
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
                                "employee_id": "EMP001",
                                "employee_name": "张三",
                                "job_type": "组装",
                                "quantity": 50,
                                "performance_factor": 1.2,
                                "performance_amount": 1200.0,
                                "work_date": "2025-01-01T00:00:00Z",
                                "upload_date": "2025-01-01T00:00:00Z",
                                "validation_result": "正常",
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
async def get_employee_worklog(
    page: int = Query(1, ge=1, description="页码，从 1 开始", example=1),
    page_size: int = Query(
        10, ge=1, le=100, description="每页数量，最大 100", example=10
    ),
    order_no: Optional[str] = Query(
        None, description="订单号（模糊匹配）", example="ORD20250101"
    ),
    start_date: Optional[datetime] = Query(
        None,
        description="开始日期（基于 work_date），格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-01T00:00:00",
    ),
    end_date: Optional[datetime] = Query(
        None,
        description="结束日期（基于 work_date），格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-31T23:59:59",
    ),
    employee_id: Optional[str] = Query(
        None, description="员工工号（精确匹配）", example="EMP001"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    查询员工工作量列表

    支持分页查询和多种过滤条件：
    - 分页：通过 page 和 page_size 参数控制
    - 订单号过滤：支持模糊匹配
    - 日期范围过滤：基于 work_date 字段
    - 员工工号过滤：精确匹配

    Args:
        page: 页码，从 1 开始，默认 1
        page_size: 每页数量，范围 1-100，默认 10
        order_no: 订单号（可选），支持模糊匹配
        start_date: 开始日期（可选），基于 work_date 字段
        end_date: 结束日期（可选），基于 work_date 字段
        employee_id: 员工工号（可选），精确匹配
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        EmployeeWorklogListResponse: 包含以下字段：
            - total (int): 总记录数
            - page (int): 当前页码
            - page_size (int): 每页数量
            - items (List[EmployeeWorklogResponse]): 员工工作量列表
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


@router.get(
    "/{order_no}",
    response_model=List[EmployeeWorklogResponse],
    summary="按订单号查询员工工作量",
    description="根据订单号精确查询所有相关的员工工作量记录。需要 Bearer Token 认证。",
    response_description="返回该订单号下的所有员工工作量记录",
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
                            "employee_id": "EMP001",
                            "employee_name": "张三",
                            "job_type": "组装",
                            "quantity": 50,
                            "performance_factor": 1.2,
                            "performance_amount": 1200.0,
                            "work_date": "2025-01-01T00:00:00Z",
                            "upload_date": "2025-01-01T00:00:00Z",
                            "validation_result": "正常",
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
async def get_employee_worklog_by_order_no(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    按订单号查询员工工作量

    根据订单号精确查询所有相关的员工工作量记录，按工作日期倒序排列。

    Args:
        order_no: 订单号（路径参数）
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        List[EmployeeWorklogResponse]: 该订单号下的所有员工工作量记录列表
    """
    items = (
        db.query(EmployeeWorklogDB)
        .filter(EmployeeWorklogDB.order_no == order_no)
        .order_by(EmployeeWorklogDB.work_date.desc())
        .all()
    )

    return [EmployeeWorklogResponse.model_validate(item) for item in items]
