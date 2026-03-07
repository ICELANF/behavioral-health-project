<template>
  <div class="screen">
    <div class="prog-hdr">
      <div class="prog-back" @click="goBack">←</div>
      <div class="prog-bar-wrap">
        <div class="prog-bar">
          <div class="prog-fill" :style="{ width: progress + '%', background: `linear-gradient(90deg, ${q.color}, ${q.color}cc)` }" />
        </div>
        <div class="prog-step">{{ qIdx + 1 }} / {{ total }}</div>
      </div>
    </div>
    <div class="q-wrap fi">
      <div class="q-dim-badge" :style="{ background: `rgba(${q.rgb},.1)`, color: q.color }">
        {{ q.icon }} {{ q.dim }}
      </div>
      <div class="q-text">{{ q.q }}</div>
      <div class="q-sub">{{ q.sub }}</div>
      <div class="q-multi-hint">可多选 — 选择所有符合的选项</div>
      <div class="q-opts">
        <div v-for="(o, i) in q.opts" :key="i"
          :class="['q-opt', { sel: selected.includes(i) }]"
          :style="selected.includes(i) ? { borderColor: q.color, boxShadow: `0 0 0 3px ${q.color}18` } : {}"
          @click="store.toggleAnswer(qIdx, i)">
          <div class="q-check" :style="selected.includes(i) ? { background: q.color, borderColor: q.color } : {}">
            <span v-if="selected.includes(i)" style="color:#fff;font-size:10px">✓</span>
          </div>
          <div class="q-opt-text" :style="selected.includes(i) ? { color: 'var(--ink)', fontWeight: '600' } : {}">{{ o }}</div>
        </div>
      </div>
    </div>
    <div class="q-nav">
      <button v-if="qIdx > 0" class="btn-ghost" @click="qIdx--">← 上一题</button>
      <button class="btn-main" :disabled="selected.length === 0"
        :style="{ background: selected.length > 0 ? q.color : 'rgba(0,0,0,.06)',
                   color: selected.length > 0 ? '#fff' : D.muted,
                   boxShadow: selected.length > 0 ? `0 4px 14px ${q.color}40` : 'none' }"
        @click="next">
        {{ qIdx < total - 1 ? '下一题 →' : '✨ 生成分析报告' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import { QUESTIONS } from '@/data/questions'
import { D } from '@/design/tokens'

const router = useRouter()
const store = useAssessmentStore()
const qIdx = ref(0)
const total = QUESTIONS.length
const q = computed(() => QUESTIONS[qIdx.value])
const progress = computed(() => (qIdx.value / total) * 100)
const selected = computed(() => store.answers[qIdx.value] || [])

function goBack() {
  if (qIdx.value > 0) qIdx.value--
  else router.push('/belief')
}

function next() {
  if (qIdx.value < total - 1) qIdx.value++
  else router.push('/analyzing')
}
</script>

<style scoped>
.prog-hdr { padding: 16px 22px; display: flex; align-items: center; gap: 12px; }
.prog-back { font-size: 18px; color: var(--sub); cursor: pointer; padding: 4px; }
.prog-bar-wrap { flex: 1; }
.prog-bar { height: 6px; background: rgba(0,0,0,.06); border-radius: 3px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 3px; transition: width .5s cubic-bezier(.4,0,.2,1); }
.prog-step { font-size: 11px; color: var(--muted); text-align: right; margin-top: 4px; }
.q-wrap { flex: 1; padding: 8px 22px 24px; display: flex; flex-direction: column; }
.q-dim-badge { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 12px; font-size: 10px; font-weight: 700; letter-spacing: .5px; margin-bottom: 14px; width: fit-content; }
.q-text { font-family: 'Noto Serif SC', serif; font-size: 18px; color: var(--ink); line-height: 1.6; margin-bottom: 6px; }
.q-sub { font-size: 12px; color: var(--sub); margin-bottom: 6px; line-height: 1.5; }
.q-multi-hint { font-size: 11px; color: var(--teal); font-weight: 500; margin-bottom: 16px; }
.q-opts { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.q-opt {
  border-radius: 16px; padding: 15px 16px; cursor: pointer;
  border: 1.5px solid var(--border); background: var(--card);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03);
  display: flex; align-items: center; gap: 12px; transition: all .25s;
}
.q-opt:active { transform: scale(.98); }
.q-check {
  width: 22px; height: 22px; border-radius: 6px; border: 1.5px solid var(--border-m);
  flex-shrink: 0; transition: all .25s;
  display: flex; align-items: center; justify-content: center;
}
.q-opt-text { font-size: 13px; color: var(--sub); flex: 1; line-height: 1.4; transition: all .15s; }
.q-nav { padding: 0 22px 24px; display: flex; gap: 10px; }
.q-nav .btn-main { flex: 1; }
.q-nav .btn-ghost { flex: 0 0 auto; }
</style>
