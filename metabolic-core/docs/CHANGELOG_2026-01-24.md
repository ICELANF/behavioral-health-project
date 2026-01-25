# Metabolic Core 开发纪事 - 2026-01-24

> 行健行为教练 · 代谢慢病行为健康决策系统内核

---

## 今日工作概要

本日主要完成了**教练认证体系模块**的完整实现，以及三个核心数据结构的扩展。

---

## 一、数据结构扩展

### 1.1 MetabolicFeatureSet (代谢特征集)

**文件:** `src/trajectory/TrajectorySchema.ts`

用于表型匹配和风险预测的多时间窗口代谢特征集。

```typescript
interface MetabolicFeatureSet {
  feature_id: string;
  time_window: '24h' | '3d' | '7d' | '14d';
  glucose_features: {
    fasting_mean: number;
    postprandial_peak: number;
    time_to_peak: number;
    variability_cv: number;
    night_hypo_count: number;
  };
  hrv_features?: { rmssd_mean, lf_hf_ratio, recovery_score };
  activity_features?: { steps_mean, sedentary_ratio };
}
```

### 1.2 ProgramProtocol (项目协议)

**文件:** `src/libraries/InterventionPlaybook.ts`

结构化干预项目定义，支持14天标准化干预路径。

```typescript
interface ProgramProtocol {
  protocol_id: 'glucose_14d_basic' | string;
  target_profile: string[];
  duration_days: number;
  daily_plan: {
    day: number;
    assessment_hooks: string[];
    interventions: string[];
    coach_dialogue_templates: string[];
    expected_metrics: string[];
  }[];
  graduation_rules: { required_metrics, min_adherence_rate, stage_requirement };
}
```

### 1.3 UserLatentProfile (用户潜在画像)

**文件:** `src/trajectory/TrajectorySchema.ts`

综合用户状态评估，用于个性化干预匹配。

```typescript
interface UserLatentProfile {
  user_id: string;
  metabolic_risk_level: 'low' | 'medium' | 'high';
  dominant_phenotypes: string[];
  behavior_stage: BehaviorStage;
  motivation_level: number;  // 0-100
  adherence_tendency: 'strong' | 'medium' | 'weak';
  stress_load: 'low' | 'medium' | 'high';
  update_log: { timestamp, field, old_value, new_value, reason }[];
}
```

---

## 二、教练认证体系模块 (核心工作)

### 2.1 模块概述

**来源文档:** `D:\行为健康教练认证体系 · 工程级系统规范.txt`

**模块目录:** `src/certification/`

**设计目标:**
- 构建可持续输出高质量行为健康教练的人才流水线
- 与主动行为健康中枢共享评估、画像、干预、追踪能力
- 实现"内容—能力—认证—任务—收益—晋级"正循环系统

### 2.2 五级认证体系

| 等级 | 名称 | 定位 | 分成比例 | 可服务人群 |
|------|------|------|----------|------------|
| **L0** | 公众学习者 | 免费入口层 | 0% | - |
| **L1** | 初级行为健康教练 | 助理级，执行标准路径 | 30% | 低风险 |
| **L2** | 中级行为健康教练 | 独立上岗，平台主力 | 50% | 低/中风险 |
| **L3** | 高级行为健康教练 | 专项/慢病专家级 | 65% | 全部风险等级 |
| **L4** | 行为健康督导/讲师/专家 | 方法论中枢，核心师资 | 75% | 全部风险等级 |

### 2.3 K-M-S-V 四维能力模型

