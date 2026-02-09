<template>
  <div class="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50">
    <van-nav-bar title="健康成长伙伴" left-arrow @click-left="$router.back()" />

    <div class="px-4 py-6">
      <!-- Latest insight -->
      <div v-if="latestMessage" class="bg-white rounded-2xl shadow-lg p-6 border border-green-100 mb-4">
        <div class="flex items-start gap-3 mb-4">
          <div class="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center shrink-0">
            <van-icon name="rising" color="white" size="20" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-green-900 mb-1">今日健康洞察</h2>
            <p class="text-xs text-green-600">{{ formatDate(latestMessage.created_at) }}</p>
          </div>
        </div>
        <p class="text-base leading-relaxed text-green-800 italic">
          {{ latestMessage.content }}
        </p>
        <div class="mt-4 pt-4 border-t border-green-100 flex items-center justify-between text-xs">
          <span class="flex items-center gap-1 text-green-600">
            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
            由专业团队审核
          </span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="bg-white rounded-2xl shadow-lg p-10 text-center border border-green-100">
        <div class="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
          <van-icon name="like" color="#22c55e" size="28" />
        </div>
        <h2 class="text-lg font-bold text-green-900 mb-2">暂无新消息</h2>
        <p class="text-green-600 text-sm">当有新的健康洞察时，我们会第一时间通知您</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchPublishedNarrative } from '@/api/tasks'

interface NarrativeMessage {
  id: string
  content: string
  created_at: string
}

const latestMessage = ref<NarrativeMessage | null>(null)

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })

onMounted(async () => {
  try {
    const res: any = await fetchPublishedNarrative()
    const messages = res?.messages || res || []
    if (messages.length > 0) {
      latestMessage.value = messages[0]
    }
  } catch { /* silent fallback */ }
})
</script>
