<template>
  <div class="screen" v-if="label">
    <div class="comp-hdr">
      <div class="comp-hdr-bg" />
      <div style="position:relative;z-index:2">
        <div class="comp-date">{{ today }}</div>
        <div class="comp-greeting">你好，成长者</div>
        <div class="comp-stage">{{ label.icon }} {{ label.name }} · 第1天</div>
      </div>
      <div class="comp-streak">
        <div class="comp-streak-n">1</div>
        <div class="comp-streak-l">连续天数</div>
      </div>
    </div>
    <div class="pg" style="padding-top:0">
      <!-- today tasks -->
      <div class="card fu d1">
        <div class="card-hd">今日微行动</div>
        <div v-for="(a, i) in label.actions" :key="i"
          :class="['task-item', 'fu', `d${i + 1}`, { done: doneTasks.includes(i) }]"
          @click="toggleTask(i)">
          <div class="task-ico" :style="{ background: a.color + '15' }">{{ a.ico }}</div>
          <div class="task-body">
            <div class="task-name">{{ a.name }}</div>
            <div class="task-why">{{ a.why.slice(0, 40) }}…</div>
          </div>
          <div :class="['task-check', { 'check-done': doneTasks.includes(i) }]"
            :style="doneTasks.includes(i) ? { background: 'var(--sage)', borderColor: 'var(--sage)' } : {}">
            {{ doneTasks.includes(i) ? '✓' : '' }}
          </div>
        </div>
      </div>

      <!-- AI companion bubble -->
      <div class="ai-bubble fu d3">
        <div class="ai-avatar">🤖</div>
        <div>{{ label.name }}的你，今天最重要的是"{{ label.actions[0].name }}"。</div>
        <div class="ai-insight" v-if="store.expectations.length">
          记住你的北极星：{{ store.expectations[0] }}。今天的微行动正在为它铺路。
        </div>
      </div>

      <!-- 成长者权益说明 -->
      <div class="grower-section fu d4">
        <div class="grower-title">成为成长者，解锁全部能力</div>
        <div class="grower-sub">从7天微实验到持续行为改变，成长者拥有完整的支持体系</div>

        <div class="benefit-list">
          <div v-for="b in benefits" :key="b.name" class="benefit-card">
            <div class="benefit-ico" :style="{ background: b.bg }">{{ b.ico }}</div>
            <div class="benefit-body">
              <div class="benefit-name">{{ b.name }}</div>
              <div class="benefit-desc">{{ b.desc }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA: 进入成长者系统 -->
      <a :href="growerUrl" class="btn-main grower-cta fu d5">
        进入成长者系统 →
      </a>

      <div class="grower-note fu d6">
        你的评估数据和体质标签将自动同步到成长者系统
      </div>
    </div>

    <!-- bottom nav -->
    <div class="bnav">
      <div :class="['bnav-item', { on: tab === 0 }]" @click="tab = 0">
        <div class="bnav-ico">📋</div><div class="bnav-lbl">今日</div>
      </div>
      <div class="bnav-item on-main" @click="goGrower">
        <div class="bnav-ico-main">🌱</div>
        <div class="bnav-lbl" style="color:var(--teal);font-weight:700">成长者</div>
      </div>
      <div :class="['bnav-item', { on: tab === 2 }]" @click="tab = 2">
        <div class="bnav-ico">💬</div><div class="bnav-lbl">对话</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)
const tab = ref(0)
const doneTasks = ref<number[]>([])

const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })

// H5 成长者系统入口（同域，不同路径）
const growerUrl = computed(() => {
  const base = window.location.origin
  return `${base}/home/today`
})

const benefits = [
  {
    ico: '🩺', name: '代谢监测',
    desc: '血糖、体重、心率持续追踪，AI 自动识别波动规律',
    bg: 'rgba(245,166,35,.1)'
  },
  {
    ico: '🎯', name: '个性化行为处方',
    desc: '基于你的体质标签，教练定制每日微行动方案',
    bg: 'rgba(0,184,160,.1)'
  },
  {
    ico: '📚', name: '课程学习',
    desc: '行为科学 + 中医体质课程，系统提升健康认知',
    bg: 'rgba(76,110,245,.1)'
  },
  {
    ico: '👩‍⚕️', name: '专属教练陪伴',
    desc: '1对1教练匹配，每日提醒、进度审核、答疑解惑',
    bg: 'rgba(245,101,101,.08)'
  },
  {
    ico: '📈', name: '行为轨迹与周报',
    desc: '可视化你的改变路径，每周生成 AI 行为分析报告',
    bg: 'rgba(212,160,23,.1)'
  },
  {
    ico: '🤝', name: '同道者社群',
    desc: '和同类型体质的伙伴互相激励，不再一个人战斗',
    bg: 'rgba(6,214,160,.1)'
  },
]

function toggleTask(i: number) {
  const idx = doneTasks.value.indexOf(i)
  if (idx >= 0) doneTasks.value.splice(idx, 1)
  else doneTasks.value.push(i)
}

