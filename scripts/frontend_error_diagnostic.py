"""
前端 11 个 500/400 逻辑错误诊断脚本 + 修复模板
契约来源: 审计发现 — 前端集成 63 端点中 11 个返回 500/400 逻辑错误

诊断方法: 逐个端点发送典型请求, 捕获错误类型和堆栈
"""

import asyncio
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ──────────────────────────────────────────
# 1. 11 个已知逻辑错误端点清单
# ──────────────────────────────────────────

@dataclass
class EndpointError:
    """前端调用出错的端点记录"""
    endpoint: str
    method: str
    frontend_component: str
    error_type: str        # "500_server" | "400_validation" | "422_unprocessable"
    symptom: str           # 用户侧症状
    probable_cause: str    # 推测原因
    fix_category: str      # "payload_mismatch" | "missing_field" | "type_error" | "auth_context" | "db_constraint"
    fix_template: str      # 修复代码模板
    priority: str          # P0(崩溃) | P1(功能异常) | P2(边缘场景)
    status: str = "pending"


KNOWN_ERRORS: List[EndpointError] = [
    
    # ── 错误 1: 评估提交 payload 字段缺失 ──
    EndpointError(
        endpoint="POST /v1/assessment/submit",
        method="POST",
        frontend_component="AssessmentPage.vue",
        error_type="422_unprocessable",
        symptom="用户完成评估点提交后页面报错,数据未保存",
        probable_cause="前端 payload 缺少 assessment_type 字段; 后端 Pydantic 模型要求此字段为必填",
        fix_category="payload_mismatch",
        fix_template="""
// AssessmentPage.vue - submitAssessment()
// 修复: 添加缺失的 assessment_type 字段
const payload = {
  user_id: this.userId,
  answers: this.answers,
  assessment_type: this.currentAssessmentType,  // ← 添加此字段
  scale_id: this.scaleId,
  completed_at: new Date().toISOString(),
};
await api.post('/v1/assessment/submit', payload);
""",
        priority="P0",
    ),
    
    # ── 错误 2: 微行动完成时心情评分类型错误 ──
    EndpointError(
        endpoint="POST /v1/micro-action/complete",
        method="POST",
        frontend_component="MicroActionCard.vue",
        error_type="422_unprocessable",
        symptom="点击'完成微行动'后报错,积分未增加",
        probable_cause="mood_score 前端传为 string (来自 select 组件), 后端期望 int",
        fix_category="type_error",
        fix_template="""
// MicroActionCard.vue - completeMicroAction()
// 修复: mood_score 转为 int
const payload = {
  action_id: this.action.id,
  completed_at: new Date().toISOString(),
  mood_score: parseInt(this.moodScore, 10),  // ← 确保为整数
  notes: this.completionNotes || null,
};
""",
        priority="P0",
    ),
    
    # ── 错误 3: 签到重复提交 DB 唯一约束 ──
    EndpointError(
        endpoint="POST /v1/checkin",
        method="POST",
        frontend_component="CheckinButton.vue",
        error_type="500_server",
        symptom="快速双击签到按钮导致服务器错误",
        probable_cause="并发请求触发 DB unique constraint (user_id + date); 后端未捕获 IntegrityError",
        fix_category="db_constraint",
        fix_template="""
# 后端修复: routers/checkin.py
from sqlalchemy.exc import IntegrityError

@router.post("/v1/checkin")
async def create_checkin(data: CheckinRequest, db=Depends(get_db), user=Depends(get_current_user)):
    try:
        checkin = await checkin_service.create(db, user.id, data)
        return {"success": True, "points": checkin.points_awarded}
    except IntegrityError:
        # 幂等处理: 已签到则返回成功
        existing = await checkin_service.get_today(db, user.id)
        return {"success": True, "points": 0, "message": "今日已签到", "already_checked_in": True}

# 前端修复: CheckinButton.vue - 添加防抖
import { debounce } from 'lodash';
methods: {
  handleCheckin: debounce(async function() {
    if (this.isSubmitting) return;
    this.isSubmitting = true;
    try {
      const res = await api.post('/v1/checkin');
      // ...
    } finally {
      this.isSubmitting = false;
    }
  }, 300),
}
""",
        priority="P0",
    ),
    
    # ── 错误 4: 健康数据录入缺少设备绑定检查 ──
    EndpointError(
        endpoint="POST /v1/health-data/record",
        method="POST",
        frontend_component="HealthDataForm.vue",
        error_type="400_validation",
        symptom="未绑定设备的用户录入数据时报400,无明确提示",
        probable_cause="后端要求 device_id, 但未绑定设备时 device_id=null, 返回泛化400错误",
        fix_category="missing_field",
        fix_template="""
# 后端修复: 允许手动录入 (device_id 可选)
class HealthDataRecordRequest(BaseModel):
    data_type: str           # blood_glucose | blood_pressure | weight | ...
    value: float
    unit: str
    device_id: Optional[int] = None   # ← 改为可选
    source: str = "manual"             # ← 默认手动录入
    recorded_at: datetime

# 前端修复: 根据是否绑定设备动态设置 source
const payload = {
  data_type: this.dataType,
  value: parseFloat(this.value),
  unit: this.unit,
  device_id: this.boundDevice?.id || null,
  source: this.boundDevice ? 'device' : 'manual',
  recorded_at: new Date().toISOString(),
};
""",
        priority="P1",
    ),
    
    # ── 错误 5: AI对话历史加载分页参数错误 ──
    EndpointError(
        endpoint="GET /v1/chat/history",
        method="GET",
        frontend_component="ChatHistory.vue",
        error_type="422_unprocessable",
        symptom="聊天记录页面空白,控制台422错误",
        probable_cause="前端传 page=0 (零索引), 后端分页从 page=1 开始",
        fix_category="payload_mismatch",
        fix_template="""
// ChatHistory.vue - loadHistory()
// 修复: 分页从 1 开始
const params = {
  agent_id: this.agentId,
  page: this.currentPage + 1,  // ← 前端0索引转后端1索引
  page_size: 20,
};
const res = await api.get('/v1/chat/history', { params });
""",
        priority="P1",
    ),
    
    # ── 错误 6: 挑战参与缺少 challenge_id 路径参数 ──
    EndpointError(
        endpoint="POST /v1/challenge/{id}/join",
        method="POST",
        frontend_component="ChallengeDetail.vue",
        error_type="400_validation",
        symptom="点击'参与挑战'按钮无响应,控制台400",
        probable_cause="前端 URL 构造错误: /v1/challenge/join 而非 /v1/challenge/{id}/join",
        fix_category="payload_mismatch",
        fix_template="""
// ChallengeDetail.vue - joinChallenge()
// 修复: 正确构造路径参数
// 错误: await api.post('/v1/challenge/join', { challenge_id: this.id });
await api.post(`/v1/challenge/${this.challengeId}/join`);  // ← 修正URL
""",
        priority="P1",
    ),
    
    # ── 错误 7: 积分历史查询排序参数无效 ──
    EndpointError(
        endpoint="GET /v1/points/history",
        method="GET",
        frontend_component="PointsHistory.vue",
        error_type="422_unprocessable",
        symptom="积分历史页面报错,无法查看积分变动",
        probable_cause="前端传 sort='latest', 后端期望 sort_by='created_at' + order='desc'",
        fix_category="payload_mismatch",
        fix_template="""
// PointsHistory.vue - loadHistory()
// 修复: 使用正确的排序参数
const params = {
  point_type: this.selectedType || null,
  sort_by: 'created_at',  // ← 替换 sort='latest'
  order: 'desc',           // ← 添加排序方向
  page: this.currentPage,
  page_size: 20,
};
""",
        priority="P2",
    ),
    
    # ── 错误 8: 课程学习进度更新缺少 module_id ──
    EndpointError(
        endpoint="PUT /v1/learning/progress",
        method="PUT",
        frontend_component="LearningModule.vue",
        error_type="422_unprocessable",
        symptom="完成课程模块后进度条未更新",
        probable_cause="payload 中 module_id 字段名与后端不一致 (前端: moduleId, 后端: module_id)",
        fix_category="payload_mismatch",
        fix_template="""
// LearningModule.vue - updateProgress()
// 修复: 字段名对齐后端 snake_case
const payload = {
  course_id: this.courseId,       // ← 不是 courseId
  module_id: this.moduleId,       // ← 不是 moduleId  
  progress_pct: this.progress,
  completed: this.progress >= 100,
  completed_at: this.progress >= 100 ? new Date().toISOString() : null,
};
await api.put('/v1/learning/progress', payload);
""",
        priority="P1",
    ),
    
    # ── 错误 9: 内容发布缺少分类标签验证 ──
    EndpointError(
        endpoint="POST /v1/content/publish",
        method="POST",
        frontend_component="ContentEditor.vue",
        error_type="422_unprocessable",
        symptom="分享者投稿内容时提交失败",
        probable_cause="tags 字段传空数组[], 后端要求至少1个标签; 且 content_tier 未传 (应为 T1~T5)",
        fix_category="payload_mismatch",
        fix_template="""
// ContentEditor.vue - publishContent()
// 修复: 验证标签 + 添加内容层级
if (!this.tags || this.tags.length === 0) {
  this.$message.warning('请至少选择一个分类标签');
  return;
}
const payload = {
  title: this.title,
  body: this.body,
  tags: this.tags,
  content_tier: this.contentTier || 'T1',  // ← 添加内容层级
  author_bio: this.authorBio || '',         // ← Sheet⑨: 投稿表单要求作者简介
  expertise_tags: this.expertiseTags || [], // ← Sheet⑨: 擅长标签
};
""",
        priority="P1",
    ),
    
    # ── 错误 10: Agent创建 system_prompt 超长未校验 ──
    EndpointError(
        endpoint="POST /v1/agent/create",
        method="POST",
        frontend_component="AgentCreator.vue",
        error_type="500_server",
        symptom="创建Agent时服务器报500 (DB字段超长)",
        probable_cause="system_prompt 超过 DB TEXT 字段实际限制; 后端未做长度校验",
        fix_category="payload_mismatch",
        fix_template="""
# 后端修复: 添加长度校验
class AgentCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    domain: str
    system_prompt: str = Field(..., max_length=10000)  # ← 添加上限
    description: str = Field(None, max_length=500)
    
    @validator('system_prompt')
    def validate_prompt_length(cls, v):
        if len(v) > 10000:
            raise ValueError('系统提示词不能超过10000字符')
        return v

// 前端修复: AgentCreator.vue - 添加字符计数
<el-input v-model="systemPrompt" type="textarea" :maxlength="10000" show-word-limit />
""",
        priority="P1",
    ),
    
    # ── 错误 11: 徽章解锁通知缺少用户 context ──
    EndpointError(
        endpoint="GET /v1/badges/unlocked",
        method="GET",
        frontend_component="BadgeNotification.vue",
        error_type="500_server",
        symptom="登录后偶现500错误弹窗 (不影响主流程但影响体验)",
        probable_cause="auth token 中 user_id 为 string, 查询时 DB 比较类型不匹配",
        fix_category="type_error",
        fix_template="""
# 后端修复: routers/badges.py - 确保 user_id 类型
@router.get("/v1/badges/unlocked")
async def get_unlocked_badges(user=Depends(get_current_user), db=Depends(get_db)):
    user_id = int(user.id)  # ← 确保为 int
    badges = await badge_service.get_unlocked(db, user_id)
    return {"badges": badges}
""",
        priority="P2",
    ),
]


