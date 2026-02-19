<!--
  内容详情页 — 展示文章/课程内容 + 互动(点赞/收藏/评论/分享)
  路由: /content/:type/:id
-->
<template>
  <div class="page-container">
    <van-nav-bar
      title="内容详情"
      left-arrow
      @click-left="router.back()"
    />

    <div class="page-content content-detail-page">
      <van-loading v-if="loading" class="detail-loading" size="24px" vertical>
        加载中...
      </van-loading>

      <template v-else-if="content">
        <!-- 封面图 -->
        <div v-if="content.cover_url" class="cover-section">
          <img :src="content.cover_url" :alt="content.title" class="cover-image" />
        </div>

        <!-- 标题与元信息 -->
        <div class="content-header card">
          <h1 class="content-title">{{ content.title }}</h1>
          <div class="content-meta">
            <div class="author-info">
              <van-icon name="user-circle-o" size="20" color="#1989fa" />
              <span class="author-name">{{ content.author || '平台编辑' }}</span>
            </div>
            <span class="publish-time">{{ formatTime(content.created_at) }}</span>
          </div>
          <div v-if="content.tags?.length" class="content-tags">
            <van-tag
              v-for="tag in content.tags"
              :key="tag"
              plain
              round
              size="medium"
              color="#1989fa"
            >
              {{ tag }}
            </van-tag>
          </div>
        </div>

        <!-- 正文 -->
        <div class="content-body card" v-html="content.body"></div>

        <!-- 评论区 -->
        <div class="comments-section card">
          <h3 class="section-title">
            评论 <span class="comment-total">({{ comments.length }})</span>
          </h3>

          <van-empty v-if="comments.length === 0" description="暂无评论，来说两句吧" image="search" />

          <div v-else class="comment-list">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <div class="comment-avatar">
                <van-icon name="user-circle-o" size="32" color="#c8c9cc" />
              </div>
              <div class="comment-content">
                <div class="comment-user">{{ comment.username || '匿名用户' }}</div>
                <div class="comment-text">{{ comment.content }}</div>
                <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 评论输入框 -->
        <div class="comment-input-area">
          <van-field
            v-model="commentText"
            placeholder="说点什么..."
            type="textarea"
            rows="1"
            autosize
            class="comment-field"
          />
          <van-button
            type="primary"
            size="small"
            :disabled="!commentText.trim()"
            :loading="submittingComment"
            @click="submitComment"
          >
            发送
          </van-button>
        </div>

        <!-- 底部占位(为 InteractionBar 留空间) -->
        <div style="height: 60px"></div>
      </template>

      <van-empty v-else description="内容不存在或已下架" />
    </div>

    <!-- 交互栏 -->
    <InteractionBar
      v-if="content"
      :content-id="content.id"
      :liked="liked"
      :collected="collected"
      :like-count="likeCount"
      :collect-count="collectCount"
      :comment-count="comments.length"
      @like="toggleLike"
      @collect="toggleCollect"
      @comment="focusComment"
      @share="showShare = true"
    />

    <!-- 分享面板 -->
    <ShareSheet
      v-model:visible="showShare"
      title="分享内容"
      :url="shareUrl"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'
import InteractionBar from '@/components/InteractionBar.vue'
import ShareSheet from '@/components/ShareSheet.vue'

const route = useRoute()
const router = useRouter()

// 路由参数
const contentType = computed(() => route.params.type as string)
const contentId = computed(() => route.params.id as string)

// 状态
const loading = ref(true)
const content = ref<any>(null)
const liked = ref(false)
const collected = ref(false)
const likeCount = ref(0)
const collectCount = ref(0)
const comments = ref<any[]>([])
const commentText = ref('')
const submittingComment = ref(false)
const showShare = ref(false)

const shareUrl = computed(() => {
  return `${window.location.origin}/content/${contentType.value}/${contentId.value}`
})

