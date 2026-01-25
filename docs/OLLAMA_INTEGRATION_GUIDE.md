# Ollama 本地模型整合指南

> 最后更新: 2026-01-19
> 适用于行健行为教练项目

---

## 一、当前集成状态

### 1.1 已使用的模型

| 用途 | 模型 | 配置位置 |
|------|------|----------|
| LLM (对话/推理) | `qwen2.5:14b` | config.yaml |
| Embedding (向量化) | `nomic-embed-text:latest` | config.yaml |

### 1.2 Ollama 调用点

| 文件 | 功能 | 调用方式 |
|------|------|----------|
| `agents/factory.py` | 全局模型设置 | `Settings.llm = Ollama(...)` |
| `agents/collaboration.py` | 多专家协作综合 | `self.llm.complete(prompt)` |
| `api/services.py` | 任务分解器 | `self.llm.complete(prompt)` |
| `ingest_obsidian.py` | 知识库向量化 | `OllamaEmbedding(...)` |

### 1.3 当前架构图

```
用户请求
    ↓
FastAPI (api/routes.py)
    ↓
AgentOrchestrator (agents/orchestrator.py)
    ↓
IntentRouter → 选择专家 (基于关键词)
    ↓
ExpertAgent.chat() → LlamaIndex ChatEngine → Ollama LLM
    ↓
CollaborationProtocol → 多专家综合 → Ollama LLM
    ↓
OctopusClampingEngine → 效能限幅
    ↓
返回响应
```

---

## 二、优化整合方案

### 2.1 模型分层策略

针对不同场景使用不同大小的模型，优化响应速度与资源使用：

```yaml
# config.yaml 建议扩展
model:
  # 轻量级模型 - 快速响应
  llm_fast: "qwen2.5:7b"        # 用于: 关键词提取、意图识别

  # 标准模型 - 日常对话
  llm_standard: "qwen2.5:14b"   # 用于: 专家对话、建议生成

  # 重量级模型 - 复杂推理
  llm_heavy: "qwen2.5:32b"      # 用于: 多专家综合、复杂分析
  # 或使用推理增强模型
  llm_reasoning: "deepseek-r1:7b"  # 用于: 行为模式分析、处方推理

  # 嵌入模型
  embed: "nomic-embed-text:latest"

  ollama_base_url: "http://localhost:11434"
```

### 2.2 推荐本地模型清单

根据行为健康场景，推荐以下模型：

| 模型 | 大小 | 适用场景 | 安装命令 |
|------|------|----------|----------|
| `qwen2.5:7b` | 4.7GB | 快速响应、简单对话 | `ollama pull qwen2.5:7b` |
| `qwen2.5:14b` | 9GB | 标准专家对话 (当前使用) | `ollama pull qwen2.5:14b` |
| `qwen2.5:32b` | 20GB | 复杂多专家综合 | `ollama pull qwen2.5:32b` |
| `deepseek-r1:7b` | 4.7GB | 推理增强、行为分析 | `ollama pull deepseek-r1` |
| `llama3.2:3b` | 2GB | 超轻量、嵌入式场景 | `ollama pull llama3.2` |
| `phi4:14b` | 9GB | 指令遵循、结构化输出 | `ollama pull phi4` |

### 2.3 专家专用模型配置

为不同专家配置最适合的模型：

```yaml
# config.yaml 扩展
experts:
  mental_health:
    name: "心理咨询师"
    model: "qwen2.5:14b"     # 需要更多同理心和细腻表达
    temperature: 0.4         # 稍高温度增加表达多样性

  nutrition:
    name: "营养师"
    model: "qwen2.5:7b"      # 营养建议相对结构化
    temperature: 0.2         # 低温度保证准确性

  sports_rehab:
    name: "运动康复师"
    model: "qwen2.5:7b"      # 运动处方较为固定
    temperature: 0.2

  tcm_wellness:
    name: "中医养生师"
    model: "qwen2.5:14b"     # 中医理论需要更强推理
    temperature: 0.3
```

---

## 三、代码整合实现

### 3.1 创建模型管理器

创建 `core/model_manager.py`：