# ──────────────────────────────────────────
# 2. 自动化诊断脚本
# ──────────────────────────────────────────

class FrontendErrorDiagnostic:
    """
    自动化诊断 11 个已知前端逻辑错误。
    
    用法 (在有后端访问的环境中):
        diag = FrontendErrorDiagnostic(base_url="http://localhost:8000")
        report = await diag.run_all()
        diag.save_report(report, "frontend_error_diagnostic.json")
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.headers = {}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def diagnose_endpoint(self, error: EndpointError) -> Dict[str, Any]:
        """诊断单个端点"""
        import aiohttp
        
        result = {
            "endpoint": error.endpoint,
            "method": error.method,
            "expected_error": error.error_type,
            "actual_status": None,
            "actual_error": None,
            "matches_expectation": False,
            "fix_verified": False,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # 构造典型触发请求
            url = self._build_url(error.endpoint)
            
            async with aiohttp.ClientSession() as session:
                if error.method == "GET":
                    async with session.get(url, headers=self.headers) as resp:
                        result["actual_status"] = resp.status
                        if resp.status >= 400:
                            result["actual_error"] = await resp.text()
                elif error.method == "POST":
                    async with session.post(url, headers=self.headers, json={}) as resp:
                        result["actual_status"] = resp.status
                        if resp.status >= 400:
                            result["actual_error"] = await resp.text()
                elif error.method == "PUT":
                    async with session.put(url, headers=self.headers, json={}) as resp:
                        result["actual_status"] = resp.status
                        if resp.status >= 400:
                            result["actual_error"] = await resp.text()
            
            result["matches_expectation"] = self._check_match(
                error.error_type, result["actual_status"]
            )
            
        except Exception as e:
            result["actual_error"] = f"Connection error: {str(e)}"
        
        return result
    
    async def run_all(self) -> Dict[str, Any]:
        """运行全部诊断"""
        results = []
        for error in KNOWN_ERRORS:
            result = await self.diagnose_endpoint(error)
            results.append(result)
        
        summary = {
            "total": len(results),
            "confirmed": sum(1 for r in results if r["matches_expectation"]),
            "different": sum(1 for r in results if not r["matches_expectation"]),
            "connection_errors": sum(1 for r in results if "Connection error" in str(r.get("actual_error", ""))),
        }
        
        return {
            "diagnostic_run": datetime.utcnow().isoformat(),
            "summary": summary,
            "results": results,
        }
    
    def _build_url(self, endpoint: str) -> str:
        """构造请求 URL"""
        # 处理路径参数
        path = endpoint.split(" ", 1)[1] if " " in endpoint else endpoint
        path = path.replace("{id}", "1")  # 默认 ID
        return f"{self.base_url}{path}"
    
    def _check_match(self, expected: str, actual_status: int) -> bool:
        """检查实际状态码是否匹配预期错误类型"""
        mapping = {
            "500_server": 500,
            "400_validation": 400,
            "422_unprocessable": 422,
        }
        return mapping.get(expected) == actual_status
    
    def save_report(self, report: dict, filepath: str) -> None:
        """保存诊断报告"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────
