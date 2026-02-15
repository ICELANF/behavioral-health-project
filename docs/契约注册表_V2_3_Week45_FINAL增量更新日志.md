# 契约注册表 V2.3 增量更新日志 — Week 4-5 体验版引擎+400分制考核

> 基线: V2.2 (Week 3) | 更新: V2.3 (Week 4-5 FINAL) | 日期: 2026-02-15
> 测试: 30/30 PASS | 全量回归: 119/119 PASS (W2: 55 + W3: 34 + W4-5: 30)

---

## 一、Week 4-5 交付总览

| 模块 | 契约来源 | 文件 | 测试 |
|------|---------|------|------|
| 体验版评估+AI试用+内容门控+功能矩阵 | Sheet③⑤⑩ | trial_engine.py | TRL×12 |
| 400分制考核系统 | Sheet⑪§5§10 | exam_400_engine.py | EXM×18 |
| **合计** | | **2 核心文件 + 1 测试** | **30 PASS** |

---

## 二、体验版评估+AI试用 (12 PASS)

### HF-20 快筛 (Sheet③+⑤)

| 规则 | 实现 | 测试 |
|------|------|------|
| 匿名游客不可用 | AccessTier.ANONYMOUS → NOT_ELIGIBLE | TRL-01 ✅ |
| 注册观察员限1次 | TrialUsageRecord.used_count ≤ 1 | TRL-02/03 ✅ |
| 成长者+完整权限 | TIER_LEVEL_MAP ≥ 1 → full_access | TRL-05 ✅ |
| 20题5维度 | 饮食×4+运动×4+睡眠×4+压力×4+习惯×4 | TRL-03 ✅ |
| 结果分级 | 优≥80/良60-79/需关注40-59/建议<40 | TRL-04 ✅ |
| 转化钩子 | 评估完成/建议完整评估 → CTA引导 | TRL-03 ✅ |

### AI 体验对话 (Sheet③+⑤)

| 规则 | 实现 | 测试 |
|------|------|------|
| 匿名不可用 | NOT_ELIGIBLE | TRL-06 ✅ |
| 限3轮 | MAX_TRIAL_ROUNDS = 3 | TRL-07 ✅ |
| 轮次策略 | R1探索 → R2分析+hint → R3价值展示+CTA | TRL-07 ✅ |
| 超限阻断 | round ≥ 3 → LIMIT_REACHED | TRL-07 ✅ |

### 内容等级门控 (Sheet⑤ v3.7.1)

| 规则 | 实现 | 测试 |
|------|------|------|
| L0-L5 分级 | user_level ≥ content_level → accessible | TRL-08 ✅ |
| 不可访问 | 隐藏body+video_url, 返回unlock提示 | TRL-09 ✅ |
| 批量过滤 | filter_content_list() | TRL-10 ✅ |

### 功能权限矩阵 (Sheet⑤ 全量 28项)

| 测试 | 覆盖 |
|------|------|
| TRL-11 | 匿名: 仅浏览T1, 无评估/AI/数据 |
| TRL-12 | 观察员: +体验HF20+AI试用; 教练: +处方+工作台; 促进师: +Agent创建 |

---

## 三、400分制考核系统 (18 PASS)

### 考核结构 (Sheet⑪ §5)

| 模块 | 满分 | 及格 | 方法 | 子模块 |
|------|------|------|------|--------|
| 理论知识 | 150 | ≥90 | 在线测评 | M1行为处方(40分)·M2五维方案(35分)·M3身份链(30分)·M4综合素养(45分) |
| 技能实践 | 150 | ≥90 | 案例+同行评审 | ≥10案例·≥3人S0-S4跃迁·可解释性≥0.8·处方实操·AI演练 |
| 综合素质 | 100 | ≥60 | 多维度 | 伦理100%(一票否决)·MI角色扮演·带教评估·转介模拟·7天挑战 |
| **合计** | **400** | **≥240** | | **且各模块≥单项及格线 且 伦理100%** |

### 核心规则验证

| 规则 | 实现 | 测试 |
|------|------|------|
| 伦理一票否决 | C1 < 100 → ethics_veto=True, 考核终止 | EXM-10 ✅ |
| 伦理无补考 | ethics_veto → get_retake → eligible=False | EXM-15 ✅ |
| 伦理通过 | C1 = 100 → ethics_passed=True | EXM-11 ✅ |
| 否决后阻断 | ethics_veto → 禁止提交/重新注册 | EXM-18 ✅ |
| 理论通过 | 各子模块≥min_score 且 总分≥90 | EXM-07 ✅ |
| 理论不及格 | 总分<90 → FAILED | EXM-08 ✅ |
| 理论重考 | max_retakes=1, 2次不过→延期6月 | EXM-13 ✅ |
| 技能无限积累 | retakes=999, 案例持续积累 | EXM-14 ✅ |
| 全量认证 | 三模块PASSED + 总分≥240 → CERTIFIED | EXM-12 ✅ |

