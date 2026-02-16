#!/usr/bin/env python3
"""
V4.1 Week 2: 数据Schema分离 — 执行清单

总共4步，按顺序执行:
    python week2.py step1   # 备份数据库
    python week2.py step2   # 运行Alembic迁移（12表→coach_schema + 兼容view）
    python week2.py step3   # ORM Model补丁（添加schema配置）
    python week2.py step4   # 验证 + 冒烟回归
    python week2.py rollback # 如果出问题：完全回滚
"""
import sys


def step1():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1/4: 备份数据库
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  执行:

  # Windows (你的环境)
  pg_dump -U postgres -d xingjian -F c -f xingjian_pre_v41w2.dump

  # 或者只备份12张教练表
  pg_dump -U postgres -d xingjian -F c \\
    -t agent_feedbacks -t agent_metrics_daily -t agent_prompt_versions \\
    -t agent_templates -t coach_exam_records -t coach_kpi_metrics \\
    -t coach_messages -t coach_push_queue -t coach_review_items \\
    -t coach_supervision_records -t decision_trace -t rx_prescriptions \\
    -f coach_tables_backup.dump

  备份完成后: python week2.py step2
""")


def step2():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 2/4: 运行Alembic迁移
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  先把迁移文件复制到Alembic目录:

  cp migrations/v41_week2_001_coach_schema.py alembic/versions/

  重要: 编辑迁移文件，填入 down_revision:

  # 查看当前最新revision
  alembic heads

  # 编辑 v41_week2_001_coach_schema.py
  # 把 down_revision = None 改为 down_revision = '<当前head>'

  然后执行:

  alembic upgrade head

  检查结果:

  psql -U postgres -d xingjian -c "
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_name IN (
      'agent_feedbacks','agent_templates','coach_messages',
      'rx_prescriptions','decision_trace'
    )
    ORDER BY table_schema;
  "

  期望输出:
    coach_schema | agent_feedbacks      (真正的表)
    coach_schema | agent_templates
    coach_schema | coach_messages
    coach_schema | rx_prescriptions
    coach_schema | decision_trace
    public       | agent_feedbacks      (兼容view)
    public       | agent_templates
    ...

  确认后: python week2.py step3
""")


def step3():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 3/4: ORM Model补丁
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  注意: 因为有兼容view，这步是可选的。
  view会让旧ORM代码继续工作。
  但为了代码正确性，建议在ORM中明确schema。

  # 预览要修改哪些文件
  python orm_schema_config.py patch . --dry-run

  # 确认后执行
  python orm_schema_config.py patch . --apply

  # 或者用Mixin方式（不修改现有文件）:
  # 在 models/__init__.py 或 models/base.py 中添加:
  #
  #   from orm_schema_config import CoachSchemaMixin
  #
  # 然后让教练层Model继承它（下次有改动时逐个加）

  完成后: python week2.py step4
""")


def step4():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 4/4: 验证 + 冒烟回归
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. SQL验证:
     python orm_schema_config.py verify-sql
     # 复制输出的SQL到psql执行

  2. API验证:
     # 重启服务
     # 教练层端点
     curl http://localhost:8000/v1/professional/agents
     curl http://localhost:8000/api/v1/agent/list  # 旧路径兼容

     # 用户层端点
     curl http://localhost:8000/v1/assistant/agents

  3. 冒烟回归:
     cd xingjian_smoke && python run.py all
     # 或
     python -m pytest smoke_tests/ -v --tb=short

  期望: 71P/0F/12S（与Week 1一致，无回归）

  4. 全绿后提交:
     git add alembic/versions/v41_week2_001_coach_schema.py
     git add models/  # ORM修改
     git add orm_schema_config.py week2.py
     git commit -m "V4.1 Week2: coach_schema分离 (12表迁移+兼容view+ORM配置)"
     git push
""")


def rollback():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  回滚: 撤销Schema分离
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  方式1: Alembic回滚（推荐）
    alembic downgrade -1

  方式2: 手动SQL回滚
    psql -U postgres -d xingjian << 'SQL'
    -- 删除兼容view
    DROP VIEW IF EXISTS public.agent_feedbacks CASCADE;
    DROP VIEW IF EXISTS public.agent_metrics_daily CASCADE;
    DROP VIEW IF EXISTS public.agent_prompt_versions CASCADE;
    DROP VIEW IF EXISTS public.agent_templates CASCADE;
    DROP VIEW IF EXISTS public.coach_exam_records CASCADE;
    DROP VIEW IF EXISTS public.coach_kpi_metrics CASCADE;
    DROP VIEW IF EXISTS public.coach_messages CASCADE;
    DROP VIEW IF EXISTS public.coach_push_queue CASCADE;
    DROP VIEW IF EXISTS public.coach_review_items CASCADE;
    DROP VIEW IF EXISTS public.coach_supervision_records CASCADE;
    DROP VIEW IF EXISTS public.decision_trace CASCADE;
    DROP VIEW IF EXISTS public.rx_prescriptions CASCADE;

    -- 移回public
    ALTER TABLE coach_schema.agent_feedbacks SET SCHEMA public;
    ALTER TABLE coach_schema.agent_metrics_daily SET SCHEMA public;
    ALTER TABLE coach_schema.agent_prompt_versions SET SCHEMA public;
    ALTER TABLE coach_schema.agent_templates SET SCHEMA public;
    ALTER TABLE coach_schema.coach_exam_records SET SCHEMA public;
    ALTER TABLE coach_schema.coach_kpi_metrics SET SCHEMA public;
    ALTER TABLE coach_schema.coach_messages SET SCHEMA public;
    ALTER TABLE coach_schema.coach_push_queue SET SCHEMA public;
    ALTER TABLE coach_schema.coach_review_items SET SCHEMA public;
    ALTER TABLE coach_schema.coach_supervision_records SET SCHEMA public;
    ALTER TABLE coach_schema.decision_trace SET SCHEMA public;
    ALTER TABLE coach_schema.rx_prescriptions SET SCHEMA public;

    -- 删除schema
    DROP SCHEMA IF EXISTS coach_schema;
    SQL

  方式3: 从备份恢复
    pg_restore -U postgres -d xingjian -c xingjian_pre_v41w2.dump
""")


COMMANDS = {
    "step1": step1, "step2": step2, "step3": step3, "step4": step4,
    "rollback": rollback,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(__doc__)
