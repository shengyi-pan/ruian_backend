"""
枚举类型定义
"""

from enum import Enum


class VldResultEnum(str, Enum):
    """校验结果枚举类型"""

    NOT_VLDED = "未校验"
    VLD_PASSED = "校验通过"
    PERFORMANCE_EXCEEDS_QUANTITY = "工作量超出系统值"
    ORDER_NO_NOT_FOUND = "工作量生产单号不存在"

