# 快速开始指南 Quick Start Guide

> 行为健康平台 - 5分钟快速体验

---

## 一、环境要求

### 必需软件
- **Python**: >= 3.10
- **Git**: 用于克隆仓库
- **虚拟环境**: venv / conda

### 可选软件（完整功能）
- **Docker**: 用于运行基础设施
- **Ollama**: 本地LLM推理
- **PostgreSQL**: 数据库（或使用Docker）
- **Redis**: 缓存（或使用Docker）

---

## 二、快速安装（5分钟）

### 方式1：使用现有虚拟环境（推荐）

```bash
# 1. 进入项目目录
cd D:\behavioral-health-project

# 2. 激活虚拟环境
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 验证安装
python -m behavioral_health --help
```

### 方式2：全新安装

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/behavioral-health-project.git
cd behavioral-health-project

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装项目（开发模式）
pip install -e .

# 6. 验证安装
python -m behavioral_health --help
```

---

## 三、首次运行（2分钟）

### 步骤1：初始化系统

```bash
python -m behavioral_health init
```

**输出示例：**
```
============================================================
🔧 系统初始化
============================================================
📝 创建 .env 文件...
✓ .env 文件已创建
⚠️  请编辑 .env 文件配置数据库等信息

📁 创建必要目录...
  ✓ data/profiles
  ✓ data/assessments
  ✓ data/logs
  ✓ data/uploads

🔍 验证外部服务...
  ✗ Ollama服务未运行
    提示：请先启动 Ollama
  ℹ️  多模态系统未运行（可选服务）

✅ 初始化完成！

下一步：
  1. 编辑 .env 文件配置必要参数
  2. 运行 'python -m behavioral_health serve' 启动服务
```

### 步骤2：配置环境变量

编辑 `.env` 文件，配置基础参数：

```bash
# API配置
API_HOST=127.0.0.1
API_PORT=8000

# Ollama配置（如果已安装）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# 多模态系统（可选）
MULTIMODAL_API_URL=http://localhost:8090

# 数据库（开发环境可以先跳过）
# DATABASE_URL=postgresql://user:password@localhost:5432/behavioral_health
```

### 步骤3：启动服务

```bash
# 开发模式（热重载）
python -m behavioral_health serve --reload

# 生产模式
python -m behavioral_health serve --host 0.0.0.0 --port 8000
```

**输出示例：**
```
============================================================
🚀 行为健康平台 - 启动中...
============================================================
📍 主机: 127.0.0.1:8000
🔄 热重载: 启用
👷 工作进程: 1

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 步骤4：验证运行

打开浏览器访问：
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **系统状态**: http://localhost:8000/orchestrator/status

---

## 四、CLI命令速查

### 基础命令

```bash
# 显示帮助
python -m behavioral_health --help

# 显示版本
python -m behavioral_health --version

# 系统初始化
python -m behavioral_health init

# 启动服务
python -m behavioral_health serve

# 系统状态检查
python -m behavioral_health status

# 运行测试
python -m behavioral_health test
```

### 数据库命令

```bash
# 初始化数据库
python -m behavioral_health db init

# 加载种子数据
python -m behavioral_health db seed

# 执行迁移
python -m behavioral_health db migrate
```

### 用户管理命令

```bash
# 创建普通用户
python -m behavioral_health user create alice --email alice@example.com

# 创建管理员
python -m behavioral_health user create admin --email admin@example.com --admin

# 列出所有用户
python -m behavioral_health user list
```

---

## 五、测试端到端流程

### 1. 使用curl测试评估API

```bash
# 提交评估请求
curl -X POST http://localhost:8000/api/assessment/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "text_content": "最近工作压力很大，天天加班，晚上睡不好",
    "glucose_values": [6.5, 11.2, 13.5],
    "hrv_values": [58, 62, 55]
  }'
```

**预期响应：**
```json
{
  "assessment_id": "ASS-abc123",
  "risk_level": "R3",
  "risk_score": 75.0,
  "triggers": [
    {"tag_id": "stress_overload", "severity": "high"},
    {"tag_id": "poor_sleep", "severity": "moderate"},
    {"tag_id": "high_glucose", "severity": "high"}
  ],
  "routing_decision": {
    "primary_agent": "StressAgent",
    "secondary_agents": ["SleepAgent", "GlucoseAgent"]
  }
}
```

### 2. 使用Python测试

```python
import httpx
import asyncio

async def test_assessment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/assessment/submit",
            json={
                "user_id": 1,
                "text_content": "今天感觉不错，血糖也正常",
                "glucose_values": [5.5, 6.2, 7.5],
                "hrv_values": [72, 75, 78]
            }
        )
        print(response.json())

asyncio.run(test_assessment())
```

### 3. 运行完整测试套件

```bash
# 运行所有测试
python -m behavioral_health test

# 运行端到端测试
python -m behavioral_health test -p tests/test_end_to_end.py -v

# 运行多模态集成测试
python -m behavioral_health test -p tests/test_multimodal_integration.py -v
```

---

## 六、常见问题

### Q1: 启动时提示"端口已被占用"

```bash
# Windows查看端口占用
netstat -ano | findstr :8000

# 结束占用进程
taskkill /PID <进程ID> /F

# 或更换端口
python -m behavioral_health serve --port 8001
```

### Q2: 提示"Ollama服务未运行"

```bash
# 下载安装Ollama
# 访问：https://ollama.ai/download

# 启动Ollama
ollama serve

# 拉取模型
ollama pull qwen2.5:7b
```

### Q3: 提示"多模态系统未运行"

多模态系统是可选服务，不影响核心功能。如需启用：

```bash
cd D:\multimodal-system-standalone\multimodal-system
python main.py --port 8090
```

### Q4: 数据库连接失败

开发阶段可以不使用PostgreSQL，系统会使用SQLite：

```bash
# .env中设置
DATABASE_URL=sqlite:///./data/behavioral_health.db
```

### Q5: 无法访问API文档

确保服务已启动，然后访问：
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## 七、下一步

### 开发者
1. 阅读 `docs/PROJECT_OVERVIEW_EXECUTIVE.md` 了解架构
2. 阅读 `docs/L2_ASSESSMENT_ENGINE.md` 了解评估引擎
3. 查看 `knowledge/triggers/README.md` 了解Trigger系统
4. 运行测试：`python -m behavioral_health test -v`

### 用户
1. 访问Admin Portal：http://localhost:5173
2. 使用H5应用（开发中）
3. 查看评估报告

### 部署
1. 阅读 `docs/DEPLOYMENT_ARCHITECTURE.md`
2. 使用Docker Compose部署完整栈
3. 配置生产环境变量

---

## 八、获取帮助

### 文档
- 项目概览：`docs/PROJECT_OVERVIEW_EXECUTIVE.md`
- 技术文档：`docs/` 目录
- API文档：http://localhost:8000/docs

### 社区
- GitHub Issues：报告问题和建议
- Discussions：技术讨论和问答

### 联系
- Email: team@behavioral-health.com
- Slack: [加入工作区]

---

**🎉 恭喜！你已成功运行行为健康平台！**

现在可以：
- ✅ 通过CLI管理系统
- ✅ 调用API进行健康评估
- ✅ 查看实时文档
- ✅ 运行端到端测试

下一步：探索完整功能，查看 `docs/PROJECT_ROADMAP.md` 了解开发计划。
