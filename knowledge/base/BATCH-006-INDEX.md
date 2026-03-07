# BHP知识库 · 批次入库索引

## BATCH-006 成就动机与激励理论批次

**入库日期**：2026-03-07  
**批次负责人**：Jack  
**来源文献**：3篇学术论文（成就动机/内在动机/组织管理理论）  
**BHP规则版本**：v4.0  

---

## 本批次知识条目清单

| KI编号 | 标题 | 领域 | TTM阶段 | 价值层 | 状态 |
|--------|------|------|--------|--------|------|
| `KI-BH-ACHIEVE-001` | 麦克利兰成就动机三需要理论与行为健康应用 | 行为健康理论 | S3,S4,S5 | 第二+三层 | ✅ 入库 |
| `KI-BH-INTRINSIC-001` | 内在动机与外在激励的关系模型及激励机制设计 | 行为健康理论 | S2,S3,S4,S5 | 第二+三层 | ✅ 入库 |
| `KI-GROWTH-ACHIEVE-001` | 成就动机框架在慢病康复叙事中的应用（S5-S6专属） | 成长超越 | S4,S5,S6 | **第三层（核心）** | ✅ 入库 |
| `KI-BH-XY-EXPECT-001` | XY理论与期望理论在行为健康教练实践中的整合应用 | 行为健康理论 | S1,S2,S3,S4 | 第一+二层 | ✅ 入库 |
| `KI-BH-MATURE-001` | 阿吉里斯"不成熟-成熟"理论与TTM行为变化阶段整合框架 | 行为健康理论 | S0-S5全阶段 | 第二+三层 | ✅ 入库 |

**本批次新增KI数量**：5条  
**累计KI总量**：约27条（原22+本批次5）

---

## 来源文献信息

| 序号 | 文献名 | 作者 | 机构 | 类型 |
|------|--------|------|------|------|
| 1 | HR论文：组织成就动机管理 | 李昌奕 | 南开大学国际商学院 | 研究生论文（2004年HR论文大赛优秀奖）|
| 2 | 内在动机与外在激励 | 蒲勇健、赵国强 | 重庆大学经济与工商管理学院 | 学术论文（含委托代理建模）|
| 3 | 组织成就动机管理（汇编） | 多位作者 | 多机构 | 理论汇编（含麦克利兰/本尼斯/阿吉里斯/麦格雷戈/弗鲁姆等经典理论）|

---

## 入库通过性检验记录

### v4.0四层漏斗检验

| KI编号 | 第一层（痛点解决）| 第二层（行为操作化）| 第三层（环境适应）| 第四层（成长超越）| 结论 |
|--------|----------------|------------------|----------------|----------------|------|
| KI-BH-ACHIEVE-001 | ✅ | ✅ | ✅ | ✅ | **入库** |
| KI-BH-INTRINSIC-001 | ✅ | ✅ | ✅ | ✅ | **入库** |
| KI-GROWTH-ACHIEVE-001 | — | — | ✅ | ✅ | **入库**（成长类，第三四层即可）|
| KI-BH-XY-EXPECT-001 | ✅ | ✅ | ✅ | — | **入库** |
| KI-BH-MATURE-001 | — | ✅ | ✅ | ✅ | **入库** |

### "奶奶测试"通过状态（操作化检验）

| KI编号 | 测试状态 | 说明 |
|--------|---------|------|
| KI-BH-ACHIEVE-001 | ✅ 通过 | 节点2话术可被60岁用户直接理解执行 |
| KI-BH-INTRINSIC-001 | ✅ 通过 | 节点1-3话术已完全转化为可对话的问句 |
| KI-GROWTH-ACHIEVE-001 | ⚠️ 豁免 | 成长类KI，适用"生命叙事检验"而非奶奶测试 |
| KI-BH-XY-EXPECT-001 | ✅ 通过 | 期望概率提升话术直接可用 |
| KI-BH-MATURE-001 | ✅ 通过 | 成熟度评估话术简洁可操作 |

### "生命叙事检验"（KI-GROWTH-ACHIEVE-001专属）

> **检验标准**：能否帮助用户说出"我以前从未这样看待自己/我的生活"？

