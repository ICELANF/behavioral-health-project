# -*- coding: utf-8 -*-
import os
import sys
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 延迟导入 Master Agent (避免循环依赖)
_master_agent = None

def get_master_agent():
    """懒加载 MasterAgent"""
    global _master_agent
    if _master_agent is None:
        try:
            from core.master_agent import MasterAgent
            _master_agent = MasterAgent()
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


app = FastAPI(title="Xingjian Agent Gateway", version="2.0")

# --- 配置中心 (后续可移入 .env 文件) ---
DIFY_API_URL = "http://localhost/v1"  # Dify Docker 默认地址
DIFY_API_KEY = "app-your-dify-api-key-here"  # 替换为你的 Dify API Key
OLLAMA_API_URL = "http://localhost:11434/api/generate"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{DIFY_API_URL}/chat-messages", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Dify 连接失败: {str(e)}")

    @staticmethod
    async def call_ollama_direct(prompt: str):
        """直接调用 Ollama（用于快速指令或 A4 数据分析）"""
        # 构建行健行为教练系统提示词
        system_prompt = """你是"行健行为教练"，专注于行为健康干预。
你的职责包括：
1. 评估用户的健康状态和心理准备度
2. 提供个性化的行为建议
3. 推荐适合的健康任务

请用温和、专业的语气回复用户。"""

        full_prompt = f"系统：{system_prompt}\n\n用户：{prompt}\n\n助手："

        payload = {
            "model": "qwen2.5:14b",
            "prompt": full_prompt,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(OLLAMA_API_URL, json=payload)
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
    mode: str = Body("dify", embed=True)  # 可选 dify 或 ollama
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
        # 直接调用本地模型执行原子任务
        result = await AgentGateway.call_ollama_direct(message)
        return {
            "status": "success",
            "source": "Ollama Local",
            "answer": result.get("response")
        }

@app.get("/health")
async def health():
    return {"status": "online", "version": "Phase 1 - Gateway"}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)