# 使用 Python 3.11 官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv

# 先复制依赖文件，利用 Docker 缓存层
COPY pyproject.toml uv.lock ./

# 复制项目源代码（uv 需要源代码来安装项目）
COPY src/ ./src/

# 使用 uv 安装项目及其依赖到系统 Python
# 这会安装 pyproject.toml 中定义的所有依赖
RUN uv pip install --system .

# 复制配置文件（不包含在包中，最后复制以便于修改）
COPY config.yaml ./

# 创建上传目录
RUN mkdir -p uploads && chmod 755 uploads

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /bin/sh -c "python -c \"import urllib.request; import sys; urllib.request.urlopen('http://localhost:8000/health', timeout=5).close()\" || exit 1"

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