```python
# -*- coding: utf-8 -*-
"""
model_manager.py - Ollama 本地模型管理器

功能:
1. 模型池管理 - 按需加载/卸载模型
2. 智能路由 - 根据任务复杂度选择模型
3. 健康检查 - 自动检测 Ollama 服务状态
4. 降级策略 - 模型不可用时自动降级
"""

import httpx
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding


class ModelTier(Enum):
    """模型层级"""
    FAST = "fast"           # 快速响应
    STANDARD = "standard"   # 标准对话
    HEAVY = "heavy"         # 重度推理
    REASONING = "reasoning" # 推理增强


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    tier: ModelTier
    temperature: float = 0.3
    request_timeout: float = 300.0
    context_window: int = 4096


class OllamaModelManager:
    """Ollama 模型管理器"""

    # 默认模型配置
    DEFAULT_MODELS = {
        ModelTier.FAST: ModelConfig("qwen2.5:7b", ModelTier.FAST, 0.2, 120.0),
        ModelTier.STANDARD: ModelConfig("qwen2.5:14b", ModelTier.STANDARD, 0.3, 300.0),
        ModelTier.HEAVY: ModelConfig("qwen2.5:32b", ModelTier.HEAVY, 0.3, 600.0),
        ModelTier.REASONING: ModelConfig("deepseek-r1:7b", ModelTier.REASONING, 0.1, 600.0),
    }

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self._llm_cache: Dict[str, Ollama] = {}
        self._available_models: List[str] = []
        self._refresh_available_models()

    def _refresh_available_models(self):
        """刷新可用模型列表"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                self._available_models = [m["name"] for m in data.get("models", [])]
        except Exception as e:
            print(f"[警告] 无法获取 Ollama 模型列表: {e}")
            self._available_models = []

    def is_ollama_running(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False

    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        if not self._available_models:
            self._refresh_available_models()
        # 支持部分匹配 (qwen2.5:14b 匹配 qwen2.5:14b-instruct-q4_0)
        return any(model_name in m for m in self._available_models)

    def get_llm(
        self,
        tier: ModelTier = ModelTier.STANDARD,
        expert_name: str = None,
        fallback: bool = True
    ) -> Optional[Ollama]:
        """
        获取指定层级的 LLM 实例

        Args:
            tier: 模型层级
            expert_name: 专家名称 (可用于专家特定配置)
            fallback: 是否启用降级策略

        Returns:
            Ollama LLM 实例
        """
        config = self.DEFAULT_MODELS.get(tier, self.DEFAULT_MODELS[ModelTier.STANDARD])

        # 检查模型可用性
        if not self.is_model_available(config.name):
            if fallback:
                # 降级策略: HEAVY → STANDARD → FAST
                fallback_order = [ModelTier.STANDARD, ModelTier.FAST]
                for fb_tier in fallback_order:
                    fb_config = self.DEFAULT_MODELS[fb_tier]
                    if self.is_model_available(fb_config.name):
                        print(f"[降级] {config.name} 不可用，使用 {fb_config.name}")
                        config = fb_config
                        break
                else:
                    print(f"[错误] 没有可用的本地模型")
                    return None
            else:
                return None

        # 使用缓存
        cache_key = f"{config.name}_{config.temperature}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = Ollama(
                model=config.name,
                base_url=self.base_url,
                temperature=config.temperature,
                request_timeout=config.request_timeout
            )

        return self._llm_cache[cache_key]

    def get_embedding(self, model_name: str = "nomic-embed-text:latest") -> Optional[OllamaEmbedding]:
        """获取嵌入模型"""
        if not self.is_model_available(model_name):
            print(f"[警告] 嵌入模型 {model_name} 不可用")
            return None

        return OllamaEmbedding(
            model_name=model_name,
            base_url=self.base_url
        )

    def select_model_for_task(self, task_complexity: str) -> ModelTier:
        """
        根据任务复杂度选择模型

        Args:
            task_complexity: "simple" | "moderate" | "complex" | "reasoning"

        Returns:
            推荐的模型层级
        """
        complexity_map = {
            "simple": ModelTier.FAST,
            "moderate": ModelTier.STANDARD,
            "complex": ModelTier.HEAVY,
            "reasoning": ModelTier.REASONING
        }
        return complexity_map.get(task_complexity, ModelTier.STANDARD)

    def list_available_models(self) -> List[str]:
        """列出所有可用模型"""
        self._refresh_available_models()
        return self._available_models

    def preload_models(self, tiers: List[ModelTier] = None):
        """预加载指定层级的模型"""
        tiers = tiers or [ModelTier.STANDARD]
        for tier in tiers:
            config = self.DEFAULT_MODELS.get(tier)
            if config and self.is_model_available(config.name):
                # 发送一个简单请求来加载模型
                try:
                    llm = self.get_llm(tier)
                    if llm:
                        llm.complete("hello")
                        print(f"[预加载] {config.name} 已加载")
                except Exception as e:
                    print(f"[预加载失败] {config.name}: {e}")


# 全局单例
_model_manager: Optional[OllamaModelManager] = None

def get_model_manager(base_url: str = "http://localhost:11434") -> OllamaModelManager:
    """获取模型管理器单例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = OllamaModelManager(base_url)
    return _model_manager
```

