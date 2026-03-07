<template>
  <div class="screen" v-if="label && scores">
    <div class="result-hero fu">
      <div class="result-orbs">
        <div class="result-orb1" :style="{ background: label.color }" />
        <div class="result-orb2" :style="{ background: D.indigo }" />
      </div>
      <div class="result-label-row">
        <div class="result-ttm">
          TTM阶段：{{ ttmStage }} &nbsp;·&nbsp; 行健平台
        </div>
        <div class="result-tag">{{ label.icon }} {{ label.name }}</div>
        <div class="result-tcm" :style="{ color: label.color }">{{ label.tcm }}</div>
      </div>
      <div class="result-insight" :style="{ borderColor: label.color }">{{ label.insight }}</div>
    </div>
    <div class="pg" style="padding-top:0">
      <div class="card fu d1">
        <div class="card-hd">五维行为图谱 <span class="chip chip-teal">BPT-6 × TTM</span></div>
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
      <button class="btn-main fu d2" :style="{ background: label.color, color: '#fff', boxShadow: `0 4px 14px ${label.color}40` }" @click="$router.push('/expectation')">
        告诉AI你希望改变什么 →
      </button>
      <button class="btn-ghost fu d3" style="width:100%;text-align:center" @click="$router.push('/share')">
        📤 分享我的体质卡片
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { D } from '@/design/tokens'
import RadarChart from '@/components/RadarChart.vue'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)
const scores = computed(() => store.currentScores)
const ttmStage = computed(() => {
  if (!scores.value) return ''
  const s = scores.value.stability
  if (s < 30) return 'S0 探索期 · 觉察中'
  if (s < 60) return 'S1-S2 觉醒-思考期 · 准备改变'
  return 'S3-S4 准备-行动期 · 已在启动'
})

const dimList = [
  { k: 'metabolism' as const, icon: '⚡', name: '代谢负荷' },
  { k: 'stress' as const, icon: '🔥', name: '压力激活' },
  { k: 'sleep' as const, icon: '🌙', name: '睡眠修复' },
  { k: 'stability' as const, icon: '🎯', name: '行为稳定' },
  { k: 'control' as const, icon: '💎', name: '心理掌控' },
]
</script>

<style scoped>
.result-hero { padding: 28px 22px 20px; position: relative; overflow: hidden; }
.result-orbs { position: absolute; inset: 0; overflow: hidden; }
.result-orb1 { position: absolute; width: 200px; height: 200px; border-radius: 50%; filter: blur(60px); opacity: .1; top: -60px; right: -40px; }
.result-orb2 { position: absolute; width: 150px; height: 150px; border-radius: 50%; filter: blur(50px); opacity: .08; bottom: -30px; left: -20px; }
.result-label-row { position: relative; z-index: 2; margin-bottom: 8px; }
.result-ttm { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: var(--muted); margin-bottom: 6px; }
.result-tag { font-family: 'ZCOOL XiaoWei', serif; font-size: 32px; color: var(--ink); line-height: 1.2; margin-bottom: 4px; }
.result-tcm { font-size: 13px; line-height: 1.5; font-weight: 500; }
.result-insight { position: relative; z-index: 2; font-size: 14px; color: var(--sub); line-height: 1.7; margin-top: 10px; padding-left: 12px; border-left: 3px solid; }
.dim-row { display: flex; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid rgba(0,0,0,.04); }
.dim-row:last-child { border-bottom: none; }
.dim-icon { font-size: 18px; width: 24px; text-align: center; flex-shrink: 0; }
.dim-info { flex: 1; }
.dim-name { font-size: 12px; font-weight: 600; color: var(--ink); margin-bottom: 4px; }
.dim-bar-bg { height: 6px; background: rgba(0,0,0,.06); border-radius: 3px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 3px; transition: width 1.2s .2s cubic-bezier(.4,0,.2,1); }
.dim-pct { font-size: 13px; font-weight: 700; min-width: 36px; text-align: right; flex-shrink: 0; }
</style>
