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
