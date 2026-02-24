"""
IncentiveEngine 治理积分集成
契约来源: Sheet⑦ 积分契约 · 治理新增 10 种 + Agent 生态 5 种
集成方式: 注册治理积分事件到现有 IncentiveEngine

依赖: 现有 IncentiveEngine (12 pytest cases pass) + AntiCheatEngine (25 cases pass)
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


# ──────────────────────────────────────────
# 1. 治理积分事件注册器
# ──────────────────────────────────────────

class GovernancePointsRegistrar:
    """
    将治理 10 种 + Agent 5 种积分事件注册到 IncentiveEngine。
    
    调用方式 (应用启动时):
        registrar = GovernancePointsRegistrar(incentive_engine)
        registrar.register_all()
    """
    
    def __init__(self, incentive_engine, config_path: str = None):
        self.engine = incentive_engine
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "point_events_governance.json"
        )
        self._config = None
    
    def load_config(self) -> dict:
        """加载治理积分配置文件"""
        if self._config is None:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        return self._config
    
    def register_all(self) -> dict:
        """
        注册全部治理积分事件。
        
        Returns:
            {"registered": 15, "skipped": 0, "errors": []}
        """
        config = self.load_config()
        result = {"registered": 0, "skipped": 0, "errors": []}
        
        # 注册治理事件
        for event in config.get("governance_events", []):
            self._register_event(event, result)
        
        # 注册 Agent 生态事件
        for event in config.get("agent_ecosystem_events", []):
            self._register_event(event, result)
        
        return result
    
    def _register_event(self, event: dict, result: dict) -> None:
        """注册单个积分事件"""
        event_type = event["event_type"]
        
        try:
            # 检查是否已注册 (幂等)
            if hasattr(self.engine, 'is_event_registered'):
                if self.engine.is_event_registered(event_type):
                    result["skipped"] += 1
                    return
            
            # 注册到 IncentiveEngine
            self.engine.register_event(
                event_type=event_type,
                points=event["points"],
                point_type=event["point_type"],
                daily_cap=event.get("daily_cap"),
                min_role=event.get("min_role", "grower"),
                min_role_level=event.get("min_role_level", 2),
                anti_cheat_strategies=event.get("anti_cheat", []),
                audit_required=event.get("audit_required", False),
                metadata={
                    "event_id": event.get("event_id"),
                    "display_name": event.get("display_name"),
                    "trigger_source": event.get("trigger_source"),
                    "trigger_action": event.get("trigger_action"),
                    "contract_ref": event.get("contract_ref"),
                },
            )
            result["registered"] += 1
            
        except Exception as e:
            result["errors"].append({
                "event_type": event_type,
                "error": str(e),
            })


# ──────────────────────────────────────────
# 2. 治理积分触发服务
# ──────────────────────────────────────────

class GovernancePointsTrigger:
    """
    治理积分触发服务。
    各业务模块通过此服务触发治理相关的积分事件。
    
    用法:
        trigger = GovernancePointsTrigger(incentive_engine, audit_logger)
        await trigger.on_ethics_test_passed(user_id=123, test_score=90)
    """
    
    def __init__(self, incentive_engine, audit_logger=None, anti_cheat_engine=None):
        self.engine = incentive_engine
        self.audit = audit_logger
        self.anti_cheat = anti_cheat_engine
    
    async def _award_points(
        self,
        user_id: int,
        event_type: str,
        context: Dict[str, Any] = None,
    ) -> dict:
        """
        通用积分授予流程:
        1. 防刷检查 (如已集成)
        2. 角色权限校验
        3. 每日上限检查
        4. 积分写入
        5. 审计记录
        """
        context = context or {}
        
        # 防刷检查
        if self.anti_cheat:
            cheat_result = await self.anti_cheat.check(
                user_id=user_id,
                event_type=event_type,
                context=context,
            )
            if not cheat_result.get("allowed", True):
                return {
                    "success": False,
                    "reason": "anti_cheat_blocked",
                    "strategy": cheat_result.get("blocked_by"),
                }
        
        # I-08: 角色差异化积分 — 读取 role_points_override
        try:
            import json as _json
            import os as _os
            _pe_path = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                "configs", "point_events.json",
            )
            with open(_pe_path, "r", encoding="utf-8") as _f:
                _pe_cfg = _json.load(_f)
            # 查找当前 event_type 的 role_points_override
            _override = None
            for section in _pe_cfg.get("events", {}).values():
                if isinstance(section, list):
                    for ev in section:
                        if ev.get("action") == event_type and "role_points_override" in ev:
                            _override = ev["role_points_override"]
                            break
            if _override and "user_role" in context:
                role_amount = _override.get(context["user_role"])
                if role_amount is not None:
                    context["amount_override"] = role_amount
        except Exception:
            pass

        # 调用 IncentiveEngine 核心计分
        result = await self.engine.award_points(
            user_id=user_id,
            event_type=event_type,
            context=context,
        )
        
        # 审计记录 (治理积分均需审计)
        if self.audit and result.get("success"):
            await self.audit.log(
                user_id=user_id,
                action=f"points_awarded_{event_type}",
                resource_type="points",
                details={
                    "event_type": event_type,
                    "points": result.get("points_awarded", 0),
                    "point_type": result.get("point_type"),
                    "context": context,
                },
            )
        
        return result
    
    # ── 具体触发方法 (10种治理事件) ──
    
    async def on_ethics_test_passed(
        self, user_id: int, test_score: int, test_id: str = None
    ) -> dict:
        """GOV-01: 完成伦理情景测试 → +50 成长分"""
        return await self._award_points(user_id, "ethics_scenario_test", {
            "test_score": test_score,
            "test_id": test_id,
        })
    
    async def on_competency_self_assessment(
        self, user_id: int, domain_scores: Dict[str, int] = None
    ) -> dict:
        """GOV-02: 完成能力自评问卷 → +30 成长分"""
        return await self._award_points(user_id, "competency_self_assessment", {
            "domain_scores": domain_scores,
        })
    
    async def on_ethics_declaration_signed(
        self, user_id: int, declaration_version: str = None
    ) -> dict:
        """GOV-03: 伦理宣言签署/更新 → +30 贡献分"""
        return await self._award_points(user_id, "ethics_declaration_signed", {
            "declaration_version": declaration_version,
        })
    
    async def on_conflict_disclosure(self, user_id: int) -> dict:
        """GOV-04: 利益冲突披露更新 → +20 贡献分"""
        return await self._award_points(user_id, "conflict_disclosure_update")
    
    async def on_alert_timely_response(
        self, user_id: int, alert_id: str, response_minutes: int
    ) -> dict:
        """GOV-05: 告警及时处置(≤4h) → +15 贡献分"""
        if response_minutes > 240:  # 4小时 = 240分钟
            return {"success": False, "reason": "response_time_exceeded"}
        return await self._award_points(user_id, "alert_timely_response", {
            "alert_id": alert_id,
            "response_minutes": response_minutes,
        })
    
    async def on_student_message_reply(
        self, user_id: int, message_id: str
    ) -> dict:
        """GOV-06: 学员消息及时回复 → +10 贡献分"""
        return await self._award_points(user_id, "student_message_reply", {
            "message_id": message_id,
        })
    
    async def on_supervision_completed(
        self, user_id: int, session_id: str, user_role: str = ""
    ) -> dict:
        """GOV-07: 督导会议完成 → 影响力分 (I-08: supervisor=80, promoter=50, master=50)"""
        return await self._award_points(user_id, "supervision_meeting", {
            "session_id": session_id,
            "user_role": user_role,
        })
    
    async def on_agent_feedback_reply(
        self, user_id: int, feedback_id: str
    ) -> dict:
        """GOV-08: Agent反馈回复 → +10 贡献分"""
        return await self._award_points(user_id, "agent_feedback_reply", {
            "feedback_id": feedback_id,
        })
    
    async def on_knowledge_shared(
        self, user_id: int, knowledge_id: str
    ) -> dict:
        """GOV-09: 知识库共享贡献 → +30 影响力分"""
        return await self._award_points(user_id, "knowledge_shared", {
            "knowledge_id": knowledge_id,
        })
    
    async def on_certificate_renewed(self, user_id: int) -> dict:
        """GOV-10: 证书定期更新确认 → +20 成长分"""
        return await self._award_points(user_id, "certificate_renewal_confirmed")


# ──────────────────────────────────────────
# 3. 防刷策略 × 治理积分映射
# ──────────────────────────────────────────

GOVERNANCE_ANTI_CHEAT_MAPPING = {
    # event_type → 适用的防刷策略 (Sheet⑦ AS-01 ~ AS-06)
    "ethics_scenario_test":        ["AS-01", "AS-05"],          # 每日上限 + 成长轨校验
    "competency_self_assessment":  ["AS-01", "AS-05"],          # 每日上限 + 成长轨校验
    "ethics_declaration_signed":   ["AS-05"],                   # 成长轨校验
    "conflict_disclosure_update":  ["AS-01"],                   # 每日上限
    "alert_timely_response":       ["AS-01", "AS-04"],          # 每日上限 + 交叉验证
    "student_message_reply":       ["AS-01", "AS-03", "AS-06"], # 每日上限 + 时间衰减 + 异常检测
    "supervision_session_completed": ["AS-04", "AS-05"],        # 交叉验证 + 成长轨校验
    "agent_feedback_reply":        ["AS-01", "AS-02"],          # 每日上限 + 质量加权
    "knowledge_shared":            ["AS-01", "AS-02", "AS-04"], # 每日上限 + 质量加权 + 交叉验证
    "certificate_renewal_confirmed": ["AS-01"],                 # 每日上限
}

# 防刷策略说明 (Sheet⑦ 防刷策略矩阵)
ANTI_CHEAT_STRATEGIES = {
    "AS-01": {
        "name": "每日上限",
        "description": "同一积分行为设定每日获取上限",
        "user_message": "今日该项积分已达上限,明天继续",
    },
    "AS-02": {
        "name": "质量加权",
        "description": "高质量×2倍, 低质量×0.5倍",
        "user_message": None,  # 不展示倍率,只展示最终积分
    },
    "AS-03": {
        "name": "时间衰减",
        "description": "同一行为重复>5次后积分递减",
        "decay_curve": {
            "6-10": 0.8,
            "11-20": 0.5,
            "21+": 0.2,
        },
        "user_message": "尝试不同行为获得更多积分",
    },
    "AS-04": {
        "name": "交叉验证",
        "description": "涉及他人的积分需对方确认",
        "user_message": "等待对方确认中",
    },
    "AS-05": {
        "name": "成长轨校验",
        "description": "积分再多, 成长轨不过=不晋级",
        "user_message": None,  # 话术见④晋级契约
    },
    "AS-06": {
        "name": "异常检测",
        "description": "1小时内同一行为>20次 → 标记审查",
        "user_message": None,  # 不提示用户(避免对抗)
    },
}
