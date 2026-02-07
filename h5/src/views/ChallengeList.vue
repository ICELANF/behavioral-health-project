<template>
  <div class="page-container">
    <van-nav-bar title="我的挑战" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-pull-refresh v-model="refreshing" @refresh="loadEnrollments">
        <van-loading v-if="loading && !refreshing" class="loading" />

        <template v-if="enrollments.length > 0">
          <!-- 进行中 -->
          <div v-if="activeList.length > 0" class="section">
            <div class="section-title">进行中</div>
            <div
              v-for="enrollment in activeList"
              :key="enrollment.id"
              class="enrollment-card card"
              @click="goToDay(enrollment)"
            >
              <div class="enrollment-header">
                <div class="enrollment-title">{{ enrollment.challenge_title }}</div>
                <van-tag type="primary" size="small" round>进行中</van-tag>
              </div>

              <div class="enrollment-progress">
                <div class="progress-info">
                  <span class="progress-day">
                    第 {{ enrollment.current_day || 0 }} 天 / 共 {{ enrollment.duration_days || 0 }} 天
                  </span>
                  <span v-if="enrollment.streak_days && enrollment.streak_days > 0" class="streak-badge-inline">
                    <van-icon name="fire-o" color="#fa8c16" size="14" />
                    {{ enrollment.streak_days }}天连续
                  </span>
                </div>
                <van-progress
                  :percentage="calcProgress(enrollment)"
                  stroke-width="8"
                  color="#1989fa"
                  track-color="#f0f0f0"
                  :show-pivot="false"
                />
              </div>

              <div class="enrollment-footer">
                <span class="enrollment-date" v-if="enrollment.started_at">
                  {{ formatDate(enrollment.started_at) }} 开始
                </span>
                <van-icon name="arrow" color="#c8c9cc" />
              </div>
            </div>
          </div>

          <!-- 待开始（教练刚分配） -->
          <div v-if="enrolledList.length > 0" class="section">
            <div class="section-title">待开始</div>
            <div
              v-for="enrollment in enrolledList"
              :key="enrollment.id"
              class="enrollment-card card"
            >
              <div class="enrollment-header">
                <div class="enrollment-title">{{ enrollment.challenge_title }}</div>
                <van-tag type="warning" size="small" round>待开始</van-tag>
              </div>

              <div class="enrollment-desc" v-if="enrollment.challenge_category">
                <van-tag
                  :type="categoryTagType(enrollment.challenge_category)"
                  size="medium"
                  round
                >
                  {{ categoryLabel(enrollment.challenge_category) }}
                </van-tag>
                <span class="duration-text">{{ enrollment.duration_days || 0 }}天</span>
              </div>

              <div class="enrollment-footer">
                <span class="enrollment-date">
                  {{ formatDate(enrollment.enrolled_at) }} 分配
                </span>
                <van-button
                  type="success"
                  size="small"
                  round
                  :loading="startingId === enrollment.id"
                  @click.stop="handleStart(enrollment)"
                >
                  开始挑战
                </van-button>
              </div>
            </div>
          </div>

          <!-- 已完成 -->
          <div v-if="completedList.length > 0" class="section">
            <div class="section-title">已完成</div>
            <div
              v-for="enrollment in completedList"
              :key="enrollment.id"
              class="enrollment-card card completed-card"
              @click="goToDay(enrollment)"
            >
              <div class="enrollment-header">
                <div class="enrollment-title">{{ enrollment.challenge_title }}</div>
                <van-tag type="success" size="small" round>已完成</van-tag>
              </div>

              <div class="enrollment-footer">
                <span class="enrollment-date" v-if="enrollment.completed_at">
                  {{ formatDate(enrollment.completed_at) }} 完成
                </span>
                <van-icon name="arrow" color="#c8c9cc" />
              </div>
            </div>
          </div>
        </template>

        <van-empty
          v-if="!loading && enrollments.length === 0"
          description="暂无挑战任务"
          image="default"
        >
          <template #description>
            <p style="color: #969799; font-size: 14px;">
              教练会为你分配适合的挑战计划
            </p>
          </template>
        </van-empty>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import api from '@/api/index'

