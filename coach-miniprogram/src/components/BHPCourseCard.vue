<template>
  <view
    class="bhp-course-card bhp-card"
    :class="{ 'bhp-course-card--horizontal': horizontal }"
    @tap="$emit('tap')"
  >
    <!-- 封面 -->
    <view class="bhp-course-card__cover">
      <image
        v-if="cover"
        :src="cover"
        mode="aspectFill"
        class="bhp-course-card__img"
      />
      <view v-else class="bhp-course-card__placeholder">
        <text class="bhp-course-card__placeholder-icon">{{ typeIcon }}</text>
      </view>
      <!-- 类型标签 -->
      <view class="bhp-course-card__type-badge">
        <text>{{ typeLabel }}</text>
      </view>
      <!-- 进度条 -->
      <view class="bhp-course-card__progress-bar" v-if="progress > 0">
        <view class="bhp-course-card__progress-fill" :style="{ width: progress + '%' }"></view>
      </view>
    </view>

    <!-- 信息 -->
    <view class="bhp-course-card__info">
      <text class="bhp-course-card__title">{{ title }}</text>
      <text class="bhp-course-card__sub text-xs text-secondary-color" v-if="subtitle">{{ subtitle }}</text>
      <view class="bhp-course-card__meta">
        <text class="text-xs text-tertiary-color" v-if="duration">{{ duration }}</text>
        <view class="bhp-course-card__pts" v-if="points">
          <text class="text-xs text-primary-color">+{{ points }}积分</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title:       string
  subtitle?:   string
  cover?:      string
  type?:       string    // article | video | audio | course
  duration?:   string    // 如 "15分钟"
  points?:     number
  progress?:   number    // 0-100
  horizontal?: boolean
}>(), {
  type:       'article',
  progress:   0,
  horizontal: false,
})

defineEmits<{ (e: 'tap'): void }>()

const TYPE_ICON: Record<string, string>  = { article: '📄', video: '🎬', audio: '🎵', course: '📚' }
const TYPE_LABEL: Record<string, string> = { article: '文章', video: '视频', audio: '音频', course: '课程' }

const typeIcon  = computed(() => TYPE_ICON[props.type  || 'article'] ?? '📄')
const typeLabel = computed(() => TYPE_LABEL[props.type || 'article'] ?? '内容')
</script>

<style scoped>
.bhp-course-card { overflow: hidden; cursor: pointer; }
.bhp-course-card:active { opacity: 0.85; }

/* 垂直布局（默认）*/
.bhp-course-card__cover {
  position: relative; width: 100%;
  height: 200rpx; background: var(--bhp-gray-100);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0; overflow: hidden;
}
.bhp-course-card__img {
  width: 100%; height: 100%;
}
.bhp-course-card__placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
.bhp-course-card__placeholder-icon { font-size: 64rpx; }
.bhp-course-card__type-badge {
  position: absolute; top: 12rpx; left: 12rpx;
  background: rgba(0,0,0,0.5); color: #fff;
  font-size: 18rpx; padding: 4rpx 10rpx;
  border-radius: var(--radius-full);
}
.bhp-course-card__progress-bar {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 6rpx; background: rgba(255,255,255,0.3);
}
.bhp-course-card__progress-fill {
  height: 100%; background: var(--bhp-primary-500);
  border-radius: var(--radius-full);
}
.bhp-course-card__info   { padding: 16rpx 20rpx 20rpx; }
.bhp-course-card__title  { font-size: 26rpx; font-weight: 600; color: var(--text-primary); line-height: 1.4; margin-bottom: 6rpx; display: block; }
.bhp-course-card__sub    { display: block; margin-bottom: 10rpx; }
.bhp-course-card__meta   { display: flex; justify-content: space-between; align-items: center; }

/* 水平布局 */
.bhp-course-card--horizontal { display: flex; flex-direction: row; height: 140rpx; }
.bhp-course-card--horizontal .bhp-course-card__cover {
  width: 180rpx; height: 140rpx; flex-shrink: 0;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}
.bhp-course-card--horizontal .bhp-course-card__info {
  flex: 1; display: flex; flex-direction: column;
  justify-content: center; padding: 12rpx 16rpx;
}
</style>
