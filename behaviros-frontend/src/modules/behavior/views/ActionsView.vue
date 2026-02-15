<!--
  ActionsView.vue — 今日行动
  微行动列表 + 一键完成 + 积分反馈
  集成第一批UI的BehaviorTaskCard设计语言
-->

<template>
  <div class="actions-view">
    <div class="page-header">
      <h2 class="page-title">今日行动</h2>
      <p class="page-desc">完成微行动获得成长积分</p>
    </div>

    <div v-if="loading" style="text-align: center; padding: 60px;">
      <a-spin size="large" />
    </div>

    <div v-else-if="actions.length" class="actions-list">
      <div
        v-for="action in actions"
        :key="action.id"
        class="action-card"
        :class="{ done: action.status === 'done', attempted: action.status === 'attempted' }"
      >
        <div class="action-header">
          <div class="action-icon">
            {{ action.status === 'done' ? '✅' : action.status === 'attempted' ? '⏸️' : '⚡' }}
          </div>
          <div class="action-detail">
            <div class="action-title">{{ action.title }}</div>
            <div class="action-desc" v-if="action.description">{{ action.description }}</div>
          </div>
        </div>

        <div v-if="action.status === 'pending'" class="action-buttons">
          <a-button
            type="primary"
            @click="completeAction(action, 'done')"
            :loading="action._loading"
            class="btn-done"
          >
            ✓ 我已完成
          </a-button>
          <a-button
            @click="completeAction(action, 'attempted')"
            :loading="action._loading"
            class="btn-attempted"
          >
            ⏸️ 尝试了但没完成
          </a-button>
        </div>

        <div v-else class="action-result">
          <a-tag :color="action.status === 'done' ? 'success' : 'warning'">
            {{ action.status === 'done' ? '已完成 +3积分' : '已记录' }}
          </a-tag>
        </div>
      </div>
    </div>

    <a-empty v-else description="今天没有安排微行动" style="padding: 60px 0;">
      <p style="color: #999; font-size: 13px;">微行动会根据您的旅程阶段自动生成</p>
    </a-empty>

    <div class="motivation-footer">
      <span>💡</span> 诚实记录比完美表现更重要
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { microActionApi } from '@/api'
import { message } from 'ant-design-vue'
import type { MicroAction } from '@/types'

const actions = ref<(MicroAction & { _loading?: boolean })[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    actions.value = await microActionApi.getToday()
  } catch { /* empty state */ }
  loading.value = false
})

async function completeAction(action: MicroAction & { _loading?: boolean }, state: string) {
  action._loading = true
  try {
    await microActionApi.complete(action.id, state)
    action.status = state as any
    if (state === 'done') {
      message.success('太棒了！获得 +3 成长积分')
    } else {
      message.info('已记录，继续加油')
    }
  } catch {
    message.error('操作失败，请重试')
  }
  action._loading = false
}
</script>

<style scoped>
.actions-view { max-width: 640px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #999; margin: 0; }

.actions-list { display: flex; flex-direction: column; gap: 12px; }

.action-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}
.action-card.done { background: #f0fdf4; border-color: #bbf7d0; }
.action-card.attempted { background: #fffbeb; border-color: #fde68a; }

.action-header { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 16px; }
.action-icon { font-size: 24px; flex-shrink: 0; margin-top: 2px; }
.action-title { font-size: 16px; font-weight: 600; color: #1a1a1a; }
.action-desc { font-size: 13px; color: #999; margin-top: 2px; }

.action-buttons { display: flex; flex-direction: column; gap: 8px; }
.btn-done {
  border-radius: 12px; height: 44px; font-weight: 600;
  background: linear-gradient(135deg, #4aa883, #2d8e69); border: none;
}
.btn-attempted {
  border-radius: 12px; height: 44px; font-weight: 500;
  border-color: #d1d5db; color: #666;
}
.action-result { text-align: right; }

.motivation-footer {
  text-align: center;
  margin-top: 32px;
  padding: 12px;
  background: #fafafa;
  border-radius: 12px;
  font-size: 13px;
  color: #999;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