interface Enrollment {
  id: number
  challenge_id?: number
  challenge_title?: string
  challenge_category?: string
  status: string
  current_day?: number
  duration_days?: number
  streak_days?: number
  started_at?: string
  completed_at?: string
  enrolled_at?: string
}

const router = useRouter()

const loading = ref(false)
const refreshing = ref(false)
const enrollments = ref<Enrollment[]>([])
const startingId = ref<number | null>(null)

// 按状态分组
const activeList = computed(() =>
  enrollments.value.filter(e => e.status === 'active' || e.status === 'in_progress')
)
const enrolledList = computed(() =>
  enrollments.value.filter(e => e.status === 'enrolled')
)
const completedList = computed(() =>
  enrollments.value.filter(e => e.status === 'completed')
)

function categoryLabel(category?: string): string {
  const map: Record<string, string> = {
    nutrition: '营养', exercise: '运动', sleep: '睡眠',
    emotion: '情绪', stress: '压力', mindfulness: '正念',
    social: '社交', cognitive: '认知', comprehensive: '综合',
  }
  return map[category || ''] || category || '综合'
}

function categoryTagType(category?: string): string {
  const map: Record<string, string> = {
    nutrition: 'success', exercise: 'warning', sleep: 'primary',
    emotion: 'danger', stress: 'primary', mindfulness: 'success',
    social: 'primary', cognitive: 'warning', comprehensive: 'default',
  }
  return map[category || ''] || 'default'
}

function calcProgress(enrollment: Enrollment): number {
  const current = enrollment.current_day || 0
  const total = enrollment.duration_days || 1
  if (enrollment.status === 'completed') return 100
  return Math.min(100, Math.round((current / total) * 100))
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = d.getMonth() + 1
  const day = d.getDate()
  return `${month}月${day}日`
}

function goToDay(enrollment: Enrollment) {
  if (enrollment.status === 'enrolled') return
  router.push(`/challenge-day/${enrollment.id}`)
}

async function loadEnrollments() {
  loading.value = true
  try {
    const res: any = await api.get('/api/v1/challenges/my-enrollments')
    enrollments.value = res.items || res.enrollments || res || []
  } catch {
    enrollments.value = []
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function handleStart(enrollment: Enrollment) {
  startingId.value = enrollment.id
  try {
    await api.post(`/api/v1/challenges/enrollments/${enrollment.id}/start`)
    showSuccessToast('挑战开始!')
    await loadEnrollments()
    router.push(`/challenge-day/${enrollment.id}`)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || '开始失败'
    showToast(msg)
  } finally {
    startingId.value = null
  }
}

onMounted(() => {
  loadEnrollments()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading {
  text-align: center;
  padding: 60px 0;
}

.section {
  margin-bottom: $spacing-md;

  .section-title {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    font-weight: 500;
    padding: $spacing-xs 0;
    margin-bottom: $spacing-xs;
  }
}

.enrollment-card {
  cursor: pointer;
  transition: transform 0.15s;

  &:active {
    transform: scale(0.98);
  }

  &.completed-card {
    opacity: 0.75;
  }

  .enrollment-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-sm;
  }

  .enrollment-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-color;
    flex: 1;
    margin-right: $spacing-xs;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .enrollment-desc {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-sm;

    .duration-text {
      font-size: $font-size-sm;
      color: $text-color-secondary;
    }
  }

  .enrollment-progress {
    margin-bottom: $spacing-sm;

    .progress-info {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }

    .progress-day {
      font-size: $font-size-sm;
      color: $text-color-secondary;
    }

    .streak-badge-inline {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      font-size: $font-size-sm;
      color: #fa8c16;
      background: #fff7e6;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 500;
    }
  }

  .enrollment-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: $spacing-xs;

    .enrollment-date {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
    }
  }
}

:deep(.van-pull-refresh) {
  min-height: 300px;
}

:deep(.van-empty) {
  padding: 40px 0;
}
</style>
