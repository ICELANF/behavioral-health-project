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

    接收用户输入，调用L2评估引擎处理，存储结果到数据库

    Args:
        data: 评估输入数据，包含:
            - text_content: 用户描述文本（可选）
            - glucose_values: 血糖值列表（可选）
            - hrv_values: HRV值列表（可选）
            - activity_data: 活动数据（可选）
            - sleep_data: 睡眠数据（可选）

    Returns:
        评估结果
    """
    try:
        import uuid

        logger.info(f"收到评估提交请求，用户: {current_user.username}")

        # 生成评估ID
        assessment_id = f"ASS-{uuid.uuid4().hex[:8].upper()}"

        # 尝试调用评估引擎
        risk_level = "R1"
        risk_score = 30.0
        primary_concern = "待评估"
        urgency = "moderate"
        primary_agent = "CoachingAgent"
        secondary_agents = []
        priority = 3
        response_time = "当日"
        recommended_actions = []
        reasoning = ""
        severity_distribution = {}

        try:
            from core.assessment_engine import AssessmentEngine
            engine = AssessmentEngine()

            # 构建引擎输入
            engine_input = {
                "user_id": str(current_user.id),
                "text": data.get("text_content", ""),
                "glucose_values": data.get("glucose_values"),
                "hrv_values": data.get("hrv_values"),
                "activity_data": data.get("activity_data"),
                "sleep_data": data.get("sleep_data"),
                "user_profile": current_user.profile or {},
            }

            result = engine.assess(engine_input)

            if result:
                risk_assessment = result.get("risk_assessment", {})
                routing = result.get("routing_decision", {})

                risk_level = risk_assessment.get("risk_level", "R1")
                risk_score = risk_assessment.get("risk_score", 30.0)
                primary_concern = risk_assessment.get("primary_concern", "")
                urgency = risk_assessment.get("urgency", "moderate")
                reasoning = risk_assessment.get("reasoning", "")
                severity_distribution = risk_assessment.get("severity_distribution", {})

                primary_agent = routing.get("primary_agent", "CoachingAgent")
                secondary_agents = routing.get("secondary_agents", [])
                priority = routing.get("priority", 3)
                response_time = routing.get("response_time", "当日")
                recommended_actions = routing.get("recommended_actions", [])

                logger.info(f"评估引擎处理完成: risk={risk_level}, score={risk_score}")

        except Exception as engine_error:
            logger.warning(f"评估引擎调用失败，使用基础评估: {engine_error}")

            # 基础评估逻辑（引擎不可用时的降级方案）
            glucose_values = data.get("glucose_values", [])
            hrv_values = data.get("hrv_values", [])
            text_content = data.get("text_content", "")

            concerns = []
            if glucose_values:
                max_glucose = max(glucose_values)
                if max_glucose > 13.0:
                    risk_level = "R3"
                    risk_score = 70.0
                    urgency = "high"
                    primary_agent = "GlucoseAgent"
                    concerns.append("严重高血糖")
                elif max_glucose > 10.0:
                    risk_level = "R2"
                    risk_score = 50.0
                    urgency = "moderate"
                    primary_agent = "GlucoseAgent"
                    concerns.append("高血糖")
                elif max_glucose > 7.0:
                    risk_level = "R1"
                    risk_score = 30.0
                    concerns.append("血糖偏高")

            if hrv_values and min(hrv_values) < 30:
                risk_score = max(risk_score, 55.0)
                secondary_agents.append("StressAgent")
                concerns.append("HRV偏低")

            # 关键词检测
            stress_keywords = ["压力", "焦虑", "紧张", "失眠", "烦躁"]
            if any(kw in text_content for kw in stress_keywords):
                secondary_agents.append("StressAgent")
                concerns.append("心理压力")

            primary_concern = "、".join(concerns) if concerns else "常规健康评估"
            recommended_actions = ["继续监测健康数据", "保持良好生活习惯"]
            reasoning = f"基础评估：发现 {len(concerns)} 个关注点"

        # 将字符串 risk_level 转换为枚举
        from core.models import RiskLevel, AgentType
        try:
            risk_level_enum = RiskLevel(risk_level)
        except (ValueError, KeyError):
            risk_level_enum = RiskLevel.R1

        try:
            agent_enum = AgentType(primary_agent)
        except (ValueError, KeyError):
            agent_enum = AgentType.COACHING

        # 存储评估结果
        assessment = Assessment(
            assessment_id=assessment_id,
            user_id=current_user.id,
            text_content=data.get("text_content"),
            glucose_values=data.get("glucose_values"),
            hrv_values=data.get("hrv_values"),
            activity_data=data.get("activity_data"),
            sleep_data=data.get("sleep_data"),
            user_profile_snapshot=current_user.profile,
            risk_level=risk_level_enum,
            risk_score=risk_score,
            primary_concern=primary_concern,
            urgency=urgency,
            severity_distribution=severity_distribution,
            reasoning=reasoning,
            primary_agent=agent_enum,
            secondary_agents=secondary_agents,
            priority=priority,
            response_time=response_time,
            recommended_actions=recommended_actions,
            status="completed",
            completed_at=datetime.utcnow(),
        )

        db.add(assessment)

        # 更新用户最后评估时间
        current_user.last_assessment_date = datetime.utcnow()

        db.commit()
        db.refresh(assessment)

        logger.info(f"✓ 评估提交成功: {assessment_id}, 风险等级: {risk_level}")

        # assessment_submit 积分
        try:
            from core.models import PointTransaction
            db.add(PointTransaction(
                user_id=current_user.id,
                action="assessment_submit",
                point_type="growth",
                amount=5,
            ))
            db.commit()
        except Exception as e:
            logger.warning(f"积分记录失败: {e}")

        return assessment_to_dict(assessment)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"提交评估失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交评估失败: {str(e)}"
        )


@router.get("/user/latest")
def get_latest_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户最新的评估记录"""
    try:
        assessment = db.query(Assessment).filter(
            Assessment.user_id == current_user.id,
            Assessment.status == "completed"
        ).order_by(Assessment.created_at.desc()).first()

        if not assessment:
            return {"message": "暂无评估记录", "data": None}

        return {"data": assessment_to_dict(assessment)}

    except Exception as e:
        logger.error(f"获取最新评估失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取最新评估失败: {str(e)}"
        )