✅ **通过**：通过提问3「你以前觉得自己没有毅力，现在你做到了这些，你还这么觉得吗？」大概率引出新的自我认知叙事。

---

## 向量化技术参数

```yaml
embedding_model: text-embedding-3-large  # 或平台指定模型
embedding_dimensions: 1024               # BHP KMS v4.0规定
chunk_strategy: semantic                 # 语义分块，按模块边界切割
chunk_size_tokens: 512-800              # 建议区间
overlap_tokens: 100

collection_mapping:
  KI-BH-ACHIEVE-001:   domain/behavioral/
  KI-BH-INTRINSIC-001: domain/behavioral/
  KI-GROWTH-ACHIEVE-001: domain/growth/
  KI-BH-XY-EXPECT-001: domain/behavioral/
  KI-BH-MATURE-001:   domain/behavioral/

scope:
  all: platform  # 全平台公共知识
  
metadata_fields:
  - ki_id
  - domain
  - ttm_stages
  - value_layer        # 1/2/3/12/23/123
  - growth_dimension   # discover_self / realize_self / transcend_self / null
  - evidence_level     # T1/T2/T3/T4
  - source
  - ingestion_date
  - has_reflection_prompts  # bool
  - has_identity_bridge     # bool
```

---

## 与现有知识库的关联图

```
本批次 BATCH-006
    │
    ├── KI-BH-ACHIEVE-001
    │   ├── 补充 BCTTv1（已入库）中的"目标设定"行为改变技术
    │   └── 为 BPT-6 P2/P4维度提供测量理论基础
    │
    ├── KI-BH-INTRINSIC-001
    │   ├── 与 SDT自我决定理论（已入库）互补（外在→内在动机迁移路径）
    │   └── 为"积分/奖励"系统设计提供使用边界依据
    │
    ├── KI-GROWTH-ACHIEVE-001
    │   ├── 与 BATCH-005 KI-MEANING-FRANKL-001（待建）深度关联
    │   ├── 直接为 L3情境 S11（S4→S5转折，待建）提供话术框架
    │   └── 与 KI-POSPSYCH-PERMA-001（待建）中"A=成就"维度共鸣
    │
    ├── KI-BH-XY-EXPECT-001
    │   ├── 为 CoachAgent风格切换逻辑（指令→赋权）提供理论支撑
    │   └── 与 Bandura自我效能理论（已入库）在"期望概率提升"上协同
    │
    └── KI-BH-MATURE-001
        ├── 与 TTM七阶段模型（已入库 base/ttm_stages.md）直接对应
        └── 为"平台终极目标：让用户不需要平台"提供理论证明
```

---

## 待补充建设项（本批次触发）

基于本批次入库内容，建议新增以下待建KI：

- [ ] `KI-BH-MCCLELLAND-MEASURE-001`：AMS成就动机量表在BHP评估中的应用（作为BAPS子量表补充）
- [ ] `L3-S11`：S4→S5转折识别情境包（优先级**P1**，本批次KI-GROWTH-ACHIEVE-001提供话术基础）
- [ ] `KI-GROWTH-IDENTITY-001`：从"我有糖尿病"到"我是健康生活者"的身份转型框架（与本批次高度互补）

---

## 质量自检清单

```
内容完整性：
  ☑ 所有KI均包含八模块标准结构（情境/逻辑/决策树/M-Action/监测/铁律/叠加/话术）
  ☑ 话术均为可直接使用的完整句子
  ☑ 铁律均附有原因说明
  ☑ 阈值均为具体数字

话术质量：
  ☑ 无说教语气（"你应该"替换为"你觉得"/"你想"）
  ☑ 无空洞鼓励（"加油！你能行！"等表达已删除）
  ☑ 有具体情境触发条件

成长类KI（KI-GROWTH-ACHIEVE-001）专项：
  ☑ growth_dimension已标注
  ☑ reflection_prompts ≥ 3个
  ☑ identity_bridge有明确表述
  ☑ applicable_life_events ≥ 2个
  ☑ 标注S0-S2的限制性使用说明
  ☑ 通过生命叙事检验
```
