"""
员工工作量查询接口测试
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.model.employee_worklog import EmployeeWorklogDB


def test_get_employee_worklog_success(
    client, auth_headers, test_db: Session, sample_employee_worklog: EmployeeWorklogDB
):
    """测试成功查询员工工作量列表"""
    response = client.get("/api/worklog", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "items" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["order_no"] == sample_employee_worklog.order_no


def test_get_employee_worklog_with_filters(
    client, auth_headers, test_db: Session
):
    """测试带过滤条件查询"""
    # 创建测试数据
    worklog1 = EmployeeWorklogDB(
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
        upload_date=datetime.now(timezone.utc),
        validation_result="未校验",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    worklog2 = EmployeeWorklogDB(
        order_no="ORD20250102002",
        model="MODEL-B",
        brand_no="BRAND-002",
        employee_id="EMP002",
        employee_name="李四",
        job_type="测试",
        quantity=100,
        performance_factor=1.5,
        performance_amount=150.0,
        work_date=datetime(2025, 2, 15, tzinfo=timezone.utc),
        upload_date=datetime.now(timezone.utc),
        validation_result="正常",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(worklog1)
    test_db.add(worklog2)
    test_db.commit()

    # 测试订单号过滤
    response = client.get(
        "/api/worklog?order_no=ORD20250101", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all("ORD20250101" in item["order_no"] for item in data["items"])

    # 测试员工工号过滤
    response = client.get("/api/worklog?employee_id=EMP001", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["employee_id"] == "EMP001" for item in data["items"])

    # 测试日期范围过滤
    response = client.get(
        "/api/worklog?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_get_employee_worklog_pagination(
    client, auth_headers, test_db: Session
):
    """测试分页功能"""
    # 创建多条测试数据
    for i in range(15):
        worklog = EmployeeWorklogDB(
            order_no=f"ORD2025010{i:04d}",
            model=f"MODEL-{i}",
            brand_no=f"BRAND-{i:03d}",
            employee_id=f"EMP{i:03d}",
            employee_name=f"员工{i}",
            job_type="组装",
            quantity=50 + i,
            performance_factor=1.2,
            performance_amount=60.0 + i,
            work_date=datetime.now(timezone.utc),
            upload_date=datetime.now(timezone.utc),
            validation_result="未校验",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(worklog)
    test_db.commit()

    # 测试第一页
    response = client.get("/api/worklog?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10

    # 测试第二页
    response = client.get("/api/worklog?page=2&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) <= 10


def test_get_employee_worklog_unauthorized(client):
    """测试未认证访问"""
    response = client.get("/api/worklog")
    assert response.status_code == 401


def test_get_employee_worklog_by_order_no_success(
    client, auth_headers, test_db: Session, sample_employee_worklog: EmployeeWorklogDB
):
    """测试按订单号查询成功"""
    response = client.get(
        f"/api/worklog/{sample_employee_worklog.order_no}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(item["order_no"] == sample_employee_worklog.order_no for item in data)


def test_get_employee_worklog_by_order_no_not_found(
    client, auth_headers
):
    """测试订单号不存在"""
    response = client.get("/api/worklog/NONEXISTENT_ORDER", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

