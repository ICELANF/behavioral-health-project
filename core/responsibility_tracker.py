"""
责任追踪服务
契约来源: Sheet⑥ 责任追踪契约

34条责任指标自动追踪:
  GRW-01~06: 成长者 (6条)
  SHR-01~05: 分享者 (5条)
  COA-01~10: 教练   (10条)
  PRO-01~07: 促进师 (7条)
  MAS-01~06: 大师   (6条)

每条责任包含:
  - 自动化指标 + 数据源
  - 健康阈值 (绿/黄/红)
  - 告警规则
  - 追踪方式 (自动/半自动)
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════
# 0. 数据结构
# ══════════════════════════════════════════

class HealthColor(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class TrackingMode(str, Enum):
    AUTO = "auto"
    SEMI_AUTO = "semi_auto"


@dataclass
class ResponsibilityItem:
    """单条责任项定义"""
    code: str                    # GRW-01, COA-03 etc.
    role: str                    # 成长者/分享者/教练/促进师/大师
    title: str                   # 责任条款
    metric_name: str             # 自动化指标名称
    data_source: str             # 数据源
    green_threshold: str         # 绿色阈值描述
    yellow_threshold: str        # 黄色告警条件
    red_threshold: str           # 红色告警条件
    alert_rule: str              # 告警规则
    tracking_mode: TrackingMode
    escalation_target: str = ""  # 升级对象


@dataclass
class TrackingResult:
    """单条责任追踪结果"""
    code: str
    title: str
    role: str
    color: HealthColor
    current_value: Any
    threshold_desc: str
    alert_message: str = ""
    last_checked: str = ""
    data_source: str = ""
    needs_action: bool = False


@dataclass
class UserHealthReport:
    """用户责任健康报告"""
    user_id: int
    role: str
    level: str
    checked_at: str
    items: List[TrackingResult]
    overall_color: HealthColor
    green_count: int = 0
    yellow_count: int = 0
    red_count: int = 0
    health_score: float = 0.0    # 0-100


# ══════════════════════════════════════════
# 1. 责任注册表 (Sheet⑥ 完整映射)
# ══════════════════════════════════════════

RESPONSIBILITY_REGISTRY: List[ResponsibilityItem] = [
    # ── 成长者 GRW-01~06 ──
    ResponsibilityItem(
        code="GRW-01", role="成长者", title="如实记录健康数据",
        metric_name="data_entry_frequency", data_source="健康数据API",
        green_threshold="每周≥3次录入", yellow_threshold="连续5天无录入",
        red_threshold="连续7天无录入", alert_rule="连续7天无录入→温和提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="GRW-02", role="成长者", title="积极参与方案交互",
        metric_name="program_interaction_rate", data_source="Program API",
        green_threshold="≥60%每日交互", yellow_threshold="连续2天未交互",
        red_threshold="连续3天未交互", alert_rule="连续3天未交互→AI推送",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="GRW-03", role="成长者", title="持续学习",
        metric_name="weekly_learning_minutes", data_source="Learning API",
        green_threshold="每周≥30分钟", yellow_threshold="本周<15分钟",
        red_threshold="连续2周未学习", alert_rule="连续2周未学习→引导推送",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="GRW-04", role="成长者", title="遵守社区规范",
        metric_name="safety_interception_rate", data_source="SafetyPipeline L1",
        green_threshold="拦截率<3%", yellow_threshold="拦截率3-5%",
        red_threshold="拦截率>5%", alert_rule=">5%→内容警告",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="GRW-05", role="成长者", title="配合教练指导",
        metric_name="coach_message_reply_rate", data_source="Messages API",
        green_threshold="48h内回复≥80%", yellow_threshold="回复率60-80%",
        red_threshold="连续3条未复", alert_rule="连续3条未复→教练提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="GRW-06", role="成长者", title="安全告知",
        metric_name="crisis_keyword_triggers", data_source="CrisisAgent Log",
        green_threshold="触发→通知教练", yellow_threshold="—",
        red_threshold="高风险→即时通知", alert_rule="高风险→即时通知",
        tracking_mode=TrackingMode.AUTO,
    ),
    # ── 分享者 SHR-01~05 ──
    ResponsibilityItem(
        code="SHR-01", role="分享者", title="内容真实准确",
        metric_name="content_approval_rate", data_source="Contributions API",
        green_threshold="通过率≥80%", yellow_threshold="通过率60-80%",
        red_threshold="连续3篇退回", alert_rule="连续3篇退回→内容培训",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="SHR-02", role="分享者", title="同道者带教责任",
        metric_name="peer_graduation_rate", data_source="CompanionRelation",
        green_threshold="毕业率≥60%", yellow_threshold="毕业率50-60%",
        red_threshold="低于50%", alert_rule="低于50%→影响晋级",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="SHR-03", role="分享者", title="不传播未证实健康信息",
        metric_name="medical_claim_interceptions", data_source="SafetyPipeline L4",
        green_threshold="0次拦截", yellow_threshold="单月1次拦截",
        red_threshold="单月>2次", alert_rule="单月>2次→培训提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="SHR-04", role="分享者", title="社区积极贡献",
        metric_name="community_reply_frequency", data_source="Content Comments",
        green_threshold="每周≥3次回复", yellow_threshold="本周1-2次",
        red_threshold="连续2周无回复", alert_rule="连续2周无回复→温和引导",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="SHR-05", role="分享者", title="示范作用",
        metric_name="personal_health_activity_rate", data_source="MicroAction+HealthData",
        green_threshold="月活跃度≥70%", yellow_threshold="月活跃度50-70%",
        red_threshold="连续月<50%", alert_rule="连续月<50%→提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    # ── 教练 COA-01~10 ──
    ResponsibilityItem(
        code="COA-01", role="教练", title="学员关怀(定期查看数据)",
        metric_name="student_data_view_frequency", data_source="StudentHealthData日志",
        green_threshold="每周≥1次/学员", yellow_threshold="本周有学员未查看",
        red_threshold="连续2周未查看", alert_rule="连续2周未查看→黄色",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="COA-02", role="教练", title="消息及时响应",
        metric_name="avg_response_time_hours", data_source="Messages API",
        green_threshold="≤24小时", yellow_threshold="24-48小时",
        red_threshold="超48h", alert_rule="超48h→红色告警",
        tracking_mode=TrackingMode.AUTO, escalation_target="Admin",
    ),
    ResponsibilityItem(
        code="COA-03", role="教练", title="告警及时处理",
        metric_name="alert_response_time", data_source="DeviceAlerts API",
        green_threshold="高风险≤4h, 普通≤24h", yellow_threshold="高风险4-8h",
        red_threshold="超时", alert_rule="超时→升级Admin",
        tracking_mode=TrackingMode.AUTO, escalation_target="Admin",
    ),
    ResponsibilityItem(
        code="COA-04", role="教练", title="专业准确性",
        metric_name="safety_pipeline_interception_rate", data_source="SafetyLog",
        green_threshold="拦截率<5%", yellow_threshold="拦截率5-10%",
        red_threshold=">10%", alert_rule=">10%→培训提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="COA-05", role="教练", title="持续学习(1500学分)",
        metric_name="quarterly_credits", data_source="Credits API",
        green_threshold="每季度≥25学分", yellow_threshold="季度<20学分",
        red_threshold="连续2季度不达标", alert_rule="连续2季度不达标→复评",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="COA-06", role="教练", title="评估跟进",
        metric_name="assessment_review_days", data_source="AssessmentAssignment",
        green_threshold="≤7天审核", yellow_threshold="7-14天",
        red_threshold="超14天", alert_rule="超14天→自动提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="COA-07", role="教练", title="伦理遵守",
        metric_name="monthly_complaint_count", data_source="SafetyLog+Complaint",
        green_threshold="每月0投诉", yellow_threshold="单月1投诉",
        red_threshold="单月≥2", alert_rule="单月≥2→督导介入",
        tracking_mode=TrackingMode.AUTO, escalation_target="督导",
    ),
    ResponsibilityItem(
        code="COA-08", role="教练", title="转介义务",
        metric_name="out_of_scope_referral_rate", data_source="AgentRouter+Safety",
        green_threshold="超范围→转介", yellow_threshold="未及时转介",
        red_threshold="未转介", alert_rule="未转介→培训触发",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="COA-09", role="教练", title="带教质量",
        metric_name="mentee_quality_score", data_source="CompanionRelation",
        green_threshold="毕业率≥70%, 质量分≥3.5", yellow_threshold="毕业率60-70%",
        red_threshold="低于阈值", alert_rule="低于阈值→影响晋级",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="COA-10", role="教练", title="数据安全",
        metric_name="unauthorized_access_count", data_source="AuditLog+RBAC",
        green_threshold="无越权访问", yellow_threshold="—",
        red_threshold="异常访问", alert_rule="异常→锁定+通知Admin",
        tracking_mode=TrackingMode.AUTO, escalation_target="Admin",
    ),
    # ── 促进师 PRO-01~07 ──
    ResponsibilityItem(
        code="PRO-01", role="促进师", title="督导下级教练",
        metric_name="supervision_frequency", data_source="督导中心API",
        green_threshold="每月2次+每季5案例", yellow_threshold="月<2次",
        red_threshold="不达标", alert_rule="不达标→季度考核扣分",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="PRO-02", role="促进师", title="内容证据分级",
        metric_name="evidence_tier_ratio", data_source="ExpertContent T1-T4",
        green_threshold="T1+T2占比≥70%", yellow_threshold="T1+T2 50-70%",
        red_threshold="T3+T4>50%", alert_rule="T3+T4>50%→审查",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="PRO-03", role="促进师", title="Agent质量",
        metric_name="agent_avg_rating", data_source="AgentMetricsDaily",
        green_threshold="平均评分≥4.0", yellow_threshold="评分3.5-4.0",
        red_threshold="<3.5", alert_rule="<3.5→模板下架审查",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="PRO-04", role="促进师", title="工作室运营",
        metric_name="tenant_monthly_active_rate", data_source="TenantStats API",
        green_threshold="月活跃≥50%", yellow_threshold="活跃30-50%",
        red_threshold="<30%", alert_rule="<30%→运营建议推送",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="PRO-05", role="促进师", title="培训义务",
        metric_name="quarterly_training_count", data_source="Credits API",
        green_threshold="每季度≥1次培训", yellow_threshold="本季0次",
        red_threshold="连续2季0", alert_rule="连续2季0→降级预警",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="PRO-06", role="促进师", title="知识贡献",
        metric_name="monthly_knowledge_contributions", data_source="KnowledgeSharing",
        green_threshold="每月≥1篇", yellow_threshold="本月0篇",
        red_threshold="连续3月0", alert_rule="连续3月0→贡献提醒",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="PRO-07", role="促进师", title="利益冲突披露",
        metric_name="disclosure_update_status", data_source="Disclosure+Creds",
        green_threshold="半年更新+证书未过期", yellow_threshold="临近过期(30天内)",
        red_threshold="过期", alert_rule="过期→限制部分权限",
        tracking_mode=TrackingMode.AUTO,
    ),
    # ── 大师 MAS-01~06 ──
    ResponsibilityItem(
        code="MAS-01", role="大师", title="行业引领(持续产出)",
        metric_name="methodology_publication_frequency", data_source="Content(methodology)",
        green_threshold="每季度≥1篇", yellow_threshold="本季0篇",
        red_threshold="连续2季0", alert_rule="连续2季0→影响力评估",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="MAS-02", role="大师", title="标准维护参与",
        metric_name="governance_participation_frequency", data_source="GovernanceLog",
        green_threshold="每半年≥1次参与", yellow_threshold="6月内未参与",
        red_threshold="1年未参", alert_rule="1年未参→治理讨论邀请",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="MAS-03", role="大师", title="高级督导",
        metric_name="advanced_supervision_count", data_source="督导中心API",
        green_threshold="每季度≥2次", yellow_threshold="本季<2次",
        red_threshold="连续2季0", alert_rule="连续2季0→督导提醒",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="MAS-04", role="大师", title="人才培养",
        metric_name="annual_high_level_mentees", data_source="CompanionRelation",
        green_threshold="年培养≥2名L4+", yellow_threshold="年内1名",
        red_threshold="持续无培养", alert_rule="持续无培养→评估讨论",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
    ResponsibilityItem(
        code="MAS-05", role="大师", title="知识贡献",
        metric_name="frontier_knowledge_contributions", data_source="KnowledgeSharing",
        green_threshold="每月≥2篇", yellow_threshold="月<2篇",
        red_threshold="连续3月不达标", alert_rule="连续3月不达标→沟通",
        tracking_mode=TrackingMode.AUTO,
    ),
    ResponsibilityItem(
        code="MAS-06", role="大师", title="生态建设",
        metric_name="quarterly_innovation_count", data_source="AgentEcosystem+Content",
        green_threshold="每季度≥1项创新", yellow_threshold="本季0项",
        red_threshold="连续2季0", alert_rule="连续2季0→引导讨论",
        tracking_mode=TrackingMode.SEMI_AUTO,
    ),
]

# 角色→责任项映射
ROLE_RESPONSIBILITIES = {
    "成长者": [r for r in RESPONSIBILITY_REGISTRY if r.role == "成长者"],
    "分享者": [r for r in RESPONSIBILITY_REGISTRY if r.role == "分享者"],
    "教练": [r for r in RESPONSIBILITY_REGISTRY if r.role == "教练"],
    "促进师": [r for r in RESPONSIBILITY_REGISTRY if r.role == "促进师"],
    "大师": [r for r in RESPONSIBILITY_REGISTRY if r.role == "大师"],
}

LEVEL_TO_ROLE = {
    "L0": "成长者", "L1": "成长者",
    "L2": "分享者", "L3": "教练",
    "L4": "促进师", "L5": "大师",
}


# ══════════════════════════════════════════
# 2. 责任追踪引擎
# ══════════════════════════════════════════

class ResponsibilityTracker:
    """
    责任追踪引擎。
    
    调用方式:
      tracker = ResponsibilityTracker(metrics_provider)
      report = await tracker.generate_health_report(user_id, level)
    
    集成点:
      - 定时任务 (每日凌晨) 批量检查
      - 教练仪表盘实时查询
      - 晋级校验前置检查
    """
    
    def __init__(self, metrics_provider=None, alert_service=None):
        self.metrics = metrics_provider
        self.alerts = alert_service
    
    async def generate_health_report(
        self, user_id: int, level: str, metrics_override: Dict[str, Any] = None
    ) -> UserHealthReport:
        """生成用户责任健康报告"""
        role = LEVEL_TO_ROLE.get(level, "成长者")
        items = ROLE_RESPONSIBILITIES.get(role, [])
        
        results = []
        for item in items:
            result = await self._evaluate_item(user_id, item, metrics_override)
            results.append(result)
        
        green = sum(1 for r in results if r.color == HealthColor.GREEN)
        yellow = sum(1 for r in results if r.color == HealthColor.YELLOW)
        red = sum(1 for r in results if r.color == HealthColor.RED)
        total = len(results)
        
        # 健康评分: 绿=100, 黄=60, 红=20
        score = ((green * 100 + yellow * 60 + red * 20) / total) if total > 0 else 0
        
        # 综合颜色
        if red > 0:
            overall = HealthColor.RED
        elif yellow > 0:
            overall = HealthColor.YELLOW
        else:
            overall = HealthColor.GREEN
        
        return UserHealthReport(
            user_id=user_id,
            role=role,
            level=level,
            checked_at=datetime.now(timezone.utc).isoformat(),
            items=results,
            overall_color=overall,
            green_count=green,
            yellow_count=yellow,
            red_count=red,
            health_score=round(score, 1),
        )
    
    async def _evaluate_item(
        self, user_id: int, item: ResponsibilityItem,
        metrics_override: Dict[str, Any] = None
    ) -> TrackingResult:
        """评估单条责任项"""
        # 获取指标值
        if metrics_override and item.metric_name in metrics_override:
            value = metrics_override[item.metric_name]
        elif self.metrics:
            try:
                value = await self.metrics.get_metric(user_id, item.metric_name)
            except Exception:
                value = None
        else:
            value = None
        
        # 判定颜色 (通用规则引擎)
        color = self._judge_color(item, value)
        
        alert_msg = ""
        needs_action = False
        if color == HealthColor.RED:
            alert_msg = item.alert_rule
            needs_action = True
        elif color == HealthColor.YELLOW:
            alert_msg = item.yellow_threshold
        
        return TrackingResult(
            code=item.code,
            title=item.title,
            role=item.role,
            color=color,
            current_value=value,
            threshold_desc=item.green_threshold,
            alert_message=alert_msg,
            last_checked=datetime.now(timezone.utc).isoformat(),
            data_source=item.data_source,
            needs_action=needs_action,
        )
    
    def _judge_color(self, item: ResponsibilityItem, value: Any) -> HealthColor:
        """
        通用颜色判定。
        
        支持多种指标类型:
          - 数值型: 与阈值比较
          - 频率型: 与最低频率比较
          - 布尔型: True=绿, False=红
          - 比率型: 百分比阈值
        """
        if value is None:
            return HealthColor.YELLOW  # 数据缺失→黄色
        
        # 特殊处理某些指标
        code = item.code
        
        # 数值型 (越高越好)
        if code in ("GRW-01", "GRW-03", "SHR-04", "COA-05"):
            return self._judge_numeric_higher_better(value, item)
        
        # 比率型 (越高越好)
        if code in ("GRW-02", "GRW-05", "SHR-01", "SHR-02", "SHR-05",
                     "COA-09", "PRO-04"):
            return self._judge_rate_higher_better(value, item)
        
        # 比率型 (越低越好)
        if code in ("GRW-04", "COA-04", "SHR-03"):
            return self._judge_rate_lower_better(value, item)
        
        # 时间型 (越短越好)
        if code in ("COA-02", "COA-03", "COA-06"):
            return self._judge_time_shorter_better(value, item)
        
        # 计数型 (越少越好)
        if code in ("COA-07", "COA-10"):
            return self._judge_count_lower_better(value, item)
        
        # 评分型 (越高越好)
        if code in ("PRO-03",):
            if isinstance(value, (int, float)):
                if value >= 4.0: return HealthColor.GREEN
                if value >= 3.5: return HealthColor.YELLOW
                return HealthColor.RED
        
        # 频率型 (有/无)
        if code in ("PRO-01", "PRO-05", "PRO-06", "MAS-01", "MAS-02",
                     "MAS-03", "MAS-04", "MAS-05", "MAS-06"):
            if isinstance(value, (int, float)):
                if value > 0: return HealthColor.GREEN
                return HealthColor.YELLOW
            return HealthColor.YELLOW
        
        # 布尔型
        if isinstance(value, bool):
            return HealthColor.GREEN if value else HealthColor.RED
        
        # 默认
        return HealthColor.GREEN
    
    def _judge_numeric_higher_better(self, value, item) -> HealthColor:
        if not isinstance(value, (int, float)):
            return HealthColor.YELLOW
        # 从 green_threshold 提取数字 (简化: 取第一个数字)
        import re
        nums = re.findall(r'[\d.]+', item.green_threshold)
        if nums:
            threshold = float(nums[0])
            if value >= threshold:
                return HealthColor.GREEN
            if value >= threshold * 0.6:
                return HealthColor.YELLOW
            return HealthColor.RED
        return HealthColor.GREEN if value > 0 else HealthColor.YELLOW
    
    def _judge_rate_higher_better(self, value, item) -> HealthColor:
        if not isinstance(value, (int, float)):
            return HealthColor.YELLOW
        import re
        nums = re.findall(r'[\d.]+', item.green_threshold)
        if nums:
            threshold = float(nums[0])
            # 百分比处理
            if threshold > 1:
                threshold /= 100
            if value >= threshold:
                return HealthColor.GREEN
            if value >= threshold * 0.8:
                return HealthColor.YELLOW
            return HealthColor.RED
        return HealthColor.GREEN
    
    def _judge_rate_lower_better(self, value, item) -> HealthColor:
        if not isinstance(value, (int, float)):
            return HealthColor.YELLOW
        import re
        nums = re.findall(r'[\d.]+', item.green_threshold)
        if nums:
            threshold = float(nums[0])
            if threshold > 1:
                threshold /= 100
            if value <= threshold:
                return HealthColor.GREEN
            if value <= threshold * 1.5:
                return HealthColor.YELLOW
            return HealthColor.RED
        return HealthColor.GREEN
    
    def _judge_time_shorter_better(self, value, item) -> HealthColor:
        if not isinstance(value, (int, float)):
            return HealthColor.YELLOW
        import re
        nums = re.findall(r'[\d.]+', item.green_threshold)
        if nums:
            threshold = float(nums[0])
            if value <= threshold:
                return HealthColor.GREEN
            if value <= threshold * 2:
                return HealthColor.YELLOW
            return HealthColor.RED
        return HealthColor.GREEN
    
    def _judge_count_lower_better(self, value, item) -> HealthColor:
        if not isinstance(value, (int, float)):
            return HealthColor.YELLOW
        if value == 0:
            return HealthColor.GREEN
        if value <= 1:
            return HealthColor.YELLOW
        return HealthColor.RED
    
    # ── 批量检查 (定时任务) ──
    
    async def batch_check(
        self, user_ids_levels: List[Tuple[int, str]],
        metrics_batch: Dict[int, Dict[str, Any]] = None,
    ) -> List[UserHealthReport]:
        """批量检查所有用户责任健康"""
        reports = []
        for user_id, level in user_ids_levels:
            user_metrics = (metrics_batch or {}).get(user_id)
            report = await self.generate_health_report(user_id, level, user_metrics)
            reports.append(report)
            
            # 触发告警
            if report.overall_color == HealthColor.RED and self.alerts:
                red_items = [r for r in report.items if r.color == HealthColor.RED]
                for red in red_items:
                    await self._fire_alert(user_id, level, red)
        
        return reports
    
    async def _fire_alert(self, user_id: int, level: str, result: TrackingResult):
        """触发告警"""
        if self.alerts:
            try:
                # 查找升级目标
                item = next((r for r in RESPONSIBILITY_REGISTRY if r.code == result.code), None)
                await self.alerts.send(
                    user_id=user_id,
                    alert_type="responsibility_red",
                    code=result.code,
                    title=result.title,
                    message=result.alert_message,
                    escalation_target=item.escalation_target if item else "",
                )
            except Exception:
                pass
    
    # ── 查询接口 ──
    
    def get_responsibilities_for_role(self, role: str) -> List[Dict]:
        """查询角色的所有责任项"""
        items = ROLE_RESPONSIBILITIES.get(role, [])
        return [
            {
                "code": r.code,
                "title": r.title,
                "metric_name": r.metric_name,
                "data_source": r.data_source,
                "green_threshold": r.green_threshold,
                "alert_rule": r.alert_rule,
                "tracking_mode": r.tracking_mode.value,
            }
            for r in items
        ]
    
    def get_all_registry_stats(self) -> Dict[str, Any]:
        """注册表统计"""
        return {
            "total_items": len(RESPONSIBILITY_REGISTRY),
            "by_role": {role: len(items) for role, items in ROLE_RESPONSIBILITIES.items()},
            "auto_count": sum(1 for r in RESPONSIBILITY_REGISTRY if r.tracking_mode == TrackingMode.AUTO),
            "semi_auto_count": sum(1 for r in RESPONSIBILITY_REGISTRY if r.tracking_mode == TrackingMode.SEMI_AUTO),
        }
