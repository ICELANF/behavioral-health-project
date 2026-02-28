<template>
  <view class="cc-page">
    <view class="cc-navbar safe-area-top">
      <view class="cc-navbar__back" @tap="goBack"><text class="cc-navbar__arrow">&#8249;</text></view>
      <text class="cc-navbar__title">{{ chapter?.title || '章节学习' }}</text>
      <view class="cc-navbar__placeholder"></view>
    </view>

    <scroll-view scroll-y class="cc-body">
      <template v-if="loading">
        <view class="bhp-skeleton" style="height: 360rpx; border-radius: var(--radius-lg);"></view>
      </template>
      <template v-else-if="chapter">

        <!-- 章节头 -->
        <view class="cc-header">
          <text class="cc-header__course">{{ chapter.course_title || '所属课程' }}</text>
          <text class="cc-header__title">{{ chapter.title }}</text>
          <text class="cc-header__order" v-if="chapter.order_num">第 {{ chapter.order_num }} 章</text>
        </view>

        <!-- 视频内容 -->
        <view class="cc-media" v-if="chapter.video_url">
          <video
            class="cc-video"
            :src="chapter.video_url"
            :poster="chapter.cover_url"
            controls
            object-fit="contain"
          />
        </view>

        <!-- 图文内容 -->
        <view class="cc-content" v-if="chapter.content">
          <rich-text :nodes="chapter.content"></rich-text>
        </view>

        <!-- 完成标记 -->
        <view class="cc-complete" @tap="markComplete">
          <view class="cc-complete__check">
            <text>{{ completed ? '&#9745;' : '&#9744;' }}</text>
          </view>
          <text class="cc-complete__text">{{ completed ? '已完成本章' : '标记为已完成' }}</text>
        </view>

      </template>
    </scroll-view>

    <!-- 上一章/下一章 -->
    <view class="cc-footer safe-area-bottom" v-if="chapter">
      <view class="cc-footer__btn" :class="{ 'cc-footer__btn--disabled': !chapter.prev_id }" @tap="goPrev">
        <text>上一章</text>
      </view>
      <view class="cc-footer__btn cc-footer__btn--next" :class="{ 'cc-footer__btn--disabled': !chapter.next_id }" @tap="goNext">
        <text>下一章</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const chapter   = ref<any>(null)
const loading   = ref(false)
const completed = ref(false)
const chapterId = ref(0)

onMounted(() => {
  const pages = getCurrentPages()
  const pg = pages[pages.length - 1] as any
  chapterId.value = Number(pg.$page?.options?.id || pg.options?.id || 0)
  if (chapterId.value) loadChapter(chapterId.value)
})

async function loadChapter(id: number) {
  loading.value = true
  try {
    chapter.value = await http.get<any>(`/v1/content/chapter/${id}`)
    completed.value = chapter.value.completed ?? false
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function markComplete() {
  if (completed.value) return
  try {
    await http.post(`/v1/content/chapter/${chapterId.value}/complete`, {})
    completed.value = true
    uni.showToast({ title: '已标记完成', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  }
}

function goPrev() {
  if (!chapter.value?.prev_id) return
  uni.redirectTo({ url: `/pages/learning/course-chapter?id=${chapter.value.prev_id}` })
}

function goNext() {
  if (!chapter.value?.next_id) return
  uni.redirectTo({ url: `/pages/learning/course-chapter?id=${chapter.value.next_id}` })
}

function goBack() { uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) }) }
</script>

<style scoped>
.cc-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }
.cc-navbar { display: flex; align-items: center; justify-content: space-between; padding: 8rpx 24rpx; background: var(--surface); border-bottom: 1px solid var(--border-light); }
.cc-navbar__back { width: 64rpx; height: 64rpx; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.cc-navbar__arrow { font-size: 48rpx; color: var(--text-primary); font-weight: 300; }
.cc-navbar__title { font-size: 28rpx; font-weight: 600; color: var(--text-primary); max-width: 400rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cc-navbar__placeholder { width: 64rpx; }
.cc-body { flex: 1; padding: 20rpx 32rpx 160rpx; }

.cc-header { margin-bottom: 24rpx; }
.cc-header__course { display: block; font-size: 22rpx; color: var(--text-tertiary); margin-bottom: 8rpx; }
.cc-header__title { display: block; font-size: 32rpx; font-weight: 800; color: var(--text-primary); margin-bottom: 4rpx; }
.cc-header__order { display: block; font-size: 22rpx; color: var(--bhp-primary-500); font-weight: 600; }

.cc-media { margin-bottom: 24rpx; border-radius: var(--radius-lg); overflow: hidden; }
.cc-video { width: 100%; height: 400rpx; }

.cc-content {
  background: var(--surface); border-radius: var(--radius-lg); padding: 24rpx; margin-bottom: 24rpx;
  border: 1px solid var(--border-light); font-size: 28rpx; color: var(--text-primary); line-height: 1.8;
}

.cc-complete {
  display: flex; align-items: center; gap: 12rpx; padding: 20rpx 24rpx;
  background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border-light); cursor: pointer;
}
.cc-complete__check { font-size: 36rpx; color: var(--bhp-primary-500); }
.cc-complete__text { font-size: 26rpx; font-weight: 600; color: var(--text-primary); }

.cc-footer {
  position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 16rpx;
  padding: 16rpx 32rpx 24rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.cc-footer__btn {
  flex: 1; height: 80rpx; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; background: var(--surface-secondary); color: var(--text-secondary);
  border: 1px solid var(--border-light); cursor: pointer;
}
.cc-footer__btn--next { background: var(--bhp-primary-500); color: #fff; border: none; }
.cc-footer__btn--disabled { opacity: 0.4; }
.cc-footer__btn:active { opacity: 0.85; }
</style>