```
┌─────────────────────────────────────────────────────────────┐
│                    K-M-S-V 能力模型                          │
├─────────────────┬───────────────────────────────────────────┤
│ Knowledge       │ 行为科学 · 代谢医学 · 生活方式医学          │
│ (知识体系)      │ 心理动机理论 · 数据指标解读                 │
├─────────────────┼───────────────────────────────────────────┤
│ Method          │ 行为评估方法 · 阶段模型(TTM/COM-B)          │
│ (方法体系)      │ 行为处方设计 · 干预路径拆解 · 复盘调整      │
├─────────────────┼───────────────────────────────────────────┤
│ Skill           │ 动机访谈(MI) · 教练式对话 · 阻抗处理        │
│ (核心技能)      │ 目标拆解 · 陪伴反馈 · 平台工具使用          │
├─────────────────┼───────────────────────────────────────────┤
│ Value           │ 主动健康观 · 行为改变伦理                   │
│ (观念心智)      │ 边界角色认知 · 长程陪伴理念                 │
└─────────────────┴───────────────────────────────────────────┘
```

### 2.4 文件清单

| 文件 | 功能 | 代码行数 |
|------|------|----------|
| `CertificationSchema.ts` | 核心数据结构定义 | ~350行 |
| `CertificationService.ts` | 认证服务 (课程/考试/案例管理) | ~450行 |
| `PromotionEngine.ts` | 晋级判定引擎 | ~350行 |
| `index.ts` | 模块导出 | 8行 |

### 2.5 核心数据结构

**CoachProfile (教练档案)**
```typescript
interface CoachProfile {
  coach_id: string;
  user_id: string;
  name: string;
  level: CertificationLevel;           // L0-L4
  specialty_tags: SpecialtyTag[];      // 专项方向
  competency: CoachCompetencyModel;    // K-M-S-V能力评分
  completed_courses: CompletedCourse[];
  passed_exams: PassedExam[];
  real_cases: string[];                // 案例ID列表
  quality_score: number;               // 0-100
  platform_rating: 'S'|'A+'|'A'|...|'D';
  agent_permissions: AgentPermission[];
  serviceable_risk_levels: ('low'|'medium'|'high')[];
  revenue_share_ratio: number;         // 分成比例
  mentoring_records: MentoringRecord[];
  status: 'active'|'inactive'|'suspended'|'pending_review';
}
```

**CoachCase (教练案例)**
```typescript
interface CoachCase {
  case_id: string;
  coach_id: string;
  user_id: string;                     // 客户ID
  risk_type: 'low'|'medium'|'high';
  intervention_path: { path_id, path_name, duration_days, phases };
  outcome_metrics: { metric, baseline, final, improvement_percent }[];
  supervisor_score?: number;
  dialogue_quality_score?: number;
  client_satisfaction?: number;
  status: 'ongoing'|'completed'|'abandoned';
}
```

### 2.6 预定义资源

**课程库 (18门)**
- L0: 2门 (行为健康入门、慢病与代谢基础)
- L1: 7门 (理论/方法/技能模块)
- L2: 9门 (代谢综合征、CGM深度解读、高级MI等)

**考试库 (12项)**
- 理论考试 (机考)
- 案例模拟考试
- 对话质控评估
- 专项笔试 (糖尿病逆转/高血压/体重管理)

**专项方向 (6个)**
- diabetes_reversal: 糖尿病逆转专项
- hypertension: 高血压专项
- weight_management: 体重管理专项
- stress_psychology: 心理压力专项
- metabolic_syndrome: 代谢综合征专项
- sleep_optimization: 睡眠优化专项

### 2.7 晋级判定引擎

**评估维度:**
1. 理论成绩 (权重因等级而异)
2. 技能评分 (案例模拟 + 对话评估)
3. 实战案例数量与质量
4. 平台评分等级
5. 督导评分 (L3+)
6. 带教记录 (L4)

**输出:**
- 是否允许晋级
- 缺失条件清单
- 推荐补修模块
- 授权新Agent权限

### 2.8 REST API 端点 (15个)

