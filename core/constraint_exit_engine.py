"""
约束与退出机制
契约来源: Sheet⑪ 第9节「约束与退出机制」

违规分级 (5类):
  1. 轻微投诉    — -20积分+警告, 30天无复发自动恢复
  2. 越权首次    — -100积分+强制补训, 补训通过恢复
  3. 越权二次    — -300积分+降级1-2级+6月观察期
  4. 伦理红线    — 积分清零+永久取消 (唯一不可恢复)
  5. KPI持续不达标 — 不扣积分, 暂停分配+督导辅导

保护机制:
  - 新晋级3月保护期 (首次免罚)
  - 降级有明确恢复路径
  - 自愿退出积分冻结12月可恢复

退出类型:
  - 自愿退出: 积分保留(冻结), 12月内可申请恢复
  - 强制退出: 伦理红线, 不可恢复
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta, date
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════
# 0. 违规分级枚举
# ══════════════════════════════════════════

class ViolationType(str, Enum):
    MINOR_COMPLAINT = "minor_complaint"            # 轻微投诉
    FIRST_OVERREACH = "first_overreach"             # 越权首次
    SECOND_OVERREACH = "second_overreach"           # 越权二次
    ETHICS_REDLINE = "ethics_redline"               # 伦理红线
    KPI_UNDERPERFORM = "kpi_underperform"           # KPI持续不达标


class ExitType(str, Enum):
    VOLUNTARY = "voluntary"       # 自愿退出
    FORCED = "forced"             # 强制退出 (伦理红线)
    SUSPENDED = "suspended"       # 暂停 (观察期)


class RecoveryStatus(str, Enum):
    ELIGIBLE = "eligible"         # 可恢复
    IN_PROGRESS = "in_progress"   # 恢复中
    COMPLETED = "completed"       # 已恢复
    INELIGIBLE = "ineligible"     # 不可恢复


# ══════════════════════════════════════════
# 1. 违规处理配置 (Sheet⑪ 第9节)
# ══════════════════════════════════════════

@dataclass
class ViolationConfig:
    type: ViolationType
    name: str
    points_penalty: int            # 积分扣罚 (负数)
    additional_action: str         # 附加处罚
    applicable_levels: str         # 适用层级
    recovery_path: str             # 恢复路径
    appeal_window_days: int        # 申诉窗口
    reviewer: str                  # 审核人
    detection_method: str          # 检测方式
    protection_exempt: bool        # 保护期是否豁免


VIOLATION_CONFIGS: Dict[ViolationType, ViolationConfig] = {
    ViolationType.MINOR_COMPLAINT: ViolationConfig(
        type=ViolationType.MINOR_COMPLAINT,
        name="轻微投诉",
        points_penalty=-20,
        additional_action="口头警告",
        applicable_levels="L1-L5",
        recovery_path="自动恢复(30天无复发)",
        appeal_window_days=7,
        reviewer="直属督导",
        detection_method="投诉系统",
        protection_exempt=True,  # 保护期内首次免罚
    ),
    ViolationType.FIRST_OVERREACH: ViolationConfig(
        type=ViolationType.FIRST_OVERREACH,
        name="越权行为(首次)",
        points_penalty=-100,
        additional_action="强制补训(指定模块)",
        applicable_levels="L1-L5",
        recovery_path="补训通过后恢复正常",
        appeal_window_days=7,
        reviewer="督导+Admin",
        detection_method="权限日志+行为审计",
        protection_exempt=True,
    ),
    ViolationType.SECOND_OVERREACH: ViolationConfig(
        type=ViolationType.SECOND_OVERREACH,
        name="越权行为(二次)",
        points_penalty=-300,
        additional_action="降级1-2级+6个月观察期",
        applicable_levels="L2-L5",
        recovery_path="观察期满+能力复评通过→可恢复",
        appeal_window_days=7,
        reviewer="伦理委员会",
        detection_method="权限日志+违规记录",
        protection_exempt=False,
    ),
    ViolationType.ETHICS_REDLINE: ViolationConfig(
        type=ViolationType.ETHICS_REDLINE,
        name="伦理红线违规",
        points_penalty=-999999,  # 积分清零 (特殊处理)
        additional_action="一票否决·永久取消资格(不可恢复)",
        applicable_levels="L1-L5",
        recovery_path="无恢复路径(唯一不可恢复)",
        appeal_window_days=0,  # 无申诉
        reviewer="伦理委员会全票",
        detection_method="伦理审查+投诉",
        protection_exempt=False,  # 保护期不豁免
    ),
    ViolationType.KPI_UNDERPERFORM: ViolationConfig(
        type=ViolationType.KPI_UNDERPERFORM,
        name="KPI持续不达标(非恶意)",
        points_penalty=0,  # 不扣积分
        additional_action="暂停新学员分配+安排督导辅导",
        applicable_levels="L3-L5",
        recovery_path="复评通过→恢复; 未通过→降级",
        appeal_window_days=0,
        reviewer="督导",
        detection_method="KPI红绿灯",
        protection_exempt=True,  # 保护期内不触发
    ),
}


@dataclass
class ViolationRecord:
    """违规记录"""
    record_id: str
    user_id: int
    violation_type: ViolationType
    description: str
    points_deducted: int
    action_taken: str
    occurred_at: str
    reviewer: str
    appeal_status: str = "none"   # none | pending | approved | rejected
    appeal_deadline: str = ""
    resolved: bool = False
    resolved_at: str = ""


@dataclass
class ProtectionStatus:
    """保护期状态"""
    user_id: int
    is_protected: bool
    protection_start: str = ""
    protection_end: str = ""
    days_remaining: int = 0
    last_promotion_date: str = ""


@dataclass
class ExitRecord:
    """退出记录"""
    user_id: int
    exit_type: ExitType
    exit_date: str
    previous_level: str
    points_frozen: int
    recovery_eligible: bool
    recovery_deadline: str = ""    # 12月内可恢复
    reason: str = ""


# ══════════════════════════════════════════
# 2. 约束引擎
# ══════════════════════════════════════════

class ConstraintEngine:
    """
    约束与退出引擎。
    
    调用方式:
      engine = ConstraintEngine()
      result = await engine.process_violation(user_id, violation_type, ...)
      exit_result = await engine.process_exit(user_id, exit_type, ...)
    """
    
    PROTECTION_PERIOD_DAYS = 90    # 新晋级3月保护期
    VOLUNTARY_EXIT_RECOVERY_MONTHS = 12  # 自愿退出12月内可恢复
    OBSERVATION_PERIOD_DAYS = 180  # 观察期6个月
    
    def __init__(self, points_service=None, audit_logger=None, notification_service=None):
        self.points = points_service
        self.audit = audit_logger
        self.notifications = notification_service
        # 内存存储 (生产用DB)
        self._violation_records: List[ViolationRecord] = []
        self._exit_records: List[ExitRecord] = []
        self._protection_cache: Dict[int, ProtectionStatus] = {}
    
    # ── 2.1 保护期检查 ──
    
    def check_protection(self, user_id: int, promotion_date: str = "") -> ProtectionStatus:
        """检查用户是否在新晋级3月保护期内"""
        if user_id in self._protection_cache:
            status = self._protection_cache[user_id]
            if status.is_protected:
                # 检查是否过期
                end = datetime.fromisoformat(status.protection_end)
                if datetime.now(timezone.utc) > end:
                    status.is_protected = False
                    status.days_remaining = 0
                else:
                    status.days_remaining = (end - datetime.now(timezone.utc)).days
            return status
        
        # 默认: 无保护
        return ProtectionStatus(user_id=user_id, is_protected=False)
    
    def activate_protection(self, user_id: int, promotion_date: str) -> ProtectionStatus:
        """激活新晋级保护期"""
        start = datetime.fromisoformat(promotion_date)
        end = start + timedelta(days=self.PROTECTION_PERIOD_DAYS)
        
        status = ProtectionStatus(
            user_id=user_id,
            is_protected=True,
            protection_start=start.isoformat(),
            protection_end=end.isoformat(),
            days_remaining=(end - datetime.now(timezone.utc)).days,
            last_promotion_date=promotion_date,
        )
        self._protection_cache[user_id] = status
        return status
    
    # ── 2.2 违规处理 ──
    
    async def process_violation(
        self,
        user_id: int,
        violation_type: ViolationType,
        description: str = "",
        current_level: str = "L1",
        current_points: int = 0,
    ) -> Dict[str, Any]:
        """
        处理违规行为。
        
        Returns: {violation_record, points_deducted, action_taken, protection_applied}
        """
        config = VIOLATION_CONFIGS[violation_type]
        
        # 保护期检查
        protection = self.check_protection(user_id)
        protection_applied = False
        
        if protection.is_protected and config.protection_exempt:
            # 检查是否首次违规
            past_violations = [
                v for v in self._violation_records
                if v.user_id == user_id and not v.resolved
            ]
            if len(past_violations) == 0:
                protection_applied = True
        
        # 计算实际扣分
        if protection_applied:
            actual_penalty = 0
            action = "保护期内首次违规: 免罚, 仅警告"
        elif violation_type == ViolationType.ETHICS_REDLINE:
            actual_penalty = current_points  # 清零
            action = config.additional_action
        else:
            actual_penalty = abs(config.points_penalty)
            action = config.additional_action
        
        # 创建违规记录
        record_id = f"VIO-{user_id}-{len(self._violation_records) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()
        
        appeal_deadline = ""
        if config.appeal_window_days > 0:
            deadline = datetime.now(timezone.utc) + timedelta(days=config.appeal_window_days)
            appeal_deadline = deadline.isoformat()
        
        record = ViolationRecord(
            record_id=record_id,
            user_id=user_id,
            violation_type=violation_type,
            description=description,
            points_deducted=actual_penalty,
            action_taken=action,
            occurred_at=now,
            reviewer=config.reviewer,
            appeal_deadline=appeal_deadline,
        )
        self._violation_records.append(record)
        
        # 降级处理
        demotion_info = None
        if violation_type == ViolationType.SECOND_OVERREACH:
            demotion_info = self._calculate_demotion(current_level, levels_down=1)
        elif violation_type == ViolationType.ETHICS_REDLINE:
            demotion_info = {"new_level": "TERMINATED", "observation_days": 0, "recoverable": False}
        
        # 退出处理
        exit_info = None
        if violation_type == ViolationType.ETHICS_REDLINE:
            exit_info = await self.process_exit(
                user_id, ExitType.FORCED, current_level, current_points,
                reason="伦理红线违规: 永久取消",
            )
        
        return {
            "record": {
                "record_id": record.record_id,
                "violation_type": violation_type.value,
                "name": config.name,
                "points_deducted": actual_penalty,
                "action_taken": action,
                "appeal_deadline": appeal_deadline,
                "reviewer": config.reviewer,
            },
            "protection_applied": protection_applied,
            "demotion": demotion_info,
            "exit": exit_info,
            "recovery_path": config.recovery_path,
        }
    
    def _calculate_demotion(self, current_level: str, levels_down: int = 1) -> Dict:
        """计算降级"""
        level_order = ["L0", "L1", "L2", "L3", "L4", "L5"]
        try:
            idx = level_order.index(current_level)
            new_idx = max(0, idx - levels_down)
            return {
                "new_level": level_order[new_idx],
                "levels_dropped": idx - new_idx,
                "observation_days": self.OBSERVATION_PERIOD_DAYS,
                "recoverable": True,
                "recovery_condition": "观察期满+能力复评通过",
            }
        except ValueError:
            return {"new_level": current_level, "levels_dropped": 0, "observation_days": 0, "recoverable": True}
    
    # ── 2.3 退出处理 ──
    
    async def process_exit(
        self,
        user_id: int,
        exit_type: ExitType,
        current_level: str,
        current_points: int,
        reason: str = "",
    ) -> Dict[str, Any]:
        """处理退出"""
        now = datetime.now(timezone.utc)
        
        recovery_eligible = exit_type != ExitType.FORCED
        recovery_deadline = ""
        if recovery_eligible:
            deadline = now + timedelta(days=self.VOLUNTARY_EXIT_RECOVERY_MONTHS * 30)
            recovery_deadline = deadline.isoformat()
        
        record = ExitRecord(
            user_id=user_id,
            exit_type=exit_type,
            exit_date=now.isoformat(),
            previous_level=current_level,
            points_frozen=current_points if exit_type == ExitType.VOLUNTARY else 0,
            recovery_eligible=recovery_eligible,
            recovery_deadline=recovery_deadline,
            reason=reason,
        )
        self._exit_records.append(record)
        
        return {
            "exit_type": exit_type.value,
            "previous_level": current_level,
            "points_status": "frozen" if exit_type == ExitType.VOLUNTARY else "cleared",
            "points_frozen": record.points_frozen,
            "recovery_eligible": recovery_eligible,
            "recovery_deadline": recovery_deadline,
            "message": self._get_exit_message(exit_type),
        }
    
    def _get_exit_message(self, exit_type: ExitType) -> str:
        messages = {
            ExitType.VOLUNTARY: "您的积分已冻结保留, 12个月内可申请恢复。感谢您的参与, 期待再次相遇。",
            ExitType.FORCED: "因伦理红线违规, 资格已永久取消。",
            ExitType.SUSPENDED: "您已进入观察期, 观察期满后可申请能力复评恢复。",
        }
        return messages.get(exit_type, "")
    
    # ── 2.4 恢复流程 ──
    
    async def request_recovery(
        self, user_id: int
    ) -> Dict[str, Any]:
        """申请恢复"""
        # 查找退出记录
        exit_record = next(
            (r for r in reversed(self._exit_records) if r.user_id == user_id),
            None,
        )
        
        if not exit_record:
            return {"eligible": False, "reason": "未找到退出记录"}
        
        if not exit_record.recovery_eligible:
            return {"eligible": False, "reason": "伦理红线违规, 不可恢复"}
        
        # 检查恢复期限
        if exit_record.recovery_deadline:
            deadline = datetime.fromisoformat(exit_record.recovery_deadline)
            if datetime.now(timezone.utc) > deadline:
                return {"eligible": False, "reason": "恢复期限已过 (12个月)"}
        
        return {
            "eligible": True,
            "previous_level": exit_record.previous_level,
            "points_frozen": exit_record.points_frozen,
            "recovery_steps": [
                "提交恢复申请",
                "完成能力复评",
                "通过督导面谈",
                "恢复至原级别 (积分解冻)",
            ],
            "deadline": exit_record.recovery_deadline,
        }
    
    # ── 2.5 查询接口 ──
    
    def get_violation_history(self, user_id: int) -> List[Dict]:
        """查询违规历史"""
        records = [v for v in self._violation_records if v.user_id == user_id]
        return [
            {
                "record_id": v.record_id,
                "type": v.violation_type.value,
                "description": v.description,
                "points_deducted": v.points_deducted,
                "action": v.action_taken,
                "occurred_at": v.occurred_at,
                "appeal_status": v.appeal_status,
                "resolved": v.resolved,
            }
            for v in records
        ]
    
    def get_exit_status(self, user_id: int) -> Optional[Dict]:
        """查询退出状态"""
        record = next(
            (r for r in reversed(self._exit_records) if r.user_id == user_id),
            None,
        )
        if not record:
            return None
        return {
            "exit_type": record.exit_type.value,
            "exit_date": record.exit_date,
            "previous_level": record.previous_level,
            "points_frozen": record.points_frozen,
            "recovery_eligible": record.recovery_eligible,
            "recovery_deadline": record.recovery_deadline,
        }
