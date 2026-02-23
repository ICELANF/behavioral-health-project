"""
R4: 评估完成 → 自动角色升级触发器

功能:
  1. 监听评估完成事件 (assessment_sessions 全部module完成)
  2. 检查升级条件 (5个评估模块全部完成)
  3. 执行角色升级: observer(1) → grower(2)
  4. 初始化Grower数据 (创建streak记录、触发首次处方生成)
  5. 返回升级结果给前端 (前端据此跳转新首页)

部署:
  1. 复制到 api/ 目录
  2. 在评估完成的API端点中调用 check_and_upgrade()
  3. 或注册独立端点 POST /api/v1/assessment/complete-and-upgrade
"""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

logger = logging.getLogger("role_upgrade")

router = APIRouter(prefix="/api/v1", tags=["role-upgrade"])


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

class UpgradeCheckResponse(BaseModel):
    """升级检查结果"""
    eligible: bool
    current_role: str
    current_level: int
    target_role: Optional[str] = None
    target_level: Optional[int] = None
    reason: str = ""
    assessment_complete: bool = False
    modules_done: list[str] = []
    modules_missing: list[str] = []


class UpgradeExecuteResponse(BaseModel):
    """升级执行结果"""
    success: bool
    old_role: str
    new_role: str
    new_level: int
    new_role_level: int = 2
    message: str
    redirect_to: str = "/onboarding/grower"  # 前端跳转: 引导页


class SharerUpgradeCheckResponse(BaseModel):
    """Grower→Sharer 升级检查结果"""
    eligible: bool
    growth_points: int = 0
    contribution_points: int = 0
    growth_required: int = 500
    contribution_required: int = 50
    reason: str = ""


# ═══════════════════════════════════════════════════
# 升级条件
# ═══════════════════════════════════════════════════

REQUIRED_MODULES = {"ttm7", "big5", "bpt6", "capacity", "spi"}

ROLE_LEVEL_MAP = {
    "observer": 1,
    "grower": 2,
    "sharer": 3,
    "bhp_coach": 4,
    "bhp_promoter": 5,
    "bhp_master": 6,
    "admin": 99,
}


# ═══════════════════════════════════════════════════
# 核心逻辑: 检查升级条件
# ═══════════════════════════════════════════════════

async def check_upgrade_eligibility(
    db: AsyncSession, user_id: int
) -> UpgradeCheckResponse:
    """
    检查用户是否满足升级条件
    
    Observer → Grower 条件:
    1. 当前角色是 observer (role_level = 1)
    2. BAPS 五维评估全部完成 (ttm7 + big5 + bpt6 + capacity + spi)
    """
    # 查询用户当前角色
    user_stmt = text("SELECT id, role FROM users WHERE id = :uid")
    user_result = await db.execute(user_stmt, {"uid": user_id})
    user = user_result.mappings().first()

    if not user:
        return UpgradeCheckResponse(
            eligible=False, current_role="unknown", current_level=0,
            reason="用户不存在"
        )

    current_role = (user["role"] or "observer").lower()
    current_level = ROLE_LEVEL_MAP.get(current_role, 1)

    # 只处理 observer → grower 升级
    if current_level >= 2:
        return UpgradeCheckResponse(
            eligible=False, current_role=current_role, current_level=current_level,
            reason="已经是Grower或更高角色，无需升级",
            assessment_complete=True, modules_done=list(REQUIRED_MODULES),
        )

    # 查询已完成的评估模块
    # 尝试多种可能的表结构
    modules_done = set()
    
    try:
        # 方式1: assessment_sessions 表
        assess_stmt = text("""
            SELECT DISTINCT module_type 
            FROM assessment_sessions
            WHERE user_id = :uid AND status = 'completed'
        """)
        result = await db.execute(assess_stmt, {"uid": user_id})
        for row in result.fetchall():
            modules_done.add(row[0].lower())
    except Exception:
        pass

    if not modules_done:
        try:
            # 方式2: baps_results 表
            baps_stmt = text("""
                SELECT DISTINCT assessment_type
                FROM baps_results
                WHERE user_id = :uid AND completed = true
            """)
            result = await db.execute(baps_stmt, {"uid": user_id})
            for row in result.fetchall():
                modules_done.add(row[0].lower())
        except Exception:
            pass

    if not modules_done:
        try:
            # 方式3: user_assessments 表
            ua_stmt = text("""
                SELECT DISTINCT type
                FROM user_assessments
                WHERE user_id = :uid AND status = 'completed'
            """)
            result = await db.execute(ua_stmt, {"uid": user_id})
            for row in result.fetchall():
                modules_done.add(row[0].lower())
        except Exception:
            pass

    modules_missing = REQUIRED_MODULES - modules_done
    all_done = len(modules_missing) == 0

    return UpgradeCheckResponse(
        eligible=all_done,
        current_role=current_role,
        current_level=current_level,
        target_role="grower" if all_done else None,
        target_level=2 if all_done else None,
        reason="评估全部完成，可以升级" if all_done else f"还需完成: {', '.join(modules_missing)}",
        assessment_complete=all_done,
        modules_done=sorted(modules_done),
        modules_missing=sorted(modules_missing),
    )


