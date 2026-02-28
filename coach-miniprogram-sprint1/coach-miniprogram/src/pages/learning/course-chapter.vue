<template>
  <view class="chapter-page">

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="px-4 mt-4">
        <view class="bhp-skeleton" style="height: 40rpx; width: 70%; margin-bottom: 12rpx;"></view>
        <view v-for="i in 6" :key="i" class="bhp-skeleton" style="height: 24rpx; margin-bottom: 8rpx;"></view>
      </view>
    </template>

    <template v-else-if="chapter">

      <!-- 视频章节 -->
      <template v-if="chapter.content_type === 'video' && chapter.media_url">
        <view class="chapter-video-wrap">
          <video
            id="chapter-video"
            class="chapter-video"
            :src="chapter.media_url"
            :initial-time="initialTime"
            :enable-progress-gesture="true"
            :show-fullscreen-btn="true"
            :show-play-btn="true"
            :show-center-play-btn="true"
            object-fit="contain"
            @timeupdate="onTimeUpdate"
            @ended="onVideoEnded"
          ></video>
        </view>
      </template>

      <!-- 图文/音频章节 -->
      <template v-else-if="chapter.content_type === 'article' && chapterBody">
        <view class="chapter-body px-4">
          <rich-text :nodes="chapterBody" class="chapter-rich-text"></rich-text>
        </view>
      </template>

      <!-- 通用内容区 -->
      <view class="chapter-info px-4">
        <text class="chapter-title">{{ chapter.title }}</text>
        <view class="chapter-meta flex-start gap-3 mt-2">
          <text class="text-xs text-secondary-color">第 {{ chapterIndex + 1 }} 章节</text>
          <text class="text-xs text-secondary-color" v-if="chapter.duration">
            {{ formatDuration(chapter.duration) }}
          </text>
        </view>

        <!-- 进度条（视频时显示）-->
        <view class="chapter-progress-bar mt-3" v-if="chapter.content_type === 'video' && totalDuration > 0">
          <view class="chapter-progress-fill" :style="{ width: progressPercent + '%' }"></view>
        </view>
      </view>

      <!-- 章节导航 -->
      <view class="chapter-nav px-4">
        <view
          class="chapter-nav-btn"
          :class="{ 'chapter-nav-btn--disabled': chapterIndex <= 0 }"
          @tap="gotoPrev"
        >
          <text>‹ 上一章</text>
        </view>
        <view
          v-if="!chapterCompleted"
          class="chapter-nav-btn chapter-nav-btn--primary"
          @tap="markDone"
        >
          <text v-if="!completing">完成本章</text>
          <text v-else>提交中...</text>
        </view>
        <view
          v-else
          class="chapter-nav-btn chapter-nav-btn--primary"
          @tap="gotoNext"
        >
          <text>下一章 ›</text>
        </view>
      </view>
    </template>

    <!-- 错误 -->
    <view class="chapter-error" v-else-if="!loading">
      <text class="chapter-error__icon">😕</text>
      <text class="chapter-error__text">章节加载失败</text>
      <view class="bhp-btn bhp-btn--secondary mt-4" @tap="loadChapter">重试</view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { contentApi, type ChapterItem, type ContentDetail } from '@/api/learning'

const courseId     = ref(0)
const chapterId    = ref(0)
const chapterIndex = ref(0)
const course       = ref<ContentDetail | null>(null)
const chapter      = ref<ChapterItem | null>(null)
const chapterBody  = ref('')
const loading      = ref(false)
const completing   = ref(false)
const chapterCompleted = ref(false)
const currentTime  = ref(0)
const totalDuration= ref(0)
const initialTime  = ref(0)

let heartbeatTimer: any = null

const progressPercent = computed(() => {
  if (!totalDuration.value) return 0
  return Math.min((currentTime.value / totalDuration.value) * 100, 100)
})

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  courseId.value  = Number(query.course_id || 0)
  chapterId.value = Number(query.chapter_id || 0)
  if (courseId.value) await loadCourse()
})

onUnmounted(() => {
  if (heartbeatTimer) clearInterval(heartbeatTimer)
})

