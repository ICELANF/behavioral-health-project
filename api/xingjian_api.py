# -*- coding: utf-8 -*-
"""
行健Agent API 服务

为 Dify 提供 REST API 接口，实现无缝对接
支持：专家咨询、效能限幅、健康数据看板
"""

import os
import sys
import uvicorn
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.dependencies import get_current_user
from core.models import User
from agents.orchestrator import AgentOrchestrator
from agents.octopus_engine import OctopusClampingEngine, get_clamping_engine

# ============ FastAPI 应用 ============
app = FastAPI(
    title="行健行为教练 API",
    description="为 Dify 提供健康咨询、效能限幅、数据分析等能力",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 跨域配置 (允许 Dify 访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
orchestrator: Optional[AgentOrchestrator] = None


# ============ 数据模型 ============

class ChatRequest(BaseModel):
    """健康咨询请求"""
    message: str = Field(..., description="用户问题", example="我最近失眠怎么办？")
    expert_id: Optional[str] = Field(None, description="指定专家ID（可选）", example="mental_health")


class ChatResponse(BaseModel):
    """健康咨询响应"""
    response: str = Field(..., description="专家回复")
    primary_expert: str = Field(..., description="主要处理专家")
    consulted_experts: List[str] = Field(default=[], description="咨询的其他专家")
    confidence: float = Field(..., description="路由置信度")


class ClampingRequest(BaseModel):
    """效能限幅请求"""
    user_id: str = Field(..., description="用户ID", example="user_001")
    efficacy_score: int = Field(..., ge=0, le=100, description="效能分(0-100)", example=35)
    tasks: List[Dict[str, Any]] = Field(..., description="待限幅任务列表")
    wearable_data: Optional[Dict[str, Any]] = Field(None, description="穿戴设备数据", example={"hr": 85})


class ClampingResponse(BaseModel):
    """效能限幅响应"""
    clamped_tasks: List[Dict[str, Any]] = Field(..., description="限幅后的任务")
    final_efficacy: int = Field(..., description="最终效能分")
    clamping_level: str = Field(..., description="限幅等级")
    reasoning_path: List[Dict[str, Any]] = Field(..., description="推理路径")


class ExpertInfo(BaseModel):
    """专家信息"""
    id: str
    name: str
    description: str


# ============ 生命周期事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 Orchestrator"""
    global orchestrator
    print("\n正在初始化行健行为教练...")
    try:
        orchestrator = AgentOrchestrator("config.yaml")
        print("行健行为教练 初始化完成\n")
    except Exception as e:
        print(f"警告: Agent 初始化失败 - {e}")
        print("部分功能可能不可用\n")


# ============ API 端点 ============

@app.get("/", tags=["基础"])
async def root():
    """API 根路径"""
    return {
        "service": "行健行为教练 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "orchestrator": orchestrator is not None,
        "experts_count": len(orchestrator.registry) if orchestrator else 0
    }


@app.get("/experts", response_model=List[ExpertInfo], tags=["专家"])
async def list_experts(current_user: User = Depends(get_current_user)):
    """获取可用专家列表"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    return orchestrator.get_available_experts()


@app.post("/chat", response_model=ChatResponse, tags=["咨询"])
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    健康咨询接口

    - 自动路由到合适的专家
    - 支持多专家协作
    - 可指定专家直接对话
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    try:
        if request.expert_id:
            # 直接与指定专家对话
            response_text = orchestrator.direct_chat(request.expert_id, request.message)
            expert_config = orchestrator.registry.get_config(request.expert_id)
            return ChatResponse(
                response=response_text,
                primary_expert=expert_config.name if expert_config else request.expert_id,
                consulted_experts=[],
                confidence=1.0
            )
        else:
            # 自动路由
            result = orchestrator.process_query(request.message)
            return ChatResponse(
                response=result.final_response,
                primary_expert=result.primary_expert,
                consulted_experts=result.consulted_experts,
                confidence=result.routing_confidence
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clamping", response_model=ClampingResponse, tags=["八爪鱼引擎"])
async def octopus_clamping(request: ClampingRequest, current_user: User = Depends(get_current_user)):
    """
    八爪鱼效能限幅接口

    根据用户效能分和穿戴数据，动态裁剪任务难度和数量
    """
    try:
        engine = get_clamping_engine(request.user_id, request.efficacy_score)
        result = engine.octopus_clamping(request.tasks, request.wearable_data)

        return ClampingResponse(
            clamped_tasks=result.clamped_tasks,
            final_efficacy=result.final_efficacy,
            clamping_level=result.clamping_level,
            reasoning_path=result.reasoning_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset", tags=["管理"])
async def reset_conversation(current_user: User = Depends(get_current_user)):
    """重置所有对话历史"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    orchestrator.reset_all()
    return {"status": "ok", "message": "所有对话历史已重置"}


# ============ Dify 工具 Schema (OpenAPI 3.0) ============

@app.get("/openapi-tools.json", tags=["Dify集成"])
async def get_dify_tools_schema(current_user: User = Depends(get_current_user)):
    """
    获取 Dify 自定义工具 Schema

    在 Dify 中创建自定义工具时，导入此 Schema
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "行健行为教练",
            "version": "1.0.0",
            "description": "行健行为教练 - 多专家协作健康咨询系统"
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "本地服务"}
        ],
        "paths": {
            "/chat": {
                "post": {
                    "operationId": "healthConsultation",
                    "summary": "健康咨询",
                    "description": "向行健健康专家团咨询健康问题，支持心理、营养、运动、中医四大专家",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["message"],
                                    "properties": {
                                        "message": {
                                            "type": "string",
                                            "description": "用户的健康问题"
                                        },
                                        "expert_id": {
                                            "type": "string",
                                            "description": "可选，指定专家ID: mental_health/nutrition/sports_rehab/tcm_wellness"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "咨询成功",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {"type": "string"},
                                            "primary_expert": {"type": "string"},
                                            "consulted_experts": {"type": "array", "items": {"type": "string"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/clamping": {
                "post": {
                    "operationId": "efficacyClamping",
                    "summary": "效能限幅",
                    "description": "根据用户效能感分值和穿戴数据，动态调整任务难度和数量",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["user_id", "efficacy_score", "tasks"],
                                    "properties": {
                                        "user_id": {"type": "string"},
                                        "efficacy_score": {"type": "integer", "minimum": 0, "maximum": 100},
                                        "tasks": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "content": {"type": "string"},
                                                    "difficulty": {"type": "integer", "minimum": 1, "maximum": 5}
                                                }
                                            }
                                        },
                                        "wearable_data": {
                                            "type": "object",
                                            "properties": {
                                                "hr": {"type": "integer", "description": "心率"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "限幅成功"
                        }
                    }
                }
            }
        }
    }


# ============ 启动入口 ============

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  行健行为教练 API 服务")
    print("=" * 60)
    print("\n启动服务...")
    print("  API 文档: http://localhost:8000/docs")
    print("  Dify 工具 Schema: http://localhost:8000/openapi-tools.json")
    print("\n")

    uvicorn.run(
        "xingjian_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
