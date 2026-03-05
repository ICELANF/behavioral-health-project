<template>
  <div class="home">
    <!-- Header -->
    <div class="header">
      <div class="header__deco1" /><div class="header__deco2" />
      <div class="header__top">
        <div class="logo">
          <div class="logo__icon">👁️</div>
          <div class="logo__text">护眼行动</div>
        </div>
        <div class="header__date">{{ today }}</div>
      </div>
      <div class="header__greeting">你好，<span class="gold">{{ store.userName }}</span>！</div>
      <div class="header__sub">青少年科学使用视力 · 第{{ store.streak }}天</div>

      <div class="score-row">
        <div class="score-card">
          <ScoreRing :pct="store.score" />
          <div class="score-info">
            <div class="score-info__label">今日护眼评分</div>
            <div class="score-info__desc">{{ scoreDesc }}</div>
          </div>
        </div>
        <div class="streak-chip">
          <div class="streak-chip__num">{{ store.streak }}</div>
          <div class="streak-chip__label">连续<br/>打卡天</div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="content">
      <!-- Risk banner -->
      <div :class="['risk-banner', `risk-banner--${store.riskLevel}`]" class="fu">
        <div class="risk-icon">{{ riskInfo.icon }}</div>
        <div>
          <div class="risk-title">{{ riskInfo.title }}</div>
          <div class="risk-desc">{{ riskInfo.desc }}</div>
        </div>
      </div>

      <!-- Tasks card -->
      <div class="card fu fu-1">
        <div class="card-title">
          今日护眼打卡
          <span class="chip chip--teal">{{ store.doneCount }}/{{ store.tasks.length }} 完成</span>
        </div>
        <div
          v-for="t in store.tasks" :key="t.id"
          class="task-item" @click="store.toggleTask(t.id)"
        >
          <div class="task-item__icon" :style="{ background: t.iconBg }">{{ t.icon }}</div>
          <div class="task-item__body">
            <div class="task-item__name">{{ t.name }}</div>
            <div class="task-item__meta">{{ t.meta }}</div>
          </div>
          <div class="task-item__check" :class="{ done: t.done }">{{ t.done ? '✓' : '' }}</div>
        </div>
      </div>

      <!-- Weekly trend -->
      <div class="card fu fu-2">
        <div class="card-title">本周行为趋势</div>
        <div class="chart">
          <div v-for="(d, i) in weekData" :key="i" class="chart__col">
            <div class="chart__bar-wrap">
              <div class="chart__bar" :style="{
                height: Math.round((d.outdoor / 180) * 60) + 'px',
                background: d.done ? 'var(--teal)' : 'var(--border)'
              }" />
            </div>
            <div class="chart__day" :class="{ today: i === 6 }">{{ d.day }}</div>
          </div>
        </div>
      </div>

      <!-- Achievements -->
      <div class="card fu fu-3">
        <div class="card-title">🏆 护眼成就</div>
        <div class="badges">
          <span v-for="b in unlockedBadges" :key="b" class="badge badge--active">{{ b }}</span>
          <span class="badge badge--locked">🔒 连续30天</span>
        </div>
      </div>
    </div>

    <!-- Spacer for tab bar -->
    <div style="height: 70px" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useVisionStore } from '@/stores/vision'
import ScoreRing from '@/components/ScoreRing.vue'

const store = useVisionStore()

const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })

const scoreDesc = computed(() => {
  if (store.score >= 80) return '表现优秀 🌟'
  if (store.score >= 60) return '表现良好 👍'
  return '继续加油 💪'
})

const riskInfo = computed(() => ({
  normal: { icon: '🟢', title: '今日用眼状况良好', desc: `已完成护眼行为 ${store.doneCount}/${store.tasks.length}，继续保持！` },
  watch:  { icon: '🟡', title: '还有几项未完成', desc: '屏幕时间和距离检查别忘了哦。' },
  alert:  { icon: '🔴', title: '今日护眼任务完成较少', desc: '建议先完成眼保健操和户外活动。' },
}[store.riskLevel]))

