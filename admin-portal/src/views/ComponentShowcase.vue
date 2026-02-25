<template>
  <div class="component-showcase">
    <!-- 导航栏 -->
    <div class="showcase-header">
      <div class="header-back" @click="goBack">
        <LeftOutlined />
      </div>
      <h1 class="header-title">BehaviorOS 组件库</h1>
      <div class="header-right"></div>
    </div>

    <!-- 三个可选按钮 -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- 组件展示区 -->
    <div class="showcase-content">

      <!-- ========== Tab 1: 健康组件 ========== -->
      <template v-if="activeTab === 'health'">
        <section class="component-section">
          <h2 class="section-title">1. HealthScoreCircle - 健康评分圆环</h2>
          <div class="component-demo">
            <div class="demo-grid">
              <HealthScoreCircle :score="90" :size="120" status-text="状态非常好！" subtitle="连续打卡 14 天" />
              <HealthScoreCircle :score="75" :size="120" status-text="保持得不错" subtitle="继续加油" />
              <HealthScoreCircle :score="55" :size="120" status-text="继续加油" subtitle="距离目标越来越近" />
              <HealthScoreCircle :score="35" :size="120" status-text="需要更多关注" subtitle="每天坚持就有收获" />
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">2. TaskList - 任务列表</h2>
          <div class="component-demo">
            <TaskList :tasks="demoTasks" title="今天要做的事" :show-progress="true" :show-encouragement="true" @toggle="handleTaskToggle" />
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">3. HealthMetricCard - 健康指标卡片</h2>
          <div class="component-demo">
            <div class="metrics-grid">
              <HealthMetricCard icon="🩸" label="血糖" value="6.5" status="good" status-text="正常" trend="↓ 0.3" theme="glucose" />
              <HealthMetricCard icon="⚖️" label="体重" value="72.5" status="good" trend="↓ 0.5kg" theme="weight" />
              <HealthMetricCard icon="🏃" label="运动" value="120" :progress="80" progress-text="本周目标 150 分钟" :show-progress="true" theme="exercise" />
              <HealthMetricCard icon="💊" label="用药" value="2/3" badge="已服用" theme="medication" />
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">4. TrendChart - 趋势图表</h2>
          <div class="component-demo">
            <TrendChart type="line" :data="glucoseData" :labels="weekLabels" title="血糖趋势" subtitle="近7天" icon="🩸" line-color="#ef4444" :show-area="true" :show-dots="true" :show-stats="true" trend-text="平稳下降" trend-direction="down" />
          </div>
          <div class="component-demo" style="margin-top: 16px;">
            <TrendChart type="bar" :data="exerciseData" :labels="weekLabels" title="每日运动" subtitle="分钟数" icon="🏃" bar-color="#10b981" :show-values="true" :show-stats="true" trend-text="运动量稳步提升" trend-direction="up" />
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">5. AchievementBadge - 成就徽章</h2>
          <div class="component-demo">
            <div class="badges-grid">
              <AchievementBadge icon="🏅" name="7天打卡" description="连续记录数据7天" :unlocked="true" unlocked-date="2026-01-20" />
              <AchievementBadge icon="🎯" name="血糖达标" description="连续7天血糖正常" :unlocked="true" unlocked-date="2026-01-25" />
              <AchievementBadge icon="💪" name="运动健将" description="单周运动超150分钟" :unlocked="false" :progress="78" />
              <AchievementBadge icon="⭐" name="减重成功" description="成功减重5kg" :unlocked="false" :progress="45" />
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">6. BigNumberInput - 大号数字输入</h2>
          <div class="component-demo">
            <BigNumberInput v-model="glucoseInput" label="血糖值" subtitle="输入您的血糖测量结果" icon="🩸" unit="mmol/L" :step="0.1" :hint="`您近7天的平均值是 <strong>6.5</strong> mmol/L`" :historical-value="6.8" :quick-values="[5.0, 5.5, 6.0, 6.5, 7.0]" />
          </div>
        </section>
      </template>

      <!-- ========== Tab 2: 行为组件 ========== -->
      <template v-else-if="activeTab === 'behavior'">
        <section class="component-section">
          <h2 class="section-title">1. UserIdentityHeader - 用户身份标识</h2>
          <p class="section-desc">根据行为阶段 (AWARENESS / ACTION / STABILIZATION / RELAPSE) 显示不同的渐变色和文案</p>
          <div class="component-demo">
            <div class="stage-grid">
              <UserIdentityHeader stage="AWARENESS" />
              <UserIdentityHeader stage="ACTION" />
              <UserIdentityHeader stage="STABILIZATION" />
              <UserIdentityHeader stage="RELAPSE" />
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">2. BehaviorTaskCard - 行为任务卡片</h2>
          <p class="section-desc">用户每日行为任务的交互卡片，包含"已完成"和"尝试但未完成"两种反馈路径</p>
          <div class="component-demo">
            <div style="max-width: 420px; margin: 0 auto;">
              <BehaviorTaskCard stage="ACTION" task-name="饭后散步15分钟" @interact="handleBehaviorInteract" />
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">3. CoachEmpathyDashboard - 教练共情仪表板</h2>
          <p class="section-desc">教练视角的双栏布局：左侧镜像用户界面，右侧显示干预决策支持</p>
          <div class="component-demo">
            <CoachEmpathyDashboard :user-data="coachDemoData" />
          </div>
        </section>
      </template>

      <!-- ========== Tab 3: React 组件 ========== -->
      <template v-else-if="activeTab === 'react'">
        <section class="component-section">
          <h2 class="section-title">React 组件导航</h2>
          <p class="section-desc">以下 React 组件通过 ReactBridge 嵌入 Vue 3，点击卡片跳转独立页面</p>
          <div class="react-nav-grid">
            <div class="react-nav-card" @click="router.push('/journey')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #22c55e, #16a34a);">🌱</div>
              <div class="nav-card-info">
                <div class="nav-card-title">JourneyPage</div>
                <div class="nav-card-desc">成长之旅 - 患者行为变化旅程可视化</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/expert/workspace')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #475569, #64748b);">🔬</div>
              <div class="nav-card-info">
                <div class="nav-card-title">ExpertWorkspace</div>
                <div class="nav-card-desc">专家工作台 - 审核队列、决策回溯、规则引擎</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/admin/evolution')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #8b5e3c, #a0522d);">📊</div>
              <div class="nav-card-info">
                <div class="nav-card-title">AdminEvolution</div>
                <div class="nav-card-desc">管理演化视图 - 系统整体运营态势</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/trace')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">🔍</div>
              <div class="nav-card-info">
                <div class="nav-card-title">TracePage</div>
                <div class="nav-card-desc">决策追踪 - AI 决策全链路溯源图谱</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/react/demo')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706);">🧪</div>
              <div class="nav-card-info">
                <div class="nav-card-title">DemoPage</div>
                <div class="nav-card-desc">React 组件 Demo - 所有 React 子组件联合展示</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/client')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #2D7A6E, #34d399);">🏠</div>
              <div class="nav-card-info">
                <div class="nav-card-title">GrowerDashboard</div>
                <div class="nav-card-desc">成长者首页 - 移动端健康仪表盘原型</div>
              </div>
            </div>
            <div class="react-nav-card" @click="router.push('/expert/dual-sign')">
              <div class="nav-card-icon" style="background: linear-gradient(135deg, #1e293b, #475569);">✍️</div>
              <div class="nav-card-info">
                <div class="nav-card-title">DualSignPanel</div>
                <div class="nav-card-desc">双签审批面板 - L5 临床→L6 叙事转换审核</div>
              </div>
            </div>
          </div>
        </section>

        <section class="component-section">
          <h2 class="section-title">Vue Wrappers (7 个)</h2>
          <p class="section-desc">通过 ReactBridge.ts 桥接，每个 React 组件都有对应的 Vue 包装器，可在 Vue 模板中直接使用</p>
          <div class="wrapper-list">
            <div class="wrapper-item" v-for="w in vueWrappers" :key="w.name">
              <code class="wrapper-code">&lt;{{ w.name }} /&gt;</code>
              <span class="wrapper-desc">{{ w.desc }}</span>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
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
import UserIdentityHeader from '@/components/behavior/UserIdentityHeader.vue'
import BehaviorTaskCard from '@/components/behavior/BehaviorTaskCard.vue'
import CoachEmpathyDashboard from '@/components/behavior/CoachEmpathyDashboard.vue'
import type { Stage, CompletionState } from '@/components/core/types'

