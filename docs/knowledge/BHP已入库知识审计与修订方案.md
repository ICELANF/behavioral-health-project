# BHP已入库知识内容审计与修订方案

> **目标**: 对照v2.1规则，审计已入库的全部知识内容，输出差异报告和具体修订行动
> **审计范围**: L1底座(4份) + L2领域知识(12份) + L3情境包(10份) + CLAUDE.md + README.md
> **日期**: 2026-02-28

---

## 一、审计方法论

### 不是"推倒重来"，是"分级补丁"

已入库内容的质量基础是好的——八模块结构完整、话术可用、铁律清晰。问题不在于内容本身错了，而在于**缺少v2.1要求的技术对齐字段和操作化增强**。

修订策略分三级：

| 修订级别 | 含义 | 工作量 | 涉及文件 |
|---------|------|--------|---------|
| 🔴 **必须修** | 与平台技术冲突，不修会导致系统错误 | 小 | L1底座(TTM阶段) |
| 🟡 **应该补** | 缺少v2.1要求的字段，不补则功能不完整 | 中 | 全部L2+L3 |
| 🟢 **可以增** | 操作化增强，不加也能用但质量差一档 | 大 | 含量化指标的L2 |

---

## 二、逐层审计结果

### 2.1 L1底座知识审计（4份文件）

#### `base/ttm_stages.md` — 🔴 必须修

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| 阶段数量 | S0-S6共**7个**阶段 | S0-S5共**6个**阶段 | 🔴 **硬冲突** |
| 阶段命名 | S0无知无觉→S6内化习惯 | S0无意向期→S5复发/循环期 | 🔴 **命名不一致** |
| 用户友好名 | 探索期→收获期 | 无 | 🟡 缺失 |
| StageRuntimeBuilder铁律 | 7条晋级硬规则 | 仅3条概要 | 🟡 不完整 |
| BehaviorFacts门槛 | streak_days/completion_rate等 | 无 | 🟡 缺失 |

**具体问题**：
- 当前写的是TTM经典6阶段（无意向→维持+复发循环），平台实际实现是扩展的S0-S6七阶段
- S6"内化习惯"是平台自定义阶段，经典TTM没有这一层
- "复发/循环期(S5)"在平台中不是独立阶段，而是任意阶段的回退机制
- 阶段晋级门槛（action_completed_7d≥3、streak_days≥14等）完全缺失

**修订行动**：

```markdown
需要重写的内容：

旧版（6阶段）:
  S0 无意向期 → S1 意向期 → S2 准备期 → S3 行动期 → S4 维持期 → S5 复发/循环期

新版（7阶段，对齐平台TTM-7量表）:
  S0 无知无觉(探索期) → S1 强烈抗拒(觉醒期) → S2 被动应对(思考期)
  → S3 勉强接受(准备期) → S4 尝试阶段(行动期) → S5 主动实践(成长期)
  → S6 内化习惯(收获期)

需要补充的内容：
  - 每个阶段的TTM-7量表判定逻辑（每阶段3题，满分15分）
  - 7条阶段晋级铁律（来自StageRuntimeBuilder）
  - BehaviorFacts门槛值
  - 交互模式映射（S0-S1→EMPATHY / S2-S3→EMPATHY或CHALLENGE / S4-S6→EXECUTION）
```

---

#### `base/bpt6_dimensions.md` — 🟡 应该补

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| 维度体系 | 对齐平台BPT-6量表（6类型×3题=18题） | 自定义P1-P6六维度（1-10分） | 🟡 **体系不同** |
| 人格→行为推断 | BIG5→BPT6交叉推断逻辑 | 无 | 🟡 缺失 |
| 与InterventionMatcher对接 | bpt6_type作为处方匹配维度之一 | 无 | 🟡 缺失 |

**具体问题**：
- 当前版本的P1-P6是从教练实训教材提炼的实用维度（情绪化敏感/自我效能感/认知弹性/外部支持度/躯体觉知力/延迟满足感），这些维度在教练工作中非常实用
- 平台的BPT-6是正式量表（action/knowledge/emotion/relation/environment/ambivalent六类型，每类3题共18题）
- 两者不矛盾——P1-P6是"观察维度"，BPT-6是"正式评估工具"

