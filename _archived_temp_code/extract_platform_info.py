"""
行健平台 — 契约注册表信息提取工具包
=======================================
用途: 从代码库和运行中的平台提取6类关键信息
运行: python extract_platform_info.py --project-root D:\behavioral-health-project
输出: 在项目根目录生成 _contract_extraction/ 文件夹，包含6个结构化JSON文件

前置条件:
  1. Python 3.10+
  2. pip install requests pyyaml  (如果还没装)
  3. 平台如果正在运行，可以额外提取运行时信息(可选)
"""

import os
import re
import sys
import json
import glob
import ast
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ═══════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════

OUTPUT_DIR_NAME = "_contract_extraction"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_output_dir(project_root):
    """创建输出目录"""
    out = Path(project_root) / OUTPUT_DIR_NAME
    out.mkdir(exist_ok=True)
    return out


def save_json(out_dir, filename, data):
    """保存JSON文件"""
    path = out_dir / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✅ 已保存: {path}")
    return path


# ═══════════════════════════════════════════════════
# 提取器 1: 数据模型 (SQLAlchemy Models)
# ═══════════════════════════════════════════════════

def extract_data_models(project_root):
    """
    扫描所有 .py 文件，提取 SQLAlchemy 模型定义
    识别: class XxxModel(Base) 或 class Xxx(db.Model) 等模式
    """
    print("\n📊 [1/6] 提取数据模型...")
    
    models = []
    model_files = []
    
    # 常见的SQLAlchemy基类模式
    base_patterns = [
        r'class\s+(\w+)\s*\(\s*(?:Base|db\.Model|DeclarativeBase|SQLModel)\s*\)',
        r'class\s+(\w+)\s*\(\s*\w*Base\w*\s*\)',
        r'class\s+(\w+)\s*\(.*Mixin.*Base.*\)',
    ]
    
    # 字段模式
    column_pattern = re.compile(
        r'(\w+)\s*[=:]\s*(?:Column|mapped_column|Field)\s*\(\s*(\w+)'
    )
    relationship_pattern = re.compile(
        r'(\w+)\s*[=:]\s*(?:relationship|Relationship)\s*\(\s*["\'](\w+)["\']'
    )
    fk_pattern = re.compile(
        r'ForeignKey\s*\(\s*["\'](\w+\.\w+)["\']'
    )
    
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv", "venv", "migrations"]):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        for pattern in base_patterns:
            for match in re.finditer(pattern, content):
                model_name = match.group(1)
                
                # 提取该类的字段
                # 找到类定义的范围(简化: 从class到下一个class或文件末尾)
                class_start = match.start()
                next_class = re.search(r'\nclass\s+', content[class_start+10:])
                class_end = class_start + 10 + next_class.start() if next_class else len(content)
                class_body = content[class_start:class_end]
                
                # 表名
                tablename_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_body)
                tablename = tablename_match.group(1) if tablename_match else model_name.lower()
                
                # 字段
                columns = []
                for col_match in column_pattern.finditer(class_body):
                    columns.append({
                        "name": col_match.group(1),
                        "type": col_match.group(2)
                    })
                
                # 关系
                relationships = []
                for rel_match in relationship_pattern.finditer(class_body):
                    relationships.append({
                        "field": rel_match.group(1),
                        "target": rel_match.group(2)
                    })
                
                # 外键
                foreign_keys = fk_pattern.findall(class_body)
                
                rel_path = os.path.relpath(py_file, project_root)
                
                models.append({
                    "model_name": model_name,
                    "table_name": tablename,
                    "file": rel_path,
                    "columns": columns,
                    "relationships": relationships,
                    "foreign_keys": foreign_keys,
                    "column_count": len(columns)
                })
                
                if rel_path not in model_files:
                    model_files.append(rel_path)
    
    print(f"  发现 {len(models)} 个模型，分布在 {len(model_files)} 个文件中")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "total_models": len(models),
            "total_files": len(model_files),
            "model_files": model_files
        },
        "models": sorted(models, key=lambda x: x["model_name"])
    }


# ═══════════════════════════════════════════════════
# 提取器 2: API 端点
# ═══════════════════════════════════════════════════

