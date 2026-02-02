# 开发纪事：四层诊断/处方 UI 集成至教练工作台

**日期**: 2026-02-02
**模块**: admin-portal / 教练工作台 (CoachHome)
**变更文件**: `admin-portal/src/views/coach/CoachHome.vue`
**变更类型**: 功能新增（Feature）

---

## 一、变更概述

在教练工作台的学员详情抽屉中，新增 **"诊断评估"** 和 **"行为处方"** 两个 Tab 页，实现四层行为诊断与处方的可视化展示。所有组件基于 Ant Design Vue，与现有 UI 风格统一。

---

## 二、新增功能

### 2.1 诊断评估 Tab（key="diagnosis"）

| 区块 | 内容 | 组件 |
|------|------|------|
| 行为诊断 - 问题/困难/目的 | 问题描述、困难度星级、干预目的 | 自定义 info-box |
| 行为诊断 - 六类原因分析 | 知识不足、技能欠缺、动机不强、环境障碍、信念偏差、习惯惯性 | `a-progress` + `a-tag`（薄弱项标记） |
| 行为诊断 - 心理层次 | 认知层、情绪层、动机层、行为层 | `a-tag` 彩色标签 |
| 行为诊断 - 循证依据 | 近7天餐后血糖均值、饮食打卡完成率、运动执行率 | 状态着色文本 |
| SPI 评估 - 分数圆圈 | SPI 综合评分（72分），三档配色（good/mid/low） | 自定义 spi-circle |
| SPI 评估 - 成功率 | 当前干预成功率 68% | info-box |
| SPI 评估 - 评估公式 | SPI = 0.4×行为执行 + 0.3×指标改善 + 0.2×知识掌握 + 0.1×态度转变 | formula-box |
| SPI 评估 - 干预提醒 | SPI低于80分预警 | `a-alert` warning |

### 2.2 行为处方 Tab（key="prescription"）

| 区块 | 内容 | 组件 |
|------|------|------|
| 当前处方 - 干预阶段 | 评估期→启动期→强化期(当前)→巩固期→维持期 | `a-tag` 状态标签 |
| 当前处方 - 目标行为 | 每餐主食减量1/3(60%)、餐后散步(75%)、血糖监测(85%) | `a-progress` 进度条 |
| 当前处方 - 干预策略 | 动机访谈、行为契约、同伴支持、奖励机制 | `a-tag` 彩色标签 |
| 当前处方 - 操作按钮 | 调整处方、查看历史 | `a-button` |
| AI 诊断建议 | 3条建议卡片，含优先级标签（高优/中优）和采纳/参考按钮 | suggestion-card |

---

## 三、代码变更明细

### 3.1 数据层（script setup）

新增 3 个响应式数据对象：

```
diagnosisData     — SPI评分、六类原因、心理层次、问题-困难-目的、循证依据、干预公式与提醒
prescriptionData  — 干预阶段、目标行为（含进度）、干预策略
aiDiagnosisSuggestions — 3条AI建议（标题、内容、类型、优先级）
```

### 3.2 辅助函数

| 函数 | 用途 |
|------|------|
| `getBarColor(score, max, isWeak)` | 根据分值和薄弱项标记返回进度条颜色 |
| `getDifficultyStars(level)` | 将困难度数值转为 ★☆ 星级字符串 |
| `getTaskColor(rate)` | 根据完成率返回绿/黄/红颜色 |

### 3.3 模板层

在学员详情抽屉 `<a-tabs>` 内，于"干预方案"Tab 之后追加两个 `<a-tab-pane>`：
- `key="diagnosis" tab="诊断评估"` — 双栏网格布局
- `key="prescription" tab="行为处方"` — 双栏网格布局

双栏在 ≤640px 屏幕下自动降级为单栏。

### 3.4 样式层

新增 CSS 类共 30+，主要分组：

| 分组 | 核心类 |
|------|--------|
| 网格布局 | `.dx-grid` |
| 卡片容器 | `.dx-card`, `.dx-card-title`, `.dx-subtitle` |
| SPI 圆圈 | `.spi-circle-wrap`, `.spi-circle`, `.spi-good/mid/low` |
| 柱状条 | `.bar-container`, `.bar-source`, `.bar-label` |
| 信息框 | `.info-box`, `.info-row`, `.formula-box` |
| 循证依据 | `.evidence-list`, `.evidence-item`, `.ev-danger/warning/normal` |
| 心理层次 | `.level-badges` |
| 处方阶段 | `.phase-tags`, `.phase-info` |
| 任务列表 | `.task-list`, `.task-item`, `.task-header`, `.task-target` |
| AI 建议 | `.suggestion-list`, `.suggestion-card`, `.sug-high/medium` |

---

## 四、组件映射（Element Plus → Ant Design Vue）

本次集成将原 CoachStudentDetail.vue（Element Plus）的设计转换为 Ant Design Vue：

| 原组件 (Element Plus) | 实际使用 (Ant Design Vue) |
|---|---|
| `el-card` | `div.dx-card`（自定义样式） |
| `el-progress` | `a-progress` |
| `el-tag` | `a-tag` |
| `el-button` | `a-button` |
| `el-alert` | `a-alert` |
| `el-divider` | `a-divider` |
| `el-tabs / el-tab-pane` | 复用已有 `a-tabs / a-tab-pane` |

---

## 五、验证结果

| 检查项 | 状态 |
|--------|------|
| Vite 编译无报错 | ✅ 通过 |
| 页面正常加载（HTTP 200） | ✅ 通过 |
| 编译产物包含新增模板 | ✅ 通过（grep 确认 dx-grid、spi-circle、诊断评估、行为处方） |
| 登录教练账号 → 学员详情抽屉 | ✅ 通过 |
| "诊断评估"Tab 显示正常 | ✅ 通过（行为诊断卡片 + SPI评估卡片） |
| "行为处方"Tab 显示正常 | ✅ 通过（当前处方卡片 + AI建议卡片） |
| 原有三个Tab（健康数据、跟进记录、干预方案）正常 | ✅ 通过 |
| 移动端响应式（430px 宽度） | ✅ 通过（单栏堆叠） |

验证方式：Playwright 自动化截图（headless Chromium, 430×932 viewport）

---

## 六、截图存档

| 文件 | 描述 |
|------|------|
| `coach_main.png` | 教练工作台主页 |
| `coach_drawer.png` | 学员详情抽屉（健康数据Tab） |
| `coach_diagnosis.png` | 诊断评估Tab（顶部） |
| `coach_diagnosis_scroll.png` | 诊断评估Tab（下滚至循证依据 + SPI） |
| `coach_prescription.png` | 行为处方Tab（顶部） |
| `coach_prescription_scroll.png` | 行为处方Tab（下滚至AI建议） |

---

## 七、后续事项

- [ ] 将 mock 数据替换为后端 API 接口（`/api/diagnosis/{studentId}`, `/api/prescription/{studentId}`）
- [ ] SPI 评估圆圈考虑改用 `a-progress type="circle"` 替代自定义实现
- [ ] AI 诊断建议的"采纳"操作对接后端写入逻辑
- [ ] 添加处方调整的编辑弹窗
- [ ] 六类原因分析数据与评估引擎（L2 Assessment Engine）对接
