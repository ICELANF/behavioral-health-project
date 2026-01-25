# 行为健康项目纪事 (Project Chronicle)

> 最后更新: 2026-01-24
> 此文件用于记录项目进展和关键信息，防止 AI 助手记忆遗忘

---

## 项目概述

**项目名称**: 行健行为教练 (XingJian Behavioral Coach)
**项目目录**: `D:\behavioral-health-project`
**技术栈**: FastAPI + Ollama (qwen2.5:14b) + Weaviate + Dify + Docker
**状态**: 开发中

---

## 核心架构

### 四大专家系统

| 专家 | 标识符 | 优先级 | 专业领域 |
|------|--------|--------|----------|
| 心理咨询师 | mental_health | 1 | 情绪管理、压力调节、睡眠改善、认知行为技术 |
| 营养师 | nutrition | 2 | 个性化膳食指导、营养素建议、体重管理 |
| 运动康复师 | sports_rehab | 3 | 运动处方、损伤康复、体态矫正 |
| 中医养生师 | tcm_wellness | 4 | 体质调理、四季养生、经络穴位保健 |

### 八爪鱼行为干预引擎 (五层架构 v2.0)

行为处方从"固定文本"进化为**"自适应对象"**：

| 层级 | 功能 | 数据结构 |
|------|------|----------|
| **输入层** | 从 Excel/PDF 抓取生理(SDNN/HRV)与心理(焦虑/SCL-90)数据 | user_state_schema.json |
| **解析层** | 状态建模：改变阶段判定 + 动机强度计算 + 行为模式识别 | user_state_schema.json |
| **策略层** | 匹配 behavior_logic.json 专家规则 | behavior_logic.json |
| **输出层** | 生成处方包(指导意见+知识点+视频+产品ID) | prescription_schema.json |
| **反馈层** | 记录执行后数据波动，效能闭环 | prescription_schema.json |

**核心数据文件位置**: `core/schemas/`

### 效能限幅规则

| 效能评分 | 最大任务数 | 最大难度 |
|----------|------------|----------|
| < 20 | 1 | 1 |
| < 50 | 2 | 2 |
| >= 50 | 3 | 5 |

---

## 自研理论框架

### 五层次心理准备度模型 (替代跨理论模型TTM)

| 层次 | 名称 | 核心心理 | SPI系数 | 成功率 | 干预策略 |
|------|------|----------|---------|--------|----------|
| 1 | 完全对抗 | 改变是威胁 | 0.3 | <30% | 安全感建立 |
| 2 | 抗拒与反思 | 不想改但开始看见必要性 | 0.5 | <30% | 矛盾处理 |
| 3 | 妥协与接受 | 改变必要但想可控进行 | 0.7 | 40-60% | 门槛降低 |
| 4 | 顺应与调整 | 改变合理，愿意适应 | 0.9 | 70-85% | 习惯强化 |
| 5 | 全面臣服 | 这是我是谁的一部分 | 1.0 | >90% | 身份巩固 |

**核心原则**: 根据心理层次匹配干预策略，而非一刀切

### 四阶段养成方案

| 阶段 | 名称 | 时间跨度 | 陪跑频率 | 核心任务 |
|------|------|----------|----------|----------|
| 1 | 启动期 | 第1-2周 | 每日 | 建立打卡习惯、及时解决困难 |
| 2 | 适应期 | 第3-8周 | 每周 | 巩固行为、应对障碍、建立自动化 |
| 3 | 稳定期 | 第2-4月 | 每月 | 减少外部依赖、应对高风险情境 |
| 4 | 内化期 | 4月以上 | 按需 | 身份认同、自主维持、成为榜样 |

### SPI (成功可能性指数) 计算公式

```
SPI = (trigger_score/125) × level_coefficient × (urgency_score/30) × 100
```

| 组成部分 | 说明 | 分值范围 |
|----------|------|----------|
| trigger_score | 改变触发原因得分 (6维度25题) | 0-125 |
| level_coefficient | 心理层次系数 | 0.3-1.0 |
| urgency_score | 改变迫切程度得分 (3维度) | 0-30 |

**SPI 解读**:
- 60-100: 高成功可能性 → 立即启动系统化改变计划
- 40-59: 中等可能性 → 强化部分要素后启动
- 20-39: 较低可能性 → 先进行准备工作
- 0-19: 可能性低 → 时机尚未成熟，持续支持

### 六类改变触发原因

| 原因类型 | 子维度 | 分值 |
|----------|--------|------|
| 内在驱动力 | 价值感、身份愿望、意义认知 | 0-20 |
| 外在事件与压力 | 健康危机、生活事件、环境变化 | 0-20 |
| 情绪体验变化 | 恐惧、愤怒、羞耻、鼓舞 | 0-20 |
| 认知与知识变化 | 洞察、知识、风险意识、未来想象 | 0-20 |
| 能力与资源改善 | 时间、金钱、技能、环境 | 0-20 |
| 社会支持与关系 | 榜样、同伴、家庭、专业、文化 | 0-25 |

---

## 目录结构

```
D:\behavioral-health-project/
├── agents/                 # 多专家协调系统 (1523行)
│   ├── base.py            # ExpertAgent 基类
│   ├── orchestrator.py    # Agent 协调器
│   ├── router.py          # 意图路由器
│   ├── registry.py        # Agent 注册表
│   ├── collaboration.py   # 多专家协作协议
│   ├── factory.py         # Agent 工厂
│   └── octopus_engine.py  # 八爪鱼限幅引擎
│
├── api/                    # FastAPI 后端 (1994行)
│   ├── main.py            # 应用入口
│   ├── routes.py          # REST API 路由
│   ├── schemas.py         # Pydantic 数据模型
│   ├── services.py        # 业务逻辑服务
│   ├── session.py         # 会话管理
│   └── xingjian_api.py    # 行健 API 定义
│
├── core/                   # 核心业务逻辑
│   ├── master_agent.py    # 中枢 Master Agent (9步流程控制器) ★新增
│   ├── pipeline.py        # 五层架构处理流程引擎
│   ├── workflow.py        # 八爪鱼工作流引擎
│   ├── limiter.py         # 效能限幅器
│   ├── data_extractor.py  # 数据提取器 (输入层)
│   ├── model_manager.py   # Ollama 模型管理器
│   └── schemas/           # 数据结构定义
│       ├── behavior_logic.json      # 专家规则库 + 阶段判定 + 动机计算
│       ├── prescription_schema.json # 处方包 Schema
│       └── user_state_schema.json   # 用户状态模型
│
├── models/                 # 模型库 (新增)
│   ├── rx_library.json    # 行为处方库 (6大类, 分阶段干预)
│   └── Modelfile.behavioral-coach  # Ollama 定制模型配置
│
├── scripts/                # 脚本工具
│   ├── prescription_engine.py   # 处方引擎 (隐性疲劳识别 + Agent指导生成)
│   ├── assessment_importer.py   # 评估数据导入器 (新增)
│   └── dashboard_generator.py   # 看板生成器 (新增)
│
├── data/
│   ├── profiles/                 # 用户主画像存储 ★新增
│   ├── assessments/              # 评估数据目录
│   │   ├── raw/                  # 原始数据 (按批次组织)
│   │   ├── processed/            # 标准化 JSON 数据
│   │   │   ├── users/            # 用户评估历史
│   │   │   └── index.json        # 用户索引
│   │   └── exports/              # 导出报告
│   │       ├── individual/       # 个人看板导出
│   │       └── group/            # 群体看板导出
│   ├── knowledge/mental_health/  # 心理健康知识库 (PDF文档)
│   └── vectordb/                 # 向量数据库存储
│
├── knowledge/              # 知识库文档
│   ├── kb_theory/         # 理论知识库
│   ├── kb_case_studies/   # 案例库
│   └── kb_products/       # 产品库
│
├── docs/                   # 项目文档
│   ├── DEPLOYMENT_ARCHITECTURE.md
│   ├── DIFY_INTEGRATION.md
│   └── OLLAMA_INTEGRATION_GUIDE.md  # Ollama 本地模型整合指南 (新增)
│
├── dify/                   # Dify 平台相关
├── MyOctopusProject/       # 健康数据处理项目
├── xingjian-agent/         # 行健Agent 子项目 (镜像副本)
├── volumes/                # Docker 数据卷
│
├── 用户档案/               # Obsidian 用户健康档案 (新增)
├── 行为处方/               # Obsidian 处方卡片 (新增)
├── _templates/             # Obsidian 模板 (新增)
│
├── config.yaml             # 主配置文件
├── docker-compose.yaml     # Docker 编排配置
├── .env                    # 环境变量配置
├── big_five_assessment.py  # 五大人格测评 (399行)
├── big_five_questionnaire.html  # 测评问卷 HTML
└── generate_pdf_report.py  # PDF 报告生成器 (482行)
```