def extract_api_endpoints(project_root):
    """
    两种方式提取API端点:
    方式A: 从运行中的平台获取 OpenAPI spec (优先)
    方式B: 从代码中扫描 FastAPI router 定义
    """
    print("\n🔌 [2/6] 提取API端点...")
    
    endpoints = []
    
    # === 方式B: 从代码扫描 ===
    # FastAPI 路由模式
    route_patterns = [
        # @router.get("/path")
        re.compile(r'@(?:router|app)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'),
        # @router.api_route("/path", methods=["GET"])
        re.compile(r'@(?:router|app)\.api_route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[([^\]]+)\]'),
    ]
    
    # 权限依赖模式
    auth_patterns = [
        re.compile(r'Depends\s*\(\s*(require_admin|require_coach_or_admin|get_current_user|require_\w+)\s*\)'),
        re.compile(r'dependencies\s*=\s*\[.*?Depends\s*\(\s*(\w+)\s*\)'),
    ]
    
    # prefix 模式
    prefix_pattern = re.compile(r'(?:APIRouter|router)\s*\(\s*(?:prefix\s*=\s*)?["\']([^"\']*)["\']')
    include_pattern = re.compile(r'include_router\s*\(\s*(\w+).*?prefix\s*=\s*["\']([^"\']+)["\']')
    
    router_files = []
    
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv", "test"]):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        if "router" not in content.lower() and "app." not in content:
            continue
            
        # 找前缀
        prefix = ""
        prefix_match = prefix_pattern.search(content)
        if prefix_match:
            prefix = prefix_match.group(1)
        
        found_routes = False
        for pattern in route_patterns:
            for match in pattern.finditer(content):
                groups = match.groups()
                if len(groups) == 2:
                    method, path = groups[0].upper(), groups[1]
                else:
                    path = groups[0]
                    methods_str = groups[1] if len(groups) > 1 else "GET"
                    method = methods_str.replace('"', '').replace("'", "").strip()
                
                # 找该端点附近的权限要求
                # 往回看50行找函数定义和依赖
                line_start = content[:match.start()].rfind('\n', 0, max(0, match.start()-2000))
                context = content[max(0,line_start):match.end()+500]
                
                auth = "unknown"
                for auth_pat in auth_patterns:
                    auth_match = auth_pat.search(context)
                    if auth_match:
                        auth = auth_match.group(1)
                        break
                
                # 找函数名
                func_match = re.search(r'(?:async\s+)?def\s+(\w+)', content[match.end():match.end()+200])
                func_name = func_match.group(1) if func_match else "unknown"
                
                full_path = prefix + path if not path.startswith(prefix) else path
                
                rel_path = os.path.relpath(py_file, project_root)
                
                endpoints.append({
                    "method": method,
                    "path": full_path,
                    "function": func_name,
                    "auth": auth,
                    "file": rel_path,
                })
                found_routes = True
        
        if found_routes:
            router_files.append(os.path.relpath(py_file, project_root))
    
    # 按模块分组
    modules = defaultdict(list)
    for ep in endpoints:
        # 从路径提取模块名: /v1/coach/messages -> coach
        parts = ep["path"].strip("/").split("/")
        module = parts[1] if len(parts) > 1 else parts[0] if parts else "root"
        modules[module].append(ep)
    
    print(f"  发现 {len(endpoints)} 个端点，{len(modules)} 个模块，{len(router_files)} 个路由文件")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "total_endpoints": len(endpoints),
            "total_modules": len(modules),
            "router_files": sorted(router_files),
            "by_method": {
                method: len([e for e in endpoints if e["method"] == method])
                for method in sorted(set(e["method"] for e in endpoints))
            },
            "by_auth": {
                auth: len([e for e in endpoints if e["auth"] == auth])
                for auth in sorted(set(e["auth"] for e in endpoints))
            }
        },
        "modules": {k: sorted(v, key=lambda x: x["path"]) for k, v in sorted(modules.items())},
        "all_endpoints": sorted(endpoints, key=lambda x: (x["path"], x["method"]))
    }


# ═══════════════════════════════════════════════════
# 提取器 3: Agent 注册表
# ═══════════════════════════════════════════════════

