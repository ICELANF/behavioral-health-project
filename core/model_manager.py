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

try:
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.ollama import OllamaEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    Ollama = None
    OllamaEmbedding = None


class ModelTier(Enum):
    """模型层级"""
    FAST = "fast"           # 快速响应 (7B 级别)
    STANDARD = "standard"   # 标准对话 (14B 级别)
    HEAVY = "heavy"         # 重度推理 (32B+ 级别)
    REASONING = "reasoning" # 推理增强 (DeepSeek-R1 等)


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    tier: ModelTier
    temperature: float = 0.3
    request_timeout: float = 300.0
    context_window: int = 4096
    description: str = ""


class OllamaModelManager:
    """
    Ollama 模型管理器

    功能:
    - 管理多个本地模型
    - 智能选择模型 (根据任务复杂度)
    - 自动降级 (模型不可用时)
    - 健康检查
    """

    # 默认模型配置
    DEFAULT_MODELS = {
        ModelTier.FAST: ModelConfig(
            name="qwen2.5:0.5b",
            tier=ModelTier.FAST,
            temperature=0.2,
            request_timeout=120.0,
            description="快速响应，适用于简单对话和意图识别"
        ),
        ModelTier.STANDARD: ModelConfig(
            name="qwen2.5:0.5b",
            tier=ModelTier.STANDARD,
            temperature=0.3,
            request_timeout=300.0,
            description="标准模型，适用于专家对话和建议生成"
        ),
        ModelTier.HEAVY: ModelConfig(
            name="qwen2.5:32b",
            tier=ModelTier.HEAVY,
            temperature=0.3,
            request_timeout=600.0,
            description="重量级模型，适用于复杂多专家综合"
        ),
        ModelTier.REASONING: ModelConfig(
            name="deepseek-r1:7b",
            tier=ModelTier.REASONING,
            temperature=0.1,
            request_timeout=600.0,
            description="推理增强模型，适用于行为模式深度分析"
        ),
    }

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        初始化模型管理器

        Args:
            base_url: Ollama 服务地址
        """
        self.base_url = base_url
        self._llm_cache: Dict[str, 'Ollama'] = {}
        self._embed_cache: Dict[str, 'OllamaEmbedding'] = {}
        self._available_models: List[str] = []
        self._refresh_available_models()

    def _refresh_available_models(self):
        """刷新可用模型列表"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                self._available_models = [m["name"] for m in data.get("models", [])]
                print(f"[ModelManager] 发现 {len(self._available_models)} 个本地模型")
        except Exception as e:
            print(f"[ModelManager] 无法获取 Ollama 模型列表: {e}")
            self._available_models = []

    def is_ollama_running(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False

    def is_model_available(self, model_name: str) -> bool:
        """
        检查模型是否可用

        Args:
            model_name: 模型名称 (支持部分匹配)

        Returns:
            是否可用
        """
        if not self._available_models:
            self._refresh_available_models()

        # 支持部分匹配 (qwen2.5:0.5b 匹配 qwen2.5:0.5b-instruct-q4_0)
        return any(model_name in m or m in model_name for m in self._available_models)

    def get_llm(
        self,
        tier: ModelTier = ModelTier.STANDARD,
        expert_name: str = None,
        fallback: bool = True,
        custom_temperature: float = None
    ) -> Optional['Ollama']:
        """
        获取指定层级的 LLM 实例

        Args:
            tier: 模型层级
            expert_name: 专家名称 (可用于专家特定配置)
            fallback: 是否启用降级策略
            custom_temperature: 自定义温度

        Returns:
            Ollama LLM 实例，失败返回 None
        """
        if not LLAMAINDEX_AVAILABLE:
            print("[ModelManager] 错误: llama_index 未安装")
            return None

        config = self.DEFAULT_MODELS.get(tier, self.DEFAULT_MODELS[ModelTier.STANDARD])

        # 检查模型可用性
        if not self.is_model_available(config.name):
            if fallback:
                # 降级策略: HEAVY → STANDARD → FAST
                fallback_order = [ModelTier.STANDARD, ModelTier.FAST]
                for fb_tier in fallback_order:
                    fb_config = self.DEFAULT_MODELS[fb_tier]
                    if self.is_model_available(fb_config.name):
                        print(f"[ModelManager] 降级: {config.name} 不可用，使用 {fb_config.name}")
                        config = fb_config
                        break
                else:
                    print(f"[ModelManager] 错误: 没有可用的本地模型")
                    return None
            else:
                print(f"[ModelManager] 错误: {config.name} 不可用")
                return None

        # 确定温度
        temperature = custom_temperature if custom_temperature is not None else config.temperature

        # 使用缓存
        cache_key = f"{config.name}_{temperature}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = Ollama(
                model=config.name,
                base_url=self.base_url,
                temperature=temperature,
                request_timeout=config.request_timeout
            )
            print(f"[ModelManager] 加载模型: {config.name} (温度={temperature})")

        return self._llm_cache[cache_key]

    def get_embedding(
        self,
        model_name: str = "mxbai-embed-large:latest"
    ) -> Optional['OllamaEmbedding']:
        """
        获取嵌入模型

        Args:
            model_name: 嵌入模型名称

        Returns:
            OllamaEmbedding 实例
        """
        if not LLAMAINDEX_AVAILABLE:
            print("[ModelManager] 错误: llama_index 未安装")
            return None

        if not self.is_model_available(model_name):
            print(f"[ModelManager] 警告: 嵌入模型 {model_name} 不可用")
            return None

        if model_name not in self._embed_cache:
            self._embed_cache[model_name] = OllamaEmbedding(
                model_name=model_name,
                base_url=self.base_url
            )
            print(f"[ModelManager] 加载嵌入模型: {model_name}")

        return self._embed_cache[model_name]

    def select_model_for_task(self, task_complexity: str) -> ModelTier:
        """
        根据任务复杂度选择模型层级

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
        return complexity_map.get(task_complexity.lower(), ModelTier.STANDARD)

    def list_available_models(self) -> List[str]:
        """列出所有可用的本地模型"""
        self._refresh_available_models()
        return self._available_models

    def get_model_info(self, tier: ModelTier) -> Optional[ModelConfig]:
        """获取指定层级的模型配置信息"""
        return self.DEFAULT_MODELS.get(tier)

    def preload_models(self, tiers: List[ModelTier] = None):
        """
        预加载指定层级的模型

        Args:
            tiers: 要预加载的模型层级列表
        """
        tiers = tiers or [ModelTier.STANDARD]

        for tier in tiers:
            config = self.DEFAULT_MODELS.get(tier)
            if config and self.is_model_available(config.name):
                try:
                    llm = self.get_llm(tier, fallback=False)
                    if llm:
                        # 发送简单请求来加载模型到 GPU
                        llm.complete("hello")
                        print(f"[ModelManager] 预加载完成: {config.name}")
                except Exception as e:
                    print(f"[ModelManager] 预加载失败 {config.name}: {e}")

    def clear_cache(self):
        """清除模型缓存"""
        self._llm_cache.clear()
        self._embed_cache.clear()
        print("[ModelManager] 缓存已清除")

    def get_status(self) -> Dict:
        """获取模型管理器状态"""
        return {
            "ollama_running": self.is_ollama_running(),
            "base_url": self.base_url,
            "available_models": self.list_available_models(),
            "cached_llms": list(self._llm_cache.keys()),
            "cached_embeddings": list(self._embed_cache.keys())
        }


# ============ 全局单例 ============

_model_manager: Optional[OllamaModelManager] = None


def get_model_manager(base_url: str = "http://localhost:11434") -> OllamaModelManager:
    """
    获取模型管理器单例

    Args:
        base_url: Ollama 服务地址

    Returns:
        OllamaModelManager 单例实例
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = OllamaModelManager(base_url)
    return _model_manager