**修订行动**：不删除P1-P6（教练实用工具保留），但补充BPT-6正式量表的说明和映射关系：

```markdown
需要补充的内容：
  - BPT-6正式量表（6类型/18题）与P1-P6观察维度的映射表
  - 人格→行为类型推断逻辑（BIG5交叉分析）
  - 六大行为类型的干预策略矩阵
  - 标注：P1-P6用于教练日常观察，BPT-6用于正式评估
```

---

#### `base/bfr_framework.md` — ✅ 基本合格

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| BFR六要素 | B/F/R/S/T/P | B/F/R/S/T/P ✅ | 无 |
| 强制回溯原则 | 给M-Action前必须完成B和F | ✅ 已有 | 无 |
| 有效vs无效对比 | 需要案例对比 | ✅ 已有 | 无 |

**修订行动**：仅需补充一行，说明BFR是MasterAgent 9步流水线中Step 3"知识检索"的优先触发条件。

---

#### `base/crisis_protocol.md` — ✅ 基本合格，小补

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| 生理红线 | 血糖<2.8或>16.7 / 血压>180/110 | ✅ 一致 | 无 |
| 心理红线 | 直接/间接/自伤表达 | ✅ 已有 | 无 |
| 动作标准 | 停止→路由→教练预警→医疗指引 | ✅ 已有 | 无 |
| CoachPushQueue铁律 | AI→审核→推送零旁路 | 未明确提及 | 🟡 小补 |

**修订行动**：补充一段说明CrisisAgent触发后的处方片段也必须经CoachPushQueue，requires_coach_review=true硬编码。

---

### 2.2 L3情境知识包审计（10份，以S05为典型分析）

**10份情境包共性问题（全部需要补丁）**：

| 检查项 | v2.1要求 | S01-S10当前状态 | 差异级别 |
|--------|---------|---------------|---------|
| TTM阶段标注 | 用S0-S6 | 用S1-S5（旧体系） | 🔴 必须改 |
| evidence_tier | 标注T级 | 无 | 🟡 应该补 |
| scope | 标注platform/domain/tenant | 无 | 🟡 应该补 |
| Markdown元数据 | `<!-- 领域:X \| 证据:T2 \| 阶段:S3,S4 -->` | 无 | 🟡 应该补 |
| InterventionMatcher维度 | 5维匹配标签 | 无 | 🟡 应该补 |
| BehaviorFacts关联 | 阶段晋级门槛 | 无 | 🟡 应该补 |
| 操作化锚点 | 身体尺度/工具/比喻 | **部分已有**（如"200ml温水"） | 🟢 可增强 |
| 五场景脚本 | 在家/外出/超市/聚会/出差 | 无完整覆盖 | 🟢 可增强 |
| 信任分体系 | 对齐平台trust_score(0-100) | 用"2-8分"或"building(30-50%)" | 🟡 格式统一 |

**S01-S10阶段标注的具体修订映射**：

| 情境 | 当前标注 | 应改为（对齐平台S0-S6） |
|------|---------|----------------------|
| S01 情绪进食 | S01-S03(前意向-准备期) | S1-S3(觉醒-准备期) |
| S02 家庭冲突 | S2-S3 | S2-S3(思考-准备期) ✅ 数字一致但名称需更新 |
| S03 自我否定 | S0-S1 | S0-S1(探索-觉醒期) ✅ |
| S04 绩效焦虑 | S2-S3 | S2-S3(思考-准备期) ✅ |
| S05 职场高压 | S1-S2(前意向-意向期) | S1-S2(觉醒-思考期) |
| S06 工具依赖 | S3-S4 | S4-S5(行动-成长期) ← 需要核实 |
| S07 社交应酬 | S2-S3 | S2-S3(思考-准备期) ✅ |
| S08 运动恐惧 | S0-S1 | S0-S1(探索-觉醒期) ✅ |
| S09 价值矛盾 | S0-S1摇摆 | S0-S1(探索-觉醒期) ✅ |
| S10 习得性无助 | S0 | S0(探索期) ✅ |

