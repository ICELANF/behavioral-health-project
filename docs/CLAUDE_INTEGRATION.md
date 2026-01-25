# Claude API 与行为健康平台集成方案

> 生成时间: 2026-01-26
> 基于: Claude Platform 官方文档

---

## 一、集成架构总览

### 八爪鱼架构中的定位

```
                    ┌─────────────────────────────────┐
                    │           大脑 (Brain)           │
                    ├─────────────────────────────────┤
                    │  ┌─────────┐    ┌─────────────┐ │
                    │  │ Ollama  │    │ Claude API  │ │
                    │  │ (本地)  │    │  (云端)     │ │
                    │  │ qwen2.5 │    │ claude-4    │ │
                    │  │ deepseek│    │ opus/sonnet │ │
                    │  └────┬────┘    └──────┬──────┘ │
                    │       │    智能路由    │        │
                    │       └───────┬────────┘        │
                    └───────────────┼─────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
   ┌─────────┐               ┌─────────┐               ┌─────────┐
   │ 触手1   │               │ 触手2   │               │ 触手3   │
   │专家Chat │               │用户行为 │               │教练培养 │
   │  flow   │               │  养成   │               │  体系   │
   └─────────┘               └─────────┘               └─────────┘
```

### 双引擎模式

| 引擎 | 场景 | 优势 | 成本 |
|------|------|------|------|
| Ollama (本地) | 日常对话、简单问答 | 免费、隐私、低延迟 | 硬件成本 |
| Claude API (云端) | 复杂推理、工具调用、深度分析 | 高质量、强能力 | API费用 |

---

## 二、直接集成方案

### 2.1 作为替代大脑 (Alternative Brain)

**场景**: 当本地 Ollama 模型能力不足时，切换到 Claude API

```python
# 智能路由示例
class BrainRouter:
    def route(self, task_complexity: str, task_type: str):
        if task_complexity == "high" or task_type in ["tool_use", "reasoning"]:
            return "claude-api"
        return "ollama"
```

**适用场景**:
- 复杂健康方案制定
- 多步骤推理任务
- 需要工具调用的场景

### 2.2 Tool Use 集成 (工具调用)

Claude API 的 Tool Use 功能可以让 AI 调用我们定义的健康工具。

**工具定义示例**:

```json
{
  "name": "ttm_assessment",
  "description": "评估用户当前的行为改变阶段 (TTM模型)",
  "input_schema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "用户ID"
      },
      "behavior_type": {
        "type": "string",
        "enum": ["diet", "exercise", "sleep", "medication"],
        "description": "要评估的行为类型"
      },
      "responses": {
        "type": "array",
        "items": { "type": "string" },
        "description": "用户对评估问题的回答"
      }
    },
    "required": ["user_id", "behavior_type", "responses"]
  }
}
```

**可定义的健康工具清单**:

| 工具名称 | 功能 | 所属触手 |
|----------|------|----------|
| `ttm_assessment` | TTM阶段评估 | 触手2 |
| `diet_analyzer` | 饮食分析 | 触手1/2 |
| `exercise_tracker` | 运动记录查询 | 触手2 |
| `goal_setter` | SMART目标设定 | 触手2 |
| `coach_evaluator` | 教练能力评估 | 触手3 |
| `case_analyzer` | 案例分析 | 触手3 |
| `knowledge_search` | 知识库检索 | 全部 |

### 2.3 Agent Skills 集成

Claude 的 Agent Skills 可以创建专业化的健康教练技能。

**技能定义示例**:

```yaml
# 动机访谈技能
skill_name: motivational_interviewing
description: |
  运用动机访谈(MI)技术，帮助用户探索和解决矛盾心理，
  增强内在改变动机。

triggers:
  - 用户表现出矛盾心理
  - 用户缺乏改变动机
  - 用户表示"不想/不能"

techniques:
  - OARS: 开放式提问、肯定、反映、总结
  - 引出改变语言
  - 滚动与阻抗
```

---

## 三、间接集成方案

### 3.1 Dify + Claude API 混合架构

```
┌─────────────────────────────────────────────────────┐
│                    Dify 平台                         │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Ollama 模型 │  │ Claude API  │  │  其他模型   │ │
│  │  (已配置)   │  │  (待配置)   │  │  (可扩展)   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │        │
│         └────────────────┼────────────────┘        │
│                          ▼                          │
│              ┌───────────────────┐                  │
│              │   智能编排引擎    │                  │
│              │ (Chatflow/Agent)  │                  │
│              └─────────┬─────────┘                  │
│                        │                            │
└────────────────────────┼────────────────────────────┘
                         ▼
                  ┌─────────────┐
                  │  专家应用   │
                  │ (吃动守恒等)│
                  └─────────────┘
```

**配置步骤**:
1. 在 Dify 后台添加 Claude 模型供应商
2. 输入 Claude API Key
3. 在 Chatflow 中配置模型切换逻辑

