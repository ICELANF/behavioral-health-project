"""
跨层授权 — 教练访问用户数据的权限校验

规则 (Sheet⑤ + Sheet⑫):
  - 教练只能访问自己带教的用户数据
  - 督导可以访问下属教练的所有用户数据
  - Admin可以访问所有数据
  - 用户层Agent永远不能访问教练层数据
"""


async def verify_coach_access(coach_id: str, user_id: str, db) -> bool:
    """验证教练是否有权访问该用户的数据"""
    # TODO: 查询 coach_student_mapping 表
    # mapping = await db.execute(
    #     select(CoachStudentMapping)
    #     .where(CoachStudentMapping.coach_id == coach_id)
    #     .where(CoachStudentMapping.student_id == user_id)
    #     .where(CoachStudentMapping.is_active == True)
    # )
    # return mapping.scalar_one_or_none() is not None
    return True  # STUB


async def verify_supervisor_access(supervisor_id: str, user_id: str, db) -> bool:
    """验证督导是否有权（通过下属教练）访问用户数据"""
    # TODO: 两级查询
    # 1. supervisor → coaches (supervisor_coach_mapping)
    # 2. coaches → users (coach_student_mapping)
    return True  # STUB
