# BATCH-009-INDEX
## BHP知识库 BATCH-009 批次索引

**批次状态**：✅ 已完成  
**处理日期**：2026-03-08  
**来源文档**：1份（《Nutrition Therapy & Pathophysiology》，约400万字）  
**生成KI数量**：4个  

---

## 来源文档信息

| 字段 | 内容 |
|------|------|
| 书名 | Nutrition Therapy & Pathophysiology（第3版） |
| 作者 | Nelms M, Sucher KP, Lacey K, Roth SL |
| 出版社 | Cengage Learning |
| 定位 | 美国注册营养师（RD）核心教材 |
| 字数 | 约400万字，涵盖全疾病谱营养治疗 |
| 批次策略 | 按慢性病模块拆分，聚焦BHP平台高频场景 |

---

## 本批次生成KI清单

| KI ID | 标题 | 领域 | 证据级 | 适用阶段 | 价值层 | Chunks估计 |
|-------|------|------|--------|---------|--------|-----------|
| KI-NUTR-CVD-001 | 心血管疾病营养治疗循证指南：高血压/血脂异常/动脉粥样硬化综合干预 | clinical | T2(C) | S1-S4 | L1+L2 | 8-10 |
| KI-NUTR-DM-001 | 2型糖尿病营养治疗循证指南：血糖管理/碳水计数/饮食模式综合干预 | clinical | T1(A) | S1-S4 | L1+L2+L3 | 8-10 |
| KI-NUTR-OBE-001 | 肥胖/超重营养治疗与行为策略：能量平衡/饮食模式/行为疗法综合指南 | clinical | T1(A) | S0-S4 | L1+L2 | 8-10 |
| KI-NUTR-NCP-001 | 营养照护流程（NCP）框架：营养评估/诊断/干预/监测四步法与BHP整合 | clinical | T2(C) | S0-S6 | L1+L2 | 6-8 |

---

## 领域覆盖分析

### 疾病维度覆盖

```
本批次临床营养KI覆盖的慢性病场景：

  心血管疾病（CVD）← KI-NUTR-CVD-001
    ├── 高血压（DASH饮食/减盐）
    ├── 血脂异常（LDL/HDL/TG分型干预）
    ├── 动脉粥样硬化（心脏保护性饮食）
    └── 心力衰竭（钠/液体管理）

  2型糖尿病（T2DM）← KI-NUTR-DM-001
    ├── 碳水化合物计数/GI管理
    ├── 糖尿病前期逆转（DPP方案）
    └── 饮食模式选择（地中海/低碳）

  肥胖/超重 ← KI-NUTR-OBE-001
    ├── 能量平衡/热量管理
    ├── 行为疗法（自我监测/环境设计）
    └── 减重维持策略

  营养评估流程 ← KI-NUTR-NCP-001
    ├── NCP四步法（评估→诊断→干预→监测）
    └── BHP平台各模块整合路径
```

### 与既有KI的协同关系

```
营养KI集群（BATCH-009）与其他批次KI的联动：

  KI-NUTR-CVD-001 联动：
    ← KI-EX-NBA-001（运动处方：有氧运动降血压）
    ← KI-TCM-WUYUN-001（五运六气：冬季CVD管理）
    → KI-NUTR-DM-001（CVD+DM最高频组合）

  KI-NUTR-DM-001 联动：
    ← KI-EX-NBA-001（运动：餐后血糖管理）
    ← KI-BH-SWITCH-001（改变障碍：先菜后饭行为改变）
    → KI-NUTR-OBE-001（DM+超重：同时体重和血糖目标）

  KI-NUTR-OBE-001 联动：
    ← KI-EX-NBA-001（抗阻训练：维持基础代谢）
    ← KI-OBE-PEDI-001（成人肥胖←→儿童肥胖家庭干预）
    ← KI-BH-SWITCH-001（路径原理：食物环境设计）

  KI-NUTR-NCP-001 联动：
    → 所有NUTR KI（NCP是营养评估的框架骨架）
    → XZB CoachAgent问询流程（实现载体）
    → behavior_rx营养模块（输出载体）
```

---

## 平台模块整合标注

```
BHP各模块营养KI调用路径：

  XZB（行诊智伴）
    问询触发词 → KI-NUTR-* → 个性化营养建议
    NCP框架 → CoachAgent营养评估问询逻辑

  BehaviorOS核心平台
    BAPS评估（营养维度）→ 匹配KI-NUTR-*
    behavior_rx营养处方 → M-Action清单输出

  VisionGuard（青少年视力）
    NCP框架扩展 → 视力营养素评估
    （omega-3/叶黄素/维生素A）

  H5应用
    用户面向的营养教育内容 → KI-NUTR-*的话术变体库
```

---

## 向量化入库规划

```
Qdrant入库参数统一：
  collection: bhp_domain_behavioral
  embedding_dim: 1024
  
  本批次预估总切片数：30-38个切片
  
  建议入库优先级：
  P1（立即入库）：
    KI-NUTR-CVD-001（高血压/血脂——最高频CVD场景）
    KI-NUTR-DM-001（T2DM——中国慢性病第一大类）
    KI-NUTR-OBE-001（肥胖——平台核心用户痛点）
  
  P2（随后入库）：
    KI-NUTR-NCP-001（专业框架——平台内部使用优先）
```

---

## BATCH-009 完成小结

### 知识库价值增量
1. **临床营养覆盖完整化**：填补了此前知识库缺乏系统性营养治疗指南的空白
2. **三大高频慢性病完整覆盖**：CVD/T2DM/肥胖——中国慢性病最高发三类
3. **专业流程框架入库**：NCP四步法为平台营养模块提供标准化作业规范
4. **BHP整合标注完整**：每个KI均明确标注与XZB/VisionGuard/BAPS/behavior_rx的整合点

### 待生成KI（同来源文档，BATCH-010候选）
```
《Nutrition Therapy & Pathophysiology》尚未覆盖的高价值模块：
  [ ] KI-NUTR-RENAL-001：慢性肾病营养治疗（低蛋白/限钾/限磷）
  [ ] KI-NUTR-GOUT-001：痛风/高尿酸营养治疗（低嘌呤饮食）
  [ ] KI-NUTR-CANCER-001：癌症营养支持（恶病质/化疗期营养）
  [ ] KI-NUTR-ELDERLY-001：老年营养（肌少症/营养不良风险）
  [ ] KI-NUTR-SCREEN-001：营养筛查工具（MNA/MST/NRS2002）
```

---

## 累计知识库状态更新

| 批次 | KI数量 | 主要覆盖领域 | 状态 |
|------|--------|------------|------|
| BATCH-001至005 | ~18 | 代谢/运动/营养/L1底座/TCM/行为/临床 | ✅ |
| BATCH-006 | 2 | WRAP决策/SMCP四型性格 | ✅ |
| BATCH-007 | 3 | 希思兄弟行为设计学（峰值/改变/传播）| ✅ |
| BATCH-008 | 5 | 教练工具/TCM本草/儿童BMI/五运六气/体能 | ✅ |
| **BATCH-009** | **4** | **临床营养治疗（CVD/DM/肥胖/NCP）** | **✅** |
| **合计** | **~32** | | |

---

*BHP知识库建设 | BATCH-009-INDEX | v1.0 | 2026-03-08*
