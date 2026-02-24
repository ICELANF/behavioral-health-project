# -*- coding: utf-8 -*-
import os
import sys
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from loguru import logger
from fastapi import BackgroundTasks, Depends, FastAPI, Body, Header, HTTPException

# ── 日志配置: 文件轮转 + 结构化 ──
_log_dir = os.getenv("LOG_DIR", "/app/logs")
try:
    os.makedirs(_log_dir, exist_ok=True)
except PermissionError:
    _log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(_log_dir, exist_ok=True)
logger.add(
    os.path.join(_log_dir, "bhp_{time:YYYY-MM-DD}.log"),
    rotation="00:00",    # 每天零点轮转
    retention="30 days", # 保留30天
    compression="gz",    # 压缩旧日志
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
    enqueue=True,        # 异步写入 (多 worker 安全)
)
# JSON 结构化日志 (用于 ELK/Loki 采集)
if os.getenv("LOG_JSON", "").lower() == "true":
    logger.add(
        os.path.join(_log_dir, "bhp_{time:YYYY-MM-DD}.jsonl"),
        rotation="00:00",
        retention="14 days",
        compression="gz",
        serialize=True,
        level="INFO",
        enqueue=True,
    )
# 拦截标准 logging → loguru
class _InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
for _name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
    logging.getLogger(_name).handlers = [_InterceptHandler()]

import time as _time_mod
_app_start_time = _time_mod.time()
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.dependencies import get_current_user
from core.models import User

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 延迟导入 Master Agent — 统一单例 (v0+v6 合并)
_master_agent = None

def get_master_agent(db_session=None):
    """获取统一 MasterAgent 单例 (v0+v6 合并)"""
    global _master_agent
    if _master_agent is None:
        try:
            from core.master_agent_unified import UnifiedMasterAgent
            if db_session is None:
                try:
                    from core.database import SessionLocal
                    db_session = SessionLocal()
                except Exception:
                    pass
            _master_agent = UnifiedMasterAgent(db_session=db_session)
            print("[API] UnifiedMasterAgent (v0+v6) 初始化成功")
        except Exception as e:
            print(f"[API] UnifiedMasterAgent 初始化失败: {e}")
    return _master_agent


def get_agent_master(db_session=None):
    """deprecated — 使用 get_master_agent()"""
    return get_master_agent(db_session)


def reset_agent_master():
    """重置统一单例, 下次调用时重建 (Agent 模板变更后调用)"""
    global _master_agent
    _master_agent = None


def _resolve_tenant_ctx_by_user_id(user_id: str, db) -> Optional[Dict[str, Any]]:
    """从 user_id 字符串解析 tenant_ctx (供 orchestrator 端点用)"""
    try:
        from core.models import ExpertTenant, TenantClient
        from core.agent_template_service import get_tenant_routing_context

        uid = int(user_id)

        # 1. 用户是专家
        tenant = db.query(ExpertTenant).filter(
            ExpertTenant.expert_user_id == uid,
        ).first()
        if tenant:
            return get_tenant_routing_context(tenant.id, db)

        # 2. 用户是租户客户
        client = db.query(TenantClient).filter(
            TenantClient.user_id == uid,
            TenantClient.status == "active",
        ).first()
        if client:
            return get_tenant_routing_context(client.tenant_id, db)

        return None
    except Exception:
        return None


# ============================================================================
# Pydantic 模型
# ============================================================================

class DeviceDataInput(BaseModel):
    """设备数据输入"""
    cgm: Optional[Dict[str, Any]] = None
    hrv: Optional[Dict[str, Any]] = None
    sleep: Optional[Dict[str, Any]] = None
    steps: int = 0
    heart_rate: Optional[Dict[str, Any]] = None

class OrchestratorRequest(BaseModel):
    """Orchestrator 请求"""
    user_id: str = Field(..., description="用户ID")
    input_type: str = Field("text", description="输入类型: text/voice/device/form")
    content: Optional[str] = Field(None, description="用户输入内容")
    device_data: Optional[DeviceDataInput] = None
    efficacy_score: Optional[float] = Field(None, ge=0, le=100)
    session_id: Optional[str] = None

class OrchestratorResponse(BaseModel):
    """Orchestrator 响应"""
    reply: str
    coach_style: str
    intervention_plan: Optional[Dict[str, Any]] = None
    daily_tasks: List[Dict[str, Any]] = []
    daily_briefing: Optional[Dict[str, Any]] = None
    insights: Optional[Dict[str, Any]] = None
    updated_profile: Optional[Dict[str, Any]] = None
    pipeline_summary: Optional[Dict[str, Any]] = None

class DailyBriefingRequest(BaseModel):
    """每日简报请求"""
    user_id: str

class AgentTaskRequest(BaseModel):
    """Agent 任务请求"""
    task_id: Optional[str] = None
    agent_type: str = Field(..., description="Agent类型: SleepAgent/GlucoseAgent/StressAgent等")
    question: str
    priority: str = "normal"
    context: Optional[Dict[str, Any]] = None

class ActionPlanRequest(BaseModel):
    """行动计划请求"""
    user_id: str
    goal: str
    phase: str = "week_1"
    tags: List[str] = []


class AgentAnalysisInput(BaseModel):
    """Agent 分析结果输入"""
    agent: str
    analysis: str
    risk_level: str = "low"
    suggestions: List[str] = []
    tags: List[str] = []
    confidence: float = 0.8


class CoordinateRequest(BaseModel):
    """协调请求"""
    agent_results: List[AgentAnalysisInput]


from contextlib import asynccontextmanager


def _validate_startup_env():
    """启动时校验关键环境变量，缺失则警告"""
    required = {
        "DATABASE_URL": "数据库连接",
        "JWT_SECRET_KEY": "JWT签名密钥",
    }
    recommended = {
        "CORS_ORIGINS": "CORS白名单 (生产必须设置)",
        "REDIS_URL": "Redis连接 (限流/缓存/任务锁)",
        "SENTRY_DSN": "Sentry错误追踪 (生产建议开启)",
    }
    for var, desc in required.items():
        val = os.getenv(var, "")
        if not val:
            logger.warning(f"[STARTUP] 缺少必需环境变量 {var} ({desc})")
        else:
            logger.info(f"[STARTUP] ✓ {var} ({desc})")
    for var, desc in recommended.items():
        val = os.getenv(var, "")
        if not val:
            logger.warning(f"[STARTUP] 建议设置环境变量 {var} ({desc})")


def _seed_agent_presets(db):
    """首次启动时自动 seed 12 个预设 Agent 模板"""
    from core.models import AgentTemplate
    presets = [
        ("metabolic", "代谢管理Agent", "specialist", "glucose", "血糖、体重、代谢分析与建议", ["血糖","代谢","胰岛素"], 1),
        ("sleep", "睡眠管理Agent", "specialist", "sleep", "睡眠质量分析、作息优化", ["睡眠","失眠","作息"], 2),
        ("emotion", "情绪管理Agent", "specialist", "mental", "情绪评估、压力管理、心理支持", ["情绪","焦虑","抑郁","压力"], 3),
        ("motivation", "动机激励Agent", "specialist", "motivation", "行为动机分析、阶段推进", ["动机","坚持","习惯"], 4),
        ("coaching", "教练风格Agent", "specialist", None, "统一教练风格输出、回复合成", ["教练","指导"], 5),
        ("nutrition", "营养管理Agent", "specialist", "nutrition", "膳食分析、营养建议", ["营养","饮食","膳食"], 6),
        ("exercise", "运动康复Agent", "specialist", "exercise", "运动方案、康复指导", ["运动","健身","康复"], 7),
        ("tcm", "中医养生Agent", "specialist", "tcm", "中医体质分析、养生建议", ["中医","体质","养生"], 8),
        ("crisis", "危机干预Agent", "specialist", "crisis", "高风险识别与危机干预", ["自杀","自残","危机"], 0),
        ("behavior_rx", "行为处方Agent", "integrative", "behavior_rx", "行为处方制定、习惯干预", ["行为处方","戒烟","依从性"], 3),
        ("weight", "体重管理Agent", "integrative", "weight", "体重/BMI监测、减重方案", ["体重","BMI","减重"], 4),
        ("cardiac_rehab", "心脏康复Agent", "integrative", "cardiac_rehab", "心血管康复评估、运动处方", ["心脏","心血管","康复"], 5),
    ]
    for agent_id, name, atype, domain, desc, keywords, priority in presets:
        db.add(AgentTemplate(
            agent_id=agent_id, display_name=name, agent_type=atype,
            domain_enum=domain, description=desc, keywords=keywords,
            priority=priority, is_preset=True, is_enabled=True,
        ))
    db.commit()
    print(f"[API] Agent 预设模板已 seed: {len(presets)} 个")


_scheduler = None