---

## 关键配置

### config.yaml

- **LLM 模型**: `qwen2.5:14b` (Ollama, localhost:11434)
- **嵌入模型**: `nomic-embed-text:latest`
- **温度**: 0.3
- **知识库路径**: `J:/Knowledge-Hub-Obsidian-Vault/02-Knowledge-Base`
- **向量数据库路径**: `J:/xingjian-agent/data/vectordb`

### docker-compose.yaml 服务

| 服务 | 镜像 | 内存限制 | 端口 |
|------|------|----------|------|
| Dify API | langgenius/dify-api:0.15.3 | 8GB | - |
| Dify Worker | langgenius/dify-api:0.15.3 | 12GB | - |
| Dify Web | langgenius/dify-web:0.15.3 | 2GB | - |
| PostgreSQL | postgres:15-alpine | 4GB | - |
| Redis | redis:7-alpine | 3GB | - |
| Weaviate | semitechnologies/weaviate:1.19.0 | 6GB | - |
| Nginx | nginx:latest | 512MB | 8080/8443 |

### 数据库凭据

- PostgreSQL: `difyai123456`
- Redis: `difyai123456`
- Dify 初始密码: `dify123456`

---

## API 端点

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | /api/v1/chat | 多专家对话 |
| POST | /api/v1/behavioral/process | 八爪鱼完整流程 |
| POST | /api/v1/telemetry | 穿戴设备数据上报 |
| POST | /api/v1/clamping | 效能限幅 |
| POST | /api/v1/decompose | 任务分解 |
| GET | /api/v1/experts | 获取可用专家列表 |
| GET | /api/v1/session/{id} | 获取会话信息 |

---

## 已完成功能

- [x] 多专家协调系统框架 (agents/)
- [x] FastAPI 后端 API (api/)
- [x] 八爪鱼行为干预引擎 (core/)
- [x] 效能限幅器
- [x] 意图路由器 (关键词匹配)
- [x] 五大人格测评系统
- [x] PDF 报告生成器
- [x] Docker 基础设施配置
- [x] Dify 集成框架
- [x] 向量数据库初始化
- [x] 心理健康知识库 (睡眠相关)
- [x] 五层架构数据结构设计 (core/schemas/)
- [x] **自研理论体系整合**:
  - [x] 五层次心理准备度模型 (替代跨理论模型TTM)
  - [x] 四阶段养成方案 (启动/适应/稳定/内化)
  - [x] SPI成功可能性指数计算公式
  - [x] 六类改变触发原因评估框架
  - [x] 干预策略与心理层次对应映射
- [x] **五层架构处理流程** (core/pipeline.py):
  - [x] 输入层: 集成 data_extractor 数据抓取
  - [x] 解析层: 阶段判定 (历史数据频率) + 动机计算 (精力-心情匹配度)
  - [x] 策略层: 匹配 behavior_logic.json 专家规则
  - [x] 输出层: 生成完整处方包 JSON (指导/知识/视频/产品)
  - [x] 反馈层: 效能闭环数据记录
- [x] **行为处方库** (models/rx_library.json):
  - [x] 6大类处方: 睡眠调节、压力管理、运动养成、营养管理、情绪调节、中医养生
  - [x] 分阶段话术: 意向期、准备期、行动期三阶段差异化干预
  - [x] 完整内容结构: 建设性意见、核心知识点、教学视频路径、商城产品ID
  - [x] 已集成到 pipeline.py 五层架构流程
- [x] **处方引擎** (scripts/prescription_engine.py):
  - [x] BehavioralProfile 类: 行为画像分析 (行为倾向、模式、动机强度、改变阶段)
  - [x] 行为模式识别: 7种模式 (机体耗竭、隐性疲劳、过度补偿、应激逃避、躯体化、情绪失调、平衡)
  - [x] **隐性疲劳模式**: HRV恢复能力低但主观压力低 → 早期预警
  - [x] 处方组件集成: 知识科普 + 示范视频 (./assets/videos/) + 产品推荐 (海棠心智穿戴设备)
  - [x] Agent 指导意见生成: 基于动机强度和改变阶段的 Coach 话术
  - [x] 干预策略: 6种策略 (强制修复、隐性疲劳修复、微习惯、渐进提升、习惯强化、身份巩固)
  - [x] **Word 文档导出**: 专业报告生成 (8个章节: 画像分析、处方概述、任务、Coach话术、知识、视频、产品、注意事项)
- [x] **Ollama 本地模型整合**:
  - [x] 模型管理器 (core/model_manager.py): 多模型池、智能路由、降级策略、健康检查
  - [x] 定制 Modelfile (models/Modelfile.behavioral-coach): 行为健康教练专用模型配置
  - [x] 整合指南 (docs/OLLAMA_INTEGRATION_GUIDE.md): 模型分层策略、性能优化
- [x] **评估数据管理系统** (新增):
  - [x] 数据目录结构 (data/assessments/): raw → processed → exports 三级组织
  - [x] 评估数据导入器 (scripts/assessment_importer.py):
    - [x] Excel 解析 (openpyxl): 生理测评数据、心理测评数据
    - [x] PDF 解析 (pdfplumber/PyPDF2): 心理健康测评报告
    - [x] 数据标准化: 统一 JSON 格式输出
    - [x] 风险评估: 基于综合得分、HRV、心理指标自动分级
    - [x] 用户索引管理: index.json 自动维护
    - [x] 批量导入: 支持整个批次目录导入
  - [x] 看板生成器 (scripts/dashboard_generator.py):
    - [x] 个人看板 (IndividualDashboard): 历史评估、趋势分析、综合评语、健康建议
    - [x] 群体看板 (GroupDashboard): 风险分布、得分分布、群体均值、高风险名单
    - [x] 趋势分析: 指标变化百分比、趋势方向判断、解读文案生成
    - [x] Word 导出: 专业报告格式 (python-docx)
    - [x] JSON 导出: 结构化数据输出
  - [x] 数据格式规范 (data/assessments/README.md): 完整目录结构和 JSON Schema 文档
- [x] **Dify 行健教练工作流** (新增):
  - [x] 行健教练-核心闭环 (TTM双节点工作流)
  - [x] TTM评估官节点 (5阶段判定 + JSON输出)
  - [x] 麦肯基治疗师节点 (阶段适配康复方案)
  - [x] Ollama qwen2.5:14b 模型集成
  - [x] 对话记忆 (10轮历史窗口)
- [x] **Obsidian 知识库集成** (新增):
  - [x] ingest_obsidian.py 重构: 全面支持评估数据与 Obsidian 联动
  - [x] 用户档案自动生成: 以用户 ID 命名的 Markdown 文件
    - [x] YAML Front Matter: 标签、别名、元数据
    - [x] Dataview 查询支持
    - [x] 历史评估表格
    - [x] 风险等级 Callout 显示
    - [x] 自动引用 knowledge/ 干预建议
  - [x] 处方卡片生成: Obsidian Callout 格式预览
    - [x] 任务卡片 (todo callout)
    - [x] 知识科普链接
    - [x] 示范视频引用
    - [x] Coach 话术展示
  - [x] 干预知识库文件 (knowledge/kb_theory/):
    - [x] 压力管理.md
    - [x] 疲劳恢复.md
    - [x] 情绪调节.md
    - [x] HRV优化.md
    - [x] 隐性疲劳.md
    - [x] 健康维护.md
  - [x] Obsidian 模板 (_templates/)
  - [x] 向量化知识库: LlamaIndex + Ollama Embedding

---

## 待开发功能

- [ ] 前端应用
  - [ ] H5 网页端 (Vue3/React)
  - [ ] 微信小程序 (Taro/uni-app)
