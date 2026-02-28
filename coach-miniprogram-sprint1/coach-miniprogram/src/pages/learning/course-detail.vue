<template>
  <view class="cd-page">

    <!-- 封面 -->
    <view class="cd-cover" v-if="!loading && content?.cover_url">
      <image class="cd-cover__img" :src="content.cover_url" mode="aspectFill" />
      <view class="cd-cover__overlay">
        <text class="cd-cover__title">{{ content.title }}</text>
        <view class="cd-cover__meta flex-start gap-2 mt-2">
          <view class="bhp-badge bhp-badge--primary" v-if="content.module">
            <text>{{ content.module?.toUpperCase() }}</text>
          </view>
          <view class="bhp-badge bhp-badge--gray" v-if="content.level">
            <text>{{ content.level }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="bhp-skeleton" style="height: 360rpx; border-radius: 0;"></view>
      <view class="px-4 mt-4">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 100rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else-if="content">
      <!-- 整体进度 -->
      <view class="cd-overall px-4">
        <view class="cd-overall__card bhp-card bhp-card--flat">
          <view class="flex-between mb-2">
            <text class="text-sm font-semibold">整体学习进度</text>
            <text class="text-sm text-primary-color font-semibold">{{ overallProgress }}%</text>
          </view>
          <view class="cd-overall__bar">
            <view class="cd-overall__fill" :style="{ width: overallProgress + '%' }"></view>
          </view>
          <view class="flex-between mt-2">
            <text class="text-xs text-secondary-color">
              已完成 {{ completedCount }} / {{ totalChapters }} 章节
            </text>
            <text class="text-xs text-secondary-color">{{ content.view_count || 0 }} 人已学</text>
          </view>
        </view>
      </view>

      <!-- 摘要 -->
      <view class="cd-summary px-4" v-if="content.summary">
        <text class="text-sm text-secondary-color line-clamp-3">{{ content.summary }}</text>
      </view>

      <!-- 章节列表 -->
      <view class="cd-chapters px-4">
        <view class="cd-section-title">
          <text class="cd-section-title__text">课程章节</text>
          <text class="cd-section-title__count">{{ totalChapters }}节</text>
        </view>

        <view
          v-for="(chapter, index) in chapters"
          :key="chapter.id"
          class="cd-chapter bhp-card bhp-card--flat"
          @tap="goChapter(chapter)"
        >
          <!-- 序号 -->
          <view class="cd-chapter__num" :class="{ 'cd-chapter__num--done': chapter.completed }">
            <text v-if="!chapter.completed">{{ index + 1 }}</text>
            <text v-else>✓</text>
          </view>

          <!-- 信息 -->
          <view class="cd-chapter__body">
            <text class="cd-chapter__title line-clamp-1">{{ chapter.title }}</text>
            <view class="flex-start gap-2 mt-1">
              <text class="text-xs text-secondary-color">{{ TYPE_LABEL[chapter.content_type] || '内容' }}</text>
              <text class="text-xs text-secondary-color" v-if="chapter.duration">
                {{ formatDuration(chapter.duration) }}
              </text>
            </view>
          </view>

          <!-- 箭头 -->
          <text class="cd-chapter__arrow">›</text>
        </view>
      </view>

      <!-- 测验入口 -->
      <view class="cd-quiz-entry px-4" v-if="content.has_quiz && content.quiz_id">
        <view
          class="cd-quiz-card"
          :class="{ 'cd-quiz-card--available': overallProgress >= 80 }"
          @tap="overallProgress >= 80 ? goQuiz() : showQuizLock()"
        >
          <text class="cd-quiz-card__icon">📝</text>
          <view class="flex-1">
            <text class="cd-quiz-card__title">课程测验</text>
            <text class="cd-quiz-card__sub">
              {{ overallProgress >= 80 ? '完成测验可获得学分和积分' : `完成80%章节后解锁（当前${overallProgress}%）` }}
            </text>
          </view>
          <text class="cd-quiz-card__arrow" :class="{ 'cd-quiz-card__arrow--locked': overallProgress < 80 }">
            {{ overallProgress >= 80 ? '›' : '🔒' }}
          </text>
        </view>
      </view>
    </template>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { contentApi, type ContentDetail, type ChapterItem } from '@/api/learning'

const contentId     = ref(0)
const content       = ref<ContentDetail | null>(null)
const loading       = ref(false)
const chapters      = ref<ChapterItem[]>([])

const TYPE_LABEL: Record<string, string> = {
  article: '图文', video: '视频', course: '课程',
  audio: '音频', card: '练习卡'
}

const totalChapters = computed(() => chapters.value.length)
const completedCount= computed(() => chapters.value.filter(c => c.completed).length)
const overallProgress = computed(() => {
  if (!totalChapters.value) return 0
  return Math.round((completedCount.value / totalChapters.value) * 100)
})

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  contentId.value = Number(query.id || 0)
  if (contentId.value) await loadContent()
})