@asynccontextmanager
async def lifespan(app):
    """启动/关闭 APScheduler + Agent 模板缓存预热"""
    _validate_startup_env()
    global _scheduler
    try:
        from core.scheduler import setup_scheduler
        _scheduler = setup_scheduler()
        if _scheduler:
            _scheduler.start()
            print("[API] APScheduler 已启动")
    except Exception as e:
        print(f"[API] APScheduler 启动失败: {e}")

    # Agent 模板: 自动 seed 预设 + 缓存预热
    try:
        from core.database import SessionLocal
        from core.models import AgentTemplate
        from core.agent_template_service import load_templates
        db = SessionLocal()
        try:
            existing = db.query(AgentTemplate).count()
            if existing == 0:
                _seed_agent_presets(db)
            templates = load_templates(db)
            print(f"[API] Agent 模板缓存预热完成: {len(templates)} 个模板")
        finally:
            db.close()
    except Exception as e:
        print(f"[API] Agent 模板缓存预热失败 (非阻塞): {e}")

    # v6 AgentMaster 初始化 (template-aware, 用于 agent routing)
    try:
        am = get_agent_master()
        if am:
            print(f"[API] AgentMaster (v6) 初始化完成, {len(am._agents)} 个 Agent")
    except Exception as e:
        print(f"[API] AgentMaster (v6) 初始化失败 (非阻塞): {e}")

    # V007 PolicyEngine 规则缓存预热
    try:
        from core.database import SessionLocal
        from core.rule_registry import RuleRegistry
        db = SessionLocal()
        try:
            registry = RuleRegistry(db_session_factory=lambda: db)
            registry.initialize()
            print(f"[API] V007 PolicyEngine 规则缓存预热完成")
        finally:
            db.close()
    except Exception as e:
        print(f"[API] V007 PolicyEngine 规则缓存预热失败 (非阻塞): {e}")

    # Behavior Rx: 专家 Agent 初始化 + MasterAgent 补丁 + DI 注入
    try:
        from behavior_rx.master_agent_integration import (
            setup_expert_agents, patch_master_agent_v0,
        )
        from behavior_rx.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.agent_handoff_service import AgentHandoffService
        from core.agents.master_agent import MasterAgent

        # 创建共享实例 (所有组件复用同一份)
        _rx_engine = BehaviorRxEngine()
        _handoff_svc = AgentHandoffService()
        expert_router = setup_expert_agents(
            rx_engine=_rx_engine, handoff_service=_handoff_svc
        )
        patch_master_agent_v0(MasterAgent)
        # 注入到全局 MasterAgent 实例
        ma = get_master_agent()
        if ma and hasattr(ma, 'register_expert_router'):
            ma.register_expert_router(expert_router)
        # 注入共享实例到 rx_routes DI (解决单例脱节问题)
        try:
            from behavior_rx.rx_routes import set_shared_instances
            set_shared_instances(
                engine=_rx_engine,
                handoff=_handoff_svc,
                orchestrator=expert_router._orchestrator,
            )
        except Exception as inject_err:
            print(f"[API] Behavior Rx DI 注入失败: {inject_err}")
        print("[API] Behavior Rx 专家 Agent 已初始化 + MasterAgent 已补丁 + DI 已注入")
    except Exception as e:
        print(f"[API] Behavior Rx 初始化失败 (非阻塞): {e}")

    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
        print("[API] APScheduler 已关闭")

# FIX-07: 生产环境禁用 API 文档
_env = os.getenv("ENVIRONMENT", "production")
_docs_url = "/docs" if _env in ("development", "test") else None
_redoc_url = "/redoc" if _env in ("development", "test") else None
_openapi_url = "/openapi.json" if _env in ("development", "test") else None

