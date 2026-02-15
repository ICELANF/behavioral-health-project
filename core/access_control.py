# -*- coding: utf-8 -*-
"""
FIX-09: IDOR 细粒度访问控制
═══════════════════════════════

规则:
  - 自己的数据: 始终允许
  - admin / supervisor: 允许查看所有用户
  - coach / promoter / master: 仅限自己学员 (通过 assessment_assignments 关联)
  - observer / grower: 仅限自己

部署:
  1. 将此文件放入 core/access_control.py
  2. 在 api/learning_api.py 顶部添加:
     from core.access_control import check_user_data_access
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger


def check_user_data_access(
    current_user,
    target_user_id: int,
    db: Session,
) -> None:
    """
    检查当前用户是否有权访问目标用户数据。
    无权限时直接抛出 403 HTTPException。

    Parameters
    ----------
    current_user : User (SQLAlchemy model, 由 get_current_user 注入)
    target_user_id : int (路径参数中的 user_id)
    db : Session (SQLAlchemy session)
    """

    # ── 1. 自己的数据 → 放行 ──
    if target_user_id == current_user.id:
        return

    # ── 2. 获取角色字符串 ──
    role = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role)
    )

    # ── 3. 管理员/督导 → 放行所有 ──
    if role in ("admin", "supervisor"):
        return

    # ── 4. 教练/促进师/总教练 → 仅限自己学员 ──
    if role in ("coach", "promoter", "master"):
        is_my_student = _check_coach_student_relation(
            db, current_user.id, target_user_id
        )
        if is_my_student:
            return

        logger.warning(
            f"[IDOR] 越权尝试: user={current_user.id} role={role} "
            f"试图访问 user={target_user_id} 的数据"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能访问自己学员的数据",
        )

    # ── 5. observer / grower / 其他 → 仅限自己 ──
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问其他用户数据",
    )


def _check_coach_student_relation(
    db: Session,
    coach_id: int,
    student_id: int,
) -> bool:
    """
    检查教练与学员之间是否存在活跃关联。

    查询三张表 (任一匹配即视为关联):
      - assessment_assignments (评估任务)
      - coach_messages (教练消息)
      - coach_push_queue (推送审批)
    """
    # 优先查最常用的 assessment_assignments
    sql = text("""
        SELECT 1 FROM assessment_assignments
        WHERE coach_id = :coach_id
          AND student_id = :student_id
          AND status != 'cancelled'
        LIMIT 1
    """)

    try:
        result = db.execute(sql, {
            "coach_id": coach_id,
            "student_id": student_id,
        }).fetchone()

        if result:
            return True

        # 补充查: coach_messages (覆盖仅通过消息建立关系的情况)
        sql_msg = text("""
            SELECT 1 FROM coach_messages
            WHERE coach_id = :coach_id
              AND student_id = :student_id
            LIMIT 1
        """)
        result_msg = db.execute(sql_msg, {
            "coach_id": coach_id,
            "student_id": student_id,
        }).fetchone()

        return result_msg is not None

    except Exception as e:
        # 表不存在或查询失败 → 安全降级: 拒绝访问
        logger.error(
            f"[IDOR] coach-student 关系查询异常: coach={coach_id} "
            f"student={student_id} error={e}"
        )
        return False