# ═══════════════════════════════════════════════════
# 核心逻辑: 执行升级
# ═══════════════════════════════════════════════════

async def execute_upgrade(
    db: AsyncSession, user_id: int
) -> UpgradeExecuteResponse:
    """
    执行 Observer → Grower 升级
    
    步骤:
    1. 二次检查升级条件
    2. 更新 users.role + users.role_level
    3. 初始化 user_streaks 记录
    4. 触发首次处方生成 (通过 rx_composer Agent 或默认处方)
    5. 触发首次每日任务生成
    """
    # Step 1: 二次检查
    check = await check_upgrade_eligibility(db, user_id)
    if not check.eligible:
        return UpgradeExecuteResponse(
            success=False, old_role=check.current_role, new_role=check.current_role,
            new_level=check.current_level,
            message=f"升级失败: {check.reason}",
        )

    old_role = check.current_role

    # Step 2: 更新角色
    await db.execute(text("""
        UPDATE users 
        SET role = 'grower', updated_at = NOW()
        WHERE id = :uid
    """), {"uid": user_id})

    # Step 3: 初始化 streak
    await db.execute(text("""
        INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date, updated_at)
        VALUES (:uid, 0, 0, NULL, NOW())
        ON CONFLICT (user_id) DO NOTHING
    """), {"uid": user_id})

    # Step 4: 尝试触发处方生成
    try:
        await _generate_initial_prescription(db, user_id)
    except Exception as e:
        logger.warning(f"用户 {user_id} 初始处方生成失败: {e}，将使用默认处方")
        await _generate_default_prescription(db, user_id)

    # Step 5: 触发首次每日任务生成
    try:
        from api.r2_scheduler_agent import generate_daily_tasks_for_user
        from datetime import date
        await generate_daily_tasks_for_user(db, user_id, date.today())
    except Exception as e:
        logger.warning(f"用户 {user_id} 首次任务生成失败: {e}")

    await db.commit()

    logger.info(f"用户 {user_id}: {old_role} → grower 升级完成")

    return UpgradeExecuteResponse(
        success=True,
        old_role=old_role,
        new_role="grower",
        new_level=2,
        new_role_level=2,
        message="恭喜！您已完成健康评估，正式成为行健平台的成长者。从今天开始，我们为您定制了每日健康行动计划！",
        redirect_to="/onboarding/grower",
    )


# ═══════════════════════════════════════════════════
# API端点
# ═══════════════════════════════════════════════════