app = FastAPI(
    title="BHP Xingjian Agent Gateway",
    version="3.1.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# FIX-02: 全局异常处理脱敏
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    import uuid as _uuid
    error_id = str(_uuid.uuid4())[:8]
    logger.exception(f"[{error_id}] Unhandled exception: {exc}")
    detail = str(exc) if _env in ("development", "test") else f"请联系管理员, 错误编号: {error_id}"
    return JSONResponse(status_code=500, content={"error": "InternalServerError", "message": "服务器内部错误", "detail": detail})

# --- 配置中心 (从 api.config 集中读取) ---
from api.config import DIFY_API_URL, DIFY_API_KEY, OLLAMA_API_URL, OLLAMA_MODEL

# --- 生产级中间件 (CORS白名单 + 安全头 + 日志 + 限流 + Sentry) ---
from core.middleware import setup_production_middleware
setup_production_middleware(app)

# --- 安全加固中间件 (FIX-12~18: Legacy鉴权 + CSRF审计 + HTTPS重定向) ---
try:
    from core.register_security import register_all_security
    register_all_security(app)
except Exception as e:
    logger.warning(f"[Security] 安全中间件注册失败: {e}")

# 注册认证路由
try:
    from api.auth_api import router as auth_router
    app.include_router(auth_router)
    print("[API] 认证路由已注册")
except ImportError as e:
    print(f"[API] 认证路由注册失败: {e}")

# 注册评估路由
try:
    from api.assessment_api import router as assessment_router
    app.include_router(assessment_router)
    print("[API] 评估路由已注册")
except ImportError as e:
    print(f"[API] 评估路由注册失败: {e}")

# 注册小程序路由
try:
    from api.miniprogram import router as mp_router
    app.include_router(mp_router, prefix="/api/v1")
    print("[API] 小程序路由已注册")
except ImportError as e:
    print(f"[API] 小程序路由注册失败: {e}")

# 注册设备数据路由
try:
    from api.device_data import router as device_router
    app.include_router(device_router, prefix="/api/v1/mp")
    print("[API] 设备数据路由已注册")
except ImportError as e:
    print(f"[API] 设备数据路由注册失败: {e}")

# 注册内容管理路由
try:
    from api.content_api import router as content_router
    app.include_router(content_router)
    print("[API] 内容管理路由已注册")
except ImportError as e:
    print(f"[API] 内容管理路由注册失败: {e}")

# 注册学习激励路由
try:
    from api.learning_api import router as learning_router
    app.include_router(learning_router)
    print("[API] 学习激励路由已注册")
except ImportError as e:
    print(f"[API] 学习激励路由注册失败: {e}")

# 注册 WebSocket 实时推送路由
try:
    from api.websocket_api import router as ws_router
    app.include_router(ws_router)
    print("[API] WebSocket 实时推送路由已注册")
except ImportError as e:
    print(f"[API] WebSocket 路由注册失败: {e}")

# 注册教练等级体系路由
try:
    from api.paths_api import router as paths_router
    app.include_router(paths_router)
    print("[API] 教练等级体系路由已注册")
except ImportError as e:
    print(f"[API] 教练等级体系路由注册失败: {e}")

# 注册用户分层路由
try:
    from api.segments_api import router as segments_router
    app.include_router(segments_router)
    print("[API] 用户分层路由已注册")
except ImportError as e:
    print(f"[API] 用户分层路由注册失败: {e}")

# 注册用户管理路由（管理后台）
try:
    from api.user_api import router as user_admin_router
    app.include_router(user_admin_router)
    print("[API] 用户管理路由已注册")
except ImportError as e:
    print(f"[API] 用户管理路由注册失败: {e}")

# 注册设备数据REST路由
try:
    from api.device_rest_api import router as device_rest_router
    app.include_router(device_rest_router)
    print("[API] 设备REST路由已注册")
except ImportError as e:
    print(f"[API] 设备REST路由注册失败: {e}")

# 注册聊天REST路由
try:
    from api.chat_rest_api import router as chat_rest_router
    app.include_router(chat_rest_router)
    print("[API] 聊天REST路由已注册")
except ImportError as e:
    print(f"[API] 聊天REST路由注册失败: {e}")

# 注册教练端路由
try:
    from api.coach_api import router as coach_router
    app.include_router(coach_router)
    print("[API] 教练端路由已注册")
except ImportError as e:
    print(f"[API] 教练端路由注册失败: {e}")

# 注册评估管道路由
try:
    from api.assessment_pipeline_api import router as pipeline_router
    app.include_router(pipeline_router)
    print("[API] 评估管道路由已注册")
except ImportError as e:
    print(f"[API] 评估管道路由注册失败: {e}")

# 注册微行动路由
try:
    from api.micro_action_api import router as micro_action_router
    app.include_router(micro_action_router)
    print("[API] 微行动路由已注册")
except ImportError as e:
    print(f"[API] 微行动路由注册失败: {e}")

# 注册教练消息路由
try:
    from api.coach_message_api import router as coach_message_router
    app.include_router(coach_message_router)
    print("[API] 教练消息路由已注册")
except ImportError as e:
    print(f"[API] 教练消息路由注册失败: {e}")

# 注册提醒管理路由
try:
    from api.reminder_api import router as reminder_router
    app.include_router(reminder_router)
    print("[API] 提醒管理路由已注册")
except ImportError as e:
    print(f"[API] 提醒管理路由注册失败: {e}")

# 注册评估推送与审核路由
try:
    from api.assessment_assignment_api import router as assessment_assignment_router
    app.include_router(assessment_assignment_router)
    print("[API] 评估推送与审核路由已注册")
except ImportError as e:
    print(f"[API] 评估推送与审核路由注册失败: {e}")

# 注册高频题目路由
try:
    from api.high_freq_api import router as high_freq_router
    app.include_router(high_freq_router)
    print("[API] 高频题目路由已注册")
except ImportError as e:
    print(f"[API] 高频题目路由注册失败: {e}")

# 注册设备预警路由
try:
    from api.device_alert_api import router as device_alert_router
    app.include_router(device_alert_router)
    print("[API] 设备预警路由已注册")
except ImportError as e:
    print(f"[API] 设备预警路由注册失败: {e}")

# 注册AI推送建议路由
try:
    from api.push_recommendation_api import router as push_recommendation_router
    app.include_router(push_recommendation_router)
    print("[API] AI推送建议路由已注册")
except ImportError as e:
    print(f"[API] AI推送建议路由注册失败: {e}")

# 注册Prompt模板路由
try:
    from api.prompt_api import router as prompt_router
    app.include_router(prompt_router)
    print("[API] Prompt模板路由已注册")
except ImportError as e:
    print(f"[API] Prompt模板路由注册失败: {e}")

# 注册干预包路由
try:
    from api.intervention_api import router as intervention_router
    app.include_router(intervention_router)
    print("[API] 干预包路由已注册")
except ImportError as e:
    print(f"[API] 干预包路由注册失败: {e}")

# 注册挑战/打卡活动路由
try:
    from api.challenge_api import router as challenge_router
    app.include_router(challenge_router)
    print("[API] 挑战/打卡活动路由已注册")
except ImportError as e:
    print(f"[API] 挑战/打卡活动路由注册失败: {e}")

# 注册教练推送审批队列路由
try:
    from api.coach_push_queue_api import router as push_queue_router
    app.include_router(push_queue_router)
    print("[API] 教练推送审批队列路由已注册")
except ImportError as e:
    print(f"[API] 教练推送审批队列路由注册失败: {e}")

# 注册全平台搜索路由
try:
    from api.search_api import router as search_router
    app.include_router(search_router)
    print("[API] 全平台搜索路由已注册")
except ImportError as e:
    print(f"[API] 全平台搜索路由注册失败: {e}")

# 注册用户行为周报路由
try:
    from api.weekly_report_api import router as weekly_report_router
    app.include_router(weekly_report_router)
    print("[API] 用户行为周报路由已注册")
except ImportError as e:
    print(f"[API] 用户行为周报路由注册失败: {e}")

# 注册多Agent协作路由
try:
    from api.agent_api import router as agent_router
    app.include_router(agent_router)
    print("[API] 多Agent协作路由已注册")
except ImportError as e:
    print(f"[API] 多Agent协作路由注册失败: {e}")

# 注册图片上传路由
try:
    from api.upload_api import router as upload_router
    app.include_router(upload_router)
    print("[API] 图片上传路由已注册")
except ImportError as e:
    print(f"[API] 图片上传路由注册失败: {e}")

# 注册食物识别路由
try:
    from api.food_recognition_api import router as food_router
    app.include_router(food_router)
    print("[API] 食物识别路由已注册")
except ImportError as e:
    print(f"[API] 食物识别路由注册失败: {e}")

# ========== 注册音频处理路由 (V5.2.0 ASR) ==========
try:
    from api.audio_api import router as audio_router
    app.include_router(audio_router)
    print("[API] 音频处理路由已注册")
except ImportError as e:
    print(f"[API] 音频处理路由注册失败: {e}")

# ============================================
# 注册 v3 路由 (诊断管道/Coach对话/渐进评估/效果追踪/激励积分/知识库)
# ============================================
try:
    from v3.routers import (
        auth as v3_auth,
        diagnostic as v3_diagnostic,
        chat as v3_chat,
        assessment as v3_assessment,
        tracking as v3_tracking,
        incentive as v3_incentive,
        knowledge as v3_knowledge,
        health as v3_health,
    )
    app.include_router(v3_health.router)
    app.include_router(v3_auth.router)
    app.include_router(v3_diagnostic.router)
    app.include_router(v3_chat.router)
    app.include_router(v3_assessment.router)
    app.include_router(v3_tracking.router)
    app.include_router(v3_incentive.router)
    app.include_router(v3_knowledge.router)
    print("[API] v3 路由已注册 (8 routers: auth/diagnostic/chat/assessment/tracking/incentive/knowledge/health)")
except Exception as e:
    print(f"[API] v3 路由注册失败: {e}")

# ============================================
# 注册 行智诊疗 (XZB) 专家个人AGENT路由
# ============================================
try:
    from api.xzb_api import router as xzb_router
    app.include_router(xzb_router)
    print("[API] 行智诊疗(XZB)路由已注册 (29 endpoints: experts/knowledge/chat/rx/med-circle)")
except ImportError as e:
    print(f"[API] 行智诊疗路由注册失败: {e}")

# 挂载静态文件服务
try:
    from fastapi.staticfiles import StaticFiles
    _static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    os.makedirs(_static_dir, exist_ok=True)
    app.mount("/api/static", StaticFiles(directory=_static_dir), name="static")
    print("[API] 静态文件服务已挂载 /api/static")
except Exception as e:
    print(f"[API] 静态文件服务挂载失败: {e}")

class AgentGateway:
    """行健行为教练网关：连接编排层与模型层"""
    
    @staticmethod
    async def call_dify_workflow(user_id: str, query: str):
        """调用 Dify 工作流（A1+A2 协同）"""
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": user_id
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(f"{DIFY_API_URL}/chat-messages", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Dify 连接失败: {str(e)}")

    @staticmethod
    def _get_system_prompt() -> str:
        """行健行为教练系统提示词"""
        return """你是"行健行为教练"，专注于行为健康干预。
你的职责包括：
1. 评估用户的健康状态和心理准备度
2. 提供个性化的行为建议
3. 推荐适合的健康任务

请用温和、专业的语气回复用户。"""

    @staticmethod
    async def call_ollama_direct(prompt: str):
        """直接调用 Ollama（用于快速指令或 A4 数据分析）"""
        system_prompt = AgentGateway._get_system_prompt()
        full_prompt = f"系统：{system_prompt}\n\n用户：{prompt}\n\n助手："

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{OLLAMA_API_URL}/api/generate", json=payload)
                return response.json()
        except httpx.TimeoutException:
            return {"response": "抱歉，服务响应超时，请稍后重试。"}
        except Exception as e:
            return {"response": f"服务暂时不可用：{str(e)}"}

    @staticmethod
    async def call_ollama_with_prompt(prompt: str, system_prompt: str):
        """使用指定 system_prompt 调用 Ollama (RAG 增强版)"""
        full_prompt = f"系统：{system_prompt}\n\n用户：{prompt}\n\n助手："

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(f"{OLLAMA_API_URL}/api/generate", json=payload)
                return response.json()
        except httpx.TimeoutException:
            return {"response": "抱歉，服务响应超时，请稍后重试。"}
        except Exception as e:
            return {"response": f"服务暂时不可用：{str(e)}"}

# --- API 路由 ---

@app.post("/api/v1/dispatch")
async def dispatch_request(
    user_id: str = Body("", embed=True),
    message: str = Body(..., embed=True),
    mode: str = Body("ollama", embed=True),  # 可选 dify 或 ollama
    agent_id: str = Body("", embed=True),
    tenant_id: str = Body("", embed=True),
    current_user: User = Depends(get_current_user),
):
    """行健行为教练分发中心：根据模式选择路由"""
    # user_id 可选，默认取当前登录用户
    if not user_id:
        user_id = str(current_user.id)

    if mode == "dify":
        # 走 Dify 编排好的 A1+A2+A3 完整工作流
        result = await AgentGateway.call_dify_workflow(user_id, message)
        return {
            "status": "success",
            "source": "Dify Orchestrator",
            "answer": result.get("answer"),
            "conversation_id": result.get("conversation_id")
        }
    else:
        # 直接调用本地模型 + RAG 知识库增强
        from sqlalchemy.orm import Session as DBSession
        from core.database import SessionLocal

        db = SessionLocal()
        rag_data = None
        try:
            from core.knowledge import rag_enhance, record_citations

            enhanced = rag_enhance(
                db=db,
                query=message,
                agent_id=agent_id,
                tenant_id=tenant_id,
                base_system_prompt=AgentGateway._get_system_prompt(),
            )

            # 用 RAG 增强后的 prompt 调用 Ollama
            result = await AgentGateway.call_ollama_with_prompt(
                prompt=message,
                system_prompt=enhanced.system_prompt,
            )
            answer = result.get("response", "")

            # 包装引用数据
            rag_data = enhanced.wrap_response(answer)

            # 记录引用 (审计)
            record_citations(
                db=db,
                enhanced=enhanced,
                llm_response=answer,
                agent_id=agent_id,
                tenant_id=tenant_id,
                user_id=user_id,
            )

        except Exception as e:
            logger_main = logging.getLogger("api.main")
            logger_main.warning(f"RAG 增强失败, 回退直接调用: {e}")
            result = await AgentGateway.call_ollama_direct(message)
            answer = result.get("response", "")
        finally:
            db.close()

        resp = {
            "status": "success",
            "source": "Ollama Local",
            "answer": rag_data["text"] if rag_data else answer,
        }
        if rag_data:
            resp["rag"] = rag_data
        return resp

@app.get("/health")
async def health():
    """Liveness 探针 — 进程存活即返回 200"""
    import time as _t
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(_t.time() - _app_start_time),
    }


@app.get("/ready")
async def readiness():
    """Readiness 探针 — DB 可连接才返回 200"""
    from fastapi.responses import JSONResponse
    try:
        from core.database import check_database_connection
        if check_database_connection():
            return {"status": "ready"}
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "database unreachable"})
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": str(e)})


