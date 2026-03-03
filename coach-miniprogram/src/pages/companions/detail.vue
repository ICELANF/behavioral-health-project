<template>
  <view class="cd2-page">
    <view v-if="loading" class="cd2-loading"><text>加载中...</text></view>

    <scroll-view v-else-if="companion" scroll-y class="cd2-scroll">
      <!-- 头部 -->
      <view class="cd2-header">
        <view class="cd2-avatar" :style="{ background: avatarColor(companion.name || companion.username) }">
          {{ (companion.name || companion.username || '?')[0] }}
        </view>
        <text class="cd2-name">{{ companion.name || companion.username }}</text>
        <text class="cd2-level">{{ levelName(companion.level || companion.journey_level) }}</text>
        <view class="cd2-days-badge">
          <text class="cd2-days-num">{{ companion.companion_days || 0 }}</text>
          <text class="cd2-days-label">同行天数</text>
        </view>
      </view>

      <!-- 统计 -->
      <view class="cd2-stats">
        <view class="cd2-stat-item">
          <text class="cd2-stat-num">{{ companion.streak_days || 0 }}</text>
          <text class="cd2-stat-label">连续打卡</text>
        </view>
        <view class="cd2-stat-item">
          <text class="cd2-stat-num">{{ companion.total_credits || 0 }}</text>
          <text class="cd2-stat-label">总学分</text>
        </view>
        <view class="cd2-stat-item">
          <text class="cd2-stat-num">{{ companion.completed_tasks || 0 }}</text>
          <text class="cd2-stat-label">完成任务</text>
        </view>
      </view>

      <!-- 最近动态 -->
      <view class="cd2-section">
        <text class="cd2-section-title">最近动态</text>
        <view v-if="companion.recent_activities?.length > 0">
          <view v-for="(act, i) in companion.recent_activities" :key="i" class="cd2-activity">
            <text class="cd2-activity-text">{{ act.description }}</text>
            <text class="cd2-activity-time">{{ act.time }}</text>
          </view>
        </view>
        <text v-else class="cd2-no-activity">暂无近期动态</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>

    <view v-else class="cd2-error">
      <text class="cd2-error-icon">😕</text>
      <text class="cd2-error-text">加载失败</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const companion = ref<any>(null)
const loading = ref(false)
let companionId = 0

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}
function levelName(k: string) { return { observer:'观察者', grower:'成长者', sharer:'分享者', guide:'向导者', master:'大师' }[k] || (k || '成长者') }

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  companionId = Number(page?.options?.id || 0)
  if (!companionId) return
  loading.value = true
  try {
    companion.value = await http<any>(`/api/v1/companions/${companionId}`)
  } catch { companion.value = null } finally { loading.value = false }
})
</script>

<style scoped>
.cd2-page { min-height: 100vh; background: #F5F6FA; }
.cd2-loading { display: flex; align-items: center; justify-content: center; height: 100vh; font-size: 28rpx; color: #8E99A4; }
.cd2-scroll { height: 100vh; }

.cd2-header {
  display: flex; flex-direction: column; align-items: center; padding: 48rpx 32rpx;
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff;
  padding-top: calc(48rpx + env(safe-area-inset-top));
}
.cd2-avatar { width: 120rpx; height: 120rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 48rpx; font-weight: 700; margin-bottom: 16rpx; }
.cd2-name { font-size: 40rpx; font-weight: 700; margin-bottom: 8rpx; }
.cd2-level { font-size: 24rpx; opacity: 0.85; margin-bottom: 16rpx; }
.cd2-days-badge { text-align: center; background: rgba(255,255,255,0.2); border-radius: 16rpx; padding: 12rpx 32rpx; }
.cd2-days-num { display: block; font-size: 48rpx; font-weight: 700; }
.cd2-days-label { display: block; font-size: 20rpx; opacity: 0.85; }

.cd2-stats { display: flex; background: #fff; margin: 0 0 16rpx; padding: 24rpx 0; }
.cd2-stat-item { flex: 1; text-align: center; border-right: 1rpx solid #F0F0F0; }
.cd2-stat-item:last-child { border-right: none; }
.cd2-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2D8E69; }
.cd2-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.cd2-section { background: #fff; margin: 0 24rpx 16rpx; border-radius: 16rpx; padding: 24rpx; }
.cd2-section-title { display: block; font-size: 28rpx; font-weight: 700; color: #2C3E50; margin-bottom: 16rpx; }
.cd2-activity { padding: 12rpx 0; border-bottom: 1rpx solid #F8F8F8; display: flex; justify-content: space-between; }
.cd2-activity-text { font-size: 24rpx; color: #5B6B7F; }
.cd2-activity-time { font-size: 20rpx; color: #8E99A4; }
.cd2-no-activity { font-size: 24rpx; color: #8E99A4; }

.cd2-error { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; gap: 16rpx; }
.cd2-error-icon { font-size: 80rpx; }
.cd2-error-text { font-size: 28rpx; color: #8E99A4; }
</style>
