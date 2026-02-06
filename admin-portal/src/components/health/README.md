# 健康组件库 (Health Components)

统一的健康数据可视化组件库，用于行为健康数字平台。

## 🎨 设计原则

- **绿色主题**: 主色调 `#10b981`，代表健康和成长
- **大号触控**: 最小触摸目标 44px，适合移动端
- **鼓励性**: 正向反馈，温暖的文案
- **简洁层次**: 3层信息架构，避免过度复杂

## 📦 组件清单

### 1. HealthScoreCircle - 健康评分圆环

**用途**: 显示健康总分、单项评分等数值指标

**Props**:
- `score` (number, required): 评分 0-100
- `size` (number): 圆环大小，默认 120
- `strokeWidth` (number): 线条宽度，默认 10
- `unit` (string): 单位，默认 '分'
- `label` (string): 标签文字
- `statusText` (string): 状态文字
- `subtitle` (string): 副标题
- `showInfo` (boolean): 是否显示底部信息
- `colorTheme` ('green' | 'blue' | 'orange' | 'red' | 'auto'): 颜色主题

**示例**:
```vue
<HealthScoreCircle
  :score="82"
  :size="140"
  unit="分"
  label="健康总分"
  status-text="保持得不错"
  subtitle="🔥 连续打卡 7 天"
/>
```

**效果**:
- 自动根据评分选择颜色（90+绿色，70+蓝色，50+橙色，<50红色）
- 响应式字体大小
- 状态标签带颜色背景

---

### 2. TaskList - 任务列表

**用途**: 显示每日任务、待办事项

**Props**:
- `tasks` (Task[], required): 任务列表
- `title` (string): 标题
- `titleIcon` (string): 标题图标
- `showHeader` (boolean): 显示标题栏
- `showProgress` (boolean): 显示完成进度
- `showEncouragement` (boolean): 全部完成时显示鼓励
- `encouragementIcon` (string): 鼓励图标
- `encouragementText` (string): 鼓励文字
- `emptyIcon` (string): 空状态图标
- `emptyText` (string): 空状态文字
- `compact` (boolean): 紧凑模式

**Task 类型**:
```typescript
interface Task {
  id: string | number
  name: string
  completed: boolean
  disabled?: boolean
  hint?: string
  dueTime?: string
  icon?: string
  emoji?: string
  priority?: 'high' | 'medium' | 'low'
}
```

**Events**:
- `@toggle`: 任务状态切换
- `@click`: 任务点击

**示例**:
```vue
<TaskList
  :tasks="tasks"
  title="✨ 今天要做的事"
  :show-progress="true"
  :show-encouragement="true"
  @toggle="handleToggle"
/>
```

---

### 3. HealthMetricCard - 健康指标卡片

**用途**: 显示单个健康指标（血糖、体重等）

**Props**:
- `icon` (string, required): 图标
- `label` (string, required): 标签
- `value` (string | number): 数值
- `status` ('good' | 'normal' | 'warning' | 'danger'): 状态
- `statusText` (string): 状态文字
- `trend` (string): 趋势文字
- `badge` (string): 徽章
- `progress` (number): 进度值
- `progressText` (string): 进度文字
- `showProgress` (boolean): 显示进度条
- `theme` ('glucose' | 'weight' | 'exercise' | 'medication' | 'bp' | 'mood'): 主题
- `clickable` (boolean): 可点击
- `compact` (boolean): 紧凑模式

**Events**:
- `@click`: 卡片点击

**示例**:
```vue
<HealthMetricCard
  icon="🩸"
  label="血糖"
  value="6.5"
  status="good"
  status-text="正常"
  trend="↓ 0.3"
  theme="glucose"
  @click="goToDetail"
/>
```

**主题颜色**:
- glucose: 红色 `#ef4444`
- weight: 紫色 `#8b5cf6`
- exercise: 绿色 `#10b981`
- medication: 橙色 `#f59e0b`
- bp: 粉色 `#ec4899`
- mood: 蓝色 `#3b82f6`

---

### 4. TrendChart - 趋势图表

**用途**: 显示数据趋势（折线图或柱状图）

