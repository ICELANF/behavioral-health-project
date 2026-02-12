# -*- coding: utf-8 -*-
import os
import sys
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from fastapi import BackgroundTasks, FastAPI, Body, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 延迟导入 Master Agent (避免循环依赖)
_master_agent = None

def get_master_agent():
    """懒加载 MasterAgent — 优先从 DB 模板加载, 降级到硬编码"""
    global _master_agent
    if _master_agent is None:
        try:
            from core.master_agent import MasterAgent
            # 尝试用 DB session 初始化 (从模板加载 Agent)
            db_session = None
            try:
                from core.database import SessionLocal
                db_session = SessionLocal()
                _master_agent = MasterAgent(db_session=db_session)
            except Exception as e:
                print(f"[API] MasterAgent DB 模板加载失败, 使用硬编码: {e}")
                _master_agent = MasterAgent()
            finally:
                if db_session:
                    db_session.close()
            print("[API] MasterAgent 初始化成功")
        except Exception as e:
            print(f"[API] MasterAgent 初始化失败: {e}")
    return _master_agent


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

_scheduler = None

@asynccontextmanager
async def lifespan(app):
    """启动/关闭 APScheduler + Agent 模板缓存预热"""
    global _scheduler
    try:
        from core.scheduler import setup_scheduler
        _scheduler = setup_scheduler()
        if _scheduler:
            _scheduler.start()
            print("[API] APScheduler 已启动")
    except Exception as e:
        print(f"[API] APScheduler 启动失败: {e}")

    # Agent 模板缓存预热
    try:
        from core.database import SessionLocal
        from core.agent_template_service import load_templates
        db = SessionLocal()
        try:
            templates = load_templates(db)
            print(f"[API] Agent 模板缓存预热完成: {len(templates)} 个模板")
        finally:
            db.close()
    except Exception as e:
        print(f"[API] Agent 模板缓存预热失败 (非阻塞): {e}")

    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
        print("[API] APScheduler 已关闭")

app = FastAPI(title="BHP Xingjian Agent Gateway", version="3.1.0", lifespan=lifespan)

# --- 配置中心 (从 api.config 集中读取) ---
from api.config import DIFY_API_URL, DIFY_API_KEY, OLLAMA_API_URL, OLLAMA_MODEL

# --- 生产级中间件 (CORS白名单 + 安全头 + 日志 + 限流 + Sentry) ---
from core.middleware import setup_production_middleware
setup_production_middleware(app)

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
    user_id: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    mode: str = Body("dify", embed=True),  # 可选 dify 或 ollama
    agent_id: str = Body("", embed=True),
    tenant_id: str = Body("", embed=True),
):
    """行健行为教练分发中心：根据模式选择路由"""

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
    """基础健康检查（快速）"""
    return {"status": "online", "version": "16.0.0"}


@app.get("/api/v1/health")
async def comprehensive_health():
    """综合健康检查（检测所有依赖）"""
    from core.health import full_health_check
    return await full_health_check()


# --- 专家列表接口 ---
@app.get("/api/v1/experts")
async def get_experts():
    """获取可用专家列表"""
    return [
        {"id": "mental_health", "name": "心理咨询师", "role": "情绪管理、压力调节、睡眠改善"},
        {"id": "nutrition", "name": "营养师", "role": "膳食指导、营养建议、体重管理"},
        {"id": "sports_rehab", "name": "运动康复师", "role": "运动处方、损伤康复、体态矫正"},
        {"id": "tcm_wellness", "name": "中医养生师", "role": "体质调理、四季养生、经络保健"}
    ]


# --- 个人看板接口 ---
@app.get("/api/v1/dashboard/{user_id}")
async def get_dashboard(user_id: str):
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
    efficacy_score: int = Body(50, embed=True)
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
async def orchestrator_process(request: OrchestratorRequest):
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
async def get_daily_briefing(request: DailyBriefingRequest):
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
async def get_daily_message(user_id: str):
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
async def execute_agent_task(request: AgentTaskRequest):
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
async def create_action_plan(request: ActionPlanRequest):
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
async def get_phased_plan(user_id: str, goal: str = "健康管理", weeks: int = 4):
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
async def get_user_profile(user_id: str):
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
    device_data: DeviceDataInput = Body(...)
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
async def coordinate_agents(request: CoordinateRequest):
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
async def route_agents(request: RouteRequest):
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
async def route_agents_detailed(request: RouteRequest):
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
async def orchestrator_status():
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
# [v16-NEW] 注册专家白标租户路由
# ============================================================================
try:
    from api.tenant_api import router as tenant_router
    app.include_router(tenant_router)
    print("[API] 专家租户路由已注册")
except ImportError as e:
    print(f"[API] 专家租户路由注册失败: {e}")

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

# ========== V006 Agent 模板管理路由 ==========
try:
    from api.agent_template_api import router as agent_template_router
    app.include_router(agent_template_router)
    print("[API] V006 Agent 模板管理路由已注册")
except ImportError as e:
    print(f"[API] V006 Agent 模板管理路由注册失败: {e}")

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

# 注册遗漏的 routes.py 路由（审计修复 #7）
try:
    from api.routes import router as legacy_v1_router
    app.include_router(legacy_v1_router)
    print("[API] v1 通用路由已注册")
except ImportError as e:
    print(f"[API] v1 通用路由注册失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)