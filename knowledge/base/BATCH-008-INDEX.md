# BATCH-008-INDEX
## BHP知识库 第八批次（BATCH-008）知识项索引

```yaml
batch_id: BATCH-008
created: 2026-03-08
source_documents: 5份
ki_count: 5
status: COMPLETED
operator: Jack（BehaviorOS创始人）
rule_version: BHP KMS v4.0
cumulative_ki_total: 27（BATCH-001至BATCH-008）
```

---

## 一、来源文档映射

| # | 来源文档 | 类型 | 字数约 | 生成KI | 说明 |
|---|---------|------|--------|--------|------|
| 1 | 56版中医中药名称功能.docx | 中医本草学教材 | 52,000字 | KI-TCM-HERBS-001 | 提取慢性病相关品种 |
| 2 | 6岁_8岁学龄儿童青少年性别年龄BMI筛查超重与肥胖界值.doc | 国家卫生标准（WS/T 586-2018）| 700字（数据表）| KI-OBE-PEDI-001 | T1级临床参考标准 |
| 3 | 60年运气交司表.docx | TCM五运六气经典 | 8,700字 | KI-TCM-WUYUN-001 | 季节性行为处方框架 |
| 4 | 76个经典教练模型.docx | 教练能力系统综述 | 122,000字 | KI-COACH-76M-001 | 提取12个BHP核心模型 |
| 5 | NBＡ体能训练.docx | 专项体能训练参考 | 61,800字 | KI-EX-NBA-001 | 适配慢性病用户 |

---

## 二、BATCH-008知识项目录

| KI ID | 标题 | 领域 | 证据级 | 价值层 | TTM适用 | 核心用途 |
|-------|------|------|--------|--------|---------|---------|
| **KI-COACH-76M-001** | 76个经典教练模型精华：CoachAgent行为激活与成长促进工具矩阵 | behavioral | T3(D) | 第二+三+四层 | S0-S6全段 | CoachAgent核心工具库（GROW/Egan/Rogers/内化游戏/Bateson等12个关键模型）|
| **KI-TCM-HERBS-001** | 56味经典本草精要：慢性病行为健康TCM辅助干预速查指南 | tcm | T3(D) | 第一+二层 | S1-S4 | 药食同源食材行为整合；TCM慢病辅助干预参考 |
| **KI-OBE-PEDI-001** | 中国儿童青少年BMI超重肥胖筛查标准（6-18岁）与行为干预触发决策树 | clinical | T1(A) | 第一+二层 | S0-S3 | VisionGuard联动；家长慢病+儿童体重双线干预 |
| **KI-TCM-WUYUN-001** | 五运六气框架：TCM自然节律与行为健康季节性干预矩阵 | tcm | T3(D) | 第二+三层 | S3-S5 | 六节气段行为处方；高文化认同度的季节性干预 |
| **KI-EX-NBA-001** | NBA体能训练要素精华：运动处方中的功能性体能模块设计指南 | exercise | T3(D) | 第一+二层 | S2-S4 | 临床运动处方的具体执行层；五大体能要素L1-L3 |

---

## 三、入库检验汇总

| KI | 四层筛选 | 奶奶测试 | 意义层检验 | v4.0铁律 |
|----|---------|---------|---------|---------|
| KI-COACH-76M-001 | ✅ 第二+三+四层 | ✅ 通过 | ✅ Bateson/Mezirow服务S4-S6 | ✅ 铁律7B/C/D |
| KI-TCM-HERBS-001 | ✅ 第一+二层 | ✅ 通过 | N/A（非成长类）| ✅ 铁律4/critical_disclaimer |
| KI-OBE-PEDI-001 | ✅ 第一+二层 | ✅ 通过 | N/A | ✅ 铁律4/A/C |
| KI-TCM-WUYUN-001 | ✅ 第二+三层 | ✅ 通过 | 部分适用（秋季成就回顾S4+）| ✅ 铁律1/A/B |
| KI-EX-NBA-001 | ✅ 第一+二层 | ✅ 通过 | N/A | ✅ 铁律1/A/B/C/E |

---

## 四、向量化参数汇总

