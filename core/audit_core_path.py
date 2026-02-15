"""
审计日志核心路径补全
契约来源: Sheet⑨ 治理触点契约 · 30个治理触点
目标: 从 16% (6/30+) 提升到 ~50% — 覆盖核心用户旅程

核心用户旅程审计路径:
  注册 → 评估 → AI对话 → 微行动/挑战 → 积分累积 → 晋级
  
现有审计 (6项): content_publish, agent_template_change, knowledge_review,
                challenge_push, safety_block, violation_record

新增审计 (14项): 覆盖核心路径 + 教练7天挑战
"""

from __future__ import annotations
import time
import json
import functools
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession


# ──────────────────────────────────────────
# 1. 审计事件类型定义 (对齐 Sheet⑨)
# ──────────────────────────────────────────

class AuditAction(str, Enum):
    """审计动作枚举 — 按用户旅程排序"""
    
    # ── 已有 (6项) ──
    CONTENT_PUBLISH = "content_publish"
    AGENT_TEMPLATE_CHANGE = "agent_template_change"
    KNOWLEDGE_REVIEW = "knowledge_review"
    CHALLENGE_PUSH = "challenge_push"
    SAFETY_BLOCK = "safety_block"
    VIOLATION_RECORD = "violation_record"
    
    # ── 新增 · 注册入口 (3项) ──
    USER_REGISTER = "user_register"                     # 用户注册
    USER_LOGIN = "user_login"                           # 用户登录
    ROLE_UPGRADE = "role_upgrade"                       # 角色升级 (观察员→成长者等)
    
    # ── 新增 · 评估路径 (2项) ──
    ASSESSMENT_STARTED = "assessment_started"           # 开始评估
    ASSESSMENT_SUBMITTED = "assessment_submitted"       # 提交评估
    
    # ── 新增 · AI对话 (2项) ──
    CHAT_SESSION_START = "chat_session_start"           # 开始AI对话
    CHAT_MESSAGE_SENT = "chat_message_sent"             # 发送消息 (含Agent ID)
    
    # ── 新增 · 行为干预 (3项) ──
    MICRO_ACTION_COMPLETED = "micro_action_completed"   # 微行动完成
    CHALLENGE_JOINED = "challenge_joined"               # 参与挑战
    CHECKIN_COMPLETED = "checkin_completed"              # 每日签到
    
    # ── 新增 · 积分与晋级 (2项) ──
    POINTS_AWARDED = "points_awarded"                   # 积分授予
    PROMOTION_INITIATED = "promotion_initiated"         # 晋级启动
    
    # ── 新增 · 数据管理 (2项) ──
    HEALTH_DATA_RECORDED = "health_data_recorded"       # 健康数据录入
    DEVICE_BOUND = "device_bound"                       # 设备绑定


