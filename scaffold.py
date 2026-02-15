#!/usr/bin/env python3
"""
V4.1 Agent双层分离 — 自动化脚手架

功能:
  1. 扫描现有Agent代码，分类为用户层/教练层
  2. 生成双模块目录结构
  3. 创建跨层API网关路由表
  4. 生成数据迁移脚本骨架

用法:
    python scaffold.py analyze /path/to/xingjian/app     # 分析现有Agent
    python scaffold.py generate /path/to/xingjian/app     # 生成双层结构
    python scaffold.py migrate-plan /path/to/xingjian/app # 生成迁移计划
"""
import re
import sys
import json
from pathlib import Path
from collections import defaultdict


# ═══════════════════════════════════════════
# Sheet⑫ Agent分层定义
# ═══════════════════════════════════════════

# 用户层 (assistant_agents): 科普/支持/危机, 不给个体建议
ASSISTANT_AGENTS = {
    "health_assistant":    {"domain": "general",     "desc": "健康知识科普助手"},
    "nutrition_guide":     {"domain": "nutrition",   "desc": "营养知识引导"},
    "exercise_guide":      {"domain": "exercise",    "desc": "运动知识引导"},
    "sleep_guide":         {"domain": "sleep",       "desc": "睡眠知识引导"},
    "emotion_support":     {"domain": "mental",      "desc": "情绪支持（非诊断）"},
    "tcm_wellness":        {"domain": "tcm",         "desc": "中医养生知识"},
    "motivation_support":  {"domain": "mental",      "desc": "动机激发支持"},
    "crisis_responder":    {"domain": "safety",      "desc": "危机响应（转介）"},
    "habit_tracker":       {"domain": "general",     "desc": "习惯追踪助手"},
    "community_guide":     {"domain": "social",      "desc": "社区引导助手"},
    "onboarding_guide":    {"domain": "general",     "desc": "新手引导 (TrustGuide)"},
    "content_recommender": {"domain": "general",     "desc": "内容推荐助手"},
}

# 教练层 (professional_agents): 处方/评估/组合, 必须经教练审核
PROFESSIONAL_AGENTS = {
    # 12个领域专业Agent
    "behavior_coach":      {"domain": "behavior",    "desc": "行为教练（上游前置）", "rx": True},
    "metabolic_expert":    {"domain": "endocrine",   "desc": "代谢内分泌专家", "rx": True},
    "cardiac_rehab":       {"domain": "cardio",      "desc": "心血管康复专家", "rx": True},
    "adherence_monitor":   {"domain": "adherence",   "desc": "就医依从性（横切）", "rx": True},
    "nutrition_expert":    {"domain": "nutrition",   "desc": "营养处方专家", "rx": True},
    "exercise_expert":     {"domain": "exercise",    "desc": "运动处方专家", "rx": True},
    "sleep_expert":        {"domain": "sleep",       "desc": "睡眠干预专家", "rx": True},
    "tcm_expert":          {"domain": "tcm",         "desc": "中医辨证专家", "rx": True},
    "mental_expert":       {"domain": "mental",      "desc": "心理干预专家", "rx": True},
    "chronic_manager":     {"domain": "chronic",     "desc": "慢病管理专家", "rx": True},
    "rehab_expert":        {"domain": "rehab",       "desc": "康复管理专家", "rx": True},
    "health_educator":     {"domain": "education",   "desc": "健康教育专家", "rx": True},
    # 4个专家级Agent
    "assessment_engine":   {"domain": "assessment",  "desc": "评估引擎Agent", "rx": False},
    "rx_composer":         {"domain": "rx",          "desc": "处方编排Agent", "rx": True},
    "supervisor_reviewer": {"domain": "governance",  "desc": "督导审核Agent", "rx": False},
    "quality_auditor":     {"domain": "governance",  "desc": "质量审计Agent", "rx": False},
}


# ═══════════════════════════════════════════
# 分析: 扫描现有Agent代码
# ═══════════════════════════════════════════

