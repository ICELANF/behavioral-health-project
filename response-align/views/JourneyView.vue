<!--
  JourneyView.vue — 我的旅程
  S0-S5阶段时间线 + 双轨状态 + IES评分 + 主体性模式 + 转换历史
  对接: journeyApi.getStatus() + journeyApi.getTransitions()
-->

<template>
  <div class="journey-view">
    <div class="page-header">
      <h2 class="page-title">我的旅程</h2>
      <p class="page-desc">从觉察到自主，每一步都是成长</p>
    </div>

    <a-spin :spinning="loading" tip="加载中...">
      <template v-if="status">
        <!-- 当前阶段 Hero -->
        <div class="stage-hero" :style="{ borderLeft: `4px solid ${currentColor}` }">
          <div class="hero-main">
            <div class="hero-badge" :style="{ background: currentColor + '20', color: currentColor }">
              {{ currentStageLabel }}
            </div>
            <div class="hero-meta">
              已在此阶段 <strong>{{ status.days_in_stage }}</strong> 天
              <span class="meta-sep">·</span>
              进入时间 {{ formatDate(status.stage_entered_at) }}
            </div>
          </div>
          <div class="hero-scores">
            <div class="score-item">
              <div class="score-val">{{ status.trust_score?.toFixed(1) ?? '—' }}</div>
              <div class="score-lbl">信任分</div>
            </div>
            <div class="score-item">
              <div class="score-val">{{ status.agency_score?.toFixed(1) ?? '—' }}</div>
              <div class="score-lbl">主体性</div>
            </div>
            <div class="score-item">
              <div class="score-val">{{ status.ies_score?.toFixed(2) ?? '—' }}</div>
              <div class="score-lbl">IES综合</div>
            </div>
            <div class="score-item">
              <div class="score-val">{{ status.points_total ?? 0 }}</div>
              <div class="score-lbl">总积分</div>
            </div>
          </div>
        </div>

        <!-- 阶段时间线 -->
        <div class="card">
          <h3 class="card-title">阶段进度</h3>
          <div class="timeline">
            <div
              v-for="(s, i) in allStages" :key="s.key"
              class="tl-node"
              :class="{ done: i < curIdx, cur: i === curIdx, fut: i > curIdx }"
            >
              <div class="tl-bar" v-if="i > 0" :class="{ filled: i <= curIdx }"></div>
              <div class="tl-dot">
                <check-outlined v-if="i < curIdx" style="font-size:12px;" />
                <span v-else>{{ i }}</span>
              </div>
              <div class="tl-label">{{ s.label }}</div>
              <div class="tl-desc">{{ s.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 双轨 + 主体性模式 -->
        <div class="two-col">
          <div class="card">
            <h3 class="card-title">双轨晋级</h3>
            <div class="dt-list">
              <div class="dt-row">
                <span class="dt-icon">📊</span>
                <div><div class="dt-lbl">积分轨</div><div class="dt-val">{{ parseDualTrack('points') }}</div></div>
              </div>
              <div class="dt-row">
                <span class="dt-icon">🌱</span>
                <div><div class="dt-lbl">成长轨</div><div class="dt-val">{{ parseDualTrack('growth') }}</div></div>
              </div>
              <div class="dt-row">
                <span class="dt-icon">⚡</span>
                <div>
                  <div class="dt-lbl">综合</div>
                  <a-tag :color="dtColor">{{ status.dual_track_status || '—' }}</a-tag>
                </div>
              </div>
            </div>
          </div>
          <div class="card">
            <h3 class="card-title">主体性模式</h3>
            <div class="am-grid">
              <div
                v-for="m in amodes" :key="m.key"
                class="am-item" :class="{ on: status.agency_mode === m.key }"
              >
                <div style="font-size:22px;">{{ m.icon }}</div>
                <div class="am-name">{{ m.label }}</div>
                <div class="am-hint">{{ m.desc }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 转换历史 -->
        <div class="card" v-if="transitions.length">
          <h3 class="card-title">阶段转换记录</h3>
          <a-timeline>
            <a-timeline-item
              v-for="t in transitions" :key="t.id"
              :color="t.direction === 'forward' ? 'green' : 'red'"
            >
              <strong>{{ t.from_stage }}</strong> → <strong>{{ t.to_stage }}</strong>
              <span v-if="t.reason" style="color:#999;font-size:13px;">（{{ t.reason }}）</span>
              <div style="font-size:12px;color:#bbb;margin-top:2px;">{{ formatDate(t.created_at) }}</div>
            </a-timeline-item>
          </a-timeline>
        </div>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { journeyApi } from '@/api'
import { JourneyStage, STAGE_LABELS, STAGE_COLORS, AgencyMode, type JourneyStatus } from '@/types'
import { CheckOutlined } from '@ant-design/icons-vue'

const loading = ref(true)
const status = ref<JourneyStatus | null>(null)
const transitions = ref<any[]>([])

const allStages = [
  { key: JourneyStage.S0_AUTHORIZATION, label: 'S0 授权', desc: '知情同意' },
  { key: JourneyStage.S1_EXPLORATION, label: 'S1 探索', desc: '好奇探索' },
  { key: JourneyStage.S2_ENGAGEMENT, label: 'S2 投入', desc: '主动投入' },
  { key: JourneyStage.S3_PRACTICE, label: 'S3 实践', desc: '稳定实践' },
  { key: JourneyStage.S4_MASTERY, label: 'S4 精通', desc: '自如应对' },
  { key: JourneyStage.S5_GRADUATION, label: 'S5 毕业', desc: '自主管理' },
]
const amodes = [
  { key: AgencyMode.SCAFFOLDED, label: '脚手架', desc: 'AI主导引导', icon: '🏗️' },
  { key: AgencyMode.GUIDED, label: '引导式', desc: 'AI建议+选择', icon: '🧭' },
  { key: AgencyMode.COLLABORATIVE, label: '协作式', desc: '平等共建', icon: '🤝' },
  { key: AgencyMode.AUTONOMOUS, label: '自主式', desc: '用户主导', icon: '🦅' },
]

const curIdx = computed(() => status.value ? allStages.findIndex(s => s.key === status.value!.journey_stage) : 0)
const currentColor = computed(() => status.value ? STAGE_COLORS[status.value.journey_stage] || '#999' : '#999')
const currentStageLabel = computed(() => status.value ? STAGE_LABELS[status.value.journey_stage] || '' : '')
const dtColor = computed(() => {
  const s = status.value?.dual_track_status || ''
  return s.includes('eligible') || s.includes('ready') ? 'success' : s.includes('pending') ? 'warning' : 'default'
})

function parseDualTrack(track: string) {
  const raw = status.value?.dual_track_status
  if (!raw) return '—'
  if (typeof raw === 'object') return (raw as any)[`${track}_track`] || '—'
  return raw
}

function formatDate(iso: string) {
  return iso ? new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

onMounted(async () => {
  try {
    const [s, t] = await Promise.allSettled([
      journeyApi.getStatus(),
      journeyApi.getTransitions(),
    ])
    if (s.status === 'fulfilled') status.value = s.value
    if (t.status === 'fulfilled') transitions.value = t.value
  } catch {}
  loading.value = false
})
</script>

<style scoped>
.journey-view { max-width: 960px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Noto Serif SC', serif; font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #999; margin: 0; }
.card { background: #fff; border-radius: 14px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.04); border: 1px solid #f0f0f0; margin-bottom: 16px; }
.card-title { font-size: 16px; font-weight: 600; margin: 0 0 16px; }

.stage-hero { background: #fff; border-radius: 14px; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,.04); margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }
.hero-badge { display: inline-block; padding: 6px 18px; border-radius: 20px; font-weight: 700; font-size: 18px; margin-bottom: 8px; }
.hero-meta { font-size: 13px; color: #999; }
.hero-meta strong { color: #333; }
.meta-sep { margin: 0 8px; }
.hero-scores { display: flex; gap: 28px; }
.score-item { text-align: center; }
.score-val { font-size: 24px; font-weight: 700; color: #1a1a1a; }
.score-lbl { font-size: 11px; color: #999; margin-top: 2px; }

.timeline { display: flex; justify-content: space-between; position: relative; padding: 0 8px; }
.tl-node { display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; }
.tl-bar { position: absolute; top: 16px; right: 50%; left: -50%; height: 2px; background: #e5e7eb; z-index: 0; }
.tl-bar.filled { background: #4aa883; }
.tl-dot { width: 34px; height: 34px; border-radius: 50%; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: #9ca3af; z-index: 1; border: 2px solid #e5e7eb; }
.tl-node.done .tl-dot { background: #4aa883; border-color: #4aa883; color: #fff; }
.tl-node.cur .tl-dot { background: #fff; border-color: #4aa883; color: #4aa883; box-shadow: 0 0 0 4px rgba(74,168,131,.15); transform: scale(1.1); }
.tl-label { font-size: 12px; font-weight: 600; color: #666; margin-top: 10px; }
.tl-node.cur .tl-label { color: #1a1a1a; }
.tl-desc { font-size: 10px; color: #bbb; margin-top: 2px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.dt-list { display: flex; flex-direction: column; gap: 14px; }
.dt-row { display: flex; align-items: center; gap: 12px; }
.dt-icon { font-size: 20px; width: 40px; height: 40px; background: #f5f5f5; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.dt-lbl { font-size: 12px; color: #999; }
.dt-val { font-size: 14px; font-weight: 600; color: #333; }

.am-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.am-item { padding: 14px; border-radius: 12px; border: 1px solid #f0f0f0; text-align: center; opacity: .45; transition: all .2s; }
.am-item.on { border-color: #4aa883; background: #eef8f4; opacity: 1; box-shadow: 0 0 0 2px rgba(74,168,131,.1); }
.am-name { font-size: 13px; font-weight: 600; margin-top: 4px; }
.am-hint { font-size: 11px; color: #999; }

@media (max-width: 768px) {
  .stage-hero { flex-direction: column; align-items: flex-start; }
  .hero-scores { flex-wrap: wrap; gap: 16px; }
  .two-col { grid-template-columns: 1fr; }
}
</style>
