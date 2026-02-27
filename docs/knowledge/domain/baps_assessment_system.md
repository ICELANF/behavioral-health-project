# 评估系统知识库
> BAPS（行为评估与处方系统）v2.0 · 知识库整合文档  
> 编译日期：2026-02-26  
> 涵盖内容：5大评估工具 · 171题完整题库 · 评分算法 · 状态机逻辑 · 报告模板

---

## 目录

1. [系统架构总览](#一系统架构总览)
2. [评估工具索引](#二评估工具索引)
3. [T1：大五人格测评（BIG5）](#三t1大五人格测评big5)
4. [T2：行为模式分型（BPT6）](#四t2行为模式分型bpt6)
5. [T3：改变阶段评估（TTM7）](#五t3改变阶段评估ttm7)
6. [T4：改变潜力诊断（CAPACITY）](#六t4改变潜力诊断capacity)
7. [T5：成功可能性评估（SPI）](#七t5成功可能性评估spi)
8. [评分算法与引擎](#八评分算法与引擎)
9. [状态机与策略闸门](#九状态机与策略闸门)
10. [BAPS状态驱动逻辑](#十baps状态驱动逻辑)
11. [综合报告模板](#十一综合报告模板)
12. [API接口规范](#十二api接口规范)

---

## 一、系统架构总览

### 1.1 系统定位

BAPS（Behavior Assessment & Prescription System）是一套基于大五人格理论和跨理论模型（TTM）的行为评估与处方系统，核心用途：

- 识别个体行为模式类型（BPT6）
- 评估改变阶段和准备度（TTM7）
- 诊断改变潜力（CAPACITY）
- 预测成功可能性（SPI）
- 生成个性化干预处方

适用场景：行为健康促进、慢病逆转、健康管理

### 1.2 评估工具矩阵

| 编号 | 工具名称 | 代码 | 题数 | 评估维度 | 核心产出 |
|:---:|----------|------|:---:|----------|----------|
| T1 | 大五人格测评 | BIG5 | 50 | 5维度×6情境 | 人格画像 |
| T2 | 行为模式分型 | BPT6 | 18 | 6种类型，各3题 | 行为类型 |
| T3 | 改变阶段评估 | TTM7 | 21 | 7阶段，各3题 | 当前阶段 |
| T4 | 改变潜力诊断 | CAPACITY | 32 | 8维度，各4题 | 潜力指数 |
| T5 | 成功可能性评估 | SPI | 50 | 5维度，各10题 | 成功概率 |
| — | **合计** | — | **171** | — | — |

### 1.3 评估流程

**完整流程（171题）：**
```
BIG5(50题) → BPT6(18题) → TTM7(21题) → CAPACITY(32题) → SPI(50题) → 综合报告
```

**快速流程（39题）：**
```
BPT6(18题) → TTM7(21题) → 快速处方匹配
```

### 1.4 阶段状态代码对照

| 系统代码 | 阶段名称 | TTM经典阶段 | 觉察度 | 意愿度 | 行动度 |
|---------|----------|------------|:-----:|:-----:|:-----:|
| S0 | 无知无觉 | 前意向期 | 0 | 0 | 0 |
| S1 | 强烈抗拒 | 前意向期 | 1 | 0 | 0 |
| S2 | 被动应对 | 意向期 | 2 | 1 | 0 |
| S3 | 勉强接受 | 准备期 | 3 | 2 | 1 |
| S4 | 尝试阶段 | 行动期（早期） | 4 | 3 | 2 |
| S5 | 主动实践 | 行动期 | 5 | 4 | 4 |
| S6 | 内化习惯 | 维持期 | 5 | 5 | 5 |

> **注意**：系统代码（S0–S6）用于 BehaviorRuntime 状态机；TTM7 问卷内部用 1–7 数字编号（TTM 第1阶段 = S0，第7阶段 = S6）。

---

## 二、评估工具索引

### 2.1 题号快查索引

| 问卷 | 题号范围 | 总题数 | 量表类型 |
|------|----------|:-----:|---------|
| BIG5 | E01–E10, N01–N10, C01–C10, A01–A10, O01–O10 | 50 | 双极-4~+4 |
| BPT6 | BPT01–BPT18 | 18 | Likert 1–5 |
| TTM7 | TTM01–TTM21 | 21 | Likert 1–5 |
| CAPACITY | CAP01–CAP32 | 32 | Likert 1–5 |
| SPI | SPI01–SPI50 | 50 | Likert 1–5 |

### 2.2 量表说明

**双极量表（BIG5专用）：**

| 分值 | 含义 |
|:---:|------|
| -4 | 完全不符合 |
| -3 | 很不符合 |
| -2 | 比较不符合 |
| -1 | 有些不符合 |
| 0 | 中立/不确定 |
| +1 | 有些符合 |
| +2 | 比较符合 |
| +3 | 很符合 |
| +4 | 完全符合 |

**Likert 5级量表（BPT6 / TTM7 / CAPACITY / SPI 通用）：**

| 分值 | 含义 |
|:---:|------|
| 1 | 完全不符合 |
| 2 | 不太符合 |
| 3 | 不确定 |
| 4 | 比较符合 |
| 5 | 完全符合 |

---

## 三、T1：大五人格测评（BIG5）

> 工具编号：T1 · 题目数量：50题 · 评分量表：双极 -4~+4

### 3.1 维度结构

| 维度 | 代码 | 题数 | 高分特征 | 低分特征 | 行为影响 |
|------|:---:|:---:|----------|----------|----------|
| 外向性 | E | 10 | 热情、社交、活力 | 内敛、独立、安静 | 社会支持偏好 |
| 神经质 | N | 10 | 敏感、焦虑、情绪化 | 稳定、冷静、抗压 | 情绪管理需求 |
| 尽责性 | C | 10 | 自律、有序、坚持 | 随性、灵活、即兴 | 执行力基础 |
| 宜人性 | A | 10 | 友善、合作、同理 | 竞争、独立、批判 | 关系依赖度 |
| 开放性 | O | 10 | 好奇、创新、审美 | 传统、务实、保守 | 接受新方法 |

**反向计分题：E03**（独自一人待一整天后，我会感到精力充沛）

### 3.2 题目完整列表

#### 外向性（E）10题

| 编号 | 题目 | 情境维度 | 反向 |
|------|------|---------|:---:|
| E01 | 在家庭聚会中，我通常是主动发起话题、活跃气氛的那个人 | 家庭 | 否 |
| E02 | 我每周需要与多个不同的朋友见面或深度交流才感到满足 | 人际 | 否 |
| E03 | 独自一人待一整天后，我会感到精力充沛、思路清晰 | 情绪 | **是** |
| E04 | 遇到问题时，我的第一反应是立即打电话找人倾诉和讨论 | 社会支持 | 否 |
| E05 | 户外活动中，我更喜欢热闹的团体运动而非独自徒步 | 自然环境 | 否 |
| E06 | 我经常主动组织家庭活动，并享受与家人的热闹相处时光 | 家庭 | 否 |
| E07 | 在陌生场合，我能轻松地与不认识的人开启对话 | 人际 | 否 |
| E08 | 我的快乐很大程度上来源于与他人的互动和共享体验 | 情绪 | 否 |
| E09 | 我从他人的认可和外部成就中获得人生意义感 | 精神价值 | 否 |
| E10 | 周末理想的状态是参加多个社交活动，而非宅在家中 | 人际 | 否 |

#### 神经质（N）10题

| 编号 | 题目 | 情境维度 |
|------|------|---------|
| N01 | 我经常担心可能发生的坏事，即使概率很小 | 情绪 |
| N02 | 家人的一个不经意的评论就可能让我情绪低落很久 | 家庭 |
| N03 | 遇到挫折后，我需要很长时间才能恢复到正常状态 | 情绪 |
| N04 | 我常常担心朋友是否真的喜欢我，或是否会突然离开我 | 人际 |
| N05 | 环境中的噪音、杂乱或不适会严重影响我的情绪状态 | 自然环境 |
| N06 | 我的情绪像过山车，经常在短时间内大起大落 | 情绪 |
| N07 | 压力大时，我会反复向不同的人倾诉同一件事以寻求安慰 | 社会支持 |
| N08 | 我经常质疑人生的意义，并因此感到焦虑或沮丧 | 精神价值 |
| N09 | 家庭中的小冲突会让我感到极度不安，难以继续正常生活 | 家庭 |
| N10 | 即使事情进展顺利，我也会担心下一刻可能出错 | 情绪 |

#### 尽责性（C）10题

| 编号 | 题目 | 情境维度 |
|------|------|---------|
| C01 | 我会提前规划家庭活动，并确保每个细节都安排妥当 | 家庭 |
| C02 | 完成目标和履行责任是我人生意义的核心来源 | 精神价值 |
| C03 | 我总是准时赴约，并且会提前到达约定地点 | 人际 |
| C04 | 我会持续执行环保行为（分类、节能等），即使麻烦也坚持 | 自然环境 |
| C05 | 未完成的任务会让我持续感到焦虑，难以放松享受休闲时光 | 情绪 |
| C06 | 我会坚持让家人遵守共同制定的规则和时间表 | 家庭 |
| C07 | 朋友找我帮忙时，我一定会尽全力完成我的承诺 | 社会支持 |
| C08 | 我对自己有很高的标准，并且会严厉批评自己的失误 | 精神价值 |
| C09 | 我的居住空间总是整洁有序，物品都有固定位置 | 自然环境 |
| C10 | 即使疲惫或情绪低落，我也会强迫自己完成计划中的任务 | 情绪 |

#### 宜人性（A）10题

| 编号 | 题目 | 情境维度 |
|------|------|---------|
| A01 | 家庭冲突中，我通常会选择妥协以维持和谐，即使牺牲自己的需求 | 家庭 |
| A02 | 我很难拒绝他人的请求，即使这会给我带来不便 | 人际 |
| A03 | 看到他人痛苦时，我会深深感受到他们的情绪，甚至影响自己的状态 | 情绪 |
| A04 | 我经常主动关心和帮助他人，即使他们没有开口求助 | 社会支持 |
| A05 | 我对动物和环境的苦难感到深深的悲伤和责任感 | 自然环境 |
| A06 | 我会压抑自己的愤怒或不满，以避免让家人不开心 | 家庭 |
| A07 | 在团队合作中，我更关注他人的感受而非任务的效率 | 人际 |
| A08 | 帮助他人和为社会做贡献是我人生最重要的价值追求 | 精神价值 |
| A09 | 即使他人对我不好，我也倾向于原谅并理解他们的难处 | 情绪 |
| A10 | 我给予他人的支持和帮助远远多于我向他人寻求的帮助 | 社会支持 |

#### 开放性（O）10题

| 编号 | 题目 | 情境维度 |
|------|------|---------|
| O01 | 我经常思考深层的哲学问题，如生命的意义、存在的本质等 | 精神价值 |
| O02 | 我鼓励家人尝试新事物、接触不同文化和非传统观念 | 家庭 |
| O03 | 在自然中，我会深刻体验到审美感动或与宇宙的连接感 | 自然环境 |
| O04 | 我被那些有独特思想和创造力的人深深吸引，即使他们很"怪" | 人际 |
| O05 | 我体验到复杂细腻的情感，有时难以用语言准确描述 | 情绪 |
| O06 | 我的信念和价值观在过去几年中经历了显著的改变和演进 | 精神价值 |
| O07 | 我会因为追求新的体验和机会而改变家庭的生活安排（如搬家、转行） | 家庭 |
| O08 | 我寻求的支持是对思想的理解和共鸣，而非实际的帮助 | 社会支持 |
| O09 | 艺术作品（音乐、画作、诗歌等）能够深深地触动我，甚至改变我的状态 | 情绪 |
| O10 | 我更愿意探索未知的、野生的自然环境，而非去熟悉的公园 | 自然环境 |

### 3.3 BIG5评分规则

- 每维度得分 = 10题累加（E03反向，计分时取负值）
- 得分范围：每维度 -40 ~ +40

| 得分范围 | 水平 |
|---------|:---:|
| +25 ~ +40 | 很高 |
| +10 ~ +24 | 偏高 |
| -9 ~ +9 | 中等 |
| -24 ~ -10 | 偏低 |
| -40 ~ -25 | 很低 |

### 3.4 人格-行为类型-阶段交叉对照

| 人格特征组合 | 倾向行为类型 | 阶段路径特点 |
|------------|-----------|------------|
| 高E + 高C | 行动型 | S4→S5→S6 快速推进，挑战性目标有效 |
| 高O + 低C | 知识型 | S3→S4 容易卡顿，需MVP启动策略 |
| 高N + 高O | 情绪型 | 阶段反复震荡，情绪管理优先 |
| 高E + 高A | 关系型 | 需要伴随支持，伙伴机制驱动 |
| 中等各维度 | 环境型 | 主动性弱，需要环境设计 |
| 高N + 中等 | 矛盾型 | S1–S3 循环，ACT技术+小步实验 |

---

## 四、T2：行为模式分型（BPT6）

> 工具编号：T2 · 题目数量：18题 · 评分：Likert 1–5 · 每类型3题

### 4.1 六种行为类型定义

| 类型 | 代码 | 人格基础 | 改变优势 | 改变风险 | 最佳教练姿态 |
|------|:---:|---------|---------|---------|------------|
| 行动型 | ACT | 高C+低N | 执行力强，快速启动 | 过度行动，跳步 | 设置清晰边界 |
| 知识型 | KNO | 高O+低C | 理解深入，洞察力好 | 分析瘫痪，准备过度 | MVP实验框架 |
| 情绪型 | EMO | 高N+高O | 感受敏锐，变化动力强 | 情绪波动，难以持续 | 情绪-行动解耦 |
| 关系型 | REL | 高E+高A | 社会支持充足 | 过度依赖他人 | 陪伴+渐进独立 |
| 环境型 | ENV | 各维度中等 | 适应性强 | 缺乏内在主动 | 环境设计优先 |
| 矛盾型 | AMB | 高N | 自省能力强 | 持续犹豫，循环放弃 | ACT技术+微承诺 |

### 4.2 题目完整列表

#### 行动型（ACT）— 3题

| 编号 | 题目 |
|------|------|
| BPT01 | 面对问题，我通常会立即采取行动而不是过多思考 |
| BPT02 | 我习惯于先做再说，在行动中调整方向 |
| BPT03 | 即使信息不完整，我也能快速做决策并承担风险 |

#### 知识型（KNO）— 3题

| 编号 | 题目 |
|------|------|
| BPT04 | 我需要充分理解原理和机制后才愿意行动 |
| BPT05 | 我会花大量时间研究方法，但常常"准备过度" |
| BPT06 | 我的书签/收藏夹里有大量健康资料但很少实践 |

#### 情绪型（EMO）— 3题

| 编号 | 题目 |
|------|------|
| BPT07 | 我的行为很大程度上取决于当时的情绪状态 |
| BPT08 | 我会因为感动/恐惧而冲动改变，但激情消退后难坚持 |
| BPT09 | 情绪低落时，我完全失去改变的动力 |

#### 关系型（REL）— 3题

| 编号 | 题目 |
|------|------|
| BPT10 | 我需要有人陪伴/监督才能坚持健康行为 |
| BPT11 | 他人的认可和鼓励是我最大的动力来源 |
| BPT12 | 如果朋友/家人不支持，我很难独自坚持 |

#### 环境型（ENV）— 3题

| 编号 | 题目 |
|------|------|
| BPT13 | 我的行为很容易受到周围环境的影响 |
| BPT14 | 在支持性环境中我表现很好，但环境变化后立即反弹 |
| BPT15 | 我很难主动创造条件，更习惯"条件具备了再说" |

#### 矛盾型（AMB）— 3题

| 编号 | 题目 |
|------|------|
| BPT16 | 我既想改变又害怕改变，内心充满矛盾 |
| BPT17 | 我经常在"开始—放弃—重新开始"中循环 |
| BPT18 | 我总能找到不行动的合理借口 |

### 4.3 BPT6评分规则

- 每类型得分 = 3题累加，范围 3–15
- 分型判定：

| 条件 | 分型 |
|------|------|
| 单一类型 ≥ 12分 | 纯型（主导型） |
| 两种类型均 ≥ 10分 | 混合型 |
| 所有类型 7–9分 | 分散型（需访谈） |

---

## 五、T3：改变阶段评估（TTM7）

> 工具编号：T3 · 题目数量：21题 · 每阶段3题 · 含3个子维度

### 5.1 七阶段详细定义

| 阶段编号 | 代码 | 阶段名称 | TTM对应 | 核心特征 | 典型语言 |
|:-------:|:---:|---------|---------|---------|---------|
| 1 | S0 | 无知无觉 | 前意向期 | 完全无觉察 | "我没问题啊" |
| 2 | S1 | 强烈抗拒 | 前意向期 | 否认、拒绝 | "这跟我没关系" |
| 3 | S2 | 被动应对 | 意向期 | 被动承认 | "好吧，可能有点问题" |
| 4 | S3 | 勉强接受 | 准备期 | 矛盾挣扎 | "我知道该改，但是…" |
| 5 | S4 | 尝试阶段 | 行动期（早期） | 小范围探索 | "我试试看" |
| 6 | S5 | 主动实践 | 行动期 | 持续执行 | "我正在坚持做" |
| 7 | S6 | 内化习惯 | 维持期 | 自动化、身份整合 | "这就是我的生活方式" |

### 5.2 阶段干预策略矩阵

| 阶段 | 干预重点 | 推荐技术 | 禁忌 | 预期时长 |
|------|---------|---------|------|---------|
| S0 无知无觉 | 提升觉察 | 健康教育、风险告知、体检反馈 | 直接要求改变 | 2–4周 |
| S1 强烈抗拒 | 建立关系 | 动机访谈、非评判倾听 | 说教、施压 | 2–4周 |
| S2 被动应对 | 激发矛盾 | 探索利弊、价值观澄清 | 急于给方案 | 2–4周 |
| S3 勉强接受 | 制定计划 | 目标设定、行动计划、承诺强化 | 过高期望 | 1–2周 |
| S4 尝试阶段 | 支持行动 | 技能训练、问题解决、即时反馈 | 过早撤离支持 | 4–8周 |
| S5 主动实践 | 维持巩固 | 习惯堆叠、环境设计、自我监测 | 忽视复发风险 | 4–8周 |
| S6 内化习惯 | 防止复发 | 身份强化、应对高风险情境 | 放松警惕 | 持续 |

### 5.3 题目完整列表

> 子维度：AW = 觉察度，WI = 意愿度，AC = 行动度

#### S0 无知无觉 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM01 | 我从来没有觉得自己的[目标行为]有什么问题 | AW |
| TTM02 | 别人说我需要改变，但我完全不理解为什么 | WI |
| TTM03 | 我的生活方式一直这样，从没想过要改变什么 | AC |

#### S1 强烈抗拒 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM04 | 我知道别人认为我应该改变，但我觉得没必要 | AW |
| TTM05 | 有人建议我改变时，我会感到反感或被冒犯 | WI |
| TTM06 | 我认为坚持现在的方式没什么不好，不需要改变 | AC |

#### S2 被动应对 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM07 | 我承认可能有些问题，但还没有认真考虑改变 | AW |
| TTM08 | 如果有人帮我安排好一切，我可能会尝试改变 | WI |
| TTM09 | 我偶尔会想到应该改变，但很快就忘了 | AC |

#### S3 勉强接受 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM10 | 我清楚地知道自己需要做出改变 | AW |
| TTM11 | 我已经决定要改变，正在考虑具体怎么做 | WI |
| TTM12 | 我计划在近期（一个月内）开始采取行动 | AC |

#### S4 尝试阶段 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM13 | 我已经开始尝试新的行为，虽然还不太稳定 | AW |
| TTM14 | 我在努力坚持，但有时候会中断或放弃 | WI |
| TTM15 | 我的改变还需要刻意提醒自己才能做到 | AC |

#### S5 主动实践 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM16 | 我已经持续执行新行为超过一个月了 | AW |
| TTM17 | 我对自己的改变感到满意，并有信心继续下去 | WI |
| TTM18 | 我能够应对大多数阻碍，保持行为的一致性 | AC |

#### S6 内化习惯 — 3题

| 编号 | 题目 | 子维度 |
|------|------|:-----:|
| TTM19 | 这个行为已经成为我生活的自然组成部分 | AW |
| TTM20 | 我已经把自己看作是"那样的人"（如健康的人、自律的人） | WI |
| TTM21 | 即使遇到困难或诱惑，我也几乎不会回到旧习惯 | AC |

### 5.4 TTM7评分规则

- 每阶段得分 = 3题累加，范围 3–15
- **阶段判定逻辑**：早期阶段（1–3）高分优先；否则取后期（4–7）最高分阶段
- **准备度指数公式**：各阶段加权求和后归一化至0–100

```
weights = {1: -3, 2: -2, 3: -1, 4: 0, 5: +1, 6: +2, 7: +3}
readiness = (Σ(stage_score × weight) + 90) / 180 × 100
```

| 阶段得分 | 判定条件 |
|---------|---------|
| ≥ 12分 | 该阶段为当前主导阶段 |
| 10–11分 | 次要阶段特征 |
| < 10分 | 该阶段特征不明显 |

---

## 六、T4：改变潜力诊断（CAPACITY）

> 工具编号：T4 · 题目数量：32题 · 8维度×4题 · CAPACITY首字母缩写

### 6.1 CAPACITY八维度定义

| 字母 | 维度名称 | 英文 | 核心含义 | 薄弱表现 |
|:---:|---------|------|---------|---------|
| C | 觉察力 | Consciousness | 对自身行为模式的认知与反思 | 不知道触发因素 |
| A | 自主感 | Autonomy | 改变源自内在真实动力 | 被迫改变，没有内驱 |
| P | 匹配度 | Personality Match | 改变方式与个性特点适配 | 用不适合的方式强迫自己 |
| A | 行动资源 | Action Resources | 时间、经济、知识、环境等 | 资源不足，条件不够 |
| C | 承诺水平 | Commitment | 面对困难的持续意志 | 遇挫即放弃 |
| I | 身份认同 | Identity | 改变是否与理想自我一致 | 改变与自我形象矛盾 |
| T | 时间视角 | Timeline | 对改变周期的合理预期 | 急于求成，等待奇迹 |
| Y | 收益期待 | Yield Expectation | 对付出与收益比的现实评估 | 期望过高容易失望 |

### 6.2 题目完整列表

#### C1 觉察力（Consciousness）— 4题

| 编号 | 题目 |
|------|------|
| CAP01 | 我清楚知道哪些情境会触发我的不健康行为 |
| CAP02 | 我能准确描述自己当前的行为模式 |
| CAP03 | 我理解现在的行为如何影响我的未来健康 |
| CAP04 | 我经常反思自己的选择和后果 |

#### A1 自主感（Autonomy）— 4题

| 编号 | 题目 |
|------|------|
| CAP05 | 这个改变是我自己真心想要的，不是为了取悦他人 |
| CAP06 | 我相信自己能够掌控这个改变过程 |
| CAP07 | 即使没有外部监督，我也会坚持 |
| CAP08 | 我对改变有强烈的内在动力 |

#### P 匹配度（Personality Match）— 4题

| 编号 | 题目 |
|------|------|
| CAP09 | 我找到了适合自己性格的改变方式 |
| CAP10 | 我的改变策略与我的生活习惯相融合 |
| CAP11 | 改变方案考虑了我的个人特点 |
| CAP12 | 我不需要强迫自己用不适合的方式改变 |

#### A2 行动资源（Action Resources）— 4题

| 编号 | 题目 |
|------|------|
| CAP13 | 我有足够的时间来执行改变计划 |
| CAP14 | 我有必要的经济条件支持改变 |
| CAP15 | 我具备所需的知识和技能 |
| CAP16 | 我的环境条件有利于改变 |

#### C2 承诺水平（Commitment）— 4题

| 编号 | 题目 |
|------|------|
| CAP17 | 我愿意为这个改变投入时间和精力 |
| CAP18 | 面对挫折我会坚持而非放弃 |
| CAP19 | 我已经向重要的人公开了我的改变计划 |
| CAP20 | 我有明确的阶段性目标和期限 |

#### I 身份认同（Identity）— 4题

| 编号 | 题目 |
|------|------|
| CAP21 | 这个改变与我理想中的自己是一致的 |
| CAP22 | 我愿意成为"那样的人"（如健康的人、自律的人） |
| CAP23 | 改变后的行为会让我更接近真正的自己 |
| CAP24 | 我能接受改变带来的身份转变 |

#### T 时间视角（Timeline）— 4题

| 编号 | 题目 |
|------|------|
| CAP25 | 我对改变所需的时间有合理的预期 |
| CAP26 | 我能接受在一段时间内看不到明显效果 |
| CAP27 | 我有长期坚持的心理准备 |
| CAP28 | 我理解习惯养成需要时间 |

#### Y 收益期待（Yield Expectation）— 4题

| 编号 | 题目 |
|------|------|
| CAP29 | 我对改变的预期收益是现实的 |
| CAP30 | 我认为付出与收益比是可接受的 |
| CAP31 | 我清楚改变会给我带来哪些具体好处 |
| CAP32 | 我不会因为期望过高而失望 |

### 6.3 CAPACITY评分规则

- 每维度得分 = 4题累加，范围 4–20
- 薄弱维度标准：维度得分 < 12分

| 维度得分 | 水平 |
|---------|:---:|
| 16–20 | 高 ★★★★★ |
| 12–15 | 中高 ★★★★☆ |
| 8–11 | 中等 ★★★☆☆ |
| 4–7 | 较低 ★★☆☆☆ |

| 总分（满分160） | 潜力等级 |
|--------------|---------|
| ≥ 128 | 高潜力 |
| 96–127 | 中高潜力 |
| 64–95 | 中等潜力 |
| < 64 | 需要准备 |

---

## 七、T5：成功可能性评估（SPI）

> 工具编号：T5 · 题目数量：50题 · MASEH模型 · 加权计分

### 7.1 MASEH五维度与权重

| 字母 | 维度 | 英文 | 题数 | 权重 | 含义 |
|:---:|-----|------|:---:|:---:|------|
| M | 动机 | Motivation | 10 | 30% | 内在驱动力强度 |
| A | 能力 | Ability | 10 | 25% | 知识、技能、自我效能 |
| S | 支持 | Support | 10 | 20% | 社会支持网络 |
| E | 环境 | Environment | 10 | 15% | 物理与社会环境条件 |
| H | 历史 | History | 10 | 10% | 过去成功/失败经验 |

**SPI公式：** `SPI = M×0.30 + A×0.25 + S×0.20 + E×0.15 + H×0.10`

### 7.2 题目完整列表

#### M 动机（Motivation）— SPI01–SPI10

| 编号 | 题目 |
|------|------|
| SPI01 | 我真心想要做出这个改变 |
| SPI02 | 这个改变对我的生活非常重要 |
| SPI03 | 我已经准备好现在就开始改变 |
| SPI04 | 这个改变是我自己的决定，不是被迫的 |
| SPI05 | 我相信这个改变会给我带来好处 |
| SPI06 | 我有明确的改变目标 |
| SPI07 | 我对改变充满期待 |
| SPI08 | 我愿意为改变付出代价 |
| SPI09 | 改变的理由对我来说很有意义 |
| SPI10 | 我的内心驱动力很强 |

#### A 能力（Ability）— SPI11–SPI20

| 编号 | 题目 |
|------|------|
| SPI11 | 我知道具体应该怎么做 |
| SPI12 | 我有足够的知识来支持这个改变 |
| SPI13 | 我具备必要的技能 |
| SPI14 | 我有过类似的成功经验 |
| SPI15 | 我相信自己能够做到 |
| SPI16 | 我知道如何应对可能的困难 |
| SPI17 | 我能够监测自己的进展 |
| SPI18 | 我知道何时需要调整策略 |
| SPI19 | 我有能力解决过程中的问题 |
| SPI20 | 我对自己的执行力有信心 |

#### S 支持（Support）— SPI21–SPI30

| 编号 | 题目 |
|------|------|
| SPI21 | 有人会支持我的改变 |
| SPI22 | 我能获得专业的指导 |
| SPI23 | 遇到困难时有人可以帮助我 |
| SPI24 | 我的家人理解并支持我 |
| SPI25 | 我有可以一起改变的伙伴 |
| SPI26 | 我知道去哪里寻求帮助 |
| SPI27 | 我有获取信息和资源的渠道 |
| SPI28 | 我周围有成功的榜样 |
| SPI29 | 我能得到情感上的支持 |
| SPI30 | 我的社交圈对改变持正面态度 |

#### E 环境（Environment）— SPI31–SPI40

| 编号 | 题目 |
|------|------|
| SPI31 | 我的物理环境有利于改变 |
| SPI32 | 我有足够的时间来执行计划 |
| SPI33 | 我有必要的工具和设备 |
| SPI34 | 我的工作/生活条件允许改变 |
| SPI35 | 我的经济状况支持这个改变 |
| SPI36 | 我生活中的诱惑因素已减少 |
| SPI37 | 我的环境中有提醒和线索 |
| SPI38 | 我有合适的时间段来执行 |
| SPI39 | 我的空间条件支持新行为 |
| SPI40 | 外部障碍已经被识别和处理 |

#### H 历史（History）— SPI41–SPI50

| 编号 | 题目 |
|------|------|
| SPI41 | 我过去有过成功改变的经历 |
| SPI42 | 我从过去的失败中学到了经验 |
| SPI43 | 我知道什么方法对我有效 |
| SPI44 | 我了解自己容易在哪里失败 |
| SPI45 | 我有应对复发的经验 |
| SPI46 | 我的改变历史让我更有信心 |
| SPI47 | 我知道自己的行为模式 |
| SPI48 | 我了解自己的触发因素 |
| SPI49 | 我能识别自己的高风险情境 |
| SPI50 | 我比过去更了解自己 |

### 7.3 SPI评分解读

| SPI分数（满分50） | 成功概率 | 建议策略 |
|----------------|---------|---------|
| ≥ 40 | > 75% | 可挑战高目标 |
| 30–39 | 50–75% | 稳步推进 |
| 20–29 | 30–50% | 降低难度，加强支持 |
| 10–19 | 15–30% | 从微习惯起步 |
| < 10 | < 15% | 暂缓，先解决前置问题 |

---

## 八、评分算法与引擎

### 8.1 BIG5评分（Python参考实现）

```python
def score_big5(answers: dict) -> dict:
    """
    answers: {"E01": 3, "E02": -1, ...}  # 值域 -4 ~ +4
    returns: {"E": 15, "N": -8, "C": 22, "A": 10, "O": 18}
    """
    reverse_items = ["E03"]
    dimensions = {
        "E": [f"E{i:02d}" for i in range(1, 11)],
        "N": [f"N{i:02d}" for i in range(1, 11)],
        "C": [f"C{i:02d}" for i in range(1, 11)],
        "A": [f"A{i:02d}" for i in range(1, 11)],
        "O": [f"O{i:02d}" for i in range(1, 11)],
    }
    results = {}
    for dim, items in dimensions.items():
        total = sum(-answers.get(i, 0) if i in reverse_items else answers.get(i, 0) for i in items)
        results[dim] = total
    return results
```

### 8.2 BPT6评分（Python参考实现）

```python
def score_bpt6(answers: dict) -> dict:
    """
    返回: {"dominant": "关系型", "secondary": "情绪型", "pattern": "混合型", "scores": {...}}
    """
    type_items = {
        "行动型": ["BPT01","BPT02","BPT03"],
        "知识型": ["BPT04","BPT05","BPT06"],
        "情绪型": ["BPT07","BPT08","BPT09"],
        "关系型": ["BPT10","BPT11","BPT12"],
        "环境型": ["BPT13","BPT14","BPT15"],
        "矛盾型": ["BPT16","BPT17","BPT18"],
    }
    scores = {t: sum(answers.get(i, 0) for i in items) for t, items in type_items.items()}
    dominant = [t for t, s in scores.items() if s >= 12]
    secondary = [t for t, s in scores.items() if 10 <= s < 12]
    if len(dominant) == 1 and not secondary:
        pattern = "纯型"
    elif len(dominant) >= 1 or len(secondary) >= 2:
        pattern = "混合型"
    else:
        pattern = "分散型"
    return {"scores": scores, "dominant": dominant, "secondary": secondary, "pattern": pattern}
```

### 8.3 TTM7评分（Python参考实现）

```python
def score_ttm7(answers: dict) -> dict:
    """
    返回: {"current_stage": 5, "stage_name": "尝试阶段", "readiness_index": 68.5, ...}
    注意：TTM7内部用1–7编号，对应S0–S6
    """
    stages = {i: [f"TTM{(i-1)*3+j:02d}" for j in range(1,4)] for i in range(1,8)}
    stage_scores = {s: sum(answers.get(i, 0) for i in items) for s, items in stages.items()}
    
    # 优先检查早期阶段（1-3）
    current = None
    for s in range(1, 4):
        if stage_scores[s] >= 12:
            current = s
            break
    if current is None:
        for s in range(7, 0, -1):
            if stage_scores[s] >= 12:
                current = s
                break
    if current is None:
        current = max(stage_scores, key=stage_scores.get)
    
    # 准备度指数
    weights = {1:-3, 2:-2, 3:-1, 4:0, 5:1, 6:2, 7:3}
    weighted_sum = sum(stage_scores[s] * weights[s] for s in range(1,8))
    readiness = round((weighted_sum + 90) / 180 * 100, 1)
    
    names = {1:"无知无觉",2:"强烈抗拒",3:"被动应对",4:"勉强接受",5:"尝试阶段",6:"主动实践",7:"内化习惯"}
    return {"current_stage": current, "stage_name": names[current],
            "stage_scores": stage_scores, "readiness_index": readiness}
```

### 8.4 CAPACITY评分（Python参考实现）

```python
def score_capacity(answers: dict) -> dict:
    dims = {
        "C1_觉察力": ["CAP01","CAP02","CAP03","CAP04"],
        "A1_自主感": ["CAP05","CAP06","CAP07","CAP08"],
        "P_匹配度":  ["CAP09","CAP10","CAP11","CAP12"],
        "A2_资源":   ["CAP13","CAP14","CAP15","CAP16"],
        "C2_承诺":   ["CAP17","CAP18","CAP19","CAP20"],
        "I_身份":    ["CAP21","CAP22","CAP23","CAP24"],
        "T_时间":    ["CAP25","CAP26","CAP27","CAP28"],
        "Y_期待":    ["CAP29","CAP30","CAP31","CAP32"],
    }
    dim_scores = {d: sum(answers.get(i,0) for i in items) for d, items in dims.items()}
    total = sum(dim_scores.values())
    level_map = [(128,"高潜力"),(96,"中高潜力"),(64,"中等潜力"),(0,"需要准备")]
    level = next(l for t, l in level_map if total >= t)
    weak = [d for d, s in dim_scores.items() if s < 12]
    return {"dimension_scores": dim_scores, "total": total, "level": level, "weak_dimensions": weak}
```

### 8.5 SPI评分（Python参考实现）

```python
def score_spi(answers: dict) -> dict:
    dims = {
        "M": {"items": [f"SPI{i:02d}" for i in range(1,11)],  "weight": 0.30},
        "A": {"items": [f"SPI{i:02d}" for i in range(11,21)], "weight": 0.25},
        "S": {"items": [f"SPI{i:02d}" for i in range(21,31)], "weight": 0.20},
        "E": {"items": [f"SPI{i:02d}" for i in range(31,41)], "weight": 0.15},
        "H": {"items": [f"SPI{i:02d}" for i in range(41,51)], "weight": 0.10},
    }
    spi = sum(sum(answers.get(i,0) for i in d["items"]) * d["weight"] for d in dims.values())
    spi = round(spi, 2)
    interp = [(40,">75%","可挑战高目标"),(30,"50-75%","稳步推进"),
              (20,"30-50%","降低难度"),(10,"15-30%","微习惯起步"),(0,"<15%","暂缓行动")]
    prob, rec = next((p, r) for t, p, r in interp if spi >= t)
    return {"spi": spi, "success_probability": prob, "recommendation": rec}
```

---

## 九、状态机与策略闸门

> 来源：状态导入评估.txt — BehaviorRuntime + RuntimePolicyGate + BehaviorEngine

### 9.1 核心数据结构

```python
class BehaviorStage(Enum):
    S0 = "S0"  # 无意识期
    S1 = "S1"  # 抵触期
    S2 = "S2"  # 犹豫期
    S3 = "S3"  # 准备期
    S4 = "S4"  # 行动期
    S5 = "S5"  # 维护期
    S6 = "S6"  # 习惯化

class InteractionMode(Enum):
    EMPATHY   = "EMPATHY"    # 共情模式
    CHALLENGE = "CHALLENGE"  # 挑战模式
    EXECUTION = "EXECUTION"  # 执行模式

@dataclass
class BehaviorRuntime:
    current_stage:    BehaviorStage = BehaviorStage.S0
    stage_confidence: float = 0.0
    stage_stability:  str = "stable"   # stable | semi_stable | unstable
    stage_hypothesis: dict = field(default_factory=lambda: {
        "proposed_stage": None, "confidence": 0.0, "source": ""
    })
    risk_flags: list = field(default_factory=list)
```

### 9.2 RuntimePolicyGate — 四条核心规则

| 优先级 | 规则名称 | 触发条件 | 决策结果 |
|:-----:|---------|---------|---------|
| 1 | 不稳定态禁止强干预 | `stage_stability == "unstable"` | DELAY — 延迟干预 |
| 2 | 低阶段强制降级 | `current_stage in [S0, S1]` | ALLOW_SOFT_SUPPORT — 仅情感陪伴 |
| 3 | 高风险教练升级 | `"dropout_risk" in risk_flags AND stage >= S3` | ESCALATE_COACH — 人工介入 |
| 4 | 逻辑一致准予执行 | 其他情况 | ALLOW — 执行原始干预包 |

```python
class RuntimePolicyGate:
    def evaluate(self, runtime: BehaviorRuntime, recommended_pkg: str) -> PolicyDecision:
        if runtime.stage_stability == "unstable":
            return PolicyDecision(DELAY, "阶段极不稳定，延迟强力干预")
        if runtime.current_stage in [BehaviorStage.S0, BehaviorStage.S1]:
            return PolicyDecision(ALLOW_SOFT_SUPPORT, "低动机期，禁止指令输出，仅允许情感陪伴")
        if "dropout_risk" in runtime.risk_flags and runtime.current_stage.value >= "S3":
            return PolicyDecision(ESCALATE_COACH, "高阶用户脱落风险，触发专家介入",
                                  intervention="URGENT_COACH_ESCALATION")
        return PolicyDecision(ALLOW, "干预包与当前阶段匹配", intervention=recommended_pkg)
```

### 9.3 BehaviorEngine — 阶段跃迁逻辑

**核心设计原则：**
- Agent 只能提交"推测（hypothesis）"，不能直接修改 `current_stage`
- Engine 是唯一持有 SSOT 状态的主体
- 只有当推测置信度 > 0.9 时，Engine 才执行阶段跃迁
- 跃迁后稳定性自动降为 `semi_stable`

**执行流程：**
```
Agent 提交 proposal → Engine 记录 hypothesis
    → 置信度 > 0.9 → Engine 执行 _transition_stage
    → PolicyGate.evaluate() → 返回最终决策
    → _execute_decision() → 输出实际动作
```

**输出决策映射：**

| PolicyDecision | 实际输出 |
|---------------|---------|
| ALLOW | EXECUTE_ORIGINAL — 执行原始干预包 |
| ALLOW_SOFT_SUPPORT | REWRITE_TO_EMPATHY — 重写为温柔陪伴话术 |
| DELAY | 返回 delay 原因，不执行 |
| ESCALATE_COACH | 触发人工/专家 Agent 介入 |

---

## 十、BAPS状态驱动逻辑

> 来源：状态驱动.txt — BAPS逻辑映射元数据 + BapsScoreMapper

### 10.1 BAPS五维度逻辑映射

| 维度代码 | 含义 | 权重 | 跃迁阈值 |
|---------|------|:---:|---------|
| V1_AMB | 改变意愿/动机（Ambition） | 0.30 | ≥ 0.6 → 推 S2 |
| V2_EFF | 执行效能（Efficacy） | 0.25 | ≥ 0.7 → 推 S4 |
| V3_ENV | 环境支持（Environment） | 0.15 | 影响稳定性 |
| V4_CON | 承诺水平（Commitment） | 0.20 | ≥ 0.65 → 推 S3 |
| V5_ACT | 行动指数（Action） | 0.10 | ≥ 0.8 → 推 S5 |

### 10.2 BapsScoreMapper 阶段跃迁判定矩阵

```
输入：评估完成后的归一化向量 {"V1_AMB": 0.0–1.0, "V2_EFF": ..., ...}

判定逻辑（阶梯优先级）：
┌────────────────────────────────────────────────────────┐
│  if V1_AMB < 0.4                 → target = S1 (0.90)  │
│  if V1_AMB ≥ 0.6 AND V4_CON < 0.6  → target = S2 (0.85) │
│  if V4_CON ≥ 0.65 AND V2_EFF < 0.7 → target = S3 (0.80) │
│  if V2_EFF ≥ 0.70 AND V5_ACT < 0.8 → target = S4 (0.90) │
│  if V5_ACT ≥ 0.80               → target = S5 (0.85)   │
│  else                            → target = None (0.0)  │
└────────────────────────────────────────────────────────┘
```

### 10.3 ingest_baps_scores — 实时分数摄入方法

当用户完成部分题目或对话提取到分值时调用：

```python
def ingest_baps_scores(self, user_runtime: BehaviorRuntime, new_scores: dict):
    """
    平滑移动平均更新（防止单次波动）：
    new_value = old_value × 0.7 + new_score × 0.3
    
    只有当 BAPS 证据足够强（confidence > 0.7），才执行 SSOT 状态修改。
    """
    for key, value in new_scores.items():
        if key in user_runtime.baps_vector:
            user_runtime.baps_vector[key] = (user_runtime.baps_vector[key] * 0.7) + (value * 0.3)
    
    drive = BapsScoreMapper.calculate_stage_drive(user_runtime.baps_vector)
    
    if drive["target"] and drive["confidence"] > 0.7:
        target_stage = BehaviorStage(drive["target"])
        if target_stage != user_runtime.current_stage:
            self._transition_stage(user_runtime, target_stage)
            user_runtime.stage_confidence = drive["confidence"]
```

**设计要点：** BIG5/BPT6/TTM7/CAPACITY/SPI的归一化得分 → BAPS五维度向量 → BapsScoreMapper → 推荐阶段 → Engine 决定是否跃迁

---

## 十一、综合报告模板

### 11.1 报告数据结构（JSON Schema）

```json
{
  "report_id": "RPT-20260226-001",
  "user_id": "string",
  "assessment_date": "2026-02-26",
  "target_behavior": "每日运动30分钟",
  
  "executive_summary": {
    "overall_readiness": "中高",
    "success_probability": "50-75%",
    "key_strengths": ["动机强", "支持充足"],
    "key_challenges": ["能力待提升", "环境需改善"],
    "recommended_approach": "渐进式启动，重点加强技能培训"
  },
  
  "big5": {
    "E": {"score": 15, "level": "偏高"},
    "N": {"score": -5, "level": "中等"},
    "C": {"score": 8,  "level": "中等"},
    "A": {"score": 20, "level": "偏高"},
    "O": {"score": 12, "level": "偏高"},
    "profile_summary": "社交型、合作性强、对新事物开放，但自律性需外部支持"
  },
  
  "bpt6": {
    "dominant_type": "关系型",
    "secondary_type": "情绪型",
    "coaching_approach": "陪伴式支持 + 情绪管理技能"
  },
  
  "ttm_stage": {
    "current_stage": 5,
    "stage_name": "尝试阶段",
    "ttm_equivalent": "准备期",
    "readiness_index": 68.5
  },
  
  "capacity": {
    "total_score": 112,
    "level": "中高潜力",
    "weak_dimensions": ["A2_资源"],
    "capacity_index": 70.0
  },
  
  "spi": {
    "spi_score": 35.6,
    "success_probability": "50-75%",
    "recommendation": "稳步推进"
  },
  
  "personalized_prescription": {
    "goal_type": "关系嵌入型目标",
    "primary_goal": "与伙伴一起每周运动3次，每次30分钟",
    "milestones": [
      "第1周：找到运动伙伴，确定时间",
      "第2-3周：完成4次运动",
      "第4周：建立稳定规律"
    ],
    "core_strategies": ["社交嵌入", "情绪缓冲", "环境设计"],
    "tracking_method": "情绪+行为日记",
    "review_frequency": "每周回顾"
  },
  
  "risk_alerts": [
    {"risk": "独自时难以坚持", "probability": "高", "prevention": "提前安排替代支持方案"},
    {"risk": "情绪低落时放弃", "probability": "中", "prevention": "建立「情绪低≠不运动」认知"}
  ]
}
```

### 11.2 Markdown报告模板（教练使用版）

```markdown
# 行为评估综合报告 · {report_id}

评估日期：{date} | 目标行为：{target_behavior}

---
## 执行摘要
- 整体准备度：{overall_readiness}
- 成功可能性：{success_probability}
- 核心优势：{key_strengths}
- 主要挑战：{key_challenges}
- 建议方向：{recommended_approach}

---
## 一、人格画像（BIG5）
| 维度 | 得分 | 水平 |
|E外向性 | {E_score} | {E_level} |
|N神经质 | {N_score} | {N_level} |
|C尽责性 | {C_score} | {C_level} |
|A宜人性 | {A_score} | {A_level} |
|O开放性 | {O_score} | {O_level} |
> {profile_summary}

---
## 二、行为类型（BPT6）
主导类型：**{dominant_type}** | 次要类型：{secondary_type}
教练姿态：{coaching_approach}

---
## 三、改变阶段（TTM7）
当前阶段：**{stage_name}**（TTM：{ttm_equivalent}）
准备度指数：{readiness_index}/100

---
## 四、改变潜力（CAPACITY）
总分：{capacity_total}/160 | 等级：{level}
薄弱维度：{weak_dimensions}

---
## 五、成功预测（SPI）
SPI分数：{spi_score}/50 | 成功概率：{success_probability}

---
## 六、个性化处方
目标：{primary_goal}
策略：{core_strategies}
追踪：{tracking_method}，{review_frequency}

---
## 七、风险预警
{risk_alerts_table}

---
*本报告由BAPS v2.0自动生成，仅供专业参考*
```

---

## 十二、API接口规范

### 12.1 RESTful API端点

```yaml
# 评测管理
POST   /api/v2/assessments
  body: { user_id, target_behavior, questionnaire_types: [] }
  response: { session_id, first_questionnaire }

GET    /api/v2/assessments/{id}/questions
  response: { questionnaire_type, questions }

POST   /api/v2/assessments/{id}/answers
  body: { questionnaire_id, answers: { question_id: score } }
  response: { saved, next_questionnaire }

GET    /api/v2/assessments/{id}/progress
  response: { completed, remaining, progress_percent }

GET    /api/v2/results/{user_id}/latest
  response: { result }

POST   /api/v2/reports/generate
  body: { user_id, result_id, format: "json|pdf|html" }
  response: { report_url }

GET    /api/v2/recommendations/{user_id}
  response: { recommendations }
```

### 12.2 WebSocket 实时评测

```javascript
// 连接
ws://api/v2/ws/assessment/{session_id}

// 客户端 → 服务端
{ "type": "answer", "question_id": "E01", "score": 3 }

// 服务端 → 客户端
{ "type": "progress", "completed": 1, "total": 171 }
{ "type": "next_question", "question": {...} }
{ "type": "questionnaire_complete", "questionnaire": "BIG5" }
{ "type": "assessment_complete", "results": {...} }
```

### 12.3 答案数据结构

```json
{
  "user_id": "string",
  "session_id": "string",
  "questionnaire_type": "BIG5 | BPT6 | TTM7 | CAPACITY | SPI",
  "started_at": "datetime",
  "completed_at": "datetime",
  "answers": { "question_id": "score" },
  "metadata": { "device": "string", "duration_seconds": 0 }
}
```

---

## 附录A：版本记录

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-01-24 | 初始版本：BIG5、BPT6、CAPACITY、SPI |
| v2.0 | 2026-01-26 | 新增TTM7（无知无觉阶段）；建立S0–S6双轨对照模型 |
| v2.0-KB | 2026-02-26 | 知识库整合：加入状态机逻辑、BAPS驱动向量、PolicyGate规则 |

## 附录B：文件来源索引

| 来源文件 | 知识层 | 对应章节 |
|---------|-------|--------|
| `BAPS_v2.0_完整开发文档.md` | 题库+算法 | 三 ~ 七、十一、十二 |
| `01_系统概述与理论框架.md` | 理论框架 | 一、二 |
| `02~06_各工具问卷.md` | 完整题库 | 三 ~ 七 |
| `07_综合评分系统与报告模板.md` | 评分引擎+报告 | 八、十一 |
| `状态导入评估.txt` | 状态机逻辑 | 九 |
| `状态驱动.txt` | BAPS驱动向量 | 十 |

---

*评估系统知识库 · BAPS v2.0 · 编译完成*
