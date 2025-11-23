"""
FastAPI 应用主入口
"""

from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response

from app.api import auth, production, upload, validation, worklog
from app.config import get_config
from app.exceptions import AppException

config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    yield
    # 关闭时执行


# OpenAPI 标签描述
tags_metadata = [
    {
        "name": "auth",
        "description": "用户认证相关接口，包括登录和获取当前用户信息。",
    },
    {
        "name": "upload",
        "description": "文件上传接口，支持本地存储和阿里云 OSS 两种方式上传生产信息和员工工作量数据。",
    },
    {
        "name": "production",
        "description": "生产信息查询接口，支持分页、订单号、日期范围等条件查询。",
    },
    {
        "name": "worklog",
        "description": "员工工作量查询接口，支持分页、订单号、日期范围、员工工号等条件查询。",
    },
    {
        "name": "validation",
        "description": "数据核验接口，用于验证生产信息和员工工作量数据的一致性。",
    },
]

# 创建 FastAPI 应用
app = FastAPI(
    title=config.app.name,
    version=config.app.version,
    description="""
    ## 锐安后端 API 文档

    本 API 提供以下功能：

    * **认证管理**: 用户登录和身份验证
    * **文件上传**: 支持本地存储和阿里云 OSS 两种方式上传 Excel 文件
    * **生产信息查询**: 查询和管理生产订单信息
    * **员工工作量查询**: 查询和管理员工工作量记录
    * **数据核验**: 验证生产信息和员工工作量数据的一致性

    ## 认证说明

    大部分接口需要 Bearer Token 认证。请先调用 `/api/auth/login` 接口获取 token，
    然后在请求头中添加：`Authorization: Bearer <your_token>`

    ## 错误响应

    所有错误响应都遵循统一格式：
    ```json
    {
        "error": true,
        "message": "错误消息",
        "detail": {}
    }
    ```
    """,
    debug=config.app.debug,
    lifespan=lifespan,
    tags_metadata=tags_metadata,
    contact={
        "name": "API Support",
        "email": "shengyi.pan@gmail.com",
    },
    license_info={
        "name": "MIT",
    },
)


def custom_openapi():
    """自定义 OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )

    # 添加安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "输入 JWT token（仅输入 token 本身，无需添加 'Bearer' 前缀，系统会自动添加）",
        }
    }

    # 为需要认证的路径添加 security 字段
    # 检查所有路径，如果路径描述中包含"需要 Bearer Token 认证"或"需要认证"，
    # 或者路径不在 /api/auth/login 和 / 等公开路径中，则添加 security 字段
    public_paths = {"/", "/health", "/openapi.json", "/openapi.yaml", "/docs", "/redoc"}
    auth_paths = {"/api/auth/login"}  # 登录接口不需要认证

    for path, methods in openapi_schema.get("paths", {}).items():
        # 跳过公开路径
        if path in public_paths or path in auth_paths:
            continue

        # 为路径下的所有 HTTP 方法添加 security 字段
        for method, operation in methods.items():
            if isinstance(operation, dict):
                # 检查描述中是否提到需要认证，或者直接为所有非公开路径添加
                description = operation.get("description", "")
                summary = operation.get("summary", "")
                # 如果描述或摘要中提到需要认证，或者路径是 /api/ 下的非登录接口
                if (
                    "需要 Bearer Token 认证" in description
                    or "需要认证" in description
                    or "需要 Bearer Token" in description
                    or (path.startswith("/api/") and path != "/api/auth/login")
                ):
                    operation["security"] = [{"Bearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allow_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
)


# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理应用自定义异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理其他异常"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "服务器内部错误",
            "detail": {"type": type(exc).__name__, "message": str(exc)},
        },
    )


# 注册路由
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(production.router)
app.include_router(worklog.router)
app.include_router(validation.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to ruian-backend API",
        "version": config.app.version,
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    """导出 OpenAPI 规范（YAML 格式）"""
    openapi_schema = app.openapi()
    yaml_content = yaml.dump(openapi_schema, allow_unicode=True, sort_keys=False)
    return Response(content=yaml_content, media_type="application/x-yaml")


def main():
    """主入口函数（用于命令行启动）"""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.app.debug,
    )


if __name__ == "__main__":
    main()