// 加载内容详情
async function loadContent() {
  loading.value = true
  try {
    const res: any = await api.get(`/api/v1/content/detail/${contentType.value}/${contentId.value}`)
    content.value = res
    liked.value = res.liked || false
    collected.value = res.collected || false
    likeCount.value = res.like_count || 0
    collectCount.value = res.collect_count || 0
    comments.value = res.comments || []
  } catch (err) {
    console.error('加载内容失败:', err)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

// 点赞
async function toggleLike() {
  try {
    await api.post(`/api/v1/content/${contentId.value}/like`)
    liked.value = !liked.value
    likeCount.value += liked.value ? 1 : -1
  } catch {
    showToast('操作失败')
  }
}

// 收藏
async function toggleCollect() {
  try {
    await api.post(`/api/v1/content/${contentId.value}/collect`)
    collected.value = !collected.value
    collectCount.value += collected.value ? 1 : -1
  } catch {
    showToast('操作失败')
  }
}

// 聚焦评论框
function focusComment() {
  const field = document.querySelector('.comment-field textarea') as HTMLTextAreaElement
  if (field) field.focus()
}

// 提交评论
async function submitComment() {
  const text = commentText.value.trim()
  if (!text) return
  submittingComment.value = true
  try {
    const res: any = await api.post(
      `/api/v1/content/${contentId.value}/comment`,
      { content: text }
    )
    comments.value.unshift(res.comment || {
      id: Date.now(),
      content: text,
      username: '我',
      created_at: new Date().toISOString()
    })
    commentText.value = ''
    showToast({ message: '评论成功', type: 'success' })
  } catch {
    showToast('评论失败')
  } finally {
    submittingComment.value = false
  }
}

// 格式化时间
function formatTime(time: string): string {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  loadContent()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.detail-loading {
  padding: 80px 0;
}

.cover-section {
  margin: -$spacing-md;
  margin-bottom: $spacing-md;
}

.cover-image {
  width: 100%;
  max-height: 240px;
  object-fit: cover;
  display: block;
}

.content-header {
  .content-title {
    font-size: 20px;
    font-weight: 700;
    line-height: 1.4;
    color: $text-color;
    margin-bottom: $spacing-sm;
  }

  .content-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-xs;
  }

  .author-info {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .author-name {
    font-size: $font-size-sm;
    color: $text-color;
    font-weight: 500;
  }

  .publish-time {
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }

  .content-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: $spacing-xs;
  }
}

.content-body {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  word-break: break-word;

  :deep(img) {
    max-width: 100%;
    border-radius: 8px;
    margin: 12px 0;
  }

  :deep(p) {
    margin-bottom: 12px;
  }

  :deep(h2),
  :deep(h3) {
    margin: 20px 0 12px;
    font-weight: 600;
  }
}

.comments-section {
  .section-title {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }

  .comment-total {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    font-weight: 400;
  }
}

.comment-list {
  .comment-item {
    display: flex;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid $border-color;

    &:last-child {
      border-bottom: none;
    }
  }

  .comment-avatar {
    flex-shrink: 0;
  }

  .comment-content {
    flex: 1;
    min-width: 0;
  }

  .comment-user {
    font-size: $font-size-md;
    font-weight: 500;
    color: $text-color;
    margin-bottom: 4px;
  }

  .comment-text {
    font-size: $font-size-md;
    color: #333;
    line-height: 1.5;
    margin-bottom: 4px;
  }

  .comment-time {
    font-size: $font-size-xs;
    color: $text-color-placeholder;
  }
}

.comment-input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: $spacing-sm $spacing-md;
  background: #fff;
  border-top: 1px solid $border-color;
  margin: 0 (-$spacing-md);

  .comment-field {
    flex: 1;
    background: #f7f8fa;
    border-radius: 8px;
    padding: 0;

    :deep(.van-field__control) {
      min-height: 32px;
    }
  }
}
</style>
