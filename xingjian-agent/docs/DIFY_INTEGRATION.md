# Dify + 行健Agent 集成指南

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面                              │
│                     (Dify Web/App)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Dify 平台 (Docker)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   工作流    │  │   知识库    │  │   自定义工具        │  │
│  │   编排      │  │   RAG      │  │   (行健Agent API)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│  Ollama LLM     │ │  向量数据库     │ │  行健Agent API      │
│  (qwen2.5:14b)  │ │  (PostgreSQL)   │ │  (localhost:8000)   │
│  :11434         │ │                 │ │                     │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────────┐
                                        │  行健Agent 核心     │
                                        │  - 四专家协作       │
                                        │  - 八爪鱼限幅       │
                                        │  - RAG 知识库       │
                                        └─────────────────────┘
```

## 快速开始

### 前置条件

- Windows 10/11
- Docker Desktop (WSL2 后端)
- Ollama 已安装并运行
- Python 3.10+

### 一键部署

```powershell
# 1. 部署 Dify
.\scripts\deploy_dify.ps1

# 2. 安装 API 依赖
pip install fastapi uvicorn pydantic

# 3. 启动所有服务
.\scripts\start_all_services.ps1
```

## 详细配置步骤

### Step 1: 配置 Ollama 网络访问

Dify 运行在 Docker 中，需要能访问宿主机的 Ollama。

**Windows 环境变量设置：**
1. 右键「此电脑」→ 属性 → 高级系统设置 → 环境变量
2. 新建系统变量：
   - 变量名：`OLLAMA_HOST`
   - 变量值：`0.0.0.0:11434`
3. 重启 Ollama

### Step 2: 在 Dify 中添加 Ollama 模型

1. 访问 http://localhost (首次需设置管理员账号)
2. 点击右上角头像 → 设置 → 模型供应商
3. 找到 **Ollama**，点击「添加模型」
4. 填写配置：
   - 模型名称：`qwen2.5:14b`
   - 基础 URL：`http://host.docker.internal:11434`
   - 模型类型：LLM
   - 上下文长度：4096
5. 点击保存

### Step 3: 启动行健Agent API

```bash
cd J:\xingjian-agent
python api\xingjian_api.py
```

验证：访问 http://localhost:8000/docs 查看 API 文档

### Step 4: 在 Dify 中添加行健Agent 工具

1. 在 Dify 中创建应用（聊天助手或工作流）
2. 点击「工具」→「自定义」→「创建自定义工具」
3. 工具名称：`行健行为教练`
4. Schema 来源：选择「从 URL 导入」
5. URL：`http://host.docker.internal:8000/openapi-tools.json`
6. 点击导入，然后保存

### Step 5: 创建健康咨询应用

**方式一：聊天助手**
1. 创建「聊天助手」应用
2. 添加工具：行健行为教练
3. 设置提示词：
```
你是一个健康助手，可以调用行健行为教练来回答用户的健康问题。
当用户询问健康相关问题时，使用 healthConsultation 工具获取专业建议。

可用的专家：
- mental_health: 心理咨询师
- nutrition: 营养师
- sports_rehab: 运动康复师
- tcm_wellness: 中医养生师
```

**方式二：工作流**
1. 创建「工作流」应用
2. 添加节点：
   - 开始 → LLM(意图识别) → 条件分支 → 行健工具调用 → LLM(回复优化) → 结束

## API 接口说明

### 健康咨询 `/chat`

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我最近总是失眠怎么办？"}'
```

响应：
```json
{
  "response": "我理解失眠给您带来的困扰...",
  "primary_expert": "心理咨询师",
  "consulted_experts": [],
  "confidence": 0.85
}
```

### 效能限幅 `/clamping`

```bash
curl -X POST http://localhost:8000/clamping \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "efficacy_score": 25,
    "tasks": [
      {"id": 1, "content": "深度冥想20分钟", "difficulty": 4},
      {"id": 2, "content": "记录情绪日志", "difficulty": 2},
      {"id": 3, "content": "3次深呼吸", "difficulty": 1}
    ],
    "wearable_data": {"hr": 95}
  }'
```

响应：
```json
{
  "clamped_tasks": [{"id": 3, "content": "3次深呼吸", "difficulty": 1}],
  "final_efficacy": 5,
  "clamping_level": "minimal",
  "reasoning_path": [...]
}
```

## 高级配置

### 使用外部知识库

Dify 自带知识库功能，可以补充行健Agent 的专业知识：

1. 在 Dify 中创建知识库
2. 上传健康相关文档（PDF/TXT/Markdown）
3. 在应用中同时引用 Dify 知识库 + 行健工具

### 工作流示例：健康评估流程

```
开始
  ↓
LLM节点: 分析用户诉求类型
  ↓
条件分支:
  - 心理问题 → 行健工具(expert_id=mental_health)
  - 饮食问题 → 行健工具(expert_id=nutrition)
  - 运动问题 → 行健工具(expert_id=sports_rehab)
  - 养生问题 → 行健工具(expert_id=tcm_wellness)
  - 其他 → 默认回复
  ↓
LLM节点: 优化回复格式
  ↓
结束
```

## 故障排查

### Docker 连接宿主机失败

- Windows: 使用 `host.docker.internal`
- Linux: 使用 `172.17.0.1` 或配置 `network_mode: host`

### Ollama 连接超时

1. 检查 `OLLAMA_HOST` 环境变量
2. 检查防火墙设置
3. 验证：`curl http://localhost:11434/api/tags`

### 行健API 无法访问

1. 确保 API 服务已启动
2. 检查端口 8000 是否被占用
3. 查看 API 日志

## 服务端口汇总

| 服务 | 端口 | 用途 |
|------|------|------|
| Dify Web | 80 | 用户界面 |
| Dify API | 5001 | Dify 后端 |
| Ollama | 11434 | LLM 服务 |
| 行健API | 8000 | Agent 接口 |
| PostgreSQL | 5432 | Dify 数据库 |
| Redis | 6379 | Dify 缓存 |
