<script setup lang="ts">
/**
 * Trigger列表组件
 * 用于显示识别的风险信号
 */
import type { Trigger } from '@/types'

interface Props {
  triggers: Trigger[]
}

defineProps<Props>()

/**
 * 获取严重程度标签类型
 */
const getSeverityType = (severity: string) => {
  const typeMap: Record<string, any> = {
    critical: 'danger',
    high: 'warning',
    moderate: 'primary',
    low: 'default'
  }
  return typeMap[severity] || 'default'
}
</script>

<template>
  <div class="trigger-list">
    <template v-if="triggers.length > 0">
      <van-cell-group inset>
        <van-cell v-for="(trigger, index) in triggers" :key="index" :title="trigger.name">
          <template #label>
            <div class="trigger-info">
              <van-tag :type="getSeverityType(trigger.severity)" size="medium">
                {{ trigger.severity }}
              </van-tag>
              <span class="category">{{ trigger.category }}</span>
              <span class="confidence">
                置信度: {{ (trigger.confidence * 100).toFixed(0) }}%
              </span>
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </template>

    <template v-else>
      <div class="empty-state">
        <div class="empty-state-icon">✓</div>
        <div class="empty-state-text">未识别到风险信号</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.trigger-list {
  width: 100%;
}

.trigger-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.category,
.confidence {
  font-size: 12px;
  color: #969799;
}
</style>
