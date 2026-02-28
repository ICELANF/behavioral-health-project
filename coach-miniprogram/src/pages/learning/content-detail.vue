<template>
  <view class="cd-page">

    <!-- 导航栏 -->
    <view class="cd-navbar safe-area-top">
      <view class="cd-navbar__back" @tap="goBack">
        <text class="cd-navbar__arrow">‹</text>
      </view>
      <text class="cd-navbar__title">内容详情</text>
      <view class="cd-navbar__placeholder"></view>
    </view>

    <scroll-view
      scroll-y
      class="cd-body"
      @scroll="onScroll"
      :scroll-top="0"
    >

      <!-- 封面 -->
      <image
        v-if="content?.cover_url"
        class="cd-cover"
        :src="content.cover_url"
        mode="aspectFill"
      />

      <!-- 标题区 -->
      <view class="cd-header">
        <text class="cd-header__title">{{ content?.title || '加载中...' }}</text>
        <view class="cd-header__meta">
          <text class="cd-header__author">{{ content?.author || '行健平台' }}</text>
          <text class="cd-header__time">{{ formatDate(content?.published_at) }}</text>
        </view>
      </view>

      <!-- 正文 -->
      <view class="cd-content">
        <rich-text :nodes="content?.html_content || content?.content || ''" />
      </view>

      <!-- Tab: 评论 -->
      <view class="cd-section">
        <view class="cd-section__tabs">
          <view
            class="cd-section__tab"
            :class="{ 'cd-section__tab--active': activeTab === 'comments' }"
            @tap="activeTab = 'comments'"
          >
            <text>评论 ({{ comments.length }})</text>
          </view>
          <view
            class="cd-section__tab"
            :class="{ 'cd-section__tab--active': activeTab === 'related' }"
            @tap="activeTab = 'related'"
          >
            <text>相关推荐</text>
          </view>
        </view>

        <!-- 评论列表 -->
        <template v-if="activeTab === 'comments'">
          <view class="cd-comments" v-if="comments.length">
            <view v-for="c in comments" :key="c.id" class="cd-comment">
              <image class="cd-comment__avatar" :src="c.avatar || '/static/default-avatar.png'" mode="aspectFill" />
              <view class="cd-comment__body">
                <view class="cd-comment__top">
                  <text class="cd-comment__name">{{ c.username }}</text>
                  <text class="cd-comment__time">{{ formatDate(c.created_at) }}</text>
                </view>
                <text class="cd-comment__text">{{ c.content }}</text>
              </view>
            </view>
          </view>
          <view class="cd-empty-inline" v-else>
            <text>暂无评论，来说两句吧</text>
          </view>
        </template>

        <!-- 相关推荐 -->
        <template v-if="activeTab === 'related'">
          <view class="cd-related" v-if="related.length">
            <view v-for="r in related" :key="r.id" class="cd-related__item" @tap="goContent(r.id)">
              <text class="cd-related__title">{{ r.title }}</text>
              <text class="cd-related__type">{{ r.content_type || '图文' }}</text>
            </view>
          </view>
          <view class="cd-empty-inline" v-else>
            <text>暂无推荐</text>
          </view>
        </template>
      </view>

      <!-- 底部占位 -->
      <view style="height: 200rpx;"></view>
    </scroll-view>

    <!-- 底部互动栏 -->
    <view class="cd-bar safe-area-bottom">
      <!-- 评论输入 -->
      <view class="cd-bar__input" @tap="openCommentInput">
        <text class="cd-bar__input-text">写评论...</text>
      </view>
      <view class="cd-bar__actions">
        <view class="cd-bar__action" @tap="toggleLike">
          <text>{{ liked ? '❤️' : '🤍' }}</text>
          <text class="cd-bar__count">{{ content?.like_count ?? 0 }}</text>
        </view>
        <view class="cd-bar__action" @tap="toggleFav">
          <text>{{ favorited ? '⭐' : '☆' }}</text>
          <text class="cd-bar__count">{{ content?.fav_count ?? 0 }}</text>
        </view>
        <view class="cd-bar__action" @tap="doShare">
          <text>↗</text>
        </view>
      </view>
    </view>

    <!-- 评论弹窗 -->
    <view class="cd-modal" v-if="showCommentModal" @tap="showCommentModal = false">
      <view class="cd-modal__box" @tap.stop>
        <textarea
          class="cd-modal__input"
          v-model="commentText"
          placeholder="写下你的评论..."
          :maxlength="500"
          :auto-focus="true"
        />
        <view class="cd-modal__submit" @tap="submitComment">
          <text>发布</text>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup lang="ts">
