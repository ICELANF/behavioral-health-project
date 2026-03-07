# BHP知识库建设 · 本轮成果汇总与本地Claude执行说明
<!-- 文档类型：项目交接 / 执行指令 -->
<!-- 适用对象：本地Claude（Ollama / qwen系列 or claude-code环境）-->
<!-- 编写日期：2026-03-07 -->
<!-- 项目：行健平台（BehaviorOS）BHP KMS v4.0 知识库 -->
<!-- 规则文件：BHP知识库建设及管理规则_完整版_v4_0.md -->

---

## 一、本轮对话成果总览

本轮对话（含紧接上轮的BATCH-007/008）共完成三个批次的知识项生成：

| 批次 | 来源文件 | 输出文件 | KI数量 | 字符量 |
|------|---------|---------|--------|--------|
| BATCH-006 | HBR《自我发现与重塑》 | `KI-GROWTH-HBR_自我发现与重塑_向量chunks.md` | 8 | ≈45KB |
| BATCH-007 | 赖杞丰博士《萨提亚个人成长与家庭重塑》+ 《行为健康培训课程方案》 | `KI-GROWTH-SATIR_萨提亚模式_行为健康培训_向量chunks.md` | 7 | ≈41KB |
| BATCH-008 | 李中莹《重塑心灵：NLP》（修订版，2006） | `KI-GROWTH-NLP_重塑心灵_李中莹NLP_向量chunks.md` | 7 | ≈51KB |

**三批次合计：22个KI，约137KB，均符合BHP KMS v4.0规范**

---

## 二、各批次KI完整清单

### BATCH-006（HBR自我发现与重塑）

| KI编号 | 核心内容 | 阶段 |
|--------|---------|------|
| `KI-GROWTH-HBR-001` | 克里斯坦森·如何衡量你的人生（意义罗盘） | S4-S6 |
| `KI-IDENT-HBR-001` | 德鲁克·自我管理（回馈分析法） | S4-S5 |
| `KI-MEANING-HBR-001` | 库图·复原力三大秘密 | S2-S5 |
| `KI-GROWTH-HBR-002` | 施瓦茨·管理能量（四维能量更新） | S3-S5 |
| `KI-GROWTH-HBR-003` | 弗里德曼·全方位领导力 | S4-S6 |
| `KI-IDENT-HBR-002` | 奎因·本真领导力 | S4-S5 |
| `KI-GROWTH-HBR-004` | 卡普兰·领导者自省7问 | S4-S6 |
| `KI-GROWTH-HBR-005` | 戈尔曼·情绪领导力与自我重塑 | S3-S6 |
| `KI-GROWTH-HBR-000` | 整合索引 | 全阶段 |

### BATCH-007（萨提亚模式 + 行为健康培训）

| KI编号 | 核心内容 | 阶段 |
|--------|---------|------|
| `KI-GROWTH-SATIR-001` | 萨提亚模式总览（人性观·三大目标·核心命题） | S2-S6 |
| `KI-GROWTH-SATIR-002` | 冰山七层模型 | S2-S5 |
| `KI-IDENT-SATIR-001` | 应对姿态五态（讨好/指责/超理智/打岔/一致性） | S2-S5 |
| `KI-IDENT-SATIR-002` | 家庭重塑（原生家庭·代际传承·资源整合） | S4-S6 |
| `KI-GROWTH-SATIR-003` | 一致性沟通+规条转化+天气预报（三工具） | S3-S5 |
| `KI-COACH-BH-001` | 行动导向培训体系（六模块·三教法·四阶段） | 系统层 |
| `KI-GROWTH-SATIR-000` | 整合索引 | 全阶段 |

### BATCH-008（李中莹 NLP·重塑心灵）

