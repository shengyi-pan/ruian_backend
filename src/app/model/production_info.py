from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator

# UTC+8 时区（东八区，中国标准时间）
TZ_UTC_PLUS_8 = timezone(timedelta(hours=8))


# ------------------------------
# 1) 定义 Pydantic BaseModel
# ------------------------------
class ProductionInfo(BaseModel):
    """
    对应表 production_info 的数据模型。
    说明：
      - id: 数据库自增，导入阶段可不提供，设为 None
      - performance_factor: Excel 没有映射，给一个合法正数默认值 1.00
      - upload_date: 默认为当天
      - created_at/updated_at: 映射自 Excel「单据日期」字段, 若缺失则使用当前时间
    """

    id: Optional[int] = Field(default=None)

    order_no: str  # 生产订单号（Excel: 生产订单号）
    model: str  # 产品型号/名称（Excel: 产品名称）
    brand_no: str  # 牌号/单据编号（Excel: 单据编号）
    quantity: int  # 合格数量（Excel: 合格数量），需 > 0
    job_type: str  # 工种/转出作业（Excel: 转出作业）

    performance_factor: Decimal = Field(
        default=Decimal("1.00"),  # 合法正数默认值
        description="绩效系数,Excel未提供时默认1.00",
    )

    upload_date: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="上传日期，默认当天",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="更新时间",
    )

    # --------- 校验与清洗 ---------
    @field_validator("order_no", "model", "brand_no", "job_type", mode="before")
    @classmethod
    def _strip_str(cls, v):
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("quantity", mode="before")
    @classmethod
    def _quantity_positive(cls, v):
        # 允许浮点/字符串，最终转为正整数
        if v is None or (isinstance(v, float) and pd.isna(v)):
            raise ValueError("quantity 不能为空")
        try:
            q = int(Decimal(str(v)))
        except Exception:
            raise ValueError(f"quantity 无法转换为整数: {v!r}")
        if q <= 0:
            raise ValueError(f"quantity 必须为正整数，当前: {q}")
        return q

    @field_validator("performance_factor", mode="before")
    @classmethod
    def _pf_decimal(cls, v):
        if v in (None, "", 0, 0.0):
            v = Decimal("1.00")
        d = Decimal(str(v))
        if d <= 0:
            raise ValueError("performance_factor 必须为正数")
        # 保留两位小数
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _to_aware_datetime(dt_like) -> datetime:
        """
        将 Excel 里的时间(可能是 pandas.Timestamp、datetime、str 或 NaT)
        统一转换为 timezone-aware 的 UTC+8 datetime。
        """
        if dt_like is None or (isinstance(dt_like, float) and pd.isna(dt_like)):
            return datetime.now(TZ_UTC_PLUS_8)

        # pandas/pyarrow 读出的时间戳
        if isinstance(dt_like, pd.Timestamp):
            if dt_like.tzinfo is None:
                # 视为本地时间，转为 UTC+8（这里假定为本地无时区，直接当作 naive，再设置为 UTC+8）
                return dt_like.to_pydatetime().replace(tzinfo=TZ_UTC_PLUS_8)
            return dt_like.to_pydatetime().astimezone(TZ_UTC_PLUS_8)

        # Python datetime
        if isinstance(dt_like, datetime):
            if dt_like.tzinfo is None:
                return dt_like.replace(tzinfo=TZ_UTC_PLUS_8)
            return dt_like.astimezone(TZ_UTC_PLUS_8)

        # 字符串尝试解析
        if isinstance(dt_like, str):
            s = dt_like.strip()
            if not s:
                return datetime.now(TZ_UTC_PLUS_8)
            # 常见格式尝试
            fmt_candidates = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y/%m/%d %H:%M",
            ]
            for fmt in fmt_candidates:
                try:
                    naive = datetime.strptime(s, fmt)
                    return naive.replace(tzinfo=TZ_UTC_PLUS_8)
                except Exception:
                    pass
            # 尝试由 pandas 解析
            try:
                ts = pd.to_datetime(s, errors="raise")
                if isinstance(ts, pd.Timestamp):
                    if ts.tzinfo is None:
                        return ts.to_pydatetime().replace(tzinfo=TZ_UTC_PLUS_8)
                    return ts.to_pydatetime().astimezone(TZ_UTC_PLUS_8)
            except Exception:
                pass
            # 实在解析不了就用当前时间
            return datetime.now(TZ_UTC_PLUS_8)

        # 其它类型兜底
        return datetime.now(TZ_UTC_PLUS_8)

    @staticmethod
    def _to_naive_datetime(dt_like) -> datetime:
        """
        将 Excel 里的时间(可能是 pandas.Timestamp、datetime、str 或 NaT)
        统一转换为 naive (本地时间) datetime，去除时区信息。
        """
        if dt_like is None or (isinstance(dt_like, float) and pd.isna(dt_like)):
            return datetime.now()

        # pandas/pyarrow 读出的时间戳
        if isinstance(dt_like, pd.Timestamp):
            # 如果有时区信息，先转换为 UTC+8，再转为 naive
            if dt_like.tzinfo is not None:
                dt_aware = dt_like.to_pydatetime().astimezone(TZ_UTC_PLUS_8)
                return dt_aware.replace(tzinfo=None)
            return dt_like.to_pydatetime()

        # Python datetime
        if isinstance(dt_like, datetime):
            # 如果有时区信息，先转换为 UTC+8，再转为 naive
            if dt_like.tzinfo is not None:
                dt_aware = dt_like.astimezone(TZ_UTC_PLUS_8)
                return dt_aware.replace(tzinfo=None)
            return dt_like

        # 字符串尝试解析
        if isinstance(dt_like, str):
            s = dt_like.strip()
            if not s:
                return datetime.now()
            # 常见格式尝试
            fmt_candidates = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y/%m/%d %H:%M",
            ]
            for fmt in fmt_candidates:
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    pass
            # 尝试由 pandas 解析
            try:
                ts = pd.to_datetime(s, errors="raise")
                if isinstance(ts, pd.Timestamp):
                    if ts.tzinfo is not None:
                        dt_aware = ts.to_pydatetime().astimezone(TZ_UTC_PLUS_8)
                        return dt_aware.replace(tzinfo=None)
                    return ts.to_pydatetime()
            except Exception:
                pass
            # 实在解析不了就用当前时间
            return datetime.now()

        # 其它类型兜底
        return datetime.now()

    @field_validator("upload_date", "created_at", "updated_at", mode="before")
    @classmethod
    def _dt_to_naive(cls, v):
        return ProductionInfo._to_naive_datetime(v)