### 3.2 处方引擎集成推理模型

更新 `scripts/prescription_engine.py`，对复杂行为分析使用推理增强模型：

```python
# 在 generate_prescription 函数中添加
from core.model_manager import get_model_manager, ModelTier

def generate_prescription_with_reasoning(
    physio_data: Dict[str, Any],
    psych_data: Dict[str, Any],
    history: Dict[str, Any] = None,
    use_reasoning_model: bool = True
) -> Dict[str, Any]:
    """
    使用推理增强模型生成处方

    对于复杂行为模式 (隐性疲劳、多因素交织)，
    使用 deepseek-r1 等推理模型进行深度分析
    """
    # 1. 基础处方生成
    prescription = generate_prescription(physio_data, psych_data, history)

    # 2. 如果检测到复杂模式，使用推理模型增强分析
    profile = prescription.get('behavioral_profile', {})
    flags = profile.get('flags', {})

    is_complex = (
        flags.get('is_hidden_fatigue_mode') or
        flags.get('is_exhaustion_mode') or
        profile.get('analysis', {}).get('risk_level') == 'high'
    )

    if is_complex and use_reasoning_model:
        manager = get_model_manager()
        reasoning_llm = manager.get_llm(ModelTier.REASONING)

        if reasoning_llm:
            # 使用推理模型进行深度分析
            analysis_prompt = f"""
            请对以下行为健康数据进行深度分析：

            生理指标: {json.dumps(physio_data, ensure_ascii=False)}
            心理指标: {json.dumps(psych_data, ensure_ascii=False)}
            检测到的模式: {profile.get('analysis', {}).get('behavior_mode')}

            请分析:
            1. 该模式的深层原因
            2. 可能的风险演变路径
            3. 最关键的干预点
            4. 个性化调整建议

            请用 JSON 格式输出，包含 root_cause, risk_path, intervention_point, personalized_advice 字段。
            """

            try:
                result = reasoning_llm.complete(analysis_prompt)
                # 解析并添加到处方中
                prescription['deep_analysis'] = {
                    'model': 'reasoning',
                    'content': result.text
                }
            except Exception as e:
                print(f"[推理分析] 失败: {e}")

    return prescription
```

### 3.3 API 层集成

更新 `api/services.py`，使用模型管理器：

```python
from core.model_manager import get_model_manager, ModelTier

class TaskDecomposer:
    def __init__(self, config_path: str = "config.yaml"):
        # ... 现有代码 ...

        # 使用模型管理器
        self.model_manager = get_model_manager(
            model_config.get("ollama_base_url", "http://localhost:11434")
        )

        # 任务分解使用快速模型
        self.llm = self.model_manager.get_llm(ModelTier.FAST)

        # 复杂任务使用标准模型
        self.llm_standard = self.model_manager.get_llm(ModelTier.STANDARD)

    def decompose(self, advice: str, complexity: str = "moderate") -> List[Dict]:
        """
        分解建议为原子任务

        Args:
            advice: 专家建议文本
            complexity: 任务复杂度 (simple/moderate/complex)
        """
        # 根据复杂度选择模型
        tier = self.model_manager.select_model_for_task(complexity)
        llm = self.model_manager.get_llm(tier)

        if llm is None:
            return []

        # ... 后续处理 ...
```