def extract_agent_registry(project_root):
    """
    提取所有Agent相关定义:
    - Agent类定义 (domain, keywords, priority, risk_level)
    - AGENT_DOMAIN_MAP 配置
    - 路由规则
    - 安全关键词
    """
    print("\n🤖 [3/6] 提取Agent注册表...")
    
    agents = []
    domain_maps = {}
    router_rules = []
    agent_files = []
    
    # 搜索Agent类定义
    agent_class_pattern = re.compile(
        r'class\s+(\w*Agent\w*)\s*\(\s*(\w+)\s*\)'
    )
    
    # 搜索domain定义
    domain_pattern = re.compile(r'domain\s*=\s*(?:AgentDomain\.)?(\w+)')
    keywords_pattern = re.compile(r'keywords\s*=\s*\[(.*?)\]', re.DOTALL)
    priority_pattern = re.compile(r'priority\s*=\s*(\d+)')
    weight_pattern = re.compile(r'base_weight\s*=\s*([\d.]+)')
    display_name_pattern = re.compile(r'display_name\s*=\s*["\']([^"\']+)["\']')
    
    # 搜索 AGENT_DOMAIN_MAP
    domain_map_pattern = re.compile(
        r'AGENT_DOMAIN_MAP\s*[=:]\s*\{(.*?)\}', re.DOTALL
    )
    
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv"]):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        rel_path = os.path.relpath(py_file, project_root)
        
        # Agent类
        for match in agent_class_pattern.finditer(content):
            class_name = match.group(1)
            base_class = match.group(2)
            
            # 跳过明显不是Agent的类
            if class_name in ["BaseAgent", "AbstractAgent"]:
                continue
            
            # 提取类体
            class_start = match.start()
            next_class = re.search(r'\nclass\s+', content[class_start+10:])
            class_end = class_start + 10 + next_class.start() if next_class else len(content)
            class_body = content[class_start:class_end]
            
            domain_match = domain_pattern.search(class_body)
            keywords_match = keywords_pattern.search(class_body)
            priority_match = priority_pattern.search(class_body)
            weight_match = weight_pattern.search(class_body)
            display_match = display_name_pattern.search(class_body)
            
            # 解析keywords列表
            kw_list = []
            if keywords_match:
                kw_raw = keywords_match.group(1)
                kw_list = re.findall(r'["\']([^"\']+)["\']', kw_raw)
            
            agents.append({
                "class_name": class_name,
                "base_class": base_class,
                "domain": domain_match.group(1) if domain_match else "unknown",
                "display_name": display_match.group(1) if display_match else class_name,
                "keywords": kw_list,
                "priority": int(priority_match.group(1)) if priority_match else None,
                "base_weight": float(weight_match.group(1)) if weight_match else None,
                "file": rel_path,
            })
            
            if rel_path not in agent_files:
                agent_files.append(rel_path)
        
        # AGENT_DOMAIN_MAP
        for map_match in domain_map_pattern.finditer(content):
            map_body = map_match.group(1)
            for line in map_body.split("\n"):
                kv = re.match(r'\s*["\'](\w+)["\']\s*:\s*\[(.*?)\]', line)
                if kv:
                    domain = kv.group(1)
                    related = re.findall(r'["\'](\w+)["\']', kv.group(2))
                    domain_maps[domain] = related
    
    # 搜索 AgentDomain 枚举定义
    enum_values = []
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if "__pycache__" in py_file:
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        enum_match = re.search(r'class\s+AgentDomain\s*\(.*?\):(.*?)(?=\nclass|\Z)', content, re.DOTALL)
        if enum_match:
            for val_match in re.finditer(r'(\w+)\s*=\s*["\'](\w+)["\']', enum_match.group(1)):
                enum_values.append({
                    "enum_name": val_match.group(1),
                    "value": val_match.group(2)
                })
    
    print(f"  发现 {len(agents)} 个Agent类，{len(domain_maps)} 个领域映射，{len(enum_values)} 个枚举值")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "total_agents": len(agents),
            "total_domains": len(domain_maps),
            "agent_files": sorted(agent_files),
            "enum_values": enum_values,
        },
        "agents": sorted(agents, key=lambda x: x.get("priority") or 99),
        "domain_map": domain_maps,
    }


# ═══════════════════════════════════════════════════
# 提取器 4: 配置文件
# ═══════════════════════════════════════════════════

