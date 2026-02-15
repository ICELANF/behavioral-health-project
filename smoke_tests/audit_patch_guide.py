"""
审计补全补丁 — 补全 Sheet⑮ 标注的3个⬜审计端点
目标端点: survey.create / exam.create / exam.submit
工作量: ~0.5天

使用方式:
1. 定位项目中现有的审计中间件/装饰器（参考 audit_core_path.py）
2. 将下方模式应用到对应的路由函数

前置假设: 项目已有 UserActivityLog 写入机制（V2.4确认审计覆盖≥50%）
"""

# ============================================================
# 模式A: 如果使用装饰器方式（推荐）
# ============================================================

"""
在现有审计装饰器基础上，给3个端点加上 @audit_log 装饰器。

示例 — 找到 survey 路由文件（通常在 api/v1/survey.py 或 routers/survey.py）:

# === survey.create ===
@router.post("/surveys", ...)
@audit_log(event_type="survey.create", resource_type="survey")  # ← 加这行
async def create_survey(survey_in: SurveyCreate, ...):
    ...

# === exam.create ===
@router.post("/exams", ...)
@audit_log(event_type="exam.create", resource_type="exam")  # ← 加这行
async def create_exam(exam_in: ExamCreate, ...):
    ...

# === exam.submit ===
@router.post("/exams/{exam_id}/submit", ...)
@audit_log(event_type="exam.submit", resource_type="exam")  # ← 加这行
async def submit_exam(exam_id: str, ...):
    ...
"""

# ============================================================
# 模式B: 如果使用中间件方式
# ============================================================

"""
在审计中间件的事件映射表中添加3条规则。
找到类似 AUDIT_EVENT_MAP 或 audit_routes 的配置:

AUDIT_EVENT_MAP = {
    # ... 现有映射 ...

    # 新增3条 — Sheet⑮ 审计补全
    ("POST", "/api/v1/surveys"): "survey.create",
    ("POST", "/api/v1/exams"): "exam.create",
    ("POST", "/api/v1/exams/{exam_id}/submit"): "exam.submit",
}
"""

# ============================================================
# 模式C: 如果需要手动写入 UserActivityLog
# ============================================================

AUDIT_PATCH_TEMPLATE = '''
# 在每个端点的业务逻辑之后，return之前插入:

from app.models.activity_log import UserActivityLog  # 按实际路径调整
from app.core.database import get_db

async def _write_audit(
    db,
    user_id: str,
    event_type: str,
    resource_type: str,
    resource_id: str = None,
    metadata: dict = None,
):
    """通用审计写入（如果项目没有统一的审计工具函数，用这个）"""
    log = UserActivityLog(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
    )
    db.add(log)
    await db.flush()  # 不单独commit，跟随业务事务

# --- 在 create_survey 中 ---
await _write_audit(db, current_user.id, "survey.create", "survey",
                   resource_id=str(new_survey.id),
                   metadata={"title": survey_in.title})

# --- 在 create_exam 中 ---
await _write_audit(db, current_user.id, "exam.create", "exam",
                   resource_id=str(new_exam.id),
                   metadata={"title": exam_in.title, "type": exam_in.exam_type})

# --- 在 submit_exam 中 ---
await _write_audit(db, current_user.id, "exam.submit", "exam",
                   resource_id=exam_id,
                   metadata={"score": result.score, "passed": result.passed})
'''

# ============================================================
# 验证脚本 — 确认补丁生效
# ============================================================

VERIFY_SCRIPT = '''
"""运行于补丁后，验证审计日志写入"""
import httpx

API = "http://localhost:8000/api/v1"

def verify_audit_patch():
    # 1. 登录Admin
    login = httpx.post(f"{API}/auth/login",
        json={"email": "admin@xingjian.local", "password": "Admin@2026!"})
    token = login.json().get("access_token") or login.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 查询审计日志
    for event_type in ["survey.create", "exam.create", "exam.submit"]:
        r = httpx.get(f"{API}/admin/audit-logs", headers=headers,
                      params={"event_type": event_type, "limit": 1})
        if r.status_code == 200:
            items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
            status = "✅" if items else "⬜ (无记录，需触发一次操作)"
        else:
            status = f"❌ ({r.status_code})"
        print(f"  {event_type}: {status}")

if __name__ == "__main__":
    print("审计补丁验证:")
    verify_audit_patch()
'''

if __name__ == "__main__":
    print("=" * 60)
    print("审计补全补丁说明")
    print("=" * 60)
    print()
    print("目标: 为以下3个端点补全审计日志写入")
    print("  1. survey.create  (POST /surveys)")
    print("  2. exam.create    (POST /exams)")
    print("  3. exam.submit    (POST /exams/{id}/submit)")
    print()
    print("步骤:")
    print("  1. 确认项目现有审计机制（装饰器/中间件/手动）")
    print("  2. 按对应模式(A/B/C)添加审计写入")
    print("  3. 运行验证脚本确认生效")
    print()
    print("预计工时: 0.5天（含测试）")
