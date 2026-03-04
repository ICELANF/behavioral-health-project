<template>
  <view class="fd-page">
    <view class="fd-navbar">
      <view class="fd-back" @tap="goBack">←</view>
      <text class="fd-title">饮食日记</text>
      <picker mode="date" :value="selectedDate" @change="onDateChange">
        <view class="fd-date-picker">{{ displayDate }} ▾</view>
      </picker>
    </view>
    <scroll-view scroll-y class="fd-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 今日营养总计 -->
      <view class="fd-nutrition-summary">
        <text class="fd-summary-title">今日摄入</text>
        <view class="fd-nutrition-row">
          <view class="fd-nutrition-item">
            <text class="fd-nutrition-num">{{ totals.calories }}</text>
            <text class="fd-nutrition-unit">kcal</text>
            <text class="fd-nutrition-label">总热量</text>
          </view>
          <view class="fd-nutrition-divider"></view>
          <view class="fd-nutrition-item">
            <text class="fd-nutrition-num">{{ totals.carbs }}</text>
            <text class="fd-nutrition-unit">g</text>
            <text class="fd-nutrition-label">碳水</text>
          </view>
          <view class="fd-nutrition-divider"></view>
          <view class="fd-nutrition-item">
            <text class="fd-nutrition-num">{{ totals.protein }}</text>
            <text class="fd-nutrition-unit">g</text>
            <text class="fd-nutrition-label">蛋白质</text>
          </view>
          <view class="fd-nutrition-divider"></view>
          <view class="fd-nutrition-item">
            <text class="fd-nutrition-num">{{ totals.fat }}</text>
            <text class="fd-nutrition-unit">g</text>
            <text class="fd-nutrition-label">脂肪</text>
          </view>
        </view>
      </view>

      <!-- 热量平衡卡 -->
      <view v-if="balance" class="fd-balance-card">
        <view class="fd-balance-header">
          <text class="fd-balance-title">⚖️ 热量平衡</text>
          <view class="fd-balance-badge" :style="{ background: confidenceBg, color: confidenceColor }">
            {{ confidenceLabel }}
          </view>
        </view>
        <view class="fd-balance-row">
          <view class="fd-balance-item">
            <text class="fd-balance-num">{{ balance.intake?.calories ?? '—' }}</text>
            <text class="fd-balance-unit">kcal</text>
            <text class="fd-balance-label">今日摄入</text>
          </view>
          <view class="fd-balance-vs">VS</view>
          <view class="fd-balance-item">
            <text class="fd-balance-num">{{ Math.round(balance.expenditure?.total ?? 0) }}</text>
            <text class="fd-balance-unit">kcal</text>
            <text class="fd-balance-label">估算支出</text>
          </view>
        </view>
        <view class="fd-balance-result" :style="{ background: balanceBg }">
          <text class="fd-balance-diff" :style="{ color: balanceColor }">
            {{ balanceDiff >= 0 ? '+' : '' }}{{ balanceDiff }} kcal
          </text>
          <text class="fd-balance-label-text" :style="{ color: balanceColor }">{{ balance.balance_label ?? '' }}</text>
        </view>
        <view class="fd-balance-breakdown">
          <text class="fd-balance-sub">基础代谢 {{ Math.round(balance.expenditure?.bmr ?? 0) }}  ·  日常活动 {{ Math.round(balance.expenditure?.neat ?? 0) }}  ·  运动消耗 {{ Math.round(balance.expenditure?.eat ?? 0) }}</text>
        </view>
        <text v-if="balance.empirical" class="fd-balance-empirical">✓ 已结合近期体重变化实测校准</text>
      </view>

      <!-- 按餐次分组 -->
      <view v-for="meal in mealGroups" :key="meal.type" class="fd-meal-section">
        <view class="fd-meal-header">
          <view class="fd-meal-icon" :style="{ background: mealIconBg(meal.type) }">
            <text :style="{ color: mealIconColor(meal.type) }">{{ mealEmoji(meal.type) }}</text>
          </view>
          <text class="fd-meal-name">{{ mealName(meal.type) }}</text>
          <text class="fd-meal-calories">{{ mealCalories(meal.items) }} kcal</text>
        </view>
        <view v-if="meal.items.length === 0" class="fd-meal-empty">
          <text class="fd-meal-empty-text">暂无记录</text>
        </view>
        <view v-for="food in meal.items" :key="food.id" class="fd-food-card">
          <view class="fd-food-info">
            <text class="fd-food-name">{{ food.food_name }}</text>
            <text class="fd-food-time">{{ formatTime(food.recorded_at) }}</text>
          </view>
          <view class="fd-food-nutrition">
            <text class="fd-food-cal">{{ food.nutrition?.calories || 0 }} kcal</text>
            <text class="fd-food-macros">
              碳 {{ food.nutrition?.carbs || 0 }}g · 蛋 {{ food.nutrition?.protein || 0 }}g · 脂 {{ food.nutrition?.fat || 0 }}g
            </text>
          </view>
        </view>
      </view>

      <view v-if="!loading && totalItems === 0" class="fd-empty">
        <text class="fd-empty-icon">🥗</text>
        <text class="fd-empty-text">今日暂无饮食记录</text>
        <text class="fd-empty-hint">使用食物扫描功能添加记录</text>
      </view>
      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const loading      = ref(false)