def extract_config_files(project_root):
    """
    提取所有JSON/YAML配置文件的内容
    重点: point_events, milestones, badges, credit_requirements, 门户配置等
    """
    print("\n⚙️ [4/6] 提取配置文件...")
    
    configs = {}
    
    # 搜索关键配置文件
    config_patterns = [
        "**/*point*event*.json",
        "**/*milestone*.json",
        "**/*badge*.json",
        "**/*credit*.json",
        "**/*portal*.json",
        "**/*portal*.py",   # 有时配置在py dict里
        "**/*config*.json",
        "**/*config*.yaml",
        "**/*config*.yml",
        "**/*settings*.json",
        "**/*settings*.yaml",
        "**/configs/**/*.json",
        "**/config/**/*.json",
        "**/.env.example",
    ]
    
    found_files = set()
    for pattern in config_patterns:
        for f in glob.glob(str(Path(project_root) / pattern), recursive=True):
            if any(skip in f for skip in ["__pycache__", "node_modules", ".venv", "package"]):
                continue
            found_files.add(f)
    
    for filepath in sorted(found_files):
        rel_path = os.path.relpath(filepath, project_root)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # 尝试解析JSON
            if filepath.endswith(".json"):
                try:
                    data = json.loads(content)
                    configs[rel_path] = {
                        "type": "json",
                        "size_bytes": len(content),
                        "content": data
                    }
                except json.JSONDecodeError:
                    configs[rel_path] = {
                        "type": "json_invalid",
                        "size_bytes": len(content),
                        "preview": content[:500]
                    }
            elif filepath.endswith((".yaml", ".yml")):
                configs[rel_path] = {
                    "type": "yaml",
                    "size_bytes": len(content),
                    "content_raw": content[:3000]  # YAML 原样保留
                }
            else:
                configs[rel_path] = {
                    "type": "text",
                    "size_bytes": len(content),
                    "preview": content[:2000]
                }
        except Exception as e:
            configs[rel_path] = {"type": "error", "error": str(e)}
    
    # 额外: 扫描Python文件中的内联配置字典
    inline_configs = {}
    important_dicts = [
        "PORTAL_CONFIGS", "POINT_EVENTS", "MILESTONES", "BADGES",
        "CREDIT_REQUIREMENTS", "ROLE_PERMISSIONS", "PROMOTION_THRESHOLDS",
        "SERVICE_TIERS", "AGENT_PRIORITIES", "SAFETY_RULES",
    ]
    
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv"]):
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        for dict_name in important_dicts:
            pattern = re.compile(rf'{dict_name}\s*[=:]\s*\{{', re.IGNORECASE)
            match = pattern.search(content)
            if match:
                # 尝试提取字典范围(简化：取后2000字符)
                start = match.start()
                snippet = content[start:start+3000]
                rel_path = os.path.relpath(py_file, project_root)
                inline_configs[f"{rel_path}::{dict_name}"] = {
                    "file": rel_path,
                    "variable": dict_name,
                    "preview": snippet[:2000]
                }
    
    print(f"  发现 {len(configs)} 个配置文件，{len(inline_configs)} 个内联配置字典")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "total_config_files": len(configs),
            "total_inline_configs": len(inline_configs),
            "config_files": sorted(configs.keys()),
            "inline_config_locations": sorted(inline_configs.keys()),
        },
        "config_files": configs,
        "inline_configs": inline_configs,
    }


# ═══════════════════════════════════════════════════
# 提取器 5: 多租户架构
# ═══════════════════════════════════════════════════