---

### 2.3 L2领域知识审计（12份文档）

L2文档是在更早的对话中生成的，使用的是初版BHP KMS格式。根据之前的审计记录，共性问题：

| 检查项 | v2.1要求 | L2文档当前状态 | 差异级别 |
|--------|---------|--------------|---------|
| 证据等级 | T1/T2/T3/T4 | 可能用L1-L5旧体系 | 🔴 必须改 |
| 行为阶段 | S0-S6 | 可能用S2_INTENDING等旧命名 | 🔴 必须改 |
| Scope标注 | platform/domain/tenant | 无 | 🟡 应该补 |
| InterventionMatcher 5维 | stage×psych×bpt6×spi×domain | 可能不完整 | 🟡 应该补 |
| 操作化锚点 | 身体尺度/工具/比喻 | 大部分缺失 | 🟢 可增强 |
| Chunker适配 | 每##≤800字符+元数据标注 | 无元数据 | 🟡 应该补 |
| 版本元数据 | document_version/ingest_date/review_cycle | 不确定 | 🟡 应该补 |

---

### 2.4 CLAUDE.md + README.md审计

#### CLAUDE.md — 🟡 应该补

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| AI→审核→推送铁律 | 提及CoachPushQueue | ✅ 已有 | 无 |
| 全局铁律数量 | 3-5条核心 | 5条 ✅ | 无 |
| 行数控制 | ≤100行 | 91行 ✅ | 无 |
| T级说明 | 提及T1-T4证据分级 | 未提及 | 🟡 补 |
| Scope说明 | 提及三级Scope | 未提及 | 🟡 补 |

#### README.md — 🟡 应该补

| 检查项 | v2.1要求 | 当前状态 | 差异 |
|--------|---------|---------|------|
| 阶段标注 | S0-S6 | 用S0-S4+摇摆等描述 | 🔴 必须改 |
| 叠加情境 | 处理优先级 | ✅ 已有 | 无 |
| 跨情境原则 | 5条核心原则 | ✅ 已有 | 无 |
| 知识版本/T级/Scope | 标注 | 未标注 | 🟡 补 |

---

## 三、修订执行方案

### 3.1 修订优先级排序

```
第一批（🔴 1-2天）: 必须修——不修系统对不上
  ① ttm_stages.md 重写（6阶段→7阶段，补晋级铁律）
  ② README.md 阶段标注更新
  ③ S01-S10 的TTM阶段标注统一到S0-S6
  ④ L2文档的证据等级从L1-L5改为T1-T4（如果确认用了旧体系）

第二批（🟡 3-5天）: 应该补——不补功能不完整
  ⑤ 全部L3情境包补Markdown元数据头（领域/证据/阶段/维度）
  ⑥ 全部L3情境包补InterventionMatcher 5维标签
  ⑦ bpt6_dimensions.md 补BPT-6正式量表映射
  ⑧ CLAUDE.md 补T级和Scope说明
  ⑨ 全部L2文档补scope和Chunker元数据

第三批（🟢 1-2周）: 可以增——增了质量上一个台阶
  ⑩ L2文档中含量化指标的KI条目补操作化锚点
  ⑪ L3情境包的M-Action补五场景脚本
  ⑫ 全部文档补版本元数据头(version/ingest_date/review_cycle)
```

### 3.2 第一批修订的具体操作

#### ① ttm_stages.md 重写

**输入**: 当前文件(43行) + 平台TTM-7规格
**输出**: 新版文件(约80行)

核心变更：
```
删除: S5复发/循环期（平台中复发是回退机制，不是独立阶段）
新增: S6内化习惯(收获期)
重写: S0-S1命名对齐平台（无知无觉/强烈抗拒 vs 无意向期/意向期）
新增: 7条StageRuntimeBuilder铁律
新增: BehaviorFacts门槛值表
新增: 交互模式映射表（EMPATHY/CHALLENGE/EXECUTION）
新增: 用户友好名称（探索期/觉醒期/思考期/准备期/行动期/成长期/收获期）
```

