# -*- coding: utf-8 -*-
"""
BAPS API 服务
行健行为教练 - 行为评估系统 REST API

为 Dify 和其他客户端提供评估服务接口
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import uvicorn

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.baps.scoring_engine import BAPSScoringEngine
from core.baps.report_generator import BAPSReportGenerator
from core.baps.questionnaires import (
    BigFiveQuestionnaire,
    BPT6Questionnaire,
    CAPACITYQuestionnaire,
    SPIQuestionnaire
)


# ============ Pydantic Models ============

class BigFiveAnswers(BaseModel):
    """大五人格答案模型"""
    user_id: str = Field(default="anonymous", description="用户ID")
    answers: Dict[str, int] = Field(..., description="答案字典 {题号: 得分(-4到+4)}")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "answers": {
                    "E1": 3, "E2": 2, "E3": -1, "E4": 2, "E5": 1,
                    "E6": 3, "E7": 2, "E8": 2, "E9": 3, "E10": 2
                }
            }
        }


class BPT6Answers(BaseModel):
    """BPT-6答案模型"""
    user_id: str = Field(default="anonymous", description="用户ID")
    answers: Dict[str, int] = Field(..., description="答案字典 {题号: 得分(1-5)}")


class CAPACITYAnswers(BaseModel):
    """CAPACITY答案模型"""
    user_id: str = Field(default="anonymous", description="用户ID")
    answers: Dict[str, int] = Field(..., description="答案字典 {题号: 得分(1-5)}")


class SPIAnswers(BaseModel):
    """SPI答案模型"""
    user_id: str = Field(default="anonymous", description="用户ID")
    answers: Dict[str, int] = Field(..., description="答案字典 {题号: 得分(1-5)}")


class ComprehensiveAnswers(BaseModel):
    """综合评估答案模型"""
    user_id: str = Field(default="anonymous", description="用户ID")
    big_five: Dict[str, int] = Field(..., description="大五人格答案")
    bpt6: Dict[str, int] = Field(..., description="BPT-6答案")
    capacity: Dict[str, int] = Field(..., description="CAPACITY答案")
    spi: Dict[str, int] = Field(..., description="SPI答案")


class QuickAssessmentRequest(BaseModel):
    """快速评估请求"""
    user_id: str = Field(default="anonymous", description="用户ID")
    assessment_type: str = Field(..., description="评估类型: big_five, bpt6, capacity, spi")
    answers: Dict[str, int] = Field(..., description="答案字典")


# ============ FastAPI App ============

app = FastAPI(
    title="行健行为教练 BAPS API",
    description="行为评估系统与处方（Behavior Assessment & Prescription System）RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 全局实例
scoring_engine = BAPSScoringEngine()
report_generator = BAPSReportGenerator()

# 问卷实例
questionnaires = {
    "big_five": BigFiveQuestionnaire(),
    "bpt6": BPT6Questionnaire(),
    "capacity": CAPACITYQuestionnaire(),
    "spi": SPIQuestionnaire()
}


# ============ 基础端点 ============

@app.get("/", tags=["基础"])
async def root():
    """API根路径"""
    return {
        "service": "行健行为教练 BAPS API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "questionnaires": "/questionnaires",
            "assess": "/assess/{type}",
            "comprehensive": "/assess/comprehensive",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============ 问卷管理端点 ============

@app.get("/questionnaires", tags=["问卷管理"])
async def list_questionnaires():
    """获取所有可用问卷列表"""
    result = []
    for key, q in questionnaires.items():
        result.append({
            "id": q.id,
            "name": q.name,
            "description": q.description,
            "total_items": q.total_items,
            "estimated_minutes": q.estimated_minutes,
            "endpoint": f"/questionnaires/{key}"
        })
    return {"questionnaires": result}


@app.get("/questionnaires/{questionnaire_type}", tags=["问卷管理"])
async def get_questionnaire(questionnaire_type: str):
    """获取指定问卷的详细信息和题目"""
    if questionnaire_type not in questionnaires:
        raise HTTPException(status_code=404, detail=f"问卷类型 '{questionnaire_type}' 不存在")

    q = questionnaires[questionnaire_type]
    return {
        "id": q.id,
        "name": q.name,
        "description": q.description,
        "total_items": q.total_items,
        "estimated_minutes": q.estimated_minutes,
        "scale": {
            "type": q.scale.type,
            "range": list(q.scale.range),
            "labels": q.scale.labels
        },
        "dimensions": {
            k: {"name": v.name, "items": v.items}
            for k, v in q.dimensions.items()
        },
        "items": q.get_items()
    }


@app.get("/questionnaires/{questionnaire_type}/items", tags=["问卷管理"])
async def get_questionnaire_items(
    questionnaire_type: str,
    dimension: Optional[str] = Query(None, description="筛选特定维度")
):
    """获取问卷题目列表"""
    if questionnaire_type not in questionnaires:
        raise HTTPException(status_code=404, detail=f"问卷类型 '{questionnaire_type}' 不存在")

    q = questionnaires[questionnaire_type]
    items = q.get_items()

    if dimension:
        items = [item for item in items if item["dimension"] == dimension]

    return {
        "questionnaire": q.name,
        "total_items": len(items),
        "items": items
    }


# ============ 评估端点 ============

@app.post("/assess/big_five", tags=["评估"])
async def assess_big_five(request: BigFiveAnswers):
    """
    大五人格评估

    提交50题答案，返回五维度得分和人格画像
    """
    try:
        result = scoring_engine.score_big_five(request.answers, request.user_id)
        report = report_generator.generate_big_five_report(result)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/bpt6", tags=["评估"])
async def assess_bpt6(request: BPT6Answers):
    """
    BPT-6行为模式分型评估

    提交18题答案，返回行为类型分类和干预建议
    """
    try:
        result = scoring_engine.score_bpt6(request.answers, request.user_id)
        report = report_generator.generate_bpt6_report(result)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/capacity", tags=["评估"])
async def assess_capacity(request: CAPACITYAnswers):
    """
    CAPACITY改变潜力诊断

    提交32题答案，返回8维度改变潜力评估
    """
    try:
        result = scoring_engine.score_capacity(request.answers, request.user_id)
        report = report_generator.generate_capacity_report(result)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/spi", tags=["评估"])
async def assess_spi(request: SPIAnswers):
    """
    SPI成功可能性评估

    提交50题答案，返回SPI指数和成功预测
    """
    try:
        result = scoring_engine.score_spi(request.answers, request.user_id)
        report = report_generator.generate_spi_report(result)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/comprehensive", tags=["评估"])
async def assess_comprehensive(request: ComprehensiveAnswers):
    """
    综合评估

    提交四份问卷全部答案，返回综合评估报告
    """
    try:
        report = report_generator.generate_comprehensive_report(
            big_five_answers=request.big_five,
            bpt6_answers=request.bpt6,
            capacity_answers=request.capacity,
            spi_answers=request.spi,
            user_id=request.user_id
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/comprehensive/markdown", tags=["评估"], response_class=PlainTextResponse)
async def assess_comprehensive_markdown(request: ComprehensiveAnswers):
    """
    综合评估（Markdown格式）

    返回Markdown格式的综合评估报告
    """
    try:
        report = report_generator.generate_comprehensive_report(
            big_five_answers=request.big_five,
            bpt6_answers=request.bpt6,
            capacity_answers=request.capacity,
            spi_answers=request.spi,
            user_id=request.user_id
        )
        markdown = report_generator.generate_markdown_report(report)
        return markdown
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assess/quick", tags=["评估"])
async def quick_assess(request: QuickAssessmentRequest):
    """
    快速评估

    通用评估接口，根据assessment_type自动路由
    """
    type_map = {
        "big_five": (scoring_engine.score_big_five, report_generator.generate_big_five_report),
        "bpt6": (scoring_engine.score_bpt6, report_generator.generate_bpt6_report),
        "capacity": (scoring_engine.score_capacity, report_generator.generate_capacity_report),
        "spi": (scoring_engine.score_spi, report_generator.generate_spi_report)
    }

    if request.assessment_type not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"无效的评估类型: {request.assessment_type}. 可选: {list(type_map.keys())}"
        )

    try:
        score_func, report_func = type_map[request.assessment_type]
        result = score_func(request.answers, request.user_id)
        report = report_func(result)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Dify集成端点 ============

@app.get("/openapi-tools.json", tags=["Dify集成"])
async def get_dify_tools_schema():
    """
    获取Dify自定义工具Schema

    在Dify中创建自定义工具时，导入此Schema
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "行健行为教练 BAPS",
            "version": "1.0.0",
            "description": "行为评估系统与处方 - 多维度行为评估服务"
        },
        "servers": [
            {"url": "http://localhost:8001", "description": "本地服务"}
        ],
        "paths": {
            "/assess/quick": {
                "post": {
                    "operationId": "behaviorAssessment",
                    "summary": "行为评估",
                    "description": "对用户进行行为评估，支持大五人格、行为分型、改变潜力、成功可能性四种评估",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["assessment_type", "answers"],
                                    "properties": {
                                        "user_id": {
                                            "type": "string",
                                            "description": "用户ID"
                                        },
                                        "assessment_type": {
                                            "type": "string",
                                            "enum": ["big_five", "bpt6", "capacity", "spi"],
                                            "description": "评估类型"
                                        },
                                        "answers": {
                                            "type": "object",
                                            "description": "答案字典 {题号: 得分}"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "评估报告",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/questionnaires/{type}": {
                "get": {
                    "operationId": "getQuestionnaire",
                    "summary": "获取问卷",
                    "description": "获取指定类型的问卷题目",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["big_five", "bpt6", "capacity", "spi"]
                            },
                            "description": "问卷类型"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "问卷详情",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


# ============ 模拟测试数据端点 ============

@app.get("/test/sample-answers/{questionnaire_type}", tags=["测试"])
async def get_sample_answers(questionnaire_type: str):
    """获取问卷的示例答案（用于测试）"""
    if questionnaire_type not in questionnaires:
        raise HTTPException(status_code=404, detail=f"问卷类型 '{questionnaire_type}' 不存在")

    q = questionnaires[questionnaire_type]
    items = q.get_items()

    # 生成模拟答案
    if questionnaire_type == "big_five":
        # 大五人格: -4 到 +4
        import random
        answers = {item["id"]: random.randint(-2, 3) for item in items}
    else:
        # 其他问卷: 1 到 5
        import random
        answers = {item["id"]: random.randint(2, 5) for item in items}

    return {
        "questionnaire": q.name,
        "sample_answers": answers,
        "note": "这是随机生成的示例答案，仅供测试使用"
    }


@app.post("/test/full-assessment", tags=["测试"])
async def test_full_assessment():
    """
    完整评估测试

    使用模拟数据进行四份问卷的完整评估
    """
    import random

    # 生成模拟答案
    big_five_answers = {f"E{i}": random.randint(-2, 3) for i in range(1, 11)}
    big_five_answers.update({f"N{i}": random.randint(-1, 3) for i in range(1, 11)})
    big_five_answers.update({f"C{i}": random.randint(0, 3) for i in range(1, 11)})
    big_five_answers.update({f"A{i}": random.randint(-1, 3) for i in range(1, 11)})
    big_five_answers.update({f"O{i}": random.randint(-1, 4) for i in range(1, 11)})

    bpt6_answers = {f"BPT{i}": random.randint(2, 5) for i in range(1, 19)}

    capacity_answers = {f"CAP{i}": random.randint(2, 5) for i in range(1, 33)}

    spi_answers = {f"SPI{i}": random.randint(2, 5) for i in range(1, 51)}

    # 执行评估
    report = report_generator.generate_comprehensive_report(
        big_five_answers=big_five_answers,
        bpt6_answers=bpt6_answers,
        capacity_answers=capacity_answers,
        spi_answers=spi_answers,
        user_id="test_user"
    )

    return report


# ============ 启动入口 ============

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  行健行为教练 BAPS API 服务")
    print("=" * 60)
    print("\n启动服务...")
    print("  API 文档: http://localhost:8001/docs")
    print("  Dify 工具 Schema: http://localhost:8001/openapi-tools.json")
    print("\n可用评估类型:")
    print("  - big_five: 大五人格测评 (50题)")
    print("  - bpt6: 行为模式分型 (18题)")
    print("  - capacity: 改变潜力诊断 (32题)")
    print("  - spi: 成功可能性评估 (50题)")
    print("\n")

    uvicorn.run(
        "baps_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
