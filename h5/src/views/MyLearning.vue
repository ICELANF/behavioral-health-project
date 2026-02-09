<!--
  我的学习页面 — 学习统计 + 进度里程碑 + 学习记录
  路由: /my-learning
-->
<template>
  <div class="page-container">
    <van-nav-bar
      title="我的学习"
      left-arrow
      @click-left="router.back()"
    />

    <div class="page-content my-learning-page">
      <van-loading v-if="loading" class="learning-loading" size="24px" vertical>
        加载中...
      </van-loading>

      <template v-else>
        <!-- 学习统计卡片 -->
        <div class="stats-row">
          <div class="stat-card card">
            <div class="stat-icon">
              <van-icon name="clock-o" size="24" color="#1989fa" />
            </div>
            <div class="stat-value">{{ stats.totalMinutes }}</div>
            <div class="stat-label">学习分钟</div>
          </div>
          <div class="stat-card card">
            <div class="stat-icon">
              <van-icon name="gem-o" size="24" color="#ff976a" />
            </div>
            <div class="stat-value">{{ stats.totalPoints }}</div>
            <div class="stat-label">积累积分</div>
          </div>
          <div class="stat-card card">
            <div class="stat-icon">
              <van-icon name="fire-o" size="24" color="#ee0a24" />
            </div>
            <div class="stat-value">{{ stats.streakDays }}</div>
            <div class="stat-label">连续天数</div>
          </div>
        </div>

        <!-- 下一个里程碑 -->
        <div class="milestone-card card">
          <div class="milestone-header">
            <h3>下一个里程碑</h3>
            <van-tag type="primary" round size="medium">
              Lv.{{ stats.currentLevel }}
            </van-tag>
          </div>
          <div class="milestone-info">
            <span class="milestone-current">{{ stats.totalPoints }} 分</span>
            <span class="milestone-target">/ {{ nextMilestone }} 分</span>
          </div>
          <van-progress
            :percentage="milestoneProgress"
            :stroke-width="8"
            color="linear-gradient(to right, #1989fa, #07c160)"
            track-color="#ebedf0"
            :show-pivot="true"
            :pivot-text="milestoneProgress + '%'"
          />
          <div class="milestone-hint">
            再获得 {{ nextMilestone - stats.totalPoints }} 分即可升级
          </div>
        </div>

        <!-- 本周学习时长 -->
        <div class="weekly-card card">
          <h3>本周学习</h3>
          <div class="weekly-bar-chart">
            <div
              v-for="(day, index) in weeklyData"
              :key="index"
              class="bar-col"
            >
              <div class="bar-wrapper">
                <div
                  class="bar-fill"
                  :style="{ height: barHeight(day.minutes) }"
                ></div>
              </div>
              <span class="bar-label">{{ day.label }}</span>
            </div>
          </div>
        </div>

        <!-- 最近学习记录 -->
        <div class="records-card card">
          <h3>最近学习记录</h3>

          <van-empty v-if="records.length === 0" description="暂无学习记录" image="search" />

          <div v-else class="record-list">
            <div
              v-for="record in records"
              :key="record.id"
              class="record-item"
            >
              <div class="record-icon">
                <van-icon :name="recordIcon(record.type)" size="20" :color="recordColor(record.type)" />
              </div>
              <div class="record-info">
                <div class="record-title">{{ record.title }}</div>
                <div class="record-detail">
                  <span v-if="record.duration">{{ record.duration }}分钟</span>
                  <span v-if="record.duration && record.points" class="record-dot"></span>
                  <span v-if="record.points">+{{ record.points }}积分</span>
                  <span v-if="!record.duration && !record.points">学习记录</span>
                </div>
              </div>
              <div class="record-time">{{ formatDate(record.completed_at) }}</div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)

const stats = ref({
  totalMinutes: 0,
  totalPoints: 0,
  streakDays: 0,
  currentLevel: 1
})

const records = ref<any[]>([])

// 本周数据
const weeklyData = ref([
  { label: '一', minutes: 0 },
  { label: '二', minutes: 0 },
  { label: '三', minutes: 0 },
  { label: '四', minutes: 0 },
  { label: '五', minutes: 0 },
  { label: '六', minutes: 0 },
  { label: '日', minutes: 0 }
])

// 里程碑进度
const milestones = [100, 300, 600, 1000, 1800, 3000, 5000, 10000]

const nextMilestone = computed(() => {
  const pts = stats.value.totalPoints
  for (const m of milestones) {
    if (pts < m) return m
  }
  return milestones[milestones.length - 1]
})

const milestoneProgress = computed(() => {
  const pts = stats.value.totalPoints
  const target = nextMilestone.value
  // 找到上一个里程碑
  let prev = 0
  for (const m of milestones) {
    if (pts < m) break
    prev = m
  }
  const range = target - prev
  if (range <= 0) return 100
  return Math.min(100, Math.round(((pts - prev) / range) * 100))
})

// 柱状图高度
function barHeight(minutes: number): string {
  const max = Math.max(...weeklyData.value.map(d => d.minutes), 1)
  return Math.round((minutes / max) * 80) + 'px'
}

// 记录图标
function recordIcon(type: string): string {
  const map: Record<string, string> = {
    article: 'description',
    video: 'video-o',
    course: 'bookmark-o',
    assessment: 'todo-list-o'
  }
  return map[type] || 'records-o'
}