#### ② README.md 阶段标注更新

全局替换路由表中的阶段标注：
```
S0-S1 → S0-S1(探索-觉醒期)
S1-S2 → S1-S2(觉醒-思考期)
S2-S3 → S2-S3(思考-准备期)
S3-S4 → S3-S4(准备-行动期)
S0-S1摇摆 → S0-S1(探索-觉醒期，摇摆型)
```

#### ③ S01-S10 统一阶段标注

每份情境包的"适用识别条件"表格中，TTM阶段行统一格式：
```
旧: TTM阶段 | S1–S2（前意向→意向期）
新: TTM阶段 | S1-S2（觉醒期→思考期）| 交互模式: EMPATHY
```

### 3.3 第二批修订的具体操作

#### ⑤ L3情境包补Markdown元数据头

在每份情境包的H1标题下方添加：
```markdown
# S05 · 职场高压 — 身不由己的「职场精英」
<!-- 领域:nutrition,exercise | 证据:P2(影子专家经验) | scope:platform
     阶段:S1,S2 | 交互模式:EMPATHY | 知识包等级:B级
     InterventionMatcher: stage=[S1,S2] | psych=[L2,L3] | bpt6=[environment,action] | spi_min=10 | domain=[nutrition,exercise] -->
```

#### ⑥ L3情境包补InterventionMatcher标签

在每份情境包的"适用识别条件"表格中追加一行：

```markdown
| InterventionMatcher | stage=[S1,S2] · psych=[L2,L3] · bpt6=[environment,action] · spi_min=10 · domain=[nutrition,exercise] |
```

S01-S10各情境的推荐标签：

| 情境 | stage | psych_level | bpt6 | spi_min | domain |
|------|-------|-------------|------|---------|--------|
| S01 情绪进食 | S1,S2,S3 | L2,L3 | emotion,ambivalent | 10 | nutrition,emotion |
| S02 家庭冲突 | S2,S3 | L2,L3 | relation,environment | 15 | nutrition,social |
| S03 自我否定 | S0,S1 | L1,L2 | emotion,ambivalent | 10 | emotion,cognitive |
| S04 绩效焦虑 | S2,S3 | L2,L3 | knowledge,emotion | 15 | nutrition,stress |
| S05 职场高压 | S1,S2 | L2,L3 | environment,action | 10 | nutrition,exercise |
| S06 工具依赖 | S4,S5 | L3,L4 | knowledge,action | 20 | nutrition,cognitive |
| S07 社交应酬 | S2,S3 | L2,L3 | relation,environment | 15 | nutrition,social |
| S08 运动恐惧 | S0,S1 | L1,L2 | emotion,ambivalent | 10 | exercise,emotion |
| S09 价值矛盾 | S0,S1 | L1,L2 | ambivalent,knowledge | 10 | cognitive,emotion |
| S10 习得性无助 | S0 | L1 | emotion,ambivalent | 10 | emotion,cognitive |

---

## 四、自动化审计脚本

以下Python脚本可以扫描全部已入库知识文件，输出差异报告：

