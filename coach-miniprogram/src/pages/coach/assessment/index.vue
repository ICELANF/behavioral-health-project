<template>
  <view class="cam-page">

    <view class="cam-navbar safe-area-top">
      <view class="cam-navbar__back" @tap="goBack"><text class="cam-navbar__arrow">‹</text></view>
      <text class="cam-navbar__title">评估管理</text>
      <view class="cam-navbar__placeholder"></view>
    </view>

    <!-- Tab -->
    <view class="cam-tabs">
      <view
        v-for="tab in TABS"
        :key="tab.key"
        class="cam-tab"
        :class="{ 'cam-tab--active': activeTab === tab.key }"
        @tap="switchTab(tab.key)"
      >
        <text>{{ tab.label }}</text>
        <view class="cam-tab__badge" v-if="tabCounts[tab.key] > 0">
          <text>{{ tabCounts[tab.key] }}</text>
        </view>
      </view>
    </view>

    <!-- 列表 -->
    <scroll-view scroll-y class="cam-body">

      <template v-if="loading">
        <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 140rpx; border-radius: var(--radius-lg); margin-bottom: 16rpx;"></view>
      </template>

      <view v-else-if="filteredList.length" class="cam-list">
        <view v-for="item in filteredList" :key="item.id" class="cam-card" @tap="goDetail(item)">
          <view class="cam-card__header">
            <text class="cam-card__name">{{ item.student_name || '学员#' + item.student_id }}</text>
            <view class="cam-card__status" :class="`cam-card__status--${item.status}`">
              <text>{{ STATUS_LABEL[item.status] || item.status }}</text>
            </view>
          </view>
          <view class="cam-card__info">
            <text class="cam-card__scales">{{ item.scales?.join(' + ') || '综合评估' }}</text>
          </view>
          <view class="cam-card__footer">
            <text class="cam-card__date">{{ formatDate(item.created_at) }}</text>
          </view>
        </view>
      </view>

      <view v-else class="cam-empty">
        <text class="cam-empty__icon">📋</text>
        <text class="cam-empty__text">暂无评估</text>
      </view>

    </scroll-view>

    <!-- 分配新评估按钮 -->
    <view class="cam-fab" @tap="showAssignModal = true">
      <text class="cam-fab__text">+ 分配评估</text>
    </view>

    <!-- 分配弹窗 -->
    <view class="cam-modal-mask" v-if="showAssignModal" @tap="showAssignModal = false">
      <view class="cam-modal" @tap.stop>
        <text class="cam-modal__title">分配新评估</text>

        <view class="cam-modal__field">
          <text class="cam-modal__label">选择学员</text>
          <picker :range="studentNames" @change="onStudentPick">
            <view class="cam-modal__picker">
              <text>{{ selectedStudent ? selectedStudent.full_name || selectedStudent.username : '请选择' }}</text>
              <text class="cam-modal__picker-arrow">▼</text>
            </view>
          </picker>
        </view>

        <view class="cam-modal__field">
          <text class="cam-modal__label">量表组合</text>
          <view class="cam-modal__scale-list">
            <view
              v-for="s in SCALE_OPTIONS"
              :key="s"
              class="cam-modal__scale"
              :class="{ 'cam-modal__scale--active': selectedScales.includes(s) }"
              @tap="toggleScale(s)"
            >
              <text>{{ s }}</text>
            </view>
          </view>
        </view>

        <view class="cam-modal__actions">
          <view class="cam-modal__btn cam-modal__btn--cancel" @tap="showAssignModal = false">
            <text>取消</text>
          </view>
          <view class="cam-modal__btn cam-modal__btn--ok" @tap="submitAssign">
            <text>确认分配</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const TABS = [
  { key: 'all',         label: '全部' },
  { key: 'assigned',    label: '待分配' },
  { key: 'in_progress', label: '进行中' },
  { key: 'pending_review', label: '待审核' },
  { key: 'completed',   label: '已完成' },
]
const STATUS_LABEL: Record<string, string> = {
  assigned: '待完成', in_progress: '进行中', pending_review: '待审核', completed: '已完成',
}
const SCALE_OPTIONS = ['SCL-90', 'PHQ-9', 'GAD-7', 'PSQI', 'SF-36', 'BFI-44']

const activeTab      = ref('all')
const list           = ref<any[]>([])
const loading        = ref(false)
const showAssignModal = ref(false)
const students       = ref<any[]>([])
const selectedStudent = ref<any>(null)
const selectedScales = ref<string[]>([])

const tabCounts = computed(() => {
  const counts: Record<string, number> = { all: list.value.length }
  for (const item of list.value) {
    counts[item.status] = (counts[item.status] || 0) + 1
  }
  return counts
})

const filteredList = computed(() => {
  if (activeTab.value === 'all') return list.value
  return list.value.filter(i => i.status === activeTab.value)
})

const studentNames = computed(() => students.value.map(s => s.full_name || s.username))

onMounted(() => { loadList(); loadStudents() })

