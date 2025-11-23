"""
数据核验接口测试
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.model.employee_worklog import EmployeeWorklogDB
from app.model.production_info import ProductionInfoDB


def test_validate_data_success(
    client, auth_headers, test_db: Session
):
    """测试数据核验成功"""
    # 创建匹配的生产信息和员工工作量数据
    production = ProductionInfoDB(
        order_no="ORD20250101001",
        model="MODEL-A",
        brand_no="BRAND-001",
        quantity=100,
        job_type="组装",
        worklog_no="WL001",
        performance_factor=1.2,
        upload_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    test_db.add(production)

    worklog = EmployeeWorklogDB(
        order_no="ORD20250101001",
        model="MODEL-A",
        brand_no="BRAND-001",
        employee_id="EMP001",
        employee_name="张三",
        job_type="组装",
        quantity=50,
        performance_factor=1.2,
        performance_amount=60.0,
        work_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        upload_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        validation_result="未校验",
        created_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
    )
    test_db.add(worklog)
    test_db.commit()

    # 执行核验
    response = client.post(
        "/api/validation/check",
        headers=auth_headers,
        json={
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-01-31T23:59:59",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_production_records" in data
    assert "total_worklog_records" in data
    assert "exception_count" in data
    assert "normal_count" in data
    assert "exceptions" in data
    assert "normal" in data
    assert isinstance(data["exceptions"], list)
    assert isinstance(data["normal"], list)


def test_validate_data_invalid_date_range(
    client, auth_headers
):
    """测试无效日期范围"""
    response = client.post(
        "/api/validation/check",
        headers=auth_headers,
        json={
            "start_date": "2025-01-31T23:59:59",
            "end_date": "2025-01-01T00:00:00",  # 开始日期晚于结束日期
        },
    )

    assert response.status_code == 400


def test_validate_data_unauthorized(client):
    """测试未认证访问"""
    response = client.post(
        "/api/validation/check",
        json={
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-01-31T23:59:59",
        },
    )

    assert response.status_code == 401

