"""
教练层剩余13个Agent — 领域专家 + 督导 + 质控

领域专家 (9): metabolic, cardiac_rehab, adherence, nutrition, exercise,
              sleep, tcm, mental, chronic_manager
康复教育 (2): rehab_expert, health_educator
督导质控 (2): supervisor_reviewer, quality_auditor

共享架构: 专业知识规则 + LLM增强 + review_required=True
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from ..base import BaseProfessionalAgent

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# 领域专家基类
# ═══════════════════════════════════════════════════════════

class DomainExpertAgent(BaseProfessionalAgent):
    """领域专家基类 — 接收评估数据→生成领域建议→标记教练审核"""

    AGENT_NAME = "domain_expert"
    AGENT_DOMAIN = "general"
    EXPERT_PROMPT = "你是健康领域专家。"
    FOCUS_AREAS: List[str] = []
    RED_FLAGS: List[str] = []

    @property
    def name(self) -> str:
        return self.AGENT_NAME

    @property
    def domain(self) -> str:
        return self.AGENT_DOMAIN

    def _get_llm(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        profile = kwargs.get("user_profile", {})
        assessment = kwargs.get("assessment_data", {})

        # 红旗检测
        red_flags = self._check_red_flags(message, profile, assessment)

        # 领域分析
        analysis = self._domain_analysis(profile, assessment)

        # LLM增强
        enhanced = await self._llm_enhance(message, analysis, red_flags)

        return self._format_response(
            content=enhanced,
            domain=self.AGENT_DOMAIN,
            red_flags=red_flags,
            focus_areas=self.FOCUS_AREAS,
            analysis=analysis,
            review_required=True,
            confidence=0.7 if not red_flags else 0.5,
        )

    def _check_red_flags(self, message: str, profile: dict, assessment: dict) -> List[str]:
        flags = []
        for flag in self.RED_FLAGS:
            if flag.lower() in message.lower():
                flags.append(flag)
        return flags

    def _domain_analysis(self, profile: dict, assessment: dict) -> dict:
        return {
            "stage": profile.get("ttm_stage", "unknown"),
            "focus_areas": self.FOCUS_AREAS,
            "domain": self.AGENT_DOMAIN,
        }

    async def _llm_enhance(self, message: str, analysis: dict, red_flags: list) -> str:
        llm = self._get_llm()
        if not llm:
            areas = ", ".join(self.FOCUS_AREAS[:3])
            flags = f"\n⚠️ 注意: {', '.join(red_flags)}" if red_flags else ""
            return f"【{self.AGENT_DOMAIN}领域分析】\n关注方向: {areas}{flags}\n\n（LLM不可用，请教练自行判断）"

        flag_note = f"\n红旗提示: {', '.join(red_flags)}。需特别关注。" if red_flags else ""
        prompt = f"""{self.EXPERT_PROMPT}
{flag_note}
分析数据: {str(analysis)[:300]}
教练问题: {message}