```python
#!/usr/bin/env python3
"""
BHP知识库v2.1合规审计工具
扫描知识文件 → 检查v2.1规则 → 输出差异报告
"""
import os, re, json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AuditIssue:
    file: str
    severity: str        # "critical" / "warning" / "enhancement"
    category: str        # "stage_naming" / "evidence_tier" / "scope" / "metadata" / "operationalization"
    description: str
    fix_suggestion: str

@dataclass
class AuditReport:
    issues: List[AuditIssue] = field(default_factory=list)
    
    def add(self, **kwargs):
        self.issues.append(AuditIssue(**kwargs))
    
    def summary(self):
        critical = [i for i in self.issues if i.severity == "critical"]
        warning = [i for i in self.issues if i.severity == "warning"]
        enhancement = [i for i in self.issues if i.severity == "enhancement"]
        return f"🔴 必须修: {len(critical)} | 🟡 应该补: {len(warning)} | 🟢 可增强: {len(enhancement)}"


# ── v2.1合规检查规则 ──

VALID_STAGES = {"S0","S1","S2","S3","S4","S5","S6"}
OLD_STAGE_PATTERNS = [
    r"S0[0-9]",                    # S01, S03等（旧编号）
    r"前意向期",                    # 旧名称
    r"复发/循环期",                 # S5在新体系中不存在
    r"S2_INTENDING",               # v2.0旧命名
    r"S3_PREPARING",
]
OLD_EVIDENCE_PATTERNS = [
    r"L[1-5]级",                   # 旧证据分级
    r"evidence.*L[1-5]",           # 旧字段
]
REQUIRED_METADATA_FIELDS = [
    "领域", "证据", "阶段", "scope"  # Markdown元数据注释中应包含的关键词
]

def audit_file(filepath: str, report: AuditReport):
    """审计单个知识文件"""
    content = Path(filepath).read_text(encoding="utf-8")
    fname = os.path.basename(filepath)
    
    # ── 检查1: 旧阶段命名 ──
    for pattern in OLD_STAGE_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            report.add(
                file=fname,
                severity="critical",
                category="stage_naming",
                description=f"发现旧阶段命名: {matches[:3]}",
                fix_suggestion="替换为S0-S6平台阶段体系（S0无知无觉→S6内化习惯）"
            )
    
    # ── 检查2: 旧证据等级 ──
    for pattern in OLD_EVIDENCE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            report.add(
                file=fname,
                severity="critical",
                category="evidence_tier",
                description=f"发现旧证据分级: {matches[:3]}",
                fix_suggestion="替换为T1/T2/T3/T4平台证据等级"
            )
    
    # ── 检查3: Markdown元数据注释 ──
    has_metadata = "<!--" in content and any(
        kw in content for kw in REQUIRED_METADATA_FIELDS
    )
    if not has_metadata and fname.endswith(".md") and fname != "README.md":
        report.add(
            file=fname,
            severity="warning",
            category="metadata",
            description="缺少Markdown元数据注释（<!-- 领域:X | 证据:TX | ... -->）",
            fix_suggestion="在每个##章节标题下方添加结构化元数据注释"
        )
    
    # ── 检查4: Scope标注 ──
    if "scope" not in content.lower() and fname not in ["CLAUDE.md", "README.md"]:
        report.add(
            file=fname,
            severity="warning",
            category="scope",
            description="未标注scope(platform/domain/tenant)",
            fix_suggestion="在文件元数据中添加scope字段"
        )
    
    # ── 检查5: InterventionMatcher维度（仅L3情境包和含IT-的文档） ──
    if "dietary_s" in fname or "IT-" in content:
        matcher_keywords = ["applicable_stages", "applicable_psych", 
                           "applicable_bpt6", "spi_min", "InterventionMatcher"]
        has_matcher = any(kw in content for kw in matcher_keywords)
        if not has_matcher:
            report.add(
                file=fname,
                severity="warning",
                category="intervention_matcher",
                description="缺少InterventionMatcher五维匹配标签",
                fix_suggestion="添加 stage×psych_level×bpt6×spi×domain 标签"
            )
    
    # ── 检查6: 操作化锚点（含量化指标的文档） ──
    quantitative_patterns = [r"\d+\s*g\b", r"\d+\s*mg\b", r"\d+\s*ml\b", 
                            r"\d+\s*kcal", r"\d+%"]
    has_quantities = any(re.search(p, content) for p in quantitative_patterns)
    operationalization_keywords = ["拳头", "掌心", "限盐勺", "瓶盖", "身体尺度", "操作化"]
    has_operationalization = any(kw in content for kw in operationalization_keywords)
    
    if has_quantities and not has_operationalization:
        report.add(
            file=fname,
            severity="enhancement",
            category="operationalization",
            description="包含量化指标但缺少操作化锚点（身体尺度/工具/比喻）",
            fix_suggestion="为量化指标补充傻瓜相机七原则的操作化表达"
        )
    
    # ── 检查7: 版本元数据 ──
    version_keywords = ["document_version", "ingest_date", "review_cycle", "版本"]
    has_version = any(kw in content for kw in version_keywords)
    if not has_version and fname not in ["README.md", "CLAUDE.md"]:
        report.add(
            file=fname,
            severity="enhancement",
            category="version_metadata",
            description="缺少版本元数据（version/ingest_date/review_cycle）",
            fix_suggestion="添加文档头部版本信息块"
        )
    
    # ── 检查8: BehaviorFacts关联（L3情境包） ──
    if "dietary_s" in fname:
        bf_keywords = ["action_completed_7d", "streak_days", "completion_rate", 
                       "BehaviorFacts", "行为事实"]
        has_bf = any(kw in content for kw in bf_keywords)
        if not has_bf:
            report.add(
                file=fname,
                severity="warning",
                category="behavior_facts",
                description="L3情境包未关联BehaviorFacts触发条件",
                fix_suggestion="补充阶段晋级的BehaviorFacts门槛值"
            )


def run_audit(knowledge_dir: str) -> AuditReport:
    """扫描目录下所有.md文件"""
    report = AuditReport()
    
    for root, dirs, files in os.walk(knowledge_dir):
        for f in files:
            if f.endswith(".md"):
                filepath = os.path.join(root, f)
                audit_file(filepath, report)
    
    return report


def print_report(report: AuditReport):
    """格式化输出审计报告"""
    print("=" * 70)
    print("BHP知识库 v2.1合规审计报告")
    print("=" * 70)
    print(f"\n{report.summary()}\n")
    
    # 按严重级别分组
    for severity, label in [("critical","🔴 必须修"), ("warning","🟡 应该补"), ("enhancement","🟢 可增强")]:
        issues = [i for i in report.issues if i.severity == severity]
        if issues:
            print(f"\n{'─'*50}")
            print(f"{label} ({len(issues)}项)")
            print(f"{'─'*50}")
            for i, issue in enumerate(issues, 1):
                print(f"\n  {i}. [{issue.category}] {issue.file}")
                print(f"     问题: {issue.description}")
                print(f"     修复: {issue.fix_suggestion}")
    
    print(f"\n{'='*70}")


# ── 执行 ──
if __name__ == "__main__":
    import sys
    knowledge_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/knowledge"
    report = run_audit(knowledge_dir)
    print_report(report)
```