---

## 四、ollama_models 源码的价值

您的 `ollama_models` 目录是 Ollama 的 **Go 源代码**，可以用于：

### 4.1 自定义编译

```bash
cd D:\behavioral-health-project\ollama_models

# 编译自定义 Ollama (需要 Go 环境)
go build .

# 编译带 MLX 支持的版本 (Apple Silicon)
cmake --preset MLX
cmake --build --preset MLX --parallel
```

### 4.2 创建定制 Modelfile

为行为健康场景创建专用模型：

```dockerfile
# D:\behavioral-health-project\models\Modelfile.behavioral-coach
FROM qwen2.5:14b

# 行为健康教练专用参数
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192

# 系统提示词
SYSTEM """
你是"行健行为教练"的AI健康教练，专注于行为健康促进。

核心职责:
1. 基于HRV、睡眠、情绪等生理心理指标，识别用户的行为模式
2. 运用五层次心理准备度模型评估改变意愿
3. 生成个性化的行为处方，包括任务、知识、视频推荐
4. 使用温和、专业、非评判的语气与用户沟通

沟通原则:
- 以用户为中心，尊重其当前状态
- 循序渐进，不给过大压力
- 用数据说话，但不过度解读
- 关注长期行为改变，而非短期结果
"""

# 模板格式
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""
```

创建并使用:
```bash
# 创建定制模型
ollama create behavioral-coach -f D:\behavioral-health-project\models\Modelfile.behavioral-coach

# 测试
ollama run behavioral-coach "分析一下SDNN=42ms, 压力指数41的用户状态"
```

### 4.3 更新 config.yaml 使用定制模型

```yaml
model:
  embed: "nomic-embed-text:latest"
  llm: "behavioral-coach"  # 使用定制模型
  llm_fast: "qwen2.5:7b"
  llm_reasoning: "deepseek-r1:7b"
  ollama_base_url: "http://localhost:11434"
  temperature: 0.3
  request_timeout: 600.0
```

---

## 五、快速启动命令

```bash
# 1. 确保 Ollama 服务运行
ollama serve

# 2. 安装推荐模型
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
ollama pull deepseek-r1
ollama pull nomic-embed-text

# 3. 创建定制模型 (可选)
ollama create behavioral-coach -f models/Modelfile.behavioral-coach

# 4. 验证模型列表
ollama list

# 5. 测试处方引擎
python scripts/prescription_engine.py --test hidden_fatigue --word report.docx
```

---

## 六、性能优化建议

### 6.1 模型预加载

在应用启动时预加载常用模型：

```python
# api/main.py
from core.model_manager import get_model_manager, ModelTier

@app.on_event("startup")
async def startup_event():
    manager = get_model_manager()

    # 预加载标准模型
    manager.preload_models([ModelTier.STANDARD, ModelTier.FAST])

    print("✅ Ollama 模型预加载完成")
```

### 6.2 GPU 内存管理

```bash
# 设置 Ollama 环境变量
set OLLAMA_NUM_GPU=1
set OLLAMA_GPU_MEMORY_FRACTION=0.8

# 或在 ollama serve 时指定
ollama serve --gpu-memory-fraction 0.8
```

### 6.3 并发请求优化

```bash
# 增加并发数
set OLLAMA_NUM_PARALLEL=4
set OLLAMA_MAX_LOADED_MODELS=2
```

---

## 七、监控与日志

### 7.1 添加 Ollama 健康检查端点

```python
# api/routes.py
@router.get("/api/v1/ollama/health")
async def ollama_health():
    """检查 Ollama 服务状态"""
    manager = get_model_manager()

    return {
        "status": "healthy" if manager.is_ollama_running() else "unhealthy",
        "available_models": manager.list_available_models(),
        "base_url": manager.base_url
    }
```

---

*此文档应随项目发展持续更新*
