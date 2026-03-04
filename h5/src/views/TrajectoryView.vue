<template>
  <div class="traj-page">
    <van-nav-bar title="我的行为轨迹" left-arrow @click-left="goBack()" />

    <van-loading v-if="loading" size="32" class="traj-loading" />

    <template v-else-if="data">
      <!-- 综合成长分 -->
      <div class="score-card">
        <div class="score-ring">
          <svg viewBox="0 0 80 80">
            <circle class="ring-bg" cx="40" cy="40" r="34" />
            <circle class="ring-fill" cx="40" cy="40" r="34"
              :stroke-dasharray="`${(data.trajectory_score / 100) * 213.6} 213.6`"
              :stroke="scoreColor"
            />
          </svg>
          <span class="score-num">{{ data.trajectory_score }}</span>
        </div>
        <div class="score-right">
          <div class="score-label">综合成长分</div>
          <div class="score-sub">{{ data.period_days }}天行为轨迹</div>
          <div class="qualify-badge" :class="{ passed: data.qualifies_for_sharer }">
            {{ data.qualifies_for_sharer ? '✓ 达到分享者门槛' : '继续积累中…' }}
          </div>
        </div>
      </div>

      <!-- 四维指标 -->
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-icon">🎯</div>
          <div class="metric-val" :style="{ color: adherenceColor }">{{ data.adherence_rate }}%</div>
          <div class="metric-label">依从率</div>
          <div class="metric-hint">{{ data.done_tasks }}/{{ data.total_tasks }} 次</div>
        </div>
        <div class="metric-item">
          <div class="metric-icon">📚</div>
          <div class="metric-val">{{ data.learning_hours }}h</div>
          <div class="metric-label">学习时长</div>
          <div class="metric-hint">近{{ data.period_days }}日</div>
        </div>
        <div class="metric-item">
          <div class="metric-icon">🔥</div>
          <div class="metric-val">{{ data.current_streak }}天</div>
          <div class="metric-label">当前连续</div>
          <div class="metric-hint">最长 {{ data.max_streak }}天</div>
        </div>
        <div class="metric-item">
          <div class="metric-icon">⚡</div>
          <div class="metric-val">
            {{ data.recovery_speed != null ? data.recovery_speed + '天' : '无中断' }}
          </div>
          <div class="metric-label">恢复速度</div>
          <div class="metric-hint">{{ data.interruptions }}次中断</div>
        </div>
      </div>

      <!-- 依从性趋势（周） -->
      <div class="section-card">
        <div class="section-title">依从性趋势</div>
        <div class="bar-chart" v-if="data.adherence_weekly?.length">
          <div v-for="w in data.adherence_weekly" :key="w.week_start" class="bar-col">
            <div class="bar-track">
              <div class="bar-fill" :style="{ height: w.rate + '%', background: barColor(w.rate) }"></div>
            </div>
            <div class="bar-label">{{ weekLabel(w.week_start) }}</div>
            <div class="bar-val">{{ w.rate }}%</div>
          </div>
        </div>
        <van-empty v-else description="暂无数据" image-size="60" />
      </div>

      <!-- 学习时长（周） -->
      <div class="section-card" v-if="data.learning_minutes_weekly?.length">
        <div class="section-title">学习时长（周）</div>
        <div class="bar-chart">
          <div v-for="w in data.learning_minutes_weekly" :key="w.week_start" class="bar-col">
            <div class="bar-track">
              <div class="bar-fill learn-bar" :style="{ height: Math.min(w.minutes / 120 * 100, 100) + '%' }"></div>
            </div>
            <div class="bar-label">{{ weekLabel(w.week_start) }}</div>
            <div class="bar-val">{{ w.minutes }}m</div>
          </div>
        </div>
      </div>

      <!-- 能力提升 -->
      <div class="section-card">
        <div class="section-title">评估能力提升</div>
        <div v-if="data.assessment_delta != null" class="delta-row">
          <div class="delta-item">
            <span class="delta-label">初始分</span>
            <span class="delta-val">{{ data.assessment_first }}</span>
          </div>
          <div class="delta-arrow">→</div>
          <div class="delta-item">
            <span class="delta-label">最新分</span>
            <span class="delta-val">{{ data.assessment_latest }}</span>
          </div>
          <div class="delta-change" :class="data.assessment_delta >= 0 ? 'up' : 'down'">
            {{ data.assessment_delta >= 0 ? '+' : '' }}{{ data.assessment_delta }}
          </div>
        </div>
        <div v-else class="delta-empty">
          <span>{{ data.assessment_count >= 1 ? '已完成 ' + data.assessment_count + ' 次评估，继续积累…' : '尚未完成评估' }}</span>
        </div>
      </div>

      <!-- 分享者资质提示 -->
      <div class="sharer-hint" @click="router.push('/become-sharer')">
        <div class="sharer-hint-inner">
          <span class="sharer-hint-icon">{{ data.qualifies_for_sharer ? '🌟' : '📈' }}</span>
          <div class="sharer-hint-text">
            <div class="sharer-hint-title">{{ data.qualifies_for_sharer ? '行为轨迹已达标！' : '距分享者更近一步' }}</div>
            <div class="sharer-hint-sub">{{ data.qualifies_for_sharer ? '你的成长历程可以激励更多人' : '保持依从率 ≥50%，连续打卡 ≥3天' }}</div>
          </div>
          <span class="sharer-hint-arrow">→</span>
        </div>
      </div>

    </template>

    <van-empty v-else description="暂无轨迹数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import { useGoBack } from '@/composables/useGoBack'

