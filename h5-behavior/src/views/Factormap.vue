<template>
  <div class="screen" v-if="label">
    <div class="land-bg" style="opacity:.3">
      <div class="orb" :style="{ background: label.color, width: '200px', height: '200px', top: '-40px', right: '-40px', opacity: '.12', position: 'absolute', borderRadius: '50%', filter: 'blur(60px)' }" />
    </div>
    <div class="fmap-hdr fu">
      <div class="fmap-title">两张影响因素地图</div>
      <div class="fmap-sub">你说的原因，和AI识别到的，是两份不同的清单</div>
    </div>
    <div class="pg" style="padding-top:0;gap:12px">
      <div class="fmap-col fmap-you fu d1">
        <div class="fmap-col-title" :style="{ color: D.amber }"><span>👤</span> 你认为的原因</div>
        <div v-for="(bt, bi) in store.beliefTexts" :key="bi" class="fmap-row match">
          <div class="fmap-factor">{{ bt }}</div>
          <div class="fmap-bar-wrap"><div class="fmap-bar-bg"><div class="fmap-bar-fill" :style="{ width: (55 - bi * 8) + '%', background: `linear-gradient(90deg, ${D.amber}, ${D.amber}aa)` }" /></div></div>
          <span class="fmap-tag fmap-match">✓ 有效</span>
        </div>
        <div style="font-size:12px;color:var(--muted);margin-top:8px;font-style:italic">
          这个原因是真实的，但它更多是结果，而不是根源。
        </div>
      </div>
      <div class="fmap-col fmap-ai fu d2">
        <div class="fmap-col-title" :style="{ color: D.teal }"><span>🤖</span> AI识别到的真实影响因素</div>
        <div v-for="(f, i) in aiFactors" :key="i" :class="['fmap-row', { match: f.tag === 'match' }]">
          <div class="fmap-factor">{{ f.name }}</div>
          <div class="fmap-bar-wrap"><div class="fmap-bar-bg"><div class="fmap-bar-fill" :style="{ width: f.pct + '%', background: f.tag === 'match' ? D.sage : `linear-gradient(90deg, ${D.teal}, ${D.teal}aa)` }" /></div></div>
          <span :class="['fmap-tag', f.tag === 'match' ? 'fmap-match' : 'fmap-new']">
            {{ f.tag === 'match' ? '✓ 你提到了' : '🆕 你没提到' }}
          </span>
        </div>
      </div>
      <div class="fmap-insight fu d3">
        <div class="fmap-insight-q">💡 关键洞察</div>
        <div class="fmap-insight-p">
          这些你没提到的因素，正在以你看不见的方式累积影响。
          好消息是：<strong :style="{ color: D.teal }">其中4项，只需要改变特定行为就能直接干预</strong>——
          不需要药物，不需要巨大的意志力。
        </div>
      </div>
      <button class="btn-main fu d4" :style="{ background: label.color, color: '#fff', boxShadow: `0 4px 14px ${label.color}40` }" @click="$router.push('/result')">
        查看你的完整画像 →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { D } from '@/design/tokens'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)

const aiFactors = computed(() => [
  { name: '血糖波动节律', pct: 88, tag: 'new' },
  { name: '皮质醇昼夜节律', pct: 76, tag: 'new' },
  { name: '恢复行为严重缺位', pct: 70, tag: 'new' },
  { name: store.beliefTexts[0] || '睡眠质量', pct: 52, tag: 'match' },
  { name: '环境设计缺失', pct: 45, tag: 'new' },
])
</script>

<style scoped>
.fmap-hdr { padding: 28px 22px 16px; }
.fmap-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 26px; color: var(--ink); margin-bottom: 6px; }
.fmap-sub { font-size: 13px; color: var(--sub); line-height: 1.6; }
.fmap-col { border-radius: 20px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.fmap-you { background: rgba(245,166,35,.06); border: 1px solid rgba(245,166,35,.15); }
.fmap-ai { background: rgba(0,184,160,.05); border: 1px solid rgba(0,184,160,.15); }
.fmap-col-title { font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
.fmap-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,.04); }
.fmap-row:last-child { border-bottom: none; padding-bottom: 0; }
.fmap-factor { flex: 1; font-size: 13px; color: var(--sub); }
.fmap-row.match .fmap-factor { color: var(--ink); font-weight: 500; }
.fmap-bar-wrap { width: 90px; }
.fmap-bar-bg { height: 6px; background: rgba(0,0,0,.06); border-radius: 3px; overflow: hidden; }
.fmap-bar-fill { height: 100%; border-radius: 3px; transition: width 1s .3s; }
.fmap-tag { font-size: 10px; padding: 2px 8px; border-radius: 8px; font-weight: 600; flex-shrink: 0; }
.fmap-new { background: rgba(0,184,160,.12); color: var(--teal-d); }
.fmap-match { background: rgba(6,214,160,.12); color: #05a87e; }
.fmap-insight { border-radius: 20px; padding: 18px; background: rgba(212,160,23,.06); border: 1px solid rgba(212,160,23,.15); margin-top: 2px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.fmap-insight-q { font-size: 14px; font-weight: 600; color: var(--gold); margin-bottom: 6px; }
.fmap-insight-p { font-size: 13px; color: var(--sub); line-height: 1.7; }
</style>
