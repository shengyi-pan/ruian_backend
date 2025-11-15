<!--
 * @Author: sy.pan
 * @Date: 2025-09-10 10:27:41
 * @LastEditors: sy.pan
 * @LastEditTime: 2025-11-12 17:27:18
 * @FilePath: /ruian_backend/README.md
 * @Description:
 *
 * Copyright (c) 2025 by sy.pan, All Rights Reserved.
-->

# 瑞安后端 API

Python UV project demo.

Must review pyproject.toml and pytest.ini content before deploying.
Good Luck!

## API 文档

### 在线文档

启动服务后，可以通过以下地址访问 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **OpenAPI YAML**: http://localhost:8000/openapi.yaml

### 离线文档导出

由于开发阶段后端服务可能不会一直在线，可以使用以下方式导出 API 文档供离线使用：

#### 方式一：使用命令行脚本

```bash
# 导出到默认目录 (docs/api/)
python -m scripts.export_docs

# 或指定输出目录
python -m scripts.export_docs -o /path/to/output
```

#### 方式二：使用安装的命令

```bash
# 如果已安装项目
export-docs
```

导出的文件：
- `docs/api/openapi.json` - OpenAPI 规范（JSON 格式）
- `docs/api/openapi.yaml` - OpenAPI 规范（YAML 格式）

#### 使用导出的文档

1. **导入到 API 测试工具**
   - Postman: 导入 `openapi.json` 或 `openapi.yaml`
   - Insomnia: 导入 `openapi.json` 或 `openapi.yaml`
   - 其他支持 OpenAPI 的工具

2. **生成静态 HTML 文档**
   ```bash
   # 使用 redoc-cli（需要 Node.js）
   npx @redocly/cli build-docs docs/api/openapi.yaml -o docs/api/index.html
   
   # 或使用 swagger-ui-dist
   # 参考相关文档
   ```

3. **版本控制**
   - 将导出的文档提交到 Git，方便团队共享
   - 在 CI/CD 流程中自动导出最新文档

## 认证说明

大部分 API 接口需要 Bearer Token 认证：

1. 首先调用 `/api/auth/login` 接口获取 token
2. 在后续请求的请求头中添加：`Authorization: Bearer <your_token>`

在 Swagger UI 中，可以点击右上角的 "Authorize" 按钮，输入 token 进行认证。
