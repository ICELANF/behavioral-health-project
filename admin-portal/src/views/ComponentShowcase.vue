<template>
  <div class="component-showcase">
    <!-- 导航栏 -->
    <div class="showcase-header">
      <div class="header-back" @click="goBack">
        <LeftOutlined />
      </div>
      <h1 class="header-title">健康组件库展示</h1>
      <div class="header-right"></div>
    </div>

    <!-- 组件展示区 -->
    <div class="showcase-content">
      <!-- 1. HealthScoreCircle -->
      <section class="component-section">
        <h2 class="section-title">1. HealthScoreCircle - 健康评分圆环</h2>
        <div class="component-demo">
          <div class="demo-grid">
            <HealthScoreCircle
              :score="90"
              :size="120"
              status-text="状态非常好！"
              subtitle="🔥 连续打卡 14 天"
            />
            <HealthScoreCircle
              :score="75"
              :size="120"
              status-text="保持得不错"
              subtitle="继续加油"
            />
            <HealthScoreCircle
              :score="55"
              :size="120"
              status-text="继续加油"
              subtitle="距离目标越来越近"
            />
            <HealthScoreCircle
              :score="35"
              :size="120"
              status-text="需要更多关注"
              subtitle="每天坚持就有收获"
            />
          </div>
        </div>
        <div class="code-example">
          <pre><code>&lt;HealthScoreCircle
  :score="82"
  :size="140"
  status-text="保持得不错"
  subtitle="🔥 连续打卡 7 天"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 2. TaskList -->
      <section class="component-section">
        <h2 class="section-title">2. TaskList - 任务列表</h2>
        <div class="component-demo">
          <TaskList
            :tasks="demoTasks"
            title="✨ 今天要做的事"
            :show-progress="true"
            :show-encouragement="true"
            @toggle="handleTaskToggle"
          />
        </div>
        <div class="code-example">
          <pre><code>&lt;TaskList
  :tasks="tasks"
  title="✨ 今天要做的事"
  :show-progress="true"
  @toggle="handleToggle"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 3. HealthMetricCard -->
      <section class="component-section">
        <h2 class="section-title">3. HealthMetricCard - 健康指标卡片</h2>
        <div class="component-demo">
          <div class="metrics-grid">
            <HealthMetricCard
              icon="🩸"
              label="血糖"
              value="6.5"
              status="good"
              status-text="正常"
              trend="↓ 0.3"
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
            <HealthMetricCard
              icon="🏃"
              label="运动"
              value="120"
              :progress="80"
              progress-text="本周目标 150 分钟"
              :show-progress="true"
              theme="exercise"
            />
            <HealthMetricCard
              icon="💊"
              label="用药"
              value="2/3"
              badge="已服用"
              theme="medication"
            />
          </div>
        </div>
        <div class="code-example">
          <pre><code>&lt;HealthMetricCard
  icon="🩸"
  label="血糖"
  value="6.5"
  status="good"
  status-text="正常"
  trend="↓ 0.3"
  theme="glucose"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 4. TrendChart - 折线图 -->
      <section class="component-section">
        <h2 class="section-title">4. TrendChart - 趋势图表（折线图）</h2>
        <div class="component-demo">
          <TrendChart
            type="line"
            :data="glucoseData"
            :labels="weekLabels"
            title="血糖趋势"
            subtitle="近7天"
            icon="🩸"
            line-color="#ef4444"
            :show-area="true"
            :show-dots="true"
            :show-stats="true"
            trend-text="平稳下降"
            trend-direction="down"
          />
        </div>
        <div class="code-example">
          <pre><code>&lt;TrendChart
  type="line"
  :data="[6.8, 6.5, 6.3, 6.7, 6.4, 6.2, 6.5]"
  :labels="['一', '二', '三', '四', '五', '六', '日']"
  title="血糖趋势"
  icon="🩸"
  line-color="#ef4444"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 5. TrendChart - 柱状图 -->
      <section class="component-section">
        <h2 class="section-title">5. TrendChart - 趋势图表（柱状图）</h2>
        <div class="component-demo">
          <TrendChart
            type="bar"
            :data="exerciseData"
            :labels="weekLabels"
            title="每日运动"
            subtitle="分钟数"
            icon="🏃"
            bar-color="#10b981"
            :show-values="true"
            :show-stats="true"
            trend-text="运动量稳步提升"
            trend-direction="up"
          />
        </div>
        <div class="code-example">
          <pre><code>&lt;TrendChart
  type="bar"
  :data="[30, 25, 35, 20, 30, 40, 0]"
  :labels="['一', '二', '三', '四', '五', '六', '日']"
  title="每日运动"
  icon="🏃"
  bar-color="#10b981"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 6. AchievementBadge -->
      <section class="component-section">
        <h2 class="section-title">6. AchievementBadge - 成就徽章</h2>
        <div class="component-demo">
          <div class="badges-grid">
            <AchievementBadge
              icon="🏅"
              name="7天打卡"
              description="连续记录数据7天"
              :unlocked="true"
              unlocked-date="2026-01-20"
            />
            <AchievementBadge
              icon="🎯"
              name="血糖达标"
              description="连续7天血糖正常"
              :unlocked="true"
              unlocked-date="2026-01-25"
            />
            <AchievementBadge
              icon="💪"
              name="运动健将"
              description="单周运动超150分钟"
              :unlocked="false"
              :progress="78"
            />
            <AchievementBadge
              icon="⭐"
              name="减重成功"
              description="成功减重5kg"
              :unlocked="false"
              :progress="45"
            />
          </div>
        </div>
        <div class="code-example">
          <pre><code>&lt;AchievementBadge
  icon="🏅"
  name="7天打卡"
  description="连续记录数据7天"
  :unlocked="true"
  unlocked-date="2026-01-20"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 7. BigNumberInput -->
      <section class="component-section">
        <h2 class="section-title">7. BigNumberInput - 大号数字输入</h2>
        <div class="component-demo">
          <BigNumberInput
            v-model="glucoseInput"
            label="血糖值"
            subtitle="输入您的血糖测量结果"
            icon="🩸"
            unit="mmol/L"
            :step="0.1"
            :hint="`您近7天的平均值是 <strong>6.5</strong> mmol/L`"
            :historical-value="6.8"
            :quick-values="[5.0, 5.5, 6.0, 6.5, 7.0]"
          />
        </div>
        <div class="code-example">
          <pre><code>&lt;BigNumberInput
  v-model="glucoseValue"
  label="血糖值"
  icon="🩸"
  unit="mmol/L"
  :step="0.1"
  :hint="\`您近7天的平均值是 &lt;strong&gt;${average}&lt;/strong&gt; mmol/L\`"
  :historical-value="6.5"
