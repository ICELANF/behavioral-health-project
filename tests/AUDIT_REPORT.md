# 测试套件审计报告 — 对照实际代码逐项比对

> 审计日期: 2026-02-08
> 对照文件: platform-architecture-overview.md (v21) + 16个实际代码文件

---

## 🔴 必须修复 (3处硬伤 — 不修会直接 ImportError / AssertionError)

### 1. test_01_models.py — 枚举类名错误

| 位置 | 测试假设 | 实际代码 (knowledge.py) |
|------|---------|----------------------|
| 第27行 | `from models.knowledge import ... VisibilityScope` | **实际名: `KnowledgeScope`** |
| 第39行 | `from models.knowledge import VisibilityScope` | 同上 |

**影响**: `ImportError: cannot import name 'VisibilityScope'` → test_01 全层崩溃

### 2. test_01_models.py — 租户模型类名错误

| 位置 | 测试假设 | 实际代码 (tenant.py) |
|------|---------|---------------------|
| 第71行 | `from models.tenant import ExpertTenant, TenantConfig, TenantPersona` | **实际: `ExpertTenant, TenantClient, TenantAgentMapping, TenantAuditLog`** |
| 第75行 | 同上 | 没有 `TenantConfig` 和 `TenantPersona` 类 |

**影响**: `ImportError: cannot import name 'TenantConfig'` → TestTenantModels 全部失败

### 3. test_00_preflight.py — 租户表名错误

| 位置 | 测试假设 | 实际表名 |
|------|---------|---------|
| 第154行 | `tenant_configs, tenant_personas, billing_records` | **`tenant_clients, tenant_agent_mappings, tenant_audit_logs`** |

**影响**: 预飞检查误报 "租户表缺失" → 误导判断，可能阻断后续测试

---

## 🟡 注意事项 (不影响通过，但需知晓)

### 4. Agent ID 命名差异 — 架构总览 vs 代码

| 架构总览 (12个) | retriever.py 代码 (12个) | 说明 |
|----------------|-------------------------|------|
| `metabolic` | `glucose` | 代码聚焦血糖 |
| `emotion` | `stress` | 代码聚焦压力 |
| `coaching` | ❌ 不存在 | 代码中无此Agent |
| ❌ 不存在 | `mental` | 代码中有, 架构中无 |

测试中的 `expected_agents` **已正确匹配代码**而非架构总览，所以能通过。
但这意味着集成时 Agent ID 映射可能需要对齐。

### 5. test_03 中 _format_ref_block 调用方式

`_format_ref_block` 是 `@staticmethod`，测试通过实例调用 `retriever._format_ref_block(c, row)`。
Python 允许通过实例调用静态方法，所以**不会报错**，但不够规范。

### 6. test_05 中的去重逻辑

`test_ingest_dedup` 假设重复入库返回相同 doc_id 或 None。
实际 `KnowledgeIngestor.ingest_file()` 的去重行为取决于 file_hash 查询逻辑。
需确认实际实现是返回已有 ID 还是抛异常。

---

## ✅ 已验证正确的部分

| 测试 | 验证项 | 状态 |
|------|--------|------|
| test_01 | SCOPE_BOOST 值 (tenant=0.15, domain=0.08, platform=0.0) | ✅ 匹配 |
| test_01 | Citation.to_dict() 返回字段 | ✅ 匹配 |
| test_01 | scope_label 映射 (🔒/📂/🌐) | ✅ 匹配 |
| test_01 | _extract_model_supplements 4种标记 | ✅ 匹配 |
| test_01 | _build_injection 6条关键指令 | ✅ 匹配 |
| test_01 | _build_no_knowledge_injection 内容 | ✅ 匹配 |
| test_02 | 知识库4张表名 | ✅ 匹配 |
| test_02 | embedding 列类型检测 | ✅ 匹配 |
| test_02 | boosted_score SQL 逻辑 | ✅ 匹配 |
| test_03 | DocumentParser / SmartChunker 接口 | ✅ 匹配 |
| test_03 | EmbeddingService 768维 | ✅ 匹配 |
| test_03 | DOMAIN_SEEDS 15个领域 | ✅ 匹配 |
| test_04 | knowledge router 路径/方法 | ✅ 匹配 |
| test_05 | RAGContext.format_response 完整结构 | ✅ 匹配 |
| test_05 | 前端数据契约 (Vue props) | ✅ 匹配 |