function recordColor(type: string): string {
  const map: Record<string, string> = {
    article: '#1989fa',
    video: '#7c3aed',
    course: '#10b981',
    assessment: '#ff976a'
  }
  return map[type] || '#969799'
}

function formatDate(time: string): string {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

// 计算简单等级（基于积分里程碑）
function computeLevel(totalPoints: number): number {
  const thresholds = [100, 300, 600, 1000, 1800, 3000, 5000, 10000]
  let level = 1
  for (const t of thresholds) {
    if (totalPoints >= t) level++
    else break
  }
  return level
}

// 加载学习统计
async function loadStats() {
  loading.value = true
  try {
    const userId = userStore.userId

    // 计算本周一日期
    const now = new Date()
    const dayOfWeek = now.getDay()
    const monday = new Date(now)
    monday.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))
    const mondayStr = monday.toISOString().split('T')[0]

    // 并行请求：统计 + 本周时长记录 + 积分记录
    const [statsRes, weekHistoryRes, pointsHistoryRes]: any[] = await Promise.all([
      api.get(`/api/v1/learning/grower/stats/${userId}`),
      api.get(`/api/v1/learning/grower/time/${userId}/history`, {
        params: { start_date: mondayStr, page_size: 100 }
      }).catch(() => null),
      api.get(`/api/v1/learning/coach/points/${userId}/history`, {
        params: { page_size: 10 }
      }).catch(() => null),
    ])

    // 映射嵌套响应结构
    if (statsRes) {
      const lt = statsRes.learning_time || {}
      const lp = statsRes.learning_points || {}
      const streak = statsRes.streak || {}

      stats.value = {
        totalMinutes: lt.total_minutes || 0,
        totalPoints: lp.total_points || 0,
        streakDays: streak.current_streak || 0,
        currentLevel: computeLevel(lp.total_points || 0),
      }
    }

    // 本周学习柱状图
    if (weekHistoryRes?.items) {
      const dailyMinutes = [0, 0, 0, 0, 0, 0, 0]
      for (const item of weekHistoryRes.items) {
        if (!item.earned_at) continue
        const d = new Date(item.earned_at)
        const dayIndex = (d.getDay() + 6) % 7 // Mon=0, Sun=6
        dailyMinutes[dayIndex] += item.minutes || 0
      }
      const days = ['一', '二', '三', '四', '五', '六', '日']
      weeklyData.value = days.map((label, i) => ({
        label,
        minutes: dailyMinutes[i],
      }))
    }

    // 最近学习记录（积分日志）
    if (pointsHistoryRes?.items) {
      records.value = pointsHistoryRes.items.map((item: any) => ({
        id: item.record_id,
        title: item.source_title || item.source_type || '学习',
        type: item.source_type === 'quiz' ? 'assessment' : 'article',
        duration: 0,
        points: item.points || 0,
        completed_at: item.earned_at,
      }))
    }
  } catch (err) {
    console.error('加载学习统计失败:', err)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.learning-loading {
  padding: 80px 0;
}

.stats-row {
  display: flex;
  gap: 10px;
  margin-bottom: $spacing-md;

  .stat-card {
    flex: 1;
    text-align: center;
    padding: 14px 8px;
    margin-bottom: 0;
  }

  .stat-icon {
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: $text-color;
    line-height: 1;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }
}

.milestone-card {
  .milestone-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-sm;

    h3 {
      font-size: $font-size-lg;
    }
  }

  .milestone-info {
    margin-bottom: $spacing-xs;
    font-size: $font-size-sm;
  }

  .milestone-current {
    font-weight: 600;
    color: $primary-color;
  }

  .milestone-target {
    color: $text-color-secondary;
  }

  .milestone-hint {
    margin-top: $spacing-xs;
    font-size: $font-size-xs;
    color: $text-color-secondary;
    text-align: center;
  }
}

.weekly-card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-md;
  }

  .weekly-bar-chart {
    display: flex;
    justify-content: space-around;
    align-items: flex-end;
    height: 120px;
    padding: 0 4px;
  }

  .bar-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
  }

  .bar-wrapper {
    width: 20px;
    height: 80px;
    background: #f0f2f5;
    border-radius: 10px;
    display: flex;
    align-items: flex-end;
    overflow: hidden;
  }

  .bar-fill {
    width: 100%;
    background: linear-gradient(to top, #1989fa, #36d1dc);
    border-radius: 10px;
    transition: height 0.3s ease;
    min-height: 4px;
  }

  .bar-label {
    margin-top: 8px;
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }
}

.records-card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }
}

.record-list {
  .record-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid $border-color;

    &:last-child {
      border-bottom: none;
    }
  }

  .record-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #f7f8fa;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .record-info {
    flex: 1;
    min-width: 0;
  }

  .record-title {
    font-size: $font-size-md;
    font-weight: 500;
    color: $text-color;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 2px;
  }

  .record-detail {
    font-size: $font-size-xs;
    color: $text-color-secondary;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .record-dot {
    width: 3px;
    height: 3px;
    background: $text-color-placeholder;
    border-radius: 50%;
  }

  .record-time {
    font-size: $font-size-xs;
    color: $text-color-placeholder;
    flex-shrink: 0;
  }
}
</style>