const weekData = [
  { day: '周一', outdoor: 110, done: true },
  { day: '周二', outdoor: 130, done: true },
  { day: '周三', outdoor: 90,  done: false },
  { day: '周四', outdoor: 140, done: true },
  { day: '周五', outdoor: 120, done: true },
  { day: '周六', outdoor: 180, done: true },
  { day: '今天', outdoor: 90,  done: false },
]

const unlockedBadges = ['连续7天✓', '户外达人', '习惯养成者']
</script>

<style scoped>
.header {
  background: var(--grad-header);
  padding: 20px 20px 28px;
  position: relative;
  overflow: hidden;
}
.header__deco1 {
  position: absolute; top: -30px; right: -30px;
  width: 120px; height: 120px; border-radius: 50%;
  background: rgba(255,255,255,.08);
}
.header__deco2 {
  position: absolute; bottom: -20px; left: 60px;
  width: 80px; height: 80px; border-radius: 50%;
  background: rgba(255,255,255,.06);
}
.header__top {
  display: flex; justify-content: space-between;
  align-items: center; margin-bottom: 16px; position: relative; z-index: 1;
}
.logo { display: flex; align-items: center; gap: 8px; }
.logo__icon {
  width: 32px; height: 32px; background: rgba(255,255,255,.2);
  border-radius: 10px; display: flex; align-items: center;
  justify-content: center; font-size: 18px;
}
.logo__text { font-weight: 900; font-size: 16px; color: white; letter-spacing: -.3px; }
.header__date { font-size: 12px; color: rgba(255,255,255,.75); }
.header__greeting { font-size: 22px; font-weight: 700; color: white; line-height: 1.3; position: relative; z-index: 1; }
.gold { color: var(--gold); }
.header__sub { font-size: 13px; color: rgba(255,255,255,.8); position: relative; z-index: 1; }

.score-row {
  display: flex; gap: 12px; margin-top: 16px; position: relative; z-index: 1;
}
.score-card {
  background: rgba(255,255,255,.15); border-radius: 16px;
  padding: 12px 14px; display: flex; align-items: center; gap: 12px; flex: 1;
}
.score-info__label { font-size: 11px; color: rgba(255,255,255,.75); }
.score-info__desc { font-size: 13px; font-weight: 600; color: white; margin-top: 2px; }
.streak-chip {
  background: rgba(255,255,255,.15); border-radius: 16px;
  padding: 12px 14px; display: flex; flex-direction: column;
  justify-content: center; align-items: center; gap: 4px;
}
.streak-chip__num { font-weight: 900; font-size: 24px; color: var(--gold); }
.streak-chip__label { font-size: 11px; color: rgba(255,255,255,.75); text-align: center; }

.content { padding: 16px; display: flex; flex-direction: column; gap: 12px; }

.risk-icon { font-size: 28px; flex-shrink: 0; }
.risk-title { font-size: 13px; font-weight: 700; color: var(--ink); }
.risk-desc { font-size: 12px; color: var(--sub); margin-top: 2px; line-height: 1.4; }

.task-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #F2F7F6;
  cursor: pointer; transition: all .15s;
}
.task-item:last-child { border-bottom: none; }
.task-item:active { transform: scale(.98); }
.task-item__icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.task-item__body { flex: 1; }
.task-item__name { font-size: 13px; font-weight: 600; color: var(--ink); }
.task-item__meta { font-size: 11px; color: var(--sub); margin-top: 2px; }
.task-item__check {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid var(--border); display: flex;
  align-items: center; justify-content: center;
  font-size: 13px; transition: all .2s; flex-shrink: 0;
}
.task-item__check.done { background: var(--teal); border-color: var(--teal); color: white; }

.chart { display: flex; align-items: flex-end; gap: 8px; height: 80px; padding-top: 8px; }
.chart__col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.chart__bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; }
.chart__bar { width: 100%; border-radius: 6px 6px 0 0; transition: height .5s; min-height: 4px; }
.chart__day { font-size: 10px; color: var(--sub); }
.chart__day.today { color: var(--teal); font-weight: 700; }

.badges { display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
  font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 20px;
}
.badge--active { background: var(--teal-l); color: var(--teal); }
.badge--locked { background: #F5F5F5; color: var(--sub); }
</style>
