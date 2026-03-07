---
document_version: v1.0
knowledge_id_prefix: KI-DM-CGM
source_name: 《中国血糖监测临床应用指南（2021年版）》解读
source_publish_date: 2021-10
ingest_date: 2026-03-04
evidence_tier: T1
scope: domain
authority_level: A
domain_prefix: DM-CGM
applicable_agents: [MetabolicAgent, CoachCopilotAgent]
pack_grade: C级（待影子专家审核）
review_cycle: 12个月
next_review_date: 2027-03-04
tags: [糖尿病, 血糖监测, CGM, HbA1c, TIR, SMBG, 血糖管理]
---

# 中国血糖监测临床应用指南（2021）知识库

## 元数据

- **证据来源**: 中华医学会糖尿病学分会，中华糖尿病杂志2021年10月第13卷第10期
- **覆盖范围**: 毛细血管血糖监测 / HbA1c / 糖化白蛋白 / CGM（含扫描式CGM）
- **推荐等级**: A级基于多项RCT/Meta；B级基于单项RCT；C级基于专家共识

---

## KI-DM-CGM-001｜血糖监测方法总览

```yaml
knowledge_id: KI-DM-CGM-001
title: 糖尿病血糖监测方法分类与选择原则
life_dimension: MONITORING
applicable_stages: [S2, S3, S4, S5, S6]
evidence_tier: T1
tags: [血糖监测, 监测方法, 个体化]
retrieval_queries:
  - 糖尿病如何监测血糖？
  - 血糖监测有哪些方法？
  - 什么时候用CGM？
```

糖尿病血糖监测分四种方法：
1. **毛细血管血糖（SMBG/POCT）**——指尖采血，是基础监测形式
2. **HbA1c**——反映2-3个月平均血糖，≥6.5%可作补充诊断标准
3. **糖化白蛋白（GA）**——反映近2-3周血糖，肾病/溶血等HbA1c不准时使用
4. **CGM（持续葡萄糖监测）**——分回顾性/实时/扫描式三类，可捕捉全天波动

**教练核心应用**：根据患者病情、意愿和依从性选择个体化方案，**不存在统一标准方案**。

---

## KI-DM-CGM-002｜血糖仪准确度标准

```yaml
knowledge_id: KI-DM-CGM-002
title: 便携式血糖仪准确度与精密度要求
life_dimension: MONITORING
applicable_stages: [S3, S4, S5]
evidence_tier: T1
tags: [血糖仪, 准确度, 精密度, WS/T781]
retrieval_queries:
  - 血糖仪的误差允许多少？
  - 血糖仪测量结果准不准？
  - 血糖仪什么时候需要校准？
```

依据国家卫生行业标准 WS/T 781-2021：

**准确度要求**（与实验室结果比较）：
- 血糖 <5.5 mmol/L：95%结果偏差在 **±0.83 mmol/L** 以内
- 血糖 ≥5.5 mmol/L：95%结果偏差在 **±15%** 以内

**精密度要求**（同一样本重复测量）：
- 血糖 <5.5 mmol/L：标准差 <0.42 mmol/L
- 血糖 ≥5.5 mmol/L：变异系数（CV）<7.5%

> 🔔 **教练行动指令**：若用户反映不同时间同一血糖仪差异>2 mmol/L，提示精密度问题，建议更换或检测血糖仪。

---

## KI-DM-CGM-003｜SMBG监测频率个体化原则

```yaml
knowledge_id: KI-DM-CGM-003
title: 自我血糖监测频率的个体化原则
life_dimension: MONITORING
applicable_stages: [S2, S3, S4, S5]
evidence_tier: T1
tags: [SMBG, 监测频率, 个体化, 血糖波动]
retrieval_queries:
  - 血糖一天应该测几次？
  - 什么情况需要增加血糖监测次数？
  - 血糖稳定还需要每天测吗？
```

**总体原则**：根据患者病情和治疗需求制定，不再推荐统一固定方案（2021年版新变化）。

**需增加监测频率的情况**：
- 血糖波动较大
- 使用胰岛素治疗
- 近期有低血糖发生（**≤3.9 mmol/L**）
- 正在调整药物或剂量
- 妊娠期患者
- 出现感染、手术等应激情况

**可适当减少频率的情况**：血糖控制稳定、生活规律、非胰岛素治疗。

> ⚠️ **安全铁律**：血糖 <3.9 mmol/L（低血糖）须立即处理，不能等下次测量。

---

## HI-DM-CGM-001｜核心血糖监测指标与阈值

```yaml
knowledge_id: HI-DM-CGM-001
title: 糖尿病血糖管理核心监测指标阈值
life_dimension: MONITORING
applicable_stages: [S2, S3, S4, S5, S6]
evidence_tier: T1
tags: [HbA1c, TIR, 低血糖, 高血糖, 阈值]
retrieval_queries:
  - 糖化血红蛋白正常值是多少？
  - TIR目标是多少？
  - 血糖多少算低血糖？
```