const { goBack } = useGoBack()
const router = useRouter()

const loading = ref(false)
const data = ref<any>(null)

const scoreColor = computed(() => {
  const s = data.value?.trajectory_score ?? 0
  if (s >= 80) return '#16a34a'
  if (s >= 60) return '#d97706'
  return '#6b7280'
})

const adherenceColor = computed(() => {
  const r = data.value?.adherence_rate ?? 0
  if (r >= 70) return '#16a34a'
  if (r >= 50) return '#d97706'
  return '#dc2626'
})

function barColor(rate: number) {
  if (rate >= 70) return '#16a34a'
  if (rate >= 50) return '#d97706'
  return '#ef4444'
}

function weekLabel(isoDate: string) {
  if (!isoDate) return ''
  const d = new Date(isoDate)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

async function loadTrajectory() {
  loading.value = true
  try {
    data.value = await api.get('/api/v1/learning/trajectory', { params: { days: 30 } })
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => loadTrajectory())
</script>

<style scoped>
.traj-page { min-height: 100vh; background: #f7f8fa; padding-bottom: 32px; }
.traj-loading { display: block; text-align: center; padding: 60px; }

/* score card */
.score-card {
  display: flex; align-items: center; gap: 20px;
  background: #fff; margin: 12px 16px; padding: 20px;
  border-radius: 16px; box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.score-ring { position: relative; width: 80px; height: 80px; flex-shrink: 0; }
.score-ring svg { transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: #f3f4f6; stroke-width: 6; }
.ring-fill { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dasharray 0.8s; }
.score-num {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 900; color: #111;
}
.score-right { flex: 1; }
.score-label { font-size: 16px; font-weight: 700; color: #111; margin-bottom: 2px; }
.score-sub { font-size: 12px; color: #9ca3af; margin-bottom: 8px; }
.qualify-badge {
  display: inline-block; font-size: 12px; font-weight: 600;
  padding: 4px 10px; border-radius: 12px;
  background: #f3f4f6; color: #6b7280;
}
.qualify-badge.passed { background: #dcfce7; color: #16a34a; }

/* metrics grid */
.metrics-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 0; margin: 0 16px 12px;
  background: #fff; border-radius: 14px; overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.metric-item {
  padding: 14px 8px; text-align: center;
  border-right: 1px solid #f3f4f6;
}
.metric-item:last-child { border-right: none; }
.metric-icon { font-size: 18px; margin-bottom: 4px; }
.metric-val { font-size: 17px; font-weight: 800; color: #111; }
.metric-label { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.metric-hint { font-size: 10px; color: #d1d5db; }

/* section card */
.section-card {
  background: #fff; margin: 0 16px 12px; padding: 16px;
  border-radius: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}
.section-title { font-size: 14px; font-weight: 700; color: #111; margin-bottom: 14px; }

/* bar chart */
.bar-chart { display: flex; gap: 8px; align-items: flex-end; height: 100px; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; }
.bar-track {
  flex: 1; width: 100%; background: #f3f4f6; border-radius: 4px;
  display: flex; align-items: flex-end; overflow: hidden;
}
.bar-fill { width: 100%; border-radius: 4px 4px 0 0; transition: height 0.6s; min-height: 2px; }
.learn-bar { background: linear-gradient(180deg, #6366f1, #818cf8); }
.bar-label { font-size: 10px; color: #9ca3af; }
.bar-val { font-size: 10px; color: #6b7280; font-weight: 600; }

/* delta */
.delta-row { display: flex; align-items: center; gap: 12px; justify-content: center; }
.delta-item { text-align: center; }
.delta-label { display: block; font-size: 11px; color: #9ca3af; margin-bottom: 4px; }
.delta-val { display: block; font-size: 22px; font-weight: 800; color: #111; }
.delta-arrow { font-size: 20px; color: #d1d5db; }
.delta-change {
  font-size: 20px; font-weight: 800; padding: 6px 12px;
  border-radius: 8px;
}
.delta-change.up { color: #16a34a; background: #dcfce7; }
.delta-change.down { color: #dc2626; background: #fee2e2; }
.delta-empty { text-align: center; font-size: 13px; color: #9ca3af; padding: 12px 0; }

/* sharer hint */
.sharer-hint { margin: 0 16px; cursor: pointer; }
.sharer-hint-inner {
  background: linear-gradient(135deg, #ede9fe, #dbeafe);
  border-radius: 14px; padding: 16px;
  display: flex; align-items: center; gap: 12px;
}
.sharer-hint-icon { font-size: 24px; flex-shrink: 0; }
.sharer-hint-text { flex: 1; }
.sharer-hint-title { font-size: 14px; font-weight: 700; color: #1e1b4b; }
.sharer-hint-sub { font-size: 12px; color: #6d28d9; margin-top: 2px; }
.sharer-hint-arrow { font-size: 18px; color: #6d28d9; font-weight: 700; }
</style>