@app.get("/api/v1/health")
async def comprehensive_health():
    """综合健康检查（检测所有依赖）"""
    from core.health import full_health_check
    return await full_health_check()


# --- 健康状态概览接口 (Home.vue 使用) ---
@app.get("/api/v1/health/latest-status")
async def get_latest_health_status(current_user: User = Depends(get_current_user)):
    """
    获取用户最新健康状态概览。

    返回最近血糖读数、趋势历史等，供首页健康卡片使用。
    """
    result = {
        "current_glucose": 0,
        "ai_content": "暂无数据",
        "strategy_name": "等待数据",
        "history": [],
        "timestamps": [],
    }
    try:
        from core.database import get_db_session
        from sqlalchemy import desc
        db = next(get_db_session())
        try:
            from core.models import DeviceData
            # 获取最近血糖数据
            readings = db.query(DeviceData).filter(
                DeviceData.user_id == current_user.id,
                DeviceData.data_type == "glucose",
            ).order_by(desc(DeviceData.recorded_at)).limit(10).all()

            if readings:
                latest = readings[0]
                result["current_glucose"] = float(latest.value) if latest.value else 0
                result["history"] = [float(r.value) for r in reversed(readings) if r.value]
                result["timestamps"] = [
                    r.recorded_at.strftime("%H:%M") if r.recorded_at else ""
                    for r in reversed(readings)
                ]
                result["ai_content"] = "数据已更新"
                result["strategy_name"] = "持续监测"
        except Exception:
            pass
        finally:
            db.close()
    except Exception:
        pass

    return result


