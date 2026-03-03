# -*- coding: utf-8 -*-
"""
P0: AI 评估结果解读 API
POST /api/v1/assessment-assignments/{id}/ai-interpret  — 触发 AI 解读，结果存入 pipeline_result.ai_report
GET  /api/v1/assessment-assignments/{id}/ai-report     — 获取已存储的 AI 解读报告
"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import AssessmentAssignment
from api.dependencies import require_coach_or_admin

router = APIRouter(prefix="/api/v1/assessment-assignments", tags=["assessment-ai"])

# ── 量表中文描述 ──
_SCALE_DESC = {
    "ttm7":     "TTM行为改变阶段（7阶段）",
    "big5":     "大五人格特质（OCEAN）",
    "bpt6":     "BPT行为类型（6维）",
    "capacity": "行为能力评估",
    "spi":      "自我效能感量表（SPI）",
    "hf20":     "高频20题健康筛查",
    "hf50":     "高频50题综合筛查",
}

_STAGE_DESC = {
    "S0": "前意向期 — 学员尚未意识到问题需要改变",
    "S1": "意向期 — 学员已有改变意愿但尚未行动",
    "S2": "准备期 — 学员正在准备行动",
    "S3": "行动期 — 学员已开始行动但不稳定",
    "S4": "维持期 — 行为已坚持超过6个月",
    "S5": "巩固期 — 行为深度融合",
    "S6": "融入期 — 行为完全融入生活方式",
}


def _build_interpretation_prompt(assignment: AssessmentAssignment) -> tuple[str, str]:
    """从评估任务构建 AI 解读 prompt，返回 (system, user)"""
    pr = assignment.pipeline_result or {}
    scales = assignment.scales or []
    if isinstance(scales, list):
        scale_names = "、".join(_SCALE_DESC.get(s, s) for s in scales)
    else:
        scale_names = str(scales)

    stage = pr.get("stage_decision") or pr.get("stage") or "未知"
    stage_desc = _STAGE_DESC.get(stage, stage)
    profile = pr.get("profile") or {}
    interventions = pr.get("interventions") or pr.get("intervention_plan") or []
    baps = pr.get("baps_scores") or pr.get("scores") or {}

    # 精简 interventions 列表 (仅取前3条，防止 prompt 过长)
    int_summary = []
    for iv in (interventions[:3] if isinstance(interventions, list) else []):
        if isinstance(iv, dict):
            int_summary.append(iv.get("name") or iv.get("title") or iv.get("domain") or str(iv)[:30])

    system = """你是一位资深行为健康顾问，负责为教练解读学员的评估结果。
请用中文输出一份专业、温暖、可操作的解读报告。
输出格式必须是合法 JSON，结构如下（不要输出任何 JSON 之外的文字）：
{
  "summary": "2-3句总结，面向教练的视角",
  "stage_interpretation": "对当前行为改变阶段的深度解读（100字以内）",
  "strengths": ["优势1", "优势2"],
  "risks": ["风险1", "风险2"],
  "coach_actions": ["建议行动1", "建议行动2", "建议行动3"],
  "prescription_hint": "针对这位学员的处方方向建议（50字以内）",
  "confidence": 0.85
}"""

    user = f"""请解读以下评估结果：

使用量表：{scale_names}
当前阶段：{stage} — {stage_desc}
行为画像摘要：{json.dumps(profile, ensure_ascii=False)[:300]}
评估得分：{json.dumps(baps, ensure_ascii=False)[:200]}
系统建议干预方向：{', '.join(int_summary) if int_summary else '暂无'}