请给出2-3条专业建议（给教练看，不是给用户的）。"""

        try:
            resp = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            return resp if isinstance(resp, str) else getattr(resp, 'content', str(resp))
        except Exception:
            return f"【{self.AGENT_DOMAIN}】LLM不可用，请教练根据评估数据自行判断。"


# ═══════════════════════════════════════════════════════════
# 9个领域专家实例
# ═══════════════════════════════════════════════════════════

class MetabolicExpertAgent(DomainExpertAgent):
    AGENT_NAME = "metabolic_expert"
    AGENT_DOMAIN = "metabolic"
    EXPERT_PROMPT = "你是代谢健康专家。专长：血糖管理、血脂调控、体重管理、代谢综合征。为教练提供代谢领域的专业建议。"
    FOCUS_AREAS = ["血糖控制", "血脂调控", "体重管理", "胰岛素抵抗", "代谢综合征"]
    RED_FLAGS = ["低血糖", "酮症", "HbA1c>9", "BMI>35", "急性高血糖"]


class CardiacRehabAgent(DomainExpertAgent):
    AGENT_NAME = "cardiac_rehab"
    AGENT_DOMAIN = "cardiac"
    EXPERT_PROMPT = "你是心脏康复专家。专长：心血管康复评估、运动耐量评估、心脏事件后康复。为教练提供心脏康复领域建议。"
    FOCUS_AREAS = ["运动耐量评估", "心血管风险分层", "康复运动处方", "二级预防"]
    RED_FLAGS = ["胸痛", "呼吸困难", "心律不齐", "血压>180", "心脏事件<3月"]


class AdherenceMonitorAgent(DomainExpertAgent):
    AGENT_NAME = "adherence_monitor"
    AGENT_DOMAIN = "adherence"
    EXPERT_PROMPT = "你是依从性监测专家。专长：用药依从性、行为依从性、干预方案执行率分析。帮教练识别依从性下降信号。"
    FOCUS_AREAS = ["用药依从性", "行为方案执行率", "复诊依从", "自我监测频率"]
    RED_FLAGS = ["连续3天未打卡", "用药中断", "失访", "拒绝评估"]


class NutritionExpertAgent(DomainExpertAgent):
    AGENT_NAME = "nutrition_expert"
    AGENT_DOMAIN = "nutrition_pro"
    EXPERT_PROMPT = "你是临床营养专家。专长：疾病营养支持、特殊人群膳食、营养评估解读。为教练提供专业营养建议（需审核）。"
    FOCUS_AREAS = ["热量计算", "宏量营养素配比", "微量营养素评估", "特殊饮食管理"]
    RED_FLAGS = ["BMI<18.5", "白蛋白<35", "严重偏食", "进食障碍征兆"]


class ExerciseExpertAgent(DomainExpertAgent):
    AGENT_NAME = "exercise_expert"
    AGENT_DOMAIN = "exercise_pro"
    EXPERT_PROMPT = "你是运动医学专家。专长：运动处方设计、运动风险评估、慢性病运动管理。为教练提供专业运动建议（需审核）。"
    FOCUS_AREAS = ["运动处方", "运动强度分层", "运动禁忌评估", "功能性训练"]
    RED_FLAGS = ["运动中胸痛", "关节急性损伤", "平衡障碍", "未控制高血压运动"]


class SleepExpertAgent(DomainExpertAgent):
    AGENT_NAME = "sleep_expert"
    AGENT_DOMAIN = "sleep_pro"
    EXPERT_PROMPT = "你是睡眠医学专家。专长：睡眠障碍评估、CBT-I指导、睡眠卫生教育。为教练提供专业睡眠建议（需审核）。"
    FOCUS_AREAS = ["失眠严重度评估", "睡眠日记分析", "CBT-I策略", "睡眠呼吸评估"]
    RED_FLAGS = ["嗜睡评分>10", "AHI>15", "安眠药依赖", "梦游/夜惊"]


class TcmExpertAgent(DomainExpertAgent):
    AGENT_NAME = "tcm_expert"
    AGENT_DOMAIN = "tcm_pro"
    EXPERT_PROMPT = "你是中医专家。专长：体质辨识、辨证论治方向、中西医结合建议。为教练提供中医视角的专业建议（需审核，不开方）。"
    FOCUS_AREAS = ["体质辨识", "证型分析", "中西医结合思路", "经络调理方向"]
    RED_FLAGS = ["药物相互作用", "孕妇禁忌", "过敏体质", "急性期"]


class MentalExpertAgent(DomainExpertAgent):
    AGENT_NAME = "mental_expert"
    AGENT_DOMAIN = "mental"
    EXPERT_PROMPT = "你是心理健康专家。专长：心理评估解读、干预策略建议、危机识别。为教练提供心理层面的专业建议（需审核）。"
    FOCUS_AREAS = ["心理评估解读", "情绪调节策略", "认知重构方向", "社会支持评估"]
    RED_FLAGS = ["自杀意念", "严重焦虑", "创伤反应", "精神病性症状", "物质滥用"]


class ChronicManagerAgent(DomainExpertAgent):
    AGENT_NAME = "chronic_manager"
    AGENT_DOMAIN = "chronic"
    EXPERT_PROMPT = "你是慢性病管理专家。专长：多病共管、长期随访策略、慢病控制指标追踪。为教练提供慢病综合管理建议。"
    FOCUS_AREAS = ["多病共管策略", "指标趋势分析", "并发症预防", "长期随访计划"]
    RED_FLAGS = ["指标急剧恶化", "新发并发症", "多药联用>5种", "频繁住院"]


# ═══════════════════════════════════════════════════════════
# rehab_expert — 康复专家
# ═══════════════════════════════════════════════════════════

class RehabExpertAgent(DomainExpertAgent):
    AGENT_NAME = "rehab_expert"
    AGENT_DOMAIN = "rehabilitation"
    EXPERT_PROMPT = "你是康复医学专家。专长：功能评估、康复方案设计、ADL能力评估。为教练提供康复方向建议（需审核）。"
    FOCUS_AREAS = ["功能障碍评估", "康复目标设定", "辅助器具建议", "家庭康复方案"]
    RED_FLAGS = ["急性期", "神经功能恶化", "跌倒风险高", "疼痛评分>7"]


# ═══════════════════════════════════════════════════════════
# health_educator — 健康教育师
# ═══════════════════════════════════════════════════════════

class HealthEducatorAgent(DomainExpertAgent):
    AGENT_NAME = "health_educator"
    AGENT_DOMAIN = "education"
    EXPERT_PROMPT = "你是健康教育专家。专长：健康素养评估、教育方案设计、行为改变教育策略。帮教练设计适合用户水平的教育内容。"
    FOCUS_AREAS = ["健康素养评估", "教育内容适配", "学习风格匹配", "教育效果评估"]
    RED_FLAGS = ["低健康素养", "语言障碍", "认知障碍", "文化敏感话题"]


# ═══════════════════════════════════════════════════════════
# supervisor_reviewer — 督导审核
# ═══════════════════════════════════════════════════════════

class SupervisorReviewerAgent(BaseProfessionalAgent):
    """督导审核 — 审核教练的干预方案质量"""

    @property
    def name(self) -> str:
        return "supervisor_reviewer"

    @property
    def domain(self) -> str:
        return "supervision"

    def _get_llm(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        review_data = kwargs.get("review_data", {})
        rx_to_review = kwargs.get("rx_data", {})

        # 审核维度
        checklist = self._review_checklist(rx_to_review)

        # LLM审核
        llm = self._get_llm()
        if llm:
            prompt = f"""作为督导审核专家，请审核以下干预方案：

