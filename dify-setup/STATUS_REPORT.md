# Dify 系统状态报告

生成时间: 2026-01-26 02:15 (更新)

## 测试结果: 全部通过

---

## 一、系统状态

### 容器服务 (全部正常运行)
| 服务 | 状态 |
|------|------|
| dify-api-1 | Running |
| dify-worker-1 | Running |
| dify-web-1 | Running |
| dify-nginx-1 | Running |
| dify-db-1 | Running (healthy) |
| dify-redis-1 | Running (healthy) |
| dify-weaviate-1 | Running |
| dify-sandbox-1 | Running (healthy) |
| dify-ssrf_proxy-1 | Running |

### Ollama 模型
| 模型 | 大小 |
|------|------|
| qwen2.5:14b | 9.0 GB |
| deepseek-r1:7b | 4.7 GB |
| nomic-embed-text | 274 MB |

### 数据库
- PostgreSQL: 连接正常
- 模型供应商: 55个可用 (包含 Ollama)

---

## 二、配置文件清单

### Dify DSL 配置文件 (位于 D:\behavioral-health-project\dify-setup\)

| 文件名 | 用途 | 模型 | 状态 |
|--------|------|------|------|
| proactive-health-coach.yaml | 主动健康教练 (qwen2.5) | qwen2.5:14b | 完整 |
| proactive-health-coach-deepseek.yaml | 主动健康教练 (deepseek) | deepseek-r1:7b | 完整 |
| proactive-health-balance.yaml | 吃动守恒配置 | - | 参考文档 |
| behavior-health-coach.yaml | 行为健康教练 | - | 备用 |

### 架构文档
| 文件名 | 描述 |
|--------|------|
| D:\behavioral-health-project\architecture.yaml | 系统整体架构 |

---

## 三、访问信息

### Dify 控制台
- **地址**: http://localhost:8080
- **账号**: xiangpingyu@gmail.com
- **密码**: dify123456

### Ollama API
- **地址**: http://localhost:11434
- **Docker内访问**: http://host.docker.internal:11434

---

## 四、配置 Ollama 步骤

1. 登录 Dify 控制台: http://localhost:8080
2. 进入 **设置** (右上角头像) → **模型供应商**
3. 找到 **Ollama** 并点击 **设置**
4. 填写配置:
   - Base URL: `http://host.docker.internal:11434`
   - Model Name: `qwen2.5:14b` 或 `deepseek-r1:7b`
5. 点击保存

---

## 五、导入应用配置

配置好 Ollama 后:

1. 进入 **工作室** → **创建应用** → **导入DSL文件**
2. 选择文件: `D:\behavioral-health-project\dify-setup\proactive-health-coach.yaml`
3. 点击导入

---

## 六、已修复的问题

1. **数据库迁移错误** - 已修复 (flask db stamp)
2. **用户密码问题** - 已重置为 PBKDF2 格式
3. **providers.encrypted_config 缺失** - 已添加列
4. **provider_models.encrypted_config 缺失** - 已添加列
5. **无效的默认模型** - 已清理 langgenius/ollama/ollama 记录

---

## 七、已部署应用

### 主动健康教练
- **App ID**: da2cba0e-7225-4c3c-b891-30fb90812107
- **API Key**: app-TSdoLNkz636aipfD9zTtHdEY
- **模型**: qwen2.5:14b (Ollama)
- **模式**: agent-chat
- **状态**: 正常工作

### 测试验证 (2026-01-26 02:12)
```
问: 什么是吃动守恒？
答: 吃动守恒是一种健康的生活方式理念，旨在通过科学饮食和合理运动达到能量平衡...
```

---

## 八、核心理念

### 吃动守恒
健康的本质是能量平衡:
- **吃**: 科学饮食，合理摄入
- **动**: 规律运动，有效消耗
- **守恒**: 摄入与消耗动态平衡

### 四大健康支柱
1. 科学饮食 - 低GI、均衡营养
2. 合理运动 - 有氧+力量、循序渐进
3. 血糖管理 - 规律监测、波动分析
4. 行为改变 - TTM阶段匹配、动机访谈