def analyze(app_dir: str):
    """扫描现有Agent代码，输出分层分析"""
    app_path = Path(app_dir)
    print(f"\n{'═'*60}")
    print(f"  V4.1 Agent双层分离 — 代码分析")
    print(f"  扫描: {app_path}")
    print(f"{'═'*60}\n")

    # 1. 找所有Agent相关文件
    agent_files = []
    for pattern in ["**/agent*.py", "**/agents/**/*.py", "**/chat/**/*.py",
                    "**/services/agent*.py", "**/services/chat*.py"]:
        agent_files.extend(app_path.glob(pattern))
    agent_files = sorted(set(agent_files))

    print(f"[1] Agent相关文件: {len(agent_files)}个")
    for f in agent_files:
        print(f"    {f.relative_to(app_path)}")

    # 2. 找Agent类/函数定义
    print(f"\n[2] Agent定义扫描")
    agents_found = {}
    for f in agent_files:
        content = f.read_text(errors="ignore")
        # 类定义
        for m in re.finditer(r'class\s+(\w*Agent\w*)\s*[:(]', content):
            agents_found[m.group(1)] = str(f.relative_to(app_path))
        # 字典/配置注册
        for m in re.finditer(r'["\'](\w+_agent|agent_\w+)["\']', content):
            agents_found[m.group(1)] = str(f.relative_to(app_path))

    for name, loc in sorted(agents_found.items()):
        # 分类
        layer = "?"
        for an in ASSISTANT_AGENTS:
            if an.replace("_", "") in name.lower().replace("_", ""):
                layer = "用户层"
                break
        for an in PROFESSIONAL_AGENTS:
            if an.replace("_", "") in name.lower().replace("_", ""):
                layer = "教练层"
                break
        print(f"    {layer:4s} │ {name:30s} │ {loc}")

    # 3. 找DB模型
    print(f"\n[3] Agent相关数据表")
    model_files = list(app_path.rglob("models/*.py")) + list(app_path.rglob("models/**/*.py"))
    agent_tables = []
    for f in model_files:
        content = f.read_text(errors="ignore")
        for m in re.finditer(r'__tablename__\s*=\s*["\'](\w*(?:agent|chat|session|message)\w*)["\']',
                             content, re.I):
            agent_tables.append((m.group(1), str(f.relative_to(app_path))))

    for table, loc in sorted(agent_tables):
        # 分层: 教练层专属表 vs 共享表 vs 用户层表
        if any(kw in table for kw in ["coach", "supervisor", "professional", "rx_", "prescription"]):
            layer = "教练层"
        elif any(kw in table for kw in ["assistant", "public_chat"]):
            layer = "用户层"
        else:
            layer = "共享"
        print(f"    {layer:4s} │ {table:40s} │ {loc}")

    # 4. 找API路由
    print(f"\n[4] Agent API路由")
    route_files = list(app_path.rglob("api/**/*.py")) + list(app_path.rglob("routers/**/*.py"))
    agent_routes = []
    for f in route_files:
        content = f.read_text(errors="ignore")
        for m in re.finditer(
            r'@router\.(get|post|put|delete)\s*\(\s*["\']([^"\']*(?:agent|chat|session|message)[^"\']*)["\']',
            content, re.I
        ):
            agent_routes.append((m.group(1).upper(), m.group(2), str(f.relative_to(app_path))))

    for method, path, loc in sorted(agent_routes, key=lambda x: x[1]):
        if any(kw in path for kw in ["/assistant/", "/v1/assistant"]):
            layer = "用户层"
        elif any(kw in path for kw in ["/agent/", "/v1/agent", "/coach/"]):
            layer = "教练层"
        else:
            layer = "待分"
        print(f"    {layer:4s} │ {method:6s} {path:50s} │ {loc}")

    # 5. 生成分离计划
    print(f"\n{'═'*60}")
    print(f"  分离计划摘要")
    print(f"{'═'*60}")
    print(f"  Agent定义: {len(agents_found)}个")
    print(f"  相关数据表: {len(agent_tables)}个")
    print(f"  API路由: {len(agent_routes)}个")
    print(f"\n  下一步: python scaffold.py generate {app_dir}")

    return {
        "agents": agents_found,
        "tables": agent_tables,
        "routes": agent_routes,
        "files": [str(f.relative_to(app_path)) for f in agent_files],
    }


