# 行为健康数字平台 - 更新日志

## v11 更新内容（自第10版 f2fd215 以来的修正）

> 基线: commit `f2fd215` (2026-01-31) "feat: add Dify deep integration with auto-fallback to Ollama"
> 更新日期: 2026-02-01

---

### 1. 核心修复与增强

#### `main.py` - 决策引擎主入口
- **[新增] Ollama 智能回退机制**: `/chat_sync` 端点增加 Dify 可达性探测（2秒超时），Dify 不可用时自动回退 Ollama 本地模型（qwen2.5:14b）
- **[新增] 健康教练系统提示词**: 回退 Ollama 时注入专业行为健康教练角色 + 当前血糖状态上下文
- **[新增] 响应来源标识**: 返回 `source` 字段（"dify" / "ollama" / "error"），前端可据此展示数据来源
- **[依赖新增]** `import httpx, os` 用于 Ollama HTTP 调用和环境变量读取

#### `patient_portal.html` - 患者对话页面
- **[修复] 对话接口调用**: 从 `/chat`（SSE 流式）改为 `/chat_sync`（JSON 同步），匹配前端 `data.reply` 解析逻辑

#### `core/master_agent.py`
- **[删除]** 移除废弃的 master_agent 模块（6801 行），功能已迁移至 `core/decision_core.py`

#### `data/profiles/test-integration-user.json`
- **[更新]** 测试用户档案数据更新

---

### 2. 未提交新增文件清单（自 v10 平台提交后开发的全部新功能）

#### 后端核心 (core/)
| 文件 | 说明 |
|------|------|
| `core/decision_core.py` | 决策引擎核心（TriggerEngine + Dify 调用） |
| `core/decision_models.py` | 决策数据模型（DecisionContext, DecisionOutput） |
| `core/dify_client.py` | Dify API 客户端（缓存/流式/blocking 自适应） |
| `core/trigger_engine.py` | 触发标签引擎（血糖触发识别） |
| `core/trigger_engine_v0.py` | 触发引擎 v0 备份 |
| `core/assessment_engine.py` | L2 评估引擎 |
| `core/auth.py` | JWT 认证模块 |
| `core/database.py` | 数据库连接管理 |
| `core/models.py` | SQLAlchemy ORM 模型 |
| `core/multimodal_client.py` | 多模态系统客户端 |
| `core/master_agent_v0.py` | Master Agent v0 备份 |

#### API 层 (api/)
| 文件 | 说明 |
|------|------|
| `api/assessment_api.py` | 评估 API 路由 |
| `api/auth_api.py` | 认证 API（登录/注册） |
| `api/chat_history.py` | 聊天历史管理 |
| `api/dependencies.py` | FastAPI 依赖注入 |
| `api/device_data.py` | 设备数据 API（CGM 等） |
| `api/device_trigger.py` | 设备触发路由 |
| `api/llm_service.py` | LLM 服务封装 |

#### Agent 系统 (agents/)
| 文件 | 说明 |
|------|------|
| `agents/base_agent.py` | Agent 基类 |
| `agents/snapshot_factory.py` | 快照工厂 |

#### 前端 - 患者应用 (h5-patient-app/) **[全新]**
| 模块 | 文件数 | 说明 |
|------|--------|------|
| views/ | 10 | 首页/登录/注册/对话/数据录入/分析/历史/设置/健康数据/结果 |
| api/ | 5 | auth/assessment/chat/device/request |
| stores/ | 4 | user/assessment/chat/device |
| components/ | 3 | DataInputForm/RiskCard/TriggerList |
| router/ | 1 | Vue Router 路由配置 |

#### 运维与测试
| 文件 | 说明 |
|------|------|
| `main.py` | 决策引擎 FastAPI 入口（:8002） |
| `cli.py` | CLI 命令行工具 |
| `cgm_simulator.py` | CGM 血糖模拟器 |
| `start_all.bat` | 一键启动全部服务 |
| `stop_all.bat` | 一键停止全部服务 |
| `requirements.txt` | Python 依赖清单 |
| `setup.py` | 项目安装配置 |
| `scripts/create_mock_cases.py` | Mock 测试数据生成 |
| `scripts/seed_data.py` | 种子数据导入 |
| `tests/test_end_to_end.py` | 端到端测试 |
| `tests/test_multimodal_integration.py` | 多模态集成测试 |

#### 知识库
| 文件 | 说明 |
|------|------|
| `knowledge/triggers/trigger-tags-v1.json` | 触发标签定义 v1 |
| `knowledge/triggers/README.md` | 触发系统文档 |

#### 文档
| 文件 | 说明 |
|------|------|
| `QUICKSTART.md` | 快速开始指南 |
| `PROJECT_SUMMARY.md` | 项目总结 |
| `IMPLEMENTATION_SUMMARY.md` | 实现总结 |
| `H5_IMPLEMENTATION_PLAN.md` | H5 实现方案 |
| `MINIAPP_DIFY_ARCHITECTURE.md` | 小程序+Dify 架构 |
| `MOCK_CASES_GUIDE.md` | Mock 案例指南 |
| `docs/DEVICE_DATA_API_DESIGN.md` | 设备数据 API 设计 |
| `docs/L2_ASSESSMENT_ENGINE.md` | L2 评估引擎文档 |
| `docs/PROJECT_ROADMAP.md` | 项目路线图 |
| `docs/UI_DESIGN_SPEC.md` | UI 设计规范 |

---

### 3. 服务架构一览

```
┌─────────────────────────────────────────────────────────┐
│                    前端服务 (Vite)                        │
├──────────────┬──────────────┬───────────────────────────┤
│ h5 移动端     │ admin-portal │ h5-patient-app            │
│ :5173        │ :5174        │ :5175                     │
└──────┬───────┴──────┬───────┴──────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│                   后端 API (FastAPI/Uvicorn)              │
├──────────────┬──────────────┬───────────────────────────┤
│ Agent Gateway│ BAPS 评估 API │ 决策引擎 + 教练            │
│ :8000        │ :8001        │ :8002                     │
└──────┬───────┴──────┬───────┴──────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│              AI / 基础设施                                │
├──────────────┬──────────────┬───────────────────────────┤
│ Dify 平台     │ Ollama LLM   │ PostgreSQL / Redis /       │
│ :8080 (Docker)│ :11434       │ Weaviate (Docker)         │
└──────────────┴──────────────┴───────────────────────────┘
```