@router.get("/assessment/upgrade-check", response_model=UpgradeCheckResponse)
async def api_check_upgrade(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查当前用户是否满足升级条件"""
    return await check_upgrade_eligibility(db, current_user.id)


@router.post("/assessment/complete-and-upgrade", response_model=UpgradeExecuteResponse)
async def api_complete_and_upgrade(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    评估完成后调用此接口执行升级
    
    前端调用时机:
    1. 最后一个评估模块(SPI)提交成功后
    2. 前端调用此接口
    3. 收到 success=true → 跳转到 /grower/today
    4. 收到 success=false → 显示 message 提示缺少的模块
    """
    return await execute_upgrade(db, current_user.id)


# ═══════════════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════════════

async def _generate_initial_prescription(db: AsyncSession, user_id: int):
    """
    基于评估结果生成初始处方
    
    读取 BAPS 评估结果 → 调用 rx_composer 逻辑 → 写入 behavior_prescriptions
    
    TODO Phase 2: 接入完整的 rx_composer Agent
    """
    # 读取BPT分型
    bpt_type = "mixed"  # 默认
    try:
        bpt_stmt = text("""
            SELECT result_json->>'bpt_type' as bpt
            FROM assessment_sessions
            WHERE user_id = :uid AND module_type = 'bpt6' AND status = 'completed'
            ORDER BY completed_at DESC LIMIT 1
        """)
        result = await db.execute(bpt_stmt, {"uid": user_id})
        row = result.fetchone()
        if row and row[0]:
            bpt_type = row[0]
    except Exception:
        pass

    # 读取SPI/L层级
    l_level = "L3"  # 默认
    try:
        spi_stmt = text("""
            SELECT result_json->>'psychological_level' as level
            FROM assessment_sessions
            WHERE user_id = :uid AND module_type = 'spi' AND status = 'completed'
            ORDER BY completed_at DESC LIMIT 1
        """)
        result = await db.execute(spi_stmt, {"uid": user_id})
        row = result.fetchone()
        if row and row[0]:
            l_level = row[0]
    except Exception:
        pass

    # 根据L层级决定处方数量
    max_tasks = {"L1": 1, "L2": 1, "L3": 2, "L4": 3, "L5": 5}.get(l_level, 2)

    # 生成默认处方集
    await _generate_default_prescription(db, user_id, max_tasks)


async def _generate_default_prescription(db: AsyncSession, user_id: int, max_tasks: int = 2):
    """
    生成默认处方 (当评估数据不完整时的降级方案)
    
    默认处方:
    1. 营养: 记录三餐饮食
    2. 运动: 每日散步15分钟
    3. 监测: 血糖监测 (如果有相关病史)
    """
    default_rx = [
        {
            "target_behavior": "记录饮食",
            "frequency_dose": "每日3次",
            "time_place": "早、午、晚",
            "trigger_cue": "用餐前拍一张食物照片",
            "obstacle_plan": "如果忘记拍照，事后文字记录也可以",
            "domain": "nutrition",
            "difficulty_level": "easy",
        },
        {
            "target_behavior": "散步",
            "frequency_dose": "每日1次",
            "time_place": "下午或傍晚",
            "trigger_cue": "午休后穿上运动鞋",
            "obstacle_plan": "如果天气不好，在室内走动也算",
            "domain": "exercise",
            "difficulty_level": "easy",
        },
        {
            "target_behavior": "血糖监测",
            "frequency_dose": "每日1次",
            "time_place": "空腹",
            "trigger_cue": "晨起后第一件事",
            "obstacle_plan": "如果忘记空腹测量，餐前补测",
            "domain": "glucose",
            "difficulty_level": "easy",
        },
    ]

    for i, rx in enumerate(default_rx[:max_tasks]):
        rx_id = f"rx_default_{user_id}_{i+1}"
        await db.execute(text("""
            INSERT INTO behavior_prescriptions 
                (id, user_id, target_behavior, frequency_dose, time_place,
                 trigger_cue, obstacle_plan, domain, difficulty_level,
                 cultivation_stage, status, created_at)
            VALUES 
                (:id, :uid, :target, :freq, :time, :cue, :plan, :domain, :diff,
                 'startup', 'active', NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": rx_id, "uid": user_id,
            "target": rx["target_behavior"],
            "freq": rx["frequency_dose"],
            "time": rx["time_place"],
            "cue": rx["trigger_cue"],
            "plan": rx["obstacle_plan"],
            "domain": rx["domain"],
            "diff": rx["difficulty_level"],
        })


# ═══════════════════════════════════════════════════
# Grower → Sharer 升级
# ═══════════════════════════════════════════════════

async def check_sharer_eligibility(
    db: AsyncSession, user_id: int
) -> SharerUpgradeCheckResponse:
    """
    检查 Grower→Sharer 升级条件:
    - growth_points >= 500
    - contribution_points >= 50
    """
    # 查询用户角色
    user_result = await db.execute(
        text("SELECT id, role FROM users WHERE id = :uid"), {"uid": user_id}
    )
    user = user_result.mappings().first()
    if not user:
        return SharerUpgradeCheckResponse(eligible=False, reason="用户不存在")

    current_role = (user["role"] or "observer").lower()
    current_level = ROLE_LEVEL_MAP.get(current_role, 1)

    if current_level >= 3:
        return SharerUpgradeCheckResponse(
            eligible=False, growth_points=999, contribution_points=999,
            reason="已经是分享者或更高角色",
        )
    if current_level < 2:
        return SharerUpgradeCheckResponse(
            eligible=False, reason="需要先成为成长者(Grower)",
        )

    # 查询积分
    growth = contribution = 0
    try:
        stats_result = await db.execute(text("""
            SELECT COALESCE(growth_points, 0) AS gp,
                   COALESCE(contribution_points, 0) AS cp
            FROM user_learning_stats WHERE user_id = :uid
        """), {"uid": user_id})
        row = stats_result.mappings().first()
        if row:
            growth = row["gp"] or 0
            contribution = row["cp"] or 0
    except Exception:
        pass

    # 补充: 从 users.growth_points 获取 (可能更准确)
    if growth == 0:
        try:
            gp_result = await db.execute(
                text("SELECT COALESCE(growth_points, 0) AS gp FROM users WHERE id = :uid"),
                {"uid": user_id},
            )
            gp_row = gp_result.mappings().first()
            if gp_row:
                growth = max(growth, gp_row["gp"] or 0)
        except Exception:
            pass

    eligible = growth >= 500 and contribution >= 50
    if eligible:
        reason = "满足升级条件: 成长积分和贡献积分均已达标"
    else:
        parts = []
        if growth < 500:
            parts.append(f"成长积分 {growth}/500")
        if contribution < 50:
            parts.append(f"贡献积分 {contribution}/50")
        reason = f"尚未达标: {', '.join(parts)}"

    return SharerUpgradeCheckResponse(
        eligible=eligible,
        growth_points=growth,
        contribution_points=contribution,
        reason=reason,
    )


async def execute_sharer_upgrade(
    db: AsyncSession, user_id: int
) -> UpgradeExecuteResponse:
    """执行 Grower → Sharer 升级"""
    check = await check_sharer_eligibility(db, user_id)
    if not check.eligible:
        return UpgradeExecuteResponse(
            success=False, old_role="grower", new_role="grower",
            new_level=2, new_role_level=2,
            message=f"升级失败: {check.reason}",
        )

    await db.execute(text("""
        UPDATE users SET role = 'sharer', updated_at = NOW()
        WHERE id = :uid
    """), {"uid": user_id})
    await db.commit()

    logger.info(f"用户 {user_id}: grower → sharer 升级完成")

    return UpgradeExecuteResponse(
        success=True,
        old_role="grower",
        new_role="sharer",
        new_level=3,
        new_role_level=3,
        message="恭喜晋升为分享者！您现在可以引领同道者、分享健康经验，积累影响力了。",
        redirect_to="/onboarding/sharer",
    )


@router.get("/promotion/sharer-check", response_model=SharerUpgradeCheckResponse)
async def api_check_sharer_upgrade(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """检查当前用户是否满足 Grower→Sharer 升级条件"""
    return await check_sharer_eligibility(db, current_user.id)


@router.post("/promotion/upgrade-to-sharer", response_model=UpgradeExecuteResponse)
async def api_upgrade_to_sharer(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """执行 Grower→Sharer 升级"""
    return await execute_sharer_upgrade(db, current_user.id)
