"""
阿里云 OSS 服务封装
"""

import os
from datetime import timedelta
from pathlib import Path
from typing import Optional

import oss2

from app.config import get_config
from app.exceptions import FileUploadError

config = get_config()


class OSSService:
    """OSS 服务类"""

    def __init__(self):
        """初始化 OSS 客户端"""
        self.access_key_id = config.upload.oss.access_key_id
        self.access_key_secret = config.upload.oss.access_key_secret
        self.endpoint = config.upload.oss.endpoint
        self.bucket_name = config.upload.oss.bucket_name
        self.region = config.upload.oss.region

        # 创建 OSS 认证对象
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        # 创建 Bucket 对象
        self.bucket = oss2.Bucket(
            auth, f"https://{self.endpoint}", self.bucket_name
        )

    def generate_presigned_url(
        self, object_key: str, expires: int = 3600, method: str = "PUT"
    ) -> str:
        """
        生成预签名 URL

        Args:
            object_key: OSS 对象键（文件路径）
            expires: 过期时间（秒），默认 1 小时
            method: HTTP 方法，默认 PUT

        Returns:
            str: 预签名 URL
        """
        try:
            url = self.bucket.sign_url(method, object_key, expires)
            return url
        except Exception as e:
            raise FileUploadError(f"生成预签名 URL 失败: {str(e)}")

    def upload_file(self, local_file_path: str, object_key: str) -> str:
        """
        上传文件到 OSS

        Args:
            local_file_path: 本地文件路径
            object_key: OSS 对象键（文件路径）

        Returns:
            str: OSS 文件 URL
        """
        try:
            with open(local_file_path, "rb") as f:
                self.bucket.put_object(object_key, f)
            return f"https://{self.bucket_name}.{self.endpoint}/{object_key}"
        except Exception as e:
            raise FileUploadError(f"上传文件到 OSS 失败: {str(e)}")

    def download_file(self, object_key: str, local_file_path: str) -> str:
        """
        从 OSS 下载文件

        Args:
            object_key: OSS 对象键（文件路径）
            local_file_path: 本地保存路径

        Returns:
            str: 本地文件路径
        """
        try:
            self.bucket.get_object_to_file(object_key, local_file_path)
            return local_file_path
        except Exception as e:
            raise FileUploadError(f"从 OSS 下载文件失败: {str(e)}")

    def delete_file(self, object_key: str) -> bool:
        """
        删除 OSS 文件

        Args:
            object_key: OSS 对象键（文件路径）

        Returns:
            bool: 是否删除成功
        """
        try:
            self.bucket.delete_object(object_key)
            return True
        except Exception as e:
            raise FileUploadError(f"删除 OSS 文件失败: {str(e)}")


# 全局 OSS 服务实例
_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    """
    获取 OSS 服务实例（单例模式）

    Returns:
        OSSService: OSS 服务实例
    """
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service