async function loadList() {
  loading.value = true
  try {
    const res = await http.get<any>('/v1/assessment-assignments', { role: 'coach' })
    list.value = res.items || (Array.isArray(res) ? res : [])
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function loadStudents() {
  try {
    const res = await http.get<any>('/v1/coach/students')
    students.value = res.students || []
  } catch { /* ignore */ }
}

function switchTab(key: string) { activeTab.value = key }

function onStudentPick(e: any) {
  const idx = Number(e.detail.value)
  selectedStudent.value = students.value[idx] || null
}

function toggleScale(s: string) {
  const idx = selectedScales.value.indexOf(s)
  if (idx >= 0) selectedScales.value.splice(idx, 1)
  else selectedScales.value.push(s)
}

async function submitAssign() {
  if (!selectedStudent.value || !selectedScales.value.length) {
    uni.showToast({ title: '请选择学员和量表', icon: 'none' })
    return
  }
  try {
    await http.post('/v1/assessment-assignments', {
      student_id: selectedStudent.value.id,
      scales: selectedScales.value,
    })
    uni.showToast({ title: '分配成功', icon: 'success' })
    showAssignModal.value = false
    selectedStudent.value = null
    selectedScales.value = []
    loadList()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '分配失败', icon: 'none' })
  }
}

function formatDate(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

function goDetail(item: any) {
  uni.navigateTo({ url: `/pages/coach/assessment/review?id=${item.id}` })
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cam-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cam-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cam-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cam-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cam-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cam-navbar__placeholder { width: 64rpx; }

.cam-tabs {
  display: flex; background: var(--surface); padding: 12rpx 24rpx 16rpx;
  gap: 12rpx; border-bottom: 1px solid var(--border-light); overflow-x: auto;
}
.cam-tab {
  position: relative; display: flex; align-items: center; gap: 6rpx;
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  font-size: 22rpx; font-weight: 600; color: var(--text-secondary);
  background: var(--surface-secondary); cursor: pointer; flex-shrink: 0;
}
.cam-tab--active { background: var(--bhp-primary-500); color: #fff; }
.cam-tab__badge {
  min-width: 28rpx; height: 28rpx; border-radius: var(--radius-full);
  background: var(--bhp-error-500); color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}
.cam-tab--active .cam-tab__badge { background: rgba(255,255,255,0.3); }

.cam-body { flex: 1; padding: 20rpx 32rpx 120rpx; }
.cam-list { display: flex; flex-direction: column; gap: 16rpx; }

.cam-card {
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 24rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.cam-card:active { opacity: 0.85; }
.cam-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.cam-card__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cam-card__status { font-size: 20rpx; font-weight: 600; padding: 4rpx 14rpx; border-radius: var(--radius-full); }
.cam-card__status--assigned { background: #fff7ed; color: #ea580c; }
.cam-card__status--in_progress { background: #eff6ff; color: #2563eb; }
.cam-card__status--pending_review { background: #fefce8; color: #ca8a04; }
.cam-card__status--completed { background: #f0fdf4; color: #16a34a; }
.cam-card__info { margin-bottom: 8rpx; }
.cam-card__scales { font-size: 24rpx; color: var(--text-secondary); }
.cam-card__footer { display: flex; }
.cam-card__date { font-size: 22rpx; color: var(--text-tertiary); }

.cam-empty { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; gap: 16rpx; }
.cam-empty__icon { font-size: 64rpx; }
.cam-empty__text { font-size: 26rpx; color: var(--text-tertiary); }

/* FAB */
.cam-fab {
  position: fixed; bottom: 60rpx; right: 32rpx;
  background: var(--bhp-primary-500); color: #fff;
  padding: 16rpx 32rpx; border-radius: var(--radius-full);
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.15); cursor: pointer;
}
.cam-fab:active { opacity: 0.85; }
.cam-fab__text { font-size: 26rpx; font-weight: 700; }

/* Modal */
.cam-modal-mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 999;
}
.cam-modal {
  width: 85%; background: var(--surface); border-radius: var(--radius-xl);
  padding: 32rpx; max-height: 80vh; overflow-y: auto;
}
.cam-modal__title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 28rpx; }
.cam-modal__field { margin-bottom: 24rpx; }
.cam-modal__label { display: block; font-size: 24rpx; font-weight: 600; color: var(--text-secondary); margin-bottom: 10rpx; }
.cam-modal__picker {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 20rpx; background: var(--surface-secondary); border-radius: var(--radius-lg);
  font-size: 26rpx; color: var(--text-primary); border: 1px solid var(--border-light);
}
.cam-modal__picker-arrow { font-size: 20rpx; color: var(--text-tertiary); }
.cam-modal__scale-list { display: flex; flex-wrap: wrap; gap: 12rpx; }
.cam-modal__scale {
  padding: 10rpx 20rpx; border-radius: var(--radius-full);
  border: 1px solid var(--border-light); font-size: 22rpx; color: var(--text-secondary); cursor: pointer;
}
.cam-modal__scale--active { border-color: var(--bhp-primary-500); background: var(--bhp-primary-50); color: var(--bhp-primary-600); font-weight: 600; }
.cam-modal__actions { display: flex; gap: 16rpx; margin-top: 8rpx; }
.cam-modal__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.cam-modal__btn--cancel { background: var(--surface-secondary); color: var(--text-secondary); }
.cam-modal__btn--ok { background: var(--bhp-primary-500); color: #fff; }
</style>