- [ ] Obsidian 知识库完整同步
- [ ] 穿戴设备完整数据接口
- [x] Dify 工作流配置 (行健教练-核心闭环已完成)
- [ ] 生产环境部署
- [ ] 用户认证系统
- [ ] 更多知识库文档导入

---

## 开发里程碑

### 2026-01-19
- 完成项目纪事文件创建
- 项目整体架构已搭建完成
- 核心后端代码已实现
- **品牌命名变更**: "行健健康顾问团" 统一更名为 "行健行为教练"
  - 更新所有配置文件、API 服务、提示词模板
  - 涉及文件: config.yaml, api/*.py, agents/*.py 等
- **五层架构数据结构设计完成**:
  - `behavior_logic.json` - 专家规则库 (行为模式、改变阶段、动机计算、匹配规则)
  - `prescription_schema.json` - 处方包完整 Schema (评估摘要、处方内容、限幅信息、反馈追踪)
  - `user_state_schema.json` - 用户状态模型 (生理/心理/行为/计算指标)
- **自研理论完整整合** (重要里程碑):
  - 读取自研Word文档: 《行为诊断处方养成体系》《四层体系-问题识别》《总览使用手册》
  - 替换跨理论模型(TTM)为自研**五层次心理准备度模型**
    - 完全对抗 → 抗拒与反思 → 妥协与接受 → 顺应与调整 → 全面臣服
    - 每层对应SPI系数: 0.3, 0.5, 0.7, 0.9, 1.0
  - 整合**四阶段养成方案**: 启动期 → 适应期 → 稳定期 → 内化期
  - 实现**SPI计算公式**: `SPI = (trigger_score/125) × level_coefficient × (urgency_score/30) × 100`
  - 更新干预策略与五层次一一对应: 安全感建立、矛盾处理、门槛降低、习惯强化、身份巩固
  - 理论来源文件: `D:\行为健康平台建设构想\行为健康项目规划文件\行为健康促进体系理论-评估-方案`

### 2026-01-23
- **H5 前端项目完整实现** (重要里程碑):
  - 技术栈: Vue 3 + Vite 5 + Vant 4 + Pinia + ECharts + TypeScript
  - 项目结构: 完整的 src/ 目录架构
  - **页面开发**:
    - Home.vue - 首页 (欢迎卡片、快捷入口、专家列表、任务预览)
    - Chat.vue - 对话页 (消息列表、任务卡片、效能感滑块、穿戴数据弹窗)
    - Tasks.vue - 任务列表 (进度统计、任务筛选、完成状态)
    - Dashboard.vue - 健康看板 (评分卡片、ECharts趋势图、风险评估)
    - Profile.vue - 个人中心 (用户信息、穿戴数据、功能菜单)
  - **核心组件**:
    - MessageBubble.vue - 消息气泡组件
    - TaskCard.vue - 任务卡片组件 (难度星级、类型标签)
    - EfficacySlider.vue - 效能感滑块 (0-100, 三色等级)
    - TabBar.vue - 底部导航栏
  - **状态管理** (Pinia stores):
    - user.ts - 用户状态 (效能感、穿戴数据)
    - chat.ts - 对话状态 (消息、任务、专家)
  - **API层**:
    - 对接 `/api/v1/dispatch` 网关接口
    - 支持 Ollama 直连模式
  - **运行状态**: 开发服务器 http://localhost:5173 已启动
- **API 网关重构** (api/main.py):
  - 简化为 Dify + Ollama 双模式网关
  - AgentGateway 类封装模型调用
  - 新增接口:
    - `GET /api/v1/experts` - 专家列表
    - `GET /api/v1/dashboard/{user_id}` - 个人看板数据
    - `POST /api/v1/decompose` - 任务分解 (效能感限幅)
- **本地存储持久化** (h5/src/utils/storage.ts):
  - 用户信息、效能感、穿戴数据持久化
  - 对话消息持久化 (最近100条)
  - 任务列表持久化
- **前后端联调验证**:
  - Ollama qwen2.5:14b 模型响应正常
  - API dispatch 接口测试通过
  - Dashboard API 数据对接完成
- **Dify 服务状态**:
  - 核心服务正常运行 (http://localhost:80)
  - sandbox 组件配置问题 (非核心功能)

### 2026-01-23 (续)
- **中枢 Master Agent 架构实现** (重要里程碑):
  - 新增 `core/master_agent.py` - 多Agent系统核心控制器 (~750行)
  - **9步处理流程完整实现**:
    1. 用户输入/设备数据接收
    2. Master Agent 请求处理
    3. User Master Profile 更新
    4. Agent Router 风险优先级评估
    5. 专业Agent调用 (1-2个)
    6. Multi-Agent Coordinator 上下文统一
    7. Intervention Planner 干预路径生成
    8. Response Synthesizer 教练风格统一
    9. Profile 写回 + 今日任务生成
  - **核心类实现**:
    - `MasterAgent` - 中枢控制器，串联9步流程
    - `UserMasterProfile` - 用户主画像管理 (CRUD + 缓存 + 持久化)
    - `RiskPriorityAssessor` - 风险优先级评估器
  - **数据结构定义**:
    - `UserInput` - 统一用户输入 (对话/设备/评估/任务)
    - `RoutingDecision` - 路由决策 (风险等级 + 专家选择)
    - `InterventionPlan` - 干预计划 (任务/知识/视频/产品)
    - `SynthesizedResponse` - 合成响应 (教练风格统一)
    - `DailyTask` - 今日任务 (追踪点 + 完成标准)
  - **风险评估机制**:
    - 4级风险: CRITICAL/HIGH/MODERATE/LOW
    - 紧急关键词检测 (自杀/自残等)
    - 生理指标阈值 (HRV/睡眠/心率)
    - 心理指标阈值 (焦虑/抑郁/压力)
    - 效能感评估
  - **教练风格系统**:
    - empathetic (共情) - 危急情况
    - supportive (支持) - 高风险
    - motivational (激励) - 意向期
    - educational (教育) - 行动期
  - **便捷接口**:
    - `chat()` - 简化对话
    - `sync_device_data()` - 设备同步
    - `submit_assessment()` - 评估提交
    - `report_task_completion()` - 任务完成上报
  - 新增 `data/profiles/` - 用户画像存储目录

### 2026-01-23 (续2)
- **User Profile Schema v2.0 迁移完成**:
  - 新增 `core/schemas/user_profile_schema.json` - 统一用户主画像 Schema
  - 新增 `core/schemas/master_io_schema.json` - Master Agent 输入输出规范
  - **Profile 结构简化**:
    - `basic` - 基本信息 (年龄、性别、身高、体重)
    - `medical` - 医疗健康 (糖尿病、血压、用药)
    - `behavior` - 行为状态 (五层次阶段、SPI系数、行为模式、依从性)
    - `psych` - 心理状态 (压力、动机、焦虑、抑郁、效能感)
    - `constitution` - 体质指标 (BMI、内脏脂肪、中医体质)
    - `biometrics` - 生物指标 (血糖、HRV、睡眠、活动)
    - `preferences` - 用户偏好 (关注领域、教练风格、通知时间)
    - `risk_flags` - 风险标记数组 (根级别)
    - `history` - 历史记录摘要
    - `today` - 今日状态快照
  - **设备数据支持 (DeviceData)**:
    - CGMData - 连续血糖监测 (TIR、GMI、CV%)
    - HRVData - 心率变异性 (SDNN、RMSSD、压力指数)
    - SleepData - 睡眠数据 (深睡比例、觉醒次数、效率)
  - **代码迁移**:
    - `_determine_coach_style()` - 支持用户偏好 + 五层次行为阶段
    - `_summarize_profile()` - 适配 v2.0 字段路径
    - `_add_secondary_agents()` - 使用根级 `risk_flags`
    - `_finalize_and_save_profile()` - 更新 `today.tasks`、`history`、`risk_flags`
    - 移除所有 `computed_indicators`、`physiological_state`、`psychological_state` 旧路径引用

### 2026-01-23 (续3)
- **Agent Task 调度系统实现**:
  - 新增 `core/schemas/agent_task_schema.json` - Agent 任务通信规范
  - **AgentTask 数据结构**:
    - `AgentType` 枚举: Sleep/Glucose/Stress/Nutrition/Exercise/MentalHealth/TCMWellness/Crisis
    - `TaskStatus` 枚举: pending/processing/completed/failed/timeout
    - `AgentTask` - 任务请求 (task_id, agent_type, question, priority, context, constraints)
    - `AgentTaskResponse` - 任务响应 (analysis, recommendations, response_text, follow_up)
  - **分析结构**:
    - `AgentTaskFinding` - 发现项 (category, observation, severity, confidence)
    - `AgentTaskCorrelation` - 相关性 (factor_a, factor_b, relationship, strength)
    - `AgentTaskRecommendation` - 干预建议 (type, action, rationale, priority, difficulty)
  - **核心方法**:
    - `create_agent_task()` - 创建任务 (自动提取 Profile 摘要)
    - `execute_agent_task()` - 执行任务 (支持 orchestrator + 降级方案)
    - `_generate_task_analysis()` - 根据 Agent 类型生成分析
    - `process_agent_task_json()` - JSON API 入口
  - **规则引擎分析**:
    - SleepAgent: 睡眠时长/质量/深度睡眠分析，睡眠-血糖关联
    - GlucoseAgent: 血糖值/TIR/趋势分析
    - StressAgent: HRV/压力指数分析

### 2026-01-23 (续4)
- **Action Plan 行动计划系统实现**:
  - 新增 `core/schemas/action_plan_schema.json` - 行动计划规范
  - **ActionPlan 数据结构**:
    - `ActionType` 枚举: behavior/monitor/education/exercise/nutrition/relaxation/social/medical
    - `PlanAction` - 行动项 (type, content, timing, frequency, priority, resources)
    - `PlanEvaluation` - 评估标准 (metrics, targets, checkpoints)
    - `ActionPlan` - 完整计划 (goal, phase, actions, evaluation, status)
  - **核心方法**:
    - `create_action_plan()` - 基于分析结果创建计划 (自动推断行动类型)
    - `generate_phased_plan()` - 生成多阶段计划 (支持四阶段养成)
    - `_infer_action_type()` - 智能推断行动类型
    - `_get_max_actions_for_stage()` - 根据行为阶段限制行动数
    - `_adjust_plan_for_phase()` - 根据养成阶段调整难度
    - `update_action_plan_progress()` - 更新完成进度
    - `parse_action_plan_json()` - JSON 解析
  - **ActionPlan 便捷方法**:
    - `get_actions_by_type()` - 按类型筛选
    - `get_pending_actions()` - 获取待完成项
    - `progress_percent()` - 计算完成百分比
    - `to_daily_tasks()` - 转换为 DailyTask 列表
  - **四阶段养成整合**:
    - startup (启动期): 降低难度，增加教育
    - adaptation (适应期): 逐步增加挑战
    - stability (稳定期): 减少提醒，增加自主性
    - internalization (内化期): 最小干预

### 2026-01-23 (续5)
- **Daily Briefing 每日简报系统实现**:
  - **DailyBriefing 数据结构**:
    - 基础字段: user_id, date, tasks, coach_message
    - 扩展字段: greeting, focus_area, encouragement, streak_days, alerts, reminders
    - 自动生成问候语 (根据时间段)
  - **核心方法**:
    - `from_dict()` / `to_dict()` - JSON 序列化
    - `to_full_dict()` - 完整版输出
    - `format_message()` - 格式化推送文本
    - `from_action_plan()` - 从 ActionPlan 生成简报
  - **教练消息生成**:
    - `_generate_coach_message()` - 根据行为阶段 × 教练风格生成
    - `_generate_encouragement()` - 根据连续天数生成鼓励语
  - **MasterAgent 方法**:
    - `generate_daily_briefing()` - 生成每日简报
    - `_generate_default_daily_tasks()` - 基于 focus 领域生成默认任务
    - `_generate_daily_coach_message()` - 生成每日教练消息
    - `get_daily_push_content()` - 获取推送 JSON
    - `get_daily_push_message()` - 获取格式化推送文本
  - **消息模板矩阵**: 5个行为阶段 × 4种教练风格 = 20种消息模板

### 2026-01-23 (续6)
- **Pipeline Orchestrator 流程编排器实现** (重要架构):
  - 新增 `core/schemas/system_architecture.json` - 系统架构定义
  - **PipelineStep 枚举** - 8个流程步骤:
    1. `INPUT_HANDLER` - 输入处理
    2. `PROFILE_MANAGER` - 画像管理
    3. `RISK_ANALYZER` - 风险分析
    4. `AGENT_ROUTER` - Agent路由
    5. `MULTI_AGENT_COORDINATOR` - 多Agent协调
    6. `INTERVENTION_PLANNER` - 干预规划
    7. `RESPONSE_SYNTHESIZER` - 响应合成
    8. `TASK_GENERATOR` - 任务生成
  - **PipelineContext 数据类**:
    - 在步骤间传递数据
    - 追踪完成步骤
    - 记录错误
    - 计算执行时间
  - **PipelineOrchestrator 类**:
    - `execute()` - 执行完整8步流程
    - `_step_*()` - 各步骤独立实现
    - `_build_final_response()` - 构建最终响应
    - `_build_error_response()` - 错误处理
  - **MasterAgent 新方法**:
    - `process_with_pipeline()` - 带完整追踪的处理
    - `get_pipeline_orchestrator()` - 获取编排器实例
  - **执行摘要**:
    - completed_steps, current_step
    - errors_count, duration_ms
    - has_intervention, tasks_generated

### 2026-01-23 (续7)
- **Orchestrator REST API 实现**:
  - 更新 `api/main.py` - 添加完整 Orchestrator 接口
  - **Pydantic 模型**:
    - `OrchestratorRequest` - 核心请求模型
    - `OrchestratorResponse` - 核心响应模型
    - `DeviceDataInput` - 设备数据输入
    - `AgentTaskRequest` - Agent 任务请求
    - `ActionPlanRequest` - 行动计划请求
  - **核心接口**:
    - `POST /orchestrator/process` - 完整9步流程处理
    - `POST /orchestrator/briefing` - 获取每日简报
    - `GET /orchestrator/briefing/{user_id}/message` - 推送消息文本
    - `POST /orchestrator/agent-task` - 执行单个Agent任务
    - `POST /orchestrator/action-plan` - 创建行动计划
    - `GET /orchestrator/action-plan/{user_id}/phased` - 多阶段计划
    - `GET /orchestrator/profile/{user_id}` - 获取用户画像
    - `POST /orchestrator/device-sync` - 同步设备数据
    - `GET /orchestrator/status` - 系统状态
  - **懒加载机制**: `get_master_agent()` 避免启动时依赖

### 2026-01-23 (续8)
- **AgentRouter 智能路由器实现**:
  - **AgentRouteResult 数据类**:
    - agents: 路由结果列表 `[{"agent": "GlucoseAgent", "priority": 1}, ...]`
    - primary_agent, secondary_agents
    - reasoning: 路由决策原因
    - confidence: 置信度 0-1
  - **AgentRouter 类**:
    - 8种 Agent 定义 (Crisis/Sleep/Glucose/Stress/Nutrition/Exercise/MentalHealth/TCM)
    - 领域关联矩阵 (DOMAIN_CORRELATIONS)
    - **路由优先级规则**:
      1. 危机状态 → CrisisAgent (强制)
      2. 风险等级 → 对应 Agent
      3. 意图关键词匹配
      4. 用户偏好 (focus areas)
      5. 设备数据类型
      6. 协同领域 Agent
      7. 默认 MentalHealthAgent
    - **核心方法**:
      - `route()` - 执行路由
      - `_is_crisis()` - 危机检测
      - `_match_by_intent()` - 意图匹配
      - `_match_by_data()` - 设备数据匹配
      - `_match_by_focus()` - 偏好匹配
      - `_calculate_confidence()` - 置信度计算
  - **MasterAgent 方法**:
    - `route_agents()` - 简化版路由
    - `route_agents_detailed()` - 详细版路由
  - **API 接口**:
    - `POST /orchestrator/route` - 简化路由
    - `POST /orchestrator/route/detailed` - 详细路由

### 2026-01-23 (续9)
- **Core Data Schema v1.0 实现** (系统级数据契约):
  - 导入并执行 `D:\主动行为健康中枢.txt` 规范文档
  - 新增 `core/schemas/core_data_schema.json` - 系统最高级别数据协议规范
  - **系统级约束原则**:
    - 唯一权威原则: UserMasterProfile 是系统唯一权威用户主画像源
    - 通信协议: Orchestrator→Agent 只能用 AgentTask, Agent→Orchestrator 只能用 AgentResult
    - 写回渠道: AgentResult.data_updates / InterventionPlan.adjustment / DailyTask.feedback
    - 写回权威: 仅 Master Orchestrator 可统一写回
  - **六个核心结构体实现** (`core/master_agent.py`):
    1. `CoreUserInput` - 统一输入对象 (chat/wearable_data/medical_record/questionnaire/manual_log)
    2. `CoreUserMasterProfile` - 用户主画像 (全系统唯一权威用户状态对象)
    3. `CoreAgentTask` - 中枢→AGENT标准指令对象
    4. `CoreAgentResult` - AGENT→中枢回传对象
    5. `CoreInterventionPlan` - 干预路径对象 (行为处方)
    6. `CoreDailyTask` - 每日任务与陪伴执行对象
  - **Core 枚举类型**:
    - `CoreInputType` - 输入类型 (chat/wearable_data/medical_record/questionnaire/manual_log)
    - `CoreSource` - 输入来源 (app/device/clinician/system)
    - `CoreAgentType` - Agent类型 (metabolic/sleep/emotion/motivation/coaching/nutrition/exercise/tcm/crisis)
    - `CoreTaskType` - 任务类型 (analysis/assessment_request/planning_support/interpretation)
    - `CoreDailyTaskType` - 每日任务类型 (micro_habit/reflection/training/measurement)
    - `CoreStrategyType` - 干预策略类型 (cognitive/behavioral/emotional_support/combined)
    - `CoreModuleType` - 干预模块类型 (nutrition/exercise/sleep/emotion/cognitive)
    - `CoreBehaviorStage` - 行为改变阶段TTM (precontemplation→contemplation→preparation→action→maintenance)
    - `CoreResistanceLevel` - 五层次心理准备度 (resistance→ambivalence→compromise→adaptation→integration)
    - `CoreCultivationStage` - 四阶段养成 (startup→adaptation→stability→internalization)
  - **数据流验证器** (`CoreDataFlowValidator`):
    - `PIPELINE_STEPS` - 9步主执行链路定义
    - `ALLOWED_WRITE_CHANNELS` - 合法写回渠道
    - `validate_agent_communication()` - 验证Agent通信协议
    - `validate_profile_write()` - 验证画像写入权限
    - `get_current_step()` - 获取当前步骤
  - **版本控制**: 所有核心对象包含 `schema_version: "1.0"` 和 `extensions` 字段
  - **向后兼容**: 保留原有数据结构，Core* 前缀类为规范实现

### 2026-01-23 (续10)
- **Assessment Engine 问卷评估系统实现** (核心能力模块):
  - 导入并执行 `D:\问卷系统与主动行为健康中枢整合设计（V1）.txt`
  - 新增 `core/schemas/assessment_schema.json` - 问卷评估系统 Schema
  - **系统定位**: Core Assessment Engine - Master Orchestrator 的一级核心子系统
    - 用户画像生成引擎
    - 行为模式识别引擎
    - 干预路径触发器
  - **三层嵌入架构**:
    - 前置层: 画像初始化 / 阶段识别 (首次建档问卷)
    - 中置层: 各AGENT调用过程中的专项评估
    - 后置层: 干预路径效果评估 / 动态追踪
  - **四个新数据结构** (`core/master_agent.py`):
    1. `QuestionnaireTemplate` - 问卷模板定义 (题块/评分规则/解读规则)
    2. `QuestionnaireInstance` - 问卷实例 (答案/状态/时间)
    3. `AssessmentResult` - 评估结果 (核心得分/行为标签/风险等级)
    4. `QuestionnaireTriggerRule` - 问卷触发规则 (事件/条件/优先级)
  - **支撑数据类**:
    - `Question` - 问卷题目 (类型/选项/权重/映射)
    - `QuestionBlock` - 问卷题块
    - `QuestionOption` - 问题选项
    - `QuestionAnswer` - 问题答案
    - `ScoringRule` - 评分规则
    - `InterpretationRule` / `InterpretationRange` - 解读规则
  - **枚举类型**:
    - `QuestionnaireDomain` - 13种问卷领域
    - `QuestionType` - 7种题目类型
    - `TriggerEvent` - 12种触发事件
    - `QuestionnaireStatus` - 4种问卷状态
  - **AssessmentEngine 类** (四大子引擎):
    - **Questionnaire Generator**: `generate_questionnaire()`, `generate_adaptive_questionnaire()`
    - **Scoring Engine**: `score_questionnaire()`, `_calculate_question_score()`, `_normalize_score()`
    - **Interpretation Engine**: `interpret_results()`, `_identify_behavior_patterns()`, `_identify_barriers()`
    - **Profile Writer**: `write_to_profile()` (通过 Orchestrator 统一写回)
  - **完整评估流程**: `assess()` - 评分→核心得分计算→解读→标签识别→障碍识别→风险判定
  - **与AGENT系统集成**:
    - `handle_agent_assessment_request()` - 处理 task_type="assessment_request"
    - `to_agent_result()` - AssessmentResult 转 CoreAgentResult
  - **触发规则系统**:
    - `register_trigger_rule()` - 注册触发规则
    - `check_triggers()` - 检查触发条件
    - `check_conditions()` - 条件匹配 (支持 eq/ne/gt/lt/gte/lte/in/contains)
  - **示例问卷模板**:
    - `data/questionnaire_templates/behavior_change_assessment.json`
    - 4个题块: 改变触发原因/准备度评估/自我效能评估/障碍识别
    - 5个评分维度: motivation/readiness/self_efficacy/barrier_count/social_support
    - 3套解读规则矩阵

### 2026-01-23 (续11)
- **Dify 工作流创建器实现** (集成模块):
  - 导入并执行 `D:\import requests.txt`
  - 新增 `integrations/dify_workflow_creator.py` - Dify API 工作流创建器
  - **工作流节点类**:
    - `WorkflowNodeType` - 节点类型枚举 (start/end/llm/code/condition/http_request)
    - `WorkflowNode` - 工作流节点数据类
    - `WorkflowEdge` - 工作流边（连接）数据类
  - **DifyWorkflowCreator 类**:
    - `create_app()` - 创建 Dify 应用
    - `get_workflow_draft()` - 获取工作流草稿
    - `update_workflow()` - 更新工作流
    - `publish_workflow()` - 发布工作流
    - `build_workflow_graph()` - 构建工作流图
  - **预置 Prompt 模板**:
    - `PROMPT_TTM_ASSESSOR` - TTM/五层次心理准备度评估 (输出 JSON 含 spi_coefficient)
    - `PROMPT_INTERVENTION_PRESCRIBER` - 干预处方生成 (基于四阶段养成策略)
    - `PROMPT_SLEEP_AGENT` - 睡眠专家 Agent
    - `PROMPT_GLUCOSE_AGENT` - 血糖/代谢专家 Agent
  - **预置工作流模板**:
    - `create_ttm_assessment_workflow()` - 两节点: Assessor → Prescriber
    - `create_multi_agent_workflow()` - 四节点: Assessor → Sleep/Glucose Agents → Synthesizer
  - **导出功能**:
    - `get_workflow_definitions()` - 导出工作流定义
    - `export_prompts_to_json()` - 导出 Prompts 到 JSON
  - **模型配置**: 支持 tongyi/openai/ollama，默认 qwen2.5:14b
  - **已导出**: `data/dify_prompts.json`

### 2026-01-23 (续12)
- **数据格式兼容层实现** (DataFormatConverter):
  - 新增 `DataFormatConverter` 类 - 支持旧格式到 v2.0 的自动转换
  - **旧格式字段映射**:
    - `physiological_state` → `biometrics` (hrv/sleep/glucose/activity)
    - `psychological_state` → `psych` (stress/anxiety/depression/efficacy)
    - `behavior_state` → `behavior` (stage/spi_coefficient)
    - `computed_indicators` → `constitution` + `behavior`
    - `message/query/text/input` → `content`
  - **行为阶段映射** (TTM → 五层次):
    - precontemplation → resistance (完全对抗)
    - contemplation → ambivalence (抗拒与反思)
    - preparation → compromise (妥协与接受)
    - action → adaptation (顺应与调整)
    - maintenance → integration (全面臣服)
  - **风险等级映射**: critical/high/medium→moderate/low
  - **核心方法**:
    - `convert()` - 自动检测并转换任意数据
    - `convert_user_input()` - 转换用户输入
    - `convert_profile_data()` - 转换用户画像
    - `convert_device_data()` - 转换设备数据
    - `convert_stage()` - 转换行为阶段
    - `convert_risk_level()` - 转换风险等级
  - **已集成**: `UserInput.from_dict()` 自动使用兼容层
  - **向后兼容**: Dify 发送的旧格式数据将自动转换为 v2.0 格式

### 2026-01-24
- **Core Data Schema v1.0 最终工程规范版** (重要里程碑):
  - 新增 `core/schemas/core_data_schema_v1_final.json` - 完整六大核心结构体定义
  - 新增 `docs/CORE_DATA_SCHEMA_v1_SPECIFICATION.md` - 可读性 Markdown 规范文档
  - **补齐五个核心结构体工程级定义**:
    1. **BehaviorState** (行为状态模型):
       - 行为改变阶段 (TTM 5阶段)
       - 五层次心理准备度 (自研模型: 完全对抗→全面臣服)
       - 四阶段养成进度 (启动→适应→稳定→内化)
       - SPI 成功可能性指数计算
       - 行为模式识别 + 障碍识别 + 风险标记
       - 动机状态评估 (精力-心情匹配度)
    2. **Goal** (目标模型):
       - SMART 格式目标定义
       - 里程碑管理
       - 进度追踪与状态管理
    3. **Task** (任务模型):
       - 最小执行单元定义
       - 难度校准 (1-5级)
       - 调度配置 + 成功标准
       - 教练指导话术
    4. **AgentProfile** (Agent身份模型):
       - 9种 Agent 类型定义
       - 能力边界 + 权限配置
       - 协作规则 + 触发条件
       - 模型配置 + 调用限流
    5. **SkillDescriptor** (技能描述模型):
       - 可插拔技能单元
       - 输入/输出 Schema 定义
       - 调用条件 + 执行配置
       - 质量指标追踪
    6. **Session** (会话模型):
       - 交互会话完整上下文
       - 对话记录 + Agent 调用记录
       - 决策追踪 + Profile 更新记录
    7. **Trajectory** (轨迹模型):
       - 长期陪伴轨迹追踪
       - 阶段转换历史 + 指标趋势
       - 科研导出配置 (匿名化支持)
  - **元信息定义**:
    - 每个结构体包含: 职责说明、生命周期、读写权限、UserState关系、技能映射
  - **数据流规范**:
    - 9步主执行链路完整定义
    - 写回渠道与权限校验
    - 禁止操作清单
  - **跨结构体关系图**: 完整对象依赖关系定义
- **Dify 行健教练工作流开发** (应用集成):
  - 创建 `行健教练-核心闭环` Dify advanced-chat 应用
  - **双节点 TTM 工作流**:
    - TTM评估官节点: 基于跨理论模型判定用户行为改变阶段
      - 5阶段: Precontemplation → Contemplation → Preparation → Action → Maintenance
      - 输出 JSON: stage/stage_cn/reasoning/confidence
    - 麦肯基治疗师节点: 根据TTM阶段生成个性化颈椎康复方案
      - 阶段适配策略: 唤起意识→消除顾虑→行动计划→巩固习惯→进阶提升
      - 输出格式: 评估摘要 + 麦肯基康复方案 (推荐动作/阶段性建议/温馨提示)
  - **模型配置**: Ollama qwen2.5:14b (本地部署)
  - **工作流文件** (桌面):
    - `行健教练-核心闭环-完整版.yml` - 完整版双节点工作流
    - `行健教练-核心闭环-v2.yml` - 优化版本
    - `行健教练-核心闭环-修正版.yml` - 修正版本
    - `行健教练-简单测试.yml` - 单节点简化测试版
  - **开场白配置**: 引导用户描述颈椎症状
  - **建议问题**: 预设4类典型用户输入场景
  - **对话记忆**: 开启10轮历史窗口
- **Dify 部署文档**: 新增 `dify部署.docx` 部署指南

### 2026-01-24 (续)
- **BAPS行为评估系统完整实现** (重要里程碑):
  - 新增 `core/baps/` - 行为评估系统与处方模块
  - **四大核心问卷完整实现**:
    1. **大五人格测评 (BigFiveQuestionnaire)** - 50题
       - 五维度: 外向性(E)/神经质(N)/尽责性(C)/宜人性(A)/开放性(O)
       - 双极量表: -4 到 +4
       - 反向计分支持
    2. **BPT-6行为模式分型** - 18题
       - 六类型: 行动型/知识型/情绪型/关系型/环境型/矛盾型
       - 分型规则: 纯类型(>=12分)/混合型(>=10分)/分散型(7-9分)
       - 类型特征配置: 核心特质/人格基础/干预重点/推荐策略/避免策略
    3. **CAPACITY改变潜力诊断** - 32题
       - 八维度: 觉察力(C1)/自主感(A1)/匹配度(P)/资源(A2)/承诺(C2)/身份(I)/时间(T)/期待(Y)
       - 潜力分级: 高潜力(128-160)/中高潜力(96-127)/中等潜力(64-95)/需要准备(<64)
    4. **SPI成功可能性评估** - 50题
       - 五维度加权: 动机(M)×0.30 + 能力(A)×0.25 + 支持(S)×0.20 + 环境(E)×0.15 + 历史(H)×0.10
       - 成功预测: 很高(>75%)/较高(50-75%)/中等(30-50%)/较低(15-30%)/很低(<15%)
  - **评分引擎 (BAPSScoringEngine)**:
    - 大五人格计分: 含反向计分、人格画像生成、建议生成
    - BPT-6分型: 类型判定、干预策略匹配
    - CAPACITY诊断: 八维度评分、潜力分级
    - SPI计算: 加权公式、成功率预测
    - 综合评估: 交叉分析、行动计划生成
  - **报告生成器 (BAPSReportGenerator)**:
    - JSON格式报告: 含可视化数据(雷达图/柱状图配置)
    - Markdown格式报告: 完整排版、可直接导出
    - 执行摘要生成: 核心发现汇总
    - 四阶段行动计划: 启动期/适应期/稳定期/内化期
  - **REST API服务 (baps_api.py)**:
    - `GET /questionnaires` - 获取问卷列表
    - `GET /questionnaires/{type}` - 获取问卷详情与题目
    - `POST /assess/big_five` - 大五人格评估
    - `POST /assess/bpt6` - 行为模式分型
    - `POST /assess/capacity` - 改变潜力诊断
    - `POST /assess/spi` - 成功可能性评估
    - `POST /assess/comprehensive` - 综合评估
    - `GET /openapi-tools.json` - Dify集成Schema
  - **Dify工作流配置**:
    - `dify_workflows/baps_assessment_workflow.yml` - BAPS评估工作流
  - **集成测试通过**:
    - API健康检查: OK
    - BPT-6评估: 行动型(14分)+知识型(12分)混合
    - SPI评估: 40分(成功率>75%)
    - CAPACITY评估: 117/160(高潜力)
    - 综合评估: 交叉分析+行动计划生成

### 待记录
- (后续里程碑将在此添加)

---

## 快速启动命令

```bash
# 启动 H5 前端 (开发模式)
cd D:\behavioral-health-project\h5
npm run dev
# 访问 http://localhost:5173

# 启动 Docker 服务
cd D:\behavioral-health-project
docker-compose up -d

# 启动 FastAPI 后端 (开发模式)
cd D:\behavioral-health-project
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 启动 BAPS 行为评估服务 (端口8001)
cd D:\behavioral-health-project
python -m uvicorn api.baps_api:app --host 0.0.0.0 --port 8001
# API文档: http://localhost:8001/docs
# Dify Schema: http://localhost:8001/openapi-tools.json

# 运行五大人格测评
python big_five_assessment.py

# 生成 PDF 报告
python generate_pdf_report.py

# 运行处方引擎并生成 Word 报告
python scripts/prescription_engine.py --test hidden_fatigue --word report.docx

# 导入评估数据 (从情绪评估报告目录)
python scripts/assessment_importer.py --source "D:\情绪评估报告\情绪评估报告" --batch "2026-01-10"

# 生成个人看板
python scripts/dashboard_generator.py --type individual --user FDBC03D79348 --export-word

# 生成群体看板
python scripts/dashboard_generator.py --type group --batch 2026-01-10 --export-word

# Obsidian 集成 (扫描数据 + 生成档案 + 向量化)
python ingest_obsidian.py

# 仅生成用户档案
python ingest_obsidian.py --generate-profiles

# 仅创建干预知识库
python ingest_obsidian.py --create-knowledge
```

---

## 重要提醒

1. **Ollama 必须运行**: 确保 `localhost:11434` 可访问
2. **Docker 内存需求**: 至少 32GB RAM
3. **知识库路径**: 需确保 J: 盘路径可访问
4. **Git 状态**: 有未提交的更改，建议定期提交

---

## 文件变更记录

| 日期 | 操作 | 文件/模块 | 描述 |
|------|------|-----------|------|
| 2026-01-19 | 创建 | PROJECT_CHRONICLE.md | 项目纪事文件 |
| 2026-01-19 | 变更 | 全局命名 | "顾问团"统一改为"教练组" |
| 2026-01-19 | 新增 | core/schemas/ | 五层架构数据结构设计 |
| 2026-01-19 | 重构 | behavior_logic.json | 整合自研五层次心理准备度模型，替换TTM |
| 2026-01-19 | 新增 | behavior_logic.json | 添加四阶段养成方案(cultivation_phases) |
| 2026-01-19 | 新增 | behavior_logic.json | 添加SPI计算公式(spi_calculation) |
| 2026-01-19 | 更新 | behavior_logic.json | 干预策略与五层次对应 |
| 2026-01-19 | 新增 | behavior_logic.json | 添加 stage_detection 阶段判定规则 |
| 2026-01-19 | 更新 | behavior_logic.json | 优化 motivation_calculation 精力-心情匹配度算法 |
| 2026-01-19 | 新增 | core/pipeline.py | 五层架构完整处理流程引擎 (650行) |
| 2026-01-19 | 新增 | models/rx_library.json | 行为处方库 (6大类处方, 分阶段话术) |
| 2026-01-19 | 更新 | core/pipeline.py | 集成 rx_library 处方库到五层架构 |
| 2026-01-19 | 新增 | scripts/prescription_engine.py | 处方引擎 (BehavioralProfile类 + 处方生成) |
| 2026-01-19 | 更新 | scripts/prescription_engine.py | 添加隐性疲劳模式识别 (HIDDEN_FATIGUE) |
| 2026-01-19 | 更新 | scripts/prescription_engine.py | 集成处方组件 (知识/视频/产品) |
| 2026-01-19 | 更新 | scripts/prescription_engine.py | Agent 指导意见生成 (Coach话术系统) |
| 2026-01-19 | 新增 | scripts/prescription_engine.py | Word 文档导出功能 (export_to_word) |
| 2026-01-19 | 新增 | core/model_manager.py | Ollama 模型管理器 (多模型池/智能路由/降级) |
| 2026-01-19 | 新增 | models/Modelfile.behavioral-coach | 行为健康教练定制模型配置 |
| 2026-01-19 | 新增 | docs/OLLAMA_INTEGRATION_GUIDE.md | Ollama 本地模型整合指南 |
| 2026-01-19 | 新增 | data/assessments/README.md | 评估数据目录结构与 JSON Schema 文档 |
| 2026-01-19 | 新增 | scripts/assessment_importer.py | 评估数据导入器 (Excel/PDF解析、标准化) |
| 2026-01-19 | 新增 | scripts/dashboard_generator.py | 看板生成器 (个人/群体看板、Word导出) |
| 2026-01-19 | 重构 | ingest_obsidian.py | Obsidian 知识库集成器 (用户档案/处方卡片/向量化) |
| 2026-01-19 | 新增 | knowledge/kb_theory/*.md | 6个干预知识库文件 (压力/疲劳/情绪/HRV/隐性疲劳/健康维护) |
| 2026-01-19 | 新增 | 用户档案/ | Obsidian 用户健康档案目录 |
| 2026-01-19 | 新增 | 行为处方/ | Obsidian 处方卡片目录 |
| 2026-01-19 | 新增 | _templates/ | Obsidian 模板目录 |
| - | 新增 | agents/ | 多专家协调系统 |
| - | 新增 | api/ | FastAPI 后端 |
| - | 新增 | core/ | 核心业务逻辑 |
| - | 删除 | requirements.txt | 旧依赖文件 |
| - | 删除 | run_agent.py | 旧运行脚本 |
| - | 删除 | system_prompt.txt | 旧提示词文件 |
| 2026-01-23 | 新增 | h5/src/ | H5 前端完整项目结构 |
| 2026-01-23 | 新增 | h5/src/views/*.vue | 5个页面组件 (Home/Chat/Tasks/Dashboard/Profile) |
| 2026-01-23 | 新增 | h5/src/components/**/*.vue | 核心组件 (MessageBubble/TaskCard/EfficacySlider/TabBar) |
| 2026-01-23 | 新增 | h5/src/stores/*.ts | Pinia 状态管理 (user/chat) |
| 2026-01-23 | 新增 | h5/src/api/*.ts | API 层 (axios 封装、类型定义) |
| 2026-01-23 | 新增 | h5/src/styles/*.scss | SCSS 样式 (变量/全局样式) |
| 2026-01-23 | 更新 | h5/vite.config.ts | Vite 配置 (代理、Vant 自动导入) |
| 2026-01-23 | 重构 | api/main.py | API 网关简化 (Dify+Ollama 双模式) |
| 2026-01-23 | 新增 | core/master_agent.py | 中枢 Master Agent (~750行，9步流程控制器) |
| 2026-01-23 | 新增 | core/master_agent.py | UserMasterProfile 用户画像管理类 |
| 2026-01-23 | 新增 | core/master_agent.py | RiskPriorityAssessor 风险优先级评估器 |
| 2026-01-23 | 新增 | data/profiles/ | 用户画像持久化存储目录 |
| 2026-01-23 | 新增 | core/schemas/master_io_schema.json | Master Agent 输入输出 Schema (含示例) |
| 2026-01-23 | 更新 | core/master_agent.py | 支持 CGM 血糖数据分析 |
| 2026-01-23 | 更新 | core/master_agent.py | 新增 InsightGenerator 数据洞察生成器 |
| 2026-01-23 | 更新 | core/master_agent.py | 支持 JSON 输入输出 (process_json 方法) |
| 2026-01-24 | 新增 | core/schemas/core_data_schema_v1_final.json | Core Data Schema v1.0 最终工程规范版 |
| 2026-01-24 | 新增 | docs/CORE_DATA_SCHEMA_v1_SPECIFICATION.md | 六大核心结构体工程规范文档 |
| 2026-01-24 | 新增 | 桌面/行健教练-核心闭环-完整版.yml | Dify TTM 双节点工作流 (完整版) |
| 2026-01-24 | 新增 | 桌面/行健教练-简单测试.yml | Dify 单节点简化测试工作流 |
| 2026-01-24 | 新增 | 桌面/dify部署.docx | Dify 部署指南文档 |
| 2026-01-24 | 新增 | core/baps/__init__.py | BAPS模块入口 |
| 2026-01-24 | 新增 | core/baps/question_bank.json | 完整题库 (150题，含四大问卷) |
| 2026-01-24 | 新增 | core/baps/questionnaires.py | 问卷类定义 (BigFive/BPT6/CAPACITY/SPI) |
| 2026-01-24 | 新增 | core/baps/scoring_engine.py | 评分引擎 (计分算法+综合评估) |
| 2026-01-24 | 新增 | core/baps/report_generator.py | 报告生成器 (JSON/Markdown格式) |
| 2026-01-24 | 新增 | api/baps_api.py | BAPS REST API服务 (端口8001) |
| 2026-01-24 | 新增 | dify_workflows/baps_assessment_workflow.yml | BAPS Dify工作流配置 |
| 2026-01-24 | 新增 | test_baps.py | BAPS单元测试脚本 |
| 2026-01-24 | 新增 | test_baps_integration.py | BAPS集成测试脚本 |
| 2026-01-24 | 新增 | metabolic-core/ | 代谢慢病行为健康决策系统内核 (TypeScript) |

---

### 2026-01-24 (续2)
- **Metabolic Core 决策系统内核完整实现** (重要里程碑):
  - 新增 `metabolic-core/` - TypeScript实现的代谢慢病行为健康决策系统内核
  - 技术栈: TypeScript 5.3 + Express 4.18 + Node.js
  - **四层架构完整实现**:
    1. **Signal Layer** - 设备信号处理层
       - `SignalSchema.ts` - 信号数据结构 (CGM/BP/HRV/Scale/Watch)
       - `SignalNormalizationService.ts` - 信号标准化服务
    2. **Trajectory Layer** - 行为轨迹建模层
       - `TrajectorySchema.ts` - 轨迹数据结构 (TTM阶段/行为事件/干预记录)
       - `TrajectoryService.ts` - 轨迹构建与分析服务
    3. **Libraries Layer** - 知识库层 (7个模块)
       - `PhenotypeMapping.ts` - 表型映射库 (7个预定义表型)
       - `InterventionPlaybook.ts` - 干预剧本库 (5个剧本+16个杠杆)
       - `BehaviorChangeEngine.ts` - 行为改变引擎 (TTM阶段+习惯锁定)
       - `AssessmentSurvey.ts` - 评估问卷库 (PHQ-9/GAD-7/DSM)
       - `ContentMaterial.ts` - 内容素材库 (文章+话术脚本+消息模板)
       - `CommercialResource.ts` - 商业资源库 (8个资源)
       - `CoachTraining.ts` - 教练训练库 (模块+案例+AI Prompt)
    4. **Registry Layer** - 知识注册中心
       - `KnowledgeRegistry.ts` - 统一知识索引与搜索
       - `LibraryManager.ts` - 知识库统一管理器
    5. **Orchestrator Layer** - 决策编排层
       - `InterventionPlanner.ts` - 干预规划器
       - `Orchestrator.ts` - 核心决策编排器 (会话管理+信号处理+干预生成)
  - **REST API服务**:
    - `routes.ts` - 完整API路由 (35+个端点)
    - `server.ts` - Express服务器 (端口8002)
    - **核心端点**:
      - `POST /api/signals` - 处理设备信号
      - `GET /api/dashboard/:userId` - 用户仪表盘
      - `GET /api/context/:userId` - 对话上下文
      - `POST /api/interventions/generate` - 生成干预计划
      - `GET /api/knowledge/search` - 知识搜索
      - `GET /api/phenotypes` - 表型列表
      - `GET /api/playbooks` - 干预剧本
      - `GET /api/content/recommend` - 内容推荐
      - `GET /api/resources/recommend` - 资源推荐
    - `GET /openapi-tools.json` - Dify集成Schema
  - **示例数据**:
    - `sample-data/signals.json` - 示例信号数据
    - `sample-data/user-profiles.json` - 示例用户档案
  - **测试脚本**:
    - `tests/integration.test.ts` - Jest集成测试
    - `scripts/test-core.ts` - 核心功能测试脚本
  - **预定义表型 (7种)**:
    - PHE-001: 餐后高血糖型
    - PHE-002: 黎明现象型
    - PHE-003: 血糖波动敏感型
    - PHE-004: 夜间低血糖型
    - PHE-005: 压力应激型
    - PHE-006: 久坐代谢型
    - PHE-007: 睡眠-代谢失调型
  - **预定义干预剧本 (5个)**:
    - PLB-001: 餐后高血糖管理
    - PLB-002: 夜间低血糖预防
    - PLB-003: 压力应激管理
    - PLB-004: 久坐代谢改善
    - PLB-005: 睡眠-代谢联合干预

### 2026-01-24 (续3)
- **教练认证体系模块实现** (重要里程碑):
  - 新增 `metabolic-core/src/certification/` - 行为健康教练认证体系模块
  - 导入并执行 `D:\行为健康教练认证体系 · 工程级系统规范.txt`
  - **五级认证等级体系**:
    - L0: 公众学习者 (免费入口层)
    - L1: 初级行为健康教练 (助理级，可服务低风险人群)
    - L2: 中级行为健康教练 (独立上岗，平台主力教练)
    - L3: 高级行为健康教练 (专项/慢病专家级)
    - L4: 行为健康督导/讲师/专家 (方法论中枢)
  - **K-M-S-V 四维能力模型**:
    - Knowledge (知识体系): 行为科学/代谢医学/生活方式医学/心理动机/数据解读
    - Method (方法体系): 行为评估/阶段模型/处方设计/干预路径/复盘调整
    - Skill (核心技能): 动机访谈/教练对话/阻抗处理/目标拆解/陪伴反馈
    - Value (观念心智): 主动健康观/行为伦理/边界认知/长程陪伴
  - **核心数据结构** (`CertificationSchema.ts`):
    - `CoachProfile` - 教练档案 (等级/专项/能力模型/案例/权限)
    - `CoachCase` - 教练案例 (风险类型/干预路径/结果指标/督导评分)
    - `CoachCompetencyModel` - K-M-S-V能力模型评分
    - `CourseDefinition` - 课程定义 (模块/时长/前置条件/评估标准)
    - `ExamDefinition` - 考试定义 (类型/分数/权重)
    - `LevelRequirement` - 等级要求 (课程/考试/实战/平台评分)
    - `PromotionApplication` - 晋级申请
    - `TrainingSession` - 智能陪练会话
  - **认证服务** (`CertificationService.ts`):
    - 预定义课程库 (13门课程: L0-L2)
    - 预定义考试库 (11项考试)
    - 等级要求配置 (5级完整定义)
    - `createCoachProfile()` - 创建教练档案
    - `completeCourse()` - 完成课程
    - `passExam()` - 通过考试
    - `createCase()` - 创建案例
    - `createTrainingSession()` - 创建训练会话
  - **晋级判定引擎** (`PromotionEngine.ts`):
    - `evaluate()` - 评估晋级资格 (理论/技能/案例/平台评分/带教)
    - `promote()` - 执行晋级
    - `createApplication()` - 创建晋级申请
    - 自动推荐补修模块
    - 授权新Agent权限
  - **专项方向 (6个)**:
    - diabetes_reversal: 糖尿病逆转专项
    - hypertension: 高血压专项
    - weight_management: 体重管理专项
    - stress_psychology: 心理压力专项
    - metabolic_syndrome: 代谢综合征专项
    - sleep_optimization: 睡眠优化专项
  - **REST API端点** (15个新增):
    - `GET /api/certification/levels` - 获取认证等级要求
    - `POST /api/certification/coaches` - 创建教练档案
    - `GET /api/certification/coaches` - 获取教练列表
    - `GET /api/certification/coaches/:coachId` - 获取教练档案
    - `GET /api/certification/coaches/:coachId/cases` - 获取教练案例
    - `POST /api/certification/coaches/:coachId/courses` - 完成课程
    - `POST /api/certification/coaches/:coachId/exams` - 通过考试
    - `POST /api/certification/coaches/:coachId/cases` - 创建案例
    - `GET /api/certification/coaches/:coachId/evaluate` - 评估晋级资格
    - `POST /api/certification/coaches/:coachId/promote` - 执行晋级
    - `GET /api/certification/courses` - 获取课程列表
    - `GET /api/certification/exams` - 获取考试列表
    - `POST /api/certification/training-sessions` - 创建训练会话
  - **商业闭环设计**:
    - 等级越高 → 客户单价越高
    - 等级越高 → 分成比例越高 (30%→50%→65%→75%)
    - 等级越高 → Agent权限越多
    - 等级越高 → 可服务人群风险等级越高
  - **与主动行为健康中枢整合**:
    - 共享评估体系、干预路径库、行为模型
    - 教练即Agent: L1→基础执行, L2→个性化干预, L3→专项专家, L4→策略督导
- **新增数据结构扩展**:
  - `MetabolicFeatureSet` - 代谢特征集 (glucose/hrv/activity features)
  - `ProgramProtocol` - 项目协议 (14天结构化干预)
  - `UserLatentProfile` - 用户潜在画像 (风险/表型/阶段/依从)

---

*此文件应在每次重大更新后维护，以确保项目历史的完整性。*