### 三轨差异 (Sheet⑪ §10)

| 轨道 | 标识 | M0补课 | 积分 | 预计周期 | 测试 |
|------|------|--------|------|---------|------|
| A 分享者内生 | 🟢organic | 无 | 已有延续 | 10-12月 | EXM-04 ✅ |
| B 交费学员 | 🟠paid | M0 20学时 | 培训=成长分 | 3-6月 | EXM-05/16/17 ✅ |
| E 意向早标记 | 🔵intent | 无 | 正常成长轨 | 12-24月 | EXM-06 ✅ |

### API 端点 (+8)

| 端点 | 方法 | 功能 |
|------|------|------|
| /v1/trial/assessment/eligibility | GET | 体验评估资格 |
| /v1/trial/assessment/start | POST | 开始HF-20 |
| /v1/trial/assessment/submit | POST | 提交评估 |
| /v1/trial/ai-dialog/eligibility | GET | AI对话资格 |
| /v1/trial/ai-dialog/message | POST | 发送体验消息 |
| /v1/exam/enroll | POST | 注册考核 |
| /v1/exam/submit | POST | 提交模块成绩 |
| /v1/exam/status/{user_id} | GET | 考核全景 |

---

## 四、5周 MVP 全量指标

| 维度 | V2.0(W1) | V2.1(W2) | V2.2(W3) | V2.3(W4-5) |
|------|----------|----------|----------|------------|
| 测试通过 | 424+20 | +55 (479) | +34 (513) | +30 (**119** 新增) |
| API端点 | 626 | +12 (638) | +5 (643) | +8 (**651**) |
| 核心引擎 | 观察员+积分+审计 | 双轨晋级+防刷 | 阶段+责任+治理+约束 | 体验版+400分制 |
| 契约覆盖 | Sheet①②⑦⑧⑩ | Sheet④⑦⑩ | Sheet⑥⑩⑪§3§9 | Sheet③⑤⑩⑪§5§10 |

### 交叉集成全景

```
访客入口 (W4-5)
  ├─ 体验HF-20 (限1次) → 转化引导
  ├─ AI体验对话 (限3轮) → 转化引导
  └─ 内容L0-L5门控 → 解锁引导
        ↓ 注册/升级
成长者 S0-S5 (W3)
  ├─ StageEngine: 6阶段状态机
  ├─ 90天稳定验证 (S4)
  └─ 毕业机制 (S5) → 可晋级分享者
        ↓ 积分+成长双轨
双轨晋级 L0→L5 (W2)
  ├─ DualTrackChecker: 积分轨+成长轨
  ├─ AntiCheatPipeline: AS-01~06 防刷
  ├─ PeerTracking: 4同道者质量
  └─ GapAnalyzer: 4状态差距报告
        ↓ L2→L3 教练认证
400分制考核 (W4-5)
  ├─ 理论150 (M1-M4) + 技能150 + 综合100
  ├─ 伦理100% 一票否决
  ├─ 三轨差异: A内生/B交费/E意向
  └─ 重考规则: 理论1次/技能无限/伦理无补考
        ↓ 认证后
责任追踪 (W3)
  ├─ 34条责任: 5角色自动追踪
  ├─ KPI红绿灯: 10项实时监控
  └─ 告警升级: 红色→Admin/督导
        ↓ 违规时
约束退出 (W3)
  ├─ 5类违规分级: -20/-100/-300/清零/不扣
  ├─ 保护期: 新晋级3月首次免罚
  └─ 退出: 自愿冻结12月/伦理永久取消
```

---

## 五、交付文件总清单

### Week 4-5 (本次)
1. `trial_engine.py` — 体验评估HF-20 + AI试用3轮 + 内容门控 + 功能矩阵
2. `exam_400_engine.py` — 400分制考核 + 伦理否决 + 三轨 + 重考 + API
3. `test_week45.py` — 30测试 (TRL×12 + EXM×18)

### 全5周累计 (15文件)
W1: observer_tiers, governance_config, incentive_engine, audit_logger (4)
W2: dual_track_engine, peer_tracking, promotion_api, anti_cheat_engine, anti_cheat_api (5+tests)
W3: stage_engine, StageVisualization.jsx, responsibility_tracker, governance_dashboard, constraint_exit (5+tests)
W4-5: trial_engine, exam_400_engine (2+tests)
