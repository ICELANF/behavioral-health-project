# 行健平台 — 契约注册表信息提取工具 使用指南

## 一、这是什么？

这个工具会自动扫描你的 behavioral-health-project 代码库，提取建立「契约注册表」所需的6类关键信息：

| 编号 | 提取内容 | 输出文件 | 提取什么 |
|------|---------|---------|---------|
| 1 | 数据模型 | 1_data_models.json | SQLAlchemy 模型、字段、外键、关系 |
| 2 | API端点 | 2_api_endpoints.json | 路由路径、方法、权限、所属模块 |
| 3 | Agent注册表 | 3_agent_registry.json | Agent类、domain、关键词、优先级、领域映射 |
| 4 | 配置文件 | 4_config_files.json | JSON/YAML配置内容(积分/里程碑/徽章等) |
| 5 | 多租户架构 | 5_tenant_architecture.json | Tenant模型、隔离模式、RBAC函数 |
| 6 | 安全管道 | 6_safety_pipeline.json | 安全规则、危机关键词、PolicyGate |

## 二、运行方法

### 步骤 1：打开终端

Windows: Win+R → 输入 `cmd` → 回车
或使用 PowerShell / VS Code 终端

### 步骤 2：运行脚本

```bash
# 最简用法 — 只扫描代码
python extract_platform_info.py --project-root D:\behavioral-health-project

# 如果平台正在运行，额外提取运行时信息
python extract_platform_info.py --project-root D:\behavioral-health-project --api-url http://localhost:8000

# 跳过运行时提取（如果平台没在运行）
python extract_platform_info.py --project-root D:\behavioral-health-project --skip-runtime
```

### 步骤 3：查看输出

脚本会在项目根目录创建 `_contract_extraction/` 文件夹：

```
D:\behavioral-health-project\
  └── _contract_extraction/
      ├── SUMMARY.json              ← 先看这个！汇总报告
      ├── 0_project_structure.json  ← 项目目录结构
      ├── 1_data_models.json        ← 数据模型
      ├── 2_api_endpoints.json      ← API端点
      ├── 3_agent_registry.json     ← Agent注册表
      ├── 4_config_files.json       ← 配置文件
      ├── 5_tenant_architecture.json ← 多租户
      ├── 6_safety_pipeline.json    ← 安全管道
      └── 7_runtime_info.json       ← 运行时(可选)
```

## 三、如何把结果给Claude

### 方法A：直接上传文件（推荐）

1. 打开 claude.ai 对话
2. 将 SUMMARY.json 和你感兴趣的具体文件拖入对话
3. 告诉Claude："这是我的平台代码提取结果，请基于此生成契约注册表草稿"

### 方法B：分批上传（如果文件太大）

优先级从高到低：
1. 先上传 `SUMMARY.json` + `1_data_models.json` + `3_agent_registry.json`
2. 再上传 `2_api_endpoints.json` + `4_config_files.json`
3. 最后上传 `5_tenant_architecture.json` + `6_safety_pipeline.json`

### 方法C：如果你在用 Claude Code

```bash
cd D:\behavioral-health-project\_contract_extraction
# Claude Code 可以直接读取这些文件
```

## 四、常见问题

**Q: 脚本报错 "ModuleNotFoundError: No module named 'requests'"**
```bash
pip install requests
# 或者加 --skip-runtime 跳过运行时提取
```

**Q: 提取到的模型/端点数量为0**
可能项目结构与脚本预期不同。检查：
- 项目根目录是否正确？
- Python文件是否在子目录中？
- 尝试指定更具体的路径，如 `--project-root D:\behavioral-health-project\backend`

**Q: 文件太大怎么办？**
4_config_files.json 可能很大（包含完整JSON内容）。
可以只上传 SUMMARY.json，然后告诉Claude你需要哪些具体配置的详情。

**Q: 平台没在运行能用吗？**
可以！加 `--skip-runtime` 即可。
6类核心信息中，只有运行时OpenAPI spec需要平台在线，
其余全部从代码静态分析获取。

## 五、提取后的工作流

```
运行提取脚本
    │
    ▼
上传结果到Claude
    │
    ▼
Claude生成「契约注册表草稿」
  ├── 不变契约层（标注「已确认」或「待确认」）
  ├── 配置契约层（列出所有可配置项）
  └── 实现层边界（定义改动爆炸半径）
    │
    ▼
你Review草稿，确认/修正
    │
    ▼
形成正式版「契约注册表」
    │
    ▼
后续每次迭代：先查注册表 → 判断影响层级 → 精准改动
```
