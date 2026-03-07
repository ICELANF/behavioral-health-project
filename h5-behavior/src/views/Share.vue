<template>
  <div class="screen" v-if="label && scores">
    <div class="pg" style="padding-top:40px">
      <div class="share-card fu">
        <div class="share-card-bg">
          <div class="share-orb" :style="{ background: label.color }" />
        </div>
        <div style="position:relative;z-index:2">
          <div class="share-tag">{{ label.icon }} {{ label.name }}</div>
          <div style="font-size:12px;color:var(--sub);margin-bottom:8px">{{ label.tcm }}</div>
          <div class="share-radar">
            <div v-for="d in dimList" :key="d.k" class="share-dim">
              <div class="share-dim-bar" :style="{ height: scores[d.k] * 0.6 + 'px', background: `linear-gradient(180deg, ${label.color}, ${label.color}66)` }" />
              <div class="share-dim-lbl">{{ d.name }}</div>
            </div>
          </div>
          <div class="share-bottom">
            <div>
              <div style="font-size:11px;color:var(--sub)">{{ ttmStage }}</div>
              <div class="share-brand">行健平台 · BehaviorOS</div>
            </div>
            <div class="share-qr">📱</div>
          </div>
        </div>
      </div>
      <button class="btn-main fu d1" :style="{ background: label.color, color: '#fff', flex: 'none', width: '100%', boxShadow: `0 4px 14px ${label.color}40` }">
        保存卡片到相册
      </button>
      <button class="btn-ghost fu d2" style="flex:none;width:100%;text-align:center" @click="$router.push('/result')">
        ← 返回结果页
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)
const scores = computed(() => store.currentScores)
const ttmStage = computed(() => {
  if (!scores.value) return ''
  const s = scores.value.stability
  if (s < 30) return 'S0 探索期'
  if (s < 60) return 'S1-S2 觉醒期'
  return 'S3-S4 行动期'
})
const dimList = [
  { k: 'metabolism' as const, name: '代谢' },
  { k: 'stress' as const, name: '压力' },
  { k: 'sleep' as const, name: '睡眠' },
  { k: 'stability' as const, name: '行为' },
  { k: 'control' as const, name: '心理' },
]
</script>

<style scoped>
.share-card {
  border-radius: 24px; padding: 28px; position: relative; overflow: hidden;
  background: var(--card); border: 1px solid var(--border);
  margin-bottom: 4px; box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.share-card-bg { position: absolute; inset: 0; overflow: hidden; }
.share-orb { position: absolute; width: 160px; height: 160px; top: -30px; right: -30px; opacity: .1; border-radius: 50%; filter: blur(40px); }
.share-tag { font-family: 'ZCOOL XiaoWei', serif; font-size: 40px; color: var(--ink); margin-bottom: 6px; }
.share-radar { display: flex; gap: 8px; margin: 16px 0; }
.share-dim { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.share-dim-bar { width: 100%; border-radius: 4px; }
.share-dim-lbl { font-size: 9px; color: var(--muted); font-weight: 500; }
.share-bottom { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 16px; }
.share-qr { width: 44px; height: 44px; background: var(--bg); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; border: 1px solid var(--border); }
.share-brand { font-size: 11px; color: var(--muted); margin-top: 2px; }
</style>