| 指标 | 含义 | 目标值（成人非妊娠T2DM） | 阈值预警 |
|------|------|-------------------|---------| 
| **HbA1c** | 2-3月平均血糖 | <7%（一般）;<8%（老年/高危）| ≥8%→医疗干预 |
| **TIR** | 血糖在3.9-10.0 mmol/L的时间比例 | **>70%** | <50%→干预升级 |
| **低血糖时间** | 血糖<3.9 mmol/L的时间比例 | **<4%** | >4%→立即排查 |
| **高血糖时间** | 血糖>10.0 mmol/L的时间比例 | <25% | >25%→方案调整 |
| **空腹血糖** | 禁食8h+ | 4.4-7.0 mmol/L | >7.0→复测 |
| **餐后2h血糖** | 进食2小时后 | <10.0 mmol/L | >11.1→关注 |

**具象化比喻**：TIR就像"达标温度的时间"——空调设了26度，真正维持在26°的时间越长越好。>70%意味着24小时中至少17小时血糖"达标"。

---

## HI-DM-CGM-002｜低血糖识别与分级

```yaml
knowledge_id: HI-DM-CGM-002
title: 低血糖分级标准与处理阈值
life_dimension: MONITORING
applicable_stages: [S2, S3, S4, S5, S6]
evidence_tier: T1
tags: [低血糖, 急性处理, 安全红线]
retrieval_queries:
  - 低血糖怎么判断？
  - 血糖多少需要立刻处理？
  - 出现心跳加速是低血糖吗？
```

**低血糖分级**（国际标准）：
- **1级（警戒低血糖）**: 血糖 3.0-3.9 mmol/L → 进食15g碳水（如3颗糖/半杯果汁），15分钟后复测
- **2级（临床显著低血糖）**: 血糖 **<3.0 mmol/L** → 立即进食，若无法进食应就医
- **3级（重度低血糖）**: 意识障碍或需他人帮助 → **立即拨120/就医**

**常见症状**（自主神经症状）：心悸、手抖、出汗、饥饿感、头晕

> 🔴 **CrisisAgent触发条件**：血糖 <2.8 mmol/L，或出现意识不清/无法进食 → 停止行为干预，立即联系医疗。

---

## KI-DM-CGM-004｜HbA1c解读与影响因素

```yaml
knowledge_id: KI-DM-CGM-004
title: HbA1c临床意义、诊断标准与影响因素
life_dimension: MONITORING
applicable_stages: [S2, S3, S4, S5]
evidence_tier: T1
tags: [HbA1c, 糖化血红蛋白, 诊断标准, 影响因素]
retrieval_queries:
  - 糖化血红蛋白是什么意思？
  - 为什么糖化血红蛋白和血糖不一致？
  - 糖化血红蛋白能诊断糖尿病吗？
```

**诊断意义**：HbA1c ≥6.5% 可作为糖尿病**补充诊断标准**（须使用标准化检测方法）。但 <6.5% 不能排除通过静脉血糖检测诊断的糖尿病。

**影响因素分两类**：
1. **与检测方法无关**：红细胞寿命（溶血性贫血↓HbA1c）、血红蛋白糖基化速率（长期高血糖↑）
2. **与检测方法有关**：血红蛋白病、异常血红蛋白、某些药物干扰

**教练话术示例**：
"糖化血红蛋白就像最近三个月的'平均成绩单'，每天测的血糖是'当天的小测验'，两个都要看，因为有人平时成绩好但期末失控，有人每次血糖波动但平均还可以。"

---

## KI-DM-CGM-005｜CGM解读三步法

```yaml
knowledge_id: KI-DM-CGM-005
title: CGM图谱解读三步法与AGP标准报告
life_dimension: MONITORING
applicable_stages: [S4, S5, S6]
evidence_tier: T1
tags: [CGM, AGP, TIR, 血糖波动, 图谱解读]
retrieval_queries:
  - CGM报告怎么看？
  - 动态血糖图谱如何解读？
  - 什么是时间在范围内？
```

**解读三步法**（新版指南推荐）：
1. **第一步**：看**低血糖风险**——TBR（血糖<3.9 mmol/L的时间）是否>4%？
2. **第二步**：看**高血糖**——TAR（血糖>10.0 mmol/L的时间）是否>25%？
3. **第三步**：看**血糖波动**——日内波动（CV%）和日间波动规律

**AGP报告解读要点**：
- 中位线（50%位数）= 代表"典型血糡水平"
- 10%-90%阴影区间越宽 = 血糖波动越大
- 找出每天固定的血糖"高峰"和"低谷"时段

> 📊 **操作化指令**：把AGP报告里"高于上虚线的红色区域"面积比例 = TAR；"低于下虚线的蓝色区域" = TBR。重点关注餐后2小时和凌晨2-4时的波动。

