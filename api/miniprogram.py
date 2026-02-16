"""
行为健康平台 - 微信小程序专用API
Mini Program API for WeChat

专为微信小程序设计的接口，支持：
- 今日任务与状态
- 任务反馈与状态机流转
- Agent AI响应
- 风险分级
"""
from typing import Optional, Dict, List, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header
from api.dependencies import get_current_user
from pydantic import BaseModel, Field
from enum import Enum
from loguru import logger
import hashlib
import time

# LLM 服务
try:
    from api.llm_service import behavior_health_agent, ollama_service
    LLM_AVAILABLE = True
    logger.info("[MiniProgram] LLM服务已加载")
except ImportError as e:
    LLM_AVAILABLE = False
    behavior_health_agent = None
    ollama_service = None
    logger.warning(f"[MiniProgram] LLM服务不可用: {e}")

# Dify 服务
try:
    from api.config import LLM_PROVIDER
    from api.dify_service import dify_service
    from api.context_builder import build_dify_inputs
    DIFY_AVAILABLE = True
    logger.info(f"[MiniProgram] Dify服务已加载, LLM_PROVIDER={LLM_PROVIDER}")
except ImportError as e:
    DIFY_AVAILABLE = False
    dify_service = None
    LLM_PROVIDER = "ollama"
    logger.warning(f"[MiniProgram] Dify服务不可用: {e}")

# 聊天历史持久化
try:
    from api.chat_history import chat_history
    CHAT_HISTORY_AVAILABLE = True
    logger.info("[MiniProgram] 聊天历史服务已加载")
except ImportError as e:
    CHAT_HISTORY_AVAILABLE = False
    chat_history = None
    logger.warning(f"[MiniProgram] 聊天历史服务不可用: {e}")

router = APIRouter(prefix="/mp", tags=["小程序接口"])


# ============================================
# 枚举与常量
# ============================================

class Stage(str, Enum):
    """干预阶段"""
    INIT = "INIT"           # 初始化
    ONBOARDING = "ONBOARDING"  # 引导期（1-3天）
    FOUNDATION = "FOUNDATION"   # 基础期（4-7天）
    DEEPENING = "DEEPENING"    # 深化期（8-11天）
    CONSOLIDATION = "CONSOLIDATION"  # 巩固期（12-14天）
    MAINTENANCE = "MAINTENANCE"  # 维持期（14天后）


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Mode(str, Enum):
    """运行模式"""
    PILOT = "pilot"         # 试点模式（正常用户）
    TRAINING = "training"   # 训练模式（显示Prompt逻辑）


# 阶段配置
STAGE_CONFIG = {
    Stage.INIT: {
        "days": (0, 0),
        "focus_template": "初始评估",
        "tasks": ["CHECKIN_MEAL"]
    },
    Stage.ONBOARDING: {
        "days": (1, 3),
        "focus_template": "建立基础习惯",
        "tasks": ["CHECKIN_MEAL", "CHECKIN_MOOD"]
    },
    Stage.FOUNDATION: {
        "days": (4, 7),
        "focus_template": "养成核心行为",
        "tasks": ["CHECKIN_MEAL", "CHECKIN_GLUCOSE", "EXERCISE_WALK"]
    },
    Stage.DEEPENING: {
        "days": (8, 11),
        "focus_template": "深化行为模式",
        "tasks": ["CHECKIN_MEAL", "CHECKIN_GLUCOSE", "EXERCISE_WALK", "MINDFULNESS"]
    },
    Stage.CONSOLIDATION: {
        "days": (12, 14),
        "focus_template": "巩固与内化",
        "tasks": ["CHECKIN_MEAL", "CHECKIN_GLUCOSE", "EXERCISE_WALK", "REFLECTION"]
    },
    Stage.MAINTENANCE: {
        "days": (15, 999),
        "focus_template": "自主维持",
        "tasks": ["CHECKIN_MEAL", "CHECKIN_GLUCOSE"]
    }
}

# 每日焦点主题
DAILY_FOCUS = {
    1: "认识你的身体信号",
    2: "建立饮食觉察",
    3: "情绪与进食的关系",
    4: "餐后血糖观察",
    5: "运动的力量",
    6: "压力与血糖",
    7: "第一周回顾",
    8: "深化饮食管理",
    9: "运动强化",
    10: "情绪管理进阶",
    11: "综合实践",
    12: "习惯固化",
    13: "自主决策练习",
    14: "总结与展望"
}


# ============================================
# 请求/响应模型
# ============================================

class TodayTaskResponse(BaseModel):
    """今日任务响应"""
    stage: str
    day_index: int
    task: str
    task_code: str
    focus: str
    mode: str
    progress: float
    tasks_completed: int
    tasks_total: int
    risk_level: str = "LOW"
    agent_greeting: str = ""


