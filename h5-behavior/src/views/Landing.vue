<template>
  <div class="screen">
    <div class="land-bg">
      <div class="orb orb1" /><div class="orb orb2" /><div class="orb orb3" />
    </div>
    <div class="land-content">
      <div class="land-badge fu">🌱 行为健康 · 行健平台</div>
      <h1 class="land-h1 fu d1">你现在最大的<br /><em>隐忧</em>、<em>困惑</em>和<em>焦虑</em>？……</h1>
      <p class="land-sub fu d2">选一个最贴近你的入口，3分钟<br />AI帮你找到真正的影响因素和改变路径</p>
      <div class="land-doors">
        <div v-for="(d, i) in DOORS" :key="d.key"
          :class="['door', `door-${d.key}`, 'fu', `d${i + 2}`]"
          @click="enterDoor(d.key)">
          <div class="door-bar" :style="{ background: d.color }" />
          <div class="door-icon" :style="{ background: d.color + '18' }">{{ d.icon }}</div>
          <div class="door-body">
            <div class="door-label" :style="{ color: d.color }">{{ d.label }}</div>
            <div class="door-title">{{ d.title.slice(0, 14) }}…</div>
            <div class="door-desc">{{ d.desc }}</div>
          </div>
          <div class="door-arrow" :style="{ color: d.color }">›</div>
        </div>
      </div>
      <div class="land-footer fu d5">
        已有 <span class="land-num">12,847</span> 人完成评估 · 匿名无需注册
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import { DOORS } from '@/data/doors'

const router = useRouter()
const route = useRoute()
const store = useAssessmentStore()

function enterDoor(key: string) {
  store.setDoor(key)
  router.push('/concern')
}

// 支持从 H5 主站跳入时携带 ?door=symptom 自动进入流程
onMounted(() => {
  const door = route.query.door as string
  if (door && DOORS.some(d => d.key === door)) {
    enterDoor(door)
  }
})
</script>

<style scoped>
.land-bg { position: absolute; inset: 0; overflow: hidden; }
.orb { position: absolute; border-radius: 50%; filter: blur(70px); }
.orb1 { width: 260px; height: 260px; background: rgba(0,184,160,.15); top: -80px; right: -60px; }
.orb2 { width: 200px; height: 200px; background: rgba(245,166,35,.12); bottom: 100px; left: -80px; }
.orb3 { width: 140px; height: 140px; background: rgba(76,110,245,.1); top: 45%; right: 30px; }
.land-content { position: relative; z-index: 2; padding: 48px 22px 30px; flex: 1; display: flex; flex-direction: column; }
.land-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(0,184,160,.12); border: 1px solid rgba(0,184,160,.25);
  border-radius: 20px; padding: 6px 16px; font-size: 11px; color: var(--teal);
  font-weight: 600; letter-spacing: .5px; margin-bottom: 28px; width: fit-content;
  box-shadow: 0 2px 8px rgba(0,184,160,.15);
}
.land-badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--teal); animation: blink 2s infinite; }
.land-h1 { font-family: 'ZCOOL XiaoWei', serif; font-size: 36px; line-height: 1.2; color: var(--ink); margin-bottom: 12px; letter-spacing: 1px; }
.land-h1 em { font-style: normal; background: linear-gradient(135deg, var(--amber), var(--rose)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.land-sub { font-size: 14px; color: var(--sub); line-height: 1.7; margin-bottom: 36px; }
.land-doors { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }
.door {
  border-radius: 20px; padding: 18px 18px 18px 22px; cursor: pointer; position: relative; overflow: hidden;
  border: 1px solid var(--border); background: var(--card);
  box-shadow: var(--shadow-lg);
  transition: all .3s; display: flex; align-items: center; gap: 14px;
}
.door:active { transform: scale(.97); box-shadow: var(--shadow-sm); }
.door-bar { position: absolute; left: 0; top: 12px; bottom: 12px; width: 4px; border-radius: 0 3px 3px 0; }
.door-icon {
  width: 52px; height: 52px; border-radius: 16px; display: flex; align-items: center;
  justify-content: center; font-size: 26px; flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.door-body { flex: 1; }
.door-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 3px; }
.door-title { font-size: 16px; font-weight: 700; color: var(--ink); margin-bottom: 2px; }
.door-desc { font-size: 12px; color: var(--sub); line-height: 1.4; }
.door-arrow { font-size: 22px; flex-shrink: 0; font-weight: 300; transition: transform .2s; }
.door:active .door-arrow { transform: translateX(3px); }
.land-footer { font-size: 11px; color: var(--muted); text-align: center; line-height: 1.6; }
.land-num { color: var(--teal); font-weight: 700; font-size: 13px; }
</style>
