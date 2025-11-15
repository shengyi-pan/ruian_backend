"""
Author: sy.pan
Date: 2025-11-15 12:19:51
LastEditors: sy.pan
LastEditTime: 2025-11-15 15:42:01
FilePath: /ruian_backend/scripts/export_docs.py
Description:

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

"""
导出 API 文档脚本
用于离线导出 OpenAPI 规范文件(JSON 和 YAML 格式)
"""

import json
import sys
from pathlib import Path

import yaml

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.main import app


def export_openapi_docs(output_dir: Path = None):
    """
    导出 OpenAPI 文档到指定目录

    Args:
        output_dir: 输出目录，默认为 docs/api/
    """
    if output_dir is None:
        output_dir = project_root / "docs" / "api"

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取 OpenAPI schema
    openapi_schema = app.openapi()

    # 导出 JSON 格式
    json_path = output_dir / "openapi.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    print(f"✓ 已导出 OpenAPI JSON: {json_path}")

    # 导出 YAML 格式
    yaml_path = output_dir / "openapi.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(
            openapi_schema,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    print(f"✓ 已导出 OpenAPI YAML: {yaml_path}")

    print(f"\n文档已导出到: {output_dir}")
    print("\n使用说明:")
    print("1. 可以将 openapi.json 导入到 Postman、Insomnia 等 API 测试工具")
    print("2. 可以使用 redoc-cli 生成静态 HTML 文档:")
    print("   npx @redocly/cli build-docs docs/api/openapi.yaml -o docs/api/index.html")
    print("3. 可以将文档提交到版本控制系统，方便团队共享")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="导出 FastAPI OpenAPI 文档")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="输出目录(默认: docs/api/)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None
    export_openapi_docs(output_dir)