### 3.2 FastAPI 后端集成

在后端 API 层集成 Claude，实现业务逻辑。

```python
# app/services/ai_service.py

from anthropic import Anthropic

class AIService:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY)

    async def chat_with_tools(
        self,
        messages: list,
        tools: list,
        model: str = "claude-sonnet-4-20250514"
    ):
        """使用 Claude Tool Use 进行对话"""
        response = self.claude_client.messages.create(
            model=model,
            max_tokens=4096,
            tools=tools,
            messages=messages
        )
        return response

    async def assess_ttm_stage(self, user_id: str, responses: list):
        """评估用户 TTM 阶段"""
        tools = [TTM_ASSESSMENT_TOOL]
        messages = [
            {"role": "user", "content": f"根据以下回答评估用户的行为改变阶段: {responses}"}
        ]
        return await self.chat_with_tools(messages, tools)
```

### 3.3 知识库增强 (RAG + Claude)

利用 Claude 的 100万 token 上下文窗口，增强知识检索。

```
┌─────────────────────────────────────────┐
│           知识库检索流程                 │
├─────────────────────────────────────────┤
│                                         │
│  用户问题 ──▶ 向量检索 ──▶ 相关文档     │
│                  │                      │
│                  ▼                      │
│         ┌───────────────┐               │
│         │   Claude API  │               │
│         │ (1M上下文窗口)│               │
│         │ 深度理解+整合 │               │
│         └───────┬───────┘               │
│                 │                       │
│                 ▼                       │
│           高质量回答                     │
│                                         │
└─────────────────────────────────────────┘
```

---

## 四、特性对接矩阵

### Claude API 特性与平台功能对应

| Claude 特性 | 平台应用 | 触手 | 优先级 |
|-------------|----------|------|--------|
| **Tool Use** | 健康工具调用 | 全部 | P0 |
| **Extended Thinking** | 复杂方案制定 | 触手1/2 | P1 |
| **Citations** | 知识来源标注 | 触手1 | P1 |
| **Web Search** | 最新健康资讯 | 触手1 | P2 |
| **Code Execution** | 数据分析可视化 | 触手3 | P2 |
| **PDF Support** | 病历/报告解读 | 触手2 | P1 |
| **Prompt Caching** | 降低成本 | 全部 | P1 |
| **Batch API** | 批量评估 | 触手3 | P2 |

### 4.1 Extended Thinking (深度思考)

适用于复杂健康方案制定场景。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # 思考预算
    },
    messages=[{
        "role": "user",
        "content": "为一位55岁、BMI 28、有2型糖尿病的用户制定3个月的行为改变方案"
    }]
)
```

### 4.2 Citations (引用标注)

让专家知识回答有据可查。

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    citations={"enabled": True},
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "text", "data": knowledge_base_content},
                    "title": "行为健康专家知识库"
                },
                {
                    "type": "text",
                    "text": "TTM模型的5个阶段分别是什么？"
                }
            ]
        }
    ]
)
# 返回结果会包含 citations 字段，标注信息来源
```

### 4.3 Prompt Caching (提示缓存)

降低重复系统提示的成本。

```python
# 缓存专家系统提示
system_prompt = {
    "type": "text",
    "text": EXPERT_SYSTEM_PROMPT,  # 大段专家知识
    "cache_control": {"type": "ephemeral"}
}

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=[system_prompt],
    messages=user_messages
)
# 后续请求复用缓存，降低90%成本
```

---

## 五、实施路线图

### 第一阶段: 基础集成 (1-2周)

```
┌─────────────────────────────────────────────────────┐
│ Phase 1: 基础集成                                    │
├─────────────────────────────────────────────────────┤
│ □ 在 Dify 中配置 Claude 模型供应商                  │
│ □ 创建 Claude 版本的专家 Chatflow                   │
│ □ 实现 Ollama/Claude 智能路由                       │
│ □ 测试基本对话功能                                   │
└─────────────────────────────────────────────────────┘
```

### 第二阶段: Tool Use 集成 (2-3周)

```
┌─────────────────────────────────────────────────────┐
│ Phase 2: 工具调用                                    │
├─────────────────────────────────────────────────────┤
│ □ 定义健康工具 JSON Schema                          │
│ □ 实现 ttm_assessment 工具                          │
│ □ 实现 diet_analyzer 工具                           │
│ □ 实现 goal_setter 工具                             │
│ □ 在 FastAPI 中创建工具执行端点                     │
│ □ 测试工具调用完整流程                               │
└─────────────────────────────────────────────────────┘
```

### 第三阶段: 高级特性 (3-4周)

```
┌─────────────────────────────────────────────────────┐
│ Phase 3: 高级特性                                    │
├─────────────────────────────────────────────────────┤
│ □ 集成 Extended Thinking (复杂方案)                 │
│ □ 集成 Citations (知识引用)                         │
│ □ 配置 Prompt Caching (成本优化)                    │
│ □ 集成 PDF Support (报告解读)                       │
│ □ 完善智能路由策略                                   │
└─────────────────────────────────────────────────────┘
```

