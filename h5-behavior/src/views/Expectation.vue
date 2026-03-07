<template>
  <div class="screen" v-if="label">
    <div class="land-bg" style="opacity:.3" />
    <div class="pg" style="padding-top:40px">
      <div class="exp-title fu">如果这些改变发生了，<br />三个月后你最希望有什么不同？</div>
      <div class="exp-sub fu d1">选择2-3个你最在意的（你的北极星目标）</div>
      <div class="exp-grid fu d2">
        <div v-for="e in EXPECTATIONS" :key="e.text"
          :class="['exp-item', { sel: store.expectations.includes(e.text) }]"
          @click="store.toggleExpectation(e.text)">
          <span class="exp-ico">{{ e.ico }}</span>
          <span class="exp-text">{{ e.text }}</span>
        </div>
      </div>
      <button class="btn-main fu d3" :disabled="store.expectations.length === 0"
        :style="{ background: store.expectations.length > 0 ? label.color : 'rgba(0,0,0,.06)',
                   color: store.expectations.length > 0 ? '#fff' : D.muted, marginTop: '8px',
                   boxShadow: store.expectations.length > 0 ? `0 4px 14px ${label.color}40` : 'none' }"
        @click="$router.push('/prescription')">
        生成你的7天行为处方 →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { EXPECTATIONS } from '@/data/expectations'
import { D } from '@/design/tokens'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)
</script>

<style scoped>
.exp-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 24px; color: var(--ink); line-height: 1.4; margin-bottom: 6px; }
.exp-sub { font-size: 13px; color: var(--sub); line-height: 1.6; margin-bottom: 20px; }
.exp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.exp-item {
  border-radius: 16px; padding: 16px 12px; cursor: pointer;
  border: 1.5px solid var(--border); background: var(--card);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center; transition: all .25s;
}
.exp-item.sel {
  border-color: var(--gold); background: rgba(212,160,23,.06);
  box-shadow: 0 0 0 3px rgba(212,160,23,.1);
}
.exp-item:active { transform: scale(.97); }
.exp-ico { font-size: 26px; }
.exp-text { font-size: 12px; color: var(--sub); line-height: 1.4; }
.exp-item.sel .exp-text { color: var(--ink); font-weight: 600; }
</style>
