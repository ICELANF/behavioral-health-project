<template>
  <view class="cd-page">

    <view class="cd-navbar safe-area-top">
      <view class="cd-navbar__back" @tap="goBack"><text class="cd-navbar__arrow">‹</text></view>
      <text class="cd-navbar__title">课程详情</text>
      <view class="cd-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cd-body">

      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 360rpx; border-radius: 0;"></view>
        <view class="bhp-skeleton" style="height: 120rpx; margin: 20rpx 32rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else-if="course">
        <!-- 封面 -->
        <image class="cd-cover" :src="course.cover_url || '/static/covers/default.jpg'" mode="aspectFill" />

        <!-- 基本信息 -->
        <view class="cd-info">
          <text class="cd-info__title">{{ course.title || course.name }}</text>
          <text class="cd-info__desc" v-if="course.description">{{ course.description }}</text>
          <view class="cd-info__meta">
            <text v-if="course.author">讲师：{{ course.author.name || course.author }}</text>
            <text v-if="course.total_chapters">{{ course.total_chapters }} 章节</text>
            <text v-if="course.estimated_minutes">约 {{ course.estimated_minutes }} 分钟</text>
          </view>
        </view>

        <!-- 章节列表 -->
        <view class="cd-chapters">
          <text class="cd-chapters__title">课程章节</text>
          <view v-if="chapters.length" class="cd-chapter-list">
            <view
              v-for="(ch, idx) in chapters"
              :key="ch.id || idx"
              class="cd-chapter"
              @tap="playChapter(ch)"
            >
              <view class="cd-chapter__num" :class="{ 'cd-chapter__num--done': ch.completed }">
                <text v-if="ch.completed">✓</text>
                <text v-else>{{ idx + 1 }}</text>
              </view>
              <view class="cd-chapter__body">
                <text class="cd-chapter__name">{{ ch.title || ch.name }}</text>
                <text class="cd-chapter__dur" v-if="ch.duration_minutes">{{ ch.duration_minutes }} 分钟</text>
              </view>
              <text class="cd-chapter__arrow">›</text>
            </view>
          </view>
          <view v-else class="cd-no-chapter">
            <text class="text-sm text-secondary-color">暂无章节</text>
          </view>
        </view>
      </template>

    </scroll-view>

    <!-- 底部按钮 -->
    <view class="cd-footer safe-area-bottom" v-if="course">
      <view class="cd-enroll-btn" @tap="startLearning">
        <text>{{ hasProgress ? '继续学习' : '开始学习' }}</text>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/request'

const course     = ref<any>(null)
const chapters   = ref<any[]>([])
const loading    = ref(false)
const courseId   = ref(0)

const hasProgress = computed(() => chapters.value.some(c => c.completed))

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  courseId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (courseId.value) loadCourse()
})

async function loadCourse() {
  loading.value = true
  try {
    const res = await http.get<any>(`/v1/content/course/${courseId.value}`)
    course.value = res
    chapters.value = res.chapters || res.sections || []
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function playChapter(ch: any) {
  const type = ch.content_type || 'article'
  const id = ch.content_id || ch.id
  if (type === 'video') {
    uni.navigateTo({ url: `/pages/learning/video-player?id=${id}` })
  } else {
    uni.navigateTo({ url: `/pages/learning/content-detail?id=${id}` })
  }
}

function startLearning() {
  const next = chapters.value.find(c => !c.completed) || chapters.value[0]
  if (next) playChapter(next)
}

function goBack() {
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}
</script>

<style scoped>
.cd-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cd-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light);
}
.cd-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cd-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cd-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }
.cd-navbar__placeholder { width: 64rpx; }

.cd-body { flex: 1; padding-bottom: 140rpx; }
.cd-cover { width: 100%; height: 360rpx; background: var(--bhp-gray-100); }

.cd-info { padding: 24rpx 32rpx; background: var(--surface); }
.cd-info__title { display: block; font-size: 32rpx; font-weight: 800; color: var(--text-primary); margin-bottom: 10rpx; }
.cd-info__desc { display: block; font-size: 24rpx; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12rpx; }
.cd-info__meta { display: flex; gap: 20rpx; font-size: 22rpx; color: var(--text-tertiary); }

.cd-chapters { padding: 20rpx 32rpx; }
.cd-chapters__title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }
.cd-chapter-list { display: flex; flex-direction: column; gap: 12rpx; }

.cd-chapter {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--surface); border-radius: var(--radius-lg);
  padding: 20rpx; border: 1px solid var(--border-light); cursor: pointer;
}
.cd-chapter:active { opacity: 0.85; }
.cd-chapter__num {
  width: 48rpx; height: 48rpx; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; font-weight: 700; color: var(--text-tertiary);
  background: var(--surface-secondary);
}
.cd-chapter__num--done { background: var(--bhp-primary-500); color: #fff; }
.cd-chapter__body { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.cd-chapter__name { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.cd-chapter__dur { font-size: 20rpx; color: var(--text-tertiary); }
.cd-chapter__arrow { font-size: 32rpx; color: var(--text-tertiary); flex-shrink: 0; }
.cd-no-chapter { text-align: center; padding: 40rpx; }

.cd-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  padding: 16rpx 32rpx 24rpx; background: var(--surface);
  border-top: 1px solid var(--border-light);
}
.cd-enroll-btn {
  height: 96rpx; border-radius: var(--radius-lg); background: var(--bhp-primary-500);
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; font-weight: 700; color: #fff; cursor: pointer;
}
.cd-enroll-btn:active { opacity: 0.85; }
</style>
