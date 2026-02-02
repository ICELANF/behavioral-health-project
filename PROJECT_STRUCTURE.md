# 行为健康数字平台 - 完整项目结构

> 生成时间: 2026-02-01 | 版本: v11

```
D:\behavioral-health-project\
│
├── .env                              # 环境变量配置（含 Dify/DB/Redis 密钥）
├── .env.example                      # 环境变量模板
├── .gitignore
├── __main__.py                       # python -m behavioral_health 入口
├── main.py                           # 决策引擎 FastAPI 入口 (:8002)
├── cli.py                            # CLI 命令行工具
├── setup.py                          # pip install -e . 安装配置
├── requirements.txt                  # Python 依赖清单
├── config.yaml                       # 系统配置
├── architecture.yaml                 # 架构定义
├── docker-compose.yaml               # Dify Docker 编排
├── index.html                        # 指挥舱（静态看板）
├── patient_portal.html               # 患者对话页面（CGM + AI教练）
├── cgm_simulator.py                  # CGM 血糖数据模拟器
├── start_all.bat                     # 一键启动全部服务
├── stop_all.bat                      # 一键停止全部服务
├── start.bat / stop.bat / status.bat # 单独启停脚本
│
├── core/                             # ===== 核心引擎 =====
│   ├── __init__.py
│   ├── decision_core.py              # 决策核心（Trigger → Dify/Ollama）
│   ├── decision_models.py            # DecisionContext / DecisionOutput
│   ├── dify_client.py                # Dify API 客户端（缓存/流式/blocking）
│   ├── trigger_engine.py             # 触发标签识别引擎
│   ├── trigger_engine_v0.py          # 触发引擎 v0 备份
│   ├── assessment_engine.py          # L2 行为评估引擎
│   ├── auth.py                       # JWT 认证
│   ├── database.py                   # 数据库连接
│   ├── models.py                     # SQLAlchemy ORM 模型
│   ├── multimodal_client.py          # 多模态系统客户端
│   ├── master_agent_v0.py            # Master Agent v0 备份
│   ├── model_manager.py              # 模型管理器
│   ├── data_extractor.py             # 数据提取器
│   ├── limiter.py                    # 速率限制
│   ├── pipeline.py                   # 数据管道
│   ├── workflow.py                   # 工作流引擎
│   ├── baps/                         # BAPS 评估子系统
│   │   ├── __init__.py
│   │   ├── questionnaires.py         # 问卷定义
│   │   ├── scoring_engine.py         # 评分引擎
│   │   ├── report_generator.py       # 报告生成
│   │   └── question_bank.json        # 题库
│   └── schemas/                      # JSON Schema 定义
│       ├── core_data_schema.json
│       ├── assessment_schema.json
│       ├── user_profile_schema.json
│       ├── action_plan_schema.json
│       ├── agent_task_schema.json
│       ├── behavior_logic.json
│       ├── master_io_schema.json
│       ├── prescription_schema.json
│       ├── system_architecture.json
│       └── user_state_schema.json
│
├── api/                              # ===== API 路由层 =====
│   ├── __init__.py
│   ├── main.py                       # Agent Gateway 主入口 (:8000)
│   ├── baps_api.py                   # BAPS 评估 API (:8001)
│   ├── config.py                     # API 配置集中管理
│   ├── dify_service.py               # Dify 聊天服务封装
│   ├── assessment_api.py             # 评估 API
│   ├── auth_api.py                   # 认证 API（登录/注册）
│   ├── chat_history.py               # 聊天历史
│   ├── device_data.py                # 设备数据 API（CGM）
│   ├── device_trigger.py             # 设备触发路由
│   ├── llm_service.py                # LLM 服务
│   ├── dependencies.py               # FastAPI 依赖注入
│   ├── context_builder.py            # 上下文构建器
│   ├── miniprogram.py                # 小程序接口
│   ├── routes.py                     # 路由注册
│   ├── schemas.py                    # Pydantic Schema
│   ├── services.py                   # 业务服务层
│   ├── session.py                    # 会话管理
│   └── xingjian_api.py               # 行健 Agent API
│
├── agents/                           # ===== Agent 系统 =====
│   ├── __init__.py
│   ├── base.py                       # Agent 抽象基类
│   ├── base_agent.py                 # Agent 基础实现
│   ├── factory.py                    # Agent 工厂
│   ├── registry.py                   # Agent 注册表
│   ├── router.py                     # Agent 路由
│   ├── orchestrator.py               # Agent 编排器
│   ├── collaboration.py              # 多 Agent 协作
│   ├── workflow_engine.py            # 工作流引擎
│   ├── octopus_engine.py             # 章鱼引擎
│   ├── octopus_fsm.py                # 章鱼状态机
│   ├── snapshot_factory.py           # 快照工厂
│   ├── config.yaml                   # Agent 配置
│   ├── 行健xingjian-agent.dsl.yaml   # 行健 Agent DSL
│   └── 行健xingjian-agent_config.yaml # 行健 Agent 配置
│
├── h5/                               # ===== H5 移动端前端 (:5173) =====
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/index.ts
│   │   ├── api/                      # chat / dashboard / index / types
│   │   ├── components/
│   │   │   ├── chat/                 # MessageBubble / EfficacySlider / TaskCard
│   │   │   └── common/TabBar.vue
│   │   ├── stores/                   # chat / user
│   │   ├── styles/                   # global.scss / variables.scss
│   │   ├── utils/storage.ts
│   │   └── views/                    # Home / Chat / Dashboard / Tasks / Profile
│   └── tsconfig.json
│
├── admin-portal/                     # ===== 管理后台前端 (:5174) =====
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router.ts
│   │   ├── api/                      # client/dify/exam/interventions/ollama/...
│   │   ├── components/
│   │   │   ├── AIChatBox.vue
│   │   │   ├── BehaviorStageTag.vue
│   │   │   ├── CoachLevelBadge.vue
│   │   │   ├── RiskLevelTag.vue
│   │   │   ├── TriggerDomainTag.vue
│   │   │   ├── agent/AgentSuggestionCard.vue
│   │   │   └── exam/                 # ProctorCamera / ViolationWarning
│   │   ├── composables/              # useAntiCheat / useExamPersistence / ...
│   │   ├── constants/index.ts
│   │   ├── layouts/AdminLayout.vue
│   │   ├── stores/                   # agent / auth / exam / question
│   │   ├── types/                    # index / exam
│   │   └── views/
│   │       ├── Login.vue / Settings.vue
│   │       ├── admin/                # interventions / prompts
│   │       ├── client/               # ChatView / HomeView
│   │       ├── coach/                # CoachHome / Detail / List / Review / StudentList
│   │       ├── course/               # Chapters / Edit / List
│   │       ├── dashboard/Index.vue
│   │       ├── exam/                 # ExamEdit/List/Session/ProctorReview/QuestionBank/...
│   │       ├── expert/ExpertHome.vue
│   │       └── live/                 # Edit / List
│   └── tsconfig.json
│
├── h5-patient-app/                   # ===== 患者专用 H5 应用 (:5175) =====
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/index.ts
│   │   ├── api/                      # auth / assessment / chat / device / request
│   │   ├── components/               # DataInputForm / RiskCard / TriggerList
│   │   ├── stores/                   # user / assessment / chat / device
│   │   ├── types/index.ts
│   │   ├── utils/storage.ts
│   │   └── views/                    # Home/Login/Register/Chat/DataInput/
│   │                                 # DataAnalysis/History/HealthData/Result/Settings
│   └── tsconfig.json
│
├── knowledge/                        # ===== 知识库 =====
│   ├── triggers/
│   │   ├── trigger-tags-v1.json      # 触发标签定义
│   │   └── README.md
│   ├── kb_theory/                    # 理论知识库
│   ├── kb_case_studies/              # 案例知识库
│   └── kb_products/                  # 产品知识库
│
├── data/                             # ===== 数据目录 =====
│   ├── profiles/                     # 用户档案
│   ├── assessments/                  # 评估数据
│   ├── knowledge/mental_health/      # 心理健康 PDF 文档
│   ├── questionnaire_templates/      # 问卷模板
│   ├── vectordb/                     # 向量数据库索引
│   ├── dify_prompts.json             # Dify 提示词配置
│   └── behavioral_health.db          # SQLite 数据库
│
├── dify-setup/                       # ===== Dify 应用配置 =====
│   ├── behavior-health-agent.yml     # 行为健康教练 Agent DSL
│   ├── proactive-health-coach.yaml   # 主动健康教练 (qwen2.5:14b)
│   ├── proactive-health-coach-deepseek.yaml  # DeepSeek 版本
│   ├── proactive-health-balance.yaml # 吃动守恒 Agent
│   ├── behavior-health-coach.yaml    # 简化版教练
│   ├── http-tools-config.md          # HTTP 工具配置
│   ├── README.md                     # 部署指南
│   └── STATUS_REPORT.md              # 状态报告
│
├── dify/                             # ===== Dify 开源平台 (Docker) =====
│   └── docker/
│       ├── docker-compose.yaml       # 完整 Dify 栈编排
│       └── volumes/                  # 持久化数据
│
├── scripts/                          # ===== 脚本工具 =====
│   ├── create_mock_cases.py          # Mock 测试数据
│   ├── seed_data.py                  # 种子数据导入
│   ├── assessment_importer.py        # 评估导入
│   ├── dashboard_generator.py        # 看板生成
│   ├── prescription_engine.py        # 处方引擎
│   └── report_generator.py           # 报告生成
│
├── tests/                            # ===== 测试 =====
│   ├── integration_test.py
│   ├── test_end_to_end.py
│   └── test_multimodal_integration.py
│
├── docs/                             # ===== 文档 =====
│   ├── PROJECT_OVERVIEW_EXECUTIVE.md # 项目概览
│   ├── PROJECT_ROADMAP.md            # 路线图
│   ├── SYSTEM_ARCHITECTURE_FULL_REFERENCE.md
│   ├── DEPLOYMENT_ARCHITECTURE.md    # 部署架构
│   ├── L2_ASSESSMENT_ENGINE.md       # L2 评估引擎
│   ├── DEVICE_DATA_API_DESIGN.md     # 设备 API 设计
│   ├── DIFY_INTEGRATION.md           # Dify 集成
│   ├── CLAUDE_INTEGRATION.md         # Claude 集成
│   ├── OLLAMA_INTEGRATION_GUIDE.md   # Ollama 集成
│   ├── UI_DESIGN_SPEC.md             # UI 设计规范
│   ├── CERTIFICATION_SYSTEM_SPEC.md  # 认证体系
│   ├── GAP_ANALYSIS_BLUEPRINT.md     # 差距分析
│   ├── LOGIC_DIAGRAM.md              # 逻辑图
│   ├── TABLES_EXPORT.md              # 数据表导出
│   ├── POSTMAN_API_TESTING_GUIDE.md  # Postman 测试
│   └── CORE_DATA_SCHEMA_v1_SPECIFICATION.md
│
├── models/                           # ===== 模型配置 =====
│   ├── Modelfile.behavioral-coach    # Ollama Modelfile
│   └── rx_library.json               # 处方库
│
└── logs/                             # ===== 运行日志 =====
    ├── gateway_8000.log
    ├── baps_8001.log
    ├── decision_8002.log
    ├── h5_5173.log
    ├── admin_5174.log
    └── patient_5175.log
```