def reset_model_manager():
    """重置模型管理器 (用于测试)"""
    global _model_manager
    if _model_manager:
        _model_manager.clear_cache()
    _model_manager = None


# ============ 便捷函数 ============

def quick_llm(complexity: str = "moderate") -> Optional['Ollama']:
    """
    快速获取 LLM (根据复杂度自动选择)

    Args:
        complexity: "simple" | "moderate" | "complex" | "reasoning"

    Returns:
        Ollama LLM 实例
    """
    manager = get_model_manager()
    tier = manager.select_model_for_task(complexity)
    return manager.get_llm(tier)


# ============ 主函数 (测试用) ============

if __name__ == "__main__":
    print("="*60)
    print("Ollama 模型管理器测试")
    print("="*60)

    manager = get_model_manager()

    # 检查 Ollama 状态
    print(f"\nOllama 运行状态: {'运行中' if manager.is_ollama_running() else '未运行'}")

    # 列出可用模型
    models = manager.list_available_models()
    print(f"\n可用模型 ({len(models)}):")
    for m in models:
        print(f"  - {m}")

    # 测试获取不同层级的 LLM
    print("\n测试模型获取:")
    for tier in ModelTier:
        config = manager.get_model_info(tier)
        available = manager.is_model_available(config.name) if config else False
        status = "✅" if available else "❌"
        print(f"  {tier.value}: {config.name if config else 'N/A'} {status}")

    # 获取状态
    print(f"\n管理器状态:")
    status = manager.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
