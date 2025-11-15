"""
数据核验 API
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.exceptions import ValidationError
from app.model.employee_worklog import EmployeeWorklog, EmployeeWorklogDB
from app.model.production_info import ProductionInfo, ProductionInfoDB
from app.model.user import User
from app.schemas.error import (
    AuthenticationErrorResponse,
    InternalServerErrorResponse,
    ValidationErrorResponse,
)
from app.utils.data_vld import validate_production_and_worklog
from app.utils.enums import VldResultEnum

router = APIRouter(prefix="/api/validation", tags=["validation"])
security = HTTPBearer()


class ValidationRequest(BaseModel):
    """数据核验请求模型"""

    start_date: datetime = Field(
        ...,
        description="开始日期，格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-01T00:00:00",
    )
    end_date: datetime = Field(
        ...,
        description="结束日期，格式：YYYY-MM-DDTHH:MM:SS",
        example="2025-01-31T23:59:59",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-01-31T23:59:59",
            }
        }
    }


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

    total_production_records: int = Field(..., description="生产信息总记录数")
    total_worklog_records: int = Field(..., description="员工工作量总记录数")
    exception_count: int = Field(..., description="异常数据项数量")
    normal_count: int = Field(..., description="正常数据项数量")
    exceptions: List[ValidationExceptionItem] = Field(..., description="异常数据列表")
    normal: List[ValidationNormalItem] = Field(..., description="正常数据列表")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_production_records": 100,
                "total_worklog_records": 200,
                "exception_count": 5,
                "normal_count": 95,
                "exceptions": [
                    {
                        "order_no": "ORD20250101001",
                        "exception_type": "数量不匹配",
                        "worklogs": [
                            {
                                "id": 1,
                                "order_no": "ORD20250101001",
                                "employee_id": "EMP001",
                                "quantity": 50,
                            }
                        ],
                    }
                ],
                "normal": [
                    {
                        "order_no": "ORD20250101002",
                        "worklogs": [
                            {
                                "id": 2,
                                "order_no": "ORD20250101002",
                                "employee_id": "EMP002",
                                "quantity": 100,
                            }
                        ],
                    }
                ],
            }
        }
    }


@router.post(
    "/check",
    response_model=ValidationResponse,
    summary="数据核验",
    description="在指定时间范围内核验生产信息和员工工作量数据的一致性。需要 Bearer Token 认证。",
    response_description="返回核验结果，包含正常和异常数据列表",
    responses={
        200: {
            "description": "核验成功",
            "content": {
                "application/json": {
                    "example": {
                        "total_production_records": 100,
                        "total_worklog_records": 200,
                        "exception_count": 5,
                        "normal_count": 95,
                        "exceptions": [
                            {
                                "order_no": "ORD20250101001",
                                "exception_type": "数量不匹配",
                                "worklogs": [],
                            }
                        ],
                        "normal": [
                            {
                                "order_no": "ORD20250101002",
                                "worklogs": [],
                            }
                        ],
                    }
                }
            },
        },
        400: {
            "description": "请求参数错误（如开始日期晚于结束日期）",
            "model": ValidationErrorResponse,
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
async def validate_data(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    数据核验接口

    在指定时间范围内核验生产信息和员工工作量数据的一致性。
    核验规则包括：
    - 订单号匹配
    - 数量一致性
    - 其他业务规则

    核验结果会更新到员工工作量记录的 validation_result 字段。

    Args:
        request: 核验请求，包含：
            - start_date (datetime): 开始日期
            - end_date (datetime): 结束日期
        current_user: 当前用户（通过依赖注入获取）
        db: 数据库会话

    Returns:
        ValidationResponse: 核验结果，包含：
            - total_production_records (int): 生产信息总记录数
            - total_worklog_records (int): 员工工作量总记录数
            - exception_count (int): 异常数据项数量
            - normal_count (int): 正常数据项数量
            - exceptions (List[ValidationExceptionItem]): 异常数据列表
            - normal (List[ValidationNormalItem]): 正常数据列表
    """
    # 验证时间范围
    if request.start_date > request.end_date:
        raise ValidationError("开始日期不能晚于结束日期")

    # 从数据库查询时间范围内的 production_info
    production_info_list = (
        db.query(ProductionInfoDB)
        .filter(
            ProductionInfoDB.created_at >= request.start_date,
            ProductionInfoDB.created_at <= request.end_date,
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
                worklog_no=item.worklog_no,
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
