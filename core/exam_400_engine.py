"""
400分制考核系统 — L3教练认证
契约来源: Sheet⑪ 第5节「L3教练400分制培训考核体系」

考核结构: 理论150 + 技能150 + 综合100 = 400分
及格线:   总分≥240 且 各模块≥单项及格线 且 伦理100%

三大模块:
  理论知识 (150分, ≥90分)
    M1 行为处方设计 (120学分)
    M2 五维解决方案 (100学分)
    M3 身份链重塑 (80学分)
    M4 综合素养 (150学分) — 含 TTM/COM-B/MI/伦理/AI

  技能实践 (150分, ≥90分)
    独立完成≥10案例
    ≥3人实现S0-S4跃迁
    可解释性评分≥0.8
    行为处方设计实操
    AI副驾驶协作演练

  综合素质 (100分, ≥60分)
    伦理边界测试 (必须100%, 一票否决)
    动机式访谈角色扮演
    团队带教能力评估
    应急转介模拟
    7天教练成长挑战

重考规则:
  理论: 每模块可重考1次, 2次不过→延期6个月
  技能: 案例可持续积累, 无重考限制
  伦理: 无补考 (一票否决)

三轨差异 (Sheet⑪ §10):
  A 分享者内生: 直接学习 (有实践基础)
  B 交费学员:   M0补课+20学时平台认知, 培训期学习=成长分
  E 意向早标记: 自然衔接 (成长者已启蒙)
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════
# 0. 枚举与常量
# ══════════════════════════════════════════

class ExamModule(str, Enum):
    THEORY = "theory"          # 理论知识 150分
    SKILLS = "skills"          # 技能实践 150分
    COMPREHENSIVE = "comprehensive"  # 综合素质 100分


class ExamStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    RETAKE_PENDING = "retake_pending"
    DEFERRED = "deferred"      # 延期6月


class CoachTrack(str, Enum):
    A_ORGANIC = "organic"       # 分享者内生
    B_PAID = "paid"             # 交费学员
    E_INTENT = "intent"         # 意向早标记


class CertificationResult(str, Enum):
    CERTIFIED = "certified"
    FAILED_RETAKABLE = "failed_retakable"
    ETHICS_VETO = "ethics_veto"
    DEFERRED = "deferred"
    IN_PROGRESS = "in_progress"


# ══════════════════════════════════════════
# 1. 模块配置 (Sheet⑪ §5)
# ══════════════════════════════════════════

@dataclass
class ModuleConfig:
    module: ExamModule
    name: str
    full_score: int
    pass_score: int
    exam_method: str
    period: str
    sub_modules: List[Dict[str, Any]]
    max_retakes: int           # -1 = 无限
    retake_cooldown_days: int
    defer_months: int          # 超次延期月数
    has_ethics_veto: bool


EXAM_MODULES: Dict[ExamModule, ModuleConfig] = {
    ExamModule.THEORY: ModuleConfig(
        module=ExamModule.THEORY,
        name="理论知识",
        full_score=150,
        pass_score=90,
        exam_method="在线测评",
        period="10个月持续",
        sub_modules=[
            {
                "id": "M1", "name": "行为处方设计",
                "credits": 120, "full_score": 40, "min_score": 24,
                "topics": ["行为处方原理", "BPT-6行为类型", "处方模板设计", "SOP六步法"],
            },
            {
                "id": "M2", "name": "五维解决方案",
                "credits": 100, "full_score": 35, "min_score": 21,
                "topics": ["五维健康模型", "跨维度干预", "方案组合设计"],
            },
            {
                "id": "M3", "name": "身份链重塑",
                "credits": 80, "full_score": 30, "min_score": 18,
                "topics": ["身份认同理论", "行为-身份链", "认知重构技术"],
            },
            {
                "id": "M4", "name": "综合素养",
                "credits": 150, "full_score": 45, "min_score": 27,
                "topics": ["TTM跨理论模型", "COM-B行为模型", "动机式访谈MI",
                           "伦理进阶", "AI副驾驶协作", "数据伦理"],
            },
        ],
        max_retakes=1,
        retake_cooldown_days=14,
        defer_months=6,
        has_ethics_veto=False,
    ),
    ExamModule.SKILLS: ModuleConfig(
        module=ExamModule.SKILLS,
        name="技能实践",
        full_score=150,
        pass_score=90,
        exam_method="案例+同行评审",
        period="第3-10月",
        sub_modules=[
            {
                "id": "SK1", "name": "独立案例完成",
                "requirement": "≥10案例", "min_cases": 10,
            },
            {
                "id": "SK2", "name": "学员跃迁成果",
                "requirement": "≥3人S0-S4跃迁", "min_transitions": 3,
            },
            {
                "id": "SK3", "name": "可解释性评分",
                "requirement": "≥0.8", "min_score": 0.8,
            },
            {
                "id": "SK4", "name": "行为处方设计实操",
                "requirement": "通过", "pass_required": True,
            },
            {
                "id": "SK5", "name": "AI副驾驶协作演练",
                "requirement": "通过", "pass_required": True,
            },
        ],
        max_retakes=-1,   # 案例可持续积累
        retake_cooldown_days=0,
        defer_months=0,
        has_ethics_veto=False,
    ),
    ExamModule.COMPREHENSIVE: ModuleConfig(
        module=ExamModule.COMPREHENSIVE,
        name="综合素质",
        full_score=100,
        pass_score=60,
        exam_method="多维度评估",
        period="全程+毕业",
        sub_modules=[
            {
                "id": "C1", "name": "伦理边界测试",
                "requirement": "必须100%", "is_ethics": True, "veto_on_fail": True,
            },
            {
                "id": "C2", "name": "动机式访谈角色扮演",
                "requirement": "评分制", "full_score": 25,
            },
            {
                "id": "C3", "name": "团队带教能力评估",
                "requirement": "评分制", "full_score": 25,
            },
            {
                "id": "C4", "name": "应急转介模拟",
                "requirement": "评分制", "full_score": 25,
            },
            {
                "id": "C5", "name": "7天教练成长挑战",
                "requirement": "完成", "full_score": 25,
            },
        ],
        max_retakes=1,      # 伦理无补考, 其他可补评1次
        retake_cooldown_days=7,
        defer_months=0,
        has_ethics_veto=True,
    ),
}

TOTAL_FULL_SCORE = 400
TOTAL_PASS_SCORE = 240
CERTIFICATION_PERIOD_MONTHS = 10


# ══════════════════════════════════════════
# 2. 考生状态数据结构
# ══════════════════════════════════════════

@dataclass
class SubModuleScore:
    sub_id: str
    name: str
    score: float = 0.0
    max_score: float = 0.0
    passed: bool = False
    attempt_count: int = 0
    last_attempt_at: str = ""


@dataclass
class ModuleProgress:
    module: ExamModule
    status: ExamStatus = ExamStatus.NOT_STARTED
    score: float = 0.0
    pass_score: float = 0.0
    full_score: float = 0.0
    sub_scores: List[SubModuleScore] = field(default_factory=list)
    attempt_count: int = 0
    retakes_remaining: int = 0
    started_at: str = ""
    completed_at: str = ""
    last_attempt_at: str = ""
    ethics_passed: Optional[bool] = None  # 仅综合模块


@dataclass
class CandidateExamState:
    user_id: int
    coach_track: CoachTrack
    enrollment_date: str
    modules: Dict[str, ModuleProgress] = field(default_factory=dict)
    total_score: float = 0.0
    certification_result: CertificationResult = CertificationResult.IN_PROGRESS
    certified_at: str = ""
    ethics_veto: bool = False
    deferred_until: str = ""
    # 三轨差异
    m0_completed: bool = False    # B轨: M0补课完成
    training_growth_points: int = 0  # B轨: 培训期积累成长分


# ══════════════════════════════════════════
# 3. 400分制考核引擎
# ══════════════════════════════════════════

class Exam400Engine:
    """
    400分制考核引擎。

    核心流程:
      1. 注册考核 (含三轨差异)
      2. 各模块分别考核
      3. 伦理一票否决检查
      4. 总分+各模块及格线校验
      5. 认证/失败/延期判定
      6. 重考管理

    集成点:
      - DualTrackEngine.L2→L3 晋级校验
      - StageEngine (SK2: 学员S0-S4跃迁)
      - PeerTracking (带教质量)
      - CreditsAPI (学分追踪)
    """

    def __init__(self, stage_service=None, points_service=None):
        self.stage_service = stage_service
        self.points_service = points_service
        self._candidates: Dict[int, CandidateExamState] = {}

    # ── 3.1 注册考核 ──

    async def enroll(
        self, user_id: int, coach_track: CoachTrack
    ) -> Dict[str, Any]:
        """注册400分制考核"""
        if user_id in self._candidates:
            state = self._candidates[user_id]
            if state.certification_result == CertificationResult.CERTIFIED:
                return {"error": "already_certified", "message": "已通过认证"}
            if state.certification_result == CertificationResult.ETHICS_VETO:
                return {"error": "ethics_veto", "message": "伦理一票否决, 无法重新认证"}
            # 允许继续
            return self._build_status_response(state)

        now = datetime.now(timezone.utc).isoformat()

        state = CandidateExamState(
            user_id=user_id,
            coach_track=coach_track,
            enrollment_date=now,
        )

        # 初始化各模块进度
        for mod_enum, config in EXAM_MODULES.items():
            retakes = config.max_retakes if config.max_retakes >= 0 else 999
            progress = ModuleProgress(
                module=mod_enum,
                pass_score=config.pass_score,
                full_score=config.full_score,
                retakes_remaining=retakes,
            )
            # 初始化子模块
            for sub in config.sub_modules:
                sub_score = SubModuleScore(
                    sub_id=sub["id"],
                    name=sub["name"],
                    max_score=sub.get("full_score", sub.get("credits", 0)),
                )
                progress.sub_scores.append(sub_score)
            state.modules[mod_enum.value] = progress

        # 三轨差异
        track_info = self._get_track_requirements(coach_track)

        self._candidates[user_id] = state

        return {
            "enrolled": True,
            "user_id": user_id,
            "coach_track": coach_track.value,
            "track_info": track_info,
            "total_full_score": TOTAL_FULL_SCORE,
            "total_pass_score": TOTAL_PASS_SCORE,
            "modules": {
                m.value: {
                    "name": EXAM_MODULES[m].name,
                    "full_score": EXAM_MODULES[m].full_score,
                    "pass_score": EXAM_MODULES[m].pass_score,
                    "method": EXAM_MODULES[m].exam_method,
                }
                for m in ExamModule
            },
            "certification_period_months": CERTIFICATION_PERIOD_MONTHS,
        }

    def _get_track_requirements(self, track: CoachTrack) -> Dict[str, Any]:
        """三轨差异化要求"""
        if track == CoachTrack.A_ORGANIC:
            return {
                "track_name": "分享者内生 (轨道A)",
                "prior_experience": "有带教实践基础",
                "additional_training": None,
                "points_handling": "已有积分延续",
                "m0_required": False,
                "estimated_months": "10-12",
            }
        elif track == CoachTrack.B_PAID:
            return {
                "track_name": "交费学员 (轨道B)",
                "prior_experience": "外部引入",
                "additional_training": "M0平台认知补课 (20学时)",
                "points_handling": "培训期学习=成长分 (从0开始积累)",
                "m0_required": True,
                "estimated_months": "3-6 (全职)",
            }
        else:  # E
            return {
                "track_name": "意向早标记 (轨道E)",
                "prior_experience": "成长者阶段已启蒙",
                "additional_training": None,
                "points_handling": "正常成长轨+意向指标",
                "m0_required": False,
                "estimated_months": "12-24 (完整轨)",
            }

    # ── 3.2 提交模块成绩 ──

    async def submit_module_score(
        self, user_id: int, module: ExamModule, scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """提交单模块成绩"""
        state = self._candidates.get(user_id)
        if not state:
            return {"error": "not_enrolled"}

        if state.ethics_veto:
            return {"error": "ethics_veto", "message": "伦理一票否决, 考核已终止"}

        if state.certification_result == CertificationResult.DEFERRED:
            deferred_dt = datetime.fromisoformat(state.deferred_until)
            if datetime.now(timezone.utc) < deferred_dt:
                return {
                    "error": "deferred",
                    "message": f"延期至 {state.deferred_until[:10]}",
                }

        config = EXAM_MODULES[module]
        progress = state.modules[module.value]
        now = datetime.now(timezone.utc).isoformat()

        if not progress.started_at:
            progress.started_at = now

        progress.attempt_count += 1
        progress.last_attempt_at = now

        # 更新子模块分数
        module_total = 0.0
        all_sub_passed = True

        for sub_score in progress.sub_scores:
            if sub_score.sub_id in scores:
                sub_score.score = scores[sub_score.sub_id]
                sub_score.attempt_count += 1
                sub_score.last_attempt_at = now

                # 子模块及格判定
                sub_config = next(
                    (s for s in config.sub_modules if s["id"] == sub_score.sub_id),
                    {},
                )

                if sub_config.get("is_ethics"):
                    # 伦理: 必须100%
                    sub_score.passed = (sub_score.score >= 100.0)
                    if not sub_score.passed:
                        # ⚠️ 伦理一票否决
                        state.ethics_veto = True
                        state.certification_result = CertificationResult.ETHICS_VETO
                        progress.ethics_passed = False
                        return self._build_ethics_veto_response(state)
                    progress.ethics_passed = True
                elif "min_score" in sub_config:
                    sub_score.passed = (sub_score.score >= sub_config["min_score"])
                elif "min_cases" in sub_config:
                    sub_score.passed = (sub_score.score >= sub_config["min_cases"])
                elif "min_transitions" in sub_config:
                    sub_score.passed = (sub_score.score >= sub_config["min_transitions"])
                elif sub_config.get("pass_required"):
                    sub_score.passed = (sub_score.score > 0)
                else:
                    sub_score.passed = True

                if not sub_score.passed:
                    all_sub_passed = False

            module_total += sub_score.score

        progress.score = min(module_total, config.full_score)

        # 模块及格判定
        if progress.score >= config.pass_score and all_sub_passed:
            progress.status = ExamStatus.PASSED
            progress.completed_at = now
        else:
            # 检查重考机会
            if config.max_retakes >= 0 and progress.attempt_count > config.max_retakes + 1:
                progress.status = ExamStatus.DEFERRED
                state.deferred_until = (
                    datetime.now(timezone.utc) + timedelta(days=config.defer_months * 30)
                ).isoformat()
                state.certification_result = CertificationResult.DEFERRED
            elif progress.attempt_count > 1 and config.max_retakes >= 0:
                progress.retakes_remaining = max(0, config.max_retakes - (progress.attempt_count - 1))
                progress.status = ExamStatus.RETAKE_PENDING if progress.retakes_remaining > 0 else ExamStatus.DEFERRED
            else:
                progress.status = ExamStatus.FAILED

        # 更新总分
        state.total_score = sum(
            m.score for m in state.modules.values()
        )

        # 检查是否全部完成
        self._check_overall_certification(state)

        return self._build_module_result(state, module, progress)

    # ── 3.3 认证校验 ──

    def _check_overall_certification(self, state: CandidateExamState):
        """检查整体认证结果"""
        if state.ethics_veto:
            state.certification_result = CertificationResult.ETHICS_VETO
            return

        all_passed = all(
            m.status == ExamStatus.PASSED for m in state.modules.values()
        )
        any_deferred = any(
            m.status == ExamStatus.DEFERRED for m in state.modules.values()
        )

        if all_passed and state.total_score >= TOTAL_PASS_SCORE:
            state.certification_result = CertificationResult.CERTIFIED
            state.certified_at = datetime.now(timezone.utc).isoformat()
        elif any_deferred:
            state.certification_result = CertificationResult.DEFERRED
        elif all(m.status != ExamStatus.NOT_STARTED for m in state.modules.values()):
            # 全部有成绩但未全部通过
            state.certification_result = CertificationResult.FAILED_RETAKABLE
        else:
            state.certification_result = CertificationResult.IN_PROGRESS

    # ── 3.4 查询接口 ──

    def get_exam_status(self, user_id: int) -> Dict[str, Any]:
        """查询考核状态全景"""
        state = self._candidates.get(user_id)
        if not state:
            return {"enrolled": False}
        return self._build_status_response(state)

    def get_module_detail(self, user_id: int, module: ExamModule) -> Dict[str, Any]:
        """查询单模块详情"""
        state = self._candidates.get(user_id)
        if not state:
            return {"enrolled": False}

        progress = state.modules.get(module.value)
        if not progress:
            return {"error": "module_not_found"}

        config = EXAM_MODULES[module]
        return {
            "module": module.value,
            "name": config.name,
            "status": progress.status.value,
            "score": progress.score,
            "pass_score": config.pass_score,
            "full_score": config.full_score,
            "attempt_count": progress.attempt_count,
            "retakes_remaining": progress.retakes_remaining,
            "sub_scores": [
                {
                    "sub_id": s.sub_id, "name": s.name,
                    "score": s.score, "max_score": s.max_score,
                    "passed": s.passed, "attempts": s.attempt_count,
                }
                for s in progress.sub_scores
            ],
            "ethics_passed": progress.ethics_passed,
        }

    def get_retake_eligibility(self, user_id: int, module: ExamModule) -> Dict[str, Any]:
        """检查重考资格"""
        state = self._candidates.get(user_id)
        if not state:
            return {"eligible": False, "reason": "未注册考核"}

        if state.ethics_veto:
            return {"eligible": False, "reason": "伦理一票否决, 无补考"}

        progress = state.modules.get(module.value)
        if not progress:
            return {"eligible": False, "reason": "模块不存在"}

        config = EXAM_MODULES[module]

        # 伦理无补考
        if config.has_ethics_veto and progress.ethics_passed is False:
            return {"eligible": False, "reason": "伦理测试无补考 (一票否决)"}

        # 技能: 案例持续积累无限制
        if module == ExamModule.SKILLS:
            return {
                "eligible": True,
                "reason": "案例可持续积累, 无重考限制",
                "retakes_remaining": 999,
            }

        # 理论/综合: 检查重考次数
        if config.max_retakes >= 0 and progress.retakes_remaining <= 0:
            return {
                "eligible": False,
                "reason": f"已用完{config.max_retakes}次重考机会, 延期{config.defer_months}个月",
                "deferred_until": state.deferred_until,
            }

        # 冷却期
        if progress.last_attempt_at:
            last = datetime.fromisoformat(progress.last_attempt_at)
            cooldown_end = last + timedelta(days=config.retake_cooldown_days)
            if datetime.now(timezone.utc) < cooldown_end:
                return {
                    "eligible": False,
                    "reason": f"冷却期中, {config.retake_cooldown_days}天后可重考",
                    "cooldown_until": cooldown_end.isoformat(),
                }

        return {
            "eligible": True,
            "retakes_remaining": progress.retakes_remaining,
        }

    # ── 3.5 B轨 M0补课 ──

    async def complete_m0(self, user_id: int) -> Dict[str, Any]:
        """B轨学员完成M0平台认知补课"""
        state = self._candidates.get(user_id)
        if not state:
            return {"error": "not_enrolled"}

        if state.coach_track != CoachTrack.B_PAID:
            return {"info": "非B轨学员, 无需M0补课"}

        state.m0_completed = True
        return {
            "m0_completed": True,
            "message": "M0平台认知补课完成 (20学时), 可正式开始M1-M4学习",
            "growth_points_awarded": 20,  # 补课=成长分
        }

    # ── 3.6 B轨 培训学分→成长分 ──

    async def record_training_credits(
        self, user_id: int, credits: int, module_id: str
    ) -> Dict[str, Any]:
        """B轨: 培训学习=成长分"""
        state = self._candidates.get(user_id)
        if not state:
            return {"error": "not_enrolled"}

        if state.coach_track == CoachTrack.B_PAID:
            state.training_growth_points += credits
            return {
                "growth_points_earned": credits,
                "total_training_points": state.training_growth_points,
                "module": module_id,
                "message": f"培训学习+{credits}成长分",
            }

        return {"info": "非B轨学员, 学分正常计入"}

    # ── 响应构建 ──

    def _build_status_response(self, state: CandidateExamState) -> Dict[str, Any]:
        modules_data = {}
        for mod_key, progress in state.modules.items():
            config = EXAM_MODULES[ExamModule(mod_key)]
            modules_data[mod_key] = {
                "name": config.name,
                "status": progress.status.value,
                "score": progress.score,
                "pass_score": config.pass_score,
                "full_score": config.full_score,
                "passed": progress.status == ExamStatus.PASSED,
                "attempt_count": progress.attempt_count,
                "ethics_passed": progress.ethics_passed,
            }

        return {
            "user_id": state.user_id,
            "coach_track": state.coach_track.value,
            "enrollment_date": state.enrollment_date,
            "total_score": state.total_score,
            "total_pass_score": TOTAL_PASS_SCORE,
            "total_full_score": TOTAL_FULL_SCORE,
            "certification_result": state.certification_result.value,
            "ethics_veto": state.ethics_veto,
            "modules": modules_data,
            "certified_at": state.certified_at,
            "deferred_until": state.deferred_until,
            "m0_completed": state.m0_completed,
            "training_growth_points": state.training_growth_points,
        }

    def _build_module_result(
        self, state: CandidateExamState, module: ExamModule, progress: ModuleProgress
    ) -> Dict[str, Any]:
        config = EXAM_MODULES[module]
        return {
            "module": module.value,
            "module_name": config.name,
            "score": progress.score,
            "pass_score": config.pass_score,
            "full_score": config.full_score,
            "status": progress.status.value,
            "passed": progress.status == ExamStatus.PASSED,
            "attempt_count": progress.attempt_count,
            "retakes_remaining": progress.retakes_remaining,
            "ethics_passed": progress.ethics_passed,
            "sub_scores": [
                {"sub_id": s.sub_id, "name": s.name, "score": s.score, "passed": s.passed}
                for s in progress.sub_scores
            ],
            "overall": {
                "total_score": state.total_score,
                "certification_result": state.certification_result.value,
                "ethics_veto": state.ethics_veto,
            },
        }

    def _build_ethics_veto_response(self, state: CandidateExamState) -> Dict[str, Any]:
        return {
            "ethics_veto": True,
            "message": "伦理边界测试未通过 — 一票否决。教练认证已终止, 无补考机会。",
            "certification_result": CertificationResult.ETHICS_VETO.value,
            "consequences": [
                "400分制考核立即终止",
                "伦理测试无补考",
                "需重新参加完整伦理培训",
                "重新评估教练资格",
            ],
            "recovery_path": "完成伦理重修培训后, 经伦理委员会审核, 方可重新申请考核",
        }


# ══════════════════════════════════════════
# 4. API 端点
# ══════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/exam", tags=["exam-400"])


class EnrollRequest(BaseModel):
    user_id: int
    coach_track: str = "organic"


class ModuleScoreSubmit(BaseModel):
    user_id: int
    module: str
    scores: Dict[str, float]


class M0CompleteRequest(BaseModel):
    user_id: int


class TrainingCreditRequest(BaseModel):
    user_id: int
    credits: int
    module_id: str


# 共享引擎实例
_engine = Exam400Engine()


@router.post("/enroll")
async def enroll_exam(req: EnrollRequest):
    """注册400分制考核"""
    track = CoachTrack(req.coach_track)
    return await _engine.enroll(req.user_id, track)


@router.post("/submit")
async def submit_module_score(req: ModuleScoreSubmit):
    """提交模块成绩"""
    module = ExamModule(req.module)
    return await _engine.submit_module_score(req.user_id, module, req.scores)


@router.get("/status/{user_id}")
async def get_exam_status(user_id: int):
    """查询考核全景状态"""
    return _engine.get_exam_status(user_id)


@router.get("/module/{user_id}/{module}")
async def get_module_detail(user_id: int, module: str):
    """查询单模块详情"""
    return _engine.get_module_detail(user_id, ExamModule(module))


@router.get("/retake/{user_id}/{module}")
async def check_retake(user_id: int, module: str):
    """检查重考资格"""
    return _engine.get_retake_eligibility(user_id, ExamModule(module))


@router.post("/m0-complete")
async def complete_m0(req: M0CompleteRequest):
    """B轨M0补课完成"""
    return await _engine.complete_m0(req.user_id)


@router.post("/training-credits")
async def record_credits(req: TrainingCreditRequest):
    """B轨培训学分→成长分"""
    return await _engine.record_training_credits(req.user_id, req.credits, req.module_id)
