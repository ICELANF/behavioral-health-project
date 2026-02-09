<template>
  <div
    class="relative p-6 rounded-2xl mb-4 overflow-hidden"
    :style="{ background: `linear-gradient(135deg, ${config.gradientFrom}, ${config.gradientTo})` }"
  >
    <div class="absolute top-0 right-0 w-48 h-48 opacity-10">
      <div class="absolute inset-0" style="background: radial-gradient(circle, white 0%, transparent 70%)"></div>
    </div>
    <div class="relative z-10">
      <div class="flex items-center gap-3 mb-3">
        <span class="text-4xl">{{ config.icon }}</span>
        <div>
          <div class="text-xs uppercase tracking-widest text-white/80 font-semibold mb-0.5">当前生命状态</div>
          <h1 class="text-3xl font-bold text-white">{{ config.label }}</h1>
        </div>
      </div>
      <p class="text-base text-white/95 font-medium">{{ config.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { STAGE_CONFIG, TTM_TO_STAGE, type Stage } from '@/types/stage'
import { fetchCurrentStage } from '@/api/tasks'

const props = defineProps<{ stage?: Stage }>()

const dynamicStage = ref<Stage>('ACTION')

onMounted(async () => {
  if (!props.stage) {
    try {
      const res: any = await fetchCurrentStage()
      dynamicStage.value = TTM_TO_STAGE[res.ttm_stage] || 'AWARENESS'
    } catch {
      // fallback to default
    }
  }
})

const currentStage = computed(() => props.stage || dynamicStage.value)
const config = computed(() => STAGE_CONFIG[currentStage.value])
</script>
