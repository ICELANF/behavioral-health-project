# 行为健康数字平台 - v14.1 增量更新变更日志
# CHANGELOG v14.1 (Incremental Update)

## 版本: v14.1.0
## 发布日期: 2026-02-01
## 基础版本: v14.0.0

---

## 一、增量更新概述

本次更新在v14.0基础上新增：
1. **披露控制模块** (disclosure/) - "黑盒评估，白盒干预"
2. **专家审核工作台** (workbench/) - Streamlit界面
3. **四级权限架构** - 患者/教练/专家/管理端分层

```
v14.0.0 (基础版)
 │  ├── 功能开关系统
 │  ├── Trigger事件路由
 │  ├── 节律模型
 │  ├── Agent增强
 │  └── 质量审计
 │
 └─► v14.1.0 (增量更新)
      ├── [NEW] 披露控制模块
      │   ├── 禁词库
      │   ├── 双重签名
      │   ├── AI重写器
      │   └── 章节可见性
      │
      ├── [NEW] 专家审核工作台
      │   └── Streamlit界面
      │
      └── [NEW] 四级权限架构
          ├── 患者端（黑盒）
          ├── 教练端（执图导航）
          ├── 专家端（白盒审核）
          └── 管理端（脱敏统计）
```

---

## 二、新增文件清单

### 2.1 披露控制模块 (disclosure/)

| 文件 | 大小 | 说明 |
|------|------|------|
| `disclosure/__init__.py` | ~4KB | 模块入口 |
| `disclosure/blacklist.py` | ~12KB | 敏感词库管理 |
| `disclosure/signature.py` | ~10KB | 双重签名机制 |
| `disclosure/controller.py` | ~15KB | 披露控制器 |
| `disclosure/rewriter.py` | ~8KB | AI文案重写器 |
| `disclosure/permissions.py` | ~15KB | **[NEW]** 四级权限管理 |
| `disclosure/display_adapter.py` | ~12KB | **[NEW]** 评估展示适配器 |

### 2.2 专家工作台模块 (workbench/)

| 文件 | 说明 |
|------|------|
| `workbench/__init__.py` | 模块入口 |
| `workbench/expert_review.py` | **[NEW]** Streamlit专家审核界面 |

### 2.3 API路由 (api/v14/)

| 文件 | 说明 |
|------|------|
| `api/v14/disclosure_routes.py` | **[NEW]** 披露控制API路由 |

---

## 三、功能详解

### 3.1 禁词库 (Blacklist)

**敏感词分类：**

| 类别 | 示例 | 敏感度 |
|------|------|--------|
| clinical | 抑郁症、焦虑症、人格障碍 | CRITICAL |
| personality | 神经质、低尽责性、缺陷 | HIGH |
| ttm_stage | 无知无觉、强烈抗拒 | MODERATE |
| risk | 高风险、失败风险 | HIGH |
| behavior | 执行力差、意志力薄弱 | MODERATE |

**转换规则：**
```
"高神经质" → "你是一个情感细腻、感受力强的人"
"强烈抗拒阶段" → "正在审视改变的意义"
"执行力差" → "执行力有提升空间，我们可以一起来提高"
```

### 3.2 双重签名机制

**签名规则：**

| 风险等级 | 签名要求 | 超时时间 |
|----------|----------|----------|
| CRITICAL | 双重签名 | 24小时 |
| HIGH | 双重签名 | 48小时 |
| MODERATE | 单签名 | 72小时 |
| LOW | 可自动批准 | - |

### 3.3 章节可见性（17章）

| 章节 | 患者 | 教练 | 专家 | 说明 |
|------|------|------|------|------|
| core_profile | ✅ | ✅ | ✅ | 核心画像 |
| big5_summary | ❌ | ✅ | ✅ | 人格摘要 |
| big5_detail | ❌ | ❌ | ✅ | 人格详情 |
| mental_health | ❌ | ❌ | ✅ | 心理健康风险 |
| action_tasks | ✅ | ✅ | ✅ | 行动任务 |
| expert_notes | ❌ | ❌ | ✅ | 专家备注 |

### 3.4 四级权限架构

```
┌─────────────────────────────────────────────────────────────┐
│                     评估数据流                               │
│                                                              │
│  患者端(C端)        教练端(B端)        专家端        管理端   │
│  ┌─────────┐     ┌──────────┐    ┌─────────┐  ┌─────────┐  │
│  │ 只做问卷  │────→│ 看到结果   │───→│ 审核确认  │  │ 脱敏统计 │  │
│  │ 不看结果  │     │ 执行干预   │    │ 最终定论  │  │ 规则配置 │  │
│  │ 正向引导  │←────│ 推送建议   │←───│ 策略指导  │  │         │  │
│  └─────────┘     └──────────┘    └─────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、新增API端点

### 4.1 披露控制API (/api/v2/disclosure/)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/decision/create` | POST | 创建披露决策 |
| `/decision/{report_id}` | GET | 获取披露决策 |
| `/decision/{report_id}/sign` | POST | 签名 |
| `/decision/{report_id}/approve` | POST | 批准披露 |
| `/decision/{report_id}/reject` | POST | 驳回披露 |
| `/decision/{report_id}/chapter` | POST | 设置章节可见性 |
| `/decision/{report_id}/rewrite` | POST | 添加内容重写 |
| `/chapters` | GET | 获取章节列表 |
| `/blacklist` | GET | 获取禁词库 |
| `/blacklist/check` | POST | 检查敏感词 |
| `/blacklist/auto-replace` | POST | 自动替换敏感词 |
| `/rewrite` | POST | AI重写文本 |
| `/rewrite/assessment` | POST | 重写评估摘要 |
| `/pending` | GET | 待审核列表 |

---

## 五、专家审核工作台

### 5.1 启动方式

```bash
# 安装Streamlit（如果未安装）
pip install streamlit

# 启动专家审核界面
streamlit run workbench/expert_review.py --server.port 8501
```

### 5.2 界面功能

1. **任务队列** - 风险导向排序
2. **三栏布局** - 原始数据 | AI建议 | 披露决策
3. **实时检测** - 敏感词波浪线标记
4. **章节控制** - 17个章节可见性开关
5. **双重签名** - 主审+督导确认

---

## 六、新增功能开关

```python
# core/v14/config.py
ENABLE_DISCLOSURE_CONTROL: bool = False       # 披露控制总开关
ENABLE_BLACKLIST_FILTER: bool = True          # 禁词过滤
ENABLE_DUAL_SIGNATURE: bool = True            # 双重签名
ENABLE_AI_REWRITER: bool = True               # AI重写器
DISCLOSURE_AUTO_APPROVE_LOW_RISK: bool = True # 低风险自动批准
```

---

## 七、使用示例

### 7.1 检查敏感词

```bash
curl -X POST "http://localhost:8002/api/v2/disclosure/blacklist/check" \
  -H "Content-Type: application/json" \
  -d '{"text": "用户高神经质，处于抗拒阶段", "min_level": "moderate"}'
```

### 7.2 AI重写

```bash
curl -X POST "http://localhost:8002/api/v2/disclosure/rewrite" \
  -H "Content-Type: application/json" \
  -d '{"text": "用户高神经质，执行力差"}'
```

### 7.3 创建披露决策

```bash
curl -X POST "http://localhost:8002/api/v2/disclosure/decision/create" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "RPT_001",
    "user_id": 1001,
    "risk_level": "high",
    "initial_content": "评估报告内容..."
  }'
```

---

*文档版本: 1.0 | 构建时间: 2026-02-01*
