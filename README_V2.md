# BehaviorOS 契约提取脚本 V2.0

## 概述

从代码库静态分析提取 **10类** 契约数据，输出12个结构化JSON文件，供契约注册表V2.0使用。

## V2.0 vs V1.0 对比

| 维度 | V1.0 | V2.0 |
|------|------|------|
| 数据模型 | 2241个混合(ORM+Schema) | 分离: ORM表 + Pydantic Schema + 枚举 |
| 列定义 | 大部分为空 | 完整: 类型/约束/FK/索引/默认值 |
| API端点 | auth全部"unknown" | 提取Depends依赖链,分类权限级别 |
| 配置文件 | 内容为空(读取失败) | 完整JSON内容 |
| 安全管道 | policy_rules为空 | PolicyGate类/方法/规则提取 |
| **新增** Alembic | ❌ | 迁移历史/建表/加列/索引 |
| **新增** 前端 | ❌ | Vue路由+守卫+API服务+Store |
| **新增** 定时任务 | ❌ | Celery/APScheduler/事件总线 |
| **新增** Dify | ❌ | 工作流定义+节点图+集成代码 |

## 运行方式

### 前提条件
- Python 3.8+
- 无需安装任何第三方库(仅使用标准库)
- 在代码库根目录下运行

### 运行

```bash
# 方式1: 在代码库根目录下运行
cd D:\behavioral-health-project
python extract_platform_contracts_v2.py

# 方式2: 指定项目路径
python extract_platform_contracts_v2.py D:\behavioral-health-project
```

### 输出

```
_contract_extraction_v2/
├── 0_project_structure.json    # 项目目录结构
├── 1_data_models.json          # SQLAlchemy ORM + Pydantic Schema (分离)
├── 2_api_endpoints.json        # API端点 + 依赖注入链 + 权限分类
├── 3_agent_registry.json       # 12域Agent + 4专家Agent + 路由规则
├── 4_config_files.json         # 配置文件完整内容
├── 5_tenant_architecture.json  # 多租户模型 + 隔离模式 + Auth链
├── 6_safety_pipeline.json      # PolicyGate规则 + 危机关键词 + 安全函数
├── 7_alembic_migrations.json   # 迁移历史 + 建表/加列操作
├── 8_frontend.json             # Vue路由 + 守卫 + API服务 + 组件
├── 9_scheduled_tasks.json      # Celery任务 + 定时作业 + 事件
├── 10_dify_workflows.json      # Dify工作流定义 + 集成代码
└── SUMMARY.json                # 提取摘要 + 质量检查 + V1对比
```

## 每个模块的输出结构

### 1_data_models.json
```json
{
  "orm_models": [
    {
      "model_name": "User",
      "table_name": "users",
      "has_explicit_tablename": true,
      "columns": [
        {
          "name": "id", "type": "Integer",
          "nullable": true, "primary_key": true,
          "unique": false, "index": false,
          "foreign_key": null, "comment": null
        },
        {
          "name": "coach_id", "type": "Integer",
          "nullable": true, "primary_key": false,
          "foreign_key": "users.id"
        }
      ],
      "relationships": [...],
      "foreign_keys": [{"column": "coach_id", "references": "users.id"}]
    }
  ],
  "pydantic_schemas": [
    {
      "schema_name": "UserCreate",
      "fields": [
        {"name": "phone", "type": "str", "required": true},
        {"name": "agreement_accepted", "type": "bool", "required": false, "default": true}
      ]
    }
  ],
  "enums": [
    {
      "enum_name": "RoleName",
      "members": [{"name": "observer", "value": "observer"}, ...]
    }
  ]
}
```

### 2_api_endpoints.json
```json
{
  "endpoints": [
    {
      "method": "GET",
      "path": "/v1/coach/students",
      "function": "get_students",
      "auth_level": "coach_or_admin",
      "dependencies": [
        {"dependency": "require_coach_or_admin", "role": "coach_or_admin"}
      ],
      "module": "coach",
      "file": "api/coach_api.py"
    }
  ]
}
```

权限级别分类:
- `public` - 无需认证
- `authenticated` - 需登录(get_current_user)
- `coach_or_admin` - 教练或管理员
- `admin_only` - 仅管理员
- `expert_only` - 仅专家
- `role_required` - 指定角色
- `custom` - 自定义依赖

### 7_alembic_migrations.json
```json
{
  "migrations": [
    {
      "revision": "abc002",
      "down_revision": "abc001",
      "message": "add coach fields",
      "operations": {
        "create_table": [],
        "add_column": [
          {"table": "users", "column": "coach_id", "type": "sa.Integer()"}
        ],
        "create_index": [
          {"index": "ix_users_coach_id", "table": "users"}
        ]
      }
    }
  ],
  "migration_chain": ["abc001", "abc002"],
  "tables_created": ["users", "user_points"]
}
```

## 与Claude协作工作流

### 首次使用
1. 运行脚本，生成 `_contract_extraction_v2/`
2. 将整个文件夹打包上传给Claude
3. Claude基于V2数据生成契约注册表V2.0

### 增量更新
1. 代码变更后重新运行脚本
2. 上传新的 `_contract_extraction_v2/` + 当前契约注册表
3. Claude做增量对比，标注变更和冲突

### 建议的长期方案
将此脚本加入CI/CD，每次主分支合并时自动运行，输出JSON存入版本控制。
契约注册表从DOCX迁移到`contracts/registry.yaml`，与代码同步版本管理。

## 注意事项

- 脚本使用静态分析(AST+正则)，不需要运行项目
- 默认排除Dify目录（Dify有1581个模型会干扰统计）
- 默认排除 node_modules、.git、__pycache__ 等
- 配置文件读取支持UTF-8和GBK编码
- 支持JSON中的BOM和单行注释
- 大型配置文件内容截断至50KB