const refreshing   = ref(false)
const selectedDate = ref(todayStr())
const allItems     = ref<any[]>([])
const balance      = ref<any>(null)

const displayDate = computed(() => {
  const d = new Date(selectedDate.value)
  if (selectedDate.value === todayStr()) return '今天'
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

const MEAL_ORDER = ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner', 'supper']

const mealGroups = computed(() => {
  return MEAL_ORDER.map(type => ({
    type,
    items: allItems.value.filter(i => i.meal_type === type),
  })).filter(g => g.items.length > 0)
})

const totalItems = computed(() => allItems.value.length)

const totals = computed(() => {
  return allItems.value.reduce(
    (acc, item) => {
      acc.calories += item.nutrition?.calories || 0
      acc.carbs    += item.nutrition?.carbs    || 0
      acc.protein  += item.nutrition?.protein  || 0
      acc.fat      += item.nutrition?.fat      || 0
      return acc
    },
    { calories: 0, carbs: 0, protein: 0, fat: 0 }
  )
})

const balanceDiff = computed(() => Math.round(balance.value?.balance ?? 0))

const balanceColor = computed(() => {
  const d = balanceDiff.value
  if (d > 200)  return '#B71C1C'   // 明显盈余 → 深红警示
  if (d < -300) return '#1565C0'   // 明显亏损 → 蓝色（减重）
  return '#2E7D32'                  // 平衡 → 深绿
})

const balanceBg = computed(() => {
  const d = balanceDiff.value
  if (d > 200)  return '#FFEBEE'
  if (d < -300) return '#E3F2FD'
  return '#E8F5E9'
})

const confidenceLabel = computed(() => {
  const c = balance.value?.confidence
  if (c === 'high')   return '高置信'
  if (c === 'medium') return '中置信'
  return '参考值'
})

const confidenceBg = computed(() => {
  const c = balance.value?.confidence
  if (c === 'high')   return '#E8F5E9'
  if (c === 'medium') return '#FFF8E1'
  return '#ECEFF1'
})

const confidenceColor = computed(() => {
  const c = balance.value?.confidence
  if (c === 'high')   return '#2E7D32'
  if (c === 'medium') return '#F57F17'
  return '#546E7A'
})

function mealCalories(items: any[]): number {
  return items.reduce((s, i) => s + (i.nutrition?.calories || 0), 0)
}
function mealName(type: string): string {
  const m: Record<string, string> = {
    breakfast: '早餐', morning_snack: '上午点心',
    lunch: '午餐', afternoon_snack: '下午点心',
    dinner: '晚餐', supper: '夜宵',
  }
  return m[type] || type
}
function mealEmoji(type: string): string {
  const m: Record<string, string> = {
    breakfast: '🌅', morning_snack: '🧃',
    lunch: '☀️', afternoon_snack: '🍎',
    dinner: '🌙', supper: '🌛',
  }
  return m[type] || '🍽'
}
function mealIconBg(type: string): string {
  const m: Record<string, string> = {
    breakfast: '#FFF8E8', morning_snack: '#FFF0F5',
    lunch: '#FFF3E0', afternoon_snack: '#E8F8F0',
    dinner: '#EEF2FF', supper: '#F0EEF8',
  }
  return m[type] || '#F5F5F5'
}
function mealIconColor(type: string): string {
  const m: Record<string, string> = {
    breakfast: '#F39C12', morning_snack: '#E91E8C',
    lunch: '#E67E22', afternoon_snack: '#27AE60',
    dinner: '#5B6ED4', supper: '#9B59B6',
  }
  return m[type] || '#8E99A4'
}

function formatTime(t: string): string {
  return t ? new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''
}

async function loadData() {
  loading.value = true
  try {
    const res = await http<any>(`/api/v1/food/diary?date=${selectedDate.value}`)
    allItems.value = res.items || res || []
  } catch {
    allItems.value = []
  }
  loading.value = false
  // 加载热量平衡（静默失败）
  try {
    balance.value = await http<any>(`/api/v1/food/balance?date=${selectedDate.value}`)
  } catch { balance.value = null }
}

function onDateChange(e: any) {
  selectedDate.value = e.detail.value
  loadData()
}

async function onRefresh() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}

onMounted(() => loadData())
</script>

<style scoped>
.fd-page { min-height: 100vh; background: #F0F7FF; }
.fd-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%); color: #fff;
}
.fd-back { font-size: 40rpx; padding: 16rpx; }
.fd-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fd-date-picker {
  padding: 10rpx 20rpx; background: rgba(255,255,255,0.25);
  border-radius: 20rpx; font-size: 26rpx; color: #fff; white-space: nowrap;
}
.fd-scroll { height: calc(100vh - 180rpx); }

