"""
Author: sy.pan
Date: 2025-11-13 19:01:51
LastEditors: sy.pan
LastEditTime: 2025-11-13 19:22:49

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from app.model.employee_worklog import EmployeeWorklog
from app.model.production_info import ProductionInfo
from app.utils.enums import VldResultEnum
from app.utils.parse_util import (
    parse_employee_worklogs_from_excel,
    parse_production_excel,
)


def validate_production_and_worklog(
    production_info_list: List[ProductionInfo],
    employee_worklog_list: List[EmployeeWorklog],
) -> Tuple[
    Dict[Tuple[str, VldResultEnum], List[EmployeeWorklog]],
    Dict[str, List[EmployeeWorklog]],
]:
    """
    校验 ProductionInfo 和 EmployeeWorklog 数据

    参数:
        production_info_list: 生产信息列表
        employee_worklog_list: 员工工作量列表

    返回:
        tuple: (异常数据字典, 正常数据字典)
            - 异常数据字典: 以(order_no, 异常类型)为key, 异常明细数据为value的字典
            - 正常数据字典: 以order_no为key, 正常明细数据为value的字典
    """
    # 初始化返回结果
    exception_result: Dict[Tuple[str, VldResultEnum], List[EmployeeWorklog]] = (
        defaultdict(list)
    )
    normal_result: Dict[str, List[EmployeeWorklog]] = defaultdict(list)

    # 1. 基于 worklog_no 聚合求和 ProductionInfo.quantity
    # EmployeeWorklog.order_no 对应到 ProductionInfo.worklog_no 进行统计计算
    production_agg: Dict[str, int] = defaultdict(int)
    for prod in production_info_list:
        production_agg[prod.worklog_no] += prod.quantity

    # 2. 基于 order_no 聚合求和 EmployeeWorklog.performance_amount
    worklog_agg: Dict[str, float] = defaultdict(float)
    worklog_by_order: Dict[str, List[EmployeeWorklog]] = defaultdict(list)
    for worklog in employee_worklog_list:
        worklog_agg[worklog.order_no] += worklog.performance_amount
        worklog_by_order[worklog.order_no].append(worklog)

    # 3. 检查异常：工作量生产单号不存在
    # 如果 order_no 在 EmployeeWorklog 存在，但在 ProductionInfo.worklog_no 中不存在
    exception_order_nos = set()
    for order_no in worklog_agg.keys():
        if order_no not in production_agg:
            # 异常：工作量生产单号不存在
            exception_order_nos.add(order_no)
            worklog_list = worklog_by_order[order_no]
            # 为每个 worklog 设置校验结果
            for worklog in worklog_list:
                worklog.validation_result = VldResultEnum.ORDER_NO_NOT_FOUND.value
            exception_result[(order_no, VldResultEnum.ORDER_NO_NOT_FOUND)].extend(
                worklog_list
            )

    # 4. 检查异常：工作量超出系统值
    # 对每个 order_no 对比求和值（仅检查在 ProductionInfo.worklog_no 中存在的 order_no）
    for order_no, worklog_sum in worklog_agg.items():
        if order_no in production_agg:  # 只检查存在的订单号
            production_sum = production_agg[order_no]
            if worklog_sum > production_sum:
                # 异常：工作量超出系统值
                exception_order_nos.add(order_no)
                worklog_list = worklog_by_order[order_no]
                # 为每个 worklog 设置校验结果
                for worklog in worklog_list:
                    worklog.validation_result = (
                        VldResultEnum.PERFORMANCE_EXCEEDS_QUANTITY.value
                    )
                exception_result[
                    (order_no, VldResultEnum.PERFORMANCE_EXCEEDS_QUANTITY)
                ].extend(worklog_list)

    # 5. 收集正常数据（没有异常的 order_no）
    for order_no, worklog_list in worklog_by_order.items():
        if order_no not in exception_order_nos:
            # 为每个 worklog 设置校验结果为通过
            for worklog in worklog_list:
                worklog.validation_result = VldResultEnum.VLD_PASSED.value
            normal_result[order_no].extend(worklog_list)

    # 转换为普通字典（去除 defaultdict）
    return dict(exception_result), dict(normal_result)


if __name__ == "__main__":

    production_info_path = "/Users/sy.pan/Documents/workspace/ml_lesson/ruian_backend/data/product_info_full.xlsx"
    employee_worklog_path = "/Users/sy.pan/Documents/workspace/ml_lesson/ruian_backend/data/worklog_202510.xlsx"

    production_info_list = parse_production_excel(
        production_info_path, filter_month="202510"
    )
    print(f"共解析到 {len(production_info_list)} 条生产信息")

    employee_worklog_list = parse_employee_worklogs_from_excel(employee_worklog_path)
    print(f"共解析到 {len(employee_worklog_list)} 条员工工作量")
    employee_ids = set([worklog.employee_id for worklog in employee_worklog_list])
    print(f"共解析到 {len(employee_ids)} 个员工")

    exception_result, normal_result = validate_production_and_worklog(
        production_info_list, employee_worklog_list
    )
    print(f"共校验出 {len(exception_result)} 条异常")
    for tuple_key, worklog_list in list(exception_result.items()):
        order_no, except_enum = tuple_key
        print(f"订单号: {order_no}, 异常类型: {except_enum}")
        for worklog in worklog_list:
            worklog_dict = worklog.model_dump()
            print(
                f"生产订单号: {worklog_dict['order_no']}, 工号: {worklog_dict['employee_id']}, 工作量: {worklog_dict['performance_amount']}, 校验结果: {worklog_dict['validation_result']}"
            )
            print("-" * 100)

    print(f"\n共校验出 {len(normal_result)} 个正常订单")
    for order_no, worklog_list in list(normal_result.items())[:5]:
        print(f"订单号: {order_no}, 正常数据条数: {len(worklog_list)}")