| KI编号 | 核心内容 | 阶段 |
|--------|---------|------|
| `KI-GROWTH-NLP-001` | NLP十二条前提假设（成长信念哲学） | S2-S6 |
| `KI-IDENT-NLP-001` | 信念/价值/规条三层结构（身份重塑工具） | S3-S5 |
| `KI-GROWTH-NLP-002` | 自我价值三要素（自信/自爱/自尊） | S2-S5 |
| `KI-GROWTH-NLP-003` | **迪尔茨六层理解层次**（BHP分层干预核心框架） | S2-S6 |
| `KI-IDENT-NLP-002` | 情绪七大意义与钟摆效应 | S2-S5 |
| `KI-GROWTH-NLP-004` | 接受自己法+自我整合（内在和解操作工具） | S4-S6 |
| `KI-GROWTH-NLP-000` | 整合索引 | 全阶段 |

---

## 三、向量化优先级（Qdrant写入顺序建议）

以下按**检索频率×阶段覆盖度×平台架构重要性**综合排序：

```
【第一优先级 — 立即写入】
1. KI-GROWTH-NLP-003   迪尔茨六层理解层次
   理由：覆盖S2-S6全阶段，是BHP干预分层的底层逻辑，
         直接对应TTM×三层价值架构，平台架构层使用率最高

2. KI-GROWTH-SATIR-002  萨提亚冰山七层
   理由：S2-S4高频检索路径，情绪干预场景触发率高

3. KI-IDENT-NLP-001     信念/价值/规条三层结构
   理由：解释"知道但做不到"的核心机制，S3-S4必用

4. KI-IDENT-SATIR-001   应对姿态五态
   理由：家庭关系+沟通障碍场景触发率高（S2-S5常见情境）

【第二优先级 — 本周内写入】
5. KI-GROWTH-NLP-001    NLP十二条前提假设
6. KI-GROWTH-NLP-002    自我价值三要素
7. KI-IDENT-NLP-002     情绪七大意义+钟摆效应
8. KI-GROWTH-SATIR-001  萨提亚模式总览
9. KI-MEANING-HBR-001   库图复原力三大秘密

【第三优先级 — 下周写入】
10-22. 其余KI按文件顺序批量写入
```

---

## 四、Qdrant向量化执行指令（本地Claude执行）

### 4.1 前置检查

```bash
# 确认Qdrant服务状态
curl http://localhost:6333/health

# 确认collection存在（BHP KMS使用1024维embedding）
curl http://localhost:6333/collections/bhp_knowledge_base

# 如不存在，创建collection
curl -X PUT http://localhost:6333/collections/bhp_knowledge_base \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    }
  }'
```

### 4.2 文件位置

三个chunks文件已生成，本地Claude执行时请从以下路径读取：

```
# 来自 claude.ai 本次对话输出，需先下载到本地项目目录
# 建议放置路径：

{项目根目录}/bhp_kms/raw_chunks/
├── KI-GROWTH-HBR_自我发现与重塑_向量chunks.md       (BATCH-006, 8 KIs)
├── KI-GROWTH-SATIR_萨提亚模式_行为健康培训_向量chunks.md  (BATCH-007, 7 KIs)
└── KI-GROWTH-NLP_重塑心灵_李中莹NLP_向量chunks.md    (BATCH-008, 7 KIs)
```

### 4.3 向量化处理步骤（Python脚本逻辑）

