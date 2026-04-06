"""
数据校验工具 — 独立 GUI 版本
用于在无数据库环境的 Windows 机器上校验生产信息与员工工作量数据。
使用 PyInstaller 打包为单个 .exe 后可直接运行。
"""

import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock 数据库相关模块（必须在 import app.* 之前执行）
# 校验逻辑只使用 Pydantic 模型，不需要真正的数据库连接。
# ---------------------------------------------------------------------------
from sqlalchemy.orm import declarative_base

_mock_db = MagicMock()
_mock_db.Base = declarative_base()
sys.modules.setdefault("app.database", _mock_db)
sys.modules.setdefault("app.config", MagicMock())

# 确保 src/ 在 import path 中（开发环境直接运行时需要）
_project_root = Path(__file__).resolve().parent.parent
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from app.utils.data_vld import validate_production_and_worklog  # noqa: E402
from app.utils.enums import VldResultEnum  # noqa: E402
from app.utils.parse_util import (  # noqa: E402
    parse_employee_worklogs_from_excel,
    parse_production_excel,
)

# ---------------------------------------------------------------------------
# 结果导出
# ---------------------------------------------------------------------------


def export_results_to_excel(exception_result, normal_result, output_path: str):
    """将校验结果导出为 Excel 文件（异常 + 正常 两个 Sheet）。"""
    import pandas as pd

    exception_rows = []
    for (order_no, except_enum), worklog_list in exception_result.items():
        for w in worklog_list:
            exception_rows.append(
                {
                    "生产订单号": w.order_no,
                    "异常类型": (
                        except_enum.value
                        if isinstance(except_enum, VldResultEnum)
                        else str(except_enum)
                    ),
                    "工号": w.employee_id,
                    "姓名": w.employee_name or "",
                    "数量": w.quantity,
                    "绩效系数": w.performance_factor,
                    "绩效数量": w.performance_amount,
                    "工作日期": (
                        w.work_date.strftime("%Y-%m-%d") if w.work_date else ""
                    ),
                }
            )

    normal_rows = []
    for order_no, worklog_list in normal_result.items():
        for w in worklog_list:
            normal_rows.append(
                {
                    "生产订单号": w.order_no,
                    "工号": w.employee_id,
                    "姓名": w.employee_name or "",
                    "数量": w.quantity,
                    "绩效系数": w.performance_factor,
                    "绩效数量": w.performance_amount,
                    "工作日期": (
                        w.work_date.strftime("%Y-%m-%d") if w.work_date else ""
                    ),
                }
            )

    df_exception = pd.DataFrame(exception_rows) if exception_rows else pd.DataFrame()
    df_normal = pd.DataFrame(normal_rows) if normal_rows else pd.DataFrame()

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_exception.to_excel(writer, sheet_name="异常数据", index=False)
        df_normal.to_excel(writer, sheet_name="正常数据", index=False)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------


