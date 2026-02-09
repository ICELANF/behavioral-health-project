<template>
  <svg viewBox="0 0 400 400" width="100%" class="l-svg">
    <circle v-for="(r, i) in [180,140,100,65]" :key="'ring'+i" class="l-orbit" cx="200" cy="200" :r="r" fill="none" stroke="var(--l-accent)" stroke-width="1" :stroke-opacity="0.08 + i * 0.06" :stroke-dasharray="i % 2 ? '4 8' : 'none'" :style="{ animationDuration: (30 + i * 10) + 's', animationDirection: i % 2 ? 'reverse' : 'normal' }" />
    <g opacity="0.5">
      <path v-for="(d, i) in paths" :key="'p'+i" :d="d" fill="none" stroke="var(--l-accent)" :stroke-width="2.5 - i * 0.3" stroke-linecap="round" :stroke-opacity="0.4 + i * 0.1" class="l-draw-path" />
    </g>
    <g v-for="([x, y], i) in nodes" :key="'n'+i">
      <circle :cx="x" :cy="y" r="8" fill="var(--l-accent)" opacity="0.2" class="l-node-glow" :style="{ animationDelay: (i * 0.4) + 's' }" />
      <circle :cx="x" :cy="y" r="3" fill="var(--l-accent)" opacity="0.8" />
    </g>
    <circle cx="200" cy="200" r="18" fill="var(--l-accent)" opacity="0.12" class="l-core-pulse" />
    <circle cx="200" cy="200" r="5" fill="var(--l-accent)" opacity="0.9" />
  </svg>
</template>

<script setup lang="ts">
defineProps<{ paths: string[]; nodes: [number, number][] }>()
</script>