# 3. 修复清单总览
# ──────────────────────────────────────────

def generate_fix_checklist() -> str:
    """生成修复工作清单 (用于项目管理)"""
    lines = [
        "# 前端逻辑错误修复清单",
        f"# 生成时间: {datetime.utcnow().isoformat()}",
        f"# 总计: {len(KNOWN_ERRORS)} 个错误",
        "",
        "| # | 优先级 | 端点 | 组件 | 错误类型 | 修复类别 | 状态 |",
        "|---|--------|------|------|----------|----------|------|",
    ]
    
    for i, err in enumerate(KNOWN_ERRORS, 1):
        lines.append(
            f"| {i} | {err.priority} | `{err.endpoint}` | "
            f"{err.frontend_component} | {err.error_type} | "
            f"{err.fix_category} | {err.status} |"
        )
    
    lines.extend([
        "",
        "## 修复类别统计",
        f"- payload_mismatch (前后端字段不一致): {sum(1 for e in KNOWN_ERRORS if e.fix_category == 'payload_mismatch')}",
        f"- type_error (类型转换错误): {sum(1 for e in KNOWN_ERRORS if e.fix_category == 'type_error')}",
        f"- missing_field (字段缺失): {sum(1 for e in KNOWN_ERRORS if e.fix_category == 'missing_field')}",
        f"- db_constraint (数据库约束): {sum(1 for e in KNOWN_ERRORS if e.fix_category == 'db_constraint')}",
        "",
        "## 优先级统计",
        f"- P0 (页面崩溃/数据丢失): {sum(1 for e in KNOWN_ERRORS if e.priority == 'P0')}",
        f"- P1 (功能异常): {sum(1 for e in KNOWN_ERRORS if e.priority == 'P1')}",
        f"- P2 (边缘场景): {sum(1 for e in KNOWN_ERRORS if e.priority == 'P2')}",
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_fix_checklist())
    print("\n\n--- 各错误修复模板 ---")
    for i, err in enumerate(KNOWN_ERRORS, 1):
        print(f"\n{'='*60}")
        print(f"错误 #{i}: {err.endpoint}")
        print(f"组件: {err.frontend_component}")
        print(f"症状: {err.symptom}")
        print(f"原因: {err.probable_cause}")
        print(f"修复代码:")
        print(err.fix_template)