async function loadContent() {
  loading.value = true
  try {
    content.value = await contentApi.detail(contentId.value)
    chapters.value = content.value.chapters || []
    uni.setNavigationBarTitle({ title: content.value.title })
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function goChapter(chapter: ChapterItem) {
  uni.navigateTo({
    url: `/pages/learning/course-chapter?course_id=${contentId.value}&chapter_id=${chapter.id}`
  })
}

function goQuiz() {
  if (!content.value?.quiz_id) return
  uni.navigateTo({
    url: `/pages/learning/quiz?quiz_id=${content.value.quiz_id}&content_id=${contentId.value}`
  })
}

function showQuizLock() {
  uni.showToast({ title: '请先完成80%以上章节', icon: 'none' })
}
</script>

<style scoped>
.cd-page { background: var(--surface-secondary); min-height: 100vh; }

/* 封面 */
.cd-cover { position: relative; height: 360rpx; overflow: hidden; }
.cd-cover__img { width: 100%; height: 100%; }
.cd-cover__overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  padding: 24rpx 28rpx;
  background: linear-gradient(transparent, rgba(0,0,0,0.65));
}
.cd-cover__title { display: block; font-size: 32rpx; font-weight: 700; color: #fff; line-height: 1.4; }

/* 整体进度 */
.cd-overall { padding-top: 16rpx; }
.cd-overall__bar {
  height: 10rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.cd-overall__fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: width 0.5s;
}

.cd-summary { padding-top: 16rpx; }

/* 章节 */
.cd-chapters { padding-top: 16rpx; }
.cd-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.cd-section-title__text { font-size: 28rpx; font-weight: 700; color: var(--text-primary); }
.cd-section-title__count { font-size: 24rpx; color: var(--text-secondary); }

.cd-chapter {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 10rpx;
  cursor: pointer;
}
.cd-chapter:active { opacity: 0.8; }
.cd-chapter__num {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 2px solid var(--bhp-gray-300);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.cd-chapter__num--done {
  background: var(--bhp-success-500, #22c55e);
  border-color: var(--bhp-success-500, #22c55e);
  color: #fff;
  font-weight: 700;
}
.cd-chapter__body { flex: 1; overflow: hidden; }
.cd-chapter__title { font-size: 28rpx; color: var(--text-primary); font-weight: 500; }
.cd-chapter__arrow { font-size: 36rpx; color: var(--text-tertiary); }

/* 测验入口 */
.cd-quiz-entry { padding-top: 16rpx; }
.cd-quiz-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-100);
  border: 1px solid var(--border-light);
  cursor: pointer;
  opacity: 0.6;
}
.cd-quiz-card--available {
  background: var(--bhp-primary-50);
  border-color: var(--bhp-primary-200, #a7f3d0);
  opacity: 1;
}
.cd-quiz-card__icon { font-size: 40rpx; }
.cd-quiz-card__title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cd-quiz-card__sub { display: block; font-size: 22rpx; color: var(--text-secondary); margin-top: 4rpx; }
.cd-quiz-card__arrow { font-size: 36rpx; color: var(--bhp-primary-500); }
.cd-quiz-card__arrow--locked { color: var(--text-tertiary); font-size: 28rpx; }
</style>
