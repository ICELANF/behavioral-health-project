"""
Agent 模板服务 — 从 DB 加载 Agent 模板, 构建 Agent 实例
核心原则: DB 不可用时 100% 回退到硬编码
"""
from __future__ import annotations
import logging
import copy
from typing import Optional

logger = logging.getLogger(__name__)

# ── 模块级缓存 ──
_template_cache: dict[str, dict] = {}
_cache_loaded: bool = False


def load_templates(db) -> dict[str, dict]:
    """从 DB 加载所有 enabled 模板, 写入缓存"""
    global _template_cache, _cache_loaded
    try:
        from core.models import AgentTemplate
        rows = db.query(AgentTemplate).filter(
            AgentTemplate.is_enabled == True  # noqa: E712
        ).all()

        templates = {}
        for row in rows:
            templates[row.agent_id] = {
                "agent_id": row.agent_id,
                "display_name": row.display_name,
                "agent_type": row.agent_type,
                "domain_enum": row.domain_enum,
                "description": row.description,
                "keywords": row.keywords or [],
                "data_fields": row.data_fields or [],
                "correlations": row.correlations or [],
                "priority": row.priority if row.priority is not None else 5,
                "base_weight": row.base_weight if row.base_weight is not None else 0.8,
                "enable_llm": row.enable_llm if row.enable_llm is not None else True,
                "system_prompt": row.system_prompt or "",
                "conflict_wins_over": row.conflict_wins_over or [],
                "is_preset": row.is_preset,
                "is_enabled": row.is_enabled,
            }

        _template_cache = templates
        _cache_loaded = True
        logger.info("Agent 模板缓存已加载: %d 个模板", len(templates))
        return templates

    except Exception as e:
        logger.warning("Agent 模板加载失败 (将使用硬编码): %s", e)
        return {}


def get_cached_templates() -> dict[str, dict]:
    """返回缓存副本"""
    return copy.deepcopy(_template_cache)


def is_cache_loaded() -> bool:
    """检查缓存是否已加载"""
    return _cache_loaded


def invalidate_cache() -> None:
    """清空缓存"""
    global _template_cache, _cache_loaded
    _template_cache = {}
    _cache_loaded = False
    logger.info("Agent 模板缓存已清空")


def build_agents_from_templates(db) -> Optional[dict]:
    """
    核心: 从模板构建 Agent 实例字典

    - 预置 Agent → AGENT_CLASS_REGISTRY[agent_id]() + 覆盖属性
    - 动态 Agent → GenericLLMAgent(template)
    - DB 失败 → 返回 None (触发调用方降级)
    """
    try:
        # 确保缓存已加载
        if not _cache_loaded:
            templates = load_templates(db)
        else:
            templates = _template_cache

        if not templates:
            return None

        from core.agents.base import AGENT_CLASS_REGISTRY
        from core.agents.generic_llm_agent import GenericLLMAgent

        # 确保注册表已填充 (触发模块导入)
        if not AGENT_CLASS_REGISTRY:
            import core.agents.specialist_agents  # noqa: F401
            import core.agents.integrative_agents  # noqa: F401

        agents = {}
        for agent_id, tpl in templates.items():
            agent_type = tpl.get("agent_type", "specialist")

            if agent_type in ("specialist", "integrative"):
                # 预置 Agent: 从注册表实例化
                cls = AGENT_CLASS_REGISTRY.get(agent_id)
                if cls:
                    instance = cls()
                    # 从模板覆盖可配置属性
                    instance.keywords = tpl.get("keywords", instance.keywords)
                    instance.data_fields = tpl.get("data_fields", instance.data_fields)
                    instance.priority = tpl.get("priority", instance.priority)
                    instance.base_weight = tpl.get("base_weight", instance.base_weight)
                    instance.enable_llm = tpl.get("enable_llm", instance.enable_llm)
                    if tpl.get("system_prompt"):
                        instance._template_system_prompt = tpl["system_prompt"]
                    agents[agent_id] = instance
                else:
                    # 注册表中找不到 → 作为 GenericLLMAgent
                    logger.warning("预置 Agent '%s' 未在注册表中找到, 降级为 GenericLLMAgent", agent_id)
                    agents[agent_id] = GenericLLMAgent(tpl)
            elif agent_type == "dynamic_llm":
                # 动态 Agent: 纯 LLM
                agents[agent_id] = GenericLLMAgent(tpl)
            else:
                logger.warning("未知 agent_type '%s' for '%s', 跳过", agent_type, agent_id)

        logger.info("从模板构建了 %d 个 Agent 实例", len(agents))
        return agents if agents else None

    except Exception as e:
        logger.warning("从模板构建 Agent 失败 (将使用硬编码): %s", e)
        return None


def build_correlations_from_templates() -> Optional[dict[str, list[str]]]:
    """从缓存模板构建领域关联网络"""
    if not _cache_loaded or not _template_cache:
        return None

    correlations = {}
    for agent_id, tpl in _template_cache.items():
        corr = tpl.get("correlations", [])
        if corr:
            correlations[agent_id] = corr

    return correlations if correlations else None


def build_conflict_priority_from_templates() -> Optional[dict[tuple[str, str], str]]:
    """从缓存模板构建冲突消解优先级"""
    if not _cache_loaded or not _template_cache:
        return None

    conflicts = {}
    for agent_id, tpl in _template_cache.items():
        wins_over = tpl.get("conflict_wins_over", [])
        for loser in wins_over:
            key = tuple(sorted((agent_id, loser)))
            conflicts[key] = agent_id

    return conflicts if conflicts else None
