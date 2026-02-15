#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BehaviorOS 契约提取脚本 V2.0 (Enhanced)
========================================
行健行为健康促进平台 - 全量契约提取

用途: 从代码库静态分析提取10类契约数据,供契约注册表使用
运行: python extract_platform_contracts_v2.py [project_root]
输出: _contract_extraction_v2/ 目录下11个JSON文件 + SUMMARY.json

V2.0 改进:
  1. 数据模型: 区分SQLAlchemy ORM vs Pydantic Schema, 完整字段提取
  2. API端点: 提取依赖注入链(Depends), 权限分类
  3. Agent注册表: 12域Agent + 4专家Agent分离, 路由规则提取
  4. 配置文件: 完整内容读取(修复V1.0空数据bug)
  5. 多租户: ExpertTenant完整字段, 隔离策略分析
  6. 安全管道: PolicyGate规则提取, 完整阈值配置
  7. [新增] Alembic迁移历史
  8. [新增] 前端路由与API服务映射
  9. [新增] 定时任务与事件总线
 10. [新增] Dify工作流定义

依赖: 仅Python标准库 (ast, re, json, os, pathlib)
兼容: Python 3.8+, Windows/Linux/macOS
"""

import ast
import json
import os
import re
import sys
import time
import traceback
from collections import defaultdict, OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


# ==============================================================================
# 全局配置
# ==============================================================================

# 排除目录 (不扫描)
EXCLUDE_DIRS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env',
    '.idea', '.vscode', 'dist', 'build', '.next', '.nuxt',
    'CodeBuddy', 'MyOctopusProject', 'playwright-report',
    'volumes', 'logs', 'ollama_models', 'static',
    '_contract_extraction', '_contract_extraction_v2', 'behavior_rx_v32_complete',
}

# Dify目录 (单独统计)
DIFY_DIRS = {'dify', 'dify-setup', 'dify_workflows'}

# 核心平台目录 (重点扫描)
CORE_DIRS = {
    'api', 'core', 'models', 'schemas', 'services', 'backend',
    'agents', 'behavior_rx', 'baps', 'configs', 'data',
    'integrations', 'protocols', 'quality', 'scripts',
    'alembic', 'migrations', 'workbench', 'xingjian-agent',
    'metabolic-core', 'v3',  # v3 标注为 [legacy]
    'h5', 'h5-patient-app', 'admin-portal', 'frontend',
    'helm', 'nginx', 'e2e', 'tests', 'disclosure',
    'knowledge', 'notes', 'docs',
}

VERSION = "2.1.0"


# ==============================================================================
# 工具函数
# ==============================================================================

def safe_read(filepath: str, encoding: str = 'utf-8') -> str:
    """安全读取文件内容"""
    try:
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception:
        try:
            with open(filepath, 'r', encoding='gbk', errors='replace') as f:
                return f.read()
        except Exception:
            return ""


def safe_json_read(filepath: str) -> Any:
    """安全读取JSON文件"""
    content = safe_read(filepath)
    if not content.strip():
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试去掉BOM和注释
        content = content.lstrip('\ufeff')
        # 去掉单行注释
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped.startswith('//'):
                lines.append(line)
        try:
            return json.loads('\n'.join(lines))
        except Exception:
            return None


def safe_parse_ast(filepath: str) -> Optional[ast.Module]:
    """安全解析Python AST"""
    content = safe_read(filepath)
    if not content.strip():
        return None
    try:
        return ast.parse(content, filename=filepath)
    except SyntaxError:
        return None


def normalize_path(path: str, root: str) -> str:
    """标准化为相对路径"""
    try:
        return os.path.relpath(path, root).replace('\\', '/')
    except ValueError:
        return path.replace('\\', '/')


def is_core_platform(relpath: str) -> bool:
    """判断是否属于核心平台(非Dify)"""
    parts = relpath.replace('\\', '/').split('/')
    if parts and parts[0] in DIFY_DIRS:
        return False
    return True


def walk_files(root: str, extensions: Set[str] = None,
               include_dify: bool = False) -> List[str]:
    """遍历项目文件"""
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 排除目录
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if not include_dify:
            dirnames[:] = [d for d in dirnames if d not in DIFY_DIRS]

        for fname in filenames:
            if extensions:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in extensions:
                    continue
            results.append(os.path.join(dirpath, fname))
    return results


def progress(msg: str):
    """打印进度信息"""
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ==============================================================================
# Module 0: 项目结构
# ==============================================================================

def extract_project_structure(root: str) -> Dict:
    """提取项目目录结构"""
    progress("扫描项目结构...")

    structure = {
        "root": root,
        "top_level_dirs": [],
        "file_counts": {
            "py": 0, "ts": 0, "js": 0, "vue": 0,
            "json": 0, "yaml": 0, "yml": 0, "other": 0
        },
        "core_platform_files": 0,
        "dify_files": 0,
        "directory_tree": []
    }

    # 顶层目录
    for item in sorted(os.listdir(root)):
        full = os.path.join(root, item)
        if os.path.isdir(full) and item not in EXCLUDE_DIRS and not item.startswith('.'):
            is_dify = item in DIFY_DIRS
            # 统计文件数
            count = sum(1 for _ in walk_files(full, include_dify=True))
            structure["top_level_dirs"].append({
                "name": item,
                "is_dify": is_dify,
                "file_count": count
            })

    # 统计所有文件
    for fpath in walk_files(root, include_dify=True):
        rel = normalize_path(fpath, root)
        ext = os.path.splitext(fpath)[1].lower().lstrip('.')
        if ext in structure["file_counts"]:
            structure["file_counts"][ext] += 1
        else:
            structure["file_counts"]["other"] += 1

        if is_core_platform(rel):
            structure["core_platform_files"] += 1
        else:
            structure["dify_files"] += 1

    # 目录树 (depth<=2, 核心平台)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDE_DIRS and not d.startswith('.')]
        rel = normalize_path(dirpath, root)
        depth = rel.count('/') if rel != '.' else 0
        if depth > 2:
            dirnames[:] = []
            continue
        if not is_core_platform(rel) and depth > 0:
            continue

        py_count = sum(1 for f in filenames if f.endswith('.py'))
        ts_count = sum(1 for f in filenames if f.endswith('.ts') or f.endswith('.tsx'))
        vue_count = sum(1 for f in filenames if f.endswith('.vue'))
        json_count = sum(1 for f in filenames if f.endswith('.json'))

        structure["directory_tree"].append({
            "path": rel,
            "depth": depth,
            "subdirs": sorted(dirnames),
            "py_files": py_count,
            "ts_files": ts_count,
            "vue_files": vue_count,
            "json_files": json_count,
            "total_files": len(filenames)
        })

    progress(f"项目结构: {len(structure['top_level_dirs'])}个顶层目录, "
             f"核心平台{structure['core_platform_files']}文件, "
             f"Dify {structure['dify_files']}文件")
    return structure


# ==============================================================================
# Module 1: 数据模型 (SQLAlchemy ORM vs Pydantic Schema 分离)
# ==============================================================================

class ModelExtractor:
    """数据模型提取器 - 区分ORM模型和Pydantic Schema"""

    # SQLAlchemy 类型映射
    SA_TYPES = {
        'Column', 'Integer', 'String', 'Text', 'Float', 'Boolean',
        'DateTime', 'Date', 'JSON', 'Enum', 'ForeignKey', 'BigInteger',
        'SmallInteger', 'Numeric', 'LargeBinary', 'PickleType',
        'relationship', 'backref', 'Index', 'UniqueConstraint',
    }

    # Pydantic 基类
    PYDANTIC_BASES = {
        'BaseModel', 'BaseSchema', 'BaseResponse', 'BaseRequest',
        'Schema', 'APIResponse', 'BaseConfig',
    }

    # SQLAlchemy 基类
    SA_BASES = {'Base', 'Model', 'db.Model', 'DeclarativeBase'}

    def __init__(self, root: str):
        self.root = root
        self.orm_models = []
        self.pydantic_schemas = []
        self.enums = []

    def extract_all(self) -> Dict:
        progress("提取数据模型...")
        py_files = walk_files(self.root, {'.py'})

        for fpath in py_files:
            rel = normalize_path(fpath, self.root)
            if not is_core_platform(rel):
                continue
            self._extract_file(fpath, rel)

        progress(f"数据模型: {len(self.orm_models)} ORM表, "
                 f"{len(self.pydantic_schemas)} Pydantic Schema, "
                 f"{len(self.enums)} 枚举")

        return {
            "orm_models": self.orm_models,
            "pydantic_schemas": self.pydantic_schemas,
            "enums": self.enums,
            "summary": {
                "total_orm_models": len(self.orm_models),
                "total_pydantic_schemas": len(self.pydantic_schemas),
                "total_enums": len(self.enums),
                "orm_tables": list(set(
                    m["table_name"] for m in self.orm_models if m.get("table_name")
                )),
                "files_scanned": len(py_files),
            }
        }

    def _extract_file(self, fpath: str, rel: str):
        """从单个文件提取模型"""
        content = safe_read(fpath)
        if not content.strip():
            return

        tree = safe_parse_ast(fpath)
        if tree is None:
            # 回退到正则提取
            self._regex_extract(content, rel)
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._classify_class(node, content, rel)

    def _classify_class(self, node: ast.ClassDef, content: str, rel: str):
        """分类: ORM / Pydantic / Enum"""
        bases = self._get_base_names(node)

        # 检查是否是Enum
        if any('Enum' in b for b in bases) or any('enum' in b.lower() for b in bases):
            self._extract_enum(node, content, rel)
            return

        # 检查是否有 __tablename__
        has_tablename = False
        tablename = None
        has_column = False

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        has_tablename = True
                        tablename = self._get_const_value(item.value)
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                # 检查是否有Column()调用
                value = item.value if isinstance(item, ast.Assign) else item.value
                if value and self._is_column_call(value):
                    has_column = True

        # SQLAlchemy ORM
        if has_tablename or (has_column and any(b in self.SA_BASES for b in bases)):
            self._extract_orm(node, content, rel, tablename)
        # Pydantic Schema
        elif any(b in self.PYDANTIC_BASES for b in bases) or \
             any('Model' in b and 'Base' in b for b in bases):
            self._extract_pydantic(node, content, rel)
        # 有Column但没有__tablename__ - 仍当ORM
        elif has_column:
            self._extract_orm(node, content, rel, tablename)

    def _extract_orm(self, node: ast.ClassDef, content: str, rel: str,
                     tablename: Optional[str]):
        """提取SQLAlchemy ORM模型"""
        columns = []
        relationships = []
        foreign_keys = []
        indexes = []
        constraints = []

        for item in node.body:
            # 赋值语句 (field = Column(...))
            if isinstance(item, ast.Assign) and item.targets:
                target = item.targets[0]
                name = target.id if isinstance(target, ast.Name) else None
                if name and name.startswith('_'):
                    if name == '__tablename__':
                        continue
                    if name == '__table_args__':
                        constraints.extend(
                            self._extract_table_args(item.value, content))
                        continue

                if name and item.value:
                    col_info = self._parse_column_or_relationship(
                        name, item.value, content)
                    if col_info:
                        if col_info['kind'] == 'column':
                            columns.append(col_info)
                            if col_info.get('foreign_key'):
                                foreign_keys.append({
                                    'column': name,
                                    'references': col_info['foreign_key']
                                })
                        elif col_info['kind'] == 'relationship':
                            relationships.append(col_info)

            # 类型注解赋值 (field: Mapped[int] = mapped_column(...))
            elif isinstance(item, ast.AnnAssign) and item.target:
                name = item.target.id if isinstance(
                    item.target, ast.Name) else None
                if name and item.value:
                    col_info = self._parse_column_or_relationship(
                        name, item.value, content)
                    if col_info:
                        if col_info['kind'] == 'column':
                            columns.append(col_info)
                            if col_info.get('foreign_key'):
                                foreign_keys.append({
                                    'column': name,
                                    'references': col_info['foreign_key']
                                })
                        elif col_info['kind'] == 'relationship':
                            relationships.append(col_info)
                # 如果没有值但有注解,提取Mapped类型
                elif name and item.annotation:
                    ann_info = self._parse_mapped_annotation(
                        name, item.annotation)
                    if ann_info:
                        columns.append(ann_info)

        # 提取docstring
        docstring = ast.get_docstring(node) or ""

        self.orm_models.append({
            "model_name": node.name,
            "table_name": tablename or node.name.lower(),
            "has_explicit_tablename": tablename is not None,
            "base_classes": self._get_base_names(node),
            "file": rel,
            "line": node.lineno,
            "docstring": docstring[:200] if docstring else "",
            "columns": columns,
            "relationships": relationships,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
            "constraints": constraints,
            "column_count": len(columns),
        })

    def _extract_pydantic(self, node: ast.ClassDef, content: str, rel: str):
        """提取Pydantic Schema"""
        fields = []

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and item.target:
                name = item.target.id if isinstance(
                    item.target, ast.Name) else None
                if name and not name.startswith('_'):
                    field_info = {
                        "name": name,
                        "type": self._annotation_to_str(item.annotation),
                        "has_default": item.value is not None,
                        "default": self._get_const_value(
                            item.value) if item.value else None,
                        "required": item.value is None,
                    }
                    # 检查是否有 Field(...)
                    if item.value and isinstance(item.value, ast.Call):
                        func = item.value.func
                        func_name = ""
                        if isinstance(func, ast.Name):
                            func_name = func.id
                        elif isinstance(func, ast.Attribute):
                            func_name = func.attr
                        if func_name == 'Field':
                            field_info['field_config'] = \
                                self._extract_call_kwargs(item.value)
                    fields.append(field_info)

            elif isinstance(item, ast.Assign) and item.targets:
                name = item.targets[0].id if isinstance(
                    item.targets[0], ast.Name) else None
                if name and not name.startswith('_'):
                    fields.append({
                        "name": name,
                        "type": "Any",
                        "has_default": True,
                        "default": self._get_const_value(item.value),
                        "required": False,
                    })

        # Config class
        config = {}
        for item in node.body:
            if isinstance(item, ast.ClassDef) and item.name in (
                    'Config', 'Meta', 'model_config'):
                for sub in item.body:
                    if isinstance(sub, ast.Assign) and sub.targets:
                        key = sub.targets[0].id if isinstance(
                            sub.targets[0], ast.Name) else None
                        if key:
                            config[key] = self._get_const_value(sub.value)

        docstring = ast.get_docstring(node) or ""

        self.pydantic_schemas.append({
            "schema_name": node.name,
            "base_classes": self._get_base_names(node),
            "file": rel,
            "line": node.lineno,
            "docstring": docstring[:200] if docstring else "",
            "fields": fields,
            "config": config,
            "field_count": len(fields),
        })

    def _extract_enum(self, node: ast.ClassDef, content: str, rel: str):
        """提取枚举定义"""
        members = []
        for item in node.body:
            if isinstance(item, ast.Assign) and item.targets:
                name = item.targets[0].id if isinstance(
                    item.targets[0], ast.Name) else None
                if name and not name.startswith('_'):
                    val = self._get_const_value(item.value)
                    members.append({"name": name, "value": val})

        if members:
            self.enums.append({
                "enum_name": node.name,
                "base_classes": self._get_base_names(node),
                "file": rel,
                "line": node.lineno,
                "members": members,
                "member_count": len(members),
            })

    def _parse_column_or_relationship(self, name: str, value_node,
                                       content: str) -> Optional[Dict]:
        """解析Column()/relationship()调用"""
        if not isinstance(value_node, ast.Call):
            return None

        func = value_node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name in ('Column', 'mapped_column'):
            return self._parse_column(name, value_node)
        elif func_name == 'relationship':
            return self._parse_relationship(name, value_node)
        return None

    def _parse_column(self, name: str, call_node: ast.Call) -> Dict:
        """解析Column(type, FK, nullable, default, ...)"""
        info = {
            "kind": "column",
            "name": name,
            "type": "Unknown",
            "nullable": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "default": None,
            "server_default": None,
            "foreign_key": None,
            "comment": None,
        }

        # 位置参数 - 通常是类型和ForeignKey
        for arg in call_node.args:
            if isinstance(arg, ast.Call):
                arg_func = ""
                if isinstance(arg.func, ast.Name):
                    arg_func = arg.func.id
                elif isinstance(arg.func, ast.Attribute):
                    arg_func = arg.func.attr

                if arg_func == 'ForeignKey' and arg.args:
                    fk_val = self._get_const_value(arg.args[0])
                    info["foreign_key"] = fk_val
                elif arg_func in ('String', 'VARCHAR'):
                    length = self._get_const_value(
                        arg.args[0]) if arg.args else None
                    info["type"] = f"String({length})" if length else "String"
                elif arg_func in ('Numeric', 'DECIMAL'):
                    prec = self._get_const_value(
                        arg.args[0]) if len(arg.args) > 0 else None
                    scale = self._get_const_value(
                        arg.args[1]) if len(arg.args) > 1 else None
                    info["type"] = f"Numeric({prec},{scale})" \
                        if prec else "Numeric"
                elif arg_func == 'Enum':
                    enum_args = [self._get_const_value(a) for a in arg.args]
                    info["type"] = f"Enum({','.join(str(a) for a in enum_args)})"
                else:
                    info["type"] = arg_func
            elif isinstance(arg, ast.Name):
                if arg.id in ('Integer', 'String', 'Text', 'Float', 'Boolean',
                              'DateTime', 'Date', 'JSON', 'BigInteger',
                              'SmallInteger', 'LargeBinary'):
                    info["type"] = arg.id
            elif isinstance(arg, ast.Attribute):
                info["type"] = arg.attr

        # 关键字参数
        for kw in call_node.keywords:
            if kw.arg == 'nullable':
                info["nullable"] = self._get_const_value(kw.value)
            elif kw.arg == 'primary_key':
                info["primary_key"] = self._get_const_value(kw.value)
            elif kw.arg == 'unique':
                info["unique"] = self._get_const_value(kw.value)
            elif kw.arg == 'index':
                info["index"] = self._get_const_value(kw.value)
            elif kw.arg == 'default':
                info["default"] = self._get_const_value(kw.value)
            elif kw.arg == 'server_default':
                info["server_default"] = self._get_const_value(kw.value)
            elif kw.arg == 'comment':
                info["comment"] = self._get_const_value(kw.value)
            elif kw.arg == 'name':
                # Column('actual_name', ...)
                pass

        return info

    def _parse_relationship(self, name: str, call_node: ast.Call) -> Dict:
        """解析relationship()调用"""
        info = {
            "kind": "relationship",
            "name": name,
            "target": None,
            "back_populates": None,
            "backref": None,
            "lazy": None,
            "uselist": None,
            "cascade": None,
            "foreign_keys": None,
        }

        # 第一个位置参数是目标模型
        if call_node.args:
            info["target"] = self._get_const_value(call_node.args[0])

        # 关键字参数
        for kw in call_node.keywords:
            if kw.arg in info:
                info[kw.arg] = self._get_const_value(kw.value)

        return info

    def _parse_mapped_annotation(self, name: str, annotation) -> Optional[Dict]:
        """解析 Mapped[type] 注解"""
        type_str = self._annotation_to_str(annotation)
        if 'Mapped' in type_str or 'Column' in type_str:
            return {
                "kind": "column",
                "name": name,
                "type": type_str.replace('Mapped[', '').rstrip(']'),
                "nullable": 'Optional' in type_str,
                "primary_key": False,
                "unique": False,
                "index": False,
                "default": None,
                "server_default": None,
                "foreign_key": None,
                "comment": None,
            }
        return None

    def _extract_table_args(self, value_node, content: str) -> List[Dict]:
        """提取__table_args__中的约束"""
        constraints = []
        if isinstance(value_node, ast.Tuple):
            for elt in value_node.elts:
                if isinstance(elt, ast.Call):
                    func_name = ""
                    if isinstance(elt.func, ast.Name):
                        func_name = elt.func.id
                    elif isinstance(elt.func, ast.Attribute):
                        func_name = elt.func.attr
                    args = [self._get_const_value(a) for a in elt.args]
                    constraints.append({
                        "type": func_name,
                        "args": args,
                    })
        return constraints

    def _is_column_call(self, node) -> bool:
        """检查是否是Column()调用"""
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                return func.id in ('Column', 'mapped_column')
            if isinstance(func, ast.Attribute):
                return func.attr in ('Column', 'mapped_column')
        return False

    def _get_base_names(self, node: ast.ClassDef) -> List[str]:
        """获取基类名称列表"""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._attr_to_str(base)}")
            elif isinstance(base, ast.Subscript):
                bases.append(self._annotation_to_str(base))
        return bases

    def _annotation_to_str(self, node) -> str:
        """将AST注解节点转为字符串"""
        if node is None:
            return "Any"
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return repr(node.value)
        if isinstance(node, ast.Attribute):
            return self._attr_to_str(node)
        if isinstance(node, ast.Subscript):
            base = self._annotation_to_str(node.value)
            slice_str = self._annotation_to_str(node.slice)
            return f"{base}[{slice_str}]"
        if isinstance(node, ast.Tuple):
            elts = ', '.join(self._annotation_to_str(e) for e in node.elts)
            return elts
        if isinstance(node, ast.List):
            elts = ', '.join(self._annotation_to_str(e) for e in node.elts)
            return f"[{elts}]"
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self._annotation_to_str(node.left)
            right = self._annotation_to_str(node.right)
            return f"{left} | {right}"
        return "Unknown"

    def _attr_to_str(self, node: ast.Attribute) -> str:
        """将Attribute节点转为点号路径"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))

    def _get_const_value(self, node) -> Any:
        """获取常量值"""
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in ('True', 'False', 'None'):
                return {'True': True, 'False': False, 'None': None}[node.id]
            return node.id
        if isinstance(node, ast.List):
            return [self._get_const_value(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return [self._get_const_value(e) for e in node.elts]
        if isinstance(node, ast.Dict):
            return {self._get_const_value(k): self._get_const_value(v)
                    for k, v in zip(node.keys, node.values) if k}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            val = self._get_const_value(node.operand)
            return -val if isinstance(val, (int, float)) else val
        if isinstance(node, ast.Attribute):
            return self._attr_to_str(node)
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            return f"{func_name}(...)"
        return str(type(node).__name__)

    def _extract_call_kwargs(self, call_node: ast.Call) -> Dict:
        """提取函数调用的关键字参数"""
        kwargs = {}
        for kw in call_node.keywords:
            if kw.arg:
                kwargs[kw.arg] = self._get_const_value(kw.value)
        return kwargs

    def _regex_extract(self, content: str, rel: str):
        """正则回退提取(AST失败时)"""
        # 匹配 class Foo(Base): 和 __tablename__
        class_pattern = re.compile(
            r'class\s+(\w+)\s*\(([^)]+)\)\s*:', re.MULTILINE)
        tablename_pattern = re.compile(
            r"__tablename__\s*=\s*['\"](\w+)['\"]")

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            bases = match.group(2)

            # 查找__tablename__
            class_start = match.start()
            # 找到下一个class或文件末尾
            next_class = class_pattern.search(content, match.end())
            class_body = content[class_start:
                                 next_class.start() if next_class else len(content)]

            tn_match = tablename_pattern.search(class_body)

            # 提取Column定义
            columns = []
            col_pattern = re.compile(
                r'(\w+)\s*=\s*(?:db\.)?Column\(([^)]*)\)', re.MULTILINE)
            for cm in col_pattern.finditer(class_body):
                col_name = cm.group(1)
                col_args = cm.group(2)
                col_type = col_args.split(',')[0].strip() if col_args else "Unknown"
                columns.append({
                    "kind": "column",
                    "name": col_name,
                    "type": col_type,
                    "nullable": True,
                    "primary_key": 'primary_key=True' in col_args,
                    "unique": 'unique=True' in col_args,
                    "index": 'index=True' in col_args,
                    "default": None,
                    "server_default": None,
                    "foreign_key": None,
                    "comment": None,
                })
                # 提取ForeignKey
                fk_match = re.search(
                    r"ForeignKey\(['\"]([^'\"]+)['\"]\)", col_args)
                if fk_match:
                    columns[-1]["foreign_key"] = fk_match.group(1)

            if tn_match:
                self.orm_models.append({
                    "model_name": class_name,
                    "table_name": tn_match.group(1),
                    "has_explicit_tablename": True,
                    "base_classes": [b.strip() for b in bases.split(',')],
                    "file": rel,
                    "line": content[:class_start].count('\n') + 1,
                    "docstring": "",
                    "columns": columns,
                    "relationships": [],
                    "foreign_keys": [],
                    "indexes": [],
                    "constraints": [],
                    "column_count": len(columns),
                })
            elif 'BaseModel' in bases or 'Schema' in bases:
                # Pydantic Schema (regex)
                fields = []
                field_pattern = re.compile(
                    r'(\w+)\s*:\s*([^=\n]+?)(?:\s*=\s*(.+))?$', re.MULTILINE)
                for fm in field_pattern.finditer(class_body):
                    fname = fm.group(1)
                    if fname in ('class', 'def', 'return', 'if',
                                 'self', 'Config'):
                        continue
                    fields.append({
                        "name": fname,
                        "type": fm.group(2).strip(),
                        "has_default": fm.group(3) is not None,
                        "default": fm.group(3).strip() if fm.group(3) else None,
                        "required": fm.group(3) is None,
                    })
                if fields:
                    self.pydantic_schemas.append({
                        "schema_name": class_name,
                        "base_classes": [b.strip() for b in bases.split(',')],
                        "file": rel,
                        "line": content[:class_start].count('\n') + 1,
                        "docstring": "",
                        "fields": fields,
                        "config": {},
                        "field_count": len(fields),
                    })


# ==============================================================================
# Module 2: API端点 (含依赖注入链)
# ==============================================================================

class APIExtractor:
    """FastAPI端点提取器 - 含完整权限链"""

    # HTTP方法
    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head'}

    # 已知权限依赖
    KNOWN_DEPS = {
        'get_current_user': 'authenticated',
        'get_current_active_user': 'authenticated',
        'require_admin': 'admin_only',
        'require_coach_or_admin': 'coach_or_admin',
        'require_role': 'role_required',
        'require_expert': 'expert_only',
        'get_db': 'database',
        'get_session': 'database',
    }

    def __init__(self, root: str):
        self.root = root
        self.endpoints = []
        self.routers = []

    def extract_all(self) -> Dict:
        progress("提取API端点...")
        py_files = walk_files(self.root, {'.py'})

        for fpath in py_files:
            rel = normalize_path(fpath, self.root)
            if not is_core_platform(rel):
                continue
            self._extract_file(fpath, rel)

        # 去重并按模块分组
        modules = defaultdict(list)
        for ep in self.endpoints:
            modules[ep.get('module', 'unknown')].append(ep)

        # 统计权限分布
        auth_dist = defaultdict(int)
        for ep in self.endpoints:
            auth_dist[ep.get('auth_level', 'unknown')] += 1

        progress(f"API端点: {len(self.endpoints)}个端点, "
                 f"{len(modules)}个模块, {len(self.routers)}个路由器")

        return {
            "endpoints": self.endpoints,
            "modules": dict(modules),
            "routers": self.routers,
            "summary": {
                "total_endpoints": len(self.endpoints),
                "total_modules": len(modules),
                "total_routers": len(self.routers),
                "auth_distribution": dict(auth_dist),
                "methods_distribution": dict(
                    defaultdict(int,
                                {ep['method']: 0 for ep in self.endpoints})),
            }
        }

    def _extract_file(self, fpath: str, rel: str):
        """从Python文件提取端点"""
        content = safe_read(fpath)
        if not content.strip():
            return

        # 先检查是否包含路由定义
        if not any(pat in content for pat in
                   ['@router.', '@app.', 'APIRouter', 'FastAPI']):
            return

        # 提取路由器定义 (prefix, tags)
        self._extract_routers(content, rel)

        # AST提取
        tree = safe_parse_ast(fpath)
        if tree:
            self._extract_endpoints_ast(tree, content, rel)
        else:
            self._extract_endpoints_regex(content, rel)

    def _extract_routers(self, content: str, rel: str):
        """提取APIRouter定义"""
        # router = APIRouter(prefix="/v1/xxx", tags=["xxx"])
        pattern = re.compile(
            r'(\w+)\s*=\s*APIRouter\s*\(([^)]*)\)', re.DOTALL)
        for match in pattern.finditer(content):
            var_name = match.group(1)
            args_str = match.group(2)

            prefix = ""
            tags = []
            prefix_match = re.search(
                r'prefix\s*=\s*["\']([^"\']+)["\']', args_str)
            if prefix_match:
                prefix = prefix_match.group(1)
            tags_match = re.search(
                r'tags\s*=\s*\[([^\]]+)\]', args_str)
            if tags_match:
                tags = re.findall(r'["\']([^"\']+)["\']', tags_match.group(1))

            self.routers.append({
                "variable": var_name,
                "prefix": prefix,
                "tags": tags,
                "file": rel,
            })

        # app.include_router(router, prefix=...)
        include_pattern = re.compile(
            r'\.include_router\s*\(\s*(\w+)(?:\s*,\s*prefix\s*=\s*["\']([^"\']+)["\'])?',
        )
        for match in include_pattern.finditer(content):
            # 记录路由器挂载信息
            pass

    def _extract_endpoints_ast(self, tree: ast.Module, content: str, rel: str):
        """AST提取端点"""
        # 找到文件中的路由前缀
        file_prefix = self._find_file_prefix(content)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 检查装饰器
            for deco in node.decorator_list:
                method, path = self._parse_route_decorator(deco)
                if method and path:
                    # 提取依赖注入
                    deps = self._extract_dependencies(node, content)
                    auth_level = self._classify_auth(deps)

                    # 提取返回类型
                    return_type = None
                    if node.returns:
                        return_type = ModelExtractor(
                            self.root)._annotation_to_str(node.returns)

                    # 提取response_model从装饰器
                    response_model = self._extract_response_model(deco)

                    # 提取docstring
                    docstring = ast.get_docstring(node) or ""

                    # 确定模块
                    module = self._guess_module(path, rel)

                    full_path = file_prefix + path if not path.startswith(
                        file_prefix) else path

                    self.endpoints.append({
                        "method": method.upper(),
                        "path": full_path,
                        "function": node.name,
                        "file": rel,
                        "line": node.lineno,
                        "module": module,
                        "auth_level": auth_level,
                        "dependencies": deps,
                        "response_model": response_model,
                        "return_type": return_type,
                        "docstring": docstring[:200] if docstring else "",
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "parameters": self._extract_params(node),
                    })

    def _parse_route_decorator(self, deco) -> Tuple[Optional[str], Optional[str]]:
        """解析路由装饰器, 返回 (method, path)"""
        if isinstance(deco, ast.Call):
            func = deco.func
            if isinstance(func, ast.Attribute):
                method = func.attr
                if method in self.HTTP_METHODS:
                    # 获取path参数
                    path = ""
                    if deco.args:
                        path = ModelExtractor(self.root)._get_const_value(
                            deco.args[0])
                        if not isinstance(path, str):
                            path = str(path)
                    return method, path
        elif isinstance(deco, ast.Attribute):
            if deco.attr in self.HTTP_METHODS:
                return deco.attr, "/"
        return None, None

    def _extract_dependencies(self, func_node, content: str) -> List[Dict]:
        """提取函数参数中的Depends(...)依赖"""
        deps = []
        for arg in func_node.args.args + func_node.args.kwonlyargs:
            # 检查注解中的Depends
            if arg.annotation and isinstance(arg.annotation, ast.Call):
                call = arg.annotation
            else:
                continue

        # 检查默认值中的Depends
        defaults = func_node.args.defaults + func_node.args.kw_defaults
        all_args = func_node.args.args + func_node.args.kwonlyargs

        # 对齐默认值和参数
        for i, default in enumerate(defaults):
            if default is None:
                continue
            if isinstance(default, ast.Call):
                func = default.func
                func_name = ""
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr

                if func_name == 'Depends':
                    dep_func = ""
                    if default.args:
                        dep_arg = default.args[0]
                        if isinstance(dep_arg, ast.Name):
                            dep_func = dep_arg.id
                        elif isinstance(dep_arg, ast.Attribute):
                            dep_func = ModelExtractor(
                                self.root)._attr_to_str(dep_arg)
                        elif isinstance(dep_arg, ast.Call):
                            # Depends(require_role("admin"))
                            inner_func = dep_arg.func
                            if isinstance(inner_func, ast.Name):
                                dep_func = inner_func.id
                                args = [ModelExtractor(
                                    self.root)._get_const_value(a)
                                    for a in dep_arg.args]
                                dep_func = f"{dep_func}({','.join(str(a) for a in args)})"
                            elif isinstance(inner_func, ast.Attribute):
                                dep_func = inner_func.attr
                    if dep_func:
                        role = self.KNOWN_DEPS.get(
                            dep_func.split('(')[0], 'custom')
                        deps.append({
                            "dependency": dep_func,
                            "role": role,
                        })

        # 正则回退: 从源码行提取Depends
        if not deps:
            func_start = func_node.lineno
            func_end = func_node.end_lineno if hasattr(
                func_node, 'end_lineno') else func_start + 20
            lines = content.split('\n')[func_start - 1:func_end]
            func_text = '\n'.join(lines)

            dep_pattern = re.compile(r'Depends\(\s*(\w+(?:\([^)]*\))?)\s*\)')
            for dm in dep_pattern.finditer(func_text):
                dep_name = dm.group(1)
                role = self.KNOWN_DEPS.get(
                    dep_name.split('(')[0], 'custom')
                deps.append({
                    "dependency": dep_name,
                    "role": role,
                })

        return deps

    def _classify_auth(self, deps: List[Dict]) -> str:
        """根据依赖分类权限级别"""
        if not deps:
            return "public"

        dep_names = [d['dependency'].split('(')[0] for d in deps]

        if 'require_admin' in dep_names:
            return "admin_only"
        if 'require_coach_or_admin' in dep_names:
            return "coach_or_admin"
        if 'require_expert' in dep_names:
            return "expert_only"
        if any('require_role' in d['dependency'] for d in deps):
            return "role_required"
        if 'get_current_user' in dep_names or \
           'get_current_active_user' in dep_names:
            return "authenticated"
        return "custom"

    def _extract_response_model(self, deco) -> Optional[str]:
        """从装饰器提取response_model"""
        if isinstance(deco, ast.Call):
            for kw in deco.keywords:
                if kw.arg == 'response_model':
                    return ModelExtractor(self.root)._annotation_to_str(
                        kw.value)
        return None

    def _extract_params(self, func_node) -> List[Dict]:
        """提取函数参数"""
        params = []
        for arg in func_node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            annotation = ModelExtractor(self.root)._annotation_to_str(
                arg.annotation) if arg.annotation else "Any"
            params.append({
                "name": arg.arg,
                "type": annotation,
            })
        return params

    def _find_file_prefix(self, content: str) -> str:
        """从文件中查找路由前缀"""
        match = re.search(
            r'prefix\s*=\s*["\']([^"\']+)["\']', content)
        return match.group(1) if match else ""

    def _guess_module(self, path: str, rel: str) -> str:
        """推断端点所属模块"""
        # 从路径推断
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            # /v1/xxx/... -> xxx
            for p in parts:
                if p not in ('v1', 'v2', 'api', 'mp'):
                    return p
        # 从文件名推断
        fname = os.path.basename(rel).replace('.py', '')
        for suffix in ('_api', '_routes', '_router', '_views'):
            if fname.endswith(suffix):
                return fname[:-len(suffix)]
        return fname

    def _extract_endpoints_regex(self, content: str, rel: str):
        """正则回退提取端点"""
        file_prefix = self._find_file_prefix(content)

        pattern = re.compile(
            r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            r'(?:[^)]*response_model\s*=\s*(\w+))?[^)]*\)\s*'
            r'(?:async\s+)?def\s+(\w+)',
            re.MULTILINE | re.DOTALL
        )

        for match in pattern.finditer(content):
            method = match.group(1).upper()
            path = match.group(2)
            response_model = match.group(3)
            func_name = match.group(4)

            # 提取Depends
            func_start = match.end()
            func_block = content[match.start():func_start + 500]
            deps = []
            dep_pattern = re.compile(r'Depends\(\s*(\w+(?:\([^)]*\))?)\s*\)')
            for dm in dep_pattern.finditer(func_block):
                dep_name = dm.group(1)
                role = self.KNOWN_DEPS.get(dep_name.split('(')[0], 'custom')
                deps.append({"dependency": dep_name, "role": role})

            full_path = file_prefix + path if not path.startswith('/') \
                else path
            auth_level = self._classify_auth(deps)
            module = self._guess_module(full_path, rel)

            self.endpoints.append({
                "method": method,
                "path": full_path,
                "function": func_name,
                "file": rel,
                "line": content[:match.start()].count('\n') + 1,
                "module": module,
                "auth_level": auth_level,
                "dependencies": deps,
                "response_model": response_model,
                "return_type": None,
                "docstring": "",
                "is_async": 'async def' in func_block[:100],
                "parameters": [],
            })


# ==============================================================================
# Module 3: Agent注册表 (12域Agent + 4专家Agent)
# ==============================================================================

class AgentExtractor:
    """Agent提取器 - 域Agent、专家Agent、路由规则"""

    def __init__(self, root: str):
        self.root = root
        self.domain_agents = []
        self.expert_agents = []
        self.routing_rules = {}
        self.domain_map = {}
        self.agent_configs = {}

    def extract_all(self) -> Dict:
        progress("提取Agent注册表...")
        py_files = walk_files(self.root, {'.py'})

        for fpath in py_files:
            rel = normalize_path(fpath, self.root)
            if not is_core_platform(rel):
                continue
            content = safe_read(fpath)
            if not content:
                continue

            # 提取Agent类
            self._extract_agent_classes(fpath, content, rel)

            # 提取AGENT_DOMAIN_MAP
            self._extract_domain_map(content, rel)

            # 提取路由规则
            self._extract_routing(content, rel)

            # 提取配置
            self._extract_agent_configs(content, rel)

        progress(f"Agent: {len(self.domain_agents)}个域Agent, "
                 f"{len(self.expert_agents)}个专家Agent, "
                 f"{len(self.domain_map)}个域映射")

        return {
            "domain_agents": self.domain_agents,
            "expert_agents": self.expert_agents,
            "domain_map": self.domain_map,
            "routing_rules": self.routing_rules,
            "agent_configs": self.agent_configs,
            "summary": {
                "total_domain_agents": len(self.domain_agents),
                "total_expert_agents": len(self.expert_agents),
                "domain_list": list(set(
                    a.get('domain', '') for a in self.domain_agents)),
                "expert_list": [a['class_name'] for a in self.expert_agents],
            }
        }

    def _extract_agent_classes(self, fpath: str, content: str, rel: str):
        """提取Agent类定义"""
        tree = safe_parse_ast(fpath)
        if not tree:
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)

            is_agent = any('Agent' in b for b in bases)
            if not is_agent:
                continue

            # 提取Agent属性
            agent_info = {
                "class_name": node.name,
                "base_classes": bases,
                "file": rel,
                "line": node.lineno,
                "domain": None,
                "display_name": None,
                "keywords": [],
                "priority": None,
                "base_weight": None,
                "risk_level": None,
                "system_prompt": None,
                "description": ast.get_docstring(node) or "",
            }

            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            val = ModelExtractor(
                                self.root)._get_const_value(item.value)
                            if name == 'domain':
                                agent_info['domain'] = val
                            elif name == 'display_name':
                                agent_info['display_name'] = val
                            elif name == 'keywords':
                                agent_info['keywords'] = val if isinstance(
                                    val, list) else [val]
                            elif name == 'priority':
                                agent_info['priority'] = val
                            elif name == 'base_weight':
                                agent_info['base_weight'] = val
                            elif name == 'risk_level':
                                agent_info['risk_level'] = val
                            elif name in ('system_prompt', 'prompt',
                                          'system_message'):
                                agent_info['system_prompt'] = str(
                                    val)[:300] if val else None

            # 分类: 域Agent vs 专家Agent
            is_expert = (
                'behavior_rx' in rel or
                'Expert' in node.name or
                any('Expert' in b for b in bases) or
                'Adherence' in node.name or
                'Coach' in node.name and 'Behavior' in node.name
            )

            if is_expert:
                self.expert_agents.append(agent_info)
            else:
                self.domain_agents.append(agent_info)

    def _extract_domain_map(self, content: str, rel: str):
        """提取AGENT_DOMAIN_MAP常量"""
        # 匹配字典定义
        patterns = [
            r'AGENT_DOMAIN_MAP\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            r'DOMAIN_AGENT_MAP\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            r'domain_agents?\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
        ]
        for pat in patterns:
            match = re.search(pat, content, re.DOTALL)
            if match:
                # 尝试提取键值对
                map_content = match.group(1)
                entries = re.findall(
                    r'["\'](\w+)["\']\s*:\s*(\w+)', map_content)
                for domain, agent_class in entries:
                    self.domain_map[domain] = {
                        "agent_class": agent_class,
                        "file": rel,
                    }

    def _extract_routing(self, content: str, rel: str):
        """提取路由规则 (MasterAgent/AgentRouter)"""
        if 'route' not in content.lower() and 'dispatch' not in content.lower():
            return

        # 提取优先级规则
        priority_pattern = re.compile(
            r'priority.*?(\d+).*?["\'](\w+)["\']', re.IGNORECASE)
        for match in priority_pattern.finditer(content):
            domain = match.group(2)
            priority = int(match.group(1))
            if domain not in self.routing_rules:
                self.routing_rules[domain] = {}
            self.routing_rules[domain]['priority'] = priority
            self.routing_rules[domain]['file'] = rel

        # 提取关键词路由
        keyword_route_pattern = re.compile(
            r'keywords?\s*[=:]\s*\[([^\]]+)\].*?domain\s*[=:]\s*["\'](\w+)["\']',
            re.DOTALL
        )
        for match in keyword_route_pattern.finditer(content):
            keywords = re.findall(r'["\']([^"\']+)["\']', match.group(1))
            domain = match.group(2)
            if domain not in self.routing_rules:
                self.routing_rules[domain] = {}
            self.routing_rules[domain]['keywords'] = keywords

    def _extract_agent_configs(self, content: str, rel: str):
        """提取Agent配置(温度、最大token等)"""
        config_patterns = [
            r'temperature\s*[=:]\s*([\d.]+)',
            r'max_tokens?\s*[=:]\s*(\d+)',
            r'model\s*[=:]\s*["\']([^"\']+)["\']',
            r'max_input_?(?:length|chars?)\s*[=:]\s*(\d+)',
            r'max_output_?(?:length|chars?)\s*[=:]\s*(\d+)',
        ]
        configs_found = {}
        for pat in config_patterns:
            match = re.search(pat, content)
            if match:
                key = pat.split(r'\s')[0].rstrip('?')
                configs_found[key] = match.group(1)

        if configs_found and ('agent' in rel.lower() or 'llm' in rel.lower()):
            self.agent_configs[rel] = configs_found


# ==============================================================================
# Module 4: 配置文件完整内容
# ==============================================================================

def extract_config_files(root: str) -> Dict:
    """提取所有配置文件完整内容"""
    progress("提取配置文件...")

    configs = {}
    config_dirs = ['configs', 'data', 'behavior_rx/configs',
                   'behavior_rx_v32_complete/behavior_rx/configs']

    # 扫描所有JSON/YAML配置
    for config_dir in config_dirs:
        full_dir = os.path.join(root, config_dir)
        if not os.path.isdir(full_dir):
            continue

        for fpath in walk_files(full_dir, {'.json', '.yaml', '.yml'},
                                include_dify=False):
            rel = normalize_path(fpath, root)
            fname = os.path.basename(fpath)

            content = safe_json_read(fpath) if fpath.endswith('.json') \
                else safe_read(fpath)

            if content is not None:
                # 统计配置项数量
                item_count = 0
                if isinstance(content, list):
                    item_count = len(content)
                elif isinstance(content, dict):
                    item_count = len(content)

                configs[rel] = {
                    "filename": fname,
                    "path": rel,
                    "format": "json" if fpath.endswith('.json') else "yaml",
                    "content": content,
                    "item_count": item_count,
                    "size_bytes": os.path.getsize(fpath),
                }

    # 也扫描根目录的配置文件
    for fname in os.listdir(root):
        if fname.endswith(('.json', '.yaml', '.yml', '.env', '.toml')):
            fpath = os.path.join(root, fname)
            if os.path.isfile(fpath):
                rel = normalize_path(fpath, root)
                if fname.endswith('.json'):
                    content = safe_json_read(fpath)
                else:
                    content = safe_read(fpath)
                if content:
                    configs[rel] = {
                        "filename": fname,
                        "path": rel,
                        "format": fname.split('.')[-1],
                        "content": content if not isinstance(
                            content, str) or len(content) < 50000
                            else content[:50000] + "...[TRUNCATED]",
                        "item_count": len(content) if isinstance(
                            content, (list, dict)) else None,
                        "size_bytes": os.path.getsize(fpath),
                    }

    # 提取内联配置 (Python文件中的重要字典/列表常量)
    inline_configs = {}
    important_patterns = [
        (r'POINT_EVENTS?\s*=\s*(\[[\s\S]*?\n\])', 'point_events'),
        (r'MILESTONES?\s*=\s*(\[[\s\S]*?\n\])', 'milestones'),
        (r'BADGE[S_]*\s*=\s*(\[[\s\S]*?\n\])', 'badges'),
        (r'CREDIT_REQUIREMENTS?\s*=\s*(\{[\s\S]*?\n\})', 'credit_requirements'),
        (r'PROMOTION_RULES?\s*=\s*(\{[\s\S]*?\n\}|\[[\s\S]*?\n\])',
         'promotion_rules'),
        (r'ALERT_THRESHOLDS?\s*=\s*(\{[\s\S]*?\n\})', 'alert_thresholds'),
        (r'SAFETY_RULES?\s*=\s*(\{[\s\S]*?\n\}|\[[\s\S]*?\n\])',
         'safety_rules'),
        (r'SAFETY_KEYWORDS?\s*=\s*(\[[\s\S]*?\n\])', 'safety_keywords'),
        (r'RISK_LEVELS?\s*=\s*(\{[\s\S]*?\n\}|\[[\s\S]*?\n\])', 'risk_levels'),
        (r'SERVICE_TIERS?\s*=\s*(\{[\s\S]*?\n\}|\[[\s\S]*?\n\])',
         'service_tiers'),
    ]

    for fpath in walk_files(root, {'.py'}):
        rel = normalize_path(fpath, root)
        if not is_core_platform(rel):
            continue
        content = safe_read(fpath)
        for pattern, key in important_patterns:
            match = re.search(pattern, content)
            if match:
                inline_configs[f"{rel}::{key}"] = {
                    "file": rel,
                    "variable": key,
                    "raw_value": match.group(1)[:5000],
                }

    progress(f"配置文件: {len(configs)}个文件, {len(inline_configs)}个内联配置")

    return {
        "config_files": configs,
        "inline_configs": inline_configs,
        "summary": {
            "total_config_files": len(configs),
            "total_inline_configs": len(inline_configs),
            "config_file_list": [
                {"path": k, "items": v.get("item_count")}
                for k, v in configs.items()
            ],
        }
    }


# ==============================================================================
# Module 5: 多租户架构
# ==============================================================================

def extract_tenant_architecture(root: str) -> Dict:
    """提取多租户架构"""
    progress("提取多租户架构...")

    result = {
        "tenant_models": [],
        "isolation_patterns": [],
        "auth_chain": [],
        "rbac_definitions": [],
        "tenant_endpoints": [],
    }

    py_files = walk_files(root, {'.py'})

    for fpath in py_files:
        rel = normalize_path(fpath, root)
        if not is_core_platform(rel):
            continue
        content = safe_read(fpath)
        if not content:
            continue

        # 租户相关模型
        if 'tenant' in content.lower() or 'Tenant' in content:
            # 提取Tenant相关类
            tree = safe_parse_ast(fpath)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and \
                       'Tenant' in node.name:
                        extractor = ModelExtractor(root)
                        extractor._classify_class(node, content, rel)
                        if extractor.orm_models:
                            result["tenant_models"].extend(
                                extractor.orm_models)
                        if extractor.pydantic_schemas:
                            result["tenant_models"].extend(
                                extractor.pydantic_schemas)

        # 数据隔离模式
        isolation_patterns = [
            (r'\.filter\(.*?tenant_id\s*==', 'tenant_id_filter'),
            (r'\.filter\(.*?coach_id\s*==', 'coach_id_filter'),
            (r'\.filter\(.*?user_id\s*==', 'user_id_filter'),
            (r'\.filter\(.*?creator_id\s*==', 'creator_id_filter'),
            (r'\.filter\(.*?supervisor_id\s*==', 'supervisor_id_filter'),
            (r'WHERE.*?tenant_id\s*=', 'raw_sql_tenant_filter'),
        ]
        for pat, pat_type in isolation_patterns:
            matches = re.findall(pat, content)
            if matches:
                result["isolation_patterns"].append({
                    "file": rel,
                    "pattern_type": pat_type,
                    "count": len(matches),
                })

        # Auth链
        if 'get_current_user' in content or 'require_role' in content or \
           'require_admin' in content:
            # 提取完整的auth函数
            auth_funcs = re.findall(
                r'(?:async\s+)?def\s+(get_current_\w+|require_\w+)\s*\([^)]*\)',
                content)
            for func in auth_funcs:
                # 提取函数体概要
                func_match = re.search(
                    rf'(?:async\s+)?def\s+{re.escape(func)}\s*\([^)]*\)\s*'
                    rf'(?:->.*?)?\s*:(.*?)(?=\n(?:async\s+)?def\s|\nclass\s|\Z)',
                    content, re.DOTALL)
                body_preview = func_match.group(1)[:300].strip() \
                    if func_match else ""

                result["auth_chain"].append({
                    "function": func,
                    "file": rel,
                    "body_preview": body_preview,
                })

        # RBAC定义
        rbac_patterns = [
            (r'class\s+(\w*(?:Role|Permission|Access)\w*)', 'class'),
            (r'(\w+)\s*=\s*["\'](?:admin|coach|expert|observer|grower|sharer|master)["\']',
             'role_constant'),
            (r'role_level\s*[><=!]+\s*(\d+)', 'role_level_check'),
        ]
        for pat, pat_type in rbac_patterns:
            for match in re.finditer(pat, content):
                result["rbac_definitions"].append({
                    "file": rel,
                    "type": pat_type,
                    "value": match.group(1) if match.lastindex else match.group(0),
                    "context": content[max(0, match.start()-50):match.end()+50].strip(),
                })

    progress(f"多租户: {len(result['tenant_models'])}个模型, "
             f"{len(result['isolation_patterns'])}个隔离模式, "
             f"{len(result['auth_chain'])}个Auth函数")

    return {
        **result,
        "summary": {
            "total_tenant_models": len(result["tenant_models"]),
            "total_isolation_patterns": len(result["isolation_patterns"]),
            "total_auth_functions": len(result["auth_chain"]),
            "isolation_types": list(set(
                p["pattern_type"] for p in result["isolation_patterns"])),
        }
    }


# ==============================================================================
# Module 6: 安全管道 (PolicyGate + Safety Pipeline)
# ==============================================================================

def extract_safety_pipeline(root: str) -> Dict:
    """提取安全管道完整配置"""
    progress("提取安全管道...")

    result = {
        "policy_gate_rules": [],
        "safety_levels": [],
        "crisis_keywords": [],
        "alert_thresholds": {},
        "safety_configs": {},
        "safety_functions": [],
        "content_filters": [],
    }

    py_files = walk_files(root, {'.py'})

    for fpath in py_files:
        rel = normalize_path(fpath, root)
        if not is_core_platform(rel):
            continue
        content = safe_read(fpath)
        if not content:
            continue

        # PolicyGate规则
        if 'PolicyGate' in content or 'policy_gate' in content or \
           'policy_rules' in content:
            # 提取规则定义
            rule_patterns = [
                r'(?:Rule|PolicyRule|GateRule)\s*\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']'
                r'(?:.*?description\s*=\s*["\']([^"\']+)["\'])?',
                r'["\'](\w+_rule)["\'].*?["\']([^"\']*)["\']',
                r'rules?\s*=\s*\[([\s\S]*?)\]',
            ]
            for pat in rule_patterns:
                for match in re.finditer(pat, content, re.DOTALL):
                    result["policy_gate_rules"].append({
                        "file": rel,
                        "match": match.group(0)[:500],
                    })

            # 提取PolicyGate类/函数
            tree = safe_parse_ast(fpath)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and \
                       'Policy' in node.name:
                        # 提取方法名和docstring
                        methods = []
                        for item in node.body:
                            if isinstance(item,
                                          (ast.FunctionDef,
                                           ast.AsyncFunctionDef)):
                                doc = ast.get_docstring(item) or ""
                                methods.append({
                                    "name": item.name,
                                    "docstring": doc[:200],
                                })
                        result["policy_gate_rules"].append({
                            "file": rel,
                            "class": node.name,
                            "docstring": (ast.get_docstring(node) or "")[:300],
                            "methods": methods,
                        })

        # 安全级别
        if 'severity' in content.lower() or 'safety_level' in content.lower() \
           or 'risk_level' in content.lower():
            level_patterns = [
                r'(?:CRITICAL|HIGH|MEDIUM|LOW)\s*[=:]\s*["\']?([^"\'}\n,]+)',
                r'severity\s*[=:]\s*["\'](\w+)["\']',
                r'(?:block_and_escalate|flag_for_review|add_disclaimer|pass)\s*',
            ]
            for pat in level_patterns:
                for match in re.finditer(pat, content):
                    result["safety_levels"].append({
                        "file": rel,
                        "match": match.group(0)[:200],
                    })

        # 危机关键词
        crisis_patterns = [
            r'crisis_keywords?\s*=\s*\[([^\]]+)\]',
            r'CRISIS_KEYWORDS?\s*=\s*\[([^\]]+)\]',
            r'suicide_keywords?\s*=\s*\[([^\]]+)\]',
        ]
        for pat in crisis_patterns:
            match = re.search(pat, content)
            if match:
                keywords = re.findall(r'["\']([^"\']+)["\']', match.group(1))
                result["crisis_keywords"].extend(keywords)

        # Safety相关函数
        if 'safety' in rel.lower() or 'crisis' in rel.lower() or \
           'gatekeeper' in rel.lower():
            tree = safe_parse_ast(fpath)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node,
                                  (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if any(kw in node.name.lower()
                               for kw in ('safe', 'check', 'filter',
                                          'crisis', 'escalat', 'block')):
                            result["safety_functions"].append({
                                "function": node.name,
                                "file": rel,
                                "line": node.lineno,
                                "docstring": (ast.get_docstring(node) or "")[:200],
                                "params": [
                                    a.arg for a in node.args.args
                                    if a.arg != 'self'
                                ],
                            })

    # 读取安全配置文件
    safety_config_files = [
        'configs/safety_rules.json',
        'configs/safety_keywords.json',
        'configs/alert_thresholds.json',
    ]
    for config_rel in safety_config_files:
        fpath = os.path.join(root, config_rel)
        if os.path.isfile(fpath):
            content = safe_json_read(fpath)
            if content:
                result["safety_configs"][config_rel] = content

    # 去重crisis keywords
    result["crisis_keywords"] = list(set(result["crisis_keywords"]))

    progress(f"安全管道: {len(result['policy_gate_rules'])}条策略规则, "
             f"{len(result['crisis_keywords'])}个危机关键词, "
             f"{len(result['safety_functions'])}个安全函数")

    return {
        **result,
        "summary": {
            "total_policy_rules": len(result["policy_gate_rules"]),
            "total_crisis_keywords": len(result["crisis_keywords"]),
            "total_safety_functions": len(result["safety_functions"]),
            "crisis_keyword_list": result["crisis_keywords"],
        }
    }


# ==============================================================================
# Module 7: Alembic迁移历史 [NEW]
# ==============================================================================

def extract_alembic_migrations(root: str) -> Dict:
    """提取Alembic迁移历史"""
    progress("提取Alembic迁移历史...")

    migrations = []
    migration_dirs = ['alembic/versions', 'migrations/versions',
                      'behavior_rx/migrations/versions']

    for mig_dir in migration_dirs:
        full_dir = os.path.join(root, mig_dir)
        if not os.path.isdir(full_dir):
            continue

        for fpath in sorted(os.listdir(full_dir)):
            if not fpath.endswith('.py'):
                continue

            full_path = os.path.join(full_dir, fpath)
            rel = normalize_path(full_path, root)
            content = safe_read(full_path)
            if not content:
                continue

            # 提取revision信息
            revision = None
            down_revision = None
            message = None

            rev_match = re.search(
                r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
            if rev_match:
                revision = rev_match.group(1)

            down_match = re.search(
                r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", content)
            if down_match:
                down_revision = down_match.group(1)

            # None or tuple
            if not down_match:
                down_match = re.search(
                    r"down_revision\s*=\s*None", content)
                if down_match:
                    down_revision = None

            msg_match = re.search(
                r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')|(#.*?$)',
                content[:500], re.DOTALL | re.MULTILINE)
            if msg_match:
                message = (msg_match.group(1) or msg_match.group(2) or "").strip()
                message = message[:200]

            # 分离upgrade/downgrade
            upgrade_match = re.search(
                r'def\s+upgrade\s*\(\s*\)\s*:(.*?)(?=\ndef\s|\Z)',
                content, re.DOTALL)
            downgrade_match = re.search(
                r'def\s+downgrade\s*\(\s*\)\s*:(.*?)(?=\ndef\s|\Z)',
                content, re.DOTALL)
            upgrade_content = upgrade_match.group(1) if upgrade_match else content
            downgrade_content = downgrade_match.group(1) if downgrade_match else ""

            # 提取操作 (仅从upgrade)
            operations = {
                "create_table": [],
                "drop_table": [],
                "add_column": [],
                "drop_column": [],
                "alter_column": [],
                "create_index": [],
                "create_foreign_key": [],
                "other": [],
            }

            # create_table (upgrade only)
            for match in re.finditer(
                    r"op\.create_table\s*\(\s*['\"](\w+)['\"]",
                    upgrade_content):
                table_name = match.group(1)
                # 提取该table的列
                table_block_match = re.search(
                    rf"op\.create_table\s*\(\s*['\"]" + re.escape(table_name) +
                    r"['\"]" + r"([\s\S]*?)\n\s*\)",
                    upgrade_content)
                columns = []
                if table_block_match:
                    col_pattern = re.compile(
                        r"sa\.Column\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                        r"(sa\.\w+(?:\([^)]*\))?)")
                    for cm in col_pattern.finditer(table_block_match.group(1)):
                        columns.append({
                            "name": cm.group(1),
                            "type": cm.group(2),
                        })
                operations["create_table"].append({
                    "table": table_name,
                    "columns": columns,
                })

            # drop_table (upgrade only - means table removed in this migration)
            for match in re.finditer(
                    r"op\.drop_table\s*\(\s*['\"](\w+)['\"]",
                    upgrade_content):
                operations["drop_table"].append(match.group(1))

            # add_column
            for match in re.finditer(
                    r"op\.add_column\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                    r"sa\.Column\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                    r"(sa\.\w+(?:\([^)]*\))?)", upgrade_content):
                operations["add_column"].append({
                    "table": match.group(1),
                    "column": match.group(2),
                    "type": match.group(3),
                })

            # drop_column
            for match in re.finditer(
                    r"op\.drop_column\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                    r"['\"](\w+)['\"]", upgrade_content):
                operations["drop_column"].append({
                    "table": match.group(1),
                    "column": match.group(2),
                })

            # alter_column
            for match in re.finditer(
                    r"op\.alter_column\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                    r"['\"](\w+)['\"]", upgrade_content):
                operations["alter_column"].append({
                    "table": match.group(1),
                    "column": match.group(2),
                })

            # create_index
            for match in re.finditer(
                    r"op\.create_index\s*\(\s*['\"](\w+)['\"]\s*,\s*"
                    r"['\"](\w+)['\"]", upgrade_content):
                operations["create_index"].append({
                    "index": match.group(1),
                    "table": match.group(2),
                })

            has_ops = any(v for v in operations.values())

            migrations.append({
                "file": rel,
                "filename": fpath,
                "revision": revision,
                "down_revision": down_revision,
                "message": message,
                "operations": operations,
                "has_operations": has_ops,
            })

    # 构建迁移链
    rev_map = {m['revision']: m for m in migrations if m.get('revision')}
    chain = []
    # 找到起点(down_revision is None)
    starts = [m for m in migrations if m.get('down_revision') is None
              and m.get('revision')]
    for start in starts:
        current = start['revision']
        while current and current in rev_map:
            chain.append(current)
            # 找下一个
            nexts = [m for m in migrations
                     if m.get('down_revision') == current]
            current = nexts[0]['revision'] if nexts else None

    # 提取所有创建的表
    all_tables = set()
    for m in migrations:
        for ct in m['operations']['create_table']:
            all_tables.add(ct['table'])
        for dt in m['operations']['drop_table']:
            all_tables.discard(dt)

    progress(f"Alembic: {len(migrations)}个迁移, "
             f"{len(all_tables)}个表, "
             f"迁移链长度{len(chain)}")

    return {
        "migrations": migrations,
        "migration_chain": chain,
        "tables_created": sorted(all_tables),
        "summary": {
            "total_migrations": len(migrations),
            "total_tables": len(all_tables),
            "chain_length": len(chain),
            "migration_dirs_found": [
                d for d in migration_dirs
                if os.path.isdir(os.path.join(root, d))
            ],
        }
    }


# ==============================================================================
# Module 8: 前端路由与API服务 [NEW]
# ==============================================================================

def extract_frontend(root: str) -> Dict:
    """提取前端路由、权限守卫和API服务"""
    progress("提取前端路由与API服务...")

    result = {
        "vue_routes": [],
        "route_guards": [],
        "api_services": [],
        "vue_components": [],
        "stores": [],
    }

    frontend_dirs = ['admin-portal', 'h5', 'h5-patient-app', 'frontend']

    for fe_dir in frontend_dirs:
        full_dir = os.path.join(root, fe_dir)
        if not os.path.isdir(full_dir):
            continue

        # 扫描路由文件
        for fpath in walk_files(full_dir, {'.ts', '.js', '.tsx', '.jsx'}):
            rel = normalize_path(fpath, root)
            fname = os.path.basename(fpath)
            content = safe_read(fpath)
            if not content:
                continue

            # 路由定义
            if 'router' in rel.lower() or 'route' in fname.lower():
                routes = _extract_vue_routes(content, rel)
                result["vue_routes"].extend(routes)

                # 路由守卫
                guards = _extract_route_guards(content, rel)
                result["route_guards"].extend(guards)

            # API服务文件
            if '/api/' in rel or fname.startswith('api'):
                services = _extract_api_services(content, rel)
                result["api_services"].extend(services)

            # Store (Pinia/Vuex)
            if '/store' in rel:
                stores = _extract_stores(content, rel)
                result["stores"].extend(stores)

        # Vue组件
        for fpath in walk_files(full_dir, {'.vue'}):
            rel = normalize_path(fpath, root)
            fname = os.path.basename(fpath)
            result["vue_components"].append({
                "name": fname.replace('.vue', ''),
                "file": rel,
                "size": os.path.getsize(fpath),
            })

    progress(f"前端: {len(result['vue_routes'])}条路由, "
             f"{len(result['api_services'])}个API服务, "
             f"{len(result['vue_components'])}个组件")

    return {
        **result,
        "summary": {
            "total_routes": len(result["vue_routes"]),
            "total_api_services": len(result["api_services"]),
            "total_components": len(result["vue_components"]),
            "total_stores": len(result["stores"]),
            "frontend_dirs": [d for d in frontend_dirs
                              if os.path.isdir(os.path.join(root, d))],
        }
    }


def _extract_vue_routes(content: str, rel: str) -> List[Dict]:
    """提取Vue路由定义"""
    routes = []
    # 匹配路由对象: { path: '/xxx', name: 'xxx', component: ..., meta: ... }
    route_pattern = re.compile(
        r'\{\s*path\s*:\s*[\'"]([^\'"]+)[\'"]\s*'
        r'(?:.*?name\s*:\s*[\'"]([^\'"]+)[\'"])?'
        r'(?:.*?component\s*:\s*(?:[\w.]+\s*(?:=>|,)?\s*)?(?:import\([\'"]([^\'"]+)[\'"]\))?)?'
        r'(?:.*?meta\s*:\s*\{([^}]*)\})?',
        re.DOTALL
    )
    for match in route_pattern.finditer(content):
        path = match.group(1)
        name = match.group(2) or ""
        component = match.group(3) or ""
        meta_str = match.group(4) or ""

        # 解析meta
        meta = {}
        if meta_str:
            for kv in re.finditer(r'(\w+)\s*:\s*([^,}]+)', meta_str):
                key = kv.group(1).strip()
                val = kv.group(2).strip().strip("'\"")
                meta[key] = val

        routes.append({
            "path": path,
            "name": name,
            "component": component,
            "meta": meta,
            "file": rel,
            "requires_auth": meta.get('requiresAuth', meta.get('auth', '')),
            "required_role": meta.get('role', meta.get('requiredRole', '')),
        })
    return routes


def _extract_route_guards(content: str, rel: str) -> List[Dict]:
    """提取路由守卫"""
    guards = []
    # beforeEach, beforeEnter
    guard_pattern = re.compile(
        r'(?:router\.beforeEach|beforeEnter)\s*(?:=\s*)?\(\s*(?:async\s*)?\('
        r'[^)]*\)\s*(?:=>|{)([\s\S]*?)(?:\}|;)',
        re.DOTALL
    )
    for match in guard_pattern.finditer(content):
        body = match.group(1)[:500]
        guards.append({
            "file": rel,
            "type": "beforeEach" if "beforeEach" in match.group(0) else "beforeEnter",
            "body_preview": body.strip(),
        })

    # 权限检查
    perm_patterns = [
        r'(?:user|auth)\.(?:role|level|permission)\s*[!=<>]+\s*[\'"]?(\w+)',
        r'(?:hasRole|checkRole|isAdmin|isCoach)\s*\(',
        r'role_level\s*[><=!]+\s*(\d+)',
    ]
    for pat in perm_patterns:
        for match in re.finditer(pat, content):
            guards.append({
                "file": rel,
                "type": "permission_check",
                "pattern": match.group(0)[:200],
            })

    return guards


def _extract_api_services(content: str, rel: str) -> List[Dict]:
    """提取前端API服务定义"""
    services = []
    # axios/fetch调用: api.get('/xxx'), request.post('/xxx')
    api_pattern = re.compile(
        r'(?:export\s+(?:async\s+)?function|const|let|var)\s+(\w+)'
        r'.*?(?:axios|request|api|http|fetch)\s*'
        r'(?:\.\s*(get|post|put|delete|patch))?\s*'
        r'(?:<[^>]*>)?\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]',
        re.DOTALL
    )
    for match in api_pattern.finditer(content):
        func_name = match.group(1)
        method = (match.group(2) or 'unknown').upper()
        path = match.group(3)

        services.append({
            "function": func_name,
            "method": method,
            "path": path,
            "file": rel,
        })

    # 也匹配简洁的调用模式
    simple_pattern = re.compile(
        r'(?:get|post|put|delete|patch)\s*(?:<[^>]*>)?\s*\(\s*'
        r'[\'"`](/[^\'"` ]+)[\'"`]',
        re.IGNORECASE
    )
    seen_paths = {s['path'] for s in services}
    for match in simple_pattern.finditer(content):
        path = match.group(1)
        if path not in seen_paths:
            method_match = re.search(
                r'(get|post|put|delete|patch)', match.group(0), re.IGNORECASE)
            services.append({
                "function": "",
                "method": method_match.group(1).upper() if method_match else "UNKNOWN",
                "path": path,
                "file": rel,
            })
            seen_paths.add(path)

    return services


def _extract_stores(content: str, rel: str) -> List[Dict]:
    """提取Pinia/Vuex Store"""
    stores = []
    # defineStore('xxx', { ... })
    store_pattern = re.compile(
        r'defineStore\s*\(\s*[\'"](\w+)[\'"]')
    for match in store_pattern.finditer(content):
        stores.append({
            "name": match.group(1),
            "file": rel,
            "type": "pinia",
        })
    return stores


# ==============================================================================
# Module 9: 定时任务与事件总线 [NEW]
# ==============================================================================

def extract_scheduled_tasks(root: str) -> Dict:
    """提取定时任务和事件触发器"""
    progress("提取定时任务与事件...")

    result = {
        "celery_tasks": [],
        "scheduled_jobs": [],
        "event_handlers": [],
        "cron_configs": [],
        "push_schedules": [],
    }

    py_files = walk_files(root, {'.py'})

    for fpath in py_files:
        rel = normalize_path(fpath, root)
        if not is_core_platform(rel):
            continue
        content = safe_read(fpath)
        if not content:
            continue

        # Celery任务
        celery_patterns = [
            r'@(?:app|celery)\.task(?:\([^)]*\))?\s*(?:async\s+)?def\s+(\w+)',
            r'@shared_task(?:\([^)]*\))?\s*(?:async\s+)?def\s+(\w+)',
        ]
        for pat in celery_patterns:
            for match in re.finditer(pat, content):
                result["celery_tasks"].append({
                    "task": match.group(1),
                    "file": rel,
                    "line": content[:match.start()].count('\n') + 1,
                })

        # APScheduler
        scheduler_patterns = [
            r'scheduler\.add_job\s*\(\s*(\w+)(?:\s*,\s*[\'"](\w+)[\'"])?'
            r'(?:.*?(?:hours?|minutes?|seconds?|cron)\s*=\s*([^,)]+))?',
            r'@scheduler\.scheduled_job\s*\(\s*[\'"](\w+)[\'"]'
            r'(?:.*?(?:hour|minute|second|day)\s*=\s*([^,)]+))?',
        ]
        for pat in scheduler_patterns:
            for match in re.finditer(pat, content, re.DOTALL):
                result["scheduled_jobs"].append({
                    "function": match.group(1),
                    "file": rel,
                    "trigger": match.group(2) if match.lastindex >= 2 else None,
                    "schedule": match.group(3) if match.lastindex >= 3 else None,
                    "raw": match.group(0)[:200],
                })

        # 事件处理器
        event_patterns = [
            r'(?:on_event|@event|event_handler|subscribe)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'emit\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'publish\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'EventType\.(\w+)',
        ]
        for pat in event_patterns:
            for match in re.finditer(pat, content):
                result["event_handlers"].append({
                    "event": match.group(1),
                    "file": rel,
                    "type": "handler" if 'on_' in match.group(0) or
                            'handler' in match.group(0) or
                            'subscribe' in match.group(0) else "emitter",
                })

        # 推送时间表
        push_patterns = [
            r'(?:push|notify|send).*?(?:time|schedule|cron)\s*[=:]\s*[\'"]([^\'"]+)[\'"]',
            r'(?:09:00|11:30|17:30|23:30|midnight|daily)',
        ]
        for pat in push_patterns:
            for match in re.finditer(pat, content):
                result["push_schedules"].append({
                    "file": rel,
                    "schedule": match.group(0)[:100],
                })

    # 检查crontab/docker配置
    for fname in ['docker-compose.yml', 'docker-compose.yaml',
                   'crontab', 'Procfile']:
        fpath = os.path.join(root, fname)
        if os.path.isfile(fpath):
            content = safe_read(fpath)
            if content:
                result["cron_configs"].append({
                    "file": fname,
                    "content": content[:5000],
                })

    # Helm charts
    helm_dir = os.path.join(root, 'helm')
    if os.path.isdir(helm_dir):
        for fpath in walk_files(helm_dir, {'.yaml', '.yml'}):
            content = safe_read(fpath)
            if 'cron' in content.lower() or 'schedule' in content.lower():
                result["cron_configs"].append({
                    "file": normalize_path(fpath, root),
                    "content": content[:5000],
                })

    progress(f"定时任务: {len(result['celery_tasks'])}个Celery任务, "
             f"{len(result['scheduled_jobs'])}个定时作业, "
             f"{len(result['event_handlers'])}个事件处理器")

    return {
        **result,
        "summary": {
            "total_celery_tasks": len(result["celery_tasks"]),
            "total_scheduled_jobs": len(result["scheduled_jobs"]),
            "total_event_handlers": len(result["event_handlers"]),
            "total_cron_configs": len(result["cron_configs"]),
        }
    }


# ==============================================================================
# Module 10: Dify工作流定义 [NEW]
# ==============================================================================

def extract_dify_workflows(root: str) -> Dict:
    """提取Dify工作流定义"""
    progress("提取Dify工作流...")

    result = {
        "workflows": [],
        "workflow_configs": [],
        "dify_integration": [],
    }

    # Dify工作流目录
    wf_dirs = ['dify_workflows', 'dify-setup']
    for wf_dir in wf_dirs:
        full_dir = os.path.join(root, wf_dir)
        if not os.path.isdir(full_dir):
            continue

        for fpath in walk_files(full_dir, {'.json', '.yaml', '.yml'},
                                include_dify=True):
            rel = normalize_path(fpath, root)
            content = None
            if fpath.endswith('.json'):
                content = safe_json_read(fpath)
            else:
                content = safe_read(fpath)

            if content:
                # 提取工作流元数据
                wf_info = {
                    "file": rel,
                    "filename": os.path.basename(fpath),
                    "size_bytes": os.path.getsize(fpath),
                }

                if isinstance(content, dict):
                    wf_info["name"] = content.get('name', content.get(
                        'workflow_name', ''))
                    wf_info["description"] = content.get(
                        'description', '')[:200]
                    wf_info["nodes"] = len(content.get(
                        'nodes', content.get('graph', {}).get('nodes', [])))
                    wf_info["edges"] = len(content.get(
                        'edges', content.get('graph', {}).get('edges', [])))
                    wf_info["variables"] = list(content.get(
                        'variables', content.get('inputs', {})).keys()) \
                        if isinstance(content.get(
                            'variables', content.get('inputs', {})), dict) \
                        else []

                    # 提取节点类型
                    nodes = content.get('nodes', content.get(
                        'graph', {}).get('nodes', []))
                    if isinstance(nodes, list):
                        node_types = defaultdict(int)
                        for node in nodes:
                            if isinstance(node, dict):
                                ntype = node.get('type', node.get(
                                    'node_type', 'unknown'))
                                node_types[ntype] += 1
                        wf_info["node_types"] = dict(node_types)

                    wf_info["content_preview"] = json.dumps(
                        content, ensure_ascii=False)[:2000] \
                        if isinstance(content, dict) else str(content)[:2000]

                result["workflows"].append(wf_info)

    # Dify集成代码
    for fpath in walk_files(root, {'.py'}):
        rel = normalize_path(fpath, root)
        if not is_core_platform(rel):
            continue
        content = safe_read(fpath)
        if not content:
            continue

        if 'dify' in content.lower() and ('workflow' in content.lower() or
                                           'api' in content.lower()):
            # 提取Dify API调用
            dify_patterns = [
                r'dify_(?:api|client|workflow)\s*(?:\.|\.)\s*(\w+)',
                r'DIFY_(?:API|BASE|WORKFLOW)\w*\s*=\s*[\'"]([^\'"]+)[\'"]',
                r'workflow_id\s*=\s*[\'"]([^\'"]+)[\'"]',
            ]
            calls = []
            for pat in dify_patterns:
                for match in re.finditer(pat, content):
                    calls.append(match.group(0)[:200])

            if calls:
                result["dify_integration"].append({
                    "file": rel,
                    "calls": calls,
                })

    progress(f"Dify: {len(result['workflows'])}个工作流, "
             f"{len(result['dify_integration'])}个集成文件")

    return {
        **result,
        "summary": {
            "total_workflows": len(result["workflows"]),
            "total_integration_files": len(result["dify_integration"]),
            "workflow_list": [
                {"file": w["file"], "name": w.get("name", ""),
                 "nodes": w.get("nodes", 0)}
                for w in result["workflows"]
            ],
        }
    }


# ==============================================================================
# 验证与摘要
# ==============================================================================

def generate_summary(results: Dict, root: str, elapsed: float) -> Dict:
    """生成提取摘要"""
    summary = {
        "extraction_version": VERSION,
        "extraction_time": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "project_root": root,
        "elapsed_seconds": round(elapsed, 1),
        "modules": {},
        "totals": {},
        "quality_checks": [],
    }

    # 每个模块的统计
    module_names = [
        ("0_project_structure", "项目结构"),
        ("1_data_models", "数据模型"),
        ("2_api_endpoints", "API端点"),
        ("3_agent_registry", "Agent注册表"),
        ("4_config_files", "配置文件"),
        ("5_tenant_architecture", "多租户架构"),
        ("6_safety_pipeline", "安全管道"),
        ("7_alembic_migrations", "Alembic迁移"),
        ("8_frontend", "前端路由"),
        ("9_scheduled_tasks", "定时任务"),
        ("10_dify_workflows", "Dify工作流"),
    ]

    for key, label in module_names:
        if key in results and 'summary' in results[key]:
            summary["modules"][key] = {
                "label": label,
                **results[key]["summary"],
            }

    # 汇总
    dm = results.get("1_data_models", {})
    summary["totals"] = {
        "orm_models": len(dm.get("orm_models", [])),
        "pydantic_schemas": len(dm.get("pydantic_schemas", [])),
        "enums": len(dm.get("enums", [])),
        "api_endpoints": len(
            results.get("2_api_endpoints", {}).get("endpoints", [])),
        "domain_agents": len(
            results.get("3_agent_registry", {}).get("domain_agents", [])),
        "expert_agents": len(
            results.get("3_agent_registry", {}).get("expert_agents", [])),
        "config_files": len(
            results.get("4_config_files", {}).get("config_files", {})),
        "alembic_migrations": len(
            results.get("7_alembic_migrations", {}).get("migrations", [])),
        "vue_routes": len(
            results.get("8_frontend", {}).get("vue_routes", [])),
        "vue_components": len(
            results.get("8_frontend", {}).get("vue_components", [])),
        "celery_tasks": len(
            results.get("9_scheduled_tasks", {}).get("celery_tasks", [])),
        "dify_workflows": len(
            results.get("10_dify_workflows", {}).get("workflows", [])),
    }

    # 质量检查
    checks = []
    t = summary["totals"]

    if t["orm_models"] == 0:
        checks.append("⚠️ 未发现ORM模型 - 检查SQLAlchemy模型目录")
    if t["api_endpoints"] == 0:
        checks.append("⚠️ 未发现API端点 - 检查FastAPI路由文件")
    if t["domain_agents"] == 0:
        checks.append("⚠️ 未发现域Agent - 检查core/agents/目录")
    if t["config_files"] == 0:
        checks.append("⚠️ 未发现配置文件 - 检查configs/目录")
    if t["alembic_migrations"] == 0:
        checks.append("ℹ️ 未发现Alembic迁移 - 可能使用其他迁移工具")
    if t["vue_routes"] == 0:
        checks.append("ℹ️ 未发现Vue路由 - 检查前端目录结构")

    # 检查auth覆盖率
    eps = results.get("2_api_endpoints", {}).get("endpoints", [])
    if eps:
        public = sum(1 for e in eps if e.get('auth_level') == 'public')
        authenticated = sum(1 for e in eps
                           if e.get('auth_level') != 'public')
        if public > authenticated:
            checks.append(f"⚠️ {public}个公开端点 > {authenticated}个认证端点 - "
                         "检查是否缺少权限装饰器提取")

    summary["quality_checks"] = checks

    # V1对比
    summary["v1_comparison"] = {
        "v1_total_models": 2241,
        "v2_orm_models": t["orm_models"],
        "v2_pydantic_schemas": t["pydantic_schemas"],
        "improvement": "V2区分了ORM和Schema, V1混为一体",
        "v1_endpoints": 667,
        "v2_endpoints": t["api_endpoints"],
        "v1_auth_extracted": False,
        "v2_auth_extracted": True,
        "v1_configs_empty": True,
        "v2_configs_populated": t["config_files"] > 0,
        "new_modules": [
            "Alembic迁移历史",
            "前端路由与API服务",
            "定时任务与事件",
            "Dify工作流"
        ]
    }

    return summary


# ==============================================================================
# 主程序
# ==============================================================================

def main():
    print("=" * 60)
    print(f"BehaviorOS 契约提取脚本 V{VERSION}")
    print("行健行为健康促进平台 - 全量契约提取")
    print("=" * 60)

    # 确定项目根目录
    if len(sys.argv) > 1:
        root = os.path.abspath(sys.argv[1])
    else:
        root = os.getcwd()

    print(f"\n项目根目录: {root}")

    if not os.path.isdir(root):
        print(f"错误: 目录不存在 - {root}")
        sys.exit(1)

    # 创建输出目录
    output_dir = os.path.join(root, '_contract_extraction_v2')
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}\n")

    start_time = time.time()
    results = {}

    # ====== 执行提取 ======
    try:
        # Module 0: 项目结构
        print("[1/11] 项目结构...")
        results["0_project_structure"] = extract_project_structure(root)

        # Module 1: 数据模型
        print("[2/11] 数据模型 (SQLAlchemy ORM + Pydantic Schema)...")
        extractor = ModelExtractor(root)
        results["1_data_models"] = extractor.extract_all()

        # Module 2: API端点
        print("[3/11] API端点 (含依赖注入链)...")
        api_ext = APIExtractor(root)
        results["2_api_endpoints"] = api_ext.extract_all()

        # V2.1: OpenAPI cross-validation
        openapi_path = os.path.join(root, 'openapi_dump.json')
        if os.path.isfile(openapi_path):
            try:
                with open(openapi_path, 'r', encoding='utf-8') as oaf:
                    openapi = json.load(oaf)
                paths = openapi.get('paths', {})
                openapi_ops = sum(len(methods) for methods in paths.values())
                results["2_api_endpoints"]["openapi_validation"] = {
                    "openapi_file": "openapi_dump.json",
                    "openapi_operations": openapi_ops,
                    "static_analysis_endpoints": len(results["2_api_endpoints"].get("endpoints", [])),
                    "note": "OpenAPI为权威端点源, 静态分析补充auth_level"
                }
                progress(f"OpenAPI交叉验证: {openapi_ops}个operations vs {len(results['2_api_endpoints'].get('endpoints',[]))}个静态分析端点")
            except Exception as e:
                progress(f"OpenAPI加载失败: {e}")
        else:
            results["2_api_endpoints"]["openapi_validation"] = {
                "note": "openapi_dump.json未找到, 仅使用静态分析"
            }

        # Module 3: Agent注册表
        print("[4/11] Agent注册表 (12域 + 4专家)...")
        agent_ext = AgentExtractor(root)
        results["3_agent_registry"] = agent_ext.extract_all()

        # Module 4: 配置文件
        print("[5/11] 配置文件 (完整内容)...")
        results["4_config_files"] = extract_config_files(root)

        # Module 5: 多租户架构
        print("[6/11] 多租户架构...")
        results["5_tenant_architecture"] = extract_tenant_architecture(root)

        # Module 6: 安全管道
        print("[7/11] 安全管道 (PolicyGate + Safety)...")
        results["6_safety_pipeline"] = extract_safety_pipeline(root)

        # Module 7: Alembic迁移
        print("[8/11] Alembic迁移历史...")
        results["7_alembic_migrations"] = extract_alembic_migrations(root)

        # Module 8: 前端
        print("[9/11] 前端路由与API服务...")
        results["8_frontend"] = extract_frontend(root)

        # Module 9: 定时任务
        print("[10/11] 定时任务与事件...")
        results["9_scheduled_tasks"] = extract_scheduled_tasks(root)

        # Module 10: Dify工作流
        print("[11/11] Dify工作流定义...")
        results["10_dify_workflows"] = extract_dify_workflows(root)

    except Exception as e:
        print(f"\n❌ 提取出错: {e}")
        traceback.print_exc()

    # ====== 生成摘要 ======
    elapsed = time.time() - start_time
    summary = generate_summary(results, root, elapsed)
    results["SUMMARY"] = summary

    # ====== 保存结果 ======
    print(f"\n保存结果到 {output_dir}/...")

    for key, data in results.items():
        output_file = os.path.join(output_dir, f"{key}.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            size = os.path.getsize(output_file)
            print(f"  ✅ {key}.json ({size:,} bytes)")
        except Exception as e:
            print(f"  ❌ {key}.json - 保存失败: {e}")

    # ====== 打印摘要 ======
    print("\n" + "=" * 60)
    print("提取完成!")
    print("=" * 60)
    print(f"\n⏱️  耗时: {elapsed:.1f}秒")

    print("\n📊 提取统计:")
    for key, val in summary["totals"].items():
        print(f"  • {key}: {val}")

    if summary["quality_checks"]:
        print("\n🔍 质量检查:")
        for check in summary["quality_checks"]:
            print(f"  {check}")

    print(f"\n📁 输出文件: {output_dir}/")
    print("   共 12 个JSON文件")

    print("\n📋 V2改进对比:")
    comp = summary.get("v1_comparison", {})
    print(f"  • 数据模型: V1混合{comp.get('v1_total_models',0)}个 → "
          f"V2分离 ORM {comp.get('v2_orm_models',0)} + "
          f"Schema {comp.get('v2_pydantic_schemas',0)}")
    print(f"  • API端点: V1 auth全部unknown → V2提取依赖注入链")
    print(f"  • 配置文件: V1内容为空 → V2完整内容")
    print(f"  • 新增: {', '.join(comp.get('new_modules', []))}")

    # V2.1: Auto-generate contract registry
    try:
        _gen_registry(results, output_dir, root)
    except Exception as e:
        print(f"  ⚠️  注册表生成失败: {e}")

    print("\n下一步:")
    print("  1. 检查 contracts/registry_v2.yaml")
    print("  2. 检查 _contract_extraction_v2/ 下的 JSON 文件")
    print("  3. Celery 任务在 Flower (localhost:5555) 中监控")


if __name__ == '__main__':
    main()