**Props**:
- `type` ('line' | 'bar', required): 图表类型
- `data` (number[], required): 数据数组
- `labels` (string[]): X轴标签
- `title` (string): 标题
- `subtitle` (string): 副标题
- `icon` (string): 标题图标
- `lineColor` (string): 折线颜色
- `barColor` (string): 柱状图颜色
- `width` (number): 宽度
- `height` (number): 高度
- `showGrid` (boolean): 显示网格
- `showArea` (boolean): 显示面积填充
- `showDots` (boolean): 显示数据点
- `showLabels` (boolean): 显示X轴标签
- `showValues` (boolean): 显示数值
- `showStats` (boolean): 显示统计信息
- `strokeWidth` (number): 线条宽度
- `dotRadius` (number): 数据点半径
- `barRadius` (number): 柱子圆角
- `trendText` (string): 趋势说明
- `trendDirection` ('up' | 'down' | 'stable'): 趋势方向
- `compact` (boolean): 紧凑模式

**Events**:
- `@pointClick`: 数据点点击

**示例 - 折线图**:
```vue
<TrendChart
  type="line"
  :data="[6.8, 6.5, 6.3, 6.7, 6.4, 6.2, 6.5]"
  :labels="['一', '二', '三', '四', '五', '六', '日']"
  title="血糖趋势"
  icon="🩸"
  line-color="#ef4444"
  :show-area="true"
  :show-dots="true"
  trend-text="平稳下降"
  trend-direction="down"
/>
```

**示例 - 柱状图**:
```vue
<TrendChart
  type="bar"
  :data="[30, 25, 35, 20, 30, 40, 0]"
  :labels="['一', '二', '三', '四', '五', '六', '日']"
  title="每日运动"
  icon="🏃"
  bar-color="#10b981"
  :show-values="true"
/>
```

---

### 5. AchievementBadge - 成就徽章

**用途**: 显示成就徽章、奖章

**Props**:
- `icon` (string, required): 徽章图标
- `name` (string, required): 徽章名称
- `description` (string): 描述
- `unlocked` (boolean, required): 是否解锁
- `unlockedDate` (string): 解锁日期
- `progress` (number): 进度（未解锁时）
- `size` ('small' | 'medium' | 'large'): 尺寸
- `showInfo` (boolean): 显示信息
- `showGlow` (boolean): 显示光效
- `compact` (boolean): 紧凑模式
- `clickable` (boolean): 可点击

**Events**:
- `@click`: 徽章点击

**示例**:
```vue
<AchievementBadge
  icon="🏅"
  name="7天打卡"
  description="连续记录数据7天"
  :unlocked="true"
  unlocked-date="2026-01-20"
  size="medium"
  @click="showDetail"
/>
```

**效果**:
- 未解锁: 半透明，显示锁图标和进度条
- 已解锁: 绿色渐变背景，光效动画
- Hover: 图标放大和旋转

---

### 6. BigNumberInput - 大号数字输入

**用途**: 数据录入，大号输入框

**Props**:
- `modelValue` (string | number, required): v-model 绑定值
- `label` (string, required): 标签
- `unit` (string, required): 单位
- `subtitle` (string): 副标题
- `icon` (string): 图标
- `placeholder` (string): 占位符
- `hint` (string): 智能提示（支持HTML）
- `errorMessage` (string): 错误提示
- `historicalValue` (string | number): 历史值
- `quickValues` (number[]): 快速填充值
- `inputType` ('number' | 'text'): 输入类型
- `step` (string | number): 步长
- `min` (string | number): 最小值
- `max` (string | number): 最大值
- `disabled` (boolean): 禁用
- `showDiff` (boolean): 显示差值对比

**Events**:
- `@update:modelValue`: 值变化
- `@focus`: 获得焦点
- `@blur`: 失去焦点

**示例**:
```vue
<BigNumberInput
  v-model="glucoseValue"
  label="血糖值"
  subtitle="输入您的血糖测量结果"
  icon="🩸"
  unit="mmol/L"
  :step="0.1"
  :hint="`您近7天的平均值是 <strong>${average}</strong> mmol/L`"
  :historical-value="6.5"
  :quick-values="[5.0, 5.5, 6.0, 6.5, 7.0]"
/>
```

