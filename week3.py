#!/usr/bin/env python3
"""
V4.1 Week 3: API网关 + 跨层通信 — 执行清单

    python week3.py step1   # Alembic迁移（绑定表+审计表+回填）
    python week3.py step2   # 替换gateway/目录
    python week3.py step3   # 注册网关路由到main.py
    python week3.py step4   # 验证 + 冒烟回归
    python week3.py rollback
"""
import sys


def step1():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1/4: Alembic迁移 — 绑定表 + 审计表
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  新增2张表:
    coach_schema.coach_student_bindings  — 教练-学员权威绑定
    public.cross_layer_audit_log         — 跨层访问审计

  执行:
    1. 复制迁移文件:
       cp migrations/v41_week3_001_gateway_infra.py alembic/versions/

    2. 编辑 down_revision (查 alembic heads 获取当前head)

    3. 运行迁移:
       alembic upgrade head

    4. 检查回填结果:
       psql -U postgres -d xingjian -c "
         SELECT binding_type, COUNT(*)
         FROM coach_schema.coach_student_bindings
         GROUP BY binding_type;
       "

  完成后: python week3.py step2
""")


def step2():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 2/4: 替换 gateway/ 目录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  用新的实现替换脚手架:

    cp gateway/auth.py      项目路径/gateway/auth.py
    cp gateway/sanitizer.py 项目路径/gateway/sanitizer.py
    cp gateway/router.py    项目路径/gateway/router.py

  重要: 修改3个文件中的 import 路径:
    - from app.core.database import get_db
    - from app.core.auth import get_current_user
    - from app.models.user import User

    根据你的实际项目结构调整这些import。

  脱敏自测:
    python gateway/sanitizer.py
    # 期望: ✅ 所有脱敏测试通过

  完成后: python week3.py step3
""")


def step3():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 3/4: 注册网关路由
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  gateway/router.py 已包含 prefix="/v1/gateway"。
  如果 Week 1 已经注册过 gateway router，只需确认 import 更新:

    # main.py
    from gateway.router import router as gateway_router
    app.include_router(gateway_router)  # 已有则不用改

  新增的6个端点:
    GET  /v1/gateway/patient/{user_id}/profile      教练看学员(脱敏)
    GET  /v1/gateway/patient/{user_id}/assessments   评估摘要
    GET  /v1/gateway/patient/{user_id}/journey       旅程状态
    POST /v1/gateway/rx-delivery/{user_id}           处方下发
    GET  /v1/gateway/audit-log                       审计日志
    GET  /v1/gateway/bindings                        学员列表

  完成后: python week3.py step4
""")


def step4():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 4/4: 验证 + 冒烟回归
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 网关端点验证:
     # 教练Token
     COACH_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \\
       -d 'username=coach&password=xxx' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

     # 查看学员列表
     curl -H "Authorization: Bearer $COACH_TOKEN" \\
       http://localhost:8000/v1/gateway/bindings

     # 查看学员资料（脱敏）
     curl -H "Authorization: Bearer $COACH_TOKEN" \\
       http://localhost:8000/v1/gateway/patient/{user_id}/profile

     # 期望: email=z***@example.com, phone=138****5678, 无password_hash

  2. 审计日志验证:
     # Admin Token
     curl -H "Authorization: Bearer $ADMIN_TOKEN" \\
       http://localhost:8000/v1/gateway/audit-log

  3. 冒烟回归:
     python -m pytest smoke_tests/ -v --tb=short
     # 期望: 71P/0F/12S (无回归)

  4. 提交:
     git add gateway/ alembic/versions/v41_week3*
     git commit -m "V4.1 Week3: API网关上线 (授权+脱敏+处方下发+审计)"
     git push
""")


def rollback():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  回滚
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  alembic downgrade -1
  # 删除 coach_student_bindings 和 cross_layer_audit_log
  # gateway路由会返回500但不影响其他端点
""")


COMMANDS = {"step1": step1, "step2": step2, "step3": step3, "step4": step4, "rollback": rollback}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(__doc__)