方案内容: {str(rx_to_review)[:500]}
教练备注: {message}

审核维度:
1. 安全性 — 是否有潜在风险
2. 适切性 — 是否匹配用户阶段和特征
3. 可行性 — 用户是否能执行
4. 完整性 — 是否覆盖关键领域
5. 伦理性 — 是否尊重用户自主权

请给出审核意见和建议修改。"""

            try:
                resp = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
                text = resp if isinstance(resp, str) else getattr(resp, 'content', str(resp))
                return self._format_response(
                    content=text,
                    checklist=checklist,
                    review_required=False,  # 督导的意见不需要再审
                    confidence=0.8,
                )
            except Exception:
                pass

        return self._format_response(
            content=f"自动审核:\n" + "\n".join(f"  {'✅' if v else '⚠️'} {k}" for k, v in checklist.items()),
            checklist=checklist,
            review_required=False,
            confidence=0.5,
        )

    def _review_checklist(self, rx: dict) -> dict:
        strategies = rx.get("strategies", [])
        return {
            "安全性:无高风险策略": not any("高强度" in s or "断食" in s for s in strategies),
            "适切性:策略数量合理(≤5)": len(strategies) <= 5,
            "完整性:包含策略内容": len(strategies) > 0,
            "可行性:有时间框架": bool(rx.get("duration_weeks")),
            "伦理性:非强制性语气": not any("必须" in s or "强制" in s for s in strategies),
        }


# ═══════════════════════════════════════════════════════════
# quality_auditor — 质量审计
# ═══════════════════════════════════════════════════════════

class QualityAuditorAgent(BaseProfessionalAgent):
    """质量审计 — 系统级质量监控"""

    @property
    def name(self) -> str:
        return "quality_auditor"

    @property
    def domain(self) -> str:
        return "quality"

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(content="安全拦截", safety_intercepted=True)

        db = kwargs.get("db")
        action = kwargs.get("action", "dashboard")

        if action == "dashboard":
            return await self._quality_dashboard(db)
        elif action == "audit_agent":
            return await self._audit_agent(kwargs.get("agent_id"), db)
        else:
            return await self._quality_dashboard(db)

    async def _quality_dashboard(self, db) -> dict:
        if not db:
            return self._format_response(content="质控仪表盘需要数据库连接。", confidence=0.3)

        try:
            from sqlalchemy import text as sa_text
            # 24h内Agent活动统计
            row = await db.execute(
                sa_text("""
                    SELECT
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as recent_24h,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending_reviews,
                        COUNT(*) FILTER (WHERE priority = 0) as critical_items
                    FROM coach_schema.coach_review_items
                """)
            )
            stats = row.mappings().first()

            return self._format_response(
                content=f"质控仪表盘: 24h活动{stats['recent_24h']}件, 待审{stats['pending_reviews']}件, 紧急{stats['critical_items']}件",
                dashboard={
                    "recent_24h": stats["recent_24h"],
                    "pending_reviews": stats["pending_reviews"],
                    "critical_items": stats["critical_items"],
                },
                review_required=False,
                confidence=0.9,
            )
        except Exception as e:
            return self._format_response(content=f"质控数据获取失败: {str(e)[:100]}", confidence=0.3)

    async def _audit_agent(self, agent_id, db) -> dict:
        if not db or not agent_id:
            return self._format_response(content="需要agent_id和数据库连接。", confidence=0.3)

        try:
            from sqlalchemy import text as sa_text
            row = await db.execute(
                sa_text("""
                    SELECT COUNT(*) as total,
                           AVG(CASE WHEN status = 'approved' THEN 1.0 ELSE 0.0 END) as approval_rate
                    FROM coach_schema.coach_review_items
                    WHERE content LIKE :pattern
                """),
                {"pattern": f"%{agent_id}%"}
            )
            stats = row.mappings().first()
            return self._format_response(
                content=f"Agent [{agent_id}] 审计: {stats['total']}条记录, 通过率{(stats['approval_rate'] or 0)*100:.0f}%",
                agent_audit={"total": stats["total"], "approval_rate": stats["approval_rate"]},
                review_required=False,
            )
        except Exception as e:
            return self._format_response(content=f"审计失败: {str(e)[:100]}", confidence=0.3)
