"""
Author: sy.pan
Date: 2025-11-13 19:01:51
LastEditors: sy.pan
LastEditTime: 2025-11-13 19:22:49

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

from collections import defaultdict
from enum import Enum
from typing import Dict, List

from app.model.employee_worklog import EmployeeWorklog
from app.model.production_info import ProductionInfo


class ExceptEnum(str, Enum):
    """异常枚举类型"""

    PERFORMANCE_EXCEEDS_QUANTITY = "工作量超出系统值"
    ORDER_NO_NOT_FOUND = "工作量生产单号不存在"


def validate_production_and_worklog(
    production_info_list: List[ProductionInfo],
    employee_worklog_list: List[EmployeeWorklog],
) -> Dict[ExceptEnum, List[EmployeeWorklog]]:
    """
    校验 ProductionInfo 和 EmployeeWorklog 数据

    参数:
        production_info_list: 生产信息列表
        employee_worklog_list: 员工工作量列表

    返回:
        dict[ExceptEnum, List[EmployeeWorklog]]: 异常类型和对应的异常明细数据
    """
    # 初始化返回结果
    result: Dict[ExceptEnum, List[EmployeeWorklog]] = defaultdict(list)

    # 1. 基于 order_no 聚合求和 ProductionInfo.quantity
    production_agg: Dict[str, int] = defaultdict(int)
    for prod in production_info_list:
        production_agg[prod.order_no] += prod.quantity

    # 2. 基于 order_no 聚合求和 EmployeeWorklog.performance_amount
    worklog_agg: Dict[str, float] = defaultdict(float)
    worklog_by_order: Dict[str, List[EmployeeWorklog]] = defaultdict(list)
    for worklog in employee_worklog_list:
        worklog_agg[worklog.order_no] += worklog.performance_amount
        worklog_by_order[worklog.order_no].append(worklog)

    # 3. 检查异常：工作量生产单号不存在
    # 如果 order_no 在 EmployeeWorklog 存在，但在 ProductionInfo 不存在
    for order_no in worklog_agg.keys():
        if order_no not in production_agg:
            # 异常：工作量生产单号不存在
            result[ExceptEnum.ORDER_NO_NOT_FOUND].extend(worklog_by_order[order_no])

    # 4. 检查异常：工作量超出系统值
    # 对每个 order_no 对比求和值（仅检查在 ProductionInfo 中存在的 order_no）
    for order_no, worklog_sum in worklog_agg.items():
        if order_no in production_agg:  # 只检查存在的订单号
            production_sum = production_agg[order_no]
            if worklog_sum > production_sum:
                # 异常：工作量超出系统值
                result[ExceptEnum.PERFORMANCE_EXCEEDS_QUANTITY].extend(
                    worklog_by_order[order_no]
                )

    # 转换为普通字典（去除 defaultdict）
    return dict(result)
