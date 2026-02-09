<template>
  <div class="bg-white p-6 rounded-2xl shadow-lg border border-slate-100">
    <!-- Loading -->
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-4 bg-slate-200 rounded w-1/3"></div>
      <div class="h-8 bg-slate-200 rounded w-2/3"></div>
      <div class="h-12 bg-slate-200 rounded"></div>
    </div>

    <!-- Tasks -->
    <template v-else-if="tasks.length > 0">
      <div class="flex items-center gap-2 mb-4">
        <div
          class="w-1 h-6 rounded-full"
          :style="{ background: `linear-gradient(to bottom, ${config.gradientFrom}, ${config.gradientTo})` }"
        />
        <h2 class="text-sm font-semibold text-slate-600">{{ config.taskTitle }}</h2>
        <span class="ml-auto text-xs text-slate-400">{{ tasks.length }} 个任务</span>
      </div>

      <div v-for="task in tasks" :key="task.id" class="mb-4 last:mb-0">
        <div class="bg-slate-50 p-4 rounded-xl mb-3">
          <div class="text-xl font-bold text-slate-900">{{ task.action_text || task.title }}</div>
        </div>

        <div v-if="task.status === 'pending'" class="flex gap-3">
          <button
            @click="handleComplete(task.id)"
            class="flex-1 py-3 rounded-xl font-bold text-white transition-transform active:scale-95"
            :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }"
          >
            ✓ 完成
          </button>
          <button
            @click="handleAttempt(task.id)"
            class="flex-1 py-3 rounded-xl font-semibold border-2 transition-transform active:scale-95"
            :style="{ borderColor: config.gradientFrom, color: config.textColor }"
          >
            ~ 尝试了
          </button>
          <button
            @click="handleSkip(task.id)"
            class="px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-100 transition-colors"
          >
            跳过
          </button>
        </div>

        <div v-else class="flex items-center gap-2 py-2">
          <span
            class="text-xs px-3 py-1 rounded-full font-bold"
            :class="{
              'bg-emerald-100 text-emerald-700': task.status === 'done' || task.status === 'completed',
              'bg-amber-100 text-amber-700': task.status === 'attempted',
              'bg-slate-100 text-slate-500': task.status === 'skipped',
            }"
          >
            {{ statusLabels[task.status] || task.status }}
          </span>
        </div>
      </div>
    </template>

    <!-- Empty -->
    <div v-else class="text-center py-8 text-slate-400">
      <span class="text-3xl mb-2 block">🎉</span>
      <p>今天的任务都完成了</p>
    </div>

    <!-- Tip -->
    <div class="mt-4 text-center">
      <span class="text-xs text-slate-400">💡 诚实记录比完美表现更重要</span>
    </div>
  </div>

  <!-- Feedback overlay -->
  <van-overlay :show="showFeedback" @click="showFeedback = false">
    <div class="flex items-center justify-center h-full p-6" @click.stop>
      <div class="bg-white rounded-2xl p-6 max-w-sm w-full">
        <div class="text-center mb-4">
          <div
            class="inline-flex items-center justify-center w-14 h-14 rounded-full mb-3"
            :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }"
          >
            <span class="text-2xl">💚</span>
          </div>
          <h3 class="text-lg font-bold text-slate-900">系统反馈</h3>
        </div>
        <p class="text-slate-700 text-center mb-6">
          收到。尝试本身就是一种成功，今天到此为止，好好休息。
        </p>
        <button
          @click="showFeedback = false"
          class="w-full py-3 rounded-xl font-bold text-white"
          :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }"
        >
          知道了
        </button>
      </div>
    </div>
  </van-overlay>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { showToast } from 'vant'
import { STAGE_CONFIG, type Stage } from '@/types/stage'
import { fetchTodayTasks, completeTask, attemptTask, skipTask, type MicroAction } from '@/api/tasks'

const props = defineProps<{ stage: Stage }>()

const config = computed(() => STAGE_CONFIG[props.stage])
const tasks = ref<MicroAction[]>([])
const loading = ref(true)
const showFeedback = ref(false)

const statusLabels: Record<string, string> = {
  done: '✓ 已完成',
  completed: '✓ 已完成',
  attempted: '⏸️ 尝试了',
  skipped: '跳过',
  expired: '已过期',
  pending: '待完成',
}

onMounted(async () => {
  try {
    const res: any = await fetchTodayTasks()
    tasks.value = res?.tasks || res || []
  } catch {
    showToast('加载任务失败')
  } finally {
    loading.value = false
  }
})

const updateTaskStatus = (taskId: string, status: string) => {
  const task = tasks.value.find((t) => t.id === taskId)
  if (task) task.status = status as MicroAction['status']
}

const handleComplete = async (taskId: string) => {
  try {
    await completeTask(taskId)
    updateTaskStatus(taskId, 'done')
    showToast({ message: '🎉 完成！', type: 'success' })
  } catch {
    showToast('操作失败，请重试')
  }
}

const handleAttempt = async (taskId: string) => {
  try {
    await attemptTask(taskId)
    updateTaskStatus(taskId, 'attempted')
    showFeedback.value = true
  } catch {
    showToast('操作失败，请重试')
  }
}

const handleSkip = async (taskId: string) => {
  try {
    await skipTask(taskId)
    updateTaskStatus(taskId, 'skipped')
  } catch {
    showToast('操作失败，请重试')
  }
}
</script>