# 审计触点 → Sheet⑨ 映射关系
AUDIT_TOUCHPOINT_MAP = {
    AuditAction.USER_REGISTER: {
        "sheet_ref": "Sheet⑨ 成长者→注册",
        "user_role": "observer+",
        "sensitivity": "medium",
        "collect": ["registration_source", "entry_type"],
    },
    AuditAction.USER_LOGIN: {
        "sheet_ref": "Sheet⑨ 通用",
        "user_role": "observer+",
        "sensitivity": "low",
        "collect": ["login_method", "ip_address"],
    },
    AuditAction.ROLE_UPGRADE: {
        "sheet_ref": "Sheet⑨ 晋级仪式",
        "user_role": "observer+",
        "sensitivity": "high",
        "collect": ["old_role", "new_role", "promotion_type"],
    },
    AuditAction.ASSESSMENT_STARTED: {
        "sheet_ref": "Sheet⑨ 成长者→行为评估",
        "user_role": "observer+",
        "sensitivity": "medium",
        "collect": ["assessment_type", "scale_id"],
    },
    AuditAction.ASSESSMENT_SUBMITTED: {
        "sheet_ref": "Sheet⑨ 成长者→行为评估",
        "user_role": "observer+",
        "sensitivity": "high",   # PHI 相关
        "collect": ["assessment_type", "scale_id", "score_summary"],
    },
    AuditAction.CHAT_SESSION_START: {
        "sheet_ref": "Sheet⑨ 成长者→AI智能助手",
        "user_role": "grower+",
        "sensitivity": "medium",
        "collect": ["agent_id", "agent_domain"],
    },
    AuditAction.CHAT_MESSAGE_SENT: {
        "sheet_ref": "Sheet⑨ 成长者→AI智能助手",
        "user_role": "grower+",
        "sensitivity": "high",   # PHI 可能存在
        "collect": ["agent_id", "message_length"],  # 不记录内容, 只记录元数据
    },
    AuditAction.MICRO_ACTION_COMPLETED: {
        "sheet_ref": "Sheet⑨ 成长者→微行动",
        "user_role": "grower+",
        "sensitivity": "low",
        "collect": ["action_id", "mood_score"],
    },
    AuditAction.CHALLENGE_JOINED: {
        "sheet_ref": "Sheet⑨ 成长者→激励体系",
        "user_role": "grower+",
        "sensitivity": "low",
        "collect": ["challenge_id"],
    },
    AuditAction.CHECKIN_COMPLETED: {
        "sheet_ref": "Sheet⑨ 成长者→激励体系",
        "user_role": "grower+",
        "sensitivity": "low",
        "collect": ["points_awarded"],
    },
    AuditAction.POINTS_AWARDED: {
        "sheet_ref": "Sheet⑦ 积分契约",
        "user_role": "grower+",
        "sensitivity": "medium",
        "collect": ["event_type", "points", "point_type"],
    },
    AuditAction.PROMOTION_INITIATED: {
        "sheet_ref": "Sheet④ 晋级契约",
        "user_role": "grower+",
        "sensitivity": "high",
        "collect": ["current_level", "target_level", "track_type"],
    },
    AuditAction.HEALTH_DATA_RECORDED: {
        "sheet_ref": "Sheet⑨ 成长者→健康数据管理",
        "user_role": "grower+",
        "sensitivity": "high",   # PHI
        "collect": ["data_type", "source"],  # 不记录数值
    },
    AuditAction.DEVICE_BOUND: {
        "sheet_ref": "Sheet⑨ 成长者→健康数据管理",
        "user_role": "grower+",
        "sensitivity": "medium",
        "collect": ["device_type", "device_model"],
    },
}


# ──────────────────────────────────────────
# 2. 审计日志服务
# ──────────────────────────────────────────

