<template>
  <div class="survey-page">
    <div class="header-mini">
      <span>📋</span> 本周行为问卷
    </div>

    <div class="content" v-if="!done">
      <div class="card fu">
        <div style="font-size:12px;color:var(--sub);margin-bottom:6px">
          第{{ step + 1 }}/{{ questions.length }}题
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (step / questions.length * 100) + '%' }" />
        </div>
        <div class="q-text">{{ questions[step].q }}</div>
        <div class="q-opts">
          <div
            v-for="(opt, i) in questions[step].opts" :key="i"
            class="q-opt" :class="{ sel: answers[step] === i }"
            @click="answers[step] = i"
          >
            <div class="q-dot" />
            {{ opt }}
          </div>
        </div>
        <div class="q-nav">
          <button v-if="step > 0" class="btn-outline" @click="step--">← 上一题</button>
          <button
            class="btn-main" style="flex:1"
            :disabled="answers[step] === undefined"
            @click="next"
          >
            {{ step < questions.length - 1 ? '下一题 →' : '提交问卷' }}
          </button>
        </div>
      </div>
    </div>

    <div class="content" v-else>
      <div class="card fu" style="text-align:center;padding-top:32px">
        <div style="font-size:72px;margin-bottom:16px">🎉</div>
        <h3 style="font-size:20px;font-weight:700;margin-bottom:8px">本周问卷完成！</h3>
        <p style="font-size:14px;color:var(--sub);line-height:1.6;max-width:260px;margin:0 auto">
          数据已上报，下周一系统将自动发送新的问卷。
        </p>
      </div>
      <div class="card fu fu-1">
        <div class="card-title">本周综合评估</div>
        <div class="summary-grid">
          <div v-for="[label, value] in summaryItems" :key="label" class="summary-cell">
            <div class="summary-val">{{ value }}</div>
            <div class="summary-label">{{ label }}</div>
          </div>
        </div>
      </div>
      <button class="btn-main fu fu-2" @click="reset">查看历史记录</button>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { BEHAVIOR_QUESTIONS } from '@/data/questions'

const questions = BEHAVIOR_QUESTIONS
const step = ref(0)
const answers = reactive<Record<number, number>>({})
const done = ref(false)

const summaryItems: [string, string][] = [
  ['平均户外', '1.6h/天'],
  ['屏幕控制', '良好'],
  ['眼保健操', '4/5天'],
  ['依从评分', '82分'],
]

function next() {
  if (step.value < questions.length - 1) {
    step.value++
  } else {
    done.value = true
  }
}

function reset() {
  step.value = 0
  Object.keys(answers).forEach(k => delete answers[Number(k)])
  done.value = false
}
</script>

<style scoped>
.header-mini {
  background: var(--grad-header); color: white;
  padding: 16px 20px; font-size: 16px; font-weight: 700;
  display: flex; align-items: center; gap: 8px;
}
.content { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 16px; }
.progress-fill { height: 100%; background: var(--grad-teal); border-radius: 3px; transition: width .4s; }
.q-text { font-size: 15px; font-weight: 700; color: var(--ink); margin-bottom: 14px; line-height: 1.5; }
.q-opts { display: flex; flex-direction: column; gap: 8px; }
.q-opt {
  padding: 12px 14px; border: 2px solid var(--border); border-radius: 12px;
  font-size: 13px; color: var(--ink); cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 10px;
}
.q-opt.sel { border-color: var(--teal); background: var(--teal-l); color: var(--teal); font-weight: 600; }
.q-dot {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--border);
  flex-shrink: 0; transition: all .2s;
}
.q-opt.sel .q-dot { background: var(--teal); border-color: var(--teal); }
.q-nav { display: flex; gap: 8px; margin-top: 14px; }
.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.summary-cell {
  background: white; border-radius: 10px; padding: 10px;
  text-align: center; border: 1px solid var(--border);
}
.summary-val { font-size: 15px; font-weight: 700; color: var(--teal); }
.summary-label { font-size: 11px; color: var(--sub); margin-top: 2px; }
</style>
