"""
Author: sy.pan
Date: 2025-01-XX
Description: 导入用户脚本
用于批量导入用户到数据库，支持命令行参数和文件导入
"""

import csv
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.password import get_password_hash
from app.database import SessionLocal
from app.model.user import UserDB


def create_user(
    db: Session, username: str, password: str, skip_existing: bool = True
) -> tuple[bool, str]:
    """
    创建用户

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码（明文）
        skip_existing: 如果用户已存在，是否跳过（True）还是报错（False）

    Returns:
        tuple[bool, str]: (是否成功, 消息)
    """
    # 检查用户是否已存在
    existing_user = db.query(UserDB).filter(UserDB.username == username).first()
    if existing_user:
        if skip_existing:
            return False, f"用户 '{username}' 已存在，已跳过"
        else:
            return False, f"用户 '{username}' 已存在"

    # 创建新用户
    try:
        password_hash = get_password_hash(password)
        new_user = UserDB(username=username, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return True, f"用户 '{username}' 创建成功 (ID: {new_user.id})"
    except IntegrityError:
        db.rollback()
        return False, f"用户 '{username}' 创建失败：用户名已存在"
    except Exception as e:
        db.rollback()
        return False, f"用户 '{username}' 创建失败：{str(e)}"


def import_user_from_args(
    username: str, password: str, skip_existing: bool = True
) -> None:
    """
    从命令行参数导入单个用户

    Args:
        username: 用户名
        password: 密码
        skip_existing: 如果用户已存在，是否跳过
    """
    db: Session = SessionLocal()
    try:
        success, message = create_user(db, username, password, skip_existing)
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
    finally:
        db.close()


def import_users_from_csv(file_path: Path, skip_existing: bool = True) -> None:
    """
    从 CSV 文件批量导入用户

    CSV 文件格式：
    username,password
    admin,password123
    user1,password456

    Args:
        file_path: CSV 文件路径
        skip_existing: 如果用户已存在，是否跳过
    """
    if not file_path.exists():
        print(f"✗ 文件不存在: {file_path}")
        return

    db: Session = SessionLocal()
    success_count = 0
    skip_count = 0
    error_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # 验证 CSV 文件格式
            if (
                "username" not in reader.fieldnames
                or "password" not in reader.fieldnames
            ):
                print("✗ CSV 文件格式错误：必须包含 'username' 和 'password' 列")
                return

            print(f"开始从文件导入用户: {file_path}")
            print("-" * 60)

            for row_num, row in enumerate(
                reader, start=2
            ):  # 从第2行开始（第1行是表头）
                username = row.get("username", "").strip()
                password = row.get("password", "").strip()

                if not username:
                    print(f"✗ 第 {row_num} 行：用户名为空，已跳过")
                    error_count += 1
                    continue

                if not password:
                    print(f"✗ 第 {row_num} 行：密码为空，已跳过")
                    error_count += 1
                    continue

                success, message = create_user(db, username, password, skip_existing)
                if success:
                    print(f"✓ 第 {row_num} 行：{message}")
                    success_count += 1
                elif "已存在" in message and skip_existing:
                    print(f"⊘ 第 {row_num} 行：{message}")
                    skip_count += 1
                else:
                    print(f"✗ 第 {row_num} 行：{message}")
                    error_count += 1

        print("-" * 60)
        print(
            f"导入完成：成功 {success_count} 个，跳过 {skip_count} 个，失败 {error_count} 个"
        )

    except Exception as e:
        print(f"✗ 读取文件失败: {str(e)}")
    finally:
        db.close()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="导入用户到数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入单个用户
  python scripts/import_users.py --username admin --password password123

  # 从 CSV 文件批量导入
  python scripts/import_users.py --file users.csv

  # 从 CSV 文件导入，如果用户已存在则报错（不跳过）
  python scripts/import_users.py --file users.csv --no-skip-existing
        """,
    )

    # 创建互斥组：要么提供用户名密码，要么提供文件
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-u",
        "--username",
        type=str,
        help="用户名",
    )
    group.add_argument(
        "-f",
        "--file",
        type=str,
        help="CSV 文件路径（包含 username 和 password 列）",
    )

    parser.add_argument(
        "-p",
        "--password",
        type=str,
        help="密码（与 --username 一起使用）",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="如果用户已存在，不跳过而是报错（默认：跳过已存在的用户）",
    )

    args = parser.parse_args()

    skip_existing = not args.no_skip_existing

    # 导入单个用户
    if args.username:
        if not args.password:
            parser.error("使用 --username 时必须提供 --password")
        import_user_from_args(args.username, args.password, skip_existing)

    # 从文件批量导入
    elif args.file:
        file_path = Path(args.file)
        import_users_from_csv(file_path, skip_existing)


if __name__ == "__main__":
    main()