class DataValidatorApp:
    WINDOW_TITLE = "数据校验工具"
    WINDOW_SIZE = "720x580"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.resizable(False, False)

        self._production_path = tk.StringVar()
        self._worklog_path = tk.StringVar()
        self._filter_month = tk.StringVar(value=datetime.now().strftime("%Y%m"))

        self._build_ui()

    # ---- UI 构建 ----

    def _build_ui(self):
        pad = {"padx": 12, "pady": 6}

        # 生产信息文件
        frame1 = ttk.LabelFrame(self.root, text="生产信息 Excel", padding=8)
        frame1.pack(fill="x", **pad)
        ttk.Entry(frame1, textvariable=self._production_path, width=72).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(
            frame1, text="选择文件", command=self._pick_production_file
        ).pack(side="left")

        # 工作量文件
        frame2 = ttk.LabelFrame(self.root, text="员工工作量 Excel", padding=8)
        frame2.pack(fill="x", **pad)
        ttk.Entry(frame2, textvariable=self._worklog_path, width=72).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(frame2, text="选择文件", command=self._pick_worklog_file).pack(
            side="left"
        )

        # 月份过滤
        frame3 = ttk.Frame(self.root, padding=8)
        frame3.pack(fill="x", **pad)
        ttk.Label(frame3, text="过滤月份（格式 yyyyMM，如 202603）：").pack(
            side="left"
        )
        ttk.Entry(frame3, textvariable=self._filter_month, width=12).pack(
            side="left", padx=(4, 0)
        )

        # 校验按钮
        btn_frame = ttk.Frame(self.root, padding=4)
        btn_frame.pack(fill="x", **pad)
        self._run_btn = ttk.Button(
            btn_frame, text="开始校验", command=self._on_run
        )
        self._run_btn.pack()

        # 进度提示
        self._progress_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self._progress_var, foreground="gray").pack(
            **pad
        )

        # 结果展示
        result_frame = ttk.LabelFrame(self.root, text="校验结果", padding=8)
        result_frame.pack(fill="both", expand=True, **pad)
        self._result_text = tk.Text(
            result_frame, wrap="word", height=14, state="disabled"
        )
        scrollbar = ttk.Scrollbar(
            result_frame, orient="vertical", command=self._result_text.yview
        )
        self._result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._result_text.pack(fill="both", expand=True)

    # ---- 文件选择 ----

    def _pick_production_file(self):
        path = filedialog.askopenfilename(
            title="选择生产信息 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
        )
        if path:
            self._production_path.set(path)

    def _pick_worklog_file(self):
        path = filedialog.askopenfilename(
            title="选择员工工作量 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")],
        )
        if path:
            self._worklog_path.set(path)

    # ---- 校验逻辑（在子线程执行，避免界面卡死） ----

    def _on_run(self):
        prod_path = self._production_path.get().strip()
        wl_path = self._worklog_path.get().strip()
        month = self._filter_month.get().strip()

        if not prod_path or not os.path.isfile(prod_path):
            messagebox.showwarning("提示", "请先选择有效的生产信息 Excel 文件。")
            return
        if not wl_path or not os.path.isfile(wl_path):
            messagebox.showwarning("提示", "请先选择有效的员工工作量 Excel 文件。")
            return
        if not month or len(month) != 6 or not month.isdigit():
            messagebox.showwarning(
                "提示", "过滤月份格式不正确，请输入 6 位数字，如 202603。"
            )
            return

        self._run_btn.config(state="disabled")
        self._progress_var.set("正在校验，请稍候...")
        self._clear_result()

        threading.Thread(
            target=self._run_validation,
            args=(prod_path, wl_path, month),
            daemon=True,
        ).start()

    def _run_validation(self, prod_path: str, wl_path: str, month: str):
        try:
            production_list = parse_production_excel(prod_path, filter_month=month)
            worklog_list = parse_employee_worklogs_from_excel(wl_path)

            exception_result, normal_result = validate_production_and_worklog(
                production_list, worklog_list
            )

            out_dir = os.path.dirname(wl_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_filename = f"校验结果_{month}_{timestamp}.xlsx"
            out_path = os.path.join(out_dir, out_filename)

            export_results_to_excel(exception_result, normal_result, out_path)

            total_exception_rows = sum(len(v) for v in exception_result.values())
            total_normal_rows = sum(len(v) for v in normal_result.values())

            lines = [
                f"解析生产信息: {len(production_list)} 条",
                f"解析员工工作量: {len(worklog_list)} 条",
                "",
                "===== 校验结果 =====",
                f"异常订单数: {len(exception_result)}（共 {total_exception_rows} 条明细）",
                f"正常订单数: {len(normal_result)}（共 {total_normal_rows} 条明细）",
                "",
            ]

            if exception_result:
                lines.append("----- 异常明细 -----")
                for (order_no, except_enum), wl_list in exception_result.items():
                    enum_label = (
                        except_enum.value
                        if isinstance(except_enum, VldResultEnum)
                        else str(except_enum)
                    )
                    lines.append(
                        f"  订单号: {order_no}  |  异常: {enum_label}  |  涉及 {len(wl_list)} 条"
                    )
                lines.append("")

            lines.append(f"结果已导出到:\n{out_path}")

            self.root.after(0, self._show_result, "\n".join(lines))
            self.root.after(0, self._progress_var.set, "校验完成！")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "完成", f"校验完成！\n结果文件已保存到:\n{out_path}"
                ),
            )

        except Exception as e:
            self.root.after(0, self._show_result, f"校验出错:\n{e}")
            self.root.after(0, self._progress_var.set, "校验出错")
            self.root.after(
                0,
                lambda: messagebox.showerror("错误", f"校验过程中出错:\n{e}"),
            )
        finally:
            self.root.after(0, lambda: self._run_btn.config(state="normal"))

    # ---- 结果展示辅助 ----

    def _clear_result(self):
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.config(state="disabled")

    def _show_result(self, text: str):
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.insert("1.0", text)
        self._result_text.config(state="disabled")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main():
    root = tk.Tk()
    DataValidatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
