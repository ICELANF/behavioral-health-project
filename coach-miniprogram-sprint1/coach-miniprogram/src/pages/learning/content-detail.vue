<template>
  <view class="detail-page">

    <!-- 骨架屏 -->
    <template v-if="loading">
      <view class="detail-skeleton-cover bhp-skeleton"></view>
      <view class="px-4 mt-4">
        <view class="bhp-skeleton" style="height: 40rpx; margin-bottom: 12rpx;"></view>
        <view class="bhp-skeleton" style="height: 28rpx; width: 60%; margin-bottom: 24rpx;"></view>
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 24rpx; margin-bottom: 10rpx;"></view>
      </view>
    </template>

    <template v-else-if="content">
      <!-- 封面（图文可无封面）-->
      <view class="detail-cover" v-if="content.cover_url">
        <image class="detail-cover__img" :src="content.cover_url" mode="aspectFill" />
      </view>

      <!-- 标题区 -->
      <view class="detail-header px-4">
        <view class="flex-start gap-2 mb-2">
          <view class="bhp-badge bhp-badge--success" v-if="content.domain">
            <text>{{ DOMAIN_LABEL[content.domain] || content.domain }}</text>
          </view>
          <view class="bhp-badge bhp-badge--gray" v-if="content.level">
            <text>{{ content.level }}</text>
          </view>
          <view class="bhp-badge bhp-badge--primary" v-if="content.module">
            <text>{{ content.module?.toUpperCase() }}</text>
          </view>
        </view>
        <text class="detail-title">{{ content.title }}</text>
        <view class="detail-meta flex-start gap-4 mt-2">
          <text class="text-xs text-secondary-color">{{ content.author_name || '行健平台' }}</text>
          <text class="text-xs text-secondary-color" v-if="content.word_count">约{{ content.word_count }}字</text>
          <text class="text-xs text-secondary-color">{{ content.view_count || 0 }} 阅读</text>
        </view>
        <!-- 进度 -->
        <view class="detail-progress-bar mt-3" v-if="progress > 0">
          <view class="detail-progress-fill" :style="{ width: progress + '%' }"></view>
        </view>
      </view>

      <!-- 摘要 -->
      <view class="detail-summary px-4" v-if="content.summary">
        <view class="detail-summary__card">
          <text class="detail-summary__icon">💡</text>
          <text class="detail-summary__text">{{ content.summary }}</text>
        </view>
      </view>

      <!-- 正文（富文本）-->
      <view class="detail-body px-4" v-if="content.body">
        <rich-text :nodes="content.body" class="detail-rich-text"></rich-text>
      </view>

      <!-- 标签 -->
      <view class="detail-tags px-4" v-if="content.tags?.length">
        <view class="flex-start gap-2 flex-wrap">
          <view
            v-for="tag in content.tags"
            :key="tag"
            class="bhp-badge bhp-badge--gray"
          >
            <text># {{ tag }}</text>
          </view>
        </view>
      </view>

      <!-- 底部操作栏 -->
      <view class="detail-action-bar">
        <!-- 有测验时显示 -->
        <view
          v-if="content.has_quiz && content.quiz_id && !quizDone"
          class="bhp-btn bhp-btn--primary bhp-btn--full"
          @tap="goQuiz"
        >
          <text>开始测验</text>
        </view>
        <view
          v-else-if="quizDone"
          class="bhp-btn bhp-btn--secondary bhp-btn--full"
          @tap="goQuiz"
        >
          <text>重做测验</text>
        </view>
        <!-- 标记完成 -->
        <view
          v-else-if="!completed"
          class="bhp-btn bhp-btn--primary bhp-btn--full"
          @tap="markComplete"
        >
          <text v-if="!completing">标记已学完</text>
          <text v-else>提交中...</text>
        </view>
        <view v-else class="detail-completed-bar">
          <text>✓ 已完成学习</text>
        </view>
      </view>
    </template>

    <!-- 错误状态 -->
    <view class="detail-error" v-else-if="!loading">
      <text class="detail-error__icon">😕</text>
      <text class="detail-error__text">内容加载失败</text>
      <view class="bhp-btn bhp-btn--secondary mt-4" @tap="loadContent">重试</view>
    </view>

    <view style="height: 120rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { contentApi, learningApi, type ContentDetail } from '@/api/learning'