/&gt;</code></pre>
        </div>
      </section>

      <!-- 尺寸对比 -->
      <section class="component-section">
        <h2 class="section-title">8. 尺寸对比</h2>
        <div class="component-demo">
          <h3 class="demo-subtitle">HealthScoreCircle 尺寸</h3>
          <div class="size-demo">
            <HealthScoreCircle :score="82" :size="80" label="小" />
            <HealthScoreCircle :score="82" :size="120" label="中" />
            <HealthScoreCircle :score="82" :size="160" label="大" />
          </div>

          <h3 class="demo-subtitle">AchievementBadge 尺寸</h3>
          <div class="size-demo">
            <AchievementBadge
              icon="🏅"
              name="小徽章"
              :unlocked="true"
              size="small"
            />
            <AchievementBadge
              icon="🏅"
              name="中徽章"
              :unlocked="true"
              size="medium"
            />
            <AchievementBadge
              icon="🏅"
              name="大徽章"
              :unlocked="true"
              size="large"
            />
          </div>
        </div>
      </section>

      <!-- 主题对比 -->
      <section class="component-section">
        <h2 class="section-title">9. 主题对比</h2>
        <div class="component-demo">
          <div class="metrics-grid">
            <HealthMetricCard icon="🩸" label="血糖" value="6.5" theme="glucose" />
            <HealthMetricCard icon="⚖️" label="体重" value="72" theme="weight" />
            <HealthMetricCard icon="🏃" label="运动" value="30" theme="exercise" />
            <HealthMetricCard icon="💊" label="用药" value="3" theme="medication" />
            <HealthMetricCard icon="💓" label="血压" value="120" theme="bp" />
            <HealthMetricCard icon="😊" label="心情" value="4.5" theme="mood" />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { LeftOutlined } from '@ant-design/icons-vue'
import {
  HealthScoreCircle,
  TaskList,
  HealthMetricCard,
  TrendChart,
  AchievementBadge,
  BigNumberInput
} from '@/components/health'
import type { Task } from '@/components/health'

const router = useRouter()

const goBack = () => {
  router.back()
}

// 示例数据
const demoTasks = ref<Task[]>([
  { id: 1, name: '早餐后测血糖', hint: '建议在餐后2小时测量', emoji: '🩸', completed: false },
  { id: 2, name: '步行30分钟', hint: '可以分成两次完成', emoji: '🚶', completed: false },
  { id: 3, name: '晚上8点用药', hint: '记得饭后服用', emoji: '💊', completed: true }
])

const glucoseData = [6.8, 6.5, 6.3, 6.7, 6.4, 6.2, 6.5]
const exerciseData = [30, 25, 35, 20, 30, 40, 0]
const weekLabels = ['一', '二', '三', '四', '五', '六', '日']

const glucoseInput = ref('6.5')

const handleTaskToggle = (task: Task) => {
  task.completed = !task.completed
}
</script>

<style scoped>
.component-showcase {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 40px;
}

/* 导航栏 */
.showcase-header {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-back {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.2s;
}

.header-back:hover {
  background: rgba(255, 255, 255, 0.2);
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.header-right {
  width: 40px;
}

/* 内容区 */
.showcase-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}

.component-section {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.demo-subtitle {
  font-size: 16px;
  font-weight: 600;
  color: #4b5563;
  margin: 24px 0 16px 0;
}

.component-demo {
  margin-bottom: 20px;
}

/* 网格布局 */
.demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 20px;
  justify-items: center;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.size-demo {
  display: flex;
  gap: 32px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

/* 代码示例 */
.code-example {
  background: #1f2937;
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
}

.code-example pre {
  margin: 0;
}

.code-example code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #10b981;
}

/* 响应式 */
@media (max-width: 768px) {
  .demo-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .metrics-grid,
  .badges-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .size-demo {
    gap: 20px;
  }
}
</style>
