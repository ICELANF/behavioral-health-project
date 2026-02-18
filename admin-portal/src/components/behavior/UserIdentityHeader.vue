<template>
  <div
    class="relative p-8 rounded-3xl mb-6 overflow-hidden shadow-2xl"
    :style="{
      background: `linear-gradient(135deg, ${config.gradientFrom} 0%, ${config.gradientTo} 100%)`,
    }"
  >
    <div class="absolute top-0 right-0 w-64 h-64 opacity-10">
      <div class="absolute inset-0" :style="{
        background: 'radial-gradient(circle, white 0%, transparent 70%)'
      }"></div>
    </div>

    <div class="relative z-10">
      <div class="flex items-center gap-3 mb-4">
        <span class="text-5xl">{{ config.icon }}</span>
        <div>
          <div class="text-xs uppercase tracking-widest text-white/80 font-semibold mb-1">
            当前生命状态
          </div>
          <h1 class="text-4xl font-bold text-white drop-shadow-lg">
            {{ config.label }}
          </h1>
        </div>
      </div>
      <p class="text-lg text-white/95 font-medium leading-relaxed">
        {{ config.description }}
      </p>
    </div>

    <div class="absolute bottom-0 left-0 right-0 h-1 bg-white/30"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { STAGE_CONFIG, type Stage } from '../core/types';

const props = defineProps<{
  stage: Stage;
}>();

const config = computed(() => STAGE_CONFIG[props.stage]);
</script>