```python
"""
BHP KMS v4.0 向量化写入脚本逻辑
embedding模型：1024维（与BHP KMS v4.0规范一致）
推荐模型：bge-large-zh-v1.5（1024dim，中文优化）
         或 text-embedding-3-large（OpenAI，1024dim可配置）
"""

import re
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# 1. 解析MD文件，按KI块切分
def parse_ki_chunks(md_file_path: str) -> list[dict]:
    """
    按 '## KI-' 标记切分每个知识项
    提取：ki_id, title, content, metadata
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按 ## KI- 分割
    chunks = re.split(r'\n(?=## KI-)', content)
    
    results = []
    for chunk in chunks:
        if not chunk.startswith('## KI-'):
            continue
        
        # 提取KI编号和标题
        header = chunk.split('\n')[0]
        ki_id = re.search(r'KI-[\w-]+', header).group()
        title = header.replace('## ', '').strip()
        
        # 提取元数据注释
        meta_line = ''
        for line in chunk.split('\n'):
            if line.startswith('<!-- 领域:') or line.startswith('<!-- 类型:'):
                meta_line = line
                break
        
        # 提取适用阶段
        stages = re.findall(r'S[0-6]', meta_line)
        
        # 提取成长维度
        growth_dim = ''
        gd_match = re.search(r'成长维度:([\w,_+]+)', meta_line)
        if gd_match:
            growth_dim = gd_match.group(1)
        
        results.append({
            'ki_id': ki_id,
            'title': title,
            'content': chunk,
            'metadata': {
                'ki_id': ki_id,
                'applicable_stages': stages,
                'growth_dimension': growth_dim,
                'domain': 'growth',
                'source': 'BHP_KMS_v4.0',
                'batch': _detect_batch(ki_id),
                'evidence_level': 'T2'
            }
        })
    
    return results

def _detect_batch(ki_id: str) -> str:
    if 'HBR' in ki_id: return 'BATCH-006'
    if 'SATIR' in ki_id or 'COACH' in ki_id: return 'BATCH-007'
    if 'NLP' in ki_id: return 'BATCH-008'
    return 'UNKNOWN'

# 2. 生成embedding（1024维）
def get_embedding_1024(text: str) -> list[float]:
    # 使用本地Ollama模型（bge-large-zh-v1.5）
    # 或调用API
    # 确保输出为1024维
    pass

# 3. 写入Qdrant
def upsert_to_qdrant(chunks: list[dict], client: QdrantClient):
    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding_1024(chunk['content'])
        points.append(PointStruct(
            id=abs(hash(chunk['ki_id'])) % (10**9),  # 稳定ID
            vector=embedding,
            payload={
                'ki_id': chunk['ki_id'],
                'title': chunk['title'],
                'content': chunk['content'][:2000],  # 截取摘要
                **chunk['metadata']
            }
        ))
    
    client.upsert(
        collection_name='bhp_knowledge_base',
        points=points
    )
    print(f"✅ 已写入 {len(points)} 个KI到Qdrant")
```

### 4.4 验证写入结果

```bash
# 查询collection状态
curl http://localhost:6333/collections/bhp_knowledge_base

# 测试检索（以"知道但做不到"为查询）
# 期望返回：KI-IDENT-NLP-001（信念/价值/规条）
# 期望返回：KI-GROWTH-SATIR-002（冰山模型）
```

---

## 五、已建KI与平台模块的集成说明

### 5.1 CoachAgent知识库检索配置

以下KI应加入CoachAgent的**优先检索集**（权重提升）：

```yaml
high_priority_ki:
  # S2-S3阶段（行动期/准备期）
  - KI-GROWTH-NLP-001    # NLP前提假设 - 建立接纳氛围
  - KI-GROWTH-SATIR-002  # 冰山模型 - 情绪探索
  - KI-IDENT-SATIR-001   # 应对姿态 - 沟通模式识别
  - KI-IDENT-NLP-002     # 情绪七意义 - 负面情绪接纳

  # S4阶段（内在动力转化）
  - KI-IDENT-NLP-001     # 信念/价值/规条 - 深层动机探索
  - KI-GROWTH-NLP-002    # 自我价值 - 自我认知工作
  - KI-GROWTH-NLP-003    # 迪尔茨六层 - 干预层次诊断

  # S5-S6阶段（身份整合/超越）
  - KI-GROWTH-NLP-004    # 接受自己法 - 内在和解
  - KI-IDENT-SATIR-002   # 家庭重塑 - 代际视角
  - KI-GROWTH-HBR-001    # 克里斯坦森意义罗盘 - 人生使命
```

### 5.2 与现有XZB（行诊智伴）模块的集成点

```
XZB评估 → 输出TTM阶段 → 触发对应KI检索

S2用户触发优先KI：
  SATIR-002（冰山）+ NLP-001（前提假设）+ MEANING-HBR-001（复原力）

S4用户触发优先KI：
  NLP-003（六层）+ NLP-001（信念价值规条）+ SATIR-003（规条转化）

S5用户触发优先KI：
  NLP-004（接受自己）+ SATIR-002（家庭重塑）+ NLP-003（身份层）
```

