<template>
  <div class="screen" v-if="label && scores">
    <div class="land-bg">
      <div class="orb" :style="{ background: label.color, width: '240px', height: '240px', top: '-60px', right: '-50px', opacity: '.12', position:'absolute', borderRadius:'50%', filter:'blur(60px)' }" />
    </div>

    <!-- Phase 1: 解锁动画 -->
    <div v-if="phase === 'unlocking'" class="unlock-anim">
      <div class="unlock-orb" :style="{ boxShadow: `0 0 40px ${label.color}30` }">
        <div class="unlock-orb-inner">{{ label.icon }}</div>
      </div>
      <div class="unlock-title fu">正在解锁你的完整报告</div>
      <div class="unlock-steps">
        <div v-for="(s, i) in unlockSteps" :key="i"
          :class="['unlock-step', unlockIdx > i ? 'done' : unlockIdx === i ? 'active' : '']">
          <div class="unlock-dot" />
          <span>{{ s }}</span>
          <span v-if="unlockIdx > i" class="unlock-check">✓</span>
        </div>
      </div>
    </div>

    <!-- Phase 2: 完整报告展示 -->
    <div v-if="phase === 'report'" class="pg" style="padding-top:24px">
      <div class="report-badge fu">✅ 报告已解锁</div>

      <!-- 体质标签 hero -->
      <div class="card report-hero fu d1">
        <div class="rh-tag" :style="{ color: label.color }">{{ label.icon }} {{ label.name }}</div>
        <div class="rh-tcm">{{ label.tcm }}</div>
        <div class="rh-insight" :style="{ borderColor: label.color }">{{ label.insight }}</div>
      </div>

      <!-- 五维雷达 -->
      <div class="card fu d2">
        <div class="card-hd">五维行为图谱 <span class="chip chip-teal">BPT-6 x TTM</span></div>
        <div style="display:flex;justify-content:center;margin-bottom:8px">
          <RadarChart :scores="scores" :color="label.color" />
        </div>
        <div v-for="d in dimList" :key="d.k" class="dim-row">
          <div class="dim-icon">{{ d.icon }}</div>
          <div class="dim-info">
            <div class="dim-name">{{ d.name }}</div>
            <div class="dim-bar-bg"><div class="dim-bar-fill" :style="{ width: scores[d.k] + '%', background: `linear-gradient(90deg, ${label.color}, ${label.color}aa)` }" /></div>
          </div>
          <div class="dim-pct" :style="{ color: scores[d.k] > 65 ? D.rose : scores[d.k] > 40 ? D.amber : D.sage }">
            {{ scores[d.k] }}%
          </div>
        </div>
      </div>

      <!-- 禁忌 -->
      <div class="taboo-box fu d3">
        <span style="font-size:14px">⚠️</span>
        <div style="flex:1">
          <div style="font-size:11px;font-weight:700;color:var(--rose)">体质禁忌</div>
          <div style="font-size:12px;color:var(--sub);margin-top:2px">{{ label.taboo }}</div>
        </div>
      </div>

      <!-- 微行动方案 -->
      <div class="card fu d4">
        <div class="card-hd">你的微行动方案</div>
        <div v-for="(a, i) in label.actions" :key="i" class="action-row">
          <div class="action-ico" :style="{ background: a.color + '15' }">{{ a.ico }}</div>
          <div style="flex:1">
            <div style="font-size:14px;font-weight:600;color:var(--ink)">{{ a.name }}</div>
            <div style="font-size:12px;color:var(--sub);margin-top:2px">{{ a.why }}</div>
          </div>
        </div>
      </div>

      <!-- 北极星目标 -->
      <div v-if="assessStore.expectations.length" class="card fu d5">
        <div class="card-hd">🎯 你的北极星目标</div>
        <div v-for="exp in assessStore.expectations" :key="exp" class="exp-row">
          <span style="color:var(--teal);flex-shrink:0">→</span>
          <span style="font-size:13px;color:var(--sub)">{{ exp }}</span>
        </div>
      </div>

      <!-- CTA -->
      <button class="btn-main fu d5"
        :style="{ background: D.teal, color: '#fff', width: '100%', boxShadow: `0 4px 14px rgba(0,184,160,.4)` }"
        @click="$router.replace('/companion')">
        开始你的7天微实验 →
      </button>
      <button class="btn-ghost fu d6" style="width:100%;text-align:center"
        @click="$router.push('/share')">
        📤 分享我的体质卡片
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { D } from '@/design/tokens'
import RadarChart from '@/components/RadarChart.vue'

const assessStore = useAssessmentStore()
const label = computed(() => assessStore.currentLabel)
const scores = computed(() => assessStore.currentScores)

const phase = ref<'unlocking' | 'report'>('unlocking')
const unlockIdx = ref(0)

const unlockSteps = [
  '验证身份信息',
  '加载五维评估数据',
  '生成个性化方案',
  '报告解锁完成',
]