# --- 系统通知接口 ---
@app.get("/api/v1/notifications/system")
async def get_system_notifications(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """
    获取系统通知列表。

    聚合积分变动、里程碑达成、晋级提醒等系统级通知。
    """
    notifications = []
    try:
        from core.database import SessionLocal
        from sqlalchemy import desc
        db = SessionLocal()
        try:
            # 尝试从 credit_events 获取最近积分变动
            from core.models import CreditEvent
            events = db.query(CreditEvent).filter(
                CreditEvent.user_id == current_user.id
            ).order_by(desc(CreditEvent.created_at)).limit(limit).all()
            for ev in events:
                notifications.append({
                    "type": "system",
                    "title": f"积分变动: {ev.event_type}",
                    "body": f"获得 {ev.points} 积分 — {ev.description or ''}",
                    "created_at": ev.created_at.isoformat() if ev.created_at else None,
                })
        except Exception:
            pass

        try:
            # 尝试从 user_milestones 获取里程碑
            from core.models import UserMilestone
            milestones = db.query(UserMilestone).filter(
                UserMilestone.user_id == current_user.id
            ).order_by(desc(UserMilestone.achieved_at)).limit(limit).all()
            for m in milestones:
                notifications.append({
                    "type": "task",
                    "title": f"里程碑达成: {m.milestone_key}",
                    "body": m.display_message or "恭喜你达成了新的里程碑！",
                    "created_at": m.achieved_at.isoformat() if m.achieved_at else None,
                })
        except Exception:
            pass

        try:
            # 从 notifications 表获取推送通知 (含处方审批通知)
            from sqlalchemy import text as sa_text
            notif_rows = db.execute(sa_text("""
                SELECT id, title, body, type, is_read, created_at
                FROM notifications
                WHERE user_id = CAST(:uid AS integer)
                ORDER BY created_at DESC LIMIT :lim
            """), {"uid": current_user.id, "lim": limit}).mappings().all()
            for r in notif_rows:
                # 解析 body 中的深度链接 [link:/rx/xxx]
                body_text = r["body"] or ""
                link = None
                if "[link:" in body_text:
                    import re
                    m = re.search(r'\[link:([^\]]+)\]', body_text)
                    if m:
                        link = m.group(1)
                        body_text = body_text[:m.start()].strip()
                notifications.append({
                    "type": r["type"] or "system",
                    "title": r["title"] or "",
                    "body": body_text,
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "notif_id": r["id"],
                    "is_read": r["is_read"],
                    "link": link,
                })
        except Exception:
            pass

        # 按时间倒序排列
        notifications.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        db.close()
    except Exception:
        pass

    return {"notifications": notifications[:limit]}


@app.get("/api/v1/notifications/all")
async def get_all_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """
    获取 notifications 表中的所有通知 (含处方审批、教练推送等)。
    支持 unread_only 过滤。
    """
    items = []
    try:
        from core.database import SessionLocal
        from sqlalchemy import text as sa_text
        db = SessionLocal()
        try:
            where_clause = "WHERE user_id = CAST(:uid AS integer)"
            if unread_only:
                where_clause += " AND is_read = false"
            rows = db.execute(sa_text(f"""
                SELECT id, title, body, type, is_read, created_at
                FROM notifications
                {where_clause}
                ORDER BY created_at DESC LIMIT :lim
            """), {"uid": current_user.id, "lim": limit}).mappings().all()
            for r in rows:
                body_text = r["body"] or ""
                link = None
                if "[link:" in body_text:
                    import re
                    m = re.search(r'\[link:([^\]]+)\]', body_text)
                    if m:
                        link = m.group(1)
                        body_text = body_text[:m.start()].strip()
                items.append({
                    "id": r["id"],
                    "title": r["title"] or "",
                    "body": body_text,
                    "type": r["type"] or "system",
                    "is_read": r["is_read"],
                    "link": link,
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                })
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[notifications/all] query failed: {e}")
    return {"notifications": items, "total": len(items)}


@app.post("/api/v1/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
):
    """标记通知为已读"""
    try:
        from core.database import SessionLocal
        from sqlalchemy import text as sa_text
        db = SessionLocal()
        try:
            db.execute(sa_text("""
                UPDATE notifications SET is_read = true
                WHERE id = :nid AND user_id = CAST(:uid AS integer)
            """), {"nid": notif_id, "uid": current_user.id})
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[notifications/read] update failed: {e}")
        raise HTTPException(status_code=500, detail="更新失败")
    return {"success": True}


# --- 处方查询接口 (供 H5 使用) ---
@app.get("/api/v1/rx/my")
async def get_my_prescriptions(
    status: str = "active",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的行为处方列表"""
    items = []
    try:
        from core.database import SessionLocal
        from sqlalchemy import text as sa_text
        db = SessionLocal()
        try:
            rows = db.execute(sa_text("""
                SELECT id, target_behavior, frequency_dose, time_place,
                       trigger_cue, obstacle_plan, support_resource,
                       domain, difficulty_level, cultivation_stage,
                       status, approved_by_review, created_at
                FROM behavior_prescriptions
                WHERE user_id = CAST(:uid AS integer) AND status = :st
                ORDER BY created_at DESC LIMIT :lim
            """), {"uid": current_user.id, "st": status, "lim": limit}).mappings().all()
            for r in rows:
                items.append({
                    "id": r["id"],
                    "target_behavior": r["target_behavior"] or "",
                    "frequency_dose": r["frequency_dose"] or "",
                    "time_place": r["time_place"] or "",
                    "trigger_cue": r["trigger_cue"] or "",
                    "obstacle_plan": r["obstacle_plan"] or "",
                    "support_resource": r["support_resource"] or "",
                    "domain": r["domain"] or "",
                    "difficulty_level": r["difficulty_level"] or "",
                    "cultivation_stage": r["cultivation_stage"] or "",
                    "status": r["status"] or "",
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                })
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"[rx/my] query failed: {e}")
    return {"prescriptions": items}


@app.get("/api/v1/rx/{rx_id}")
async def get_rx_detail_by_id(
    rx_id: str,
    current_user: User = Depends(get_current_user),
):
    """获取单个处方详情 (覆盖 behavior_rx 的 501 stub)"""
    try:
        from core.database import SessionLocal
        from sqlalchemy import text as sa_text
        db = SessionLocal()
        try:
            row = db.execute(sa_text("""
                SELECT id, user_id, target_behavior, frequency_dose, time_place,
                       trigger_cue, obstacle_plan, support_resource,
                       domain, difficulty_level, cultivation_stage,
                       status, approved_by_review, created_at
                FROM behavior_prescriptions
                WHERE id = :rid
            """), {"rid": rx_id}).mappings().first()
        finally:
            db.close()
    except Exception:
        raise HTTPException(status_code=500, detail="数据库查询失败")

    if not row:
        raise HTTPException(status_code=404, detail="处方不存在")

    # 权限检查: 用户只能看自己的, 教练可看学员的
    if row["user_id"] != current_user.id:
        from core.models import UserRole
        if current_user.role not in (UserRole.COACH, UserRole.PROMOTER, UserRole.SUPERVISOR, UserRole.MASTER, UserRole.ADMIN):
            raise HTTPException(status_code=403, detail="无权限查看")

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "target_behavior": row["target_behavior"] or "",
        "frequency_dose": row["frequency_dose"] or "",
        "time_place": row["time_place"] or "",
        "trigger_cue": row["trigger_cue"] or "",
        "obstacle_plan": row["obstacle_plan"] or "",
        "support_resource": row["support_resource"] or "",
        "domain": row["domain"] or "",
        "difficulty_level": row["difficulty_level"] or "",
        "cultivation_stage": row["cultivation_stage"] or "",
        "status": row["status"] or "",
        "approved_by_review": row["approved_by_review"] or "",
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


# --- 专家列表接口 ---
@app.get("/api/v1/experts")
async def get_experts(current_user: User = Depends(get_current_user)):
    """获取可用专家列表"""
    return [
        {"id": "mental_health", "name": "心理咨询师", "role": "情绪管理、压力调节、睡眠改善"},
        {"id": "nutrition", "name": "营养师", "role": "膳食指导、营养建议、体重管理"},
        {"id": "sports_rehab", "name": "运动康复师", "role": "运动处方、损伤康复、体态矫正"},
        {"id": "tcm_wellness", "name": "中医养生师", "role": "体质调理、四季养生、经络保健"}
    ]


# --- 个人看板接口 ---
@app.get("/api/v1/dashboard/{user_id}")
async def get_dashboard(user_id: str, current_user: User = Depends(get_current_user)):
    """获取用户个人看板数据"""
    # 模拟数据 (实际应从数据库/评估系统获取)
    import random
    base_score = random.randint(55, 75)

    return {
        "user_id": user_id,
        "overall_score": base_score,
        "stress_score": base_score - random.randint(5, 15),
        "fatigue_score": base_score - random.randint(0, 10),
        "trend": [
            {"date": "01-17", "score": base_score - 6},
            {"date": "01-18", "score": base_score - 2},
            {"date": "01-19", "score": base_score - 4},
            {"date": "01-20", "score": base_score + 1},
            {"date": "01-21", "score": base_score - 1},
            {"date": "01-22", "score": base_score},
            {"date": "01-23", "score": base_score}
        ],
        "risk_level": "medium" if base_score < 65 else "low",
        "recommendations": [
            "建议每天进行10分钟深呼吸练习",
            "保持规律作息，避免熬夜",
            "适当进行户外活动，接触阳光"
        ]
    }


# --- 任务分解接口 ---
@app.post("/api/v1/decompose")
async def decompose_tasks(
    message: str = Body(..., embed=True),
    efficacy_score: int = Body(50, embed=True),
    current_user: User = Depends(get_current_user),
):
    """根据用户消息和效能感分解任务"""
    # 根据效能感限幅
    if efficacy_score < 20:
        max_tasks, max_difficulty = 1, 1
    elif efficacy_score < 50:
        max_tasks, max_difficulty = 2, 2
    else:
        max_tasks, max_difficulty = 3, 5

    # 模拟任务生成 (实际应调用 LLM)
    sample_tasks = [
        {"id": 1, "content": "进行3次深呼吸练习", "difficulty": 1, "type": "mental", "completed": False},
        {"id": 2, "content": "记录今天的情绪日志", "difficulty": 2, "type": "mental", "completed": False},
        {"id": 3, "content": "饭后散步15分钟", "difficulty": 2, "type": "exercise", "completed": False},
        {"id": 4, "content": "睡前泡脚10分钟", "difficulty": 1, "type": "tcm", "completed": False},
        {"id": 5, "content": "补充一杯温水", "difficulty": 1, "type": "nutrition", "completed": False}
    ]

    # 按效能感限幅筛选
    filtered = [t for t in sample_tasks if t["difficulty"] <= max_difficulty][:max_tasks]

    return {
        "tasks": filtered,
        "efficacy_score": efficacy_score,
        "clamping_level": "minimal" if efficacy_score < 20 else ("moderate" if efficacy_score < 50 else "normal")
    }

# ============================================================================
# Orchestrator API - Master Agent 核心接口
# ============================================================================

@app.post("/orchestrator/process", response_model=OrchestratorResponse)
async def orchestrator_process(request: OrchestratorRequest, current_user: User = Depends(get_current_user)):
    """
    Master Agent 核心处理接口

    完整 9 步流程:
    1. Input Handler - 输入处理
    2. Profile Manager - 画像管理
    3. Risk Analyzer - 风险分析
    4. Agent Router - Agent 路由
    5. Multi-Agent Coordinator - 多 Agent 协调
    6. Intervention Planner - 干预规划
    7. Response Synthesizer - 响应合成
    8. Task Generator - 任务生成
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        # 解析 tenant_ctx
        tenant_ctx = None
        try:
            from core.database import SessionLocal
            _db = SessionLocal()
            try:
                tenant_ctx = _resolve_tenant_ctx_by_user_id(request.user_id, _db)
            finally:
                _db.close()
        except Exception:
            pass

        # 构建输入
        input_json = {
            "user_id": request.user_id,
            "input_type": request.input_type,
            "content": request.content or "",
            "timestamp": datetime.now().isoformat(),
            "session_id": request.session_id or f"sess_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "efficacy_score": request.efficacy_score or 50
        }

        if request.device_data:
            input_json["device_data"] = request.device_data.dict(exclude_none=True)

        # 注入 tenant_ctx 到输入
        if tenant_ctx:
            input_json["tenant_ctx"] = tenant_ctx

        # 使用 Pipeline 处理
        response_dict, pipeline_summary = master_agent.process_with_pipeline(input_json)

        # 构建响应
        return OrchestratorResponse(
            reply=response_dict.get("response", {}).get("text", ""),
            coach_style=response_dict.get("response", {}).get("coach_style", "supportive"),
            intervention_plan=response_dict.get("intervention_plan"),
            daily_tasks=response_dict.get("daily_tasks", []),
            daily_briefing=None,  # 可选：调用 generate_daily_briefing
            insights=response_dict.get("insights"),
            updated_profile=response_dict.get("profile_updates"),
            pipeline_summary=pipeline_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/orchestrator/briefing")
async def get_daily_briefing(request: DailyBriefingRequest, current_user: User = Depends(get_current_user)):
    """
    获取每日简报

    返回格式:
    {
      "user_id": "U12345",
      "date": "2026-01-23",
      "tasks": ["今晚22:30前上床", ...],
      "coach_message": "今晚我们先从规律作息开始..."
    }
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        briefing = master_agent.generate_daily_briefing(request.user_id)
        return briefing.to_full_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成简报失败: {str(e)}")


@app.get("/orchestrator/briefing/{user_id}/message")
async def get_daily_message(user_id: str, current_user: User = Depends(get_current_user)):
    """获取格式化的每日推送消息"""
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        message = master_agent.get_daily_push_message(user_id)
        return {"user_id": user_id, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成消息失败: {str(e)}")


@app.post("/orchestrator/agent-task")
async def execute_agent_task(request: AgentTaskRequest, current_user: User = Depends(get_current_user)):
    """
    执行单个 Agent 任务

    支持的 Agent 类型:
    - SleepAgent: 睡眠分析
    - GlucoseAgent: 血糖分析
    - StressAgent: 压力分析
    - NutritionAgent: 营养分析
    - MentalHealthAgent: 心理健康
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        task_json = {
            "task_id": request.task_id,
            "agent_type": request.agent_type,
            "question": request.question,
            "priority": request.priority,
            "context": request.context or {}
        }

        result = master_agent.process_agent_task_json(task_json)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")


@app.post("/orchestrator/action-plan")
async def create_action_plan(request: ActionPlanRequest, current_user: User = Depends(get_current_user)):
    """
    创建行动计划

    返回阶段性干预方案，包含:
    - goal: 干预目标
    - phase: 当前阶段
    - actions: 行动项列表
    - evaluation: 评估标准
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        # 获取用户画像
        profile = master_agent.profile_manager.get_profile(request.user_id)

        # 收集分析结果
        analysis_results = master_agent.collect_multi_agent_analysis(profile, {})

        # 创建计划
        plan = master_agent.create_action_plan(
            goal=request.goal,
            analysis_results=analysis_results,
            profile=profile,
            phase=request.phase
        )

        return plan.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建计划失败: {str(e)}")


@app.get("/orchestrator/action-plan/{user_id}/phased")
async def get_phased_plan(user_id: str, goal: str = "健康管理", weeks: int = 4, current_user: User = Depends(get_current_user)):
    """获取多阶段行动计划"""
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        profile = master_agent.profile_manager.get_profile(user_id)
        plans = master_agent.generate_phased_plan(
            goal=goal,
            profile=profile,
            recent_data={},
            total_weeks=weeks
        )
        return {"user_id": user_id, "plans": [p.to_dict() for p in plans]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成计划失败: {str(e)}")


@app.get("/orchestrator/profile/{user_id}")
async def get_user_profile(user_id: str, current_user: User = Depends(get_current_user)):
    """获取用户画像"""
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        profile = master_agent.profile_manager.get_profile(user_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取画像失败: {str(e)}")


@app.post("/orchestrator/device-sync")
async def sync_device_data(
    user_id: str = Body(...),
    device_data: DeviceDataInput = Body(...),
    current_user: User = Depends(get_current_user),
):
    """同步穿戴设备数据"""
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        from core.master_agent import DeviceData, CGMData, HRVData, SleepData

        # 转换设备数据
        dd = DeviceData(
            cgm=CGMData(**device_data.cgm) if device_data.cgm else None,
            hrv=HRVData(**device_data.hrv) if device_data.hrv else None,
            sleep=SleepData(**device_data.sleep) if device_data.sleep else None,
            steps=device_data.steps
        )

        response = master_agent.sync_device_data(user_id, dd)
        return response.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ============================================================================
# 系统状态
class RouteRequest(BaseModel):
    """路由请求"""
    user_id: str
    intent: str = Field(..., description="用户意图/消息")
    risk_level: str = Field("low", description="风险等级: critical/high/moderate/low")
    risk_score: float = Field(30, ge=0, le=100)
    risk_factors: List[str] = []
    device_data: Optional[Dict[str, Any]] = None


@app.post("/orchestrator/coordinate")
async def coordinate_agents(request: CoordinateRequest, current_user: User = Depends(get_current_user)):
    """
    协调多个 Agent 结果 - 冲突消解 + 权重融合

    输入: 多个 Agent 的分析结果
    输出: 融合后的统一分析

    示例请求:
    {
      "agent_results": [
        {"agent": "GlucoseAgent", "analysis": "血糖偏高", "risk_level": "medium", "suggestions": ["控制饮食"]},
        {"agent": "SleepAgent", "analysis": "睡眠不足", "risk_level": "medium", "suggestions": ["早睡"]}
      ]
    }
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        # 转换为字典列表
        results_json = [r.dict() for r in request.agent_results]

        # 执行协调
        integrated = master_agent.coordinate_from_json(results_json)

        return integrated

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"协调失败: {str(e)}")


@app.post("/orchestrator/route")
async def route_agents(request: RouteRequest, current_user: User = Depends(get_current_user)):
    """
    Agent 路由 - 选择最合适的 Agent 组合

    返回格式:
    [
      {"agent": "GlucoseAgent", "priority": 1},
      {"agent": "SleepAgent", "priority": 2}
    ]
    """
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        # 获取用户画像
        profile = master_agent.profile_manager.get_profile(request.user_id)

        # 构建风险信息
        risk = {
            "level": request.risk_level,
            "score": request.risk_score,
            "factors": request.risk_factors
        }

        # 执行路由
        agents = master_agent.route_agents(
            profile=profile,
            intent=request.intent,
            risk=risk,
            device_data=request.device_data
        )

        return {
            "user_id": request.user_id,
            "intent": request.intent[:50],
            "agents": agents
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路由失败: {str(e)}")


@app.post("/orchestrator/route/detailed")
async def route_agents_detailed(request: RouteRequest, current_user: User = Depends(get_current_user)):
    """Agent 路由 (详细版) - 返回完整路由信息"""
    master_agent = get_master_agent()
    if not master_agent:
        raise HTTPException(status_code=503, detail="MasterAgent 服务不可用")

    try:
        profile = master_agent.profile_manager.get_profile(request.user_id)

        risk = {
            "level": request.risk_level,
            "score": request.risk_score,
            "factors": request.risk_factors
        }

        result = master_agent.route_agents_detailed(
            profile=profile,
            intent=request.intent,
            risk=risk,
            device_data=request.device_data
        )

        return {
            "user_id": request.user_id,
            "agents": result.agents,
            "primary_agent": result.primary_agent,
            "secondary_agents": result.secondary_agents,
            "reasoning": result.reasoning,
            "confidence": result.confidence
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路由失败: {str(e)}")


# ============================================================================

@app.get("/orchestrator/status")
async def orchestrator_status(current_user: User = Depends(get_current_user)):
    """获取 Orchestrator 状态"""
    master_agent = get_master_agent()
    return {
        "status": "online" if master_agent else "unavailable",
        "version": "2.0",
        "components": {
            "master_agent": master_agent is not None,
            "profile_manager": master_agent.profile_manager is not None if master_agent else False,
            "risk_assessor": master_agent.risk_assessor is not None if master_agent else False,
            "pipeline": True
        },
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# [v16-NEW] TTM 大脑判定 API (SOP 6.2 + L6 叙事)
# ============================================================================

class BrainEvaluateRequest(BaseModel):
    """TTM 阶段跃迁判定请求"""
    user_id: str = Field(..., description="用户ID")
    current_stage: str = Field("S0", description="当前 TTM 阶段: S0-S5")
    belief: float = Field(0.0, ge=0.0, le=1.0, description="信念指数")
    action_count_3d: int = Field(0, ge=0, description="近 3 天行动次数")


def save_behavior_to_db(
    user_id: str,
    result: Dict[str, Any],
    source_ui: Optional[str],
    belief: float,
    action_count: int,
):
    """
    后台写入数据库 — 被 BackgroundTasks 调用，不阻塞 API 响应。
    同时写入三张表：behavior_traces / behavior_history / behavior_audit_logs
    """
    from core.database import db_transaction
    from core.models import BehaviorAuditLog, BehaviorHistory, BehaviorTrace
    from loguru import logger

    try:
        with db_transaction() as db:
            # 长期记忆：完整快照（周报分析数据源）
            db.add(BehaviorTrace(
                user_id=user_id,
                from_stage=result["from_stage"],
                to_stage=result["to_stage"],
                is_transition=result.get("is_transition", False),
                belief_score=belief,
                action_count=action_count,
                narrative_sent=result.get("narrative"),
                source_ui=source_ui,
            ))

            # 全量历史：每次评估都记录
            db.add(BehaviorHistory(
                user_id=user_id,
                from_stage=result["from_stage"],
                to_stage=result["to_stage"],
                is_transition=result.get("is_transition", False),
                belief_score=belief,
                narrative_sent=result.get("narrative"),
            ))

            # 审计日志：仅跃迁时记录
            if result.get("is_transition"):
                db.add(BehaviorAuditLog(
                    user_id=user_id,
                    from_stage=result["from_stage"],
                    to_stage=result["to_stage"],
                    narrative=result.get("narrative"),
                    source_ui=source_ui,
                ))

        logger.info(f"[Brain] 行为记录已写入 user={user_id} transition={result.get('is_transition')}")
    except Exception as e:
        logger.error(f"[Brain] 行为记录写入失败 user={user_id}: {e}")


@app.post("/api/v1/brain/evaluate")
async def brain_evaluate(
    request: BrainEvaluateRequest,
    background_tasks: BackgroundTasks,
    x_source_ui: Optional[str] = Header(None, alias="X-Source-UI"),
    current_user: User = Depends(get_current_user),
):
    """
    TTM 阶段跃迁判定入口

    - X-Source-UI: UI-1 → SOP 6.2 防火墙静默
    - X-Source-UI: UI-3 等 → 进入大脑判定 + L6 叙事重写
    - 数据库写入通过 BackgroundTasks 异步执行，不阻塞响应
    """
    from core.brain.decision_engine import BehavioralBrain

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "spi_mapping.json",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    brain = BehavioralBrain(config)
    result = brain.process(
        source_ui=x_source_ui,
        current_state=request.dict(),
    )

    # 非防火墙请求 → 后台写入数据库，不阻塞 UI 响应
    if not result.get("bypass_brain"):
        background_tasks.add_task(
            save_behavior_to_db,
            user_id=request.user_id,
            result=result,
            source_ui=x_source_ui,
            belief=request.belief,
            action_count=request.action_count_3d,
        )

    return result


# ============================================================================
# [v16-NEW] 注册 Admin 行为配置路由
# ============================================================================
try:
    from api.v14.admin_routes import router as admin_behavior_router
    app.include_router(admin_behavior_router, prefix="/api/v1")
    print("[API] v16 Admin行为配置路由已注册")
except ImportError as e:
    print(f"[API] v16 Admin行为配置路由注册失败: {e}")

# ============================================================================
# CoachCopilot 路由 (copilot/analyze + copilot/suggested-actions)
# ============================================================================
try:
    from api.v14.copilot_routes import router as copilot_router
    app.include_router(copilot_router, prefix="/api/v1")
    print("[API] CoachCopilot路由已注册")
except ImportError as e:
    print(f"[API] CoachCopilot路由注册失败: {e}")

# ============================================================================
# Patient 档案路由
# ============================================================================
try:
    from api.patient_api import router as patient_router
    app.include_router(patient_router)
    print("[API] Patient路由已注册")
except ImportError as e:
    print(f"[API] Patient路由注册失败: {e}")

# ============================================================================
# Recommendation 推荐系统路由
# ============================================================================
try:
    from api.recommendation_api import router as recommendation_router
    app.include_router(recommendation_router)
    print("[API] Recommendation路由已注册")
except ImportError as e:
    print(f"[API] Recommendation路由注册失败: {e}")

# ============================================================================
# [v16-NEW] 注册专家白标租户路由
# ============================================================================
try:
    from api.tenant_api import router as tenant_router
    app.include_router(tenant_router)
    print("[API] 专家租户路由已注册")
except ImportError as e:
    print(f"[API] 专家租户路由注册失败: {e}")

# 注册督导会议路由
try:
    from api.supervision_api import router as supervision_router
    app.include_router(supervision_router)
    print("[API] 督导会议路由已注册")
except ImportError as e:
    print(f"[API] 督导会议路由注册失败: {e}")

# 注册专家内容工作室路由
try:
    from api.expert_content_api import router as expert_content_router
    app.include_router(expert_content_router)
    print("[API] 专家内容工作室路由已注册")
except ImportError as e:
    print(f"[API] 专家内容工作室路由注册失败: {e}")

# 注册Coach分析路由
try:
    from api.analytics_api import router as coach_analytics_router
    app.include_router(coach_analytics_router)
    print("[API] Coach分析路由已注册")
except ImportError as e:
    print(f"[API] Coach分析路由注册失败: {e}")

# 注册Admin分析路由
try:
    from api.admin_analytics_api import router as admin_analytics_router
    app.include_router(admin_analytics_router)
    print("[API] Admin分析路由已注册")
except ImportError as e:
    print(f"[API] Admin分析路由注册失败: {e}")

# 注册用户知识投稿路由
try:
    from api.content_contribution_api import router as contribution_router
    app.include_router(contribution_router)
    print("[API] 用户知识投稿路由已注册")
except ImportError as e:
    print(f"[API] 用户知识投稿路由注册失败: {e}")

# 注册批量知识灌注路由
try:
    from api.batch_ingestion_api import router as batch_ingestion_router
    app.include_router(batch_ingestion_router)
    print("[API] 批量知识灌注路由已注册")
except ImportError as e:
    print(f"[API] 批量知识灌注路由注册失败: {e}")

# 注册内容管理路由
try:
    from api.content_manage_api import router as content_manage_router
    app.include_router(content_manage_router)
    print("[API] 内容管理路由已注册")
except ImportError as e:
    print(f"[API] 内容管理路由注册失败: {e}")

# 注册考试管理路由
try:
    from api.exam_api import router as exam_admin_router
    app.include_router(exam_admin_router)
    print("[API] 考试管理路由已注册")
except ImportError as e:
    print(f"[API] 考试管理路由注册失败: {e}")

# 注册题库管理路由
try:
    from api.question_api import router as question_router
    app.include_router(question_router)
    print("[API] 题库管理路由已注册")
except ImportError as e:
    print(f"[API] 题库管理路由注册失败: {e}")

# 注册考试会话路由
try:
    from api.exam_session_api import router as exam_session_router
    app.include_router(exam_session_router)
    print("[API] 考试会话路由已注册")
except ImportError as e:
    print(f"[API] 考试会话路由注册失败: {e}")

# 注册用户统计路由
try:
    from api.user_stats_api import router as user_stats_router
    app.include_router(user_stats_router)
    print("[API] 用户统计路由已注册")
except ImportError as e:
    print(f"[API] 用户统计路由注册失败: {e}")

# 注册问卷引擎路由 (3个子模块: 管理/填写/统计)
try:
    from api.survey_api import router as survey_mgmt_router
    app.include_router(survey_mgmt_router)
    print("[API] 问卷管理路由已注册")
except ImportError as e:
    print(f"[API] 问卷管理路由注册失败: {e}")

try:
    from api.survey_response_api import router as survey_respond_router
    app.include_router(survey_respond_router)
    print("[API] 问卷填写路由已注册")
except ImportError as e:
    print(f"[API] 问卷填写路由注册失败: {e}")

try:
    from api.survey_stats_api import router as survey_stats_router
    app.include_router(survey_stats_router)
    print("[API] 问卷统计路由已注册")
except ImportError as e:
    print(f"[API] 问卷统计路由注册失败: {e}")


# ========== 学分制+晋级体系 (V002) ==========
try:
    from api.credits_api import router as credits_router
    app.include_router(credits_router)
    print("[API] 学分管理路由已注册")
except ImportError as e:
    print(f"[API] 学分管理路由注册失败: {e}")

try:
    from api.companion_api import router as companion_router
    app.include_router(companion_router)
    print("[API] 同道者关系路由已注册")
except ImportError as e:
    print(f"[API] 同道者关系路由注册失败: {e}")

try:
    from api.promotion_api import router as promotion_router
    app.include_router(promotion_router)
    print("[API] 晋级系统路由已注册")
except ImportError as e:
    print(f"[API] 晋级系统路由注册失败: {e}")

# ========== V004 智能监测方案引擎路由 ==========
try:
    from api.program_api import router as program_router
    app.include_router(program_router)
    print("[API] V004 智能监测方案路由已注册")
except ImportError as e:
    print(f"[API] V004 智能监测方案路由注册失败: {e}")

# ========== V005 安全管理路由 ==========
try:
    from api.safety_api import router as safety_router
    app.include_router(safety_router)
    print("[API] V005 安全管理路由已注册")
except ImportError as e:
    print(f"[API] V005 安全管理路由注册失败: {e}")

# ========== V007 策略引擎路由 ==========
try:
    from api.policy_api import router as policy_router
    app.include_router(policy_router)
    print("[API] V007 策略引擎路由已注册")
except ImportError as e:
    print(f"[API] V007 策略引擎路由注册失败: {e}")

# ========== V006 Agent 模板管理路由 ==========
try:
    from api.agent_template_api import router as agent_template_router
    app.include_router(agent_template_router)
    print("[API] V006 Agent 模板管理路由已注册")
except ImportError as e:
    print(f"[API] V006 Agent 模板管理路由注册失败: {e}")

# ========== 专家自助注册入驻路由 ==========
try:
    from api.expert_registration_api import router as expert_registration_router
    app.include_router(expert_registration_router)
    print("[API] 专家自助注册入驻路由已注册")
except ImportError as e:
    print(f"[API] 专家自助注册入驻路由注册失败: {e}")

# ========== 专家自助 Agent 管理路由 ==========
try:
    from api.expert_agent_api import router as expert_agent_router
    app.include_router(expert_agent_router)
    print("[API] 专家自助 Agent 管理路由已注册")
except ImportError as e:
    print(f"[API] 专家自助 Agent 管理路由注册失败: {e}")

# ========== Phase 5 Agent 生态路由 ==========
try:
    from api.agent_ecosystem_api import router as agent_ecosystem_router
    app.include_router(agent_ecosystem_router)
    print("[API] Phase 5 Agent 生态路由已注册")
except ImportError as e:
    print(f"[API] Phase 5 Agent 生态路由注册失败: {e}")

# ========== Phase 4 反馈学习闭环路由 ==========
try:
    from api.agent_feedback_api import router as agent_feedback_router
    app.include_router(agent_feedback_router)
    print("[API] Phase 4 反馈学习闭环路由已注册")
except ImportError as e:
    print(f"[API] Phase 4 反馈学习闭环路由注册失败: {e}")

# ========== Phase 3 知识共享路由 ==========
try:
    from api.knowledge_sharing_api import router as knowledge_sharing_router
    app.include_router(knowledge_sharing_router)
    print("[API] Phase 3 知识共享路由已注册")
except ImportError as e:
    print(f"[API] Phase 3 知识共享路由注册失败: {e}")

# ========== V003 激励体系路由 ==========
try:
    from core.milestone_service import incentive_router
    app.include_router(incentive_router)
    print("[API] V003 激励体系路由已注册")
except Exception as e:
    print(f"[API] V003 激励体系路由注册失败: {e}")

# ========== 行为处方 (Behavior Rx) 路由 ==========
try:
    from behavior_rx.rx_routes import router as rx_router
    app.include_router(rx_router)
    print("[API] 行为处方 (Behavior Rx) 路由已注册")
except ImportError as e:
    print(f"[API] 行为处方路由注册失败: {e}")

# ========== V4.0 旅程状态路由 ==========
try:
    from api.journey_api import router as journey_router
    app.include_router(journey_router)
    print("[API] V4.0 旅程状态路由已注册")
except ImportError as e:
    print(f"[API] V4.0 旅程状态路由注册失败: {e}")

# ========== V4.0 治理体系路由 ==========
try:
    from api.governance_api import router as governance_router
    app.include_router(governance_router)
    print("[API] V4.0 治理体系路由已注册")
except ImportError as e:
    print(f"[API] V4.0 治理体系路由注册失败: {e}")

# ========== V4.0 Sprint 2: 价值重塑路由 ==========
for _mod, _name in [
    ("api.peer_matching_api", "同伴配对"),
    ("api.agency_api", "主体性引擎"),
    ("api.incentive_phase_api", "三阶激励"),
    ("api.peer_support_api", "同伴支持"),
    ("api.reflection_api", "反思日志"),
    ("api.advanced_rights_api", "高级权益"),
    ("api.script_library_api", "话术库"),
    ("api.ecosystem_v4_api", "生态系统"),
    ("api.ies_api", "IES效果评分"),
    ("api.contract_api", "契约管理"),
]:
    try:
        _m = __import__(_mod, fromlist=["router"])
        app.include_router(_m.router)
        print(f"[API] V4.0 {_name}路由已注册")
    except ImportError as e:
        print(f"[API] V4.0 {_name}路由注册失败: {e}")

# 注册遗漏的 routes.py 路由（审计修复 #7）
try:
    from api.routes import router as legacy_v1_router
    app.include_router(legacy_v1_router)
    print("[API] v1 通用路由已注册")
except ImportError as e:
    print(f"[API] v1 通用路由注册失败: {e}")

# ========== V4.1 Agent双层分离路由 ==========
try:
    from assistant_agents.router import router as assistant_router
    app.include_router(assistant_router)
    print("[API] V4.1 用户层Agent路由已注册 (/v1/assistant)")
except ImportError as e:
    print(f"[API] V4.1 用户层Agent路由注册失败: {e}")

try:
    from professional_agents.router import router as professional_router
    app.include_router(professional_router)
    print("[API] V4.1 教练层Agent路由已注册 (/v1/professional)")
except ImportError as e:
    print(f"[API] V4.1 教练层Agent路由注册失败: {e}")

try:
    from gateway.router import router as gateway_router
    app.include_router(gateway_router)
    print("[API] V4.1 跨层网关路由已注册 (/v1/gateway)")
except ImportError as e:
    print(f"[API] V4.1 跨层网关路由注册失败: {e}")

# ========== R2-R8 飞轮实装路由 (必须在bridge之前注册, 避免catch-all拦截) ==========
try:
    from api.r2_scheduler_agent import scheduler_router
    app.include_router(scheduler_router)
    print("[API] R2 scheduler_agent API 已注册")
except Exception as e:
    print(f"[API] R2 scheduler_agent: {e}")

try:
    from api.r3_grower_flywheel_api_live import router as grower_live_router
    app.include_router(grower_live_router)
    print("[API] R3 Grower飞轮(Live) 已注册 (5 endpoints)")
except Exception as e:
    print(f"[API] R3 Grower(Live): {e}")

try:
    from api.r4_role_upgrade_trigger import router as upgrade_router
    app.include_router(upgrade_router)
    print("[API] R4 角色升级触发器 已注册 (2 endpoints)")
except Exception as e:
    print(f"[API] R4 role_upgrade: {e}")

try:
    from api.r5_observer_flywheel_api_live import router as observer_live_router
    app.include_router(observer_live_router)
    print("[API] R5 Observer飞轮(Live) 已注册 (3 endpoints)")
except Exception as e:
    print(f"[API] R5 Observer(Live): {e}")

try:
    from api.r6_coach_flywheel_api_live import router as coach_live_router
    app.include_router(coach_live_router)
    print("[API] R6 Coach飞轮(Live) 已注册 (4 endpoints)")
except Exception as e:
    print(f"[API] R6 Coach(Live): {e}")

try:
    from api.r7_notification_agent import notif_router
    app.include_router(notif_router)
    print("[API] R7 通知API 已注册 (2 endpoints)")
except Exception as e:
    print(f"[API] R7 notification: {e}")

try:
    from api.r8_user_context import router as context_router
    app.include_router(context_router)
    print("[API] R8 用户上下文 已注册 (3 endpoints)")
except Exception as e:
    print(f"[API] R8 user_context: {e}")

try:
    from gateway.bridge import bridge_router
    app.include_router(bridge_router)
    print("[API] V4.1 兼容桥接路由已注册 (旧路径→新路径)")
except ImportError as e:
    print(f"[API] V4.1 兼容桥接路由注册失败: {e}")

# ========== V4.2 Admin绑定管理路由 ==========
try:
    from api.admin_bindings_api import router as admin_bindings_router
    app.include_router(admin_bindings_router)
    print("[API] V4.2 Admin绑定管理路由已注册 (/v1/admin/bindings)")
except ImportError as e:
    print(f"[API] V4.2 Admin绑定管理路由注册失败: {e}")

# ========== V4.3 中医骨科康复Agent注册表 ==========
try:
    from api.routes_tcm_ortho import TCM_ORTHO_AGENT_REGISTRY, GATEWAY_EXTENSIONS
    print(f"[API] V4.3 中医骨科Agent注册表已加载 ({len(TCM_ORTHO_AGENT_REGISTRY)} agents, {len(GATEWAY_EXTENSIONS)} gateway endpoints)")
except ImportError as e:
    print(f"[API] V4.3 中医骨科Agent注册表加载失败: {e}")


# ========== V5.0 飞轮API路由 ==========
# --- Expert + Admin ---
try:
    from api.expert_flywheel_api import router as expert_flywheel_router
    app.include_router(expert_flywheel_router)
    print("[API] V5.0 Expert飞轮路由已注册 (4 endpoints)")
except ImportError as e:
    print(f"[API] V5.0 Expert飞轮路由注册失败: {e}")

try:
    from api.admin_flywheel_api import router as admin_flywheel_router
    app.include_router(admin_flywheel_router)
    print("[API] V5.0 Admin飞轮路由已注册 (12 endpoints)")
except ImportError as e:
    print(f"[API] V5.0 Admin飞轮路由注册失败: {e}")

try:
    from api.settings_api import router as settings_router
    app.include_router(settings_router)
    print("[API] P4 Settings路由已注册 (2 endpoints)")
except ImportError as e:
    print(f"[API] P4 Settings路由注册失败: {e}")


# ========== P5 Routes ==========
try:
    from api.wechat_auth_api import router as wechat_auth_router
    app.include_router(wechat_auth_router)
    print("[API] P5A WeChat Auth路由已注册 (7 endpoints)")
except ImportError as e:
    print(f"[API] P5A WeChat Auth路由注册失败: {e}")

try:
    from api.event_tracking_api import router as event_tracking_router
    app.include_router(event_tracking_router)
    print("[API] P5B Event Tracking路由已注册 (1 endpoint)")
except ImportError as e:
    print(f"[API] P5B Event Tracking路由注册失败: {e}")

try:
    from api.operations_report_api import router as ops_report_router
    app.include_router(ops_report_router)
    print("[API] P5B Operations Report路由已注册 (3 endpoints)")
except ImportError as e:
    print(f"[API] P5B Operations Report路由注册失败: {e}")

try:
    from api.feature_flag_api import router as feature_flag_router
    app.include_router(feature_flag_router)
    print("[API] P5C Feature Flags路由已注册 (6 endpoints)")
except ImportError as e:
    print(f"[API] P5C Feature Flags路由注册失败: {e}")

try:
    from api.sharer_flywheel_api import router as sharer_flywheel_router
    app.include_router(sharer_flywheel_router)
    print("[API] Sharer飞轮API已注册 (3 endpoints)")
except Exception as e:
    print(f"[API] Sharer飞轮API: {e}")


# (R2-R8 已移到 bridge 之前注册, 见上方)


# ========== 审计治理 I-07: 督导资质管理 ==========
try:
    from api.supervisor_credential_api import router as credential_router
    app.include_router(credential_router)
    print("[API] I-07 督导资质管理路由已注册 (4 endpoints)")
except ImportError as e:
    print(f"[API] I-07 督导资质管理路由注册失败: {e}")


# ========== VisionGuard 视力行为保护 ==========
try:
    from api.vision_api import router as vision_router
    app.include_router(vision_router)
    print("[API] VisionGuard 视力行为保护路由已注册 (14 endpoints)")
except ImportError as e:
    print(f"[API] VisionGuard 路由注册失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)