const userStore = useUserStore()

const contentId = ref(0)
const content   = ref<ContentDetail | null>(null)
const loading   = ref(false)
const progress  = ref(0)
const completed = ref(false)
const completing= ref(false)
const quizDone  = ref(false)

const DOMAIN_LABEL: Record<string, string> = {
  nutrition: '营养', exercise: '运动', sleep: '睡眠',
  emotion: '情绪', tcm: '中医', metabolic: '代谢', behavior: '行为'
}

onMounted(async () => {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  const query = cur.$page?.options || cur.options || {}
  contentId.value = Number(query.id || 0)
  if (contentId.value) {
    await loadContent()
    await loadProgress()
  }
})

async function loadContent() {
  if (!contentId.value) return
  loading.value = true
  try {
    content.value = await contentApi.detail(contentId.value)
    uni.setNavigationBarTitle({ title: content.value.title })
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadProgress() {
  try {
    const p = await contentApi.getProgress(contentId.value)
    progress.value = p.progress_percent || 0
    completed.value = progress.value >= 100
  } catch { /* 静默 */ }
}

async function markComplete() {
  completing.value = true
  try {
    await contentApi.saveProgress({
      content_id: contentId.value,
      progress_percent: 100,
      status: 'completed',
      time_spent_seconds: 0
    })
    completed.value = true
    progress.value = 100
    // 联动积分
    if (content.value?.module) {
      const res = await learningApi.completeModule(
        `${content.value.module}_${contentId.value}`,
        'content'
      )
      if (res.points_earned > 0 || res.credits_earned > 0) {
        uni.showToast({
          title: `+${res.points_earned}积分${res.credits_earned > 0 ? ` +${res.credits_earned}学分` : ''}`,
          icon: 'none',
          duration: 2500
        })
        userStore.addPoints(res.points_earned, 0, 0)
      }
    } else {
      uni.showToast({ title: '已标记完成 ✓', icon: 'none' })
    }
  } catch {
    uni.showToast({ title: '操作失败，请重试', icon: 'none' })
  } finally {
    completing.value = false
  }
}

function goQuiz() {
  if (!content.value?.quiz_id) return
  uni.navigateTo({
    url: `/pages/learning/quiz?quiz_id=${content.value.quiz_id}&content_id=${contentId.value}`
  })
}
</script>

<style scoped>
.detail-page { background: var(--surface); min-height: 100vh; }

.detail-skeleton-cover { height: 400rpx; border-radius: 0; }

.detail-cover { width: 100%; height: 400rpx; overflow: hidden; }
.detail-cover__img { width: 100%; height: 100%; }

.detail-header { padding-top: 24rpx; padding-bottom: 16rpx; border-bottom: 1px solid var(--border-light); }
.detail-title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}
.detail-progress-bar {
  height: 6rpx;
  background: var(--bhp-gray-200);
  border-radius: 9999px;
  overflow: hidden;
}
.detail-progress-fill {
  height: 100%;
  background: var(--bhp-primary-500);
  border-radius: 9999px;
  transition: width 0.3s;
}

.detail-summary { padding-top: 20rpx; }
.detail-summary__card {
  background: var(--bhp-primary-50);
  border-radius: var(--radius-lg);
  padding: 20rpx;
  display: flex;
  gap: 12rpx;
}
.detail-summary__icon { font-size: 32rpx; flex-shrink: 0; }
.detail-summary__text { font-size: 26rpx; color: var(--bhp-primary-700); line-height: 1.6; flex: 1; }

.detail-body { padding-top: 24rpx; }
.detail-rich-text {
  font-size: 28rpx;
  color: var(--text-primary);
  line-height: 1.8;
}

.detail-tags { padding-top: 24rpx; }

/* 底部操作栏 */
.detail-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16rpx 32rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  box-shadow: 0 -4px 12px rgba(0,0,0,0.06);
}
.detail-completed-bar {
  text-align: center;
  font-size: 28rpx;
  color: var(--bhp-success-500);
  font-weight: 600;
  padding: 16rpx;
}

/* 错误 */
.detail-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 16rpx;
}
.detail-error__icon { font-size: 80rpx; }
.detail-error__text { font-size: 28rpx; color: var(--text-tertiary); }
</style>