import { onLoad } from '@dcloudio/uni-app'
import { ref, onMounted } from 'vue'
import http from '@/api/request'

const contentId   = ref(0)
const content     = ref<any>(null)
const comments    = ref<any[]>([])
const related     = ref<any[]>([])
const activeTab   = ref('comments')
const liked       = ref(false)
const favorited   = ref(false)
const completed   = ref(false)
const commentText = ref('')
const showCommentModal = ref(false)
const scrollHeight     = ref(0)

onLoad((query: any) => {
  contentId.value = Number(query?.id || 0)
})

onMounted(async () => {
  if (contentId.value) {
    await Promise.all([loadContent(), loadComments()])
  }
})

async function loadContent() {
  try {
    const res = await http.get<any>(`/v1/content/${contentId.value}`)
    content.value = res
    liked.value     = !!res.is_liked
    favorited.value = !!res.is_favorited
    // 加载相关推荐
    if (res.related_ids?.length) {
      related.value = res.related || []
    }
  } catch {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

async function loadComments() {
  try {
    const res = await http.get<any>(`/v1/content/${contentId.value}/comments`)
    comments.value = res.items || res.comments || []
  } catch {}
}

function onScroll(e: any) {
  const { scrollTop, scrollHeight: sh } = e.detail
  // 滚动到底部 80% 触发完成
  if (!completed.value && sh > 0 && scrollTop / sh > 0.8) {
    completed.value = true
    markComplete()
  }
}

async function markComplete() {
  try {
    await http.post('/v1/content/user/learning-progress', { content_id: contentId.value, progress_pct: 100 })
  } catch {}
}

async function toggleLike() {
  try {
    await http.post(`/v1/content/${contentId.value}/like`, {})
    liked.value = !liked.value
    if (content.value) {
      content.value.like_count = liked.value
        ? (content.value.like_count || 0) + 1
        : Math.max(0, (content.value.like_count || 1) - 1)
    }
  } catch {}
}

async function toggleFav() {
  try {
    await http.post(`/v1/content/${contentId.value}/collect`, {})
    favorited.value = !favorited.value
    if (content.value) {
      content.value.fav_count = favorited.value
        ? (content.value.fav_count || 0) + 1
        : Math.max(0, (content.value.fav_count || 1) - 1)
    }
  } catch {}
}

function doShare() {
  uni.showToast({ title: '已复制链接', icon: 'success' })
}

function openCommentInput() {
  commentText.value = ''
  showCommentModal.value = true
}

async function submitComment() {
  const text = commentText.value.trim()
  if (!text) {
    uni.showToast({ title: '请输入评论', icon: 'none' })
    return
  }
  try {
    await http.post(`/v1/content/${contentId.value}/comment`, { content: text })
    showCommentModal.value = false
    commentText.value = ''
    uni.showToast({ title: '评论成功', icon: 'success' })
    await loadComments()
  } catch {
    uni.showToast({ title: '评论失败', icon: 'none' })
  }
}

function formatDate(d: string | undefined): string {
  if (!d) return ''
  return d.slice(0, 10)
}

function goContent(id: number) {
  uni.redirectTo({ url: `/pages/learning/content-detail?id=${id}` })
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

.cd-body { flex: 1; }

/* 封面 */
.cd-cover { width: 100%; height: 400rpx; display: block; }

/* 标题 */
.cd-header { background: var(--surface); padding: 24rpx 32rpx; }
.cd-header__title { font-size: 34rpx; font-weight: 800; color: var(--text-primary); line-height: 1.4; display: block; }
.cd-header__meta { display: flex; gap: 16rpx; margin-top: 12rpx; }
.cd-header__author { font-size: 24rpx; color: var(--bhp-primary-500); font-weight: 600; }
.cd-header__time { font-size: 24rpx; color: var(--text-tertiary); }

/* 正文 */
.cd-content {
  background: var(--surface); padding: 24rpx 32rpx; margin-top: 2rpx;
  font-size: 28rpx; color: var(--text-primary); line-height: 1.8;
}

/* Tab区 */
.cd-section { margin-top: 20rpx; background: var(--surface); padding: 0 32rpx 24rpx; }
.cd-section__tabs { display: flex; gap: 32rpx; padding: 20rpx 0; border-bottom: 1px solid var(--border-light); }
.cd-section__tab { font-size: 26rpx; font-weight: 600; color: var(--text-tertiary); padding-bottom: 8rpx; cursor: pointer; }
.cd-section__tab--active { color: var(--bhp-primary-500); border-bottom: 3rpx solid var(--bhp-primary-500); }

/* 评论 */
.cd-comments { padding-top: 16rpx; }
.cd-comment { display: flex; gap: 16rpx; padding: 16rpx 0; border-bottom: 1px solid var(--border-light); }
.cd-comment:last-child { border-bottom: none; }
.cd-comment__avatar { width: 64rpx; height: 64rpx; border-radius: 50%; flex-shrink: 0; background: var(--bhp-gray-100); }
.cd-comment__body { flex: 1; }
.cd-comment__top { display: flex; justify-content: space-between; align-items: center; }
.cd-comment__name { font-size: 24rpx; font-weight: 600; color: var(--text-primary); }
.cd-comment__time { font-size: 20rpx; color: var(--text-tertiary); }
.cd-comment__text { font-size: 26rpx; color: var(--text-primary); line-height: 1.5; display: block; margin-top: 6rpx; }

/* 相关推荐 */
.cd-related { padding-top: 16rpx; }
.cd-related__item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16rpx 0; border-bottom: 1px solid var(--border-light); cursor: pointer;
}
.cd-related__item:last-child { border-bottom: none; }
.cd-related__title { font-size: 26rpx; color: var(--text-primary); flex: 1; }
.cd-related__type { font-size: 20rpx; color: var(--text-tertiary); flex-shrink: 0; margin-left: 12rpx; }

.cd-empty-inline { text-align: center; padding: 40rpx; font-size: 24rpx; color: var(--text-tertiary); }

/* 底部互动栏 */
.cd-bar {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; align-items: center; gap: 16rpx;
  padding: 12rpx 32rpx; background: var(--surface); border-top: 1px solid var(--border-light);
}
.cd-bar__input {
  flex: 1; height: 64rpx; border-radius: var(--radius-full);
  background: var(--surface-secondary); display: flex; align-items: center;
  padding: 0 24rpx; cursor: pointer;
}
.cd-bar__input-text { font-size: 24rpx; color: var(--text-tertiary); }
.cd-bar__actions { display: flex; gap: 20rpx; }
.cd-bar__action { display: flex; align-items: center; gap: 4rpx; cursor: pointer; font-size: 28rpx; }
.cd-bar__action:active { opacity: 0.7; }
.cd-bar__count { font-size: 20rpx; color: var(--text-secondary); }

/* 评论弹窗 */
.cd-modal {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999;
  display: flex; align-items: flex-end; justify-content: center;
}
.cd-modal__box {
  width: 100%; background: var(--surface); border-radius: 24rpx 24rpx 0 0;
  padding: 24rpx 32rpx 40rpx; display: flex; flex-direction: column; gap: 16rpx;
}
.cd-modal__input {
  width: 100%; height: 200rpx; font-size: 28rpx; color: var(--text-primary);
  padding: 16rpx; background: var(--surface-secondary); border-radius: var(--radius-md); border: none;
}
.cd-modal__submit {
  align-self: flex-end; padding: 12rpx 40rpx; border-radius: var(--radius-full);
  background: var(--bhp-primary-500); color: #fff; font-size: 26rpx; font-weight: 700; cursor: pointer;
}
.cd-modal__submit:active { opacity: 0.85; }
</style>
