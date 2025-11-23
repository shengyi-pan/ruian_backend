"""
文件上传接口测试
"""

import io
from datetime import datetime

import pandas as pd
import pytest
from openpyxl import Workbook


def create_production_excel_file() -> io.BytesIO:
    """创建用于测试的生产信息 Excel 文件"""
    data = {
        "生产订单号": ["ORD20250101001", "ORD20250101002"],
        "产品名称": ["MODEL-A", "MODEL-B"],
        "单据编号": ["BRAND-001", "BRAND-002"],
        "单据日期": ["2025-01-15", "2025-01-16"],
        "转出作业": ["组装", "测试"],
        "合格数量": [100, 200],
        "转出工序计划号": ["WL001", "WL002"],
    }
    df = pd.DataFrame(data)

    # 将 DataFrame 写入 BytesIO
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    output.seek(0)
    return output


def create_worklog_excel_file() -> io.BytesIO:
    """创建用于测试的员工工作量 Excel 文件"""
    # 创建一个工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "EMP001"

    # 写入表头
    headers = ["编号", "日期", "生产订单号", "数量", "绩效系数", "绩效数量"]
    ws.append(headers)

    # 写入数据
    ws.append([1, "2025-01-15", "ORD20250101001", 50, 1.2, 60.0])
    ws.append([2, "2025-01-16", "ORD20250101002", 100, 1.5, 150.0])

    # 保存到 BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def test_upload_production_local_success(client, auth_headers, test_db):
    """测试本地上传生产信息成功"""
    excel_file = create_production_excel_file()

    response = client.post(
        "/api/upload/production/local",
        headers=auth_headers,
        files={
            "file": (
                "production_info.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "上传成功"
    assert "filename" in data
    assert "saved_path" in data
    assert "records_processed" in data
    assert data["records_processed"] >= 0


def test_upload_production_local_invalid_file(client, auth_headers):
    """测试无效文件类型"""
    # 创建一个非 Excel 文件
    invalid_file = io.BytesIO(b"This is not an Excel file")
    invalid_file.name = "test.txt"

    response = client.post(
        "/api/upload/production/local",
        headers=auth_headers,
        files={"file": ("test.txt", invalid_file, "text/plain")},
    )

    # FastAPI 验证错误返回 422
    assert response.status_code == 422


def test_upload_production_local_unauthorized(client):
    """测试未认证访问"""
    excel_file = create_production_excel_file()

    response = client.post(
        "/api/upload/production/local",
        files={
            "file": (
                "production_info.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    # 没有 token 时应该返回 401（未授权），而不是 403（禁止访问）
    assert response.status_code == 401


def test_upload_production_oss_success(client, auth_headers, test_db, mocker):
    """测试 OSS 上传生产信息成功（使用 pytest-mock）"""
    # Mock OSS 服务
    mock_oss_service = mocker.Mock()
    mock_oss_service.download_file = mocker.Mock()

    # Mock get_oss_service 函数（在 upload_service 中被调用）
    mocker.patch(
        "app.services.upload_service.get_oss_service",
        return_value=mock_oss_service,
    )

    # Mock 解析和保存逻辑
    mocker.patch(
        "app.services.upload_service.UploadService.parse_and_save_production_info",
        return_value=(2, []),
    )

    response = client.post(
        "/api/upload/production/oss",
        headers=auth_headers,
        json={
            "object_key": "uploads/production/2025/01/production_info.xlsx",
            "filter_month": "202501",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "处理成功"
    assert "object_key" in data
    assert "records_processed" in data


def test_upload_worklog_local_success(client, auth_headers, test_db):
    """测试本地上传员工工作量成功"""
    excel_file = create_worklog_excel_file()

    response = client.post(
        "/api/upload/worklog/local",
        headers=auth_headers,
        files={
            "file": (
                "worklog.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "上传成功"
    assert "filename" in data
    assert "saved_path" in data
    assert "records_processed" in data
    assert data["records_processed"] >= 0


def test_upload_worklog_oss_success(client, auth_headers, test_db, mocker):
    """测试 OSS 上传员工工作量成功（使用 pytest-mock）"""
    # Mock OSS 服务
    mock_oss_service = mocker.Mock()
    mock_oss_service.download_file = mocker.Mock()

    # Mock get_oss_service 函数（在 upload_service 中被调用）
    mocker.patch(
        "app.services.upload_service.get_oss_service",
        return_value=mock_oss_service,
    )

    # Mock 解析和保存逻辑
    mocker.patch(
        "app.services.upload_service.UploadService.parse_and_save_employee_worklog",
        return_value=(2, []),
    )

    response = client.post(
        "/api/upload/worklog/oss",
        headers=auth_headers,
        json={
            "object_key": "uploads/worklog/2025/01/worklog_202501.xlsx",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "处理成功"
    assert "object_key" in data
    assert "records_processed" in data


def test_get_presigned_url_success(client, auth_headers, mocker):
    """测试获取预签名 URL 成功（使用 pytest-mock）"""
    # Mock OSS 服务
    mock_oss_service = mocker.Mock()
    mock_oss_service.generate_presigned_url = mocker.Mock(
        return_value="https://bucket.oss-cn-hangzhou.aliyuncs.com/uploads/file.xlsx?Expires=1234567890&OSSAccessKeyId=xxx&Signature=xxx"
    )

    # Mock get_oss_service 函数（在 API 中被调用）
    mocker.patch(
        "app.services.oss_service.get_oss_service",
        return_value=mock_oss_service,
    )

    response = client.get(
        "/api/upload/oss/presigned-url?object_key=uploads/file.xlsx&expires=3600&method=PUT",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "presigned_url" in data
    assert "object_key" in data
    assert "expires" in data
    assert "method" in data
    assert data["object_key"] == "uploads/file.xlsx"
    assert data["expires"] == 3600
    assert data["method"] == "PUT"


def test_get_presigned_url_unauthorized(client):
    """测试未认证访问"""
    response = client.get("/api/upload/oss/presigned-url?object_key=uploads/file.xlsx")

    # 没有 token 时应该返回 401（未授权），而不是 403（禁止访问）
    assert response.status_code == 401