def extract_tenant_architecture(project_root):
    """
    提取多租户相关的代码结构:
    - Tenant模型定义
    - 租户隔离逻辑
    - RBAC 角色定义
    """
    print("\n🏢 [5/6] 提取多租户架构...")
    
    tenant_info = {
        "models": [],
        "isolation_patterns": [],
        "rbac_definitions": [],
        "tenant_files": [],
    }
    
    # 搜索 tenant 相关文件
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv"]):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        rel_path = os.path.relpath(py_file, project_root)
        
        # tenant_id 过滤模式
        tenant_filter = re.findall(r'tenant_id\s*==?\s*[:\w.]+', content)
        if tenant_filter:
            tenant_info["isolation_patterns"].append({
                "file": rel_path,
                "patterns": list(set(tenant_filter))[:10]
            })
        
        # RBAC 角色定义
        role_patterns = [
            re.compile(r'class\s+(\w*Role\w*)\s*\('),
            re.compile(r'(?:ROLES|ROLE_LEVELS|ROLE_PERMISSIONS)\s*=\s*\{'),
            re.compile(r'role_level\s*[><=]+\s*\d+'),
        ]
        
        for rp in role_patterns:
            matches = rp.findall(content)
            if matches:
                tenant_info["rbac_definitions"].append({
                    "file": rel_path,
                    "matches": matches[:10] if isinstance(matches[0], str) else [str(m) for m in matches[:10]]
                })
        
        # Tenant 模型
        if re.search(r'class\s+\w*[Tt]enant\w*\s*\(', content):
            tenant_info["tenant_files"].append(rel_path)
            # 提取该文件的完整内容(通常不大)
            tenant_info["models"].append({
                "file": rel_path,
                "content": content[:5000]
            })
    
    # 搜索权限检查函数
    auth_functions = []
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if "__pycache__" in py_file:
            continue
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        for match in re.finditer(r'(?:async\s+)?def\s+(require_\w+|check_\w*perm\w*|get_current_user)\s*\(', content):
            func_name = match.group(1)
            # 提取函数体(简化)
            func_start = match.start()
            func_body = content[func_start:func_start+1000]
            auth_functions.append({
                "function": func_name,
                "file": os.path.relpath(py_file, project_root),
                "preview": func_body[:500]
            })
    
    tenant_info["auth_functions"] = auth_functions
    
    print(f"  发现 {len(tenant_info['tenant_files'])} 个租户文件，"
          f"{len(tenant_info['isolation_patterns'])} 个隔离模式，"
          f"{len(auth_functions)} 个权限函数")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "tenant_files": tenant_info["tenant_files"],
            "isolation_pattern_count": len(tenant_info["isolation_patterns"]),
            "auth_function_count": len(auth_functions),
        },
        **tenant_info
    }


# ═══════════════════════════════════════════════════
# 提取器 6: 安全管道
# ═══════════════════════════════════════════════════

def extract_safety_pipeline(project_root):
    """
    提取安全管道相关代码:
    - Safety Pipeline 规则
    - PolicyGate 规则
    - 危机干预关键词
    - 内容审核逻辑
    """
    print("\n🛡️ [6/6] 提取安全管道...")
    
    safety_info = {
        "pipeline_files": [],
        "crisis_keywords": [],
        "policy_rules": [],
        "safety_configs": [],
    }
    
    safety_keywords = [
        "safety", "crisis", "policy_gate", "policygate", "content_filter",
        "risk_level", "RiskLevel", "CRISIS", "intervention", "escalat"
    ]
    
    for py_file in glob.glob(str(Path(project_root) / "**" / "*.py"), recursive=True):
        if any(skip in py_file for skip in ["__pycache__", "node_modules", ".venv"]):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        
        rel_path = os.path.relpath(py_file, project_root)
        
        # 检查是否包含安全相关内容
        relevance_score = sum(1 for kw in safety_keywords if kw.lower() in content.lower())
        
        if relevance_score >= 2:
            safety_info["pipeline_files"].append({
                "file": rel_path,
                "relevance_score": relevance_score,
                "size": len(content),
            })
            
            # 提取危机关键词列表
            kw_matches = re.findall(
                r'(?:CRISIS_KEYWORDS|CRITICAL_KW|WARNING_KW|危机|自杀|自残)\s*=\s*\[(.*?)\]',
                content, re.DOTALL
            )
            for km in kw_matches:
                keywords = re.findall(r'["\']([^"\']+)["\']', km)
                if keywords:
                    safety_info["crisis_keywords"].extend(keywords)
            
            # 提取PolicyGate/Safety规则
            rule_matches = re.findall(
                r'(?:POLICY_RULES|SAFETY_RULES|GATE_RULES)\s*=\s*[\[{](.*?)[\]}]',
                content, re.DOTALL
            )
            for rm in rule_matches:
                safety_info["policy_rules"].append({
                    "file": rel_path,
                    "content": rm[:2000]
                })
            
            # RiskLevel 枚举
            risk_enum = re.search(r'class\s+RiskLevel\s*\(.*?\):(.*?)(?=\nclass|\Z)', content, re.DOTALL)
            if risk_enum:
                safety_info["risk_levels"] = re.findall(
                    r'(\w+)\s*=\s*["\']?(\w+)["\']?',
                    risk_enum.group(1)
                )
    
    # 去重关键词
    safety_info["crisis_keywords"] = sorted(set(safety_info["crisis_keywords"]))
    
    # 按相关度排序
    safety_info["pipeline_files"] = sorted(
        safety_info["pipeline_files"],
        key=lambda x: x["relevance_score"],
        reverse=True
    )
    
    print(f"  发现 {len(safety_info['pipeline_files'])} 个安全相关文件，"
          f"{len(safety_info['crisis_keywords'])} 个危机关键词")
    
    return {
        "extraction_time": TIMESTAMP,
        "summary": {
            "total_safety_files": len(safety_info["pipeline_files"]),
            "crisis_keyword_count": len(safety_info["crisis_keywords"]),
            "policy_rule_count": len(safety_info["policy_rules"]),
        },
        **safety_info
    }


