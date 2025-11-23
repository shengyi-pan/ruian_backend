# Docker 部署指南

本文档说明如何使用 Docker Compose 部署 ruian-backend 应用。

## 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+

## 快速开始

### 1. 准备配置文件

确保项目根目录下有 `config.yaml` 配置文件，并配置好以下内容：

- 数据库连接信息（Supabase）
- JWT 密钥
- API 密钥
- OSS 配置（如使用）
- CORS 配置

### 2. 创建上传目录

```bash
mkdir -p uploads
```

### 3. 构建并启动服务

```bash
# 构建镜像并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

### 4. 访问应用

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- API 根路径: http://localhost:8000/

## 常用命令

### 启动服务

```bash
# 后台启动
docker-compose up -d

# 前台启动（查看日志）
docker-compose up
```

### 停止服务

```bash
# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs --tail=100

# 查看特定服务日志
docker-compose logs -f app
```

### 重启服务

```bash
# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build
```

### 进入容器

```bash
# 进入运行中的容器
docker-compose exec app bash

# 或使用 docker 命令
docker exec -it ruian-backend bash
```

### 查看服务状态

```bash
# 查看运行状态
docker-compose ps

# 查看资源使用情况
docker stats ruian-backend
```

## 配置说明

### 端口映射

默认将容器的 8000 端口映射到主机的 8000 端口。如需修改，编辑 `docker-compose.yml` 中的 `ports` 配置：

```yaml
ports:
  - "8080:8000"  # 主机端口:容器端口
```

### 配置文件挂载

`config.yaml` 以只读模式挂载，修改配置文件后需要重启容器：

```bash
docker-compose restart
```

### 数据持久化

`uploads` 目录挂载到主机，确保上传的文件在容器重启后仍然保留。

## 故障排查

### 查看容器日志

```bash
docker-compose logs app
```

### 检查容器健康状态

```bash
docker-compose ps
```

健康检查端点：http://localhost:8000/health

### 重新构建镜像

如果修改了代码或依赖，需要重新构建：

```bash
docker-compose build --no-cache
docker-compose up -d
```

### 清理资源

```bash
# 停止并删除容器、网络
docker-compose down

# 删除容器、网络和卷
docker-compose down -v

# 删除镜像
docker rmi ruian-backend_app
```

## 生产环境建议

1. **使用环境变量管理敏感信息**：考虑使用 Docker secrets 或环境变量文件
2. **配置日志轮转**：避免日志文件过大
3. **设置资源限制**：在 `docker-compose.yml` 中添加资源限制
4. **使用反向代理**：使用 Nginx 或 Traefik 作为反向代理
5. **配置 HTTPS**：使用 SSL/TLS 证书
6. **定期备份**：备份 `uploads` 目录和数据库

## 示例：添加资源限制

在 `docker-compose.yml` 中添加：

```yaml
services:
  app:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

