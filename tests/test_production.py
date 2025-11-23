"""
生产信息查询接口测试
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.model.production_info import ProductionInfoDB


def test_get_production_info_success(
    client, auth_headers, test_db: Session, sample_production_info: ProductionInfoDB
):
    """测试成功查询生产信息列表"""
    response = client.get("/api/production", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "items" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["order_no"] == sample_production_info.order_no


def test_get_production_info_with_filters(
    client, auth_headers, test_db: Session
):
    """测试带过滤条件查询"""
    # 创建测试数据
    production1 = ProductionInfoDB(
        order_no="ORD20250101001",
        model="MODEL-A",
        brand_no="BRAND-001",
        quantity=100,
        job_type="组装",
        worklog_no="WL001",
        performance_factor=1.2,
        upload_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    production2 = ProductionInfoDB(
        order_no="ORD20250102002",
        model="MODEL-B",
        brand_no="BRAND-002",
        quantity=200,
        job_type="测试",
        worklog_no="WL002",
        performance_factor=1.5,
        upload_date=datetime(2025, 2, 15, tzinfo=timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(production1)
    test_db.add(production2)
    test_db.commit()

    # 测试订单号过滤
    response = client.get(
        "/api/production?order_no=ORD20250101", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all("ORD20250101" in item["order_no"] for item in data["items"])

    # 测试日期范围过滤
    response = client.get(
        "/api/production?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_get_production_info_pagination(
    client, auth_headers, test_db: Session
):
    """测试分页功能"""
    # 创建多条测试数据
    for i in range(15):
        production = ProductionInfoDB(
            order_no=f"ORD2025010{i:04d}",
            model=f"MODEL-{i}",
            brand_no=f"BRAND-{i:03d}",
            quantity=100 + i,
            job_type="组装",
            worklog_no=f"WL{i:03d}",
            performance_factor=1.2,
            upload_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        test_db.add(production)
    test_db.commit()

    # 测试第一页
    response = client.get("/api/production?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10

    # 测试第二页
    response = client.get("/api/production?page=2&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) <= 10


def test_get_production_info_unauthorized(client):
    """测试未认证访问"""
    response = client.get("/api/production")
    assert response.status_code == 401


def test_get_production_info_by_order_no_success(
    client, auth_headers, test_db: Session, sample_production_info: ProductionInfoDB
):
    """测试按订单号查询成功"""
    response = client.get(
        f"/api/production/{sample_production_info.order_no}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(item["order_no"] == sample_production_info.order_no for item in data)


def test_get_production_info_by_order_no_not_found(
    client, auth_headers
):
    """测试订单号不存在"""
    response = client.get("/api/production/NONEXISTENT_ORDER", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

