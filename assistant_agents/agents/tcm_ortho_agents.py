"""
中医骨科康复 — 用户层 Agent (2个)

#29 pain_relief_guide — 疼痛自评引导+科普+功法推荐
#30 rehab_exercise_guide — 康复运动指导+功法套路+打卡

遵循现有 BaseAgent 模式:
  - get_agent(name) 注册
  - process_message(user_id, message, context) 主入口
  - safety_gate 前置检查
  - audit_log 自动记录
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 假设的基础设施导入 (对接现有项目)
# ──────────────────────────────────────────────
try:
    from app.agents.base import BaseAgent, AgentResponse
    from app.agents.registry import register_agent
    from app.services.rag_pipeline import RAGPipeline
    from app.services.llm_service import get_llm_response
    from app.services.audit import log_agent_action
except ImportError:
    # 独立运行时的 stub 定义
    class AgentResponse:
        def __init__(self, content: str = "", metadata: dict = None,
                     handoff: str = "", halt: bool = False):
            self.content = content
            self.metadata = metadata or {}
            self.handoff = handoff
            self.halt = halt

    class BaseAgent:
        name: str = ""
        layer: str = ""
        domain: str = ""
        review_required: bool = False

        async def process_message(self, user_id: int, message: str,
                                  context: dict = None) -> AgentResponse:
            raise NotImplementedError

    def register_agent(cls):
        return cls

    class RAGPipeline:
        async def retrieve(self, query, namespace, top_k=5):
            return []

    async def get_llm_response(prompt, system_prompt="", **kwargs):
        return "（LLM响应占位）"

    async def log_agent_action(agent, user_id, action, detail=""):
        logger.info(f"[AUDIT] {agent}.{action} user={user_id}: {detail}")


from core.safety.safety_rules_ortho import (
    get_ortho_safety_gate, SafetyLevel, SafetyCheckResult
)
from core.engines.pain_engines import PainScaleEngine
from core.agents.prompts_tcm_ortho import (
    PAIN_RELIEF_GUIDE_PROMPT, REHAB_EXERCISE_GUIDE_PROMPT
)


# ================================================================
# #29 pain_relief_guide — 疼痛自评引导
# ================================================================

@register_agent
class PainReliefGuide(BaseAgent):
    """
    用户层 — 疼痛自评引导+中医骨科科普+功法推荐

    职责:
      - 引导用户完成NRS疼痛自评
      - 提供中医骨科健康科普(经络/穴位/体质)
      - 推荐适合的康复功法动作
      - 日常防护建议(体态/工位/睡姿)

    安全:
      - 红旗症状 → 转crisis_responder
      - 边界请求(开处方/诊断) → 免责声明+引导就医
      - 不诊断/不开方/不建议侵入操作
    """
    name = "pain_relief_guide"
    layer = "用户"
    domain = "tcm_ortho"
    review_required = False  # 用户层不需审核

    def __init__(self):
        self.safety_gate = get_ortho_safety_gate()
        self.pain_engine = PainScaleEngine()
        self.rag = RAGPipeline()

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResponse:
        """处理用户消息"""
        context = context or {}
        user_tags = context.get("user_tags", [])
        current_pain_score = context.get("pain_score")

        # ── Step 1: 安全门检查 ──
        safety_result = self.safety_gate.check(
            user_message=message,
            user_tags=user_tags,
            pain_score=current_pain_score,
        )

        if safety_result.level == SafetyLevel.L1_EMERGENCY:
            await log_agent_action(
                self.name, user_id, "SAFETY_L1_EMERGENCY",
                detail=str(safety_result.triggered_rules),
            )
            return AgentResponse(
                content=safety_result.response_template,
                handoff="crisis_responder",
                halt=True,
                metadata={"safety_level": "L1", "rules": safety_result.triggered_rules},
            )

        if safety_result.level == SafetyLevel.L2_REFER:
            await log_agent_action(
                self.name, user_id, "SAFETY_L2_REFER",
                detail=str(safety_result.triggered_rules),
            )
            # L2不中断, 但在回复中嵌入就医建议
            refer_note = safety_result.response_template

        if safety_result.level == SafetyLevel.L3_BOUNDARY:
            await log_agent_action(
                self.name, user_id, "SAFETY_L3_BOUNDARY",
                detail=str(safety_result.triggered_rules),
            )
            return AgentResponse(
                content=safety_result.response_template,
                metadata={"safety_level": "L3", "rules": safety_result.triggered_rules},
            )

        # ── Step 2: 疼痛自评检测 ──
        pain_assess = self._detect_pain_input(message, context)
        if pain_assess:
            await log_agent_action(
                self.name, user_id, "PAIN_ASSESSMENT",
                detail=f"NRS={pain_assess.get('nrs', '?')} loc={pain_assess.get('location', '?')}",
            )

        # ── Step 3: RAG 检索 ──
        rag_docs = await self.rag.retrieve(
            query=message,
            namespace="TCMOrthoKB",
            top_k=3,
        )

        # ── Step 4: 构建 LLM Prompt ──
        system_prompt = PAIN_RELIEF_GUIDE_PROMPT
        user_prompt = self._build_user_prompt(
            message, context, pain_assess, rag_docs, safety_result
        )

        # ── Step 5: LLM 生成回复 ──
        response_text = await get_llm_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1024,
        )

        # ── Step 6: 嵌入L2就医建议 (如有) ──
        if safety_result.level == SafetyLevel.L2_REFER:
            response_text = f"{response_text}\n\n---\n{safety_result.response_template}"

        # ── Step 7: 嵌入L4特殊人群禁忌 (如有) ──
        if safety_result.level == SafetyLevel.L4_SPECIAL_POP:
            response_text = f"{response_text}\n\n---\n{safety_result.response_template}"

        # ── Step 8: 附加免责声明 ──
        response_text += (
            "\n\n---\n⚕️ *以上内容仅为健康科普，不构成医疗建议或诊断。"
            "如有不适请及时就医。*"
        )

        await log_agent_action(self.name, user_id, "RESPONSE_SENT")

        return AgentResponse(
            content=response_text,
            metadata={
                "pain_assess": pain_assess,
                "rag_doc_count": len(rag_docs),
                "safety_level": safety_result.level.name,
            },
        )

    def _detect_pain_input(
        self, message: str, context: dict
    ) -> Optional[dict[str, Any]]:
        """检测并提取用户疼痛描述中的结构化信息"""
        import re

        result = {}

        # 提取NRS评分
        nrs_match = re.search(
            r"(疼痛|痛).{0,10}(\d{1,2})\s*分", message
        )
        if nrs_match:
            score = int(nrs_match.group(2))
            if 0 <= score <= 10:
                result["nrs"] = score

        # 提取部位
        locations = ["颈", "肩", "腰", "背", "膝", "踝", "髋", "手腕",
                      "肘", "足", "脚", "胸椎", "颈椎", "腰椎", "骶髂"]
        found_locs = [loc for loc in locations if loc in message]
        if found_locs:
            result["location"] = "+".join(found_locs)

        # 提取持续时间
        dur_match = re.search(
            r"(\d+)\s*(天|周|月|年)", message
        )
        if dur_match:
            num = int(dur_match.group(1))
            unit = dur_match.group(2)
            days_map = {"天": 1, "周": 7, "月": 30, "年": 365}
            result["duration_days"] = num * days_map.get(unit, 1)

        return result if result else None

    def _build_user_prompt(
        self,
        message: str,
        context: dict,
        pain_assess: Optional[dict],
        rag_docs: list,
        safety_result: SafetyCheckResult,
    ) -> str:
        """构建发送给LLM的完整用户提示"""
        parts = [f"用户消息: {message}"]

        if pain_assess:
            parts.append(f"提取的疼痛信息: {pain_assess}")

        if context.get("history"):
            parts.append(f"对话历史摘要: {context['history'][-3:]}")

        if rag_docs:
            docs_text = "\n".join(
                f"- [{d.get('title', '文档')}]: {d.get('content', '')[:200]}"
                for d in rag_docs[:3]
            )
            parts.append(f"参考知识:\n{docs_text}")

        if safety_result.level == SafetyLevel.L4_SPECIAL_POP:
            parts.append(
                f"⚠️ 特殊人群禁忌需嵌入回复: "
                f"{safety_result.contraindications}"
            )

        parts.append(
            "请根据以上信息回复用户。记住：不诊断、不开方、不建议侵入操作。"
            "如需提供穴位保健建议，请附带'建议在专业指导下操作'。"
        )

        return "\n\n".join(parts)


# ================================================================
# #30 rehab_exercise_guide — 康复运动指导
# ================================================================

@register_agent
class RehabExerciseGuide(BaseAgent):
    """
    用户层 — 康复运动视频/图文指导+功法套路+打卡追踪

    职责:
      - 分部位康复动作指导(图文/视频索引)
      - 传统功法套路选择(八段锦/太极/易筋经/五禽戏)
      - 运动安全边界管理
      - 打卡记录+进度追踪

    安全:
      - 运动中疼痛加剧 → 立即建议停止
      - 术后期 → 严格遵循医嘱约束
      - 急性期 → 仅允许最低强度活动
    """
    name = "rehab_exercise_guide"
    layer = "用户"
    domain = "rehab_move"
    review_required = False

    # 功法推荐库
    GONGFA_LIBRARY = {
        "八段锦": {
            "description": "八段锦是中国传统保健功法，动作柔和缓慢，适合各年龄段",
            "sections": {
                "第一式-两手托天理三焦": {
                    "target": ["全身", "颈椎", "肩周"],
                    "difficulty": "低",
                    "contraindications": ["急性肩关节损伤", "严重颈椎不稳"],
                    "description": "双手交叉上托，拉伸躯干两侧，调理三焦气机",
                },
                "第二式-左右开弓似射雕": {
                    "target": ["肩周", "胸椎", "上肢"],
                    "difficulty": "低",
                    "contraindications": ["急性肩袖损伤"],
                    "description": "左右开弓动作，活动肩部和胸椎",
                },
                "第三式-调理脾胃须单举": {
                    "target": ["腰椎", "脊柱"],
                    "difficulty": "低",
                    "contraindications": ["急性腰椎间盘突出"],
                    "description": "一手上托一手下按，牵拉腰侧",
                },
                "第四式-五劳七伤往后瞧": {
                    "target": ["颈椎", "胸椎"],
                    "difficulty": "低",
                    "contraindications": ["颈椎严重不稳", "椎动脉型颈椎病"],
                    "description": "头部缓慢转向后方，活动颈椎",
                },
                "第五式-摇头摆尾去心火": {
                    "target": ["腰椎", "髋关节", "膝关节"],
                    "difficulty": "中",
                    "contraindications": ["膝关节急性损伤", "严重腰椎不稳"],
                    "description": "马步摇头摆尾，活动腰髋膝",
                },
                "第六式-两手攀足固肾腰": {
                    "target": ["腰椎", "腘绳肌"],
                    "difficulty": "中",
                    "contraindications": ["急性腰椎间盘突出", "腰椎滑脱"],
                    "description": "前屈后伸，牵拉腰部和下肢后侧",
                },
                "第七式-攒拳怒目增气力": {
                    "target": ["上肢", "肩周", "握力"],
                    "difficulty": "低",
                    "contraindications": ["手腕急性损伤"],
                    "description": "马步冲拳，增强上肢力量",
                },
                "第八式-背后七颠百病消": {
                    "target": ["足踝", "平衡", "小腿"],
                    "difficulty": "中",
                    "contraindications": ["踝关节不稳", "严重平衡障碍"],
                    "description": "踮脚落地，振动脊柱",
                },
            },
        },
        "太极拳": {
            "description": "太极拳注重身体协调和平衡，对膝髋关节恢复和平衡训练效果好",
            "sections": {
                "起势": {"target": ["全身", "平衡"], "difficulty": "低",
                          "contraindications": [], "description": "调息定神，膝微屈站立"},
                "云手": {"target": ["腰椎", "肩周", "平衡"], "difficulty": "中",
                          "contraindications": ["严重膝关节损伤"],
                          "description": "重心左右转移，手臂划圆，锻炼核心稳定"},
                "搂膝拗步": {"target": ["膝关节", "髋关节"], "difficulty": "中",
                              "contraindications": ["膝关节急性期"],
                              "description": "弓步行进，注意膝不过脚尖"},
            },
        },
        "易筋经": {
            "description": "易筋经侧重筋骨拉伸，适合关节僵硬和肌肉紧张",
            "sections": {
                "韦驮献杵第一式": {"target": ["肩周", "胸椎"], "difficulty": "低",
                                    "contraindications": [],
                                    "description": "合掌正立，调息开胸"},
                "韦驮献杵第二式": {"target": ["肩周", "上肢"], "difficulty": "低",
                                    "contraindications": [],
                                    "description": "双臂侧平举，拉伸肩部"},
                "韦驮献杵第三式": {"target": ["肩周", "全身"], "difficulty": "中",
                                    "contraindications": ["肩关节脱位史"],
                                    "description": "双臂上举，全身拉伸"},
                "摘星换斗": {"target": ["腰椎", "侧链"], "difficulty": "中",
                              "contraindications": ["急性腰痛"],
                              "description": "单手上托，侧弯拉伸"},
            },
        },
        "五禽戏": {
            "description": "五禽戏模仿虎鹿熊猿鸟五种动物，全身性调理功法",
            "sections": {
                "鹿戏": {"target": ["腰椎", "髋关节"], "difficulty": "中",
                          "contraindications": ["急性腰痛"],
                          "description": "腰部旋转伸展，适合腰部康复维持期"},
                "鸟戏": {"target": ["平衡", "下肢"], "difficulty": "中",
                          "contraindications": ["严重平衡障碍"],
                          "description": "单腿站立展翅，锻炼平衡和下肢力量"},
            },
        },
    }

    def __init__(self):
        self.safety_gate = get_ortho_safety_gate()
        self.rag = RAGPipeline()

    async def process_message(
        self,
        user_id: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentResponse:
        context = context or {}
        user_tags = context.get("user_tags", [])

        # ── Step 1: 安全门 ──
        safety_result = self.safety_gate.check(message, user_tags)

        if safety_result.level == SafetyLevel.L1_EMERGENCY:
            await log_agent_action(self.name, user_id, "SAFETY_L1_EMERGENCY")
            return AgentResponse(
                content=safety_result.response_template,
                handoff="crisis_responder",
                halt=True,
            )

        # ── Step 2: 意图识别 ──
        intent = self._classify_intent(message)

        # ── Step 3: 分流处理 ──
        if intent == "gongfa_recommend":
            response = await self._handle_gongfa_recommend(
                user_id, message, context
            )
        elif intent == "checkin":
            response = await self._handle_checkin(
                user_id, message, context
            )
        elif intent == "progress":
            response = await self._handle_progress_query(
                user_id, context
            )
        else:
            # 通用康复运动指导
            response = await self._handle_general_guidance(
                user_id, message, context, safety_result
            )

        await log_agent_action(self.name, user_id, "RESPONSE_SENT", intent)
        return response

    def _classify_intent(self, message: str) -> str:
        """简单意图分类"""
        if any(kw in message for kw in ["八段锦", "太极", "易筋经", "五禽戏", "功法", "套路"]):
            return "gongfa_recommend"
        if any(kw in message for kw in ["打卡", "完成", "今天做了", "练了"]):
            return "checkin"
        if any(kw in message for kw in ["进度", "坚持了", "多少天", "统计"]):
            return "progress"
        return "general"

    async def _handle_gongfa_recommend(
        self, user_id: int, message: str, context: dict
    ) -> AgentResponse:
        """处理功法推荐请求"""
        # 从上下文获取疼痛部位
        location = context.get("pain_location", "")
        if not location:
            # 从消息中提取
            for loc in ["颈", "肩", "腰", "膝", "踝", "髋"]:
                if loc in message:
                    location = loc
                    break

        recommendations = self._match_gongfa(location, context)

        response_parts = ["根据您的情况，推荐以下功法练习：\n"]
        for rec in recommendations[:3]:
            response_parts.append(
                f"**{rec['gongfa']} — {rec['section']}**\n"
                f"  {rec['description']}\n"
                f"  适合: {', '.join(rec['target'])}\n"
                f"  难度: {rec['difficulty']}\n"
                f"  {'⚠️ 注意: ' + ', '.join(rec['contraindications']) if rec['contraindications'] else '✅ 无特殊禁忌'}\n"
            )

        response_parts.append(
            "\n💡 练习提示：\n"
            "• 每个动作做6-8次，以不加重疼痛为度\n"
            "• 如疼痛超过NRS 3分请立即停止\n"
            "• 建议在空气流通处练习\n"
            "• 练习后可配合穴位按压放松"
        )

        return AgentResponse(
            content="\n".join(response_parts),
            metadata={"intent": "gongfa_recommend", "location": location,
                       "recommendations": [r["section"] for r in recommendations]},
        )

    def _match_gongfa(
        self, location: str, context: dict
    ) -> list[dict]:
        """根据部位匹配功法动作"""
        matches = []
        rehab_stage = context.get("rehab_stage", "恢复期")

        # 急性期只推荐低难度
        max_difficulty = "低" if rehab_stage == "急性期" else "中"

        for gongfa_name, gongfa_data in self.GONGFA_LIBRARY.items():
            for section_name, section in gongfa_data["sections"].items():
                # 部位匹配
                if location and not any(location in t for t in section["target"]):
                    continue
                # 难度筛选
                if max_difficulty == "低" and section["difficulty"] != "低":
                    continue

                matches.append({
                    "gongfa": gongfa_name,
                    "section": section_name,
                    "target": section["target"],
                    "difficulty": section["difficulty"],
                    "contraindications": section["contraindications"],
                    "description": section["description"],
                })

        # 按匹配度排序 (目标部位匹配越多越靠前)
        if location:
            matches.sort(
                key=lambda m: sum(1 for t in m["target"] if location in t),
                reverse=True,
            )
        return matches

    async def _handle_checkin(
        self, user_id: int, message: str, context: dict
    ) -> AgentResponse:
        """处理打卡请求 → 转交 habit_tracker"""
        # 提取运动信息
        exercise_info = {
            "type": "康复运动",
            "source_agent": self.name,
            "pain_feedback": context.get("pain_score"),
        }

        await log_agent_action(
            self.name, user_id, "CHECKIN_HANDOFF", str(exercise_info)
        )

        return AgentResponse(
            content="好的！已记录您今天的康复练习 ✅\n"
                    "继续保持，每天坚持一点点，身体会给您正反馈的。",
            metadata={"intent": "checkin", "exercise_info": exercise_info},
            handoff="habit_tracker",
        )

    async def _handle_progress_query(
        self, user_id: int, context: dict
    ) -> AgentResponse:
        """处理进度查询"""
        # 从context获取打卡统计 (由habit_tracker提供)
        stats = context.get("habit_stats", {})
        streak = stats.get("streak_days", 0)
        total = stats.get("total_days", 0)

        if streak > 0:
            content = (
                f"📊 您的康复运动统计：\n"
                f"  连续打卡: {streak} 天\n"
                f"  累计练习: {total} 天\n\n"
                f"{'🎉 太棒了！坚持就是胜利！' if streak >= 7 else '💪 加油！坚持7天会形成习惯。'}"
            )
        else:
            content = "还没有开始打卡记录。今天就开始您的第一次康复练习吧！"

        return AgentResponse(
            content=content,
            metadata={"intent": "progress", "stats": stats},
        )

    async def _handle_general_guidance(
        self, user_id: int, message: str, context: dict,
        safety_result: SafetyCheckResult,
    ) -> AgentResponse:
        """通用康复运动指导"""
        rag_docs = await self.rag.retrieve(
            query=message, namespace="RehabProtocolKB", top_k=3
        )

        system_prompt = REHAB_EXERCISE_GUIDE_PROMPT
        user_prompt = (
            f"用户消息: {message}\n"
            f"康复阶段: {context.get('rehab_stage', '未知')}\n"
            f"疼痛部位: {context.get('pain_location', '未知')}\n"
            f"当前NRS: {context.get('pain_score', '未知')}\n"
        )
        if rag_docs:
            user_prompt += "\n参考知识:\n" + "\n".join(
                f"- {d.get('content', '')[:200]}" for d in rag_docs[:3]
            )

        response_text = await get_llm_response(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        if safety_result.level == SafetyLevel.L4_SPECIAL_POP:
            response_text += f"\n\n---\n{safety_result.response_template}"

        return AgentResponse(
            content=response_text,
            metadata={"intent": "general", "rag_docs": len(rag_docs)},
        )
