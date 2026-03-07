<template>
  <div class="screen" v-if="label">
    <div class="rx-hero">
      <div class="rx-title fu">你的7天微实验</div>
      <div class="rx-sub fu d1">{{ label.name }} · 观察3天 + 行动4天</div>
    </div>
    <div class="pg" style="padding-top:0">
      <!-- 7-day grid -->
      <div class="rx-week fu d1">
        <div v-for="day in 7" :key="day" :class="['rx-day', day <= 3 ? 'phase1' : 'phase2', { today: day === 1 }]">
          <div class="rx-day-n">D{{ day }}</div>
          <div class="rx-day-ico">{{ day <= 3 ? '👀' : '🎯' }}</div>
          <div class="rx-day-lbl">{{ day <= 3 ? '观察' : '行动' }}</div>
        </div>
      </div>
      <div class="rx-phase-legend fu d1">
        <span class="rx-legend-item rx-legend-observe">D1-3 观察记录期</span>
        <span class="rx-legend-item rx-legend-action">D4-7 微行动期</span>
      </div>

      <!-- action cards -->
      <div v-for="(a, i) in label.actions" :key="i" :class="['rx-action-card', 'fu', `d${i + 2}`, { active: i === 0 }]">
        <div class="rx-action-hd">
          <div class="rx-action-ico" :style="{ background: a.color + '15' }">{{ a.ico }}</div>
          <div>
            <div class="rx-action-label" :style="{ color: a.color }">{{ i === 0 ? '今日微行动' : '储备行动 ' + i }}</div>
            <div class="rx-action-name">{{ a.name }}</div>
          </div>
        </div>
        <div class="rx-mech">{{ a.why }}</div>
      </div>

      <!-- taboo -->
      <div class="rx-taboo fu d5">{{ label.taboo }}</div>

      <!-- expectation feedback -->
      <div v-if="store.expectations.length" class="exp-feedback fu d5">
        <div class="exp-feedback-title">🎯 你的北极星目标连接</div>
        <div v-for="exp in store.expectations" :key="exp" class="exp-feedback-item">
          <span class="exp-feedback-arrow">→</span>
          <span>{{ exp }}</span>
        </div>
      </div>

      <!-- register CTA -->
      <div class="reg-cta fu d6">
        <div class="reg-title">开始你的7天微实验</div>
        <div class="reg-sub">注册后解锁每日提醒、AI陪伴、进度追踪</div>
        <div class="reg-features">
          <span class="reg-feat">✓ AI教练</span>
          <span class="reg-feat">✓ 每日提醒</span>
          <span class="reg-feat">✓ 数据追踪</span>
        </div>
        <button class="btn-main" :style="{ background: D.teal, color: '#fff', width: '100%' }"
          @click="$router.push('/register')">
          注册并开始 →
        </button>
        <div style="font-size:11px;color:var(--muted);margin-top:10px">
          已有教练在线陪伴 · 完全免费
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { D } from '@/design/tokens'

const store = useAssessmentStore()
const label = computed(() => store.currentLabel)
</script>

<style scoped>
.rx-hero { padding: 24px 22px 16px; }
.rx-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 26px; color: var(--ink); margin-bottom: 6px; }
.rx-sub { font-size: 13px; color: var(--sub); line-height: 1.6; }
.rx-week { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-bottom: 6px; }
.rx-day {
  border-radius: 12px; padding: 10px 3px 8px; text-align: center;
  border: 1.5px solid var(--border); background: var(--card);
  box-shadow: 0 1px 3px rgba(0,0,0,0.03); transition: all .3s;
}
.rx-day.phase1 { border-color: rgba(245,166,35,.2); background: rgba(245,166,35,.05); }
.rx-day.phase2 { border-color: rgba(0,184,160,.2); background: rgba(0,184,160,.04); }
.rx-day.today { box-shadow: 0 0 0 2px var(--teal), 0 2px 8px rgba(0,184,160,.15); }
.rx-day-n { font-size: 9px; color: var(--muted); margin-bottom: 4px; font-weight: 600; }
.rx-day-ico { font-size: 16px; }
.rx-day-lbl { font-size: 8px; color: var(--muted); margin-top: 3px; line-height: 1.2; }
.rx-phase-legend { display: flex; gap: 12px; margin-bottom: 14px; }
.rx-legend-item { font-size: 11px; color: var(--sub); display: flex; align-items: center; gap: 5px; }
.rx-legend-item::before { content: ''; width: 8px; height: 8px; border-radius: 2px; }
.rx-legend-observe::before { background: var(--amber); }
.rx-legend-action::before { background: var(--teal); }
.rx-action-card {
  border-radius: 20px; padding: 18px; border: 1px solid var(--border); background: var(--card);
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.rx-action-card.active { border-color: rgba(0,184,160,.25); background: rgba(0,184,160,.03); box-shadow: 0 0 0 3px rgba(0,184,160,.06), 0 2px 8px rgba(0,0,0,0.03); }
.rx-action-hd { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.rx-action-ico { width: 46px; height: 46px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.rx-action-label { font-size: 10px; font-weight: 700; letter-spacing: .5px; margin-bottom: 3px; }
.rx-action-name { font-size: 15px; font-weight: 700; color: var(--ink); }
.rx-mech { font-size: 12px; color: var(--sub); line-height: 1.6; padding-left: 6px; border-left: 2px solid rgba(0,0,0,.08); }
.rx-taboo { font-size: 11px; color: var(--rose); margin-top: 4px; padding: 10px 12px; border-radius: 12px; background: rgba(245,101,101,.06); border: 1px solid rgba(245,101,101,.12); }
.rx-taboo::before { content: '⚠️ '; margin-right: 2px; }
.exp-feedback { border-radius: 20px; padding: 18px; background: rgba(212,160,23,.05); border: 1px solid rgba(212,160,23,.15); box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
.exp-feedback-title { font-size: 12px; font-weight: 700; color: var(--gold); letter-spacing: .5px; margin-bottom: 10px; }
.exp-feedback-item { display: flex; gap: 8px; font-size: 13px; color: var(--sub); padding: 7px 0; border-bottom: 1px dashed rgba(0,0,0,.05); line-height: 1.5; }
.exp-feedback-item:last-child { border-bottom: none; padding-bottom: 0; }
.exp-feedback-arrow { color: var(--teal); flex-shrink: 0; margin-top: 1px; }
.reg-cta {
  border-radius: 24px; padding: 28px 22px;
  background: linear-gradient(135deg, rgba(0,184,160,.08), rgba(76,110,245,.06));
  border: 1px solid rgba(0,184,160,.15); text-align: center;
  box-shadow: 0 4px 20px rgba(0,184,160,.08);
}
.reg-title { font-family: 'ZCOOL XiaoWei', serif; font-size: 22px; color: var(--ink); margin-bottom: 8px; }
.reg-sub { font-size: 13px; color: var(--sub); line-height: 1.6; margin-bottom: 18px; }
.reg-features { display: flex; justify-content: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.reg-feat { font-size: 12px; color: var(--teal); display: flex; align-items: center; gap: 4px; font-weight: 500; }
</style>
