"""
评估API端点
Assessment API Endpoints

提供评估数据的CRUD操作
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from loguru import logger

from core.database import get_db
from core.models import Assessment, User, TriggerRecord
from api.dependencies import get_current_user

# 创建路由器
router = APIRouter(prefix="/api/assessment", tags=["评估"])


# ============================================
# 响应模型
# ============================================

def assessment_to_dict(assessment: Assessment) -> dict:
    """将Assessment对象转换为字典"""
    return {
        "assessment_id": assessment.assessment_id,
        "timestamp": assessment.created_at.isoformat(),
        "text_content": assessment.text_content,
        "glucose_values": assessment.glucose_values or [],
        "hrv_values": assessment.hrv_values or [],
        "risk_assessment": {
            "risk_level": assessment.risk_level.value,
            "risk_score": assessment.risk_score,
            "primary_concern": assessment.primary_concern,
            "urgency": assessment.urgency,
            "reasoning": assessment.reasoning,
            "severity_distribution": assessment.severity_distribution or {}
        },
        "triggers": [
            {
                "tag_id": t.tag_id,
                "name": t.name,
                "category": t.category.value,
                "severity": t.severity.value,
                "confidence": t.confidence,
                "evidence": t.trigger_metadata.get("evidence", []) if t.trigger_metadata else []
            }
            for t in assessment.triggers
        ],
        "routing_decision": {
            "primary_agent": assessment.primary_agent.value,
            "secondary_agents": assessment.secondary_agents or [],
            "priority": assessment.priority,
            "response_time": assessment.response_time,
            "recommended_actions": assessment.recommended_actions or []
        }
    }


# ============================================
# API端点
# ============================================

@router.get("/recent/{user_id}")
def get_recent_assessments(
    user_id: int,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户最近的评估记录

    Args:
        user_id: 用户ID
        limit: 返回数量限制（默认5条）

    Returns:
        评估记录列表
    """
    try:
        # 验证权限（用户只能查看自己的数据，管理员可以查看所有）
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问其他用户的数据"
            )

        # 查询最近的评估记录
        assessments = db.query(Assessment).filter(
            Assessment.user_id == user_id,
            Assessment.status == "completed"
        ).order_by(
            Assessment.created_at.desc()
        ).limit(limit).all()

        logger.info(f"✓ 获取用户 {user_id} 最近 {len(assessments)} 条评估记录")

        return [assessment_to_dict(a) for a in assessments]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最近评估失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评估记录失败: {str(e)}"
        )


@router.get("/history/{user_id}")
def get_assessment_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户评估历史（分页）

    Args:
        user_id: 用户ID
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        评估记录列表
    """
    try:
        # 验证权限
        if current_user.role.value != "admin" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问其他用户的数据"
            )

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询评估历史
        assessments = db.query(Assessment).filter(
            Assessment.user_id == user_id,
            Assessment.status == "completed"
        ).order_by(
            Assessment.created_at.desc()
        ).offset(offset).limit(page_size).all()

        logger.info(f"✓ 获取用户 {user_id} 评估历史 (page={page}, size={page_size}): {len(assessments)} 条")

        return [assessment_to_dict(a) for a in assessments]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评估历史失败: {str(e)}"
        )


@router.get("/{assessment_id}")
def get_assessment_result(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个评估结果详情

    Args:
        assessment_id: 评估ID (ASS-xxx格式)

    Returns:
        评估结果详情
    """
    try:
        # 查询评估记录
        assessment = db.query(Assessment).filter(
            Assessment.assessment_id == assessment_id
        ).first()

        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评估记录不存在"
            )

        # 验证权限
        if current_user.role.value != "admin" and current_user.id != assessment.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此评估记录"
            )

        logger.info(f"✓ 获取评估详情: {assessment_id}")

        return assessment_to_dict(assessment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评估详情失败: {str(e)}"
        )


@router.post("/submit")
def submit_assessment(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交新的评估数据

    这个端点目前返回Mock数据，实际评估处理将在后续实现

    Args:
        data: 评估输入数据

    Returns:
        评估结果
    """
    try:
        # TODO: 实际的评估处理逻辑
        # 这里暂时返回一个示例结果

        logger.info(f"收到评估提交请求，用户: {current_user.username}")
        logger.info(f"数据: {data}")

        # 暂时返回Mock数据，提示前端使用Mock fallback
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="评估提交功能正在开发中，请使用前端Mock模式"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交评估失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交评估失败: {str(e)}"
        )
