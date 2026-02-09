<template>
  <div class="bg-slate-700/40 backdrop-blur-sm p-3 rounded-lg border border-slate-400/60 shadow-lg">
    <p class="text-[10px] text-slate-300 uppercase tracking-wider mb-1">{{ label }}</p>
    <p class="text-xl font-bold text-white flex items-baseline gap-1">
      {{ value }}
      <span v-if="unit" class="text-xs font-normal text-slate-200">{{ unit }}</span>
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string | number; unit?: string }>()
</script>