**效果**:
- 48px 大号数字
- 自动隐藏数字输入的上下箭头
- 智能提示卡片（蓝色渐变）
- 历史值对比（显示增减）
- 快速填充按钮

---

## 🎯 使用方法

### 安装

组件已在项目中，直接导入即可：

```vue
<script setup lang="ts">
import {
  HealthScoreCircle,
  TaskList,
  HealthMetricCard,
  TrendChart,
  AchievementBadge,
  BigNumberInput
} from '@/components/health'
import type { Task } from '@/components/health'
</script>
```

### 完整示例页面

```vue
<template>
  <div class="demo-page">
    <!-- 健康评分 -->
    <HealthScoreCircle
      :score="82"
      :size="140"
      status-text="保持得不错"
      subtitle="🔥 连续打卡 7 天"
    />

    <!-- 任务列表 -->
    <TaskList
      :tasks="tasks"
      @toggle="handleToggle"
    />

    <!-- 健康指标网格 -->
    <div class="metrics-grid">
      <HealthMetricCard
        icon="🩸"
        label="血糖"
        value="6.5"
        status="good"
        status-text="正常"
        theme="glucose"
      />
      <HealthMetricCard
        icon="⚖️"
        label="体重"
        value="72.5"
        status="good"
        trend="↓ 0.5kg"
        theme="weight"
      />
    </div>

    <!-- 趋势图 -->
    <TrendChart
      type="line"
      :data="glucoseData"
      :labels="weekLabels"
      title="血糖趋势"
      icon="🩸"
    />

    <!-- 成就徽章 -->
    <div class="badges-grid">
      <AchievementBadge
        v-for="badge in badges"
        :key="badge.id"
        v-bind="badge"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  HealthScoreCircle,
  TaskList,
  HealthMetricCard,
  TrendChart,
  AchievementBadge
} from '@/components/health'
import type { Task } from '@/components/health'

const tasks = ref<Task[]>([
  { id: 1, name: '记录血糖', completed: false, emoji: '🩸' },
  { id: 2, name: '步行30分钟', completed: false, emoji: '🚶' }
])

const glucoseData = [6.8, 6.5, 6.3, 6.7, 6.4, 6.2, 6.5]
const weekLabels = ['一', '二', '三', '四', '五', '六', '日']

const badges = ref([
  {
    id: 1,
    icon: '🏅',
    name: '7天打卡',
    unlocked: true,
    unlockedDate: '2026-01-20'
  }
])

const handleToggle = (task: Task) => {
  task.completed = !task.completed
}
</script>
```

---

## 🎨 设计规范

### 颜色

```css
/* 主色调 */
--primary-500: #10b981;
--primary-400: #34d399;
--primary-600: #059669;

/* 状态颜色 */
--success: #10b981;
--warning: #f59e0b;
--danger: #ef4444;
--info: #3b82f6;

/* 中性色 */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-500: #6b7280;
--gray-900: #1f2937;
```

### 字体

```css
/* 标题 */
h1: 28px / 700
h2: 24px / 700
h3: 18px / 700

/* 正文 */
body-large: 16px / 500
body: 14px / 400
body-small: 13px / 400
caption: 12px / 400

/* 数字 */
big-number: 48px / 700
metric-value: 28px / 700
score: 32px / 700
```

### 圆角

```css
rounded-sm: 8px
rounded-md: 12px
rounded-lg: 16px
rounded-xl: 20px
rounded-2xl: 32px
```

---

## 📚 相关文档

- [UI/UX 设计指南](../../../../docs/UI_UX_DESIGN_GUIDE.md)
- [Phase B API 集成文档](../../../../docs/PHASE_B_API_INTEGRATION.md)
- [系统架构文档](../../../../docs/SYSTEM_ARCHITECTURE.md)

---

## 🤝 贡献

如需新增组件或修改现有组件，请遵循以下原则：

1. **Props 设计**: 提供合理的默认值，必需 props 尽量少
2. **Events**: 使用 TypeScript 定义 Emits
3. **样式**: 使用 scoped 样式，避免全局污染
4. **响应式**: 支持不同尺寸（size/compact props）
5. **无障碍**: 添加必要的 ARIA 属性
6. **文档**: 更新本 README

---

*最后更新: 2026-02-03*
*组件数量: 6*
