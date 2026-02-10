<template>
  <div class="message-bubble" :class="{ 'is-user': isUser }">
    <div v-if="!isUser && expert" class="expert-info">
      <van-icon name="manager" class="expert-icon" />
      <span class="expert-name">{{ expert }}</span>
    </div>
    <div class="bubble-content">
      <!-- 图片消息 (skip broken blob: URLs) -->
      <van-image
        v-if="validImageUrl"
        :src="validImageUrl"
        width="200"
        height="150"
        fit="cover"
        radius="8"
        class="bubble-image"
        @click="previewImage"
      />

      <!-- 用户消息: 纯文本 -->
      <div v-if="isUser && content" class="bubble-text">{{ content }}</div>

      <!-- AI消息: 支持引用标记 -->
      <template v-else>
        <CitationMarker
          v-if="hasKnowledge || hasModelSupplement"
          :text="content"
          :citations="citations"
          :has-model-supplement="hasModelSupplement"
          @cite-click="(idx) => $emit('cite-click', idx)"
        />
        <div v-else class="bubble-text">{{ content }}</div>

        <!-- 引用折叠块 -->
        <CitationBlock
          v-if="citations.length > 0 || hasModelSupplement"
          :citations="citations"
          :has-model-supplement="hasModelSupplement"
          :model-supplement-sections="modelSupplementSections"
          :source-stats="sourceStats"
        />
      </template>

      <div class="bubble-time">{{ formatTime(timestamp) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { showImagePreview } from 'vant'
import CitationMarker from './CitationMarker.vue'
import CitationBlock from './CitationBlock.vue'

interface Props {
  content: string
  isUser: boolean
  expert?: string
  timestamp: number
  imageUrl?: string
  // RAG 引用数据
  citations?: any[]
  hasKnowledge?: boolean
  hasModelSupplement?: boolean
  modelSupplementSections?: string[]
  sourceStats?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  imageUrl: '',
  citations: () => [],
  hasKnowledge: false,
  hasModelSupplement: false,
  modelSupplementSections: () => [],
  sourceStats: () => ({}),
})

defineEmits(['cite-click'])

// Filter out stale blob: URLs (they don't survive page reload)
const validImageUrl = computed(() => {
  const url = props.imageUrl
  if (!url) return ''
  if (url.startsWith('blob:')) return ''  // blob URLs break after reload
  return url
})

function previewImage() {
  if (validImageUrl.value) {
    showImagePreview([validImageUrl.value])
  }
}

function formatTime(ts: number): string {
  const date = new Date(ts)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.message-bubble {
  display: flex;
  flex-direction: column;
  margin-bottom: $spacing-md;
  align-items: flex-start;

  &.is-user {
    align-items: flex-end;

    .bubble-content {
      background-color: $primary-color;
      color: #fff;
      border-radius: $border-radius-lg $border-radius-lg 4px $border-radius-lg;
    }

    .bubble-time {
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.expert-info {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
  color: $text-color-secondary;
  font-size: $font-size-sm;

  .expert-icon {
    margin-right: 4px;
    color: $expert-mental;
  }

  .expert-name {
    font-weight: 500;
  }
}

.bubble-content {
  max-width: 80%;
  padding: $spacing-sm $spacing-md;
  background-color: $background-color-light;
  border-radius: $border-radius-lg $border-radius-lg $border-radius-lg 4px;
  box-shadow: $shadow-sm;
}

.bubble-image {
  margin-bottom: 4px;
  cursor: pointer;
}

.bubble-text {
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.bubble-time {
  font-size: $font-size-xs;
  color: $text-color-secondary;
  margin-top: 4px;
  text-align: right;
}
</style>
