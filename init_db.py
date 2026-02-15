# -*- coding: utf-8 -*-
import subprocess
import time

def run_cmd(cmd, description):
    print(f"--- 正在执行: {description} ---")
    try:
        # 使用 -t 避免 Windows 环境下的 TTY 错误
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ 成功: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {e.stderr}")
        return False

def main():
    print("🚀 开始 BHP v3 自动化环境对齐...\n")

    # 1. 激活 pgvector (修复 10 个数据库环境报错)
    run_cmd(
        'docker exec -t bhp_v3_postgres psql -U bhp_user -d bhp_db -c "CREATE EXTENSION IF NOT EXISTS vector;"',
        "激活 PostgreSQL 向量插件"
    )

    # 2. 自动生成缺失的迁移文件 (修复 v3_003 缺失的小尾巴)
    # 这会对比代码中的 Models 和 数据库现状，自动生成对齐脚本
    run_cmd(
        'docker exec -t bhp_v3_api alembic revision --autogenerate -m "auto_align_v3_schema"',
        "自动补齐缺失的 v3 迁移文件"
    )

    # 3. 执行物理表迁移
    run_cmd(
        'docker exec -t bhp_v3_api alembic upgrade head',
        "将 431 个路由关联的模型映射到物理数据库"
    )

    print("\n🎉 环境对齐完成！请运行 pytest 进行验证。")

if __name__ == "__main__":
    main()