/* 营养总计 */
.fd-nutrition-summary {
  margin: 24rpx; background: #fff; border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(21,101,192,0.08);
}
.fd-summary-title { display: block; font-size: 26rpx; font-weight: 600; color: #1565C0; margin-bottom: 20rpx; }
.fd-nutrition-row { display: flex; align-items: center; }
.fd-nutrition-item { flex: 1; text-align: center; }
.fd-nutrition-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.fd-nutrition-unit { display: block; font-size: 18rpx; color: #8E99A4; }
.fd-nutrition-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fd-nutrition-divider { width: 1rpx; height: 60rpx; background: #F0F0F0; }

/* 热量平衡卡 */
.fd-balance-card {
  margin: 0 24rpx 16rpx; background: #fff; border-radius: 20rpx; padding: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(21,101,192,0.06);
}
.fd-balance-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20rpx; }
.fd-balance-title { font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fd-balance-badge { font-size: 20rpx; padding: 4rpx 14rpx; border-radius: 20rpx; font-weight: 600; }
.fd-balance-row { display: flex; align-items: center; gap: 8rpx; margin-bottom: 16rpx; }
.fd-balance-item { flex: 1; text-align: center; background: #F0F7FF; border-radius: 14rpx; padding: 16rpx; }
.fd-balance-num  { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.fd-balance-unit { display: block; font-size: 18rpx; color: #8E99A4; }
.fd-balance-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fd-balance-vs { font-size: 22rpx; color: #BDC3C7; font-weight: 600; flex-shrink: 0; }
.fd-balance-result {
  border-radius: 14rpx; padding: 16rpx; text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 12rpx;
  margin-bottom: 12rpx;
}
.fd-balance-diff       { font-size: 40rpx; font-weight: 700; }
.fd-balance-label-text { font-size: 26rpx; font-weight: 600; }
.fd-balance-breakdown  { margin-bottom: 8rpx; }
.fd-balance-sub { font-size: 20rpx; color: #8E99A4; }
.fd-balance-empirical { display: block; font-size: 20rpx; color: #1565C0; margin-top: 8rpx; }

/* 餐次分组 */
.fd-meal-section { margin: 0 24rpx 16rpx; }
.fd-meal-header {
  display: flex; align-items: center; gap: 16rpx;
  background: #fff; border-radius: 16rpx 16rpx 0 0; padding: 20rpx 24rpx;
  border-bottom: 1rpx solid #F0F7FF;
}
.fd-meal-icon {
  width: 56rpx; height: 56rpx; border-radius: 14rpx;
  display: flex; align-items: center; justify-content: center; font-size: 28rpx;
}
.fd-meal-name     { flex: 1; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fd-meal-calories { font-size: 24rpx; color: #8E99A4; }
.fd-meal-empty    { background: #fff; border-radius: 0 0 16rpx 16rpx; padding: 20rpx 24rpx; }
.fd-meal-empty-text { font-size: 24rpx; color: #BDC3C7; }
.fd-food-card {
  background: #fff; padding: 16rpx 24rpx;
  border-top: 1rpx solid #F0F7FF; display: flex; justify-content: space-between; align-items: center;
}
.fd-food-card:last-child { border-radius: 0 0 16rpx 16rpx; }
.fd-food-info { flex: 1; }
.fd-food-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.fd-food-time { display: block; font-size: 20rpx; color: #BDC3C7; margin-top: 4rpx; }
.fd-food-nutrition { text-align: right; }
.fd-food-cal    { display: block; font-size: 26rpx; font-weight: 700; color: #1565C0; }
.fd-food-macros { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }

.fd-empty { text-align: center; padding: 100rpx 0; }
.fd-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.fd-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.fd-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