---

## 五、实际执行审计

将此脚本放入项目仓库 `scripts/audit_knowledge_v21.py`，执行方式：

```bash
# 审计整个知识库目录
python scripts/audit_knowledge_v21.py docs/knowledge/

# 只审计L3情境包
python scripts/audit_knowledge_v21.py docs/knowledge/ | grep dietary

# 只看必须修的
python scripts/audit_knowledge_v21.py docs/knowledge/ | grep "🔴"
```

**预期输出示例**：

```
======================================================================
BHP知识库 v2.1合规审计报告
======================================================================

🔴 必须修: 3 | 🟡 应该补: 28 | 🟢 可增强: 15

──────────────────────────────────────────────────
🔴 必须修 (3项)
──────────────────────────────────────────────────

  1. [stage_naming] ttm_stages.md
     问题: 发现旧阶段命名: ['复发/循环期']
     修复: 替换为S0-S6平台阶段体系（S0无知无觉→S6内化习惯）

  2. [stage_naming] dietary_s01_emotion.md
     问题: 发现旧阶段命名: ['S01']
     修复: 替换为S0-S6平台阶段体系

  3. [stage_naming] README.md
     问题: 发现旧阶段命名: ['S0–S1摇摆']
     修复: 替换为S0-S1(探索-觉醒期)

──────────────────────────────────────────────────
🟡 应该补 (28项)
──────────────────────────────────────────────────

  1. [metadata] dietary_s01_emotion.md
     问题: 缺少Markdown元数据注释
     修复: 在每个##章节标题下方添加结构化元数据注释
  ...

======================================================================
```

