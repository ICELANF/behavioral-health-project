"""
四同道者追踪服务
契约来源: Sheet④ 四同道者裂变 + Sheet⑪ 六级四同道者

核心规则: 每级晋级需培养4名同道者, 其中:
  - ≥2人达到进度目标
  - ≥1人达到高级目标
  
数据来源: PeerTracking 表 (Migration 036 已建) + CompanionRelation
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class PeerStatus:
    """单个同道者状态"""
    peer_user_id: int
    peer_name: str
    current_stage: str           # S0-S5
    current_level: str           # L0-L5
    met_progress_target: bool    # 是否达到进度目标
    met_advanced_target: bool    # 是否达到高级目标
    relationship_start: str      # 关系开始时间
    last_interaction: str        # 最后互动时间
    interaction_count: int       # 互动次数
    companion_hours: float       # 陪伴时长 (小时)


@dataclass
class PeerValidationResult:
    """同道者验证结果"""
    passed: bool
    total_count: int
    total_required: int
    progressed_count: int
    progressed_required: int
    advanced_count: int
    advanced_required: int
    peers: List[PeerStatus]
    gaps: List[str]


class PeerTrackingService:
    """
    四同道者追踪服务。
    
    与 DualTrackChecker 集成:
        checker = DualTrackChecker(peer_service=PeerTrackingService(db))
    
    追踪维度 (每级不同):
      L0→L1: 邀请4名观察员, ≥2人开始行为尝试
      L1→L2: 带领4名成长者, ≥2人完成S0-S3, ≥1人达S4
      L2→L3: 培养4名分享者, ≥2人通过考核, ≥1人具备教练潜力
      L3→L4: 培养4名教练, ≥2人独立执业, ≥1人项目负责人
      L4→L5: 培养4名促进师, ≥2人区域标杆, ≥1人大师潜力
    """
    
    # 各层级同道者进度判定规则
    LEVEL_PEER_RULES = {
        "L0_TO_L1": {
            "peer_level": "L0",
            "progress_check": lambda stage, level: stage in ("S1", "S2", "S3", "S4", "S5"),
            "progress_desc": "开始行为尝试",
            "advanced_check": lambda stage, level: False,  # L0→L1 无高级要求
            "advanced_desc": "",
        },
        "L1_TO_L2": {
            "peer_level": "L1",
            "progress_check": lambda stage, level: stage in ("S3", "S4", "S5"),
            "progress_desc": "完成S0-S3",
            "advanced_check": lambda stage, level: stage in ("S4", "S5"),
            "advanced_desc": "达到S4内化",
        },
        "L2_TO_L3": {
            "peer_level": "L2",
            "progress_check": lambda stage, level: level in ("L2", "L3", "L4", "L5"),
            "progress_desc": "通过分享者考核",
            "advanced_check": lambda stage, level: level in ("L3", "L4", "L5"),
            "advanced_desc": "具备教练潜力",
        },
        "L3_TO_L4": {
            "peer_level": "L3",
            "progress_check": lambda stage, level: True,  # 独立执业需额外数据
            "progress_desc": "独立执业",
            "advanced_check": lambda stage, level: False,  # 项目负责人需额外数据
            "advanced_desc": "成为项目负责人",
        },
        "L4_TO_L5": {
            "peer_level": "L4",
            "progress_check": lambda stage, level: True,
            "progress_desc": "成为区域/行业标杆",
            "advanced_check": lambda stage, level: False,
            "advanced_desc": "具备大师潜力",
        },
    }
    
    def __init__(self, db_session_factory=None):
        self.db_factory = db_session_factory
    
    async def validate_peers(
        self,
        user_id: int,
        peer_req,  # PeerRequirement from dual_track_engine
        promotion_key: str = "",
    ) -> dict:
        """
        验证同道者是否满足晋级要求。
        
        Returns:
            {
                "passed": bool,
                "total_count": int,
                "total_required": int,
                "progressed_count": int,
                "progressed_required": int,
                "advanced_count": int,
                "advanced_required": int,
                "peers": [...],
                "gaps": [...]
            }
        """
        # 获取该用户的同道者列表
        peers = await self._get_user_peers(user_id, promotion_key)
        
        rules = self.LEVEL_PEER_RULES.get(promotion_key, {})
        
        # 统计
        total = len(peers)
        progressed = sum(
            1 for p in peers
            if rules.get("progress_check", lambda s, l: False)(p.current_stage, p.current_level)
        )
        advanced = sum(
            1 for p in peers
            if rules.get("advanced_check", lambda s, l: False)(p.current_stage, p.current_level)
        )
        
        # 判定
        total_ok = total >= peer_req.total_required
        progress_ok = progressed >= peer_req.min_progressed
        advanced_ok = advanced >= peer_req.min_advanced if peer_req.min_advanced > 0 else True
        passed = total_ok and progress_ok and advanced_ok
        
        # 差距
        gaps = []
        if not total_ok:
            gaps.append(f"同道者总数差 {peer_req.total_required - total} 人")
        if not progress_ok:
            gaps.append(
                f"达到「{rules.get('progress_desc', '进度目标')}」的差 "
                f"{peer_req.min_progressed - progressed} 人"
            )
        if not advanced_ok:
            gaps.append(
                f"达到「{rules.get('advanced_desc', '高级目标')}」的差 "
                f"{peer_req.min_advanced - advanced} 人"
            )
        
        return {
            "passed": passed,
            "total_count": total,
            "total_required": peer_req.total_required,
            "progressed_count": progressed,
            "progressed_required": peer_req.min_progressed,
            "advanced_count": advanced,
            "advanced_required": peer_req.min_advanced,
            "peers": [self._peer_to_dict(p) for p in peers],
            "gaps": gaps,
        }
    
    async def get_peer_dashboard(self, user_id: int, current_level: str) -> Dict:
        """获取同道者仪表盘数据 (前端展示用)"""
        promotion_key = {
            "L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
            "L3": "L3_TO_L4", "L4": "L4_TO_L5",
        }.get(current_level)
        
        if not promotion_key:
            return {"peers": [], "summary": "已达最高等级"}
        
        peers = await self._get_user_peers(user_id, promotion_key)
        rules = self.LEVEL_PEER_RULES.get(promotion_key, {})
        
        return {
            "promotion_key": promotion_key,
            "peers": [self._peer_to_dict(p) for p in peers],
            "total": len(peers),
            "required": 4,
            "progress_target": rules.get("progress_desc", ""),
            "advanced_target": rules.get("advanced_desc", ""),
        }
    
    async def _get_user_peers(
        self, user_id: int, promotion_key: str
    ) -> List[PeerStatus]:
        """从数据库获取同道者列表"""
        if self.db_factory:
            try:
                async with self.db_factory() as session:
                    from sqlalchemy import select, and_
                    from app.models.peer_tracking import PeerTracking
                    
                    stmt = select(PeerTracking).where(
                        PeerTracking.mentor_user_id == user_id,
                        PeerTracking.is_active == True,
                    )
                    result = await session.execute(stmt)
                    rows = result.scalars().all()
                    
                    return [
                        PeerStatus(
                            peer_user_id=r.peer_user_id,
                            peer_name=r.peer_display_name or f"用户{r.peer_user_id}",
                            current_stage=r.peer_current_stage or "S0",
                            current_level=r.peer_current_level or "L0",
                            met_progress_target=r.met_progress_target or False,
                            met_advanced_target=r.met_advanced_target or False,
                            relationship_start=r.created_at.isoformat() if r.created_at else "",
                            last_interaction=r.last_interaction_at.isoformat() if r.last_interaction_at else "",
                            interaction_count=r.interaction_count or 0,
                            companion_hours=float(r.companion_hours or 0),
                        )
                        for r in rows
                    ]
            except Exception:
                pass
        return []
    
    def _peer_to_dict(self, p: PeerStatus) -> dict:
        return {
            "peer_user_id": p.peer_user_id,
            "peer_name": p.peer_name,
            "current_stage": p.current_stage,
            "current_level": p.current_level,
            "met_progress": p.met_progress_target,
            "met_advanced": p.met_advanced_target,
            "companion_hours": p.companion_hours,
            "interaction_count": p.interaction_count,
        }
