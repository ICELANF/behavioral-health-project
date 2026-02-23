# -*- coding: utf-8 -*-
"""
集中配置 - 从环境变量读取，提供默认值
"""

import os

# LLM 提供者: "ollama" | "dify" | "auto"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

# Dify 配置
DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost:8080/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_TIMEOUT = float(os.getenv("DIFY_TIMEOUT", "120.0"))

# Ollama 配置
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300.0"))

# 健康检查缓存时间（秒）
HEALTH_CACHE_TTL = int(os.getenv("HEALTH_CACHE_TTL", "30"))

# ── 云 LLM 配置 (V005) ──
CLOUD_LLM_PROVIDER = os.getenv("CLOUD_LLM_PROVIDER", "")          # deepseek / qwen / openai
CLOUD_LLM_API_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
CLOUD_LLM_BASE_URL = os.getenv("CLOUD_LLM_BASE_URL", "https://api.deepseek.com/v1")
CLOUD_LLM_MODEL = os.getenv("CLOUD_LLM_MODEL", "deepseek-chat")
LLM_ROUTE_STRATEGY = os.getenv("LLM_ROUTE_STRATEGY", "cloud_first")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# ── 安全模块配置 (V005) ──
SAFETY_ENABLED = os.getenv("SAFETY_ENABLED", "true").lower() in ("true", "1", "yes")
SAFETY_LOG_PII = os.getenv("SAFETY_LOG_PII", "false").lower() in ("true", "1", "yes")
SAFETY_STRICT_MODE = os.getenv("SAFETY_STRICT_MODE", "false").lower() in ("true", "1", "yes")

# ── ASR 语音识别配置 (V5.2.0) ──
ASR_PROVIDER = os.getenv("ASR_PROVIDER", "cloud_first")       # cloud_first / openai / ollama / disabled
ASR_OPENAI_API_KEY = os.getenv("ASR_OPENAI_API_KEY", "") or CLOUD_LLM_API_KEY  # 复用LLM key
ASR_OPENAI_BASE_URL = os.getenv("ASR_OPENAI_BASE_URL", "https://api.openai.com/v1")
ASR_OPENAI_MODEL = os.getenv("ASR_OPENAI_MODEL", "whisper-1")
ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "zh")                 # zh / en / auto
ASR_TIMEOUT = float(os.getenv("ASR_TIMEOUT", "60.0"))

# ── VLM 视觉模型配置 (V5.2.0) ──
VLM_PROVIDER = os.getenv("VLM_PROVIDER", "ollama_first")      # ollama_first / ollama / cloud / disabled
VLM_OLLAMA_MODEL = os.getenv("VLM_OLLAMA_MODEL", "qwen2.5vl:7b")
VLM_CLOUD_API_KEY = os.getenv("VLM_CLOUD_API_KEY", "") or CLOUD_LLM_API_KEY
VLM_CLOUD_BASE_URL = os.getenv("VLM_CLOUD_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
VLM_CLOUD_MODEL = os.getenv("VLM_CLOUD_MODEL", "qwen-vl-plus")
VLM_TIMEOUT = float(os.getenv("VLM_TIMEOUT", "120.0"))
