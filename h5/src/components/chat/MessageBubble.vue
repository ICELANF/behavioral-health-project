<template>
  <div class="message-bubble" :class="{ 'is-user': isUser }">
    <div v-if="!isUser && expert" class="expert-info">
      <van-icon name="manager" class="expert-icon" />
      <span class="expert-name">{{ expert }}</span>
    </div>
    <div class="bubble-content">
      <div class="bubble-text">{{ content }}</div>
      <div class="bubble-time">{{ formatTime(timestamp) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  content: string
  isUser: boolean
  expert?: string
  timestamp: number
}

defineProps<Props>()

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
