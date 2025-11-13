#!/bin/bash
# 清理可能存在的其他项目的 VIRTUAL_ENV 环境变量
unset VIRTUAL_ENV

# 运行 uv 命令
uv run app "$@"