# ═══════════════════════════════════════════
# 生成: 创建双层目录结构
# ═══════════════════════════════════════════

def generate(app_dir: str):
    """在项目中生成双层Agent目录结构"""
    app_path = Path(app_dir)

    # 目标结构
    structure = {
        "assistant_agents": {
            "__init__.py": '"""用户层Agent — 12个健康助手, 科普/支持/危机"""\n',
            "registry.py": _gen_registry("assistant", ASSISTANT_AGENTS),
            "router.py": _gen_router("assistant", "/v1/assistant"),
            "base.py": _gen_base_agent("assistant"),
            "agents/": {
                "__init__.py": "",
                **{f"{name}.py": _gen_agent_stub(name, spec, "assistant")
                   for name, spec in ASSISTANT_AGENTS.items()},
            },
            "schemas/": {
                "__init__.py": "",
                "requests.py": _gen_schemas("assistant"),
                "responses.py": _gen_response_schemas("assistant"),
            },
        },
        "professional_agents": {
            "__init__.py": '"""教练层Agent — 12+4专业Agent, 处方/评估/组合"""\n',
            "registry.py": _gen_registry("professional", PROFESSIONAL_AGENTS),
            "router.py": _gen_router("professional", "/v1/agent"),
            "base.py": _gen_base_agent("professional"),
            "agents/": {
                "__init__.py": "",
                **{f"{name}.py": _gen_agent_stub(name, spec, "professional")
                   for name, spec in PROFESSIONAL_AGENTS.items()},
            },
            "schemas/": {
                "__init__.py": "",
                "requests.py": _gen_schemas("professional"),
                "responses.py": _gen_response_schemas("professional"),
            },
        },
        "gateway": {
            "__init__.py": '"""跨层API网关 — 路由/授权/脱敏"""\n',
            "router.py": _gen_gateway_router(),
            "auth.py": _gen_gateway_auth(),
            "sanitizer.py": _gen_sanitizer(),
        },
    }

    print(f"\n{'═'*60}")
    print(f"  V4.1 Agent双层分离 — 生成目录结构")
    print(f"{'═'*60}\n")

    created = _create_tree(app_path, structure)
    print(f"\n✅ 共创建 {created} 个文件")
    print(f"\n验证: 独立import测试")
    print(f"  cd {app_path}")
    print(f"  python -c 'from assistant_agents.registry import REGISTRY; print(len(REGISTRY))'")
    print(f"  python -c 'from professional_agents.registry import REGISTRY; print(len(REGISTRY))'")


def _create_tree(base: Path, tree: dict, prefix: str = "") -> int:
    count = 0
    for name, content in tree.items():
        path = base / name
        if isinstance(content, dict):
            # 目录
            path.mkdir(parents=True, exist_ok=True)
            print(f"  📁 {prefix}{name}/")
            count += _create_tree(path, content, prefix + "  ")
        else:
            # 文件
            if not path.exists():
                path.write_text(content, encoding="utf-8")
                print(f"  📄 {prefix}{name}")
                count += 1
            else:
                print(f"  ⏭  {prefix}{name} (已存在)")
    return count


# ═══════════════════════════════════════════
# 代码生成器
# ═══════════════════════════════════════════

def _gen_registry(layer: str, agents: dict) -> str:
    entries = []
    for name, spec in agents.items():
        rx = f', "rx_enabled": True' if spec.get("rx") else ""
        entries.append(f'    "{name}": {{"domain": "{spec["domain"]}", "desc": "{spec["desc"]}"{rx}}},')

    return f'''"""
{layer.title()} Agent 注册表

每个Agent必须在此注册才能被路由发现。
从 agents/ 目录加载具体实现。
"""
from typing import Dict, Any

REGISTRY: Dict[str, Any] = {{
{chr(10).join(entries)}
}}


def get_agent(name: str):
    """按名称获取Agent实例"""
    if name not in REGISTRY:
        raise ValueError(f"未注册的Agent: {{name}}")

    # 延迟导入避免循环
    import importlib
    module = importlib.import_module(f".agents.{{name}}", package=__package__)
    agent_class = getattr(module, "Agent", None)
    if agent_class is None:
        raise ImportError(f"agents/{{name}}.py 缺少 Agent 类")
    return agent_class()


def list_agents() -> list:
    """列出所有已注册Agent"""
    return [
        {{"name": k, **v}}
        for k, v in REGISTRY.items()
    ]
'''


