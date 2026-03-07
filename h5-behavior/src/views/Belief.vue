<template>
  <div class="screen">
    <div class="land-bg" style="opacity:.4">
      <div class="orb" :style="{ background: accent, width: '220px', height: '220px', top: '-60px', left: '-60px', opacity: '.12', position:'absolute', borderRadius:'50%', filter:'blur(60px)' }" />
    </div>
    <div class="pg" style="padding-top:48px;justify-content:center">
      <div style="text-align:center;margin-bottom:8px" class="fu"><span style="font-size:36px">🤔</span></div>
      <div class="belief-q fu d1">
        在你看来，<em>"{{ sceneText }}"</em><br />主要是因为什么？
      </div>
      <div class="belief-sub fu d1">可多选，选择所有你认同的原因</div>
      <div class="belief-opts fu d2">
        <div v-for="(o, i) in BELIEF_OPTS" :key="i"
          :class="['belief-opt', { sel: store.beliefs.includes(i) }]"
          @click="store.toggleBelief(i)">
          <div class="belief-check" :class="{ checked: store.beliefs.includes(i) }">
            {{ store.beliefs.includes(i) ? '✓' : '' }}
          </div>
          <span class="belief-opt-ico">{{ o.ico }}</span>
          {{ o.text }}
        </div>
      </div>
      <button class="btn-main fu d3" :disabled="store.beliefs.length === 0"
        :style="{ background: store.beliefs.length > 0 ? accent : 'rgba(0,0,0,.06)',
                   color: store.beliefs.length > 0 ? '#fff' : D.muted, marginTop: '8px',
                   boxShadow: store.beliefs.length > 0 ? `0 4px 14px ${accent}40` : 'none' }"
        @click="startQuestions">
        {{ store.beliefs.length > 0 ? `已选 ${store.beliefs.length} 项，继续 →` : '请选择至少一项' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import { DOORS } from '@/data/doors'
import { BELIEF_OPTS } from '@/data/questions'
import { D } from '@/design/tokens'

const router = useRouter()
const store = useAssessmentStore()
const doorData = computed(() => DOORS.find(d => d.key === store.door) || DOORS[0])
const accent = computed(() => doorData.value.color)
const sceneText = computed(() => {
  if (store.scenes.length === 0) return ''
  const first = doorData.value.scenes[store.scenes[0]]
  if (store.scenes.length === 1) return first ? first.text.slice(0, 8) + '…' : ''
  return first ? first.text.slice(0, 6) + '等' + store.scenes.length + '项' : ''
})

function startQuestions() {
  router.push('/question')
}
</script>

<style scoped>
.belief-q { font-family: 'Noto Serif SC', serif; font-size: 18px; color: var(--ink); line-height: 1.6; margin-bottom: 6px; text-align: center; }
.belief-q em { font-style: normal; color: var(--amber-d); font-weight: 700; }
.belief-sub { font-size: 13px; color: var(--sub); text-align: center; margin-bottom: 24px; line-height: 1.5; }
.belief-opts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.belief-opt {
  border-radius: 16px; padding: 16px 12px; cursor: pointer;
  border: 1.5px solid var(--border); background: var(--card);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  text-align: center; transition: all .25s; font-size: 13px; color: var(--sub); line-height: 1.4;
  position: relative;
}
.belief-opt.sel {
  border-color: var(--amber); background: rgba(245,166,35,.08); color: var(--ink); font-weight: 600;
  box-shadow: 0 0 0 3px rgba(245,166,35,.12);
}
.belief-opt:active { transform: scale(.97); }
.belief-opt-ico { font-size: 22px; margin-bottom: 6px; display: block; }
.belief-check {
  position: absolute; top: 8px; right: 8px; width: 18px; height: 18px; border-radius: 5px;
  border: 1.5px solid var(--border-m); display: flex; align-items: center; justify-content: center;
  font-size: 10px; color: #fff; transition: all .2s;
}
.belief-check.checked { background: var(--amber); border-color: var(--amber); }
</style>