| KI | collection | chunk_strategy | 预估切片数 |
|----|-----------|---------------|---------|
| KI-COACH-76M-001 | bhp_domain_behavioral | per_category（3类工具）| 12-15个 |
| KI-TCM-HERBS-001 | bhp_domain_behavioral | per_category（4类功效）| 8-10个 |
| KI-OBE-PEDI-001 | bhp_domain_behavioral | per_section（BMI表/决策树/处方）| 4-6个 |
| KI-TCM-WUYUN-001 | bhp_domain_behavioral | per_season（六节气段）| 8-10个 |
| KI-EX-NBA-001 | bhp_domain_behavioral | per_component（热身+5要素+计划）| 8-10个 |

**所有KI统一参数**：embedding_dim=1024（BHP KMS v4.0规定）

---

## 五、领域覆盖分析

```
BATCH-008新增覆盖：

  behavioral（教练工具）：
    KI-COACH-76M-001 ← 首次入库完整教练工具矩阵
    意义：CoachAgent终于有了系统性的工具库，而不只是理论框架

  tcm（中医）：
    KI-TCM-HERBS-001 ← 首次入库本草学参考（药食同源重点）
    KI-TCM-WUYUN-001 ← 首次入库五运六气季节性干预
    意义：TCM域从"体质评估"扩展到"日常干预"和"季节节律"

  clinical（临床）：
    KI-OBE-PEDI-001 ← 首次入库儿童/青少年专项标准
    意义：平台覆盖延伸至青少年和家庭单元

  exercise（运动）：
    KI-EX-NBA-001 ← 运动处方执行层补充
    意义：从"知道要运动"到"知道怎么训练"
```

---

## 六、模块联动图谱（BATCH-008新增联动）

```
VisionGuard模块
    ↕ 联动
KI-OBE-PEDI-001（青少年BMI标准）
    ↕ 联动
家庭慢病管理（父母行为改变 × 子女体重干预）

TCMAgent
    ↕ 联动（体质评估结果）
KI-TCM-HERBS-001（药食同源选品）
    ↕ 叠加
KI-TCM-WUYUN-001（季节时机选择）

CoachAgent
    ↕ 调用
KI-COACH-76M-001（全阶段工具矩阵）
    ↕ 配合
KI-EX-NBA-001（运动执行层支持）

ExerciseAgent
    ↕ 原则框架
临床运动处方KI（BATCH-05以前入库）
    ↕ 执行细节
KI-EX-NBA-001（具体动作/组数/进阶）
```

---

## 七、BATCH-009建议优先项

根据BATCH-008完成情况，以下为下一批次建议方向：

**P1（高优先）**：
- [ ] `KI-POSPSYCH-PERMA-001`：Seligman PERMA幸福五元素 + S5行为设计（KMS v4.0附录G标注）
- [ ] `KI-MEANING-FRANKL-001`：弗兰克尔意义治疗框架 + 意义探索对话工具
- [ ] `KI-ACT-VALUES-001`：ACT价值观澄清技术

**P2（中优先）**：
- [ ] `KI-COACH-76M-002`：76个模型第三部分精华——团队发展/变革管理（Kotter八步/悲伤曲线等）
- [ ] `KI-TCM-CONSTITUTION-SEASONAL`：九种体质×六节气干预矩阵（体质KI与运气KI的深度整合）

**P3（参考资料归档）**：
- [ ] 《56版中医中药名称功能》全文作为参考档案保留，后续如有特定病种中药研究需求可深入提取

---

## 八、累计知识库状态（BATCH-008完成后）

| 批次 | KI数量 | 主要覆盖领域 | 状态 |
|------|--------|------------|------|
| BATCH-001至003 | ~10 | 代谢/运动/营养/L1底座 | ✅ |
| BATCH-004 | ~3 | TCM/中医体质 | ✅ |
| BATCH-005 | ~5 | 行为/心理/临床 | ✅ |
| BATCH-006 | 3 | 决策框架（WRAP）/性格（SMCP）| ✅ |
| BATCH-007 | 3+1索引 | 希思兄弟行为设计学四部曲（PEAK/SWITCH/STICK）| ✅ |
| **BATCH-008** | **5+1索引** | **教练工具/TCM本草/儿童BMI/五运六气/体能训练** | **✅** |

**累计KI总量：约27个**（含L1底座4个、L2领域23个，不含L3情境包）

---

*BHP知识库 BATCH-008批次索引 | v1.0 2026-03-08*
