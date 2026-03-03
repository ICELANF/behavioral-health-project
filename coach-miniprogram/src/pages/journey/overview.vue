<template>
  <view class="jov-page">
    <view class="jov-header">
      <text class="jov-title">成长路径</text>
      <text class="jov-sub">{{ overview.current_level_name || levelName(overview.current_level) }} → {{ overview.next_level_name || levelName(overview.next_level) }}</text>
    </view>

    <scroll-view scroll-y class="jov-scroll" refresher-enabled
      @refresherrefresh="onRefresh" :refresher-triggered="refreshing">

      <!-- 当前级别卡 -->
      <view class="jov-level-card">
        <view class="jov-level-icon">{{ levelIcon(overview.current_level) }}</view>
        <view class="jov-level-info">
          <text class="jov-level-name">{{ levelName(overview.current_level) }}</text>
          <text class="jov-level-desc">{{ levelDesc(overview.current_level) }}</text>
        </view>
        <view class="jov-level-badge">当前</view>
      </view>

      <!-- 进度条 -->
      <view class="jov-progress-section">
        <view class="jov-progress-header">
          <text class="jov-progress-title">晋级进度</text>
          <text class="jov-progress-pct">{{ overview.progress_pct || 0 }}%</text>
        </view>
        <view class="jov-progress-bar">
          <view class="jov-progress-fill" :style="{ width: (overview.progress_pct || 0) + '%' }" />
        </view>
        <text class="jov-progress-hint">距离晋升 {{ levelName(overview.next_level) }}</text>
      </view>

      <!-- 成长路径图 -->
      <view class="jov-roadmap">
        <text class="jov-roadmap-title">成长体系</text>
        <view v-for="(level, idx) in levels" :key="level.key"
          class="jov-roadmap-item"
          :class="{ 'jov-roadmap-item--current': level.key === overview.current_level, 'jov-roadmap-item--done': isLevelDone(level.key, overview.current_level) }">
          <view class="jov-roadmap-dot" />
          <view class="jov-roadmap-content">
            <text class="jov-roadmap-level-name">{{ level.icon }} {{ level.name }}</text>
            <text class="jov-roadmap-level-desc">{{ level.desc }}</text>
          </view>
          <view v-if="level.key === overview.current_level" class="jov-roadmap-current-tag">你在这里</view>
          <view v-else-if="isLevelDone(level.key, overview.current_level)" class="jov-roadmap-done-tag">已完成</view>
        </view>
      </view>

      <!-- 行动按钮 -->
      <view class="jov-actions">
        <view class="jov-action-btn" @tap="goProgress">
          <text>查看我的任务</text>
        </view>
        <view class="jov-action-btn jov-action-btn--secondary" @tap="goPromotion">
          <text>申请晋级</text>
        </view>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const overview = ref<any>({ current_level: 'observer', next_level: 'grower', progress_pct: 0 })
const refreshing = ref(false)

const levels = [
  { key: 'observer',  name: '观察者', icon: '👁', desc: '了解行为健康基础知识' },
  { key: 'grower',    name: '成长者', icon: '🌱', desc: '掌握健康促进基本技能' },
  { key: 'sharer',    name: '分享者', icon: '🤝', desc: '能够指导他人健康改变' },
  { key: 'guide',     name: '向导者', icon: '🧭', desc: '具备专业教练能力' },
  { key: 'master',    name: '大师',   icon: '⭐', desc: '行为健康领域专家' },
]

const levelOrder = levels.map(l => l.key)

function levelName(key: string): string {
  return levels.find(l => l.key === key)?.name || key
}
function levelIcon(key: string): string {
  return levels.find(l => l.key === key)?.icon || '🌱'
}
function levelDesc(key: string): string {
  return levels.find(l => l.key === key)?.desc || ''
}
function isLevelDone(levelKey: string, currentKey: string): boolean {
  return levelOrder.indexOf(levelKey) < levelOrder.indexOf(currentKey)
}