class TaskFeedbackRequest(BaseModel):
    """任务反馈请求"""
    stage: str
    result: str  # done, skip, partial
    task_code: Optional[str] = None
    data: Optional[Dict] = None
    notes: Optional[str] = None


class TaskFeedbackResponse(BaseModel):
    """任务反馈响应"""
    success: bool
    message: str
    explain: Optional[str] = None  # 训练模式显示
    next_stage: str
    points_earned: int = 0
    streak_days: int = 0
    achievement: Optional[str] = None


class AgentRequest(BaseModel):
    """Agent请求"""
    stage: str
    event: str  # start, complete, skip, ask
    context: Optional[Dict] = None
    user_input: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent响应"""
    message: str
    explain: Optional[str] = None
    suggestions: List[str] = []
    emotion: str = "supportive"


class UserStateResponse(BaseModel):
    """用户状态响应"""
    user_id: int
    day_index: int
    stage: str
    total_points: int
    streak_days: int
    risk_level: str
    last_checkin: Optional[str] = None
    next_milestone: str = ""


# ============================================
# 模拟数据存储（实际应使用数据库）
# ============================================

# 用户状态缓存
USER_STATE_CACHE: Dict[int, Dict] = {}


def get_user_state(user_id: int) -> Dict:
    """获取用户状态"""
    if user_id not in USER_STATE_CACHE:
        # 初始化用户状态
        USER_STATE_CACHE[user_id] = {
            "day_index": 1,
            "stage": Stage.ONBOARDING.value,
            "mode": Mode.PILOT.value,
            "total_points": 0,
            "streak_days": 0,
            "risk_level": RiskLevel.LOW.value,
            "tasks_today": {},
            "start_date": date.today().isoformat(),
            "last_checkin": None
        }
    return USER_STATE_CACHE[user_id]


def update_user_state(user_id: int, updates: Dict):
    """更新用户状态"""
    state = get_user_state(user_id)
    state.update(updates)
    USER_STATE_CACHE[user_id] = state


# ============================================
# 辅助函数
# ============================================

def get_stage_for_day(day_index: int) -> Stage:
    """根据天数获取阶段"""
    for stage, config in STAGE_CONFIG.items():
        start_day, end_day = config["days"]
        if start_day <= day_index <= end_day:
            return stage
    return Stage.MAINTENANCE


def get_daily_focus(day_index: int) -> str:
    """获取每日焦点"""
    return DAILY_FOCUS.get(day_index, f"第{day_index}天：持续进步")


def get_daily_task(stage: Stage, day_index: int) -> tuple:
    """获取当日主要任务"""
    config = STAGE_CONFIG.get(stage, STAGE_CONFIG[Stage.MAINTENANCE])
    tasks = config["tasks"]
    
    # 根据天数和阶段确定主任务
    task_descriptions = {
        "CHECKIN_MEAL": "记录您的三餐饮食",
        "CHECKIN_GLUCOSE": "测量并记录血糖",
        "CHECKIN_MOOD": "记录今日心情",
        "EXERCISE_WALK": "完成15分钟步行",
        "MINDFULNESS": "完成5分钟正念练习",
        "REFLECTION": "写下今日反思"
    }
    
    # 选择当天的主任务
    main_task = tasks[day_index % len(tasks)]
    description = task_descriptions.get(main_task, "完成今日任务")
    
    return main_task, description


def generate_agent_greeting(stage: Stage, day_index: int, user_name: str = "") -> str:
    """生成Agent问候语"""
    greetings = {
        Stage.ONBOARDING: [
            f"欢迎开始第{day_index}天的健康之旅！今天我们将一起{get_daily_focus(day_index)}。",
            f"新的一天开始了！作为你的健康伙伴，我会陪你度过这关键的起步阶段。"
        ],
        Stage.FOUNDATION: [
            f"太棒了，你已经坚持到第{day_index}天了！今天的重点是{get_daily_focus(day_index)}。",
            f"你的进步让我很欣慰。让我们继续建立健康的基础习惯吧！"
        ],
        Stage.DEEPENING: [
            f"第{day_index}天，你正在变得更强大！今天让我们一起{get_daily_focus(day_index)}。",
            f"你已经建立了很好的基础，现在是深化的时候了。"
        ],
        Stage.CONSOLIDATION: [
            f"第{day_index}天，胜利就在眼前！让我们{get_daily_focus(day_index)}。",
            f"你的坚持令人敬佩，这些习惯正在成为你的一部分。"
        ],
        Stage.MAINTENANCE: [
            f"第{day_index}天，你已经掌握了健康的钥匙！继续保持。",
            f"你现在是自己健康的主人了，我会继续陪伴你。"
        ]
    }
    
    import random
    stage_greetings = greetings.get(stage, greetings[Stage.MAINTENANCE])
    return random.choice(stage_greetings)


def generate_feedback_message(result: str, stage: Stage, task_code: str) -> tuple:
    """生成反馈消息和解释"""
    
    if result == "done":
        messages = {
            "CHECKIN_MEAL": ("太棒了！记录饮食是血糖管理的第一步。", "触发正向反馈路径：任务完成 → 积极强化"),
            "CHECKIN_GLUCOSE": ("血糖记录成功！持续监测能帮你发现规律。", "触发数据收集路径：血糖数据 → 趋势分析"),
            "EXERCISE_WALK": ("运动完成！你的身体会感谢你的。", "触发运动反馈：完成运动 → 多巴胺奖励"),
            "CHECKIN_MOOD": ("感谢分享心情，情绪觉察是健康的重要部分。", "触发情绪追踪：心情数据 → 情绪模式识别"),
            "MINDFULNESS": ("正念练习完成！你正在学会与身体对话。", "触发放松响应：正念完成 → 压力缓解"),
            "REFLECTION": ("今日反思已保存，自我觉察是成长的开始。", "触发认知路径：反思 → 元认知提升")
        }
        msg, explain = messages.get(task_code, ("任务完成！继续加油！", "通用完成反馈"))
        
    elif result == "skip":
        msg = "没关系，每个人都有不顺利的时候。明天是新的开始，我相信你可以的。"
        explain = "触发包容路径：跳过 → 共情响应 → 明日重置"
        
    elif result == "partial":
        msg = "完成一部分也是进步！小步前进同样值得庆祝。"
        explain = "触发部分完成路径：部分完成 → 肯定进步 → 鼓励继续"
        
    else:
        msg = "收到你的反馈，让我们一起继续前进。"
        explain = "通用反馈路径"
    
    return msg, explain


def assess_risk_level(user_state: Dict, feedback_data: Optional[Dict] = None) -> RiskLevel:
    """评估风险等级"""
    risk_score = 0
    
    # 检查连续跳过
    if user_state.get("consecutive_skips", 0) >= 3:
        risk_score += 30
    
    # 检查情绪数据
    if feedback_data:
        mood_score = feedback_data.get("mood_score", 5)
        if mood_score <= 2:
            risk_score += 40
        elif mood_score <= 3:
            risk_score += 20
        
        # 检查血糖数据
        glucose = feedback_data.get("glucose")
        if glucose:
            if glucose < 3.9 or glucose > 16.7:
                risk_score += 50
            elif glucose < 4.4 or glucose > 13.9:
                risk_score += 25
    
    # 确定风险等级
    if risk_score >= 70:
        return RiskLevel.CRITICAL
    elif risk_score >= 50:
        return RiskLevel.HIGH
    elif risk_score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


# ============================================
# 简化认证（小程序专用）
# ============================================

# DEPRECATED: 建议端点直接使用 Depends(get_current_user)
async def get_mp_user(
    current_user=Depends(get_current_user),
) -> int:
    """获取小程序用户ID (JWT认证)"""
    return current_user.id


# ============================================
# API路由
# ============================================

@router.get("/task/today", response_model=TodayTaskResponse)
async def get_today_task(user_id: int = Depends(get_mp_user)):
    """
    获取今日任务与状态
    
    返回当前阶段、天数、任务、焦点等信息
    """
    state = get_user_state(user_id)
    day_index = state["day_index"]
    stage = get_stage_for_day(day_index)
    mode = state.get("mode", Mode.PILOT.value)
    
    # 更新阶段
    if state["stage"] != stage.value:
        update_user_state(user_id, {"stage": stage.value})
    
    # 获取任务
    task_code, task_description = get_daily_task(stage, day_index)
    focus = get_daily_focus(day_index)
    
    # 计算进度
    tasks_today = state.get("tasks_today", {})
    tasks_total = len(STAGE_CONFIG[stage]["tasks"])
    tasks_completed = sum(1 for v in tasks_today.values() if v == "done")
    progress = day_index / 14  # 14天为一个完整周期
    
    # 生成问候
    greeting = generate_agent_greeting(stage, day_index)
    
    return TodayTaskResponse(
        stage=stage.value,
        day_index=day_index,
        task=task_description,
        task_code=task_code,
        focus=focus,
        mode=mode,
        progress=min(progress, 1.0),
        tasks_completed=tasks_completed,
        tasks_total=tasks_total,
        risk_level=state.get("risk_level", RiskLevel.LOW.value),
        agent_greeting=greeting
    )


@router.post("/task/feedback", response_model=TaskFeedbackResponse)
async def submit_task_feedback(
    request: TaskFeedbackRequest,
    user_id: int = Depends(get_mp_user)
):
    """
    提交任务反馈
    
    触发状态机流转，返回Agent响应和下一阶段
    """
    state = get_user_state(user_id)

    # 容错：映射非法 stage 值
    STAGE_ALIAS = {"startup": "INIT", "init": "INIT", "onboarding": "ONBOARDING"}
    stage_raw = request.stage.strip() if request.stage else ""
    stage_resolved = STAGE_ALIAS.get(stage_raw.lower(), stage_raw)
    try:
        current_stage = Stage(stage_resolved) if stage_resolved else get_stage_for_day(state["day_index"])
    except ValueError:
        valid = [s.value for s in Stage]
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段值: '{request.stage}'，合法值: {valid}"
        )
    mode = state.get("mode", Mode.PILOT.value)
    
    # 生成反馈消息
    task_code = request.task_code or "GENERAL"
    message, explain = generate_feedback_message(request.result, current_stage, task_code)
    
    # 更新任务状态
    tasks_today = state.get("tasks_today", {})
    tasks_today[task_code] = request.result
    
    # 计算积分
    points_earned = 0
    if request.result == "done":
        points_earned = 10
        state["total_points"] = state.get("total_points", 0) + points_earned
        state["streak_days"] = state.get("streak_days", 0) + 1
    elif request.result == "skip":
        state["consecutive_skips"] = state.get("consecutive_skips", 0) + 1
    
    # 评估风险
    risk_level = assess_risk_level(state, request.data)
    
    # 检查是否需要进入下一天/阶段
    next_stage = current_stage.value
    achievement = None
    
    # 如果今日任务全部完成，进入下一天
    config = STAGE_CONFIG[current_stage]
    if len([t for t in tasks_today.values() if t == "done"]) >= len(config["tasks"]):
        state["day_index"] = state["day_index"] + 1
        new_stage = get_stage_for_day(state["day_index"])
        if new_stage != current_stage:
            next_stage = new_stage.value
            achievement = f"恭喜进入{next_stage}阶段！"
    
    # 更新状态
    update_user_state(user_id, {
        "tasks_today": tasks_today,
        "risk_level": risk_level.value,
        "last_checkin": datetime.now().isoformat(),
        "day_index": state["day_index"],
        "total_points": state["total_points"],
        "streak_days": state["streak_days"]
    })
    
    return TaskFeedbackResponse(
        success=True,
        message=message,
        explain=explain if mode == Mode.TRAINING.value else None,
        next_stage=next_stage,
        points_earned=points_earned,
        streak_days=state["streak_days"],
        achievement=achievement
    )


@router.post("/agent/respond", response_model=AgentResponse)
async def agent_respond(
    request: AgentRequest,
    user_id: int = Depends(get_mp_user)
):
    """
    Agent AI响应

    根据阶段和事件生成个性化响应
    支持 LLM (Ollama) 和模板回退
    """
    state = get_user_state(user_id)
    mode = state.get("mode", Mode.PILOT.value)
    stage = Stage(request.stage) if request.stage else get_stage_for_day(state["day_index"])
    user_input = request.user_input or ""

    # ── SafetyPipeline L1: 输入过滤 ──
    _safety_pipeline = None
    _input_category = "normal"
    try:
        from core.safety.pipeline import get_safety_pipeline
        _safety_pipeline = get_safety_pipeline()
        if user_input:
            _input_result = _safety_pipeline.process_input(user_input)
            _input_category = _input_result.category
            if not _input_result.safe:
                try:
                    from core.database import SessionLocal
                    from core.models import SafetyLog
                    _db = SessionLocal()
                    _db.add(SafetyLog(
                        user_id=user_id,
                        event_type="input_blocked",
                        severity=_input_result.severity,
                        input_text=user_input[:500],
                        filter_details={"category": _input_result.category, "terms": _input_result.blocked_terms, "source": "mp_agent_respond"},
                    ))
                    _db.commit()
                    _db.close()
                except Exception:
                    logger.warning("SafetyLog write failed")
                _safe_reply = _safety_pipeline.get_crisis_response() if _input_result.category == "crisis" else "抱歉，您的消息包含不适当的内容，无法处理。"
                return AgentResponse(message=_safe_reply, suggestions=["查看任务", "聊聊心情"], emotion="supportive")
    except Exception as e:
        logger.warning(f"SafetyPipeline input filter degraded: {e}")

    # 默认建议列表
    default_suggestions = {
        "start": ["开始今日任务", "查看进度", "有问题想问"],
        "complete": ["继续下一个任务", "休息一下", "分享成就"],
        "skip": ["告诉我困难", "调整任务难度", "明天提醒我"],
        "ask": ["了解更多", "继续任务", "稍后再聊"]
    }
    suggestions = default_suggestions.get(request.event, ["查看任务", "聊聊心情", "看看进度"])

    # 构建用户消息
    if request.event == "start":
        prompt_message = f"用户刚开始第{state['day_index']}天的健康管理，请给予温暖的问候和鼓励。"
    elif request.event == "complete":
        prompt_message = "用户完成了今日任务，请给予肯定和正向强化。"
    elif request.event == "skip":
        prompt_message = "用户跳过了今日任务，请给予理解和支持，不要批评。"
    elif request.event == "ask" and user_input:
        prompt_message = user_input
    else:
        prompt_message = user_input or "你好"

    # 尝试使用 LLM 生成响应
    message = ""
    explain = None

    if LLM_AVAILABLE and behavior_health_agent:
        try:
            logger.info(f"[Agent] 调用 LLM: event={request.event}, stage={stage.value}")
            message = await behavior_health_agent.respond(
                user_message=prompt_message,
                history=None,  # 历史对话由 session_manager 管理，此处为无状态调用
                stage=stage.value,
                day_index=state["day_index"],
                event=request.event,
                risk_level=state.get("risk_level", "LOW")
            )
            explain = f"LLM响应: model=qwen2.5:0.5b, stage={stage.value}, day={state['day_index']}"
            logger.info(f"[Agent] LLM 响应成功: {message[:50]}...")
        except Exception as e:
            logger.error(f"[Agent] LLM 调用失败: {e}")
            message = ""

    # LLM 失败或不可用时，使用模板回退
    if not message:
        logger.info("[Agent] 使用模板回退")
        if request.event == "start":
            message = generate_agent_greeting(stage, state["day_index"])
            explain = f"模板响应: 阶段={stage.value}, 天数={state['day_index']}, 事件=开始"
        elif request.event == "complete":
            message = "太棒了！你完成得很好。每一次坚持都是在为健康存款。"
            explain = "模板响应: 完成事件 → 正向强化"
        elif request.event == "skip":
            message = "我理解，有时候确实很难坚持。但请记住，你已经走到这里了，明天是新的机会。"
            explain = "模板响应: 跳过事件 → 共情支持"
        elif request.event == "ask":
            if "血糖" in user_input:
                message = "血糖管理是一个循序渐进的过程。保持规律监测，注意饮食和运动的配合，你一定能看到改善。"
            elif "运动" in user_input:
                message = "运动对血糖控制非常有帮助。建议从简单的散步开始，餐后15-30分钟是最佳时间。"
            elif "心情" in user_input or "情绪" in user_input:
                message = "情绪会影响血糖，这是正常的生理反应。学会觉察情绪，是健康管理的重要一步。"
            else:
                message = "我在这里陪伴你。有任何问题都可以问我，我们一起找到答案。"
            explain = "模板响应: 关键词匹配"
        else:
            message = "有什么我可以帮助你的吗？"
            explain = "模板响应: 默认"

    # ── SafetyPipeline L4: 输出过滤 ──
    try:
        if _safety_pipeline and message:
            _output_result = _safety_pipeline.filter_output(message, _input_category)
            if _output_result.grade == "blocked":
                message = "抱歉，生成的内容未通过安全审核。如需专业建议请咨询医生。"
            else:
                message = _output_result.text
            if _output_result.grade in ("blocked", "review_needed"):
                try:
                    from core.database import SessionLocal
                    from core.models import SafetyLog
                    _db = SessionLocal()
                    _db.add(SafetyLog(
                        user_id=user_id,
                        event_type="output_blocked" if _output_result.grade == "blocked" else "output_review",
                        severity="high" if _output_result.grade == "blocked" else "medium",
                        input_text=(user_input or "")[:500],
                        output_text=_output_result.original_text[:500] if _output_result.original_text else "",
                        filter_details={"grade": _output_result.grade, "annotations": _output_result.annotations, "source": "mp_agent_respond"},
                    ))
                    _db.commit()
                    _db.close()
                except Exception:
                    logger.warning("SafetyLog write failed (mp_agent output)")
    except Exception as e:
        logger.warning(f"SafetyPipeline output filter degraded: {e}")

    return AgentResponse(
        message=message,
        explain=explain if mode == Mode.TRAINING.value else None,
        suggestions=suggestions,
        emotion="supportive"
    )


@router.get("/user/state", response_model=UserStateResponse)
async def get_user_state_api(user_id: int = Depends(get_mp_user)):
    """
    获取用户状态
    """
    state = get_user_state(user_id)
    
    # 计算下一个里程碑
    day_index = state["day_index"]
    if day_index < 7:
        next_milestone = f"距离第一周完成还有{7 - day_index}天"
    elif day_index < 14:
        next_milestone = f"距离两周挑战完成还有{14 - day_index}天"
    else:
        next_milestone = "你已经完成了两周挑战！"
    
    return UserStateResponse(
        user_id=user_id,
        day_index=state["day_index"],
        stage=state["stage"],
        total_points=state.get("total_points", 0),
        streak_days=state.get("streak_days", 0),
        risk_level=state.get("risk_level", RiskLevel.LOW.value),
        last_checkin=state.get("last_checkin"),
        next_milestone=next_milestone
    )


@router.post("/user/mode")
async def set_user_mode(
    mode: str,
    user_id: int = Depends(get_mp_user)
):
    """
    设置用户模式
    
    - pilot: 正常模式
    - training: 训练模式（显示Prompt逻辑）
    """
    if mode not in [m.value for m in Mode]:
        raise HTTPException(status_code=400, detail="无效的模式")
    
    update_user_state(user_id, {"mode": mode})
    
    return {
        "success": True,
        "mode": mode,
        "message": "训练模式已开启，你将看到AI的思考过程" if mode == "training" else "已切换到正常模式"
    }


@router.get("/progress/summary")
async def get_progress_summary(user_id: int = Depends(get_mp_user)):
    """
    获取进度摘要
    """
    state = get_user_state(user_id)
    day_index = state["day_index"]
    
    return {
        "day_index": day_index,
        "total_days": 14,
        "progress_percent": round(min(day_index / 14 * 100, 100), 1),
        "stage": state["stage"],
        "total_points": state.get("total_points", 0),
        "streak_days": state.get("streak_days", 0),
        "achievements": [
            {"name": "起步者", "unlocked": day_index >= 1},
            {"name": "三日达人", "unlocked": day_index >= 3},
            {"name": "一周勇士", "unlocked": day_index >= 7},
            {"name": "两周冠军", "unlocked": day_index >= 14}
        ]
    }


@router.get("/risk/status")
async def get_risk_status(user_id: int = Depends(get_mp_user)):
    """
    获取风险状态
    """
    state = get_user_state(user_id)
    risk_level = RiskLevel(state.get("risk_level", RiskLevel.LOW.value))
    
    notices = {
        RiskLevel.LOW: None,
        RiskLevel.MEDIUM: "我们注意到您可能需要额外支持，有什么可以帮助您的吗？",
        RiskLevel.HIGH: "您的状态已被记录，专业教练可能随时介入协助。",
        RiskLevel.CRITICAL: "请注意：我们检测到异常情况，专业团队将尽快联系您。"
    }
    
    return {
        "risk_level": risk_level.value,
        "notice": notices[risk_level],
        "show_notice": risk_level != RiskLevel.LOW,
        "support_available": risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    }


# ============================================
# LLM / AI 相关接口
# ============================================

async def _resolve_provider() -> str:
    """
    根据 LLM_PROVIDER 配置决定实际使用的提供者

    Returns: "dify" | "ollama"
    """
    if LLM_PROVIDER == "ollama":
        return "ollama"
    if LLM_PROVIDER == "dify":
        return "dify" if DIFY_AVAILABLE else "ollama"
    # auto: 先检查 Dify 健康状态
    if DIFY_AVAILABLE and dify_service:
        try:
            health = await dify_service.check_health()
            if health.get("status") == "healthy":
                return "dify"
        except Exception:
            pass
    return "ollama"


@router.get("/llm/health")
async def llm_health_check():
    """
    检查 LLM 服务健康状态

    返回 Ollama 和 Dify 服务状态
    """
    result = {
        "ollama": {"status": "unavailable"},
        "dify": {"status": "unavailable"},
        "active_provider": LLM_PROVIDER,
    }

    # Ollama 健康检查
    if LLM_AVAILABLE and ollama_service:
        try:
            health = await ollama_service.check_health()
            result["ollama"] = {
                "status": health.get("status", "unknown"),
                "models": health.get("models", []),
                "model_available": health.get("model_available", False),
                "current_model": ollama_service.model,
            }
        except Exception as e:
            result["ollama"] = {"status": "error", "message": str(e)}

    # Dify 健康检查
    if DIFY_AVAILABLE and dify_service:
        try:
            health = await dify_service.check_health()
            result["dify"] = {
                "status": health.get("status", "unknown"),
                "app": health.get("opening_statement", "主动健康教练"),
            }
        except Exception as e:
            result["dify"] = {"status": "error", "message": str(e)}

    return result


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    session_id: str
    model: str = "qwen2.5:0.5b"
    provider: str = "ollama"
    conversation_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user_id: int = Depends(get_mp_user)
):
    """
    与 AI 健康教练对话

    非流式响应，支持 Dify / Ollama 双模式路由和历史记录持久化
    """
    state = get_user_state(user_id)
    stage = get_stage_for_day(state["day_index"])
    session_id = request.session_id or f"chat_{user_id}_{int(time.time())}"
    model_name = ollama_service.model if ollama_service else "unknown"

    # ── SafetyPipeline L1: 输入过滤 ──
    _safety_pipeline = None
    _input_category = "normal"
    try:
        from core.safety.pipeline import get_safety_pipeline
        _safety_pipeline = get_safety_pipeline()
        _input_result = _safety_pipeline.process_input(request.message)
        _input_category = _input_result.category
        if not _input_result.safe:
            try:
                from core.database import SessionLocal
                from core.models import SafetyLog
                _db = SessionLocal()
                _db.add(SafetyLog(
                    user_id=user_id,
                    event_type="input_blocked",
                    severity=_input_result.severity,
                    input_text=request.message[:500],
                    filter_details={"category": _input_result.category, "terms": _input_result.blocked_terms, "source": "mp_chat"},
                ))
                _db.commit()
                _db.close()
            except Exception:
                logger.warning("SafetyLog write failed")
            _safe_reply = _safety_pipeline.get_crisis_response() if _input_result.category == "crisis" else "抱歉，您的消息包含不适当的内容，无法处理。"
            return ChatResponse(message=_safe_reply, session_id=session_id, model="safety", provider="safety")
    except Exception as e:
        logger.warning(f"SafetyPipeline input filter degraded: {e}")

    # 获取或创建会话，加载历史记录
    history = []
    if CHAT_HISTORY_AVAILABLE and chat_history:
        try:
            chat_history.get_or_create_session(user_id, session_id, model_name)
            history = chat_history.get_messages(session_id, limit=10)
            chat_history.add_message(session_id, "user", request.message)
        except Exception as e:
            logger.warning(f"[Chat] 历史记录操作失败: {e}")

    # 决定使用哪个提供者
    provider = await _resolve_provider()

    # ---- Dify 路径 ----
    if provider == "dify" and DIFY_AVAILABLE and dify_service:
        try:
            inputs = build_dify_inputs(user_id, state)
            result = await dify_service.chat(
                query=request.message,
                user=str(user_id),
                inputs=inputs,
                session_id=session_id,
            )
            ai_response = result.get("answer", "") or "我在这里陪伴你，有什么问题都可以问我。"
            conv_id = result.get("conversation_id")

            # ── SafetyPipeline L4 ──
            try:
                if _safety_pipeline:
                    _output_result = _safety_pipeline.filter_output(ai_response, _input_category)
                    if _output_result.grade == "blocked":
                        ai_response = "抱歉，生成的内容未通过安全审核。如需专业建议请咨询医生。"
                    else:
                        ai_response = _output_result.text
            except Exception as _e:
                logger.warning(f"SafetyPipeline output filter degraded (dify): {_e}")

            if CHAT_HISTORY_AVAILABLE and chat_history:
                try:
                    chat_history.add_message(session_id, "assistant", ai_response, model="dify")
                except Exception as e:
                    logger.warning(f"[Chat] 保存AI回复失败: {e}")

            return ChatResponse(
                message=ai_response,
                session_id=session_id,
                model="dify",
                provider="dify",
                conversation_id=conv_id,
            )
        except Exception as e:
            logger.error(f"Dify chat error, falling back to Ollama: {e}")
            provider = "ollama"  # 降级

    # ---- Ollama 路径 ----
    if not LLM_AVAILABLE or not behavior_health_agent:
        fallback_msg = "抱歉，AI服务暂时不可用。请稍后再试，或联系客服获取帮助。"
        if CHAT_HISTORY_AVAILABLE and chat_history:
            chat_history.add_message(session_id, "assistant", fallback_msg, model="fallback")
        return ChatResponse(
            message=fallback_msg,
            session_id=session_id,
            model="fallback",
            provider="fallback",
        )

    try:
        response = await behavior_health_agent.respond(
            user_message=request.message,
            history=history if history else None,
            stage=stage.value,
            day_index=state["day_index"],
            event="ask",
            risk_level=state.get("risk_level", "LOW")
        )

        ai_response = response or "我在这里陪伴你，有什么问题都可以问我。"

        # ── SafetyPipeline L4 ──
        try:
            if _safety_pipeline:
                _output_result = _safety_pipeline.filter_output(ai_response, _input_category)
                if _output_result.grade == "blocked":
                    ai_response = "抱歉，生成的内容未通过安全审核。如需专业建议请咨询医生。"
                else:
                    ai_response = _output_result.text
        except Exception as _e:
            logger.warning(f"SafetyPipeline output filter degraded (ollama): {_e}")

        if CHAT_HISTORY_AVAILABLE and chat_history:
            try:
                chat_history.add_message(session_id, "assistant", ai_response, model=model_name)
            except Exception as e:
                logger.warning(f"[Chat] 保存AI回复失败: {e}")

        return ChatResponse(
            message=ai_response,
            session_id=session_id,
            model=model_name,
            provider="ollama",
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        error_msg = "抱歉，处理您的消息时出现了问题。请稍后再试。"
        if CHAT_HISTORY_AVAILABLE and chat_history:
            chat_history.add_message(session_id, "assistant", error_msg, model="error")
        return ChatResponse(
            message=error_msg,
            session_id=session_id,
            model="error",
            provider="error",
        )


from fastapi.responses import StreamingResponse


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user_id: int = Depends(get_mp_user)
):
    """
    与 AI 健康教练对话（流式）

    返回 SSE 流，支持 Dify / Ollama 双模式路由
    """
    state = get_user_state(user_id)
    stage = get_stage_for_day(state["day_index"])
    session_id = request.session_id or f"chat_{user_id}_{int(time.time())}"

    provider = await _resolve_provider()

    # ---- Dify 流式路径 ----
    if provider == "dify" and DIFY_AVAILABLE and dify_service:
        inputs = build_dify_inputs(user_id, state)

        async def dify_generate():
            try:
                async for chunk in dify_service.chat_stream(
                    query=request.message,
                    user=str(user_id),
                    inputs=inputs,
                    session_id=session_id,
                ):
                    if chunk == "":
                        # keepalive: SSE comment 保持连接不超时
                        yield ": ping\n\n"
                    else:
                        yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Dify stream error: {e}")
                yield f"data: [错误] Dify流式响应失败: {str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            dify_generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # ---- Ollama 流式路径 ----
    if not LLM_AVAILABLE or not behavior_health_agent:
        async def error_stream():
            yield f"data: 抱歉，AI服务暂时不可用。\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream"
        )

    async def generate():
        try:
            async for chunk in behavior_health_agent.respond_stream(
                user_message=request.message,
                history=None,
                stage=stage.value,
                day_index=state["day_index"],
                event="ask",
                risk_level=state.get("risk_level", "LOW")
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"data: [错误] {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# ============================================
# 聊天历史 API
# ============================================

class ChatHistoryMessage(BaseModel):
    """聊天消息"""
    id: str
    role: str
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """聊天历史响应"""
    session_id: str
    messages: List[ChatHistoryMessage]
    total: int


class ChatSessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    message_count: int
    created_at: str
    updated_at: str


@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    user_id: int = Depends(get_mp_user)
):
    """
    获取聊天历史记录

    Args:
        session_id: 会话ID
        limit: 返回消息数量限制
    """
    if not CHAT_HISTORY_AVAILABLE or not chat_history:
        return {"session_id": session_id, "messages": [], "total": 0}

    try:
        messages = chat_history.get_messages(session_id, limit=limit)
        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": f"msg_{i}",
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": ""
                }
                for i, msg in enumerate(messages)
            ],
            "total": len(messages)
        }
    except Exception as e:
        logger.error(f"Get chat history error: {e}")
        return {"session_id": session_id, "messages": [], "total": 0, "error": str(e)}


@router.get("/chat/sessions")
async def get_user_chat_sessions(
    limit: int = 20,
    user_id: int = Depends(get_mp_user)
):
    """
    获取用户的所有聊天会话
    """
    if not CHAT_HISTORY_AVAILABLE or not chat_history:
        return {"sessions": [], "total": 0}

    try:
        sessions = chat_history.get_user_sessions(user_id, limit=limit)
        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "message_count": s.message_count,
                    "created_at": s.created_at.isoformat() if s.created_at else "",
                    "updated_at": s.updated_at.isoformat() if s.updated_at else ""
                }
                for s in sessions
            ],
            "total": len(sessions)
        }
    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        return {"sessions": [], "total": 0, "error": str(e)}


@router.delete("/chat/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    user_id: int = Depends(get_mp_user)
):
    """删除聊天会话"""
    if not CHAT_HISTORY_AVAILABLE or not chat_history:
        return {"success": False, "message": "历史记录服务不可用"}

    try:
        success = chat_history.delete_session(session_id)
        return {
            "success": success,
            "message": "会话已删除" if success else "会话不存在"
        }
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        return {"success": False, "message": str(e)}


@router.delete("/chat/history")
async def clear_user_chat_history(
    user_id: int = Depends(get_mp_user)
):
    """清空用户所有聊天历史"""
    if not CHAT_HISTORY_AVAILABLE or not chat_history:
        return {"success": False, "message": "历史记录服务不可用", "cleared": 0}

    try:
        count = chat_history.clear_user_history(user_id)
        return {
            "success": True,
            "message": f"已清空 {count} 个会话",
            "cleared": count
        }
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return {"success": False, "message": str(e), "cleared": 0}