def _gen_router(layer: str, prefix: str) -> str:
    role_check = (
        'requires_role(["admin", "grower", "observer"])'
        if layer == "assistant"
        else 'requires_role(["admin", "coach", "supervisor"])'
    )
    return f'''"""
{layer.title()} Agent API路由

前缀: {prefix}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 按实际路径调整
# from app.core.auth import get_current_user, {role_check.split('(')[0]}
# from app.core.database import get_db

router = APIRouter(prefix="{prefix}", tags=["{layer}_agents"])


@router.get("/agents")
async def list_agents():
    """列出可用Agent"""
    from .registry import list_agents
    return {{"agents": list_agents()}}


@router.post("/chat")
async def chat(
    agent_name: str,
    message: str,
    # current_user = Depends(get_current_user),
    # db: AsyncSession = Depends(get_db),
):
    """与Agent对话"""
    from .registry import get_agent
    try:
        agent = get_agent(agent_name)
    except (ValueError, ImportError) as e:
        raise HTTPException(404, str(e))

    # TODO: 实现实际对话逻辑
    # result = await agent.run(message, user=current_user, db=db)
    result = await agent.run(message)
    return result


@router.get("/agents/{{agent_name}}")
async def get_agent_info(agent_name: str):
    """获取Agent详情"""
    from .registry import REGISTRY
    if agent_name not in REGISTRY:
        raise HTTPException(404, f"Agent不存在: {{agent_name}}")
    return {{"name": agent_name, **REGISTRY[agent_name]}}
'''


def _gen_base_agent(layer: str) -> str:
    safety_note = (
        "用户层Agent不提供个体化建议，仅科普/支持/转介。"
        if layer == "assistant"
        else "教练层Agent输出必须经教练审核后才能触达用户。"
    )
    return f'''"""
{layer.title()} Agent 基类

安全约束: {safety_note}
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Base{layer.title()}Agent(ABC):
    """所有{layer}层Agent的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def domain(self) -> str:
        ...

    @abstractmethod
    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """处理用户/教练输入，返回结构化响应"""
        ...

    async def safety_check(self, message: str) -> bool:
        """安全检查 — L1拦截"""
        # TODO: 接入SafetyPipeline
        dangerous_keywords = ["自杀", "自残", "伤害自己"]
        return not any(kw in message for kw in dangerous_keywords)

    def _format_response(self, content: str, **metadata) -> Dict[str, Any]:
        return {{
            "agent": self.name,
            "domain": self.domain,
            "content": content,
            "layer": "{layer}",
            **metadata,
        }}
'''


def _gen_agent_stub(name: str, spec: dict, layer: str) -> str:
    base_class = f"Base{layer.title()}Agent"
    rx_section = ""
    if spec.get("rx"):
        rx_section = """
    async def compute_rx(self, profile: dict) -> dict:
        \"\"\"调用Rx引擎生成行为处方\"\"\"
        # TODO: 接入BehaviorRxEngine
        # from app.engines.behavior_rx import BehaviorRxEngine
        # rx = BehaviorRxEngine()
        # return await rx.compute(profile, domain=self.domain)
        return {"rx": "placeholder", "domain": self.domain}
"""
    return f'''"""
{spec["desc"]}
领域: {spec["domain"]}
层级: {layer}
"""
from ..base import {base_class}


class Agent({base_class}):
    @property
    def name(self) -> str:
        return "{name}"

    @property
    def domain(self) -> str:
        return "{spec['domain']}"

    async def run(self, message: str, **kwargs) -> dict:
        # 安全检查
        if not await self.safety_check(message):
            return self._format_response(
                "检测到安全风险，已转介专业支持。",
                safety_intercepted=True,
            )

        # TODO: 实现具体逻辑
        # 1. 意图识别
        # 2. 知识检索 (RAG)
        # 3. 响应生成 (LLM)
        # 4. 安全过滤 (L2-L5)

        return self._format_response(
            f"[{name}] 收到: {{message[:100]}}",
            status="stub",
        )
{rx_section}'''


