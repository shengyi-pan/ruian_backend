"""
测试基础设施和 fixtures
"""

from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.jwt import create_access_token
from app.auth.password import get_password_hash
from app.database import Base, get_db
from app.main import app

# 显式导入所有模型模块以确保表定义被注册
# 确保所有模型类都被导入，以便它们注册到 Base.metadata
from app.model import (
    EmployeeWorklogDB,
    ProductionInfoDB,
    User,
    UserDB,
    employee_worklog,
    production_info,
    user,
)

# 使用 SQLite 内存数据库进行测试
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# 创建测试数据库引擎
# 使用 StaticPool 确保所有会话共享同一个连接（SQLite 内存数据库需要）
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建测试会话工厂
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    创建测试数据库会话
    每个测试函数都会创建一个新的数据库
    """
    # 确保所有表都被删除（清理之前可能残留的表）
    Base.metadata.drop_all(bind=test_engine)

    # 创建所有表（确保所有模型类都已导入并注册到 Base.metadata）
    Base.metadata.create_all(bind=test_engine)

    # 创建数据库会话
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理所有表
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    创建测试客户端
    覆盖数据库依赖，使用测试数据库
    """

    # 覆盖数据库依赖
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db: Session) -> User:
    """
    创建测试用户
    """
    username = "testuser"
    password = "testpassword123"

    # 检查用户是否已存在
    existing_user = test_db.query(UserDB).filter(UserDB.username == username).first()
    if existing_user:
        test_db.delete(existing_user)
        test_db.commit()

    # 创建新用户
    password_hash = get_password_hash(password)
    user_db = UserDB(
        username=username,
        password_hash=password_hash,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(user_db)
    test_db.commit()
    test_db.refresh(user_db)

    return User.model_validate(user_db)


@pytest.fixture(scope="function")
def auth_token(test_user: User) -> str:
    """
    生成认证 token
    """
    return create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict:
    """
    生成带认证的请求头
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def sample_production_info(test_db: Session) -> ProductionInfoDB:
    """
    创建示例生产信息数据
    """
    production = ProductionInfoDB(
        order_no="ORD20250101001",
        model="MODEL-A",
        brand_no="BRAND-001",
        quantity=100,
        job_type="组装",
        worklog_no="WL001",
        performance_factor=1.2,
        upload_date=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(production)
    test_db.commit()
    test_db.refresh(production)
    return production


@pytest.fixture(scope="function")
def sample_employee_worklog(test_db: Session) -> EmployeeWorklogDB:
    """
    创建示例员工工作量数据
    """
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
        work_date=datetime.now(timezone.utc),
        upload_date=datetime.now(timezone.utc),
        validation_result="未校验",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_db.add(worklog)
    test_db.commit()
    test_db.refresh(worklog)
    return worklog
