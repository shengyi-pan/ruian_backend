"""
数据核验 API
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import ValidationError
from app.model.employee_worklog import EmployeeWorklog, EmployeeWorklogDB
from app.model.production_info import ProductionInfo, ProductionInfoDB
from app.model.user import User
from app.utils.data_vld import VldResultEnum, validate_production_and_worklog

router = APIRouter(prefix="/api/validation", tags=["validation"])


class ValidationRequest(BaseModel):
    """数据核验请求模型"""

    start_date: datetime
    end_date: datetime


class ValidationExceptionItem(BaseModel):
    """异常数据项"""

    order_no: str
    exception_type: str
    worklogs: List[Dict]


class ValidationNormalItem(BaseModel):
    """正常数据项"""

    order_no: str
    worklogs: List[Dict]


class ValidationResponse(BaseModel):
    """数据核验响应模型"""

    total_production_records: int
    total_worklog_records: int
    exception_count: int
    normal_count: int
    exceptions: List[ValidationExceptionItem]
    normal: List[ValidationNormalItem]


@router.post("/check", response_model=ValidationResponse)
async def validate_data(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    数据核验接口
    限定时间范围做数据核验

    Args:
        request: 核验请求（包含时间范围）
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ValidationResponse: 核验结果
    """
    # 验证时间范围
    if request.start_date > request.end_date:
        raise ValidationError("开始日期不能晚于结束日期")

    # 从数据库查询时间范围内的 production_info
    production_info_list = (
        db.query(ProductionInfoDB)
        .filter(
            ProductionInfoDB.upload_date >= request.start_date,
            ProductionInfoDB.upload_date <= request.end_date,
        )
        .all()
    )

    # 从数据库查询时间范围内的 employee_worklog
    employee_worklog_list = (
        db.query(EmployeeWorklogDB)
        .filter(
            EmployeeWorklogDB.work_date >= request.start_date,
            EmployeeWorklogDB.work_date <= request.end_date,
        )
        .all()
    )

    # 转换为 Pydantic 模型
    production_info_models = []
    for item in production_info_list:
        production_info_models.append(
            ProductionInfo(
                id=item.id,
                order_no=item.order_no,
                model=item.model,
                brand_no=item.brand_no,
                quantity=item.quantity,
                job_type=item.job_type,
                performance_factor=float(item.performance_factor),
                upload_date=item.upload_date,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    employee_worklog_models = []
    for item in employee_worklog_list:
        employee_worklog_models.append(
            EmployeeWorklog(
                id=item.id,
                order_no=item.order_no,
                model=item.model,
                brand_no=item.brand_no,
                employee_id=item.employee_id,
                employee_name=item.employee_name,
                job_type=item.job_type,
                quantity=item.quantity,
                performance_factor=float(item.performance_factor),
                performance_amount=float(item.performance_amount),
                work_date=item.work_date,
                upload_date=item.upload_date,
                validation_result=item.validation_result,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    # 调用校验函数（会更新每个 worklog 的 validation_result）
    exception_result, normal_result = validate_production_and_worklog(
        production_info_models, employee_worklog_models
    )

    # 将所有更新后的 worklog 保存回数据库
    from app.utils.db_utils import upsert_employee_worklog

    all_worklogs = []
    for worklog_list in exception_result.values():
        all_worklogs.extend(worklog_list)
    for worklog_list in normal_result.values():
        all_worklogs.extend(worklog_list)
    if all_worklogs:
        upsert_employee_worklog(db, all_worklogs)

    # 构建响应
    exceptions = []
    for (order_no, except_enum), worklog_list in exception_result.items():
        exceptions.append(
            ValidationExceptionItem(
                order_no=order_no,
                exception_type=except_enum.value,
                worklogs=[worklog.model_dump() for worklog in worklog_list],
            )
        )

    normal = []
    for order_no, worklog_list in normal_result.items():
        normal.append(
            ValidationNormalItem(
                order_no=order_no,
                worklogs=[worklog.model_dump() for worklog in worklog_list],
            )
        )

    return ValidationResponse(
        total_production_records=len(production_info_models),
        total_worklog_records=len(employee_worklog_models),
        exception_count=len(exceptions),
        normal_count=len(normal),
        exceptions=exceptions,
        normal=normal,
    )
