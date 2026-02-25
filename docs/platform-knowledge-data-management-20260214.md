# 平台知识与数据管理体系 — 全景技术文档

> **版本**: v1.0 | **日期**: 2026-02-14 | **状态**: 全部已部署
> **覆盖范围**: RAG 知识引擎、内容管理、知识共享、问卷系统、Agent 生态、数据分析、安全治理、调度系统

---

## 目录

- [第一部分: RAG 知识引擎](#第一部分-rag-知识引擎)
  - [1.1 架构总览](#11-架构总览)
  - [1.2 三层检索体系](#12-三层检索体系)
  - [1.3 证据分级制度](#13-证据分级制度)
  - [1.4 数据库模型](#14-数据库模型)
  - [1.5 文件转换与分片](#15-文件转换与分片)
  - [1.6 向量嵌入服务](#16-向量嵌入服务)
  - [1.7 检索引擎详解](#17-检索引擎详解)
  - [1.8 RAG 中间件集成](#18-rag-中间件集成)
  - [1.9 文档生命周期管理](#19-文档生命周期管理)
  - [1.10 批量导入服务](#110-批量导入服务)
  - [1.11 检索全流程示例](#111-检索全流程示例)
- [第二部分: 内容管理系统](#第二部分-内容管理系统)
  - [2.1 数据模型](#21-数据模型)
  - [2.2 内容 API (28 端点)](#22-内容-api-28-端点)
  - [2.3 内容管理 API (8 端点)](#23-内容管理-api-8-端点)
  - [2.4 用户投稿 API (7 端点)](#24-用户投稿-api-7-端点)
  - [2.5 专家内容工作室 (8 端点)](#25-专家内容工作室-8-端点)
  - [2.6 等级门控机制](#26-等级门控机制)
  - [2.7 测验评分系统](#27-测验评分系统)
  - [2.8 学习进度与连续打卡](#28-学习进度与连续打卡)
- [第三部分: 知识共享体系](#第三部分-知识共享体系)
  - [3.1 共享服务](#31-共享服务)
  - [3.2 共享 API (9 端点)](#32-共享-api-9-端点)
  - [3.3 状态流转](#33-状态流转)
- [第四部分: Agent 反馈与生态](#第四部分-agent-反馈与生态)
  - [4.1 反馈学习环](#41-反馈学习环)
  - [4.2 Agent 市场](#42-agent-市场)
  - [4.3 成长积分体系](#43-成长积分体系)
- [第五部分: 问卷系统](#第五部分-问卷系统)
  - [5.1 问卷引擎](#51-问卷引擎)
  - [5.2 BAPS 回流](#52-baps-回流)
  - [5.3 统计与导出](#53-统计与导出)
- [第六部分: 数据分析](#第六部分-数据分析)
  - [6.1 管理员分析 (7 端点)](#61-管理员分析-7-端点)
- [第七部分: 安全治理](#第七部分-安全治理)
  - [7.1 安全关键词配置](#71-安全关键词配置)
  - [7.2 安全规则配置](#72-安全规则配置)
  - [7.3 SafetyLog 模型](#73-safetylog-模型)
- [第八部分: 调度系统](#第八部分-调度系统)
  - [8.1 13 个定时任务总表](#81-13-个定时任务总表)
  - [8.2 Redis 分布式锁](#82-redis-分布式锁)
- [第九部分: 迁移记录](#第九部分-迁移记录)
- [第十部分: 文件索引](#第十部分-文件索引)
- [附录 A: 数据流图谱](#附录-a-数据流图谱)

---

## 第一部分: RAG 知识引擎

### 1.1 架构总览

知识引擎采用 **三层作用域** + **证据分级** 的 RAG (Retrieval-Augmented Generation) 架构，支持专家租户私有知识、领域共享知识和平台公共知识的分层检索。

**技术栈**:
- **向量嵌入**: sentence-transformers (`shibing624/text2vec-base-chinese`, 768 维, 主) / Ollama `nomic-embed-text` (768 维, 备)
- **向量存储**: PostgreSQL pgvector (`Vector(768)`) + JSON 降级
- **分片策略**: Markdown 感知层级切分 (800 字符上限, 100 字符重叠)
- **检索引擎**: Python numpy 余弦相似度 (非 pgvector 内置函数)
- **作用域优先**: tenant (+0.15) > domain (+0.08) > platform (基线 0.00)

**核心文件** (18 个, 2,629 行):

| 文件 | 行数 | 职责 |
|------|------|------|
| `core/knowledge/embedding_service.py` | 52 | Ollama 嵌入服务 |
| `core/knowledge/retriever.py` | 480 | 主检索引擎 + 评分 + 引用 |
| `core/knowledge/rag_middleware.py` | 178 | RAG 增强中间件 |
| `core/knowledge/chunker.py` | 71 | Markdown 分片器 |
| `core/knowledge/document_service.py` | 368 | 文档 CRUD + 发布流水线 |
| `core/knowledge/file_converter.py` | 108 | PDF/DOCX/TXT/MD 转换 |
| `core/knowledge/archive_extractor.py` | 94 | ZIP/7Z/RAR 解压 |
| `core/knowledge/batch_ingestion_service.py` | 216 | 批量导入编排 |
| `core/knowledge/sharing_service.py` | 277 | 知识共享工作流 |
| `backend/services/chunker.py` | 153 | 双后端嵌入 + SmartChunker |
| `backend/services/doc_parser.py` | 111 | Markdown 解析器 |
| `backend/services/ingest.py` | 151 | 异步知识导入 + 17 领域种子 |
| `backend/models/knowledge.py` | 70 | 模型重导出 + 枚举定义 |

### 1.2 三层检索体系

```
┌──────────────────────────────────────────────────────┐
│                   用户查询 / Agent 请求                │
└─────────────────────┬────────────────────────────────┘
                      │
      ┌───────────────▼───────────────┐
      │         作用域过滤             │
      │  ┌─ tenant  (专家私有, +0.15) │
      │  ├─ domain  (领域共享, +0.08) │
      │  └─ platform(平台公共, +0.00) │
      └───────────────┬───────────────┘
                      │
      ┌───────────────▼───────────────┐
      │      向量余弦相似度计算         │
      │  raw_score = cos(q_vec, c_vec) │
      └───────────────┬───────────────┘
                      │
      ┌───────────────▼───────────────┐
      │         综合评分               │
      │  boosted = raw_score           │
      │         + scope_boost          │
      │         + priority_adj         │
      │         - freshness_penalty    │
      └───────────────┬───────────────┘
                      │
      ┌───────────────▼───────────────┐
      │    排序 → Top-K → 引用生成     │
      │    → Prompt 注入 → LLM 生成    │
      └────────────────────────────────┘
```

**作用域加权** (`SCOPE_BOOST` in `retriever.py:48`):

| 作用域 | 加权值 | 含义 |
|--------|--------|------|
| `tenant` | +0.15 | 专家私有知识，最高优先 |
| `domain` | +0.08 | 领域共享知识 |
| `platform` | +0.00 | 平台公共知识，基线 |

**Agent-领域映射** (`AGENT_DOMAIN_MAP` in `retriever.py:29`):

| Agent | 关联领域 |
|-------|---------|
| `sleep` | sleep, mental, behavior |
| `glucose` | glucose, nutrition, metabolism |
| `stress` | stress, mental, behavior, tcm |
| `mental` | mental, psychology, behavior |
| `nutrition` | nutrition, metabolism, tcm |
| `exercise` | exercise, rehabilitation, metabolism |
| `tcm` | tcm, nutrition, constitution |
| `crisis` | crisis, mental |
| `motivation` | motivation, behavior, psychology |
| `behavior_rx` | behavior, motivation, psychology, habit |
| `weight` | weight, nutrition, exercise, metabolism |
| `cardiac_rehab` | cardiac, exercise, nutrition, rehabilitation |

### 1.3 证据分级制度

**分级优先映射** (`TIER_PRIORITY_MAP` in `core/models.py`):

| 等级 | 说明 | 优先级 | 审核要求 |
|------|------|--------|---------|
| **T1** | Meta 分析/RCT | 9 (最高) | 不需要 |
| **T2** | 队列研究 | 7 | 不需要 |
| **T3** | 专家共识 (默认) | 5 | 不需要 |
| **T4** | 个人经验 | 3 | 发布前必须审核通过 |

**T4 审核门控**:
- T4 文档创建时自动 `review_status = 'pending'`
- 发布时检查 `review_status == 'approved'`，否则拒绝
- 管理员通过 `document_service.approve_document()` 审批

### 1.4 数据库模型

#### KnowledgeDocument (knowledge_documents)

**32 列**, 知识文档主表:

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 自增主键 |
| `title` | String(300) | NOT NULL | 文档标题 |
| `author` | String(100) | | 作者 |
| `source` | String(255) | | 原始来源 |
| `description` | Text | | 摘要描述 |
| `scope` | String(50) | indexed | tenant/domain/platform |
| `domain_id` | String(50) | indexed | 所属知识领域 |
| `tenant_id` | String(64) | indexed | 专家租户 ID (NULL=平台) |
| `status` | String(20) | | draft/processing/ready/error |
| `is_active` | Boolean | default=True | RAG 检索是否包含 |
| `raw_content` | Text | | Markdown 原文 |
| `file_path` | String(500) | | 本地路径 |
| `file_type` | String(50) | default="md" | md/pdf/docx/txt |
| `file_hash` | String(128) | UNIQUE | SHA256 去重 |
| `file_size` | Integer | | 字节数 |
| `chunk_count` | Integer | | 分片数量 |
| `evidence_tier` | String(2) | default="T3" | T1/T2/T3/T4 |
| `content_type` | String(30) | | 内容分类 |
| `published_date` | DateTime | | 原始发布日期 |
| `expires_at` | DateTime | | 过期时间 (新鲜度惩罚) |
| `review_status` | String(20) | | pending/approved/rejected/not_required |
| `reviewer_id` | Integer | FK(users) | 审核人 |
| `reviewed_at` | DateTime | | 审核时间 |
| `contributor_id` | Integer | FK(users) | 投稿人 |
| `priority` | Integer | default=5 | 检索权重 (1-10) |
| `created_at` | DateTime | server_default | 创建时间 |
| `updated_at` | DateTime | onupdate | 更新时间 |

**索引**: `(scope, domain_id)`, `(scope, tenant_id)`, `(status)`, `(file_hash UNIQUE)`

#### KnowledgeChunk (knowledge_chunks)

**向量分片表**, 存储 768 维嵌入:

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | |
| `document_id` | Integer | FK CASCADE | 所属文档 |
| `chunk_index` | Integer | | 分片序号 (0-based) |
| `content` | Text | NOT NULL | 分片文本 (~800 字符) |
| `heading` | String(255) | | 所属章节标题 |
| `doc_title` | String(300) | | 文档标题 (反范式) |
| `doc_author` | String(100) | | 作者 (反范式) |
| `doc_source` | String(255) | | 来源 (反范式) |
| `page_number` | Integer | | PDF 来源页码 |
| `scope` | String(50) | indexed | 与文档同步 |
| `domain_id` | String(50) | | 与文档同步 |
| `tenant_id` | String(64) | indexed | 与文档同步 |
| `embedding` | Vector(768) / JSON | | 768 维向量 |
| `metadata` | JSON | | 自定义元数据 |
| `created_at` | DateTime | | |

**索引**: `(document_id)`, `(scope, domain_id)`, `(scope, tenant_id)`

#### KnowledgeCitation (knowledge_citations)

**引用审计表**, 追踪 RAG 引用使用情况:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `session_id` | String(100), indexed | 对话会话 |
| `message_id` | String(100) | 消息 ID |
| `agent_id` | String(50) | Agent 标识 |
| `tenant_id` | String(64) | 租户 |
| `user_id` | String(50) | 用户 |
| `chunk_id` | Integer | 被引用分片 |
| `document_id` | Integer, indexed | 被引用文档 |
| `query_text` | String(500) | 原始查询 |
| `relevance_score` | Float | 相关度得分 |
| `rank_position` | Integer | 引用排位 [1][2][3] |
| `citation_text` | String(500) | 引用文本预览 |
| `citation_label` | String(300) | 格式化标签 |
| `created_at` | DateTime | |

#### KnowledgeDomain (knowledge_domains)

**知识领域元数据** (17 个种子领域):

| domain_id | label |
|-----------|-------|
| `general` | General Health |
| `tcm` | TCM & Wellness |
| `nutrition` | Nutrition Science |
| `exercise` | Exercise & Rehab |
| `sleep` | Sleep Science |
| `mental_health` | Mental Health |
| `stress` | Stress Management |
| `metabolic` | Metabolic Diseases |
| `cardiac` | Cardiac Rehab |
| `weight` | Weight Management |
| `motivation` | Behavioral Motivation |
| `behavior_change` | Behavior Change |
| `chronic_disease` | Chronic Disease Mgmt |
| `geriatric` | Geriatric Health |
| `big_five` | Big Five Personality |
| `psychology` | Psychology Foundations |
| `rehabilitation` | Rehabilitation Medicine |

#### KnowledgeContribution (knowledge_contributions)

**知识共享工作流表** (详见第三部分):

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `document_id` | Integer FK CASCADE | 贡献的文档 |
| `tenant_id` | String(64), indexed | 贡献者租户 |
| `contributor_id` | Integer FK(users) | 贡献者 |
| `domain_id` | String(50) | 目标共享领域 |
| `reason` | Text | 贡献理由 |
| `status` | String(20) | pending/approved/rejected/revoked |
| `reviewer_id` | Integer FK(users) | 审核人 |
| `review_comment` | Text | 审核意见 |
| `reviewed_at` | DateTime | 审核时间 |
| `created_at` | DateTime | |

#### BatchIngestionJob (batch_ingestion_jobs)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK(users) | 上传者 |
| `filename` | String(300) | 文件名 |
| `file_type` | String(20) | zip/pdf/docx/md/txt/7z/rar |
| `status` | String(20) | pending/processing/completed/failed |
| `total_files` | Integer | 总文件数 |
| `processed_files` | Integer | 已处理数 |
| `total_chunks` | Integer | 生成分片数 |
| `result_doc_ids` | JSON | 成功的文档 ID 列表 |
| `error_message` | Text | 错误信息 |
| `created_at` / `updated_at` | DateTime | |

### 1.5 文件转换与分片

#### 支持的文件格式

| 格式 | 库 | 处理方式 |
|------|-----|---------|
| `.md` | 内置 | 直接读取 |
| `.txt` | 内置 | 整文件作为一个段落 |
| `.pdf` | pypdf | 按页提取, 前缀 `## Page N` |
| `.docx` | python-docx | 段落提取, 保留 H1-H4 标题层级 |
| `.zip` | zipfile | 解压 → 扫描 → 逐文件处理 |
| `.7z` | py7zr | 解压 → 扫描 → 逐文件处理 |
| `.rar` | rarfile | 解压 → 扫描 → 逐文件处理 |

**文件转换入口** (`core/knowledge/file_converter.py`):

```python
CONVERTERS = {".pdf": convert_pdf_to_markdown, ".docx": convert_docx_to_markdown,
              ".txt": convert_txt_to_markdown, ".md": convert_md_to_markdown}
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
```

#### 分片算法 (`core/knowledge/chunker.py`)

```python
def chunk_markdown(text: str, max_chars: int = 800, overlap: int = 100) -> List[Dict[str, str]]
```

**算法步骤**:
1. 正则分割: `r'^(#{1,3}\s+.+)$'` 提取标题
2. 缓冲累积: 段落聚集到 `max_chars` 上限
3. 重叠处理: 上一分片末尾 `overlap` 字符前置到下一分片
4. 最小阈值: 丢弃过短分片

**输出格式**:
```python
[{"heading": "Section Title", "content": "...文本..."}, ...]
```

#### 归档解压 (`core/knowledge/archive_extractor.py`)

```python
def extract_archive(file_path: str) -> Tuple[str, List[str]]
# 1. 检测格式 (.zip/.7z/.rar)
# 2. 创建临时目录: tempfile.mkdtemp(prefix="bhp_ingest_")
# 3. 解压全部文件
# 4. 递归扫描, 过滤 SUPPORTED_EXTENSIONS
# 5. 返回 (临时目录, [支持的文件列表])
```

### 1.6 向量嵌入服务

#### Ollama 嵌入 (`core/knowledge/embedding_service.py`)

```python
class EmbeddingService:
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

    def embed_query(self, text: str) -> List[float]     # 单文本 → 768 维
    def embed_batch(self, texts: List[str]) -> List[List[float]]  # 批量, 每 50 条记日志
    def close(self)                                       # 清理 httpx 客户端
```

- 基于 `httpx.Client(timeout=60.0)`, POST `/api/embeddings`
- 失败返回空列表 `[]` (优雅降级, LLM 在无知识增强下继续工作)

#### 混合嵌入 (`backend/services/chunker.py`)

```python
class EmbeddingService:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer("shibing624/text2vec-base-chinese")  # 主
        except:
            from core.knowledge.embedding_service import EmbeddingService as OllamaEmbed
            self._ollama = OllamaEmbed()  # 备

    def embed(self, text: str) -> List[float]
    def embed_batch(self, texts: List[str]) -> List[List[float]]
```

- **主引擎**: sentence-transformers (`text2vec-base-chinese`, 768 维, 本地 GPU/CPU)
- **备用引擎**: Ollama `nomic-embed-text` (HTTP API)

### 1.7 检索引擎详解

#### KnowledgeRetriever (`core/knowledge/retriever.py`)

```python
class KnowledgeRetriever:
    def __init__(self, db: Session, embedder)

    def retrieve(
        self,
        query: str,
        agent_id: str = "",          # Agent 标识 → 领域映射
        tenant_id: str = "",         # 专家租户 ID
        top_k: int = 5,
        min_score: float = 0.35,     # 最低相似度阈值
    ) -> RAGContext
```

**9 步检索流水线**:

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 领域解析 | `AGENT_DOMAIN_MAP[agent_id]` → 领域列表 |
| 2 | 查询向量化 | `embedder.embed_query(query)` → 768 维 |
| 3 | SQL 候选过滤 | 按 scope + tenant_id + domain_id 过滤活跃分片 |
| 4 | 余弦相似度 | `cosine_similarity(query_vec, chunk_vec)` |
| 5 | 阈值过滤 | `raw_score < min_score` 跳过 |
| 6 | 作用域加权 | `+ SCOPE_BOOST[chunk.scope]` |
| 7 | 优先级调整 | `+ (doc.priority - 5) * 0.01` |
| 8 | 新鲜度惩罚 | `- min(days_expired * 0.005, 0.10)` |
| 9 | 排序取 Top-K | 生成引用 + Prompt 注入 |

#### Citation 数据类

```python
@dataclass
class Citation:
    index: int                   # [1], [2], ...
    doc_title: str
    heading: str
    author: str
    source: str
    page_number: Optional[int]
    relevance_score: float       # 加权后得分
    content_preview: str         # 前 150 字符
    chunk_id: int
    document_id: int
    scope: str                   # tenant/domain/platform
    evidence_tier: str           # T1/T2/T3/T4

    @property
    def scope_label(self) -> str:
        return {"tenant": "🔒 专家私有", "domain": "📂 领域知识", "platform": "🌐 平台公共"}[self.scope]

    @property
    def label(self) -> str:
        # 格式: [1] Author 《Doc Title》> Heading (Page X)
```

#### RAGContext 数据类

```python
@dataclass
class RAGContext:
    query: str
    citations: List[Citation] = []
    prompt_injection: str = ""
    domains_searched: List[str] = []

    def format_response(self, llm_response: str) -> Dict[str, Any]:
        # 提取 [1][2][3] 引用编号
        # 识别【补充】标记
        # 构建完整响应信封
```

#### Prompt 注入模板

`_build_injection()` 按三层结构生成知识上下文:

```
<knowledge_base>
[知识检索规则 — 6 条严格规则, 强调本地知识优先]

━━━ 🔒 专家私有资料 (最高优先) ━━━
--- 参考资料 [1] ---
来源: Dr. Zhang, 《Diabetes Guide》> Fruit Recommendations
相关度: 95%
[内容预览]

━━━ 📂 领域专业知识 ━━━
--- 参考资料 [2] ---
[域共享内容]

━━━ 🌐 平台通用知识 ━━━
--- 参考资料 [3] ---
[公共内容]

</knowledge_base>
```

**6 条强制规则**:
1. 有本地知识时必须使用
2. 引用需标注编号 [1][2][3]
3. 本地知识权威性高于模型知识
4. 模型补充内容须以【补充】标记
5. 禁止捏造数据/百分比/方案
6. 推荐结构: 知识引用 → 补充说明 → 建议

### 1.8 RAG 中间件集成

#### rag_enhance() — 一步式 RAG 增强 (`core/knowledge/rag_middleware.py`)

```python
def rag_enhance(
    db: Session,
    query: str,
    agent_id: str = "",
    tenant_id: str = "",
    base_system_prompt: str = "",
    persona: dict = None,
    top_k: int = 5,
    min_score: float = 0.35,
) -> RAGEnhancedContext
```

**RAGEnhancedContext**:

```python
@dataclass
class RAGEnhancedContext:
    system_prompt: str          # 可直接使用的增强 system prompt
    has_knowledge: bool
    citation_count: int
    domains_searched: List[str]

    def wrap_response(self, llm_response: str) -> Dict[str, Any]:
        # 返回前端就绪结构:
        {
            "text": "...",
            "hasKnowledge": bool,
            "citationsUsed": [1, 2],
            "citations": [Citation dict, ...],
            "hasModelSupplement": bool,
            "modelSupplementSections": ["【补充】..."],
            "domainsSearched": ["nutrition", "exercise"],
            "sourceStats": {
                "knowledgeCount": 2,
                "modelSupplement": true,
                "scopeBreakdown": {"tenant": 1, "domain": 1, "platform": 0}
            }
        }
```

#### record_citations() — 引用审计持久化

```python
def record_citations(
    db: Session,
    enhanced: RAGEnhancedContext,
    llm_response: str,
    session_id: str, message_id: str,
    agent_id: str, tenant_id: str, user_id: str,
)
# 提取 LLM 响应中 [1][2][3] 引用
# 为每个使用的引用写入 KnowledgeCitation 记录
```

#### MasterAgent 集成模式

```python
# core/agents/master_agent.py — Step 7 知识注入
rag_context = rag_enhance(db, user_message, agent_id, tenant_id, system_prompt, top_k=5)
response = llm.generate(system_prompt=rag_context.system_prompt, messages=messages)
record_citations(db, rag_context, response.text, session_id, message_id, agent_id, tenant_id, user_id)
formatted = rag_context.wrap_response(response.text)
```

### 1.9 文档生命周期管理

#### 文档服务 (`core/knowledge/document_service.py`)

| 函数 | 作用 |
|------|------|
| `create_document(db, tenant_id, user, title, ...)` | 创建草稿 (T4 自动 pending) |
| `publish_document(db, doc_id, tenant_id)` | 分片→嵌入→存储→上线 |
| `unpublish_document(db, doc_id, tenant_id)` | 撤回发布 (status='draft') |
| `delete_document(db, doc_id, tenant_id)` | 级联删除 (含分片) |
| `list_documents(db, tenant_id, status, domain, keyword)` | 文档列表 |
| `approve_document(db, doc_id, reviewer_id, tenant_id)` | T4 审核通过 |
| `reject_document(db, doc_id, reviewer_id, tenant_id)` | T4 审核拒绝 |
| `handle_expired_documents(db)` | 过期降权 (priority -= 2, min=1) |
| `list_pending_reviews(db, domain)` | 待审核队列 |

**发布流水线** (`publish_document`):

```
1. 验证文档存在 + 归属租户
2. T4 门控: review_status == 'approved' 否则拒绝
3. status = 'processing'
4. 删除旧分片 (重新发布)
5. chunk_markdown(raw_content) → 分片列表
6. embedder.embed_batch(texts) → 768 维向量
7. 插入 KnowledgeChunk (含 embedding JSON + 元数据)
8. status = 'ready', is_active = True, chunk_count = N
9. 异常: status = 'error' (可恢复)
```

### 1.10 批量导入服务

#### 批量上传流水线 (`core/knowledge/batch_ingestion_service.py`)

```python
def process_batch_upload(db, user_id, file_path, filename, scope, domain_id, tenant_id) -> BatchIngestionJob
```

**处理流程**:
1. 创建 `BatchIngestionJob` (status='processing')
2. 检测文件类型
3. **归档文件**: `extract_archive()` → 临时目录 + 文件列表 → 逐个 `convert + ingest` → 清理临时目录
4. **单文件**: `convert_file_to_markdown()` → `_ingest_single_document()`
5. 成功: status='completed', result_doc_ids
6. 失败: status='failed', error_message

**单文件导入子流程** (`_ingest_single_document`):
1. 提取文件名作标题
2. 创建 KnowledgeDocument (evidence_tier='T3', status='ready', is_active=True)
3. 分片 → 尝试嵌入 (ImportError 优雅降级) → 插入分片
4. 更新 chunk_count

#### 批量导入 API (`api/batch_ingestion_api.py`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/v1/knowledge/batch-upload` | coach+ | 上传文件 (最大 100MB) |
| GET | `/api/v1/knowledge/batch-jobs` | coach+ | 任务列表 |
| GET | `/api/v1/knowledge/batch-jobs/{id}` | coach+ | 任务详情 |
| DELETE | `/api/v1/knowledge/batch-jobs/{id}` | coach+ | 删除任务 (非 processing) |

**允许扩展名**: `.pdf`, `.docx`, `.txt`, `.md`, `.zip`, `.7z`, `.rar`
**最大文件**: 100MB

### 1.11 检索全流程示例

**场景**: Glucose Agent 处理 "糖尿病能吃水果吗？", tenant_id = "expert_123"

```
Step 1  领域解析
        AGENT_DOMAIN_MAP["glucose"] → ["glucose", "nutrition", "metabolism"]

Step 2  查询向量化
        query_vec = embedder.embed_query("糖尿病能吃水果吗？") → [0.12, 0.45, ..., 0.78]  (768 维)

Step 3  SQL 候选过滤
        WHERE is_active=TRUE AND status='ready' AND embedding IS NOT NULL
          AND (
            (scope='tenant' AND tenant_id='expert_123')
            OR (scope='domain' AND domain_id IN ('glucose','nutrition','metabolism'))
            OR (scope='platform' AND (domain_id IN (...) OR domain_id='general'))
          )

Step 4  逐分片评分
        chunk_1: raw=0.78, scope='tenant'  → 0.78 + 0.15 + 0.02 - 0.00 = 0.95
        chunk_2: raw=0.72, scope='domain'  → 0.72 + 0.08 + 0.00 - 0.00 = 0.80
        chunk_3: raw=0.65, scope='platform'→ 0.65 + 0.00 + 0.01 - 0.02 = 0.64

Step 5  排序 → Top 5 → 生成 Citation 列表

Step 6  Prompt 注入 (三层结构)
        <knowledge_base>
        ━━━ 🔒 专家私有资料 ━━━
        --- 参考资料 [1] ---  Dr. Zhang, 95%
        ━━━ 📂 领域专业知识 ━━━
        --- 参考资料 [2] ---  Nutritionist Guide, 80%
        </knowledge_base>

Step 7  LLM 生成 → "根据专业知识库，糖尿病患者可以吃水果[1]...建议低 GI 水果[2]..."

Step 8  wrap_response() → {text, citationsUsed:[1,2], sourceStats:{tenant:1,domain:1}}

Step 9  record_citations() → 写入 knowledge_citations 审计表
```

---

## 第二部分: 内容管理系统

### 2.1 数据模型

#### ContentItem (content_items) — 统一内容条目

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `content_type` | String(30), indexed | article/video/course/card/case_share |
| `title` | String(300) NOT NULL | 内容标题 |
| `body` | Text | Markdown 正文 |
| `cover_url` | String(500) | 封面图 |
| `media_url` | String(500) | 视频/媒体 URL |
| `domain` | String(50), indexed | 健康领域 |
| `level` | String(10) | L0-L5 等级门控 |
| `author_id` | Integer FK(users), indexed | 创建者 |
| `tenant_id` | String(64), indexed | 专家租户 (NULL=平台) |
| `status` | String(20), indexed | draft/published/archived |
| `view_count` | Integer default=0 | 浏览数 (反范式) |
| `like_count` | Integer default=0 | 点赞数 (反范式) |
| `comment_count` | Integer default=0 | 评论数 (反范式) |
| `collect_count` | Integer default=0 | 收藏数 (反范式) |
| `has_quiz` | Boolean default=False | 是否关联测验 |
| `created_at` / `updated_at` | DateTime | |

**索引**: `(content_type, status)`, `(domain, level)`, `(author_id)`

#### ContentLike (content_likes)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK(users) | 点赞者 |
| `content_id` | Integer FK(content_items) | 被赞内容 |
| `created_at` | DateTime | |

**唯一约束**: `(user_id, content_id)` — 防重复

#### ContentBookmark (content_bookmarks)

结构同 ContentLike, 唯一约束 `(user_id, content_id)`

#### ContentComment (content_comments)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK, indexed | 评论者 |
| `content_id` | Integer FK, indexed | 目标内容 |
| `parent_id` | Integer FK(self) | 自引用 (回复) |
| `content` | Text NOT NULL | 评论文本 |
| `rating` | Integer 1-5 | 可选星级 |
| `like_count` | Integer default=0 | 评论点赞 |
| `status` | String(20) default="active" | active/hidden/deleted |
| `created_at` | DateTime, indexed | |

#### LearningProgress (learning_progress)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK, indexed | 学习者 |
| `content_id` | Integer FK, indexed | 学习内容 |
| `progress_percent` | Float default=0.0 | 0-100% |
| `last_position` | String(50) | 续播位置 (mm:ss 或章节) |
| `time_spent_seconds` | Integer default=0 | 累计学习时长 |
| `status` | String(20) | not_started/in_progress/completed |
| `created_at` / `updated_at` | DateTime | |

**唯一约束**: `(user_id, content_id)`

#### LearningTimeLog (learning_time_logs)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK, indexed | |
| `content_id` | Integer | |
| `domain` | String(50) | |
| `minutes` | Integer NOT NULL | 每次学习分钟数 (>=1) |
| `earned_at` | DateTime, indexed | |

#### LearningPointsLog (learning_points_logs)

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK, indexed | |
| `source_type` | String(50) | quiz/complete/share/comment/daily_login/streak |
| `source_id` | String(50) | 关联内容/测验 ID |
| `points` | Integer NOT NULL | 积分值 |
| `category` | String(20) | growth/contribution/influence |
| `earned_at` | DateTime, indexed | |

#### UserLearningStats (user_learning_stats) — 反范式汇总

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK UNIQUE | 每用户一条 |
| `total_minutes` | Integer | 累计学习分钟 |
| `total_points` | Integer | 总积分 |
| `growth_points` | Integer | 成长积分 |
| `contribution_points` | Integer | 贡献积分 |
| `influence_points` | Integer | 影响力积分 |
| `current_streak` | Integer | 当前连续天数 |
| `longest_streak` | Integer | 历史最高 |
| `last_learn_date` | String(10) | YYYY-MM-DD |
| `quiz_total` | Integer | 测验总次数 |
| `quiz_passed` | Integer | 通过次数 |
| `updated_at` | DateTime | |

#### ContentAudio (content_audio) — V005 TTS

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `content_item_id` | Integer FK, indexed | 关联内容 |
| `audio_url` | String(500) NOT NULL | 音频文件 URL |
| `duration_seconds` | Integer | 音频时长 |
| `voice_type` | String(30) default="tts_female" | tts_female/tts_male/human |
| `transcript` | Text | 无障碍文字稿 |
| `created_at` | DateTime | |

### 2.2 内容 API (28 端点)

**文件**: `api/content_api.py` (1,239 行)

#### 列表与发现

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content` | 登录 | 分页列表 + 等级门控 |
| GET | `/api/v1/content/recommended` | 登录 | 热门推荐 (view_count DESC) |
| GET | `/api/v1/content/feed/related` | 公开 | 关联内容 (created_at DESC) |
| GET | `/api/v1/content/recommendations` | 公开 | 推荐引擎 (同域优先 + 热度) |

**GET `/api/v1/content`** 查询参数:
- `page`, `page_size` (分页, 默认 20, 最大 100)
- `type` (article/video/course/card/case_share)
- `source` (platform 或 expert)
- `domain` (健康领域)
- `level` (L0-L5)
- `keyword` (标题模糊搜索)
- `sort_by` / `sort_order`

每条返回 `access_status: {accessible, reason, unlock_level, unlock_level_label}`

#### 课程

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/course/{id}` | 登录 | 课程详情 (含门控) |
| POST | `/api/v1/content/course/{id}/enroll` | 登录 | 报名 (UPSERT LearningProgress) |
| POST | `/api/v1/content/course/{id}/progress` | 登录 | 更新进度 + 时长 + 打卡 |

#### 视频与测验

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/video/{id}` | 登录 | 视频详情 |
| GET | `/api/v1/content/video/{id}/quiz` | 登录 | 获取测验题 (隐藏答案) |
| POST | `/api/v1/content/video/{id}/quiz/submit` | 登录 | 提交测验 (评分+积分) |

#### 案例分享

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/cases` | 公开 | 案例列表 |
| GET | `/api/v1/content/case/{id}` | 公开 | 案例详情 (view_count++) |
| POST | `/api/v1/content/case` | 登录 | 创建案例 (status=draft, 待审核) |
| POST | `/api/v1/content/case/{id}/like` | 登录 | 点赞 (Toggle) |
| POST | `/api/v1/content/case/{id}/helpful` | 登录 | 有帮助 (Toggle, ContentBookmark) |

#### 内容详情与互动

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/detail/{type}/{id}` | 登录 | 统一详情 (含 user_interaction) |
| GET | `/api/v1/content/{id}/comments` | 公开 | 评论列表 (newest/hot/oldest) |
| POST | `/api/v1/content/{id}/comment` | 登录 | 发表评论 |
| POST | `/api/v1/content/{id}/like` | 登录 | 点赞 Toggle |
| POST | `/api/v1/content/{id}/collect` | 登录 | 收藏 Toggle |
| POST | `/api/v1/content/{id}/share` | 登录 | 获取分享数据 |

#### 学习进度

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/user/learning-progress` | 登录 | 仪表板 (Coach/Grower 分支) |
| POST | `/api/v1/content/user/learning-progress` | 登录 | 记录学习 |
| GET | `/api/v1/content/user/learning-history` | 登录 | 学习历史 |
| GET | `/api/v1/content/user/{uid}/progress/{cid}` | 登录 | 指定内容进度 |

#### 审核队列

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/content/review/queue` | coach+ | 待审核列表 |
| POST | `/api/v1/content/review/submit` | coach+ | 审核决定 (approved/rejected/revision) |

#### SSE 流

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/content/stream/{id}` | 演示用 Server-Sent Events |

### 2.3 内容管理 API (8 端点)

**文件**: `api/content_manage_api.py` (229 行), 权限: coach+

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/content-manage/create` | 创建单条 (status=draft) |
| POST | `/api/v1/content-manage/batch-create` | 批量创建 (最多 50 条) |
| GET | `/api/v1/content-manage/list` | 管理列表 |
| PUT | `/api/v1/content-manage/{id}` | 更新内容 |
| POST | `/api/v1/content-manage/{id}/publish` | 发布 |
| POST | `/api/v1/content-manage/batch-publish` | 批量发布 (最多 100 条) |
| DELETE | `/api/v1/content-manage/{id}` | 归档 (软删除) |

### 2.4 用户投稿 API (7 端点)

**文件**: `api/content_contribution_api.py` (237 行)

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/api/v1/contributions/submit` | grower+ | 提交知识投稿 (T4 自动审核) |
| GET | `/api/v1/contributions/my` | grower+ | 我的投稿列表 |
| GET | `/api/v1/contributions/my/{id}` | grower+ | 投稿详情 |
| PUT | `/api/v1/contributions/my/{id}` | grower+ | 修改草稿 |
| GET | `/api/v1/contributions/review/pending` | coach+ | 审核队列 |
| POST | `/api/v1/contributions/review/{id}/approve` | coach+ | 通过 |
| POST | `/api/v1/contributions/review/{id}/reject` | coach+ | 拒绝 |

投稿创建 KnowledgeDocument (scope="platform", contributor_id=user.id, status="pending")

### 2.5 专家内容工作室 (8 端点)

**文件**: `api/expert_content_api.py` (308 行)

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/tenants/{tid}/content/documents` | 租户/admin | 文档列表 |
| POST | `/api/v1/tenants/{tid}/content/documents` | 租户/admin | 创建文档 |
| GET | `/api/v1/tenants/{tid}/content/documents/{id}` | 租户/admin | 文档详情 |
| PUT | `/api/v1/tenants/{tid}/content/documents/{id}` | 租户/admin | 更新草稿 |
| POST | `/api/v1/tenants/{tid}/content/documents/{id}/publish` | 租户/admin | 发布 (分片+嵌入) |
| POST | `/api/v1/tenants/{tid}/content/documents/{id}/unpublish` | 租户/admin | 撤回发布 |
| DELETE | `/api/v1/tenants/{tid}/content/documents/{id}` | 租户/admin | 删除 (级联分片) |
| GET | `/api/v1/tenants/{tid}/content/challenges` | 租户/admin | 专家挑战列表 |

**发布流程**:
1. SmartChunker 切分 (512-4096 字符)
2. sentence-transformers 生成 768 维嵌入
3. 创建 KnowledgeChunk + pgvector 存储
4. status='ready', chunk_count=N

### 2.6 等级门控机制

**用户角色 → 内容等级映射**:

| 角色 | 角色等级 | 可访问内容 |
|------|---------|-----------|
| observer | 1 | L0 |
| grower | 2 | L0-L1 |
| sharer | 3 | L0-L2 |
| coach | 4 | L0-L3 |
| promoter/supervisor | 5 | L0-L4 |
| master/admin | 6 | L0-L5 |

**门控行为**:
- 可访问: 返回完整 body + media_url
- 不可访问: 隐藏 body + video_url, 返回 `access_status: {reason: "需完成L2 分享者才能解锁", unlock_level: "L2"}`
- 始终显示: 标题、封面、统计数据

### 2.7 测验评分系统

**评分逻辑** (`POST /video/{id}/quiz/submit`):

1. **次数检查**: `attempts >= max_attempts` → 400 错误
2. **答案比较**:
   - 多选题: 集合相等 (`set(user) == set(expected)`)
   - 单选题: 字符串相等
   - 判断题: 字符串相等
3. **计分**: `score = (correct_count / total_count) * 100`
4. **通过判定**: `passed = (score >= exam.passing_score)`
5. **积分奖励**:
   - 通过: 10 积分
   - 满分 (100): 额外 5 积分
   - 类别: growth (成长)
6. **更新**: UserLearningStats.quiz_total++, quiz_passed++

### 2.8 学习进度与连续打卡

**连续打卡算法**:

```python
if last_learn_date != today:
    if last_learn_date == yesterday:
        current_streak += 1
    else:
        current_streak = 1  # 断连重置
    if current_streak > longest_streak:
        longest_streak = current_streak
    last_learn_date = today
```

**时间聚合**:
- `today_minutes`: WHERE earned_at >= today 00:00
- `week_minutes`: WHERE earned_at >= 本周一 00:00
- `month_minutes`: WHERE earned_at >= 本月 1 号 00:00

**互动 Toggle 模式** (点赞/收藏/有帮助):
```
若已存在 (user_id, content_id) → DELETE + count--
若不存在 → INSERT + count++ + 记录活动日志
```

**反范式缓存策略**:
- ContentItem 维护 `view_count`, `like_count`, `comment_count`, `collect_count` (原子更新, 无需 COUNT 子查询)
- UserLearningStats 维护单条汇总记录 (即时更新, 仪表板/排行榜快读)

---

## 第三部分: 知识共享体系

### 3.1 共享服务

**文件**: `core/knowledge/sharing_service.py` (277 行)

| 函数 | 作用 |
|------|------|
| `contribute_document(db, doc_id, tenant_id, contributor_id, domain_id, reason)` | 专家提交私有知识到领域共享 |
| `approve_contribution(db, contribution_id, reviewer_id, comment)` | 管理员批准 (文档+分片 scope→domain) |
| `reject_contribution(db, contribution_id, reviewer_id, comment)` | 管理员拒绝 |
| `revoke_contribution(db, contribution_id, tenant_id)` | 专家撤回 (scope→tenant) |
| `list_contributions(db, status, domain_id, tenant_id, skip, limit)` | 贡献列表 |
| `list_domain_shared_documents(db, domain_id, skip, limit)` | 领域知识库浏览 |
| `get_sharing_stats(db)` | 统计 (按状态/领域) |

**贡献验证规则**:
- 文档必须属于该租户
- 文档 scope 必须为 'tenant' (私有)
- 文档 status 必须为 'ready' (已发布)
- 不允许重复 pending 贡献

**批准操作链**:
1. contribution.status = 'approved'
2. document.scope = 'domain', domain_id = 目标领域
3. **同步所有分片**: UPDATE knowledge_chunks SET scope='domain', domain_id=... WHERE document_id=...
4. 记录 reviewer + reviewed_at

**撤回操作链**:
1. 验证 contribution 为 approved + 属于该租户
2. document.scope = 'tenant'
3. 分片 scope 回退 'tenant'
4. contribution.status = 'revoked'

### 3.2 共享 API (9 端点)

**文件**: `api/knowledge_sharing_api.py`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/v1/knowledge-sharing/contribute` | 用户 (租户) | 提交贡献 |
| GET | `/v1/knowledge-sharing/my-contributions` | 用户 | 我的贡献列表 |
| POST | `/{id}/revoke` | 用户 (租户) | 撤回 |
| GET | `/v1/knowledge-sharing/review-queue` | coach+ | 审核队列 |
| POST | `/{id}/approve` | coach+ | 批准 |
| POST | `/{id}/reject` | coach+ | 拒绝 |
| GET | `/v1/knowledge-sharing/domain-pool` | 用户 | 领域知识库 |
| GET | `/v1/knowledge-sharing/stats` | coach+ | 共享统计 |
| GET | `/v1/knowledge-sharing/domains` | 用户 | 可用领域列表 |

### 3.3 状态流转

```
pending ──→ approved ──→ revoked
    ↘──→ rejected
```

- **pending**: 等待管理员审核 (典型 72h)
- **approved**: 文档进入领域作用域, RAG 检索可见
- **rejected**: 贡献被拒, 文档保持私有
- **revoked**: 专家主动撤回, 文档回归私有

---

## 第四部分: Agent 反馈与生态

### 4.1 反馈学习环

**文件**: `core/feedback_service.py`

#### 反馈持久化

```python
def save_feedback(db, agent_id, user_id, feedback_type, rating, comment,
                  modifications, session_id, user_message, agent_response,
                  agents_used, confidence, processing_time_ms, tenant_id) -> AgentFeedback
```

**feedback_type**: accept / reject / modify / rate

#### 每日指标聚合

```python
def aggregate_daily_metrics(db, target_date=None)
# 调度: 每日 01:30 UTC
# 按 agent_id 分组计算:
#   feedback_count, accept/reject/modify/rate_count
#   acceptance_rate = accept_count / feedback_count
#   avg_rating = total_rating / rate_count
#   avg_processing_ms, avg_confidence
# UPSERT 到 AgentMetricsDaily
```

#### 成长报告

```python
def get_agent_growth_report(db, agent_id, days=30) -> dict
# 返回:
#   summary: total_feedback, acceptance_rate, avg_rating, trend_acceptance_7d
#   daily_metrics: 逐日指标数组
#   prompt_versions: 最近 5 个版本及其指标
```

#### Prompt 版本管理

```python
def create_prompt_version(db, agent_id, system_prompt, change_reason,
                          created_by, activate=True) -> AgentPromptVersion
# 1. 获取最大版本号 + 1
# 2. 快照前 30 天指标 (prev_avg_rating, prev_acceptance_rate)
# 3. 创建版本记录
# 4. 激活 → 停用旧版 + 同步 AgentTemplate.system_prompt
# 5. 支持 A/B 测试: traffic_pct 字段
```

#### 数据模型

**AgentFeedback**:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `agent_id` | String(32), indexed | Agent 标识 |
| `user_id` | Integer FK(users) | 反馈者 |
| `session_id` | String(100) | 会话 |
| `feedback_type` | String(20) | accept/reject/modify/rate |
| `rating` | Integer 1-5 | 星级评分 |
| `comment` | Text | 文字反馈 |
| `modifications` | JSON | 修改建议 |
| `user_message` | Text | 用户原始查询 |
| `agent_response` | Text | Agent 响应快照 |
| `agents_used` | JSON | 参与 Agent 列表 |
| `confidence` | Float | 置信度 |
| `processing_time_ms` | Integer | 延迟 (ms) |
| `tenant_id` | String(64) | 租户 |
| `created_at` | DateTime | |

**AgentMetricsDaily**:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `agent_id` | String(32) | |
| `metric_date` | Date | UNIQUE(agent_id, metric_date) |
| `feedback_count` | Integer | 总反馈数 |
| `accept/reject/modify/rate_count` | Integer | 各类型计数 |
| `total_rating` | Integer | 评分总和 |
| `acceptance_rate` | Float | 接受率 |
| `avg_rating` | Float | 平均评分 |
| `avg_processing_ms` | Float | 平均延迟 |
| `avg_confidence` | Float | 平均置信度 |

**AgentPromptVersion**:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `agent_id` | String(32) | |
| `version` | Integer | UNIQUE(agent_id, version) |
| `system_prompt` | Text | 完整 Prompt |
| `change_reason` | Text | 变更理由 |
| `is_active` | Boolean | 当前生产版本 |
| `traffic_pct` | Integer default=100 | A/B 测试流量百分比 |
| `prev_avg_rating` | Float | 前版本快照 |
| `prev_acceptance_rate` | Float | 前版本快照 |
| `created_by` | Integer FK(users) | |

#### 反馈 API (8 端点)

**文件**: `api/agent_feedback_api.py`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/v1/agent-feedback/submit` | 用户 | 提交反馈 |
| GET | `/v1/agent-feedback/list` | coach+ | 反馈列表 |
| GET | `/v1/agent-feedback/growth/{agent_id}` | 用户 | 成长报告 |
| GET | `/v1/agent-feedback/summary` | 用户 | 全 Agent 汇总 |
| GET | `/v1/agent-feedback/metrics/{agent_id}` | 用户 | 日指标查询 |
| POST | `/v1/agent-feedback/prompt-version` | admin | 创建版本 |
| GET | `/v1/agent-feedback/prompt-versions/{agent_id}` | 用户 | 版本历史 |
| POST | `/v1/agent-feedback/aggregate` | admin | 手动触发聚合 |

### 4.2 Agent 市场

**文件**: `core/ecosystem_service.py`

#### 市场发布流程

```python
def publish_to_marketplace(db, template_id, publisher_id, tenant_id, title, description, category, tags)
    → AgentMarketplaceListing (status='submitted')
    → 奖励 "template_published" 成长积分 (30 分)

def approve_listing(db, listing_id, reviewer_id, comment)
    → status='published', 市场可见

def reject_listing(db, listing_id, reviewer_id, comment)
    → status='rejected'
```

#### 安装 (克隆)

```python
def install_template(db, listing_id, installer_id, target_tenant_id) -> AgentTemplate
# 1. 克隆源模板
# 2. 生成唯一 agent_id (递增后缀)
# 3. display_name 追加 "(安装)"
# 4. listing.install_count++
# 5. 奖励发布者 "template_installed" (5 分)
```

#### Agent 组合

```python
def create_composition(db, name, pipeline, created_by, description, tenant_id, merge_strategy)
    → AgentComposition
    → 奖励 "composition_created" (15 分)
```

**Pipeline JSON**:
```json
[
  {"agent_id": "glucose", "order": 1, "condition": "always"},
  {"agent_id": "nutrition", "order": 2, "condition": "if:glucose.risk_level>low"},
  {"agent_id": "exercise", "order": 3, "condition": "optional"}
]
```

**merge_strategy**: `weighted_average` / `priority_first` / `consensus`

#### 数据模型

**AgentMarketplaceListing**:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `template_id` | Integer FK(agent_templates) | 模板 |
| `publisher_id` | Integer FK(users) | 发布者 |
| `tenant_id` | String(64) | 来源租户 |
| `title` | String(128) | 市场标题 |
| `description` | Text | 描述 |
| `category` | String(50) | 分类 |
| `tags` | JSON default=[] | 标签 |
| `status` | String(20) | draft/submitted/published/rejected/archived |
| `install_count` | Integer default=0 | 安装数 |
| `avg_rating` | Float default=0 | 市场评分 |
| `version` | String(20) default='1.0.0' | |

**AgentComposition**:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `name` | String(100) | |
| `description` | Text | |
| `tenant_id` | String(64) | NULL=平台级 |
| `pipeline` | JSON | Agent 编排定义 |
| `merge_strategy` | String(30) default='weighted_average' | |
| `is_enabled` | Boolean default=True | |
| `is_default` | Boolean default=False | 租户默认 |

#### 生态 API (12 端点)

**文件**: `api/agent_ecosystem_api.py`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/v1/agent-ecosystem/marketplace` | 用户 | 浏览市场 |
| POST | `/v1/agent-ecosystem/marketplace/publish` | 用户 | 提交发布 |
| GET | `/v1/agent-ecosystem/marketplace/pending` | admin | 审核队列 |
| POST | `marketplace/{id}/approve` | admin | 批准 |
| POST | `marketplace/{id}/reject` | admin | 拒绝 |
| POST | `marketplace/{id}/install` | 用户 | 安装模板 |
| GET | `marketplace/recommended` | 专家 | 领域推荐 |
| GET | `/v1/agent-ecosystem/compositions` | 用户 | 组合列表 |
| POST | `/v1/agent-ecosystem/compositions` | coach+ | 创建组合 |
| GET | `/v1/agent-ecosystem/compositions/{id}` | 用户 | 组合详情 |
| GET | `/v1/agent-ecosystem/growth-points` | 用户 | 我的成长积分 |
| GET | `/v1/agent-ecosystem/growth-points/config` | 用户 | 积分事件配置 |

### 4.3 成长积分体系

**7 种积分事件** (`GROWTH_POINT_EVENTS`):

| 事件 | 积分 | 说明 |
|------|------|------|
| `create_agent` | 20 | 创建自定义 Agent |
| `optimize_prompt` | 10 | 优化 Prompt |
| `share_knowledge` | 15 | 贡献知识到领域池 |
| `template_published` | 30 | 发布到市场 |
| `template_installed` | 5 | 被他人安装 (每次) |
| `feedback_positive` | 3 | 收到正面反馈 |
| `composition_created` | 15 | 创建 Agent 组合 |

**AgentGrowthPoints** 表:

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK(users) | 专家用户 |
| `agent_id` | String(32) | 相关 Agent |
| `event_type` | String(50) | 事件名 |
| `points` | Integer | 积分值 |
| `description` | String(255) | 事件描述 |
| `reference_id` | Integer | 关联 ID |
| `reference_type` | String(50) | template/listing/contribution |
| `created_at` | DateTime | |

---

## 第五部分: 问卷系统

### 5.1 问卷引擎

**文件**: `core/survey_service.py`

#### 13 种题型

| 类型 | 说明 | 评分 |
|------|------|------|
| `single_choice` | 单选 | option.score |
| `multiple_choice` | 多选 | - |
| `text_short` | 短文本 | - |
| `text_long` | 长文本 | - |
| `rating` | 星级评分 | value |
| `nps` | 净推荐值 (0-10) | value |
| `slider` | 滑杆 | value |
| `matrix_single` | 矩阵单选 | 列均分 |
| `matrix_multiple` | 矩阵多选 | - |
| `date` | 日期选择 | - |
| `file_upload` | 文件上传 | - |
| `section_break` | 分节符 | - |
| `description` | 说明文本 | - |

#### 短码访问

```python
def generate_short_code(length=6) -> str
# 字符集: a-zA-Z0-9 (62 字符)
# 组合数: 62^6 ≈ 568 亿
# 循环检测唯一性
```

#### 数据模型

**Survey** (5 表):

| 表 | 列数 | 说明 |
|----|------|------|
| `surveys` | 16 | 问卷主表 (short_code UNIQUE) |
| `survey_questions` | 10 | 题目 (13 种 question_type) |
| `survey_responses` | 14 | 答卷 (支持匿名 user_id=NULL) |
| `survey_response_answers` | 6 | 逐题答案 + 自动评分 |
| `survey_distributions` | 8 | 分发渠道 (7 种 channel) |

**Survey 设置** (settings JSON):
- `show_progress_bar`, `theme_color`, `welcome_message`
- `anonymous`, `require_login`
- `start_time`, `end_time`, `max_responses`
- `one_response_per_user`
- `thank_you_message`, `redirect_url`

**分发渠道**: link / qrcode / wechat / sms / email / embed / coach

#### 问卷 API (16 端点)

**管理** (`api/survey_api.py`, 10 端点):

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/api/v1/surveys` | coach+ | 创建问卷 |
| GET | `/api/v1/surveys` | coach+ | 我的问卷列表 |
| GET | `/api/v1/surveys/{id}` | coach+ | 问卷详情 |
| PATCH | `/api/v1/surveys/{id}` | coach+ | 更新 |
| DELETE | `/api/v1/surveys/{id}` | coach+ | 删除 |
| POST | `/api/v1/surveys/{id}/publish` | coach+ | 发布 |
| POST | `/api/v1/surveys/{id}/close` | coach+ | 关闭 |
| POST | `/api/v1/surveys/{id}/questions` | coach+ | 批量保存题目 |
| PUT | `/api/v1/surveys/{id}/questions/reorder` | coach+ | 排序 |
| DELETE | `/api/v1/surveys/{id}/questions/{qid}` | coach+ | 删题 |

**填写** (`api/survey_response_api.py`, 3 端点):

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/surveys/s/{short_code}` | 公开 | 获取问卷表单 |
| POST | `/api/v1/surveys/s/{short_code}/submit` | 可选 | 提交答卷 |
| POST | `/api/v1/surveys/s/{short_code}/save-draft` | 可选 | 保存草稿 |

**统计** (`api/survey_stats_api.py`, 3 端点):

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/api/v1/surveys/{id}/stats` | coach+ | 统计分析 |
| GET | `/api/v1/surveys/{id}/responses` | coach+ | 答卷列表 |
| GET | `/api/v1/surveys/{id}/export` | coach+ | CSV 导出 |

### 5.2 BAPS 回流

```python
def _sync_to_baps(self, survey, answers, user_id)
# survey.baps_mapping 定义字段映射
# 转换类型:
#   direct:            直接透传 value
#   scale_1_5_to_1_10: 乘以 2
#   option_to_number:  传递 option.score
#   matrix_row:        提取单元格值
# 更新 BehavioralProfile 对应属性
```

**回流触发**: 仅在 `baps_mapping` 配置且 `user_id` 非空时执行

### 5.3 统计与导出

**统计指标** (`get_stats`):
- **汇总**: total_responses, complete_responses, completion_rate, avg_duration_sec
- **按题型**:
  - 单选/多选: 选项分布 + 百分比
  - 评分/滑杆: avg, min, max, count
  - NPS: nps_score, promoters, passives, detractors
  - 矩阵单选: 逐行 avg_score + 列分布
  - 文本: 仅 response_count

**CSV 导出** (`export_csv`):
- 表头: 回收ID, 填写者, 填写时间, 耗时(秒), + 各题标题(50 字符)
- 编码: UTF-8 with BOM (Excel 兼容)

---

## 第六部分: 数据分析

### 6.1 管理员分析 (7 端点)

**文件**: `api/admin_analytics_api.py`, 权限: admin

| 端点 | 功能 | 返回 |
|------|------|------|
| GET `/v1/analytics/admin/overview` | 平台 KPI 概览 | total_users, active_users, coach_count, high_risk_count |
| GET `/v1/analytics/admin/user-growth` | 用户增长趋势 | months[], new_users[], cumulative[] |
| GET `/v1/analytics/admin/role-distribution` | 角色分布 (饼图) | roles[], labels[], counts[] |
| GET `/v1/analytics/admin/stage-distribution` | 行为阶段分布 (柱状) | stages[S0-S6], labels[], counts[] |
| GET `/v1/analytics/admin/risk-distribution` | 风险等级分布 | levels[R0-R4], labels[], counts[] |
| GET `/v1/analytics/admin/coach-leaderboard` | 教练排行榜 | coach_id, name, student_count, completion_rate |
| GET `/v1/analytics/admin/challenge-effectiveness` | 挑战效果 | title, enrolled, completed, completion_rate |

**教练排行榜算法**:
1. 查询所有活跃 coach
2. 统计每个 coach 的学生数
3. 查最近 30 天 MicroActionTask 完成率
4. 按 completion_rate 降序排列

**行为阶段标签**:

| 阶段 | 标签 |
|------|------|
| S0 | 觉醒期 |
| S1 | 松动期 |
| S2 | 探索期 |
| S3 | 准备期 |
| S4 | 行动期 |
| S5 | 坚持期 |
| S6 | 融入期 |

**风险等级标签**:

| 等级 | 标签 |
|------|------|
| R0 | 正常 |
| R1 | 轻度 |
| R2 | 中度 |
| R3 | 高度 |
| R4 | 危机 |

---

## 第七部分: 安全治理

### 7.1 安全关键词配置

**文件**: `configs/safety_keywords.json`

| 类别 | 数量 | 示例 |
|------|------|------|
| `crisis` (危机) | 15 | 自杀, 自残, 不想活, 结束生命, 跳楼, 割腕 |
| `warning` (警告) | 15 | 活着没意思, 崩溃, 绝望, 没有希望, 生不如死 |
| `blocked` (封禁) | 7 | 代购药物, 违禁药品, 毒品, 非法行医 |
| `medical_advice` (医嘱) | 12 | 开药, 处方, 推荐药物, 诊断, 确诊 |

### 7.2 安全规则配置

**文件**: `configs/safety_rules.json`

```json
{
  "thresholds": {
    "max_input_length": 5000,
    "max_output_length": 8000,
    "crisis_auto_escalate": true,
    "pii_log_enabled": false,
    "disclaimer_always_append": false,
    "review_queue_enabled": true
  },
  "evidence_tier_weights": {
    "T1": 1.0, "T2": 0.8, "T3": 0.5, "T4": 0.2
  },
  "severity_levels": {
    "critical": {"action": "block_and_escalate", "notify_admin": true, "log_input": true},
    "high":     {"action": "flag_for_review",     "notify_admin": true, "log_input": true},
    "medium":   {"action": "add_disclaimer",      "notify_admin": false, "log_input": true},
    "low":      {"action": "pass",                "notify_admin": false, "log_input": false}
  },
  "escalation_contacts": {
    "crisis_hotline": "400-161-9995",
    "admin_notification": true
  }
}
```

### 7.3 SafetyLog 模型

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | |
| `user_id` | Integer FK(users), indexed | 触发用户 |
| `event_type` | String(30), indexed | input_blocked/output_filtered/crisis_detected/daily_report |
| `severity` | String(15), indexed | low/medium/high/critical |
| `input_text` | Text | 输入文本 |
| `output_text` | Text | 输出文本 |
| `filter_details` | JSON | 过滤详情 |
| `resolved` | Boolean default=False, indexed | 是否已处理 |
| `resolved_by` | Integer FK(users) | 处理人 |
| `resolved_at` | DateTime | 处理时间 |
| `created_at` | DateTime | |

---

## 第八部分: 调度系统

### 8.1 13 个定时任务总表

**文件**: `core/scheduler.py`, 引擎: APScheduler AsyncIOScheduler

| 任务 | 触发 | 频率 | Redis 锁 | 说明 |
|------|------|------|---------|------|
| `daily_task_generation` | Cron 06:00 | 日 | 600s | 生成每日微行动 |
| `reminder_check` | Interval 1min | 分 | 60s | 触发到期提醒 |
| `expired_task_cleanup` | Cron 23:59 | 日 | 300s | 过期任务标记 |
| `process_approved_pushes` | Interval 5min | 分 | 300s | 推送已审核内容 |
| `expire_stale_queue_items` | Cron 06:30 | 日 | 300s | 清理 72h+ 待审项 |
| `knowledge_freshness_check` | Cron 07:00 | 日 | 300s | **过期文档降权** (priority-=2) |
| `program_advance_day` | Cron 00:05 | 日 | 600s | V004: 方案日推进 |
| `program_push_morning` | Cron 09:00 | 日 | 300s | V004: 晨推 |
| `program_push_noon` | Cron 11:30 | 日 | 300s | V004: 午推 |
| `program_push_evening` | Cron 17:30 | 日 | 300s | V004: 晚推 |
| `program_batch_analysis` | Cron 23:00 | 日 | 600s | V004: 行为分析 |
| `safety_daily_report` | Cron 02:00 | 日 | 600s | **V005: 安全日报聚合** |
| `agent_metrics_aggregate` | Cron 01:30 | 日 | 600s | **Phase 4: 反馈指标聚合** |

**知识/数据相关** (加粗标注):
- `knowledge_freshness_check` (07:00): 查找过期文档 → priority -= 2 (最小 1)
- `safety_daily_report` (02:00): 聚合昨日 SafetyLog → 写入 daily_report
- `agent_metrics_aggregate` (01:30): 聚合昨日 AgentFeedback → AgentMetricsDaily

### 8.2 Redis 分布式锁

**文件**: `core/redis_lock.py`

```python
@with_redis_lock("namespace:job_name", ttl=600)
def job_function():
    pass
```

- **模式**: SETNX (Set If Not Exists) + TTL
- **优雅降级**: Redis 不可用时任务照常执行 (无锁保护)
- **TTL**: 防止任务崩溃后死锁
- **防重复**: 并发 Worker 看到 key 存在则跳过

---

## 第九部分: 迁移记录

| 迁移号 | 日期 | 内容 |
|--------|------|------|
| 011 | 2026-02-07 | knowledge_documents + knowledge_chunks + knowledge_citations |
| 012 | 2026-02-07 | raw_content, evidence_tier, review_status 治理列 |
| 017 | 2026-02-08 | knowledge_domains + file_hash UNIQUE |
| 021 | 2026-02-11 | safety_logs + content_audio (V005) |
| 024 | 2026-02-12 | knowledge_contributions + scope 归一化 (global→platform) |
| 025 | 2026-02-12 | agent_feedbacks + agent_metrics_daily + agent_prompt_versions |
| 026 | 2026-02-12 | agent_marketplace_listings + agent_compositions + agent_growth_points |

---

## 第十部分: 文件索引

### 核心知识服务

| 组件 | 文件路径 | 关键导出 |
|------|---------|---------|
| 嵌入服务 | `core/knowledge/embedding_service.py` | `EmbeddingService.embed_query/embed_batch` |
| 分片器 | `core/knowledge/chunker.py` | `chunk_markdown()` |
| 检索引擎 | `core/knowledge/retriever.py` | `KnowledgeRetriever.retrieve()`, `Citation`, `RAGContext` |
| RAG 中间件 | `core/knowledge/rag_middleware.py` | `rag_enhance()`, `RAGEnhancedContext`, `record_citations()` |
| 文档服务 | `core/knowledge/document_service.py` | `create/publish/approve/reject/handle_expired` |
| 文件转换 | `core/knowledge/file_converter.py` | `convert_file_to_markdown()` |
| 归档解压 | `core/knowledge/archive_extractor.py` | `extract_archive()` |
| 批量导入 | `core/knowledge/batch_ingestion_service.py` | `process_batch_upload()` |
| 知识共享 | `core/knowledge/sharing_service.py` | `contribute/approve/reject/revoke_contribution()` |

### 后端桥接

| 组件 | 文件路径 | 说明 |
|------|---------|------|
| 混合嵌入 | `backend/services/chunker.py` | SmartChunker + 双后端 EmbeddingService |
| 文档解析 | `backend/services/doc_parser.py` | DocumentParser (Markdown) |
| 异步导入 | `backend/services/ingest.py` | KnowledgeIngestor + 17 领域种子 |
| 模型重导出 | `backend/models/knowledge.py` | DocStatus, KnowledgeScope 枚举 |

### API 路由

| 组件 | 文件路径 | 端点数 |
|------|---------|--------|
| 内容浏览 | `api/content_api.py` | 28 |
| 内容管理 | `api/content_manage_api.py` | 8 |
| 用户投稿 | `api/content_contribution_api.py` | 7 |
| 专家工作室 | `api/expert_content_api.py` | 8 |
| 批量导入 | `api/batch_ingestion_api.py` | 4 |
| 知识共享 | `api/knowledge_sharing_api.py` | 9 |
| Agent 反馈 | `api/agent_feedback_api.py` | 8 |
| Agent 生态 | `api/agent_ecosystem_api.py` | 12 |
| 问卷管理 | `api/survey_api.py` | 10 |
| 问卷填写 | `api/survey_response_api.py` | 3 |
| 问卷统计 | `api/survey_stats_api.py` | 3 |
| 管理分析 | `api/admin_analytics_api.py` | 7 |
| 安全管理 | `api/safety_api.py` | 8 |
| **总计** | | **115 端点** |

### 数据模型

| 模块 | 表数 | 定义位置 |
|------|------|---------|
| 知识库 | 6 | core/models.py |
| 内容系统 | 8 | core/models.py |
| Agent 反馈 | 3 | core/models.py |
| Agent 生态 | 3 | core/models.py |
| 问卷系统 | 5 | core/models.py |
| 安全日志 | 1 | core/models.py |
| **总计** | **26 表** | |

### 配置文件

| 文件 | 说明 |
|------|------|
| `configs/safety_keywords.json` | 4 类安全关键词 (49 个) |
| `configs/safety_rules.json` | 阈值/证据权重/严重级别/升级联系 |
| `configs/expert_domains.json` | 10 专家领域 + 颜色/主题/推荐 Agent |

---

## 附录 A: 数据流图谱

### A.1 知识共享 → RAG 检索

```
ExpertTenant (专家)
    ↓ create_document()
KnowledgeDocument (scope=tenant, status=ready)
    ↓ contribute_document()
KnowledgeContribution (status=pending)
    ↓ approve_contribution()
Document scope → domain, Chunks scope → domain
    ↓
KnowledgeRetriever.retrieve()  ← 其他专家同领域可检索到
    ↓ SCOPE_BOOST[domain] = +0.08
RAGContext → Prompt 注入 → LLM 生成
```

### A.2 反馈 → Agent 优化

```
用户对 Agent 响应评价
    ↓ save_feedback()
AgentFeedback (agent_id, rating, type)
    ↓ 调度 01:30 aggregate_daily_metrics()
AgentMetricsDaily (acceptance_rate, avg_rating)
    ↓ get_agent_growth_report()
管理员分析 → create_prompt_version() → 新版本上线
    ↓ 同步 AgentTemplate.system_prompt
Agent 运行时使用新 Prompt
```

### A.3 问卷 → BAPS 用户画像

```
Coach 创建问卷 + 配置 baps_mapping
    ↓ publish_survey()
用户通过 short_code 访问 → 填写 → submit_response()
    ↓ _sync_to_baps()
BehavioralProfile 属性更新 (scale/option/matrix 转换)
    ↓
Agent 对话时参考用户画像
```

### A.4 安全 → 日报 → 管理

```
Agent LLM 调用
    ↓ SafetyPipeline (4 层过滤)
        L1 input_filter  → 关键词/PII/意图
        L2 rag_safety    → 证据权重/过期
        L3 generation_guard → Prompt 注入/领域边界
        L4 output_filter → 医嘱声明/免责/分级
    ↓ SafetyLog (event_type, severity)
调度 02:00 safety_daily_report()
    ↓ 聚合昨日 by_severity + by_event_type
管理员通知 (如有 critical 事件)
```

### A.5 生态积分 → 教练等级

```
专家操作 (创建Agent/发布市场/共享知识/...)
    ↓ award_points() → AgentGrowthPoints
get_user_growth_points()
    ↓ 积分汇总
教练六级体系 (growth + contribution + influence 三维)
    ↓ _compute_user_level()
角色晋升 (L0→L5)
```

---

> **文档覆盖**: 6 个数据库模块 (26 表), 13 个 API 路由 (115 端点), 18 个核心服务文件, 7 个迁移,
> 13 个调度任务, 3 个配置文件
> **生成日期**: 2026-02-14
> **项目位置**: `D:\behavioral-health-project`

---

## 第十一部分: Claude Code 集成规范

### 11.1 知识包与 Agent 配置的隔离原则

| 类别 | 目录 | 用途 | 是否纳入 RAG |
|------|------|------|:------------:|
| 知识包 (Knowledge) | `knowledge/kb_*/**/*.md` | 分块 → 嵌入 → 向量检索 | **是** |
| Agent 配置 (System Prompt) | `docs/agents/*.md` | Agent 初始化注入 (system prompt) | **否** |

**铁律**: `docs/agents/` 目录下的 Agent 配置文件（system prompt）**只用于 Agent 初始化注入，不纳入 RAG 入库流程**，与知识包严格隔离。

- `docs/agents/` 中的文件由 `AgentTemplate.system_prompt` 或 `GenericLLMAgent` 在初始化时直接读取，作为 system message 注入 LLM 上下文
- `knowledge/` 中的文件由 `scripts/ingest_knowledge.py` 入库，经分块（`core/knowledge/chunker.py`）→ 嵌入（`EmbeddingService`）→ 写入 `knowledge_chunks` 表，供 RAG 检索引擎使用
- 两套流程互不交叉：知识包不作为 system prompt，Agent 配置不进入向量库
- 若 Agent 需引用知识库内容，应通过 RAG 中间件（`core/knowledge/rag_middleware.py`）在运行时检索注入，而非将知识文件复制到 `docs/agents/`

### 11.2 docs/agents/ 目录约定

```
docs/agents/
├── metabolic_agent.md        # 代谢专家 Agent system prompt
├── sleep_agent.md            # 睡眠专家 Agent system prompt
├── emotion_agent.md          # 情绪专家 Agent system prompt
├── motivation_agent.md       # 动机专家 Agent system prompt
├── nutrition_agent.md        # 营养专家 Agent system prompt
├── exercise_agent.md         # 运动专家 Agent system prompt
├── tcm_agent.md              # 中医体质 Agent system prompt
├── crisis_agent.md           # 危机干预 Agent system prompt
├── vision_agent.md           # 视力守护 Agent system prompt
└── ...
```

文件命名规范: `<agent_name>_agent.md`，内容为纯 Markdown，首行 `# <Agent 中文名>` 标题。