def _gen_schemas(layer: str) -> str:
    return f'''"""
{layer.title()} Agent 请求Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    agent_name: str = Field(..., description="Agent名称")
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    context: Optional[dict] = None


class AgentListRequest(BaseModel):
    domain: Optional[str] = None
    page: int = 1
    page_size: int = 20
'''


def _gen_response_schemas(layer: str) -> str:
    review_field = ""
    if layer == "professional":
        review_field = """
    coach_reviewed: bool = Field(False, description="教练是否已审核")
    review_note: Optional[str] = None"""

    return f'''"""
{layer.title()} Agent 响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Any


class ChatResponse(BaseModel):
    agent: str
    domain: str
    content: str
    layer: str = "{layer}"
    safety_intercepted: bool = False{review_field}
    metadata: Optional[dict] = None
'''


def _gen_gateway_router() -> str:
    return '''"""
跨层API网关 — 路由分发 + 权限校验

用户层请求 → /v1/assistant/*  → assistant_agents
教练层请求 → /v1/agent/*      → professional_agents
跨层请求   → /v1/gateway/*    → 授权+脱敏后转发
"""
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/v1/gateway", tags=["cross_layer_gateway"])


@router.get("/patient-summary/{user_id}")
async def get_patient_summary_for_coach(
    user_id: str,
    # current_user = Depends(require_coach_role),
):
    """
    教练查看用户摘要 — 脱敏后返回
    
    数据流: 教练层 → 网关(授权+脱敏) → 用户层DB → 脱敏 → 返回教练
    """
    from .sanitizer import sanitize_for_coach
    # TODO: 查询用户层数据
    # raw_data = await user_db.get_patient_summary(user_id)
    # return sanitize_for_coach(raw_data)
    return {"user_id": user_id, "status": "stub"}


@router.post("/rx-delivery/{user_id}")
async def deliver_rx_to_user(
    user_id: str,
    rx_data: dict,
    # current_user = Depends(require_coach_role),
):
    """
    教练审核后的处方下发给用户
    
    数据流: 教练层(审核通过) → 网关(记录+转换) → 用户层存储 → 用户可见
    """
    # TODO: 验证教练审核状态
    # TODO: 写入用户层DB
    # TODO: 审计日志
    return {"delivered": True, "user_id": user_id}
'''


def _gen_gateway_auth() -> str:
    return '''"""
跨层授权 — 教练访问用户数据的权限校验

规则 (Sheet⑤ + Sheet⑫):
  - 教练只能访问自己带教的用户数据
  - 督导可以访问下属教练的所有用户数据
  - Admin可以访问所有数据
  - 用户层Agent永远不能访问教练层数据
"""


async def verify_coach_access(coach_id: str, user_id: str, db) -> bool:
    """验证教练是否有权访问该用户的数据"""
    # TODO: 查询 coach_student_mapping 表
    # mapping = await db.execute(
    #     select(CoachStudentMapping)
    #     .where(CoachStudentMapping.coach_id == coach_id)
    #     .where(CoachStudentMapping.student_id == user_id)
    #     .where(CoachStudentMapping.is_active == True)
    # )
    # return mapping.scalar_one_or_none() is not None
    return True  # STUB


async def verify_supervisor_access(supervisor_id: str, user_id: str, db) -> bool:
    """验证督导是否有权（通过下属教练）访问用户数据"""
    # TODO: 两级查询
    # 1. supervisor → coaches (supervisor_coach_mapping)
    # 2. coaches → users (coach_student_mapping)
    return True  # STUB
'''


