# 行为健康平台 · 本地测试套件

## Knowledge RAG v2 · 本地知识优先 测试方案

### 快速开始

```bash
# 1. 确保 backend 源码在正确位置
cp -r backend/ tests/../backend/   # 如尚未就位

# 2. 一键运行全部测试
bash tests/run_all_tests.sh

# 3. 或者单独运行某层
python tests/test_00_preflight.py                    # 预飞检查
python -m pytest tests/test_01_models.py -v          # 模型定义
python -m pytest tests/test_02_database.py -v        # 数据库
python -m pytest tests/test_03_services.py -v        # 服务层
python -m pytest tests/test_04_api.py -v             # API
python -m pytest tests/test_05_e2e.py -v             # 端到端
```

### 测试分层策略

```
Layer 0: 预飞检查         ← 环境/依赖/数据库连接
  ↓ 通过
Layer 1: 模型定义         ← 枚举值/表名/列定义/数据类
  ↓ 通过
Layer 2: 数据库操作       ← CRUD/pgvector/scope过滤
  ↓ 通过
Layer 3: 服务层           ← 解析/分块/向量化/检索逻辑
  ↓ 通过
Layer 4: API端点          ← 路由/参数/响应格式
  ↓ 通过
Layer 5: 端到端           ← 文件→入库→检索→RAG增强→前端
  ↓ 全部通过
🎉 可以部署!
```

**原则: 每层只测试自己的职责，失败时立即定位问题层。**

### 各层详解

| 测试文件 | 测试数 | 依赖 | 耗时 | 作用 |
|---------|--------|------|------|------|
| `test_00_preflight.py` | ~15 | 无 | <1s | Python/依赖包/DB连接/pgvector/模型缓存 |
| `test_01_models.py` | ~18 | 无DB | <2s | 枚举值、表名、列定义、Citation序列化、SCOPE_BOOST、Agent映射 |
| `test_02_database.py` | ~10 | PostgreSQL | <5s | 连接、pgvector运算、CRUD、embedding插入、向量检索、scope加权SQL |
| `test_03_services.py` | ~15 | 部分需模型 | 10-30s | 文档解析(md/txt)、分块、向量化质量、检索逻辑、入库逻辑 |
| `test_04_api.py` | ~12 | 需完整app | <5s | 路由定义、请求参数、响应格式、错误处理 |
| `test_05_e2e.py` | ~8 | 全部 | 30-60s | 完整入库流程、去重、向量检索、scope优先级、RAG回复解析、前端数据契约 |

### RAG v2 关键测试点

1. **scope 加权检索** (`test_02`, `test_05`)
   - tenant +0.15 > domain +0.08 > platform +0.00
   - SQL 层面验证 boosted_score 排序

2. **Prompt 注入内容** (`test_01`)
   - "本地知识优先"
   - "[1][2]" 引用标记
   - "【补充】" 模型标记
   - "禁止编造"
   - "以本地资料为准"

3. **模型补充提取** (`test_01`, `test_05`)
   - 【补充】、【模型补充】、【补充说明】
   - 【以下为通用专业知识...】
   - 正确提取段落内容

4. **前端数据契约** (`test_05`)
   - Citation.to_dict() 匹配 Vue props
   - format_response() 包含所有 v2 新字段
   - scope 标签格式正确

### 环境准备 Checklist

```
□ Python >= 3.10
□ pip install sqlalchemy asyncpg alembic pydantic fastapi uvicorn pyyaml
□ pip install pgvector sentence-transformers
□ pip install pytest httpx  (测试框架)
□ PostgreSQL 运行中 + pgvector 扩展已安装
□ 数据库表已通过 Alembic 迁移创建
□ 环境变量 DATABASE_URL 已设置 (或使用默认值)
□ Embedding 模型已下载 (首次约 400MB)
```

### 故障排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `pgvector 扩展未安装` | PostgreSQL 缺少扩展 | `CREATE EXTENSION vector;` |
| `知识库表不存在` | 未运行迁移 | `alembic upgrade head` |
| `embedding 列类型异常` | 迁移脚本问题 | 检查 `002_add_knowledge_tables.py` |
| `Embedding 模型不可用` | 首次未下载 | `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('shibing624/text2vec-base-chinese')"` |
| `FastAPI app 未能导入` | 项目结构不匹配 | 检查 `main.py` 位置和 `PYTHONPATH` |
| `向量检索无结果` | chunks 表为空 | 先运行入库脚本 |