const router = useRouter()
const activeTab = ref('health')

const tabs = [
  { key: 'health', label: '健康组件', icon: '💚', count: 6 },
  { key: 'behavior', label: '行为组件', icon: '🧠', count: 3 },
  { key: 'react', label: 'React 组件', icon: '⚛️', count: 8 },
]

const goBack = () => {
  router.back()
}

// ===== 健康组件数据 =====
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

// ===== 行为组件数据 =====
const handleBehaviorInteract = (state: CompletionState) => {
}

const coachDemoData = reactive({
  user_id: 'USR-10042',
  stage: 'ACTION' as Stage,
  current_task: '饭后散步15分钟',
  history: [
    { state: 'ATTEMPTED' as CompletionState, date: '2026-02-16' },
    { state: 'DONE' as CompletionState, date: '2026-02-15' },
  ]
})

// ===== React 组件数据 =====
const vueWrappers = [
  { name: 'JourneyPageVue', desc: '成长之旅页面包装器' },
  { name: 'ExpertWorkspaceVue', desc: '专家工作台包装器' },
  { name: 'DualSignPanelVue', desc: '双签审批面板包装器' },
  { name: 'CGMChartVue', desc: 'CGM 图表包装器' },
  { name: 'LogicFlowBridgeVue', desc: '逻辑流桥接器包装器' },
  { name: 'DecisionTraceVue', desc: '决策追踪包装器' },
  { name: 'TraceGraphVue', desc: '追踪图谱包装器' },
]
</script>

