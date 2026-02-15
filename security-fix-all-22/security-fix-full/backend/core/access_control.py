"""
访问控制辅助函数 (FIX-09)
教练只能访问自己学员的数据
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.models import User


def check_user_data_access(
    current_user: User,
    target_user_id: int,
    db: Session
):
    """
    检查当前用户是否有权访问目标用户数据

    规则:
    - 自己的数据: 始终允许
    - admin/supervisor: 允许所有
    - coach/promoter/master: 只能访问自己学员
    - observer/grower: 仅限自己
    """
    if target_user_id == current_user.id:
        return  # 自己的数据

    role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

    if role in ("admin", "supervisor"):
        return  # 管理员和督导可查看所有

    if role in ("coach", "promoter", "master"):
        # 检查是否是自己的学员
        is_my_student = db.execute(
            """
            SELECT 1 FROM coach_student_assignments
            WHERE coach_id = :coach_id AND student_id = :student_id
            AND status = 'active'
            LIMIT 1
            """,
            {"coach_id": current_user.id, "student_id": target_user_id}
        ).fetchone()

        if is_my_student:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能访问自己学员的数据"
        )

    # observer/grower — 仅限自己
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="无权访问其他用户数据"
    )