---

## KI-DM-CGM-006｜扫描式CGM（FGM）使用规范

```yaml
knowledge_id: KI-DM-CGM-006
title: 扫描式葡萄糖监测（FGM）适应证与使用规范
life_dimension: MONITORING
applicable_stages: [S3, S4, S5]
evidence_tier: T2
tags: [FGM, 扫描式血糖, 免指血, 传感器]
retrieval_queries:
  - 雅培扫描血糖仪怎么用？
  - 不用扎手指的血糖仪准确吗？
  - FGM和CGM有什么区别？
```

**FGM特点**：监测时间长（14天）、免指血校正、扫描读取（非自动传输）

**与实时CGM区别**：FGM无低血糖实时报警，用户需主动扫描查看；实时CGM可设置报警阈值。

**已有证据**：使用FGM可显著改善：
- 低血糖风险（减少低血糖时间）
- TIR（血糖在范围内时间增加）
- 血糖波动
- 用户满意度

**使用要点**：
- 传感器佩戴部位：上臂背侧（规范操作减少脱落）
- 避免高强度运动时、游泳时直接扫描（易影响结果）
- 两次指尖血校正建议：血糖变化快时（运动后/进食后）以指尖血为准

---

## IT-DM-CGM-001｜血糖自我监测行为养成干预模板

```yaml
knowledge_id: IT-DM-CGM-001
title: SMBG习惯养成行为干预处方
life_dimension: MONITORING
applicable_stages: [S2, S3, S4]
evidence_tier: T2
applicable_psych_levels: [L2, L3, L4]
applicable_bpt6: [action, knowledge, environment]
spi_minimum: 15
target_domain: monitoring
```

**Phase 1：微行为启动（第1-2周）**

目标：建立"固定时间测血糖"习惯锚点

| 场景 | 微行为 | 行为链锚定 |
|------|-------|----------|
| 早餐前 | 起床→喝水→**测空腹血糖**→吃早餐 | 把血糖仪放在水杯旁边 |
| 睡前 | 刷牙→**测睡前血糖**→充电 | 把血糖仪放在床头柜 |

**Phase 2：监测扩展（第3-4周）**

增加餐后2小时监测，记录进食内容与血糖对应关系。

**Phase 3：模式识别（第5-8周）**

- 识别个人"血糖升高食物清单"
- 识别"低血糖高风险时段"（通常为餐前/运动后）
- 建立个人化预警行动

**P1铁律**：监测数据须定期与医生/教练分享，**不得以数据代替医疗决策**。

---

## BM-DM-CGM-001｜血糖监测行为映射

```yaml
knowledge_id: BM-DM-CGM-001
title: 血糖监测行为阶段映射与触发规则
life_dimension: MONITORING
applicable_stages: [S1, S2, S3, S4, S5]
evidence_tier: T2
tags: [行为映射, TTM, 血糖监测, 触发条件]
```

| BehaviorFacts字段 | 含义 | 行动触发 |
|------------------|------|---------|
| glucose_log_7d | 近7天血糖记录次数 | <3次 → 教练提醒 + S2干预 |
| glucose_log_7d | 近7天血糖记录次数 | ≥7次 → S3进阶干预解锁 |
| low_glucose_event_72h | 72小时内低血糖事件 | 任意发生 → CrisisAlert → 医疗联动 |
| hba1c_last | 最近HbA1c值 | ≥8% → 医疗升级推荐 |
| tir_weekly | 周TIR | <50% → 干预方案评估 |

**阶段推进门槛**（MONITORING维度）：
- **S2→S3**：连续7天完成每日至少1次血糖记录
- **S3→S4**：连续14天，记录完整度≥80%，无漏测高危时段
- **S4→S5**：能独立识别个人血糖波动规律，无需教练提示

---

## 附：操作化锚定速查（傻瓜相机原则应用）

```
血糖数值具象化表达：
  🟢 血糖 3.9-10.0 = "绿灯区间"（正常）
  🟡 血糖 10.1-13.3 = "黄灯区间"（偏高，注意饮食运动）
  🔴 血糖 >13.3 = "红灯区间"（立即告知教练/医生）
  🔵 血糖 <3.9 = "蓝色警报"（低血糖，立即补糖）

HbA1c直观比喻：
  HbA1c 6% ≈ 平均血糖 7.0 mmol/L
  HbA1c 7% ≈ 平均血糖 8.6 mmol/L
  HbA1c 8% ≈ 平均血糖 10.2 mmol/L（需干预）
  HbA1c 9% ≈ 平均血糖 11.8 mmol/L（高风险）

TIR行为化表达：
  "今天你的血糖有几小时在绿灯区？超过17小时就达标了！"
  （24小时 × 70% ≈ 17小时）
```

---

*生成日期: 2026-03-04 | 规则版本: BHP v3.0 | 来源文档: 《中国血糖监测临床应用指南（2021年版）》解读*
