"""
文件上传和解析服务
"""

import os
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.config import get_config
from app.exceptions import FileUploadError
from app.model.employee_worklog import EmployeeWorklog
from app.model.production_info import ProductionInfo
from app.services.oss_service import get_oss_service
from app.utils.db_utils import upsert_employee_worklog, upsert_production_info
from app.utils.parse_util import (
    parse_employee_worklogs_from_excel,
    parse_production_excel,
)

config = get_config()


class UploadService:
    """文件上传服务"""

    def __init__(self):
        """初始化上传服务"""
        self.upload_dir = Path(config.upload.local.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = config.upload.local.max_file_size_bytes

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        保存上传的文件到本地

        Args:
            file_content: 文件内容
            filename: 文件名

        Returns:
            str: 保存的文件路径
        """
        # 检查文件大小
        if len(file_content) > self.max_file_size:
            raise FileUploadError(
                f"文件大小超过限制 ({config.upload.local.max_file_size_mb}MB)"
            )

        # 生成唯一文件名
        file_path = self.upload_dir / filename
        # 如果文件已存在，添加时间戳
        if file_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.upload_dir / f"{stem}_{timestamp}{suffix}"

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    def parse_and_save_production_info(
        self, file_path: str, db: Session, filter_month: str | None = None
    ) -> Tuple[int, List[ProductionInfo]]:
        """
        解析生产信息 Excel 并保存到数据库

        Args:
            file_path: Excel 文件路径
            db: 数据库会话
            filter_month: 月份过滤参数（格式：yyyyMM）

        Returns:
            Tuple[int, List[ProductionInfo]]: (处理的记录数, 解析的数据列表)
        """
        try:
            # 解析 Excel
            production_info_list = parse_production_excel(
                file_path, filter_month=filter_month
            )

            # 保存到数据库（去重更新）
            count = upsert_production_info(db, production_info_list)

            return count, production_info_list
        except Exception as e:
            raise FileUploadError(f"解析生产信息失败: {str(e)}")

    def parse_and_save_employee_worklog(
        self, file_path: str, db: Session
    ) -> Tuple[int, List[EmployeeWorklog]]:
        """
        解析员工工作量 Excel 并保存到数据库

        Args:
            file_path: Excel 文件路径
            db: 数据库会话

        Returns:
            Tuple[int, List[EmployeeWorklog]]: (处理的记录数, 解析的数据列表)
        """
        try:
            # 解析 Excel
            worklog_list = parse_employee_worklogs_from_excel(file_path)

            # 保存到数据库（去重更新）
            count = upsert_employee_worklog(db, worklog_list)

            return count, worklog_list
        except Exception as e:
            raise FileUploadError(f"解析员工工作量失败: {str(e)}")

    def handle_oss_upload(
        self, object_key: str, file_type: str, db: Session, filter_month: str | None = None
    ) -> Tuple[int, int]:
        """
        处理 OSS 上传的文件（下载、解析、入库）

        Args:
            object_key: OSS 对象键
            file_type: 文件类型（"production" 或 "worklog"）
            db: 数据库会话
            filter_month: 月份过滤参数（仅用于生产信息）

        Returns:
            Tuple[int, int]: (处理的记录数, 0) 或 (0, 处理的记录数)
        """
        oss_service = get_oss_service()

        # 下载文件到临时目录
        temp_dir = self.upload_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = temp_dir / Path(object_key).name

        try:
            # 从 OSS 下载文件
            oss_service.download_file(object_key, str(local_file_path))

            # 根据文件类型解析和保存
            if file_type == "production":
                count, _ = self.parse_and_save_production_info(
                    str(local_file_path), db, filter_month
                )
                return count, 0
            elif file_type == "worklog":
                count, _ = self.parse_and_save_employee_worklog(
                    str(local_file_path), db
                )
                return 0, count
            else:
                raise FileUploadError(f"不支持的文件类型: {file_type}")
        finally:
            # 清理临时文件
            if local_file_path.exists():
                os.remove(local_file_path)


# 全局上传服务实例
_upload_service: UploadService | None = None


def get_upload_service() -> UploadService:
    """
    获取上传服务实例（单例模式）

    Returns:
        UploadService: 上传服务实例
    """
    global _upload_service
    if _upload_service is None:
        _upload_service = UploadService()
    return _upload_service