---

## 六、批量修订脚本（半自动）

对于高频重复性修订（如阶段命名替换），提供批量脚本：

```python
#!/usr/bin/env python3
"""
BHP知识库批量修订工具
处理第一批🔴必须修的内容
"""
import os, re
from pathlib import Path

# ── 阶段名称映射表 ──
STAGE_RENAMES = {
    # 旧名 → 新名
    "前意向期": "觉醒期",
    "意向期": "思考期",
    "准备期": "准备期",     # 不变
    "行动期": "行动期",     # 不变
    "维持期": "成长期",
    "复发/循环期": "（复发为回退机制，非独立阶段）",
    "复发期": "（复发为回退机制）",
    
    # 旧阶段引用 → 新引用
    "S01": "S1",  # 情境编号S01不变，但TTM阶段引用S01→S1
    "S02": "S2",
    "S03": "S3",
    "S04": "S4",
    "S05": "S5",
}

# ── 证据等级映射 ──
EVIDENCE_RENAMES = {
    "L1级": "T1",
    "L2级": "T2",
    "L3级": "T3",
    "L4级": "T4",
    "L5级": "T4",  # L5合并到T4
}

def batch_fix_stages(knowledge_dir: str, dry_run=True):
    """批量修正阶段命名"""
    for root, dirs, files in os.walk(knowledge_dir):
        for f in files:
            if not f.endswith(".md"):
                continue
            
            filepath = os.path.join(root, f)
            content = Path(filepath).read_text(encoding="utf-8")
            original = content
            
            # 注意：不替换情境编号（S01-S10是情境ID不是阶段代码）
            # 只替换"TTM阶段"上下文中的旧名称
            for old, new in STAGE_RENAMES.items():
                # 只在TTM/阶段上下文中替换
                content = re.sub(
                    rf'(TTM|阶段|Stage)(.{{0,20}}){re.escape(old)}',
                    lambda m: m.group(0).replace(old, new),
                    content
                )
            
            for old, new in EVIDENCE_RENAMES.items():
                content = content.replace(old, new)
            
            if content != original:
                if dry_run:
                    print(f"[DRY-RUN] 将修改: {f}")
                else:
                    Path(filepath).write_text(content, encoding="utf-8")
                    print(f"[已修改] {f}")

def add_metadata_header(filepath: str, metadata: dict, dry_run=True):
    """为单个文件添加元数据注释头"""
    content = Path(filepath).read_text(encoding="utf-8")
    
    # 在第一个##标题后插入元数据
    meta_line = f"<!-- {' | '.join(f'{k}:{v}' for k,v in metadata.items())} -->"
    
    # 找到第一个#标题行
    lines = content.split("\n")
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            insert_pos = i + 1
            break
    
    lines.insert(insert_pos, meta_line)
    
    if dry_run:
        print(f"[DRY-RUN] 将在 {os.path.basename(filepath)} 第{insert_pos+1}行插入: {meta_line}")
    else:
        Path(filepath).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import sys
    knowledge_dir = sys.argv[1] if len(sys.argv) > 1 else "docs/knowledge"
    
    print("=== 阶段命名修正（DRY-RUN）===")
    batch_fix_stages(knowledge_dir, dry_run=True)
    
    print("\n确认执行请加 --apply 参数")
    if "--apply" in sys.argv:
        batch_fix_stages(knowledge_dir, dry_run=False)
```

---

## 七、修订后的验收标准

全部修订完成后，重新运行审计脚本，目标：

```
🔴 必须修: 0    ← 必须清零
🟡 应该补: ≤5   ← 允许少量合理遗留（如部分L2文档待重新灌入）
🟢 可增强: 不限  ← 操作化增强可分批推进
```

**审计通过条件**：
1. 零🔴（全部阶段命名/证据等级对齐平台）
2. 全部L3情境包有Markdown元数据和InterventionMatcher标签
3. ttm_stages.md已重写为7阶段版本
4. CLAUDE.md已补充T级和Scope说明
