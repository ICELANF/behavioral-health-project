<template>
  <view class="credits-page">

    <!-- 学分汇总卡 -->
    <view class="credits-summary px-4">
      <view class="credits-summary__card" v-if="summary">
        <view class="credits-summary__total-row">
          <view class="credits-summary__total-label">
            <text class="credits-summary__total-text">总学分</text>
            <text class="credits-summary__total-sub">M1-M4 + 选修</text>
          </view>
          <text class="credits-summary__total-value">{{ summary.total }}</text>
        </view>

        <!-- 各模块 -->
        <view class="credits-modules">
          <view
            v-for="m in moduleItems"
            :key="m.key"
            class="credits-module-item"
          >
            <view class="credits-module-item__header">
              <view class="credits-module-item__dot" :style="{ background: m.color }"></view>
              <text class="credits-module-item__label">{{ m.label }}</text>
              <text class="credits-module-item__value">{{ summary[m.key as keyof typeof summary] || 0 }}</text>
              <text class="credits-module-item__target">/ {{ m.target }}学分</text>
            </view>
            <view class="credits-module-item__bar">
              <view
                class="credits-module-item__fill"
                :style="{
                  width: Math.min(((summary[m.key as keyof typeof summary] as number) || 0) / m.target * 100, 100) + '%',
                  background: m.color
                }"
              ></view>
            </view>
          </view>
        </view>

        <!-- 必修/选修说明 -->
        <view class="credits-summary__note">
          <text class="text-xs text-secondary-color">
            必修学分: M1(8) + M2(10) + M3(12) = 30分 | 选修: M4(6分)
          </text>
        </view>
      </view>

      <!-- 骨架屏 -->
      <view v-else class="bhp-skeleton" style="height: 280rpx; border-radius: var(--radius-xl, 16px);"></view>
    </view>

    <!-- 学分记录 -->
    <view class="credits-records px-4">
      <text class="credits-section-title">学分记录</text>

      <template v-if="loadingRecords">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 80rpx; margin-bottom: 10rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="records.length">
        <view
          v-for="record in records"
          :key="record.id"
          class="credits-record bhp-card bhp-card--flat"
        >
          <view class="credits-record__badge" :style="{ background: MODULE_COLOR[record.module_type] || '#e5e7eb' }">
            <text class="credits-record__module">{{ record.module_type?.toUpperCase() }}</text>
          </view>
          <view class="credits-record__body">
            <text class="credits-record__desc">{{ record.description }}</text>
            <text class="text-xs text-secondary-color">{{ formatDate(record.created_at) }}</text>
          </view>
          <text class="credits-record__credits">+{{ record.credits }}</text>
        </view>

        <view class="credits-load-more" v-if="hasMore" @tap="loadMore">
          <text v-if="!loadingMore">加载更多</text>
          <text v-else>加载中...</text>
        </view>
        <view class="credits-load-more credits-load-more--end" v-else>
          <text>已显示全部</text>
        </view>
      </template>

      <view class="credits-empty" v-else>
        <text class="credits-empty__icon">📋</text>
        <text class="credits-empty__text">暂无学分记录，完成学习任务即可获得</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { creditsApi, type CreditSummary, type CreditRecord } from '@/api/learning'

const summary      = ref<CreditSummary | null>(null)
const records      = ref<CreditRecord[]>([])
const loadingRecords  = ref(false)
const loadingMore  = ref(false)
const page         = ref(1)
const hasMore      = ref(true)

const MODULE_COLOR: Record<string, string> = {
  m1:      '#10b981',
  m2:      '#3b82f6',
  m3:      '#f59e0b',
  m4:      '#8b5cf6',
  elective:'#6b7280'
}