请生成专业解读报告（JSON格式）。"""
    return system, user


@router.post("/{assignment_id}/ai-interpret")
async def ai_interpret_assessment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """
    P0: 触发 AI 解读评估结果。
    - 解读结果存入 pipeline_result['ai_report']
    - 同时在 coach_push_queue 创建一条 ai_interpretation 待审条目
    """
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="评估任务不存在")
    if assignment.status == "pending":
        raise HTTPException(status_code=400, detail="学员尚未完成评估，无法解读")

    # 已有缓存的 AI 报告则直接返回（避免重复调用 LLM）
    existing = (assignment.pipeline_result or {}).get("ai_report")
    if existing and not isinstance(existing, dict):
        existing = None
    if existing:
        return {"source": "cache", "report": existing, "assignment_id": assignment_id}

    system_prompt, user_prompt = _build_interpretation_prompt(assignment)

    # ── 调用 LLM (Ollama 优先，降级到规则) ──
    report = None
    source = "rules"

    try:
        from core.agents.ollama_client import get_ollama_client
        client = get_ollama_client()
        if client.is_available():
            resp = client.chat(system=system_prompt, user=user_prompt)
            if resp.success and resp.content:
                raw = resp.content.strip()
                # 提取 JSON 块（处理模型可能在 JSON 前后输出多余文字）
                if "```" in raw:
                    raw = raw.split("```")[1].lstrip("json").strip()
                try:
                    report = json.loads(raw)
                    source = "llm"
                    logger.info(f"[assessment_ai] assignment={assignment_id} LLM解读成功 latency={resp.latency_ms}ms")
                except json.JSONDecodeError as e:
                    logger.warning(f"[assessment_ai] JSON解析失败: {e} | raw={raw[:100]}")
    except Exception as e:
        logger.warning(f"[assessment_ai] Ollama调用失败: {e}")

    # ── 降级规则报告 ──
    if report is None:
        pr = assignment.pipeline_result or {}
        stage = pr.get("stage_decision") or pr.get("stage") or "S1"
        report = {
            "summary": f"学员当前处于{_STAGE_DESC.get(stage, stage)}。系统已完成量表评估，建议教练查看详情并制定个性化方案。",
            "stage_interpretation": _STAGE_DESC.get(stage, "行为改变进行中"),
            "strengths": ["完成了评估，说明有改变意愿"],
            "risks": ["需结合面谈进一步了解实际情况"],
            "coach_actions": ["安排一次跟进沟通", "根据阶段推送对应干预内容", "关注学员近期行为打卡情况"],
            "prescription_hint": "建议以小步骤、低难度的微行动为起点",
            "confidence": 0.5,
        }

    report["generated_at"] = datetime.now().isoformat()
    report["source"] = source

    # ── 存储到 pipeline_result ──
    pr = dict(assignment.pipeline_result or {})
    pr["ai_report"] = report
    assignment.pipeline_result = pr
    db.add(assignment)

    # ── 在推送队列创建待审条目（教练需确认后推送给学员） ──
    try:
        from sqlalchemy import text
        summary = report.get("summary", "")[:200]
        hint = report.get("prescription_hint", "")[:100]
        push_content = f"AI解读：{summary}\n处方方向：{hint}"
        db.execute(text("""
            INSERT INTO coach_schema.coach_push_queue
                (coach_id, student_id, source_type, source_id, title, content,
                 priority, status, created_at)
            VALUES
                (:coach_id, :student_id, 'ai_interpretation', :source_id,
                 '评估AI解读报告', :content, 'normal', 'pending', NOW())
        """), {
            "coach_id": assignment.coach_id,
            "student_id": assignment.student_id,
            "source_id": str(assignment_id),
            "content": push_content,
        })
    except Exception as e:
        logger.warning(f"[assessment_ai] 推送队列写入失败 (non-blocking): {e}")

    db.commit()
    return {"source": source, "report": report, "assignment_id": assignment_id}


@router.get("/{assignment_id}/ai-report")
async def get_ai_report(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """P0: 获取已生成的 AI 解读报告（无报告时返回 null）"""
    assignment = db.query(AssessmentAssignment).filter(
        AssessmentAssignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="评估任务不存在")
    report = (assignment.pipeline_result or {}).get("ai_report")
    return {"report": report, "has_report": bool(report), "assignment_id": assignment_id}