# ═══════════════════════════════════════════════════
# 额外: 运行时提取 (如果平台正在运行)
# ═══════════════════════════════════════════════════

def extract_runtime_info(base_url="http://localhost:8000"):
    """
    从运行中的平台提取运行时信息(可选)
    """
    print(f"\n🌐 [附加] 尝试从运行中的平台提取 ({base_url})...")
    
    runtime = {"available": False}
    
    try:
        import requests
        
        # OpenAPI spec
        try:
            resp = requests.get(f"{base_url}/openapi.json", timeout=5)
            if resp.status_code == 200:
                spec = resp.json()
                runtime["openapi"] = {
                    "title": spec.get("info", {}).get("title"),
                    "version": spec.get("info", {}).get("version"),
                    "total_paths": len(spec.get("paths", {})),
                    "paths": list(spec.get("paths", {}).keys()),
                }
                runtime["available"] = True
                print(f"  ✅ OpenAPI: {runtime['openapi']['total_paths']} 个路径")
        except:
            print(f"  ⚠️ 无法获取 OpenAPI spec")
        
        # 健康检查
        for health_path in ["/health", "/api/health", "/api/v1/health"]:
            try:
                resp = requests.get(f"{base_url}{health_path}", timeout=3)
                if resp.status_code == 200:
                    runtime["health"] = resp.json()
                    print(f"  ✅ 健康检查: {health_path}")
                    break
            except:
                continue
        
    except ImportError:
        print(f"  ⚠️ requests 未安装，跳过运行时提取 (pip install requests)")
    except Exception as e:
        print(f"  ⚠️ 无法连接平台: {e}")
    
    return runtime


# ═══════════════════════════════════════════════════
# 项目结构概览
# ═══════════════════════════════════════════════════

def extract_project_structure(project_root, max_depth=3):
    """提取项目目录结构"""
    print("\n📁 [附加] 提取项目结构...")
    
    structure = {"dirs": [], "py_files": 0, "js_files": 0, "json_files": 0, "total_files": 0}
    
    skip_dirs = {"__pycache__", "node_modules", ".venv", "venv", ".git", 
                 ".next", "dist", "build", ".tox", ".pytest_cache"}
    
    for root, dirs, files in os.walk(project_root):
        # 过滤
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        
        depth = root.replace(str(project_root), "").count(os.sep)
        if depth > max_depth:
            dirs.clear()
            continue
        
        rel_root = os.path.relpath(root, project_root)
        if rel_root == ".":
            rel_root = ""
        
        file_summary = {}
        for f in files:
            ext = Path(f).suffix.lower()
            file_summary[ext] = file_summary.get(ext, 0) + 1
            structure["total_files"] += 1
            if ext == ".py": structure["py_files"] += 1
            elif ext in (".js", ".jsx", ".ts", ".tsx", ".vue"): structure["js_files"] += 1
            elif ext == ".json": structure["json_files"] += 1
        
        if file_summary:
            structure["dirs"].append({
                "path": rel_root or ".",
                "depth": depth,
                "subdirs": [d for d in dirs],
                "files": file_summary,
            })
    
    print(f"  项目共 {structure['total_files']} 个文件 "
          f"(Python: {structure['py_files']}, "
          f"JS/Vue: {structure['js_files']}, "
          f"JSON: {structure['json_files']})")
    
    return structure