function goGrower() {
  window.location.href = growerUrl.value
}
</script>

<style scoped>
.comp-hdr { padding: 28px 22px 22px; position: relative; overflow: hidden; }
.comp-hdr-bg { position: absolute; inset: 0; background: var(--grad-dark); }
.comp-date { font-size: 11px; color: rgba(255,255,255,.5); margin-bottom: 4px; }
.comp-greeting { font-family: 'ZCOOL XiaoWei', serif; font-size: 24px; color: #fff; margin-bottom: 2px; }
.comp-stage { font-size: 12px; color: rgba(0,212,184,.9); font-weight: 600; }
.comp-streak {
  position: absolute; top: 28px; right: 22px; text-align: center;
  background: rgba(212,160,23,.15); border: 1px solid rgba(212,160,23,.25);
  border-radius: 16px; padding: 12px 18px;
  box-shadow: 0 4px 16px rgba(212,160,23,.2);
}
.comp-streak-n { font-family: 'ZCOOL XiaoWei', serif; font-size: 32px; color: var(--amber); }
.comp-streak-l { font-size: 10px; color: rgba(255,255,255,.6); }
.task-item {
  border-radius: 16px; padding: 14px; border: 1px solid var(--border); background: var(--card);
  box-shadow: var(--shadow-md);
  display: flex; align-items: flex-start; gap: 12px; cursor: pointer; transition: all .25s; margin-bottom: 8px;
}
.task-item.done { border-color: rgba(6,214,160,.2); background: rgba(6,214,160,.04); }
.task-item:active { transform: scale(.98); }
.task-ico { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.task-body { flex: 1; }
.task-name { font-size: 14px; font-weight: 600; color: var(--ink); margin-bottom: 3px; }
.task-why { font-size: 12px; color: var(--sub); line-height: 1.5; }
.task-check {
  width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid var(--border-m);
  display: flex; align-items: center; justify-content: center; font-size: 13px; color: #fff;
  transition: all .25s; flex-shrink: 0;
}
.check-done { animation: checkPop .25s ease both; }
.ai-bubble {
  background: var(--card); border: 1px solid var(--border); border-radius: 20px 20px 20px 6px;
  padding: 16px 18px; font-size: 13px; color: var(--sub); line-height: 1.7; position: relative;
  box-shadow: var(--shadow-md);
}
.ai-avatar { position: absolute; top: -12px; left: 16px; font-size: 18px; background: var(--bg); padding: 0 4px; }
.ai-insight {
  background: rgba(212,160,23,.06); border: 1px solid rgba(212,160,23,.12);
  border-radius: 12px; padding: 12px; margin-top: 10px; font-size: 12px; color: var(--gold); line-height: 1.6;
}

/* 成长者权益 */
.grower-section {
  border-radius: 24px; padding: 24px 20px;
  background: linear-gradient(160deg, rgba(0,184,160,.06), rgba(76,110,245,.04));
  border: 1px solid rgba(0,184,160,.12);
}
.grower-title {
  font-family: 'ZCOOL XiaoWei', serif; font-size: 20px; color: var(--ink); margin-bottom: 6px;
}
.grower-sub { font-size: 12px; color: var(--sub); line-height: 1.6; margin-bottom: 18px; }
.benefit-list { display: flex; flex-direction: column; gap: 12px; }
.benefit-card {
  display: flex; align-items: center; gap: 12px;
  padding: 16px; border-radius: 16px;
  background: var(--card); border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow .2s;
}
.benefit-card:active { box-shadow: var(--shadow-md); }
.benefit-ico {
  width: 46px; height: 46px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0;
  box-shadow: 0 3px 8px rgba(0,0,0,0.06);
}
.benefit-body { flex: 1; }
.benefit-name { font-size: 14px; font-weight: 600; color: var(--ink); margin-bottom: 2px; }
.benefit-desc { font-size: 11px; color: var(--sub); line-height: 1.5; }

.grower-cta {
  display: flex; align-items: center; justify-content: center;
  width: 100%; text-decoration: none;
  background: var(--grad-teal); color: #fff;
  box-shadow: 0 6px 24px rgba(0,184,160,.4);
  font-size: 16px; font-weight: 700;
}
.grower-note {
  font-size: 11px; color: var(--muted); text-align: center; line-height: 1.5;
}

/* bottom nav */
.bnav {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 390px;
  background: rgba(255,255,255,.88); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border-top: 1px solid rgba(0,0,0,.06);
  display: flex; padding: 8px 0 18px; z-index: 30;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.06);
}
.bnav-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; cursor: pointer; padding: 4px 0; }
.bnav-ico { font-size: 21px; }
.bnav-lbl { font-size: 9px; color: var(--muted); font-weight: 500; }
.bnav-item.on .bnav-lbl { color: var(--teal); font-weight: 700; }
.on-main { position: relative; }
.bnav-ico-main {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), #00d4b8);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; margin-top: -18px;
  box-shadow: 0 4px 14px rgba(0,184,160,.3);
}
</style>