async function loadData() {
  try {
    overview.value = await http<any>('/api/v1/journey/overview')
  } catch (e) { console.warn('[journey/overview] overview:', e) }
}

function goProgress() { uni.navigateTo({ url: '/pages/journey/progress' }) }
function goPromotion() { uni.navigateTo({ url: '/pages/journey/promotion' }) }

async function onRefresh() { refreshing.value = true; await loadData(); refreshing.value = false }
onMounted(() => { loadData() })
</script>

<style scoped>
.jov-page { min-height: 100vh; background: #F5F6FA; }

.jov-header {
  padding: 24rpx 32rpx;
  padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.jov-title { display: block; font-size: 38rpx; font-weight: 700; }
.jov-sub { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 6rpx; }

.jov-scroll { height: calc(100vh - 200rpx); }

.jov-level-card {
  display: flex; align-items: center; gap: 20rpx;
  background: #fff; margin: 24rpx; border-radius: 20rpx; padding: 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(45,142,105,0.15);
}
.jov-level-icon { font-size: 56rpx; }
.jov-level-info { flex: 1; }
.jov-level-name { display: block; font-size: 34rpx; font-weight: 700; color: #2C3E50; }
.jov-level-desc { display: block; font-size: 22rpx; color: #5B6B7F; margin-top: 6rpx; }
.jov-level-badge { background: #2D8E69; color: #fff; font-size: 20rpx; padding: 6rpx 16rpx; border-radius: 10rpx; font-weight: 600; }

.jov-progress-section { background: #fff; margin: 0 24rpx 24rpx; border-radius: 16rpx; padding: 24rpx; }
.jov-progress-header { display: flex; justify-content: space-between; margin-bottom: 16rpx; }
.jov-progress-title { font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.jov-progress-pct { font-size: 28rpx; font-weight: 700; color: #2D8E69; }
.jov-progress-bar { height: 12rpx; background: #F0F0F0; border-radius: 6rpx; overflow: hidden; margin-bottom: 12rpx; }
.jov-progress-fill { height: 100%; background: linear-gradient(90deg, #2D8E69, #3BAF7C); border-radius: 6rpx; transition: width 0.5s; min-width: 12rpx; }
.jov-progress-hint { font-size: 22rpx; color: #8E99A4; }

.jov-roadmap { background: #fff; margin: 0 24rpx 24rpx; border-radius: 16rpx; padding: 24rpx; }
.jov-roadmap-title { font-size: 28rpx; font-weight: 700; color: #2C3E50; margin-bottom: 20rpx; display: block; }
.jov-roadmap-item { display: flex; align-items: flex-start; gap: 16rpx; padding: 16rpx 0; position: relative; }
.jov-roadmap-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #D0D5DD; margin-top: 8rpx; flex-shrink: 0; }
.jov-roadmap-item--done .jov-roadmap-dot { background: #2D8E69; }
.jov-roadmap-item--current .jov-roadmap-dot { background: #2D8E69; box-shadow: 0 0 0 4rpx rgba(45,142,105,0.2); }
.jov-roadmap-content { flex: 1; }
.jov-roadmap-level-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.jov-roadmap-level-desc { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }
.jov-roadmap-item--done .jov-roadmap-level-name { color: #2D8E69; }
.jov-roadmap-current-tag { background: #E8F8F0; color: #2D8E69; font-size: 18rpx; padding: 4rpx 12rpx; border-radius: 8rpx; white-space: nowrap; }
.jov-roadmap-done-tag { background: #F5F5F5; color: #8E99A4; font-size: 18rpx; padding: 4rpx 12rpx; border-radius: 8rpx; white-space: nowrap; }

.jov-actions { padding: 0 24rpx; display: flex; gap: 16rpx; }
.jov-action-btn { flex: 1; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 16rpx; padding: 20rpx; text-align: center; color: #fff; font-size: 28rpx; font-weight: 600; }
.jov-action-btn--secondary { background: #fff; color: #2D8E69; border: 2rpx solid #2D8E69; }
</style>