const dimList = [
  { k: 'metabolism' as const, icon: '⚡', name: '代谢负荷' },
  { k: 'stress' as const, icon: '🔥', name: '压力激活' },
  { k: 'sleep' as const, icon: '🌙', name: '睡眠修复' },
  { k: 'stability' as const, icon: '🎯', name: '行为稳定' },
  { k: 'control' as const, icon: '💎', name: '心理掌控' },
]

const timers: ReturnType<typeof setTimeout>[] = []

onMounted(() => {
  timers.push(setTimeout(() => { unlockIdx.value = 1 }, 600))
  timers.push(setTimeout(() => { unlockIdx.value = 2 }, 1200))
  timers.push(setTimeout(() => { unlockIdx.value = 3 }, 1800))
  timers.push(setTimeout(() => { unlockIdx.value = 4; phase.value = 'report' }, 2400))
})

onUnmounted(() => timers.forEach(clearTimeout))
</script>

<style scoped>
.land-bg { position: absolute; inset: 0; overflow: hidden; }

/* Unlock animation */
.unlock-anim {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 40px 22px; text-align: center; position: relative; z-index: 2;
}
.unlock-orb {
  width: 88px; height: 88px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(0,184,160,.15), rgba(76,110,245,.1));
  display: flex; align-items: center; justify-content: center;
  animation: unlockPulse 1.5s ease infinite;
}
.unlock-orb-inner {
  width: 64px; height: 64px; border-radius: 50%; background: var(--card);
  display: flex; align-items: center; justify-content: center; font-size: 28px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
@keyframes unlockPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}
.unlock-title {
  font-family: 'ZCOOL XiaoWei', serif; font-size: 20px; color: var(--ink); margin-top: 24px;
}
.unlock-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 24px; width: 100%; max-width: 260px; }
.unlock-step {
  display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--sub);
  padding: 10px 14px; border-radius: 12px;
  background: var(--card); border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0,0,0,0.03); transition: all .3s;
}
.unlock-step.done { border-color: rgba(6,214,160,.25); background: rgba(6,214,160,.05); }
.unlock-step.done span:first-of-type { color: var(--ink); }
.unlock-step.active { border-color: rgba(0,184,160,.3); }
.unlock-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; transition: all .3s;
  background: var(--muted);
}
.unlock-step.done .unlock-dot { background: var(--sage); }
.unlock-step.active .unlock-dot { background: var(--teal); animation: blink 1s infinite; }
.unlock-check { color: var(--sage); font-size: 13px; font-weight: 700; margin-left: auto; }

/* Report badge */
.report-badge {
  display: inline-flex; align-items: center; gap: 6px; align-self: center;
  background: rgba(6,214,160,.12); border: 1px solid rgba(6,214,160,.25);
  border-radius: 20px; padding: 6px 16px; font-size: 12px; color: var(--sage);
  font-weight: 600; margin-bottom: 4px;
  box-shadow: 0 2px 10px rgba(6,214,160,.2);
}

/* Report hero */
.report-hero {
  text-align: center; padding: 28px 24px; position: relative; overflow: hidden;
  box-shadow: var(--shadow-lg);
}
.report-hero::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  background: var(--grad-teal);
}
.rh-tag { font-family: 'ZCOOL XiaoWei', serif; font-size: 32px; margin-bottom: 6px; }
.rh-tcm { font-size: 12px; color: var(--sub); margin-bottom: 14px; }
.rh-insight {
  font-size: 13px; color: var(--sub); line-height: 1.7; text-align: left;
  padding-left: 12px; border-left: 3px solid;
}

/* Dimension bars */
.dim-row { display: flex; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,.04); }
.dim-row:last-child { border-bottom: none; }
.dim-icon { font-size: 18px; width: 24px; text-align: center; flex-shrink: 0; }
.dim-info { flex: 1; }
.dim-name { font-size: 12px; font-weight: 600; color: var(--ink); margin-bottom: 4px; }
.dim-bar-bg { height: 8px; background: rgba(0,0,0,.06); border-radius: 4px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 4px; transition: width 1.2s .2s cubic-bezier(.4,0,.2,1); box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
.dim-pct { font-size: 15px; font-weight: 800; min-width: 40px; text-align: right; flex-shrink: 0; }

/* Taboo */
.taboo-box {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-radius: 16px;
  background: rgba(245,101,101,.06); border: 1px solid rgba(245,101,101,.15);
  box-shadow: 0 2px 8px rgba(245,101,101,.08);
}

/* Actions */
.action-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 0; border-bottom: 1px solid rgba(0,0,0,.04);
}
.action-row:last-child { border-bottom: none; }
.action-ico {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;
  box-shadow: 0 3px 8px rgba(0,0,0,0.06);
}

/* Expectations */
.exp-row {
  display: flex; gap: 8px; padding: 8px 0;
  border-bottom: 1px dashed rgba(0,0,0,.05); line-height: 1.5;
}
.exp-row:last-child { border-bottom: none; }
</style>