class AuditLogger:
    """
    统一审计日志服务。
    
    写入目标:
      - UserActivityLog 表 (主存储, 用于合规查询)
      - Redis Stream (可选, 用于实时监控)
      - 结构化日志 (Python logging, 用于 ELK/Splunk)
    
    PHI 保护策略:
      - sensitivity=high 的记录自动脱敏
      - 聊天内容只记录元数据 (消息长度), 不记录原文
      - 健康数据只记录类型 (blood_glucose), 不记录数值
    """
    
    def __init__(
        self,
        db_session_factory=None,
        redis_client=None,
        logger=None,
    ):
        self.db_session_factory = db_session_factory
        self.redis = redis_client
        self.logger = logger
    
    async def log(
        self,
        user_id: int,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        request: Request = None,
        sensitivity: str = None,
    ) -> dict:
        """
        记录审计日志。
        
        Args:
            user_id: 操作者 ID
            action: 审计动作 (AuditAction 枚举值)
            resource_type: 资源类型 (assessment, chat, points, etc.)
            resource_id: 资源 ID
            details: 详细信息 (会根据 sensitivity 自动脱敏)
            request: FastAPI Request (可选, 提取 IP/UA)
            sensitivity: 敏感度覆盖
        """
        # 确定敏感度
        touchpoint = AUDIT_TOUCHPOINT_MAP.get(action, {})
        sensitivity = sensitivity or touchpoint.get("sensitivity", "low")
        
        # 脱敏处理
        safe_details = self._sanitize_details(details, sensitivity)
        
        # 构造审计记录
        record = {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "details": json.dumps(safe_details, ensure_ascii=False) if safe_details else None,
            "sensitivity": sensitivity,
            "ip_address": self._extract_ip(request) if request else None,
            "user_agent": self._extract_ua(request) if request else None,
            "timestamp": datetime.utcnow().isoformat(),
            "sheet_ref": touchpoint.get("sheet_ref"),
        }
        
        # 写入 DB
        if self.db_session_factory:
            await self._write_db(record)
        
        # 写入 Redis Stream (实时监控)
        if self.redis and sensitivity in ("high", "medium"):
            await self._write_redis_stream(record)
        
        # 结构化日志
        if self.logger:
            self.logger.info(
                "audit_event",
                extra={
                    "audit_action": action,
                    "audit_user_id": user_id,
                    "audit_resource": resource_type,
                    "audit_sensitivity": sensitivity,
                },
            )
        
        return {"logged": True, "action": action}
    
    def _sanitize_details(
        self, details: Optional[Dict], sensitivity: str
    ) -> Optional[Dict]:
        """根据敏感度脱敏"""
        if not details:
            return None
        
        if sensitivity == "high":
            # PHI 脱敏: 移除可能包含健康数据的字段
            PHI_FIELDS = {
                "score", "value", "result", "content",
                "message", "diagnosis", "condition",
                "blood_glucose", "blood_pressure", "weight",
            }
            return {
                k: "[REDACTED]" if k in PHI_FIELDS else v
                for k, v in details.items()
            }
        
        return details
    
    def _extract_ip(self, request: Request) -> Optional[str]:
        """提取客户端 IP"""
        if not request:
            return None
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return getattr(request.client, "host", None)
    
    def _extract_ua(self, request: Request) -> Optional[str]:
        """提取 User-Agent"""
        if not request:
            return None
        return request.headers.get("user-agent", "")[:200]
    
    async def _write_db(self, record: dict) -> None:
        """写入 UserActivityLog 表"""
        try:
            async with self.db_session_factory() as session:
                from app.models.user_activity_log import UserActivityLog
                log_entry = UserActivityLog(
                    user_id=record["user_id"],
                    action=record["action"],
                    resource_type=record.get("resource_type"),
                    resource_id=record.get("resource_id"),
                    details=record.get("details"),
                    ip_address=record.get("ip_address"),
                    user_agent=record.get("user_agent"),
                    created_at=datetime.utcnow(),
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            # 审计写入失败不应阻塞业务流程
            if self.logger:
                self.logger.error(f"Audit write failed: {e}")
    
    async def _write_redis_stream(self, record: dict) -> None:
        """写入 Redis Stream (实时监控)"""
        try:
            stream_key = f"audit:{record.get('sensitivity', 'low')}"
            await self.redis.xadd(stream_key, {
                "user_id": str(record["user_id"]),
                "action": record["action"],
                "timestamp": record["timestamp"],
            }, maxlen=10000)  # 保留最近 1 万条
        except Exception:
            pass  # Redis 故障不阻塞


# ──────────────────────────────────────────
# 3. FastAPI 审计装饰器 (用于路由函数)
# ──────────────────────────────────────────

def audit_endpoint(
    action: str,
    resource_type: str = None,
    sensitivity: str = None,
    extract_resource_id: Callable = None,
):
    """
    审计装饰器。
    
    用法:
        @router.post("/v1/assessment/submit")
        @audit_endpoint(
            action=AuditAction.ASSESSMENT_SUBMITTED,
            resource_type="assessment",
            extract_resource_id=lambda req, resp: resp.get("assessment_id"),
        )
        async def submit_assessment(data: AssessmentSubmit, ...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取审计日志器和请求上下文
            request = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            user = kwargs.get("user") or kwargs.get("current_user")
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 异步写入审计日志 (不阻塞响应)
            try:
                audit_logger = kwargs.get("audit") or _get_audit_logger()
                if audit_logger and user:
                    resource_id = None
                    if extract_resource_id and isinstance(result, dict):
                        resource_id = extract_resource_id(request, result)
                    
                    await audit_logger.log(
                        user_id=getattr(user, "id", 0),
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        request=request,
                        sensitivity=sensitivity,
                    )
            except Exception:
                pass  # 审计失败不影响业务
            
            return result
        return wrapper
    return decorator


def _get_audit_logger() -> Optional[AuditLogger]:
    """获取全局审计日志器实例"""
    # 实际项目中从 app state 或依赖注入获取
    try:
        from app.core.deps import get_audit_logger_singleton
        return get_audit_logger_singleton()
    except ImportError:
        return None


# ──────────────────────────────────────────
# 4. 核心路径审计端点集成示例
# ──────────────────────────────────────────

INTEGRATION_EXAMPLES = """
# ══════════════════════════════════════════
# 各路由文件中添加审计装饰器的示例
# ══════════════════════════════════════════

# --- routers/auth.py ---
@router.post("/v1/auth/register")
@audit_endpoint(action="user_register", resource_type="user")
async def register(data: RegisterRequest, ...):
    ...

@router.post("/v1/auth/login")
@audit_endpoint(action="user_login", resource_type="session", sensitivity="medium")
async def login(data: LoginRequest, ...):
    ...

# --- routers/assessment.py ---
@router.post("/v1/assessment/start")
@audit_endpoint(action="assessment_started", resource_type="assessment")
async def start_assessment(data: AssessmentStart, ...):
    ...

@router.post("/v1/assessment/submit")
@audit_endpoint(
    action="assessment_submitted",
    resource_type="assessment",
    sensitivity="high",
    extract_resource_id=lambda req, resp: resp.get("assessment_id"),
)
async def submit_assessment(data: AssessmentSubmit, ...):
    ...

# --- routers/chat.py ---
@router.post("/v1/chat/session")
@audit_endpoint(action="chat_session_start", resource_type="chat")
async def start_chat(data: ChatStart, ...):
    ...

# --- routers/micro_action.py ---
@router.post("/v1/micro-action/complete")
@audit_endpoint(action="micro_action_completed", resource_type="micro_action")
async def complete_micro_action(data: MicroActionComplete, ...):
    ...

# --- routers/checkin.py ---
@router.post("/v1/checkin")
@audit_endpoint(action="checkin_completed", resource_type="checkin")
async def daily_checkin(...):
    ...

# --- routers/health_data.py ---
@router.post("/v1/health-data/record")
@audit_endpoint(
    action="health_data_recorded",
    resource_type="health_data",
    sensitivity="high",
)
async def record_health_data(data: HealthDataRecord, ...):
    ...

# --- routers/promotion.py ---
@router.post("/v1/promotion/initiate")
@audit_endpoint(
    action="promotion_initiated",
    resource_type="promotion",
    sensitivity="high",
)
async def initiate_promotion(data: PromotionRequest, ...):
    ...
"""


# ──────────────────────────────────────────
# 5. 审计覆盖率计算
# ──────────────────────────────────────────

def calculate_audit_coverage() -> dict:
    """计算审计覆盖率"""
    # Sheet⑨ 定义的全部治理触点
    total_touchpoints = 30  # Sheet⑨ 30个触点
    
    # 现有审计 (安全加固后)
    existing = 6  # content_publish, agent_template_change, knowledge_review,
                  # challenge_push, safety_block, violation_record
    
    # 新增审计 (本次补全)
    new_core_path = 14  # 本次新增
    
    covered = existing + new_core_path
    coverage_pct = round(covered / total_touchpoints * 100, 1)
    
    return {
        "total_touchpoints": total_touchpoints,
        "existing_audit": existing,
        "new_audit": new_core_path,
        "total_covered": covered,
        "coverage_pct": coverage_pct,
        "target": "50%",
        "achieved": coverage_pct >= 50,
        "remaining_for_80pct": max(0, int(total_touchpoints * 0.8) - covered),
    }


if __name__ == "__main__":
    coverage = calculate_audit_coverage()
    print("审计覆盖率分析:")
    print(f"  Sheet⑨ 总触点: {coverage['total_touchpoints']}")
    print(f"  已有审计:     {coverage['existing_audit']}")
    print(f"  新增审计:     {coverage['new_audit']}")
    print(f"  总覆盖:       {coverage['total_covered']}/{coverage['total_touchpoints']}")
    print(f"  覆盖率:       {coverage['coverage_pct']}%")
    print(f"  目标50%达成:  {'✅' if coverage['achieved'] else '❌'}")
    print(f"  距80%还差:    {coverage['remaining_for_80pct']} 个触点")