---

## 六、成本估算

### Claude API 定价 (参考)

| 模型 | 输入 (每百万token) | 输出 (每百万token) |
|------|-------------------|-------------------|
| Claude Sonnet 4 | $3 | $15 |
| Claude Opus 4 | $15 | $75 |
| Claude Haiku 3.5 | $0.8 | $4 |

### 混合架构成本优化策略

```
┌─────────────────────────────────────────────────────┐
│              成本优化策略                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  简单对话 ──▶ Ollama (免费)                         │
│  复杂推理 ──▶ Claude Sonnet (性价比)                │
│  深度分析 ──▶ Claude Opus (最强能力)                │
│  批量处理 ──▶ Batch API (50%折扣)                   │
│  重复提示 ──▶ Prompt Caching (90%折扣)              │
│                                                     │
│  预估月成本: $50-200 (中等使用量)                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 七、环境配置

### 新增环境变量

```bash
# .env 新增

# ----------------
# Claude API 配置
# ----------------
CLAUDE_API_KEY=sk-ant-api03-xxxxxx
CLAUDE_MODEL_DEFAULT=claude-sonnet-4-20250514
CLAUDE_MODEL_ADVANCED=claude-opus-4-20250514
CLAUDE_MODEL_FAST=claude-3-5-haiku-20241022

# 智能路由配置
AI_ROUTER_ENABLED=true
AI_ROUTER_COMPLEXITY_THRESHOLD=0.7
```

### 依赖安装

```bash
# Python 后端
pip install anthropic>=0.40.0

# 或添加到 requirements.txt
anthropic>=0.40.0
```

---

## 八、代码示例

### 完整的 Tool Use 示例

```python
# app/services/claude_tool_service.py

from anthropic import Anthropic
from typing import List, Dict, Any

# 定义健康工具
HEALTH_TOOLS = [
    {
        "name": "ttm_assessment",
        "description": "评估用户的行为改变阶段(TTM模型)",
        "input_schema": {
            "type": "object",
            "properties": {
                "behavior": {"type": "string", "description": "行为类型"},
                "answers": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["behavior", "answers"]
        }
    },
    {
        "name": "set_health_goal",
        "description": "为用户设定SMART健康目标",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_type": {"type": "string"},
                "current_value": {"type": "number"},
                "target_value": {"type": "number"},
                "duration_weeks": {"type": "integer"}
            },
            "required": ["goal_type", "target_value", "duration_weeks"]
        }
    }
]

class ClaudeToolService:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def process_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """执行工具调用"""
        if tool_name == "ttm_assessment":
            return self._run_ttm_assessment(tool_input)
        elif tool_name == "set_health_goal":
            return self._set_health_goal(tool_input)
        return "未知工具"

    def _run_ttm_assessment(self, input: dict) -> str:
        # 实际的TTM评估逻辑
        behavior = input.get("behavior")
        answers = input.get("answers", [])
        # ... 评估逻辑
        return f"用户在{behavior}方面处于'准备期'阶段"

    def _set_health_goal(self, input: dict) -> str:
        # 实际的目标设定逻辑
        return f"已设定目标: {input['goal_type']} 从当前值达到 {input['target_value']}"

    async def chat_with_health_tools(
        self,
        user_message: str,
        history: List[Dict] = None
    ) -> str:
        """带健康工具的对话"""
        messages = history or []
        messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system="你是一位专业的行为健康教练，帮助用户改善健康行为。",
            tools=HEALTH_TOOLS,
            messages=messages
        )

        # 处理工具调用
        while response.stop_reason == "tool_use":
            tool_use_block = next(
                block for block in response.content
                if block.type == "tool_use"
            )

            tool_result = self.process_tool_call(
                tool_use_block.name,
                tool_use_block.input
            )

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": tool_result
                }]
            })

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                tools=HEALTH_TOOLS,
                messages=messages
            )

        # 返回最终文本回复
        return response.content[0].text
```

---

## 九、总结

### 集成价值

| 价值点 | 说明 |
|--------|------|
| **能力增强** | Claude 补充 Ollama 的复杂推理能力 |
| **工具调用** | 实现健康工具的智能调用 |
| **成本可控** | 智能路由 + 缓存优化成本 |
| **可扩展性** | 双引擎架构便于未来扩展 |

### 推荐实施顺序

1. **立即可做**: 在 Dify 添加 Claude 模型供应商
2. **短期目标**: 实现基础 Tool Use (TTM评估)
3. **中期目标**: 完善工具生态，集成高级特性
4. **长期目标**: 构建完整的智能健康教练系统

---

*文档版本: v1.0*
*最后更新: 2026-01-26*