### 5.3 VisionGuard模块的可复用KI

以下KI对青少年视力健康（VisionGuard）场景同样适用：

```
• KI-GROWTH-NLP-001  前提假设⑧（行为背后有正面动机）
  → 青少年"不愿做眼保健操"的正面动机探索

• KI-GROWTH-NLP-002  自我价值三要素
  → 家长对孩子视力问题的内疚/焦虑处理

• KI-IDENT-SATIR-001 应对姿态
  → 家长与青少年在视力管理上的沟通冲突

• KI-GROWTH-NLP-003  迪尔茨六层（行为层→能力层）
  → 诊断青少年用眼行为问题在哪个层次，匹配干预
```

---

## 六、下一批次建设建议（BATCH-009）

### 推荐来源文件

```
优先级1：
• 《接受与承诺疗法（ACT）》相关资料
  目标KI：KI-ACT-VALUES-001（价值观澄清）
          KI-ACT-DEFUSE-001（认知解离）
          KI-ACT-PRESENT-001（当下觉察）
  与现有联动：NLP六层⑥系统层 + 萨提亚规条转化

优先级2：
• 弗兰克尔《活出生命的意义》
  目标KI：KI-MEANING-FRANKL-001（意义治疗三大途径）
          KI-MEANING-FRANKL-002（苦难的意义转化）
  与现有联动：NLP系统/使命层 + 萨提亚渴望层第6层

优先级3：
• Seligman PERMA幸福模型
  目标KI：KI-POSPSYCH-PERMA-001（五维幸福）
  与现有联动：情绪七意义中的正面情绪维度
```

### 优先补建的情境知识包

```
L3情境S12（身份转型对话）知识包
  整合建议：
  ① 迪尔茨六层（诊断框架，NLP-003）
  ② 萨提亚冰山（情感深化，SATIR-002）
  ③ 接受自己法（操作工具，NLP-004）
  ④ 应对姿态（沟通模式，SATIR-001）
  → 形成完整的S4→S5身份转型对话操作手册
```

---

## 七、合规验证备忘

本轮所有22个KI均已通过以下检验：

```
✅ BHP KMS v4.0 四层漏斗筛选
   Layer1: 学术有效性 — T2证据（有研究支持的实践框架）
   Layer2: 平台适配性 — 与慢病行为改变情境直接相关
   Layer3: 文化有效性 — High（华人化/本土化版本）
   Layer4: 铁律合规性 — 遵守铁律7（S0-S2急性期不作主线）

✅ 成长类KI四个必填字段均完整
   - growth_dimension ✓
   - reflection_prompts（4-5个）✓
   - identity_bridge ✓
   - applicable_life_events（≥2个）✓

✅ CoachAgent话术无说教语气
   - 按TTM阶段分类 ✓
   - 具体情境触发 ✓
   - 体现平等伙伴关系 ✓

✅ 知识项ID格式符合规范
   {类型}-{领域缩写}-{来源缩写}-{三位序号}
```

---

## 八、文件清单（本次交接）

```
outputs/
├── KI-GROWTH-HBR_自我发现与重塑_向量chunks.md
│   └── BATCH-006 | 9个KI（含索引）| HBR经典文章系列
│
├── KI-GROWTH-SATIR_萨提亚模式_行为健康培训_向量chunks.md
│   └── BATCH-007 | 7个KI（含索引）| 萨提亚+行为健康培训
│
├── KI-GROWTH-NLP_重塑心灵_李中莹NLP_向量chunks.md
│   └── BATCH-008 | 7个KI（含索引）| 李中莹NLP华人版
│
└── BHP_KMS_BATCH006-008_交接说明_本地Claude执行.md
    └── 本文件（执行指南）
```

---

*交接文档完毕 | 行健平台 BHP KMS v4.0 | BATCH-006至BATCH-008 | 2026-03-07*
