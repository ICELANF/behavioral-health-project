<template>
  <div class="survey-page">
    <div class="content" v-if="!done">
      <div class="card fu">
        <div style="font-size:12px;color:var(--sub);margin-bottom:6px">
          本周视力营养问卷 · 第{{ idx + 1 }}/{{ total }}题
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (idx / total * 100) + '%' }" />
        </div>
        <div style="font-size:36px;text-align:center;margin-bottom:10px">{{ q.emoji }}</div>
        <div class="q-text">{{ q.text }}</div>
        <div class="q-sub">{{ q.sub }}</div>
        <div class="q-opts">
          <div
            v-for="(opt, i) in q.opts" :key="i"
            class="q-opt" :class="{ sel: answers[q.id] === i }"
            @click="answers[q.id] = i"
          >
            <div class="q-dot" />
            {{ opt }}
          </div>
        </div>
        <div class="q-nav">
          <button v-if="idx > 0" class="btn-outline" @click="idx--">← 上一题</button>
          <button
            class="btn-main" style="flex:1"
            :disabled="answers[q.id] === undefined"
            @click="next"
          >
            {{ idx < total - 1 ? '下一题 →' : '✅ 提交本周问卷' }}
          </button>
        </div>
      </div>
    </div>

    <div class="content" v-else>
      <div class="card fu" style="text-align:center;padding-top:24px">
        <div style="font-size:44px">{{ scoreMsg.emoji }}</div>
        <div class="result-score">{{ totalScore }}</div>
        <div style="font-size:13px;color:var(--sub);margin-top:4px">本周视力营养综合评分</div>
        <div style="font-size:15px;font-weight:700;color:var(--ink);margin-top:12px;line-height:1.5">
          {{ scoreMsg.text }}
        </div>
      </div>

      <div class="card fu fu-1">
        <div class="card-title">各营养素达成详情</div>
        <div v-for="[k, n] in nutEntries" :key="k" class="nut-row">
          <span style="font-size:18px;width:24px">{{ n.icon }}</span>
          <div style="flex:1">
            <div style="font-size:12px;font-weight:600;color:var(--ink)">{{ n.name }}</div>
            <div class="nut-bar">
              <div class="nut-fill" :style="{ width: (scores[k] || 0) + '%', background: n.color }" />
            </div>
          </div>
          <div class="nut-pct" :style="{ color: pctColor(scores[k] || 0) }">{{ scores[k] || 0 }}%</div>
        </div>
      </div>

      <button class="btn-main fu fu-2" @click="router.push('/food')">← 返回营养记录</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NUTRITION_QUESTIONS } from '@/data/questions'
import { NUTRIENTS } from '@/data/nutrients'

const router = useRouter()
const questions = NUTRITION_QUESTIONS
const total = questions.length
const idx = ref(0)
const answers = reactive<Record<string, number>>({})
const done = ref(false)
const scores = ref<Record<string, number>>({})

const q = computed(() => questions[idx.value])
const nutEntries = computed(() => Object.entries(NUTRIENTS))

function next() {
  if (idx.value < total - 1) {
    idx.value++
  } else {
    submit()
  }
}

function submit() {
  const nutScores: Record<string, number> = {}
  const maxPossible: Record<string, number> = { lutein: 6, dha: 3, vitA: 3, vitC: 3, vitD: 3, zinc: 3 }
  questions.forEach(q => {
    const s = answers[q.id] !== undefined ? q.scores[answers[q.id]] : 0
    nutScores[q.nutrient] = (nutScores[q.nutrient] || 0) + s
  })
  const pcts: Record<string, number> = {}
  Object.entries(nutScores).forEach(([k, v]) => {
    pcts[k] = Math.round(v / (maxPossible[k] || 3) * 100)
  })
  scores.value = pcts
  done.value = true
}

const totalScore = computed(() => {
  const vals = Object.values(scores.value)
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0
})

const scoreMsg = computed(() => {
  if (totalScore.value >= 80) return { emoji: '🌟', text: '太棒了！这周的视力营养非常充足！' }
  if (totalScore.value >= 55) return { emoji: '👍', text: '做得不错！再多吃些深海鱼和深色蔬菜。' }
  return { emoji: '💪', text: '别担心！一起制定小目标，让视力营养跟上来。' }
})

function pctColor(pct: number) {
  if (pct >= 70) return 'var(--green)'
  if (pct >= 40) return 'var(--amber)'
  return 'var(--red)'
}
</script>

<style scoped>
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.progress-bar { height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
.progress-fill { height: 100%; background: var(--grad-teal); border-radius: 3px; transition: width .4s; }
.q-text { font-size: 15px; font-weight: 700; color: var(--ink); text-align: center; margin-bottom: 4px; line-height: 1.4; }
.q-sub { font-size: 12px; color: var(--sub); text-align: center; margin-bottom: 16px; }
.q-opts { display: flex; flex-direction: column; gap: 8px; }
.q-opt {
  padding: 13px 16px; border: 2px solid var(--border); border-radius: 13px;
  font-size: 13px; color: var(--ink); cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 10px;
}
.q-opt.sel { border-color: var(--teal); background: var(--teal-l); color: var(--teal); font-weight: 600; }
.q-dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--border); flex-shrink: 0; transition: all .2s; }
.q-opt.sel .q-dot { background: var(--teal); border-color: var(--teal); }
.q-nav { display: flex; gap: 8px; margin-top: 14px; }
.result-score { font-size: 56px; font-weight: 900; color: var(--teal); line-height: 1; }
.nut-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px dashed var(--border); }
.nut-row:last-child { border-bottom: none; }
.nut-bar { height: 8px; border-radius: 4px; overflow: hidden; background: var(--border); margin-top: 3px; }
.nut-fill { height: 100%; border-radius: 4px; transition: width .8s .1s; }
.nut-pct { font-size: 11px; font-weight: 700; text-align: right; min-width: 28px; }
</style>