```
GET  /api/certification/levels              # 获取认证等级要求
GET  /api/certification/levels/:level       # 获取指定等级要求
POST /api/certification/coaches             # 创建教练档案
GET  /api/certification/coaches             # 获取教练列表
GET  /api/certification/coaches/:id         # 获取教练档案
GET  /api/certification/coaches/:id/cases   # 获取教练案例
POST /api/certification/coaches/:id/courses # 完成课程
POST /api/certification/coaches/:id/exams   # 通过考试
POST /api/certification/coaches/:id/cases   # 创建案例
GET  /api/certification/coaches/:id/evaluate # 评估晋级资格
POST /api/certification/coaches/:id/promote # 执行晋级
GET  /api/certification/courses             # 获取课程列表
GET  /api/certification/exams               # 获取考试列表
POST /api/certification/training-sessions   # 创建训练会话
```

---

## 三、测试验证

**测试脚本:** `scripts/test-certification.ts`

**测试结果:** 15/15 通过

```
============================================================
  教练认证体系测试 (Coach Certification System Test)
============================================================

--- 认证等级要求 ---
[PASS] 5个认证等级已定义

--- 课程库 ---
[PASS] 课程库已加载 (18门)

--- 考试库 ---
[PASS] 考试库已加载 (12项)

--- 教练档案管理 ---
[PASS] 教练档案创建成功
[PASS] 初始等级为L0
[PASS] 初始评分为C

--- 课程完成 ---
[PASS] 完成课程CRS-L0-K01
[PASS] 完成课程CRS-L0-K02

--- 考试通过 ---
[PASS] 通过入门考试 (85分)
[PASS] 低于及格线不通过 (70分)

--- 晋级评估 ---
[PASS] 晋级评估执行成功
[PASS] 目标等级为L1

--- 能力模型 (K-M-S-V) ---
[PASS] 能力模型已初始化

--- 智能陪练 ---
[PASS] 训练会话创建成功

--- 教练列表 ---
[PASS] 能获取教练列表

============================================================
  测试结果: 15 通过, 0 失败
============================================================
```

---

## 四、与主动行为健康中枢整合

### 4.1 共享能力
- 共用评估体系 (BAPS问卷系统)
- 共用干预路径库 (InterventionPlaybook)
- 共用行为模型 (BehaviorChangeEngine)
- 共用数据结构 (UserProfile/TrajectoryRecord)

### 4.2 教练即Agent设计
| 等级 | Agent角色 | 权限 |
|------|----------|------|
| L1 | 基础执行Agent | 基础评估Agent (execute) |
| L2 | 个性化干预Agent | 代谢干预Agent + 个性化计划 (execute) |
| L3 | 专项专家Agent | 全部Agent (configure) + 专项专家 |
| L4 | 策略督导Agent | 全部Agent (configure) + 规则共建 |

---

## 五、文件变更汇总

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 修改 | `src/trajectory/TrajectorySchema.ts` | 添加 MetabolicFeatureSet, UserLatentProfile |
| 修改 | `src/libraries/InterventionPlaybook.ts` | 添加 ProgramProtocol |
| 新增 | `src/certification/CertificationSchema.ts` | 认证体系数据结构 |
| 新增 | `src/certification/CertificationService.ts` | 认证服务 |
| 新增 | `src/certification/PromotionEngine.ts` | 晋级判定引擎 |
| 新增 | `src/certification/index.ts` | 模块导出 |
| 修改 | `src/api/routes.ts` | 添加15个认证API端点 |
| 新增 | `scripts/test-certification.ts` | 认证体系测试脚本 |
| 修改 | `PROJECT_CHRONICLE.md` | 更新项目纪事 |

---

## 六、后续工作建议

1. **智能陪练系统深化**
   - AI模拟客户对话
   - 自动生成阻抗场景
   - 教练话术评分引擎

2. **Dify工作流集成**
   - 创建认证评估工作流
   - 教练训练助手Agent
   - 案例复盘分析流程

3. **前端管理界面**
   - 教练后台管理系统
   - 学习进度可视化
   - 晋级路径图谱

---

*文档生成时间: 2026-01-24*
*模块版本: v1.0.0*
