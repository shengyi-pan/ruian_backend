"""
数据库操作辅助函数
包括去重更新逻辑(upsert)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.model.employee_worklog import EmployeeWorklog, EmployeeWorklogDB
from app.model.production_info import ProductionInfo, ProductionInfoDB


def upsert_production_info(
    db: Session, production_info_list: List[ProductionInfo]
) -> int:
    """
    批量插入或更新生产信息(去重更新)

    去重规则 order_no + model + brand_no + job_type + upload_date

    Args:
        db: 数据库会话
        production_info_list: 生产信息列表

    Returns:
        int: 处理的记录数
    """
    count = 0
    for prod_info in production_info_list:
        # 查找是否已存在
        existing = (
            db.query(ProductionInfoDB)
            .filter(
                and_(
                    ProductionInfoDB.order_no == prod_info.order_no,
                    ProductionInfoDB.model == prod_info.model,
                    ProductionInfoDB.brand_no == prod_info.brand_no,
                    ProductionInfoDB.job_type == prod_info.job_type,
                    ProductionInfoDB.upload_date == prod_info.upload_date,
                )
            )
            .first()
        )

        if existing:
            # 更新现有记录
            existing.quantity = prod_info.quantity
            existing.performance_factor = Decimal(str(prod_info.performance_factor))
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # 创建新记录
            new_record = ProductionInfoDB(
                order_no=prod_info.order_no,
                model=prod_info.model,
                brand_no=prod_info.brand_no,
                quantity=prod_info.quantity,
                job_type=prod_info.job_type,
                performance_factor=Decimal(str(prod_info.performance_factor)),
                upload_date=prod_info.upload_date,
                created_at=prod_info.created_at,
                updated_at=prod_info.updated_at,
            )
            db.add(new_record)
        count += 1

    db.commit()
    return count


def upsert_employee_worklog(db: Session, worklog_list: List[EmployeeWorklog]) -> int:
    """
    批量插入或更新员工工作量(去重更新)

    去重规则:order_no + employee_id(根据方案文档第114行)

    Args:
        db: 数据库会话
        worklog_list: 员工工作量列表

    Returns:
        int: 处理的记录数
    """
    count = 0
    for worklog in worklog_list:
        # 查找是否已存在(根据 order_no + employee_id)
        existing = (
            db.query(EmployeeWorklogDB)
            .filter(
                and_(
                    EmployeeWorklogDB.order_no == worklog.order_no,
                    EmployeeWorklogDB.employee_id == worklog.employee_id,
                )
            )
            .first()
        )

        if existing:
            # 更新现有记录
            existing.model = worklog.model
            existing.brand_no = worklog.brand_no
            existing.employee_name = worklog.employee_name
            existing.job_type = worklog.job_type
            existing.quantity = worklog.quantity
            existing.performance_factor = Decimal(str(worklog.performance_factor))
            existing.performance_amount = Decimal(str(worklog.performance_amount))
            existing.work_date = worklog.work_date
            existing.upload_date = worklog.upload_date
            existing.validation_result = worklog.validation_result
            existing.updated_at = datetime.now(timezone.utc)
        else:
            # 创建新记录
            new_record = EmployeeWorklogDB(
                order_no=worklog.order_no,
                model=worklog.model,
                brand_no=worklog.brand_no,
                employee_id=worklog.employee_id,
                employee_name=worklog.employee_name,
                job_type=worklog.job_type,
                quantity=worklog.quantity,
                performance_factor=Decimal(str(worklog.performance_factor)),
                performance_amount=Decimal(str(worklog.performance_amount)),
                work_date=worklog.work_date,
                upload_date=worklog.upload_date,
                validation_result=worklog.validation_result,
                created_at=worklog.created_at,
                updated_at=worklog.updated_at,
            )
            db.add(new_record)
        count += 1

    db.commit()
    return count