async function loadCourse() {
  loading.value = true
  try {
    course.value = await contentApi.detail(courseId.value)
    const chapters = course.value.chapters || []
    const idx = chapters.findIndex(c => c.id === chapterId.value)
    chapterIndex.value = idx >= 0 ? idx : 0
    chapter.value = chapters[chapterIndex.value] || null
    if (chapter.value) {
      chapterCompleted.value = !!chapter.value.completed
      if (chapter.value.duration) totalDuration.value = chapter.value.duration
      uni.setNavigationBarTitle({ title: chapter.value.title })
      // 加载图文正文（通过内容详情接口，用 chapter.id 查询）
      if (chapter.value.content_type === 'article') {
        await loadChapter()
      }
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadChapter() {
  if (!chapter.value) return
  try {
    const detail = await contentApi.detail(chapter.value.id)
    chapterBody.value = detail.body || ''
  } catch { /* 静默 */ }
}

function onTimeUpdate(e: any) {
  currentTime.value = e.detail?.currentTime || 0
  if (e.detail?.duration) totalDuration.value = e.detail.duration
}

function onVideoEnded() {
  chapterCompleted.value = true
  saveChapterProgress(100)
  showNextTip()
}

async function markDone() {
  completing.value = true
  try {
    // 保存进度到课程
    await contentApi.saveProgress({
      content_id: courseId.value,
      progress_percent: calcCourseProgress(),
      status: 'in_progress'
    })
    chapterCompleted.value = true
    // 更新本地章节完成状态
    if (course.value?.chapters) {
      const ch = course.value.chapters.find(c => c.id === chapterId.value)
      if (ch) ch.completed = true
    }
    uni.showToast({ title: '章节完成 ✓', icon: 'none' })
    // 自动切到下一章
    setTimeout(() => gotoNext(), 1500)
  } catch {
    uni.showToast({ title: '操作失败', icon: 'none' })
  } finally {
    completing.value = false
  }
}

function calcCourseProgress(): number {
  const chapters = course.value?.chapters || []
  if (!chapters.length) return 0
  const done = chapters.filter(c => c.completed).length
  return Math.round((done / chapters.length) * 100)
}

async function saveChapterProgress(pct: number) {
  try {
    await contentApi.saveProgress({
      content_id: courseId.value,
      progress_percent: calcCourseProgress(),
      status: 'in_progress'
    })
  } catch { /* 静默 */ }
}

function showNextTip() {
  const chapters = course.value?.chapters || []
  if (chapterIndex.value < chapters.length - 1) {
    uni.showToast({ title: '可切换下一章节', icon: 'none', duration: 2000 })
  }
}

function gotoPrev() {
  const chapters = course.value?.chapters || []
  if (chapterIndex.value <= 0) return
  const prev = chapters[chapterIndex.value - 1]
  uni.redirectTo({
    url: `/pages/learning/course-chapter?course_id=${courseId.value}&chapter_id=${prev.id}`
  })
}

function gotoNext() {
  const chapters = course.value?.chapters || []
  if (chapterIndex.value >= chapters.length - 1) {
    uni.showToast({ title: '已是最后一章', icon: 'none' })
    return
  }
  const next = chapters[chapterIndex.value + 1]
  uni.redirectTo({
    url: `/pages/learning/course-chapter?course_id=${courseId.value}&chapter_id=${next.id}`
  })
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}
</script>

<style scoped>
.chapter-page { background: var(--surface); min-height: 100vh; }

.chapter-video-wrap { background: #000; }
.chapter-video { width: 100%; height: 420rpx; }

.chapter-info {
  padding-top: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1px solid var(--border-light);
}
.chapter-title { display: block; font-size: 30rpx; font-weight: 700; color: var(--text-primary); }
.chapter-progress-bar {
  height: 8rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.chapter-progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: width 0.5s;
}

.chapter-body {
  padding-top: 24rpx;
  padding-bottom: 16rpx;
}
.chapter-rich-text { font-size: 28rpx; color: var(--text-primary); line-height: 1.8; }

/* 导航 */
.chapter-nav {
  display: flex;
  gap: 16rpx;
  padding-top: 24rpx;
}
.chapter-nav-btn {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: var(--radius-lg);
  font-size: 28rpx;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  cursor: pointer;
}
.chapter-nav-btn:active { opacity: 0.7; }
.chapter-nav-btn--primary {
  background: var(--bhp-primary-500);
  border-color: var(--bhp-primary-500);
  color: #fff;
  font-weight: 600;
}
.chapter-nav-btn--disabled { opacity: 0.4; pointer-events: none; }

/* 错误 */
.chapter-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 16rpx;
}
.chapter-error__icon { font-size: 80rpx; }
.chapter-error__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