<style scoped>
.component-showcase {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 40px;
}

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

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0;
  background: #fff;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 72px;
  z-index: 99;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
  position: relative;
}

.tab-btn:hover {
  color: #059669;
  background: #f0fdf4;
}

.tab-btn.active {
  color: #059669;
  font-weight: 700;
  border-bottom-color: #10b981;
}

.tab-icon {
  font-size: 18px;
}

.tab-count {
  font-size: 12px;
  background: #e5e7eb;
  color: #6b7280;
  padding: 1px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.tab-btn.active .tab-count {
  background: #d1fae5;
  color: #059669;
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

.section-desc {
  font-size: 14px;
  color: #6b7280;
  margin: -12px 0 20px 0;
}

.component-demo {
  margin-bottom: 20px;
}

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

.stage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

/* React Nav Grid */
.react-nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.react-nav-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.react-nav-card:hover {
  border-color: #10b981;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
  transform: translateY(-2px);
}

.nav-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.nav-card-info {
  flex: 1;
  min-width: 0;
}

.nav-card-title {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.nav-card-desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

/* Wrapper List */
.wrapper-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wrapper-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.wrapper-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #059669;
  background: #ecfdf5;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}

.wrapper-desc {
  font-size: 14px;
  color: #64748b;
}

@media (max-width: 768px) {
  .demo-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .metrics-grid,
  .badges-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .stage-grid {
    grid-template-columns: 1fr;
  }
  .react-nav-grid {
    grid-template-columns: 1fr;
  }
}
</style>
