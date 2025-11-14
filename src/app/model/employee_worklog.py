"""
Author: sy.pan
Date: 2025-11-13 17:16:52
LastEditors: sy.pan
LastEditTime: 2025-11-13 17:17:49
FilePath: /ruian_backend/src/app/model/employee_worklog.py
Description:

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, Index, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database import Base
from app.utils.data_vld import VldResultEnum


# ------------------------------
# 1) 定义 SQLAlchemy ORM 模型
# ------------------------------
class EmployeeWorklogDB(Base):
    """员工工作量数据库模型"""

    __tablename__ = "employee_worklog"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String, nullable=False, index=True)
    model = Column(String, nullable=True)
    brand_no = Column(String, nullable=True)
    employee_id = Column(String, nullable=False, index=True)
    employee_name = Column(String, nullable=True)
    job_type = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    performance_factor = Column(Numeric(6, 2), nullable=False)
    performance_amount = Column(Numeric(18, 2), nullable=False)
    work_date = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    upload_date = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    validation_result = Column(
        String, nullable=False, default=VldResultEnum.NOT_VLDED.value
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # 索引
    __table_args__ = (
        Index("idx_worklog_emp_date", "employee_id", "work_date"),
        Index("idx_worklog_order_date", "order_no", "work_date"),
        Index("idx_worklog_job_date", "job_type", "work_date"),
    )


# ------------------------------
# 2) 定义 Pydantic BaseModel
# ------------------------------


class EmployeeWorklog(BaseModel):
    """
    员工工作量 BaseModel
    (id 一般由数据库生成，因此这里设为可选)
    """

    id: Optional[int] = None

    order_no: str  # 生产订单号（Excel: 生产订单号）
    model: Optional[str] = None  # 型号（Excel中暂不提供，默认空）
    brand_no: Optional[str] = None  # 牌号（Excel中暂不提供，默认空）
    employee_id: str  # 工号（Excel: sheet name）
    employee_name: Optional[str] = None  # 姓名（Excel中暂不提供，默认空）

    # Excel 中没有对应字段，给一个合法默认值即可
    job_type: str = "未知"

    quantity: int  # 数量（Excel: 数量）
    performance_factor: float = 1.0  # 绩效系数（Excel: 绩效系数，缺失时默认 1.0）
    performance_amount: float  # 绩效数量（Excel: 绩效数量）

    work_date: datetime  # 工作日期（Excel: 日期）

    # 下面几个时间字段用当前时间作为默认值（合法、非空）
    upload_date: datetime = Field(default_factory=lambda: datetime.now())
    validation_result: str = Field(default=VldResultEnum.NOT_VLDED.value)  # 校验结果
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    # 一些简单的校验，确保满足 >0 的约束
    @field_validator("quantity")
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    @field_validator("performance_factor")
    def perf_factor_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("performance_factor must be > 0")
        return v

    @field_validator("performance_amount")
    def perf_amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("performance_amount must be > 0")
        return v