# ═══════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="行健平台契约注册表信息提取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python extract_platform_info.py --project-root D:\\behavioral-health-project
  python extract_platform_info.py --project-root D:\\behavioral-health-project --api-url http://localhost:8000
        """
    )
    parser.add_argument("--project-root", "-p", required=True, help="项目根目录路径")
    parser.add_argument("--api-url", "-u", default=None, help="运行中平台的URL(可选)")
    parser.add_argument("--skip-runtime", action="store_true", help="跳过运行时提取")
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ 项目目录不存在: {project_root}")
        sys.exit(1)
    
    print("=" * 60)
    print("  行健平台 — 契约注册表信息提取工具")
    print(f"  项目根目录: {project_root}")
    print(f"  提取时间: {TIMESTAMP}")
    print("=" * 60)
    
    out_dir = ensure_output_dir(project_root)
    print(f"\n输出目录: {out_dir}")
    
    # 项目结构
    structure = extract_project_structure(project_root)
    save_json(out_dir, "0_project_structure.json", structure)
    
    # 6 类提取
    models = extract_data_models(project_root)
    save_json(out_dir, "1_data_models.json", models)
    
    endpoints = extract_api_endpoints(project_root)
    save_json(out_dir, "2_api_endpoints.json", endpoints)
    
    agents = extract_agent_registry(project_root)
    save_json(out_dir, "3_agent_registry.json", agents)
    
    configs = extract_config_files(project_root)
    save_json(out_dir, "4_config_files.json", configs)
    
    tenant = extract_tenant_architecture(project_root)
    save_json(out_dir, "5_tenant_architecture.json", tenant)
    
    safety = extract_safety_pipeline(project_root)
    save_json(out_dir, "6_safety_pipeline.json", safety)
    
    # 运行时(可选)
    if not args.skip_runtime:
        api_url = args.api_url or "http://localhost:8000"
        runtime = extract_runtime_info(api_url)
        save_json(out_dir, "7_runtime_info.json", runtime)
    
    # 生成汇总报告
    summary = {
        "extraction_time": TIMESTAMP,
        "project_root": str(project_root),
        "totals": {
            "data_models": models["summary"]["total_models"],
            "api_endpoints": endpoints["summary"]["total_endpoints"],
            "api_modules": endpoints["summary"]["total_modules"],
            "agents": agents["summary"]["total_agents"],
            "agent_domains": agents["summary"]["total_domains"],
            "config_files": configs["summary"]["total_config_files"],
            "inline_configs": configs["summary"]["total_inline_configs"],
            "tenant_files": len(tenant["summary"]["tenant_files"]),
            "auth_functions": tenant["summary"]["auth_function_count"],
            "safety_files": safety["summary"]["total_safety_files"],
            "crisis_keywords": safety["summary"]["crisis_keyword_count"],
        },
        "output_files": [
            "0_project_structure.json — 项目目录结构",
            "1_data_models.json — SQLAlchemy 数据模型",
            "2_api_endpoints.json — API 端点清单",
            "3_agent_registry.json — Agent 注册表",
            "4_config_files.json — 配置文件内容",
            "5_tenant_architecture.json — 多租户架构",
            "6_safety_pipeline.json — 安全管道",
            "7_runtime_info.json — 运行时信息(如果可用)",
        ],
        "next_steps": [
            "将 _contract_extraction/ 文件夹整体发送给Claude",
            "Claude将基于这些数据生成契约注册表草稿",
            "标注「已确认」「待确认」「待决策」三种状态",
            "团队Review后逐步确认，形成正式版契约注册表",
        ]
    }
    save_json(out_dir, "SUMMARY.json", summary)
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("  ✅ 提取完成！汇总如下：")
    print("=" * 60)
    for k, v in summary["totals"].items():
        print(f"  {k}: {v}")
    print(f"\n  📂 输出目录: {out_dir}")
    print(f"  📄 共 {len(list(out_dir.glob('*.json')))} 个文件")
    print("\n  下一步: 将整个 _contract_extraction/ 文件夹的内容")
    print("  上传到Claude对话中，即可生成契约注册表草稿。")
    print("=" * 60)


if __name__ == "__main__":
    main()
