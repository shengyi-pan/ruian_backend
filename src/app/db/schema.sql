-- 数据库表创建脚本
-- 包括：users, production_info, employee_worklog

ALTER DATABASE postgres SET timezone = 'Asia/Shanghai';

-- 1. 用户登录验证表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

-- 2. 生产信息表
-- 生产订单的工种配置与数量（来自"上传订单信息 Excel"）
CREATE TABLE IF NOT EXISTS production_info (
    id BIGSERIAL PRIMARY KEY,
    order_no TEXT NOT NULL, -- 生产订单号（如 2516572）
    model TEXT NOT NULL, -- 产品型号（如 W/mG000-AMP）
    brand_no TEXT NOT NULL, -- 牌号（如 GXZYD00652946）
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    job_type TEXT NOT NULL, -- 工种（如 钝化 / 烧结）
    worklog_no TEXT NOT NULL, -- 转出工序计划号，用于关联工作量表
    performance_factor NUMERIC(6,2) NOT NULL CHECK (performance_factor > 0),
    upload_date TIMESTAMPTZ NOT NULL DEFAULT now(), -- 上传日期（展示列）
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- 同一订单 + 型号 + 牌号 + 工种 + 上传日期 只保留一条，防重复导入
    CONSTRAINT uq_prodinfo UNIQUE (order_no, model, brand_no, job_type, upload_date)
);

-- 常用查询索引
CREATE INDEX IF NOT EXISTS idx_prodinfo_order_date ON production_info (order_no, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_prodinfo_job_type ON production_info (job_type);
CREATE INDEX IF NOT EXISTS idx_prodinfo_worklog_no ON production_info (worklog_no);

-- 3. 员工工作量表
-- 员工按天的计件/工作量明细（来自"上传计件信息 excel"）
CREATE TABLE IF NOT EXISTS employee_worklog (
    id BIGSERIAL PRIMARY KEY,
    order_no TEXT NOT NULL, -- 生产订单号（如 2516572）
    model TEXT, -- 型号（如 W/mG000-AMP）
    brand_no TEXT, -- 牌号（如 07912）
    employee_id TEXT NOT NULL, -- 工号（如 024）
    employee_name TEXT, -- 姓名（如 张三）
    job_type TEXT NOT NULL, -- 工种（如 钝化）
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    performance_factor NUMERIC(6,2) NOT NULL CHECK (performance_factor > 0),
    -- 绩效数量 = 数量 × 绩效系数
    performance_amount NUMERIC(18,2) NOT NULL CHECK (performance_amount > 0),
    work_date TIMESTAMPTZ NOT NULL DEFAULT now(), -- 工作日期（如 2025-11-08）
    upload_date TIMESTAMPTZ NOT NULL DEFAULT now(), -- 导入日期（可选展示）
    validation_result TEXT NOT NULL DEFAULT '未校验', -- 校验结果
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 常用查询索引
CREATE INDEX IF NOT EXISTS idx_worklog_emp_date ON employee_worklog (employee_id, work_date DESC);
CREATE INDEX IF NOT EXISTS idx_worklog_order_date ON employee_worklog (order_no, work_date DESC);
CREATE INDEX IF NOT EXISTS idx_worklog_job_date ON employee_worklog (job_type, work_date DESC);