const moduleItems = [
  { key: 'm1',       label: 'M1 认知基础', target: 8,  color: MODULE_COLOR.m1 },
  { key: 'm2',       label: 'M2 评估技能', target: 10, color: MODULE_COLOR.m2 },
  { key: 'm3',       label: 'M3 干预方法', target: 12, color: MODULE_COLOR.m3 },
  { key: 'm4',       label: 'M4 高阶带教', target: 6,  color: MODULE_COLOR.m4 },
  { key: 'elective', label: '选修',         target: 10, color: MODULE_COLOR.elective },
]

onMounted(async () => {
  await Promise.all([loadSummary(), loadRecords(true)])
})

onPullDownRefresh(async () => {
  await Promise.all([loadSummary(), loadRecords(true)])
  uni.stopPullDownRefresh()
})

async function loadSummary() {
  try {
    summary.value = await creditsApi.mySummary()
  } catch { /* 静默 */ }
}

async function loadRecords(reset = false) {
  if (reset) { page.value = 1; records.value = []; hasMore.value = true }
  if (!hasMore.value) return
  reset ? (loadingRecords.value = true) : (loadingMore.value = true)
  try {
    const data = await creditsApi.myRecords(page.value, 20)
    const newItems = data.items || []
    records.value = reset ? newItems : [...records.value, ...newItems]
    hasMore.value = newItems.length === 20
    page.value++
  } catch { /* 静默 */ } finally {
    loadingRecords.value = false
    loadingMore.value = false
  }
}

function loadMore() { loadRecords(false) }

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}月${d.getDate()}日`
  } catch { return dateStr }
}
</script>

<style scoped>
.credits-page { background: var(--surface-secondary); min-height: 100vh; }

/* 汇总卡 */
.credits-summary { padding-top: 16rpx; }
.credits-summary__card {
  background: var(--surface);
  border-radius: var(--radius-xl, 16px);
  padding: 28rpx;
  box-shadow: var(--shadow-card);
}

.credits-summary__total-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1px solid var(--border-light);
}
.credits-summary__total-text { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.credits-summary__total-sub  { display: block; font-size: 20rpx; color: var(--text-tertiary); margin-top: 4rpx; }
.credits-summary__total-value {
  font-size: 64rpx;
  font-weight: 700;
  color: var(--bhp-primary-500);
}

/* 各模块 */
.credits-modules { display: flex; flex-direction: column; gap: 16rpx; margin-bottom: 16rpx; }
.credits-module-item__header {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 6rpx;
}
.credits-module-item__dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  flex-shrink: 0;
}
.credits-module-item__label { flex: 1; font-size: 24rpx; color: var(--text-secondary); }
.credits-module-item__value { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.credits-module-item__target { font-size: 22rpx; color: var(--text-tertiary); }
.credits-module-item__bar {
  height: 8rpx;
  background: var(--bhp-gray-100);
  border-radius: 9999px;
  overflow: hidden;
}
.credits-module-item__fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.6s;
}
.credits-summary__note { padding-top: 8rpx; }

/* 记录区 */
.credits-records { padding-top: 24rpx; }
.credits-section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16rpx;
}

.credits-record {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  margin-bottom: 10rpx;
}
.credits-record__badge {
  width: 60rpx;
  height: 60rpx;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.credits-record__module { font-size: 20rpx; color: #fff; font-weight: 700; }
.credits-record__body { flex: 1; overflow: hidden; }
.credits-record__desc { display: block; font-size: 26rpx; color: var(--text-primary); }
.credits-record__credits {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--bhp-primary-500);
}

.credits-load-more {
  text-align: center;
  padding: 20rpx;
  font-size: 26rpx;
  color: var(--bhp-primary-500);
  cursor: pointer;
}
.credits-load-more--end { color: var(--text-tertiary); }

/* 空状态 */
.credits-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 0;
  gap: 16rpx;
}
.credits-empty__icon { font-size: 60rpx; }
.credits-empty__text { font-size: 26rpx; color: var(--text-tertiary); text-align: center; line-height: 1.6; }
</style>
