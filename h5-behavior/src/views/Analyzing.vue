<template>
  <div class="screen">
    <div class="land-bg"><div class="orb orb1" /><div class="orb orb2" /></div>
    <div class="analyzing-wrap">
      <div class="analyzing-orb"><div class="analyzing-orb-inner">🧬</div></div>
      <div class="analyzing-title">AI正在构建你的行为图谱</div>
      <div style="font-size:13px;color:var(--sub)">整合五维评估 · 中医体质 · 行为科学模型</div>
      <div class="analyzing-steps">
        <div v-for="(s, i) in steps" :key="i" :class="['a-step', stepStatus(i)]">
          <div class="a-step-dot" />
          <div class="a-step-text">{{ s }}</div>
          <span v-if="stepStatus(i) === 'done'" class="a-step-check">✓</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'

const router = useRouter()
const store = useAssessmentStore()
const aStep = ref(0)

const steps = [
  '识别行为模式与代谢特征',
  '对比你的认知与真实影响因素',
  '匹配生态体质标签',
  '生成个性化行为处方',
]

function stepStatus(i: number) {
  if (aStep.value > i) return 'done'
  if (aStep.value === i) return 'active'
  return 'pending'
}

const timers: ReturnType<typeof setTimeout>[] = []

onMounted(async () => {
  timers.push(setTimeout(() => { aStep.value = 1 }, 900))
  timers.push(setTimeout(() => { aStep.value = 2 }, 1800))
  timers.push(setTimeout(() => { aStep.value = 3 }, 2700))
  timers.push(setTimeout(async () => {
    await store.doSubmit()
    router.replace('/factormap')
  }, 3500))
})

onUnmounted(() => timers.forEach(clearTimeout))
</script>

<style scoped>
.land-bg { position: absolute; inset: 0; overflow: hidden; }
.orb1 { position: absolute; width: 280px; height: 280px; background: var(--teal); top: -60px; right: -80px; border-radius: 50%; filter: blur(70px); opacity: .12; }
.orb2 { position: absolute; width: 220px; height: 220px; background: var(--amber); bottom: 80px; left: -60px; border-radius: 50%; filter: blur(70px); opacity: .1; }
.analyzing-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 22px; text-align: center; }
.analyzing-orb { width: 96px; height: 96px; border-radius: 50%; margin: 0 auto 28px; background: conic-gradient(var(--teal), var(--amber), var(--indigo), var(--teal)); animation: spin 2s linear infinite; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 30px rgba(0,184,160,.15); }
.analyzing-orb-inner { width: 72px; height: 72px; border-radius: 50%; background: var(--bg); display: flex; align-items: center; justify-content: center; font-size: 32px; }
.analyzing-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 22px; color: var(--ink); margin-bottom: 8px; }
.analyzing-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 28px; width: 100%; max-width: 280px; }
.a-step {
  display: flex; align-items: center; gap: 10px; font-size: 13px; padding: 12px 14px; border-radius: 14px;
  background: var(--card); border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03); transition: all .3s;
}
.a-step.done { border-color: rgba(6,214,160,.25); background: rgba(6,214,160,.06); }
.a-step.active { border-color: rgba(245,166,35,.3); }
.a-step-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; transition: all .3s; }
.a-step.done .a-step-dot { background: var(--sage); }
.a-step.active .a-step-dot { background: var(--amber); animation: blink 1s infinite; }
.a-step.pending .a-step-dot { background: var(--muted); }
.a-step-text { color: var(--sub); flex: 1; text-align: left; }
.a-step.done .a-step-text { color: var(--ink); }
.a-step.active .a-step-text { color: var(--amber-d); }
.a-step-check { color: var(--sage); font-size: 14px; font-weight: 700; }
</style>
