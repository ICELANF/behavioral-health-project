"""
V4.1 Week2: ORM Schema配置 — 教练层表指向 coach_schema

用法:
    1. 运行 Alembic 迁移（表已移到 coach_schema）
    2. 在每个教练层 Model 中添加 __table_args__ 的 schema 配置
    3. 或者用本文件的 mixin 统一处理

两种方式任选其一:
    方式A: Mixin（推荐，改动最小）
    方式B: 逐Model修改 __table_args__
"""

# ═══════════════════════════════════════════════════════════
# 方式A: Mixin — 教练层Model继承此类即可
# ═══════════════════════════════════════════════════════════

COACH_SCHEMA = "coach_schema"


class CoachSchemaMixin:
    """
    教练层表的Schema Mixin

    用法:
        class AgentTemplate(CoachSchemaMixin, Base):
            __tablename__ = 'agent_templates'
            # ... 其余不变
    
    Mixin会自动把 __table_args__ 的 schema 设为 coach_schema
    """
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 合并已有的 __table_args__
        existing = getattr(cls, '__table_args__', None)
        if existing is None:
            cls.__table_args__ = {"schema": COACH_SCHEMA}
        elif isinstance(existing, dict):
            existing["schema"] = COACH_SCHEMA
            cls.__table_args__ = existing
        elif isinstance(existing, tuple):
            # tuple形式: (UniqueConstraint(...), {"key": "val"})
            args = list(existing)
            if args and isinstance(args[-1], dict):
                args[-1]["schema"] = COACH_SCHEMA
            else:
                args.append({"schema": COACH_SCHEMA})
            cls.__table_args__ = tuple(args)


# ═══════════════════════════════════════════════════════════
# 方式B: 逐Model修改指南
# ═══════════════════════════════════════════════════════════

MODEL_CHANGES = """
# 对以下12个Model文件，添加 schema 到 __table_args__:

# ── agent_feedbacks ──
# 文件: models/agent_feedback.py (或类似)
class AgentFeedback(Base):
    __tablename__ = 'agent_feedbacks'
    __table_args__ = {'schema': 'coach_schema'}  # ← 添加这行
    # ... 如果已有 __table_args__，把 schema 加进去

# ── agent_metrics_daily ──
class AgentMetricsDaily(Base):
    __tablename__ = 'agent_metrics_daily'
    __table_args__ = {'schema': 'coach_schema'}

# ── agent_prompt_versions ──
class AgentPromptVersion(Base):
    __tablename__ = 'agent_prompt_versions'
    __table_args__ = {'schema': 'coach_schema'}

# ── agent_templates ──
class AgentTemplate(Base):
    __tablename__ = 'agent_templates'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_exam_records ──
class CoachExamRecord(Base):
    __tablename__ = 'coach_exam_records'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_kpi_metrics ──
class CoachKpiMetric(Base):
    __tablename__ = 'coach_kpi_metrics'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_messages ──
class CoachMessage(Base):
    __tablename__ = 'coach_messages'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_push_queue ──
class CoachPushQueue(Base):
    __tablename__ = 'coach_push_queue'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_review_items ──
class CoachReviewItem(Base):
    __tablename__ = 'coach_review_items'
    __table_args__ = {'schema': 'coach_schema'}

# ── coach_supervision_records ──
class CoachSupervisionRecord(Base):
    __tablename__ = 'coach_supervision_records'
    __table_args__ = {'schema': 'coach_schema'}

# ── decision_trace ──
class DecisionTrace(Base):
    __tablename__ = 'decision_trace'
    __table_args__ = {'schema': 'coach_schema'}

# ── rx_prescriptions ──
class RxPrescription(Base):
    __tablename__ = 'rx_prescriptions'
    __table_args__ = {'schema': 'coach_schema'}
"""


# ═══════════════════════════════════════════════════════════
# 自动扫描并修改 — 批量添加 schema 到 Model 文件
# ═══════════════════════════════════════════════════════════

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime


COACH_TABLES = [
    'agent_feedbacks',
    'agent_metrics_daily',
    'agent_prompt_versions',
    'agent_templates',
    'coach_exam_records',
    'coach_kpi_metrics',
    'coach_messages',
    'coach_push_queue',
    'coach_review_items',
    'coach_supervision_records',
    'decision_trace',
    'rx_prescriptions',
]


