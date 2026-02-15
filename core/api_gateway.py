# -*- coding: utf-8 -*-
"""
api_gateway.py — API 网关配置与中间件

统一 API 网关层，负责:
  - 请求路由与负载均衡
  - 认证鉴权 (JWT + API Key)
  - 速率限制 (per-user / per-tenant)
  - 请求日志与指标采集
  - nginx_proxy 反向代理配置生成

部署方式:
  - 生产: Kong / APISIX + 外部负载均衡
  - 开发: nginx_proxy + FastAPI 内置中间件
"""

import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 网关配置 (gateway_config)
# ══════════════════════════════════════════════════════════════

gateway_config: Dict[str, Any] = {
    "provider": os.getenv("API_GATEWAY_PROVIDER", "builtin"),
    "routes": {
        "/api/v1": {"upstream": "http://bhp-api:8000", "strip_prefix": False},
        "/admin": {"upstream": "http://bhp-admin-portal:5174", "strip_prefix": False},
        "/h5": {"upstream": "http://bhp-h5:5173", "strip_prefix": False},
    },
    "rate_limits": {
        "default_rpm": 200,
        "per_user_rpm": 100,
        "per_tenant_rpm": 1000,
    },
    "cors": {
        "allow_origins": ["*"],
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    },
}


def get_api_gateway_config() -> Dict[str, Any]:
    """获取当前 api_gateway 配置"""
    return gateway_config


def generate_nginx_proxy_config(routes: Dict[str, Dict] = None) -> str:
    """生成 nginx_proxy 反向代理配置

    用于开发/测试环境的 nginx 配置生成。
    """
    routes = routes or gateway_config["routes"]
    locations = []
    for path, cfg in routes.items():
        upstream = cfg["upstream"]
        locations.append(f"""
    location {path} {{
        proxy_pass {upstream};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}""")

    config = f"""# Auto-generated nginx_proxy config for api_gateway
server {{
    listen 80;
    server_name _;
{"".join(locations)}
}}"""
    logger.info("nginx_proxy config generated for api_gateway: %d routes", len(routes))
    return config