def _gen_sanitizer() -> str:
    return '''"""
数据脱敏管道 — 跨层数据传输时的字段级脱敏

规则 (Sheet⑫ 数据隔离边界):
  - 心理评估原始数据: 教练只能看聚合统计，不能看原始答题
  - 对话日志: 教练可看，但脱敏敏感关键词
  - 行为处方: 制定教练可看完整版，其他教练看摘要版
"""
from typing import Any, Dict
import re


# 敏感关键词（脱敏为 [***]）
SENSITIVE_PATTERNS = [
    r"\\b\\d{11}\\b",          # 手机号
    r"\\b\\d{17}[\\dXx]\\b",   # 身份证
    r"[\\w.-]+@[\\w.-]+",    # 邮箱
    r"(?:密码|password)\\s*[:=]\\s*\\S+",  # 密码
]


def sanitize_for_coach(data: Dict[str, Any]) -> Dict[str, Any]:
    """教练视角脱敏"""
    result = {}
    for key, value in data.items():
        if key in ("raw_assessment_answers", "psychological_raw", "therapy_notes_raw"):
            # 原始评估数据 → 聚合统计
            result[key + "_summary"] = _aggregate(value)
        elif isinstance(value, str):
            result[key] = _redact_pii(value)
        else:
            result[key] = value
    return result


def _redact_pii(text: str) -> str:
    """去除PII"""
    for pattern in SENSITIVE_PATTERNS:
        text = re.sub(pattern, "[***]", text)
    return text


def _aggregate(raw_data) -> dict:
    """原始数据→聚合统计"""
    if isinstance(raw_data, list):
        return {
            "total_items": len(raw_data),
            "summary": "已脱敏，仅显示聚合统计",
        }
    return {"summary": "已脱敏"}
'''


# ═══════════════════════════════════════════
# 迁移计划
# ═══════════════════════════════════════════

def migrate_plan(app_dir: str):
    """生成数据迁移计划"""
    app_path = Path(app_dir)
    print(f"\n{'═'*60}")
    print(f"  V4.1 数据迁移计划 (Week 2)")
    print(f"{'═'*60}\n")

    # 扫描数据表
    tables = {"user_layer": [], "coach_layer": [], "shared": []}

    model_files = list(app_path.rglob("models/*.py")) + list(app_path.rglob("models/**/*.py"))
    for f in model_files:
        content = f.read_text(errors="ignore")
        for m in re.finditer(r'__tablename__\s*=\s*["\'](\w+)["\']', content):
            table = m.group(1)
            if any(kw in table for kw in [
                "coach", "supervisor", "professional", "agent_template",
                "agent_prompt", "agent_metric", "agent_feedback",
                "rx_prescription", "rx_log", "decision_trace",
            ]):
                tables["coach_layer"].append(table)
            elif any(kw in table for kw in [
                "user", "profile", "behavioral_profile", "journey",
                "activity", "point", "badge", "achievement",
                "public_content", "community",
            ]):
                tables["user_layer"].append(table)
            else:
                tables["shared"].append(table)

    for layer, tlist in tables.items():
        print(f"  {layer} ({len(tlist)}表):")
        for t in sorted(tlist)[:10]:
            print(f"    - {t}")
        if len(tlist) > 10:
            print(f"    ... 另有{len(tlist)-10}个")
        print()

    print(f"""
迁移策略 (Sheet⑫ 3.3节):

  Phase A (Week 2 前半): Schema分离
    1. 在PostgreSQL中创建 coach_schema
    2. 将教练层表迁移到 coach_schema (ALTER TABLE SET SCHEMA)
    3. 创建cross-schema view用于过渡期兼容
    4. 更新ORM的schema_name配置

  Phase B (Week 2 后半): 连接分离
    1. 创建两个独立的database URL配置
    2. 用户层: postgresql://user_rw@.../xingjian?search_path=public
    3. 教练层: postgresql://coach_rw@.../xingjian?search_path=coach_schema
    4. 网关层: postgresql://gateway_ro@.../xingjian (只读, 两个schema都可见)

  Phase C (Week 3): 完全分离 (可选)
    1. 将coach_schema提取到独立数据库
    2. 跨库通过API网关通信
    3. 这是终态，但Phase B已满足合规要求

生成Alembic迁移脚本:
  python scaffold.py generate-migration {app_dir}
""")


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "."

    if cmd == "analyze":
        analyze(target)
    elif cmd == "generate":
        generate(target)
    elif cmd == "migrate-plan":
        migrate_plan(target)
    else:
        print(f"未知: {cmd}")
        print("支持: analyze | generate | migrate-plan")