def patch_models(app_dir: str, dry_run: bool = True):
    """扫描所有Model文件，给12张教练表添加schema配置"""
    app_path = Path(app_dir)
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\nORM Schema补丁 [{mode}]\n")

    patched = 0
    skipped = 0

    for py_file in sorted(app_path.rglob("*.py")):
        # 跳过venv/migration/test
        rel = str(py_file.relative_to(app_path))
        if any(skip in rel for skip in ['.venv', 'venv', 'migration', 'alembic',
                                         'test', '__pycache__', 'node_modules']):
            continue

        content = py_file.read_text(errors="ignore")

        # 找包含目标表名的Model定义
        for table in COACH_TABLES:
            pattern = rf"__tablename__\s*=\s*['\"]({re.escape(table)})['\"]"
            match = re.search(pattern, content)
            if not match:
                continue

            # 检查是否已有 coach_schema
            if "'coach_schema'" in content or '"coach_schema"' in content:
                print(f"  ⏭  {rel}: {table} — 已配置")
                skipped += 1
                continue

            print(f"  {'[DRY]' if dry_run else '[FIX]'} {rel}: {table}")

            if not dry_run:
                # 备份
                backup = py_file.with_suffix(f".py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
                shutil.copy2(py_file, backup)

                # 策略: 找 __table_args__ 并修改，或在 __tablename__ 后添加
                if '__table_args__' in content:
                    # 已有 __table_args__，添加 schema
                    if re.search(r"__table_args__\s*=\s*\{", content):
                        # dict形式
                        content = re.sub(
                            r"(__table_args__\s*=\s*\{)",
                            r'\1"schema": "coach_schema", ',
                            content, count=1,
                        )
                    elif re.search(r"__table_args__\s*=\s*\(", content):
                        # tuple形式 — 在最后一个元素后添加 {"schema": ...}
                        # 这个比较复杂，保守处理：添加注释提示手动修改
                        content = content.replace(
                            match.group(0),
                            f'{match.group(0)}\n    # TODO: V4.1 请手动添加 schema="coach_schema" 到 __table_args__',
                        )
                else:
                    # 没有 __table_args__，在 __tablename__ 后一行添加
                    content = content.replace(
                        match.group(0),
                        f'{match.group(0)}\n    __table_args__ = {{"schema": "coach_schema"}}',
                    )

                py_file.write_text(content)
            patched += 1

    print(f"\n结果: {patched}个需修改, {skipped}个已配置")
    if dry_run and patched > 0:
        print(f"\n确认后执行: python orm_schema_config.py patch {app_dir} --apply")


# ═══════════════════════════════════════════════════════════
# 验证 — 检查迁移后所有表可访问
# ═══════════════════════════════════════════════════════════

def verify_sql():
    """输出验证SQL"""
    print("""
-- ═══ V4.1 Schema迁移验证 SQL ═══

-- 1. 确认 coach_schema 已创建
SELECT schema_name FROM information_schema.schemata
WHERE schema_name = 'coach_schema';

-- 2. 确认12张表在 coach_schema 中
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_name IN (
    'agent_feedbacks', 'agent_metrics_daily', 'agent_prompt_versions',
    'agent_templates', 'coach_exam_records', 'coach_kpi_metrics',
    'coach_messages', 'coach_push_queue', 'coach_review_items',
    'coach_supervision_records', 'decision_trace', 'rx_prescriptions'
)
ORDER BY table_schema, table_name;

-- 3. 确认兼容view存在（过渡期）
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_name IN (
    'agent_feedbacks', 'agent_metrics_daily', 'agent_prompt_versions',
    'agent_templates', 'coach_exam_records', 'coach_kpi_metrics',
    'coach_messages', 'coach_push_queue', 'coach_review_items',
    'coach_supervision_records', 'decision_trace', 'rx_prescriptions'
)
AND table_schema = 'public'
AND table_type = 'VIEW'
ORDER BY table_name;

-- 4. 验证数据完整性（每张表的行数）
SELECT 'agent_feedbacks' as tbl, count(*) FROM coach_schema.agent_feedbacks
UNION ALL SELECT 'agent_metrics_daily', count(*) FROM coach_schema.agent_metrics_daily
UNION ALL SELECT 'agent_prompt_versions', count(*) FROM coach_schema.agent_prompt_versions
UNION ALL SELECT 'agent_templates', count(*) FROM coach_schema.agent_templates
UNION ALL SELECT 'coach_exam_records', count(*) FROM coach_schema.coach_exam_records
UNION ALL SELECT 'coach_kpi_metrics', count(*) FROM coach_schema.coach_kpi_metrics
UNION ALL SELECT 'coach_messages', count(*) FROM coach_schema.coach_messages
UNION ALL SELECT 'coach_push_queue', count(*) FROM coach_schema.coach_push_queue
UNION ALL SELECT 'coach_review_items', count(*) FROM coach_schema.coach_review_items
UNION ALL SELECT 'coach_supervision_records', count(*) FROM coach_schema.coach_supervision_records
UNION ALL SELECT 'decision_trace', count(*) FROM coach_schema.decision_trace
UNION ALL SELECT 'rx_prescriptions', count(*) FROM coach_schema.rx_prescriptions;

-- 5. 验证兼容view可读写
-- (通过view插入一条测试数据，然后删除)
-- INSERT INTO public.coach_messages (id, ...) VALUES (...);
-- SELECT * FROM coach_schema.coach_messages WHERE id = '...';
-- DELETE FROM public.coach_messages WHERE id = '...';
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python orm_schema_config.py patch /path/to/app [--dry-run|--apply]")
        print("  python orm_schema_config.py verify-sql")
        print("  python orm_schema_config.py show-mixin")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "patch":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        dry = "--apply" not in sys.argv
        patch_models(target, dry_run=dry)
    elif cmd == "verify-sql":
        verify_sql()
    elif cmd == "show-mixin":
        print(f"\n# CoachSchemaMixin 用法:\n")
        print(f"from orm_schema_config import CoachSchemaMixin\n")
        print(f"class AgentTemplate(CoachSchemaMixin, Base):")
        print(f"    __tablename__ = 'agent_templates'")
        print(f"    # ... 自动获得 schema='coach_schema'\n")
    else:
        print(f"未知: {cmd}")
