<!--
  交互栏组件 — 固定底部的点赞/收藏/评论/分享按钮
-->
<template>
  <div class="interaction-bar safe-area-bottom">
    <div class="bar-item" @click="$emit('like')">
      <van-icon
        :name="liked ? 'like' : 'like-o'"
        :color="liked ? '#ee0a24' : '#969799'"
        size="22"
      />
      <span class="bar-count">{{ likeCount || '' }}</span>
    </div>
    <div class="bar-item" @click="$emit('collect')">
      <van-icon
        :name="collected ? 'star' : 'star-o'"
        :color="collected ? '#ff976a' : '#969799'"
        size="22"
      />
      <span class="bar-count">{{ collectCount || '' }}</span>
    </div>
    <div class="bar-item" @click="$emit('comment')">
      <van-icon name="comment-o" color="#969799" size="22" />
      <span class="bar-count">{{ commentCount || '' }}</span>
    </div>
    <div class="bar-item" @click="$emit('share')">
      <van-icon name="share-o" color="#969799" size="22" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  contentId: string | number
  liked: boolean
  collected: boolean
  likeCount: number
  collectCount: number
  commentCount: number
}>()

defineEmits<{
  (e: 'like'): void
  (e: 'collect'): void
  (e: 'comment'): void
  (e: 'share'): void
}>()
</script>

<style scoped>
.interaction-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: #fff;
  border-top: 1px solid #ebedf0;
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  padding: 0 16px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex: 1;
  gap: 2px;
}

.bar-item:active {
  opacity: 0.7;
}

.bar-count {
  font-size: 10px;
  color: #969799;
  line-height: 1;
  min-height: 12px;
}
</style>
