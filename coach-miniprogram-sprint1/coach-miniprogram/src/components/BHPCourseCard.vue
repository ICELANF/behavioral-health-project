<template>
  <view class="course-card bhp-card bhp-card--hover" @tap="onTap">

    <!-- 封面图 -->
    <view class="course-card__cover">
      <image
        class="course-card__img"
        :src="course.cover_url || defaultCover"
        mode="aspectFill"
        lazy-load
      />
      <!-- 类型标签 -->
      <view class="course-card__type-badge">
        <text>{{ TYPE_ICON[course.content_type] || '📄' }}</text>
        <text class="course-card__type-text">{{ TYPE_LABEL[course.content_type] || '内容' }}</text>
      </view>
      <!-- 等级门控锁 -->
      <view class="course-card__lock" v-if="locked">
        <text>🔒</text>
      </view>
      <!-- 进度遮罩（进行中） -->
      <view class="course-card__progress-overlay" v-if="progressPct > 0 && progressPct < 100">
        <view class="course-card__progress-bar" :style="{ width: progressPct + '%' }"></view>
      </view>
      <!-- 完成标记 -->
      <view class="course-card__done" v-if="progressPct >= 100">
        <text>✅</text>
      </view>
    </view>

    <!-- 内容区 -->
    <view class="course-card__body">
      <text class="course-card__title line-clamp-2">{{ course.title }}</text>

      <view class="course-card__meta flex-start gap-2">
        <!-- 领域标签 -->
        <view class="bhp-badge bhp-badge--success" v-if="course.domain">
          <text>{{ DOMAIN_LABEL[course.domain] || course.domain }}</text>
        </view>
        <!-- 等级标签 -->
        <view class="bhp-badge bhp-badge--gray" v-if="course.level">
          <text>{{ course.level }}</text>
        </view>
        <!-- 有测验 -->
        <view class="bhp-badge bhp-badge--primary" v-if="course.has_quiz">
          <text>含测验</text>
        </view>
      </view>

      <!-- 底部：作者 + 浏览量 -->
      <view class="course-card__footer flex-between">
        <text class="course-card__author text-secondary-color">{{ course.author_name || '行健平台' }}</text>
        <text class="course-card__views text-secondary-color">{{ course.view_count || 0 }} 阅读</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface CourseItem {
  id: number
  content_type: string
  title: string
  cover_url?: string
  domain?: string
  level?: string
  has_quiz?: boolean
  view_count?: number
  author_name?: string
  progress_percent?: number
  status?: string
}

const props = defineProps<{
  course: CourseItem
  userLevel?: number   // 用于判断是否锁定
}>()

const emit = defineEmits<{ tap: [course: CourseItem] }>()

const TYPE_LABEL: Record<string, string> = {
  article:    '图文',
  video:      '视频',
  course:     '课程',
  audio:      '音频',
  card:       '练习卡',
  case_share: '案例'
}

const TYPE_ICON: Record<string, string> = {
  article:    '📖',
  video:      '▶️',
  course:     '📚',
  audio:      '🎵',
  card:       '🃏',
  case_share: '💬'
}

const DOMAIN_LABEL: Record<string, string> = {
  nutrition:  '营养',
  exercise:   '运动',
  sleep:      '睡眠',
  emotion:    '情绪',
  tcm:        '中医',
  metabolic:  '代谢',
  behavior:   '行为'
}

const LEVEL_GATE: Record<string, number> = {
  L0: 1, L1: 2, L2: 3, L3: 4, L4: 5, L5: 6
}

const locked = computed(() => {
  if (!props.course.level || !props.userLevel) return false
  const required = LEVEL_GATE[props.course.level] || 0
  return props.userLevel < required
})

const progressPct = computed(() => props.course.progress_percent || 0)

const defaultCover = '/static/default-cover.png'

function onTap() {
  if (!locked.value) emit('tap', props.course)
  else uni.showToast({ title: `需达到${props.course.level}解锁`, icon: 'none' })
}
</script>

<style scoped>
.course-card { padding: 0; overflow: hidden; }

.course-card__cover {
  position: relative;
  width: 100%;
  height: 180rpx;
  background: var(--bhp-gray-100);
}
.course-card__img { width: 100%; height: 100%; }

.course-card__type-badge {
  position: absolute;
  top: 8px; left: 8px;
  background: rgba(0,0,0,0.55);
  border-radius: 6px;
  padding: 2px 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.course-card__type-text { font-size: 20rpx; color: #fff; }

.course-card__lock {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}

.course-card__progress-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 4px;
  background: rgba(255,255,255,0.3);
}
.course-card__progress-bar {
  height: 100%;
  background: var(--bhp-primary-500);
  transition: width 0.3s;
}

.course-card__done {
  position: absolute;
  top: 8px; right: 8px;
  font-size: 32rpx;
}

.course-card__body {
  padding: 12px 14px 14px;
}
.course-card__title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 8px;
}
.course-card__meta {
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 6px;
}
.course-card__footer {
  margin-top: 8px;
}
.course-card__author,
.course-card__views { font-size: 22rpx; }
</style>
