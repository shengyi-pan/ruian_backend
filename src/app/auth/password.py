"""
Author: sy.pan
Date: 2025-11-14 15:13:05
LastEditors: sy.pan
LastEditTime: 2025-11-15 16:21:47
FilePath: /ruian_backend/src/app/auth/password.py
Description:

Copyright (c) 2025 by sy.pan, All Rights Reserved.
"""

"""
密码哈希和验证
使用 bcrypt（直接使用 bcrypt 库，避免 passlib 的初始化问题）
"""

import hashlib

import bcrypt

# bcrypt 限制密码最大长度为 72 字节
# 使用 SHA-256 预处理可以将任意长度的密码压缩到 32 字节，从而支持任意长度密码
BCRYPT_MAX_PASSWORD_LENGTH = 72


def _preprocess_password(password: str) -> bytes:
    """
    预处理密码以支持任意长度
    对所有密码都使用 SHA-256 哈希为固定 32 字节，然后再用 bcrypt 处理
    这样可以完全避免 bcrypt 的 72 字节限制，同时保持安全性（双重哈希）

    Args:
        password: 明文密码

    Returns:
        bytes: 预处理后的密码（SHA-256 哈希值的二进制形式，32 字节）
    """
    password_bytes = password.encode("utf-8")

    # 对所有密码都进行 SHA-256 预处理，确保统一处理逻辑
    # SHA-256 输出 32 字节（256 位），这样可以完全避免 bcrypt 的 72 字节限制
    # 同时提供双重哈希的安全性（SHA-256 + bcrypt）
    sha256_hash = hashlib.sha256(password_bytes).digest()  # 使用 digest() 返回 bytes
    return sha256_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码（bcrypt 哈希字符串）

    Returns:
        bool: 验证结果
    """
    # 预处理密码，确保与 get_password_hash 使用相同的预处理逻辑
    preprocessed_password = _preprocess_password(plain_password)

    # 将 bcrypt 哈希字符串编码为 bytes
    hashed_bytes = hashed_password.encode("utf-8")

    # 使用 bcrypt 验证密码
    return bcrypt.checkpw(preprocessed_password, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    支持任意长度的密码（通过 SHA-256 预处理）

    Args:
        password: 明文密码（可以是任意长度）

    Returns:
        str: 哈希后的密码（bcrypt 哈希字符串）
    """
    # 预处理密码，将任意长度的密码转换为适合 bcrypt 处理的格式
    preprocessed_password = _preprocess_password(password)

    # 生成 salt 并哈希密码
    # bcrypt.gensalt() 默认使用 12 轮（推荐值）
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(preprocessed_password, salt)

    # 返回字符串形式的哈希值
    return hashed.decode("utf-8")
