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

const loading = ref(false)
const refreshing = ref(false)
const selectedDate = ref(todayStr())
const allItems = ref<any[]>([])

const displayDate = computed(() => {
  const d = new Date(selectedDate.value)
  const today = todayStr()
  if (selectedDate.value === today) return '今天'
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

const MEAL_ORDER = ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner', 'supper']

const mealGroups = computed(() => {
  return MEAL_ORDER.map(type => ({
    type,
    items: allItems.value.filter(i => i.meal_type === type),
  })).filter(g => g.items.length > 0)  // 隐藏空餐次，减少滚动高度
})

const totalItems = computed(() => allItems.value.length)

const totals = computed(() => {
  return allItems.value.reduce(
    (acc, item) => {
      acc.calories += item.nutrition?.calories || 0
      acc.carbs += item.nutrition?.carbs || 0
      acc.protein += item.nutrition?.protein || 0
      acc.fat += item.nutrition?.fat || 0
      return acc
    },
    { calories: 0, carbs: 0, protein: 0, fat: 0 }
  )
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
.fd-page { min-height: 100vh; background: #F5F6FA; }
.fd-navbar {
  display: flex; align-items: center; padding: 8rpx 24rpx;
  padding-top: calc(88rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #1E8449, #27AE60); color: #fff;
}
.fd-back { font-size: 40rpx; padding: 16rpx; }
.fd-title { flex: 1; text-align: center; font-size: 34rpx; font-weight: 600; }
.fd-date-picker {
  padding: 10rpx 20rpx; background: rgba(255,255,255,0.25);
  border-radius: 20rpx; font-size: 26rpx; color: #fff; white-space: nowrap;
}
.fd-scroll { height: calc(100vh - 180rpx); }
.fd-nutrition-summary {
  margin: 24rpx; background: #fff; border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(39,174,96,0.1);
}
.fd-summary-title { display: block; font-size: 26rpx; font-weight: 600; color: #27AE60; margin-bottom: 20rpx; }
.fd-nutrition-row { display: flex; align-items: center; }
.fd-nutrition-item { flex: 1; text-align: center; }
.fd-nutrition-num { display: block; font-size: 36rpx; font-weight: 700; color: #2C3E50; }
.fd-nutrition-unit { display: block; font-size: 18rpx; color: #8E99A4; }
.fd-nutrition-label { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fd-nutrition-divider { width: 1rpx; height: 60rpx; background: #F0F0F0; }
.fd-meal-section { margin: 0 24rpx 16rpx; }
.fd-meal-header {
  display: flex; align-items: center; gap: 16rpx;
  background: #fff; border-radius: 16rpx 16rpx 0 0; padding: 20rpx 24rpx;
  border-bottom: 1rpx solid #F5F6FA;
}
.fd-meal-icon {
  width: 56rpx; height: 56rpx; border-radius: 14rpx;
  display: flex; align-items: center; justify-content: center; font-size: 28rpx;
}
.fd-meal-name { flex: 1; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.fd-meal-calories { font-size: 24rpx; color: #8E99A4; }
.fd-meal-empty {
  background: #fff; border-radius: 0 0 16rpx 16rpx; padding: 20rpx 24rpx;
}
.fd-meal-empty-text { font-size: 24rpx; color: #BDC3C7; }
.fd-food-card {
  background: #fff; padding: 16rpx 24rpx;
  border-top: 1rpx solid #F5F6FA; display: flex; justify-content: space-between; align-items: center;
}
.fd-food-card:last-child { border-radius: 0 0 16rpx 16rpx; }
.fd-food-info { flex: 1; }
.fd-food-name { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.fd-food-time { display: block; font-size: 20rpx; color: #BDC3C7; margin-top: 4rpx; }
.fd-food-nutrition { text-align: right; }
.fd-food-cal { display: block; font-size: 26rpx; font-weight: 700; color: #27AE60; }
.fd-food-macros { display: block; font-size: 20rpx; color: #8E99A4; margin-top: 4rpx; }
.fd-empty { text-align: center; padding: 100rpx 0; }
.fd-empty-icon { display: block; font-size: 80rpx; margin-bottom: 16rpx; }
.fd-empty-text { display: block; font-size: 30rpx; color: #5B6B7F; }
.fd-empty-hint { display: block; font-size: 24rpx; color: #8E99A4; margin-top: 8rpx; }
</style>
