<template>
  <view class="traj-page">
    <!-- 自定义导航 —— 标题随角色变化 -->
    <!--
      NOTE: 本页角色感知双模式
        grower  → 标题"行为轨迹"，深蓝绿渐变，显示分享者资质检查
        sharer  → 标题"教练之道"，紫琥珀渐变，顶部显示四维晋级进度，行为数据作为"行为证据"
      路由保持不变：/pages/trajectory/index
      首页快捷入口：grower="行为轨迹"，sharer="教练之道"（相同URL，不同标签）
    -->
    <view class="traj-nav" :class="isSharer ? 'traj-nav--sharer' : ''">
      <view class="traj-nav-back" @tap="goBack">‹</view>
      <text class="traj-nav-title">{{ isSharer ? '教练之道' : '行为轨迹' }}</text>
    </view>

    <scroll-view scroll-y class="traj-scroll" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-if="loading" class="traj-loading"><text>加载中…</text></view>

      <template v-else>

        <!-- ════════════════════════════════
             SHARER 专属：四维晋级进度
             仅分享者可见，替换原"分享者资质"banner
             ════════════════════════════════ -->
        <template v-if="isSharer">

          <!-- Hero 卡：距离教练还差多少 -->
          <view class="coach-hero" :class="promoReady ? 'coach-hero--ready' : ''">
            <view class="coach-hero-left">
              <text class="coach-hero-emoji">{{ promoReady ? '🎉' : '🎯' }}</text>
              <view>
                <text class="coach-hero-title">{{ promoReady ? '你已满足晋级条件！' : '教练之道进度' }}</text>
                <text class="coach-hero-sub">{{ promoReady ? '可申请晋级为行为健康教练' : `已完成 ${dimDone}/4 个维度` }}</text>
              </view>
            </view>
            <view v-if="promoReady" class="coach-hero-btn" @tap="goApply">立即申请 ›</view>
          </view>

          <!-- 四维进度卡 -->
          <view class="dim-list">

            <!-- 维度1：积分 -->
            <view class="dim-card">
              <view class="dim-card-head">
                <text class="dim-icon">📊</text>
                <text class="dim-name">积分</text>
                <view class="dim-badge" :class="pointsDone ? 'dim-badge--ok' : 'dim-badge--no'">
                  {{ pointsDone ? '✓ 已满足' : '未满足' }}
                </view>
              </view>
              <view class="dim-rows">
                <view class="dim-row">
                  <text class="dim-row-label">成长积分</text>
                  <text class="dim-row-val">{{ promo.growth_points ?? '—' }} / 800</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--green" :style="{ width: barPct(promo.growth_points, 800) }"></view></view>
                </view>
                <view class="dim-row">
                  <text class="dim-row-label">贡献积分</text>
                  <text class="dim-row-val">{{ promo.contribution_points ?? '—' }} / 100</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--blue" :style="{ width: barPct(promo.contribution_points, 100) }"></view></view>
                </view>
                <view class="dim-row">
                  <text class="dim-row-label">影响力积分</text>
                  <text class="dim-row-val">{{ promo.influence_points ?? '—' }} / 50</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--purple" :style="{ width: barPct(promo.influence_points, 50) }"></view></view>
                </view>
              </view>
            </view>

            <!-- 维度2：学分 -->
            <view class="dim-card">
              <view class="dim-card-head">
                <text class="dim-icon">🎓</text>
                <text class="dim-name">学分</text>
                <view class="dim-badge" :class="creditsDone ? 'dim-badge--ok' : 'dim-badge--no'">
                  {{ creditsDone ? '✓ 已满足' : '未满足' }}
                </view>
              </view>
              <view class="dim-rows">
                <view class="dim-row">
                  <text class="dim-row-label">总学分</text>
                  <text class="dim-row-val">{{ credits.total_credits ?? '—' }} / 800</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--blue" :style="{ width: barPct(credits.total_credits, 800) }"></view></view>
                </view>
              </view>
            </view>

            <!-- 维度3：同道者 -->
            <view class="dim-card">
              <view class="dim-card-head">
                <text class="dim-icon">👥</text>
                <text class="dim-name">同道者</text>
                <view class="dim-badge" :class="companionsDone ? 'dim-badge--ok' : 'dim-badge--no'">
                  {{ companionsDone ? '✓ 已满足' : '未满足' }}
                </view>
              </view>
              <view class="dim-rows">
                <view class="dim-row">
                  <text class="dim-row-label">已毕业同道者</text>
                  <text class="dim-row-val">{{ companionStats.graduated_count ?? 0 }} / 4 人</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--green" :style="{ width: barPct(companionStats.graduated_count, 4) }"></view></view>
                </view>
                <view class="dim-row">
                  <text class="dim-row-label">带教质量评分</text>
                  <text class="dim-row-val">{{ fmtScore(companionStats.avg_quality) }} / 3.5</text>
                  <view class="dim-bar-bg"><view class="dim-bar-fill dim-bar--orange" :style="{ width: barPct(companionStats.avg_quality, 3.5) }"></view></view>
                </view>
              </view>
              <text class="dim-tip">💡 邀请成长者成为同道者，持续陪伴直至他们晋级为分享者即算"毕业"</text>
            </view>

            <!-- 维度4：实践（人工审核） -->
            <view class="dim-card dim-card--manual">
              <view class="dim-card-head">
                <text class="dim-icon">📝</text>
                <text class="dim-name">实践</text>
                <view class="dim-badge dim-badge--manual">人工审核</view>
              </view>
              <view class="dim-rows">
                <view class="dim-row dim-row--manual">
                  <text class="dim-row-label">培训时长</text>
                  <text class="dim-row-hint">≥ 40 小时</text>
                </view>
                <view class="dim-row dim-row--manual">
                  <text class="dim-row-label">带教陪伴时长</text>
                  <text class="dim-row-hint">≥ 50 小时</text>
                </view>
                <view class="dim-row dim-row--manual">
                  <text class="dim-row-label">案例数</text>
                  <text class="dim-row-hint">≥ 10 份</text>
                </view>
                <view class="dim-row dim-row--manual">
                  <text class="dim-row-label">伦理评估</text>
                  <text class="dim-row-hint">100% 通过</text>
                </view>
              </view>
              <text class="dim-tip">📌 认证考试（理论+技能+综合三维）由督导评定，申请晋级后安排</text>
            </view>

            <!-- 下一步行动卡 -->
            <view class="next-card">
              <text class="next-title">🚀 当前最优先行动</text>
              <view v-for="(a, i) in sharerAdvices" :key="i" class="next-item">
                <text class="next-dot">›</text>
                <text class="next-text">{{ a }}</text>
              </view>
            </view>

          </view>

          <!-- 分隔线 + 说明 -->
          <view class="evidence-divider">
            <view class="evidence-line"></view>
            <text class="evidence-label">以下行为数据是教练资质审核的直接证据</text>
            <view class="evidence-line"></view>
          </view>

        </template>

        <!-- ════════════════════════════════
             GROWER 专属：分享者资质提示
             ════════════════════════════════ -->
        <template v-else>
          <view v-if="traj.qualifies_for_sharer" class="qualify-banner qualify-banner--yes" @tap="goBecome">
            <text class="qualify-icon">🌟</text>
            <view class="qualify-body">
              <text class="qualify-title">你已达到分享者资质！</text>
              <text class="qualify-sub">点击申请成为分享者，照亮更多同道者 →</text>
            </view>
          </view>
          <view v-else class="qualify-banner qualify-banner--no">
            <text class="qualify-icon">💪</text>
            <view class="qualify-body">
              <text class="qualify-title">继续积累，距分享者资质还差一步</text>
              <text class="qualify-sub">需: 成长分≥60 · 依从率≥50% · 连续打卡≥3天</text>
            </view>
          </view>
        </template>

        <!-- ════════════════════════════════
             共用：综合评分环
             ════════════════════════════════ -->
        <view class="score-card" :class="isSharer ? 'score-card--sharer' : ''">
          <view class="score-ring-wrap">
            <view class="score-ring">
              <text class="score-num">{{ traj.trajectory_score || 0 }}</text>
              <text class="score-label">综合成长分</text>
            </view>
          </view>
          <view class="score-meta">
            <view class="score-meta-row">
              <text class="score-meta-label">{{ isSharer ? '行为证据周期' : '评估日期' }}</text>
              <text class="score-meta-val">近 {{ traj.days || 30 }} 天</text>
            </view>
            <view class="score-meta-row">
              <text class="score-meta-label">评估项目数</text>
              <text class="score-meta-val">{{ totalMetrics }}</text>
            </view>
          </view>
        </view>

        <!-- 4 指标卡 -->
        <view class="metric-grid">
          <view class="metric-card metric-card--green">
            <text class="metric-icon">✅</text>
            <text class="metric-val">{{ pct(traj.adherence_rate) }}</text>
            <text class="metric-key">依从率</text>
            <view class="metric-bar-bg"><view class="metric-bar-fill metric-bar-fill--green" :style="{ width: pct(traj.adherence_rate) }"></view></view>
          </view>
          <view class="metric-card metric-card--blue">
            <text class="metric-icon">📚</text>
            <text class="metric-val">{{ fmtHours(traj.learning_hours) }}</text>
            <text class="metric-key">学习时长</text>
            <view class="metric-bar-bg"><view class="metric-bar-fill metric-bar-fill--blue" :style="{ width: learningBarPct }"></view></view>
          </view>
          <view class="metric-card metric-card--orange">
            <text class="metric-icon">🔥</text>
            <text class="metric-val">{{ traj.current_streak || 0 }} 天</text>
            <text class="metric-key">当前连续</text>
            <text class="metric-sub">最高 {{ traj.max_streak || 0 }} 天</text>
          </view>
          <view class="metric-card metric-card--purple">
            <text class="metric-icon">⚡</text>
            <text class="metric-val">{{ fmtRecovery(traj.recovery_speed) }}</text>
            <text class="metric-key">恢复速度</text>
            <text class="metric-sub">中断后重返</text>
          </view>
        </view>

        <!-- 每周依从率 -->
        <view class="chart-card" v-if="adherenceWeekly.length">
          <text class="chart-title">📊 近周依从率趋势</text>
          <view class="bar-chart">
            <view v-for="(d, i) in adherenceWeekly" :key="i" class="bar-col">
              <view class="bar-wrap">
                <view class="bar-fill bar-fill--green" :style="{ height: barH(d.adherence_rate) }"></view>
              </view>
              <text class="bar-label">{{ d.week_label || ('W'+(i+1)) }}</text>
            </view>
          </view>
        </view>

        <!-- 评估提升 -->
        <view class="assess-card" v-if="traj.assessment_delta != null">
          <text class="assess-title">📋 评估改善</text>
          <view class="assess-row">
            <view class="assess-item">
              <text class="assess-num">{{ traj.first_score ?? '—' }}</text>
              <text class="assess-lbl">首次评分</text>
            </view>
            <text class="assess-arrow">→</text>
            <view class="assess-item">
              <text class="assess-num assess-num--latest">{{ traj.latest_score ?? '—' }}</text>
              <text class="assess-lbl">最新评分</text>
            </view>
            <view class="assess-delta" :class="traj.assessment_delta >= 0 ? 'delta--pos' : 'delta--neg'">
              <text>{{ traj.assessment_delta >= 0 ? '+' : '' }}{{ traj.assessment_delta }}</text>
            </view>
          </view>
        </view>

        <!-- 行动建议 —— grower版；sharer用顶部"当前最优先行动"替代 -->
        <view class="advice-card" v-if="!isSharer && growerAdvices.length">
          <text class="advice-title">💡 成长建议</text>
          <view v-for="(a, i) in growerAdvices" :key="i" class="advice-item">
            <text class="advice-dot">·</text>
            <text class="advice-text">{{ a }}</text>
          </view>
        </view>

        <!-- sharer 底部申请按钮 -->
        <view v-if="isSharer" class="apply-footer">
          <view class="apply-btn" :class="promoReady ? 'apply-btn--ready' : 'apply-btn--grey'" @tap="goApply">
            {{ promoReady ? '🎉 申请晋级为教练' : '查看晋级申请' }}
          </view>
          <text class="apply-hint">积累时长约10个月 · 预估全流程</text>
        </view>

        <view style="height:120rpx;"></view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

// ── 类型 ──────────────────────────────────────────────────
interface TrajData {
  days?: number
  trajectory_score?: number
  adherence_rate?: number
  adherence_weekly?: { week_label?: string; adherence_rate: number }[]
  learning_hours?: number
  current_streak?: number
  max_streak?: number
  recovery_speed?: number
  assessment_delta?: number
  first_score?: number
  latest_score?: number
  qualifies_for_sharer?: boolean
  total_tasks?: number
  completed_tasks?: number
  total_learning_days?: number
}

// ── 角色检测 ──────────────────────────────────────────────
// NOTE: role 来自 localStorage user_info，由登录时写入，分享者 role='sharer'
function detectRole(): string {
  try {
    const s = uni.getStorageSync('user_info')
    const u = s ? (typeof s === 'string' ? JSON.parse(s) : s) : null
    return (u?.role || '').toLowerCase()
  } catch { return '' }
}
const isSharer = detectRole() === 'sharer'

// ── 状态 ──────────────────────────────────────────────────
const loading    = ref(true)
const refreshing = ref(false)
const traj       = ref<TrajData>({})

// sharer 专属
const promo          = ref<Record<string, number>>({})   // 来自 /promotion/check 或 /promotion/status
const credits        = ref<{ total_credits?: number }>({})
const companionStats = ref<{ graduated_count?: number; avg_quality?: number }>({})

// ── 计算属性 ──────────────────────────────────────────────
const adherenceWeekly = computed(() => traj.value.adherence_weekly || [])

const totalMetrics = computed(() => {
  let n = 0
  if (traj.value.adherence_rate != null) n++
  if (traj.value.learning_hours != null) n++
  if (traj.value.current_streak != null) n++
  if (traj.value.assessment_delta != null) n++
  return n
})

const learningBarPct = computed(() => {
  const h = traj.value.learning_hours || 0
  return Math.min(100, (h / 20) * 100).toFixed(0) + '%'
})

// sharer 四维达标判断（阈值来自 promotion_rules.json L2→L3）
const pointsDone     = computed(() =>
  (promo.value.growth_points ?? 0) >= 800 &&
  (promo.value.contribution_points ?? 0) >= 100 &&
  (promo.value.influence_points ?? 0) >= 50
)
const creditsDone    = computed(() => (credits.value.total_credits ?? 0) >= 800)
const companionsDone = computed(() =>
  (companionStats.value.graduated_count ?? 0) >= 4 &&
  (companionStats.value.avg_quality ?? 0) >= 3.5
)
const promoReady     = computed(() => pointsDone.value && creditsDone.value && companionsDone.value)
const dimDone        = computed(() => [pointsDone.value, creditsDone.value, companionsDone.value, false].filter(Boolean).length)

// sharer 最优先行动建议（动态生成）
const sharerAdvices = computed(() => {
  const list: string[] = []
  const p = promo.value
  const c = credits.value
  const cs = companionStats.value

  if ((p.growth_points ?? 0) < 800) {
    const gap = 800 - (p.growth_points ?? 0)
    list.push(`成长积分还差 ${gap} 分，坚持每日打卡+完成学习任务即可积累`)
  }
  if ((p.contribution_points ?? 0) < 100) {
    const gap = 100 - (p.contribution_points ?? 0)
    list.push(`贡献积分还差 ${gap} 分，多投稿经验文章或带教同道者可加速`)
  }
  if ((p.influence_points ?? 0) < 50) {
    list.push('影响力积分不足，鼓励同道者分享你的内容可提升影响力')
  }
  if ((c.total_credits ?? 0) < 800) {
    const gap = 800 - (c.total_credits ?? 0)
    list.push(`学分还差 ${gap} 分，优先完成必修模块 M1→M4`)
  }
  if ((cs.graduated_count ?? 0) < 4) {
    const gap = 4 - (cs.graduated_count ?? 0)
    list.push(`还需带教 ${gap} 位成长者直至他们晋级为分享者（算作"毕业"）`)
  }
  if ((cs.avg_quality ?? 0) < 3.5 && (cs.graduated_count ?? 0) > 0) {
    list.push('提升带教质量评分：每周至少与同道者互动一次，质量重于数量')
  }
  if (list.length === 0) {
    list.push('三项自动条件已满足！提交申请后等待督导安排认证考试')
  }
  return list
})

// grower 建议（原有逻辑）
const growerAdvices = computed(() => {
  const list: string[] = []
  const t = traj.value
  if (!t.trajectory_score) return list
  if ((t.adherence_rate || 0) < 0.5)  list.push('依从率不足50%，尝试把任务分解成更小步骤')
  if ((t.current_streak || 0) < 3)    list.push('连续打卡天数不足3天，每日睡前设提醒更容易坚持')
  if ((t.learning_hours || 0) < 5)    list.push('近期学习时长较少，建议每天利用碎片时间学习15分钟')
  if ((t.recovery_speed || 0) > 3)    list.push('中断后恢复较慢，中断时告知教练获得支持')
  if (list.length === 0) list.push('各项指标良好！继续保持当前节奏，向分享者目标迈进')
  return list
})

// ── 工具函数 ──────────────────────────────────────────────
function pct(val?: number) {
  if (val == null) return '—'
  return Math.round((val || 0) * 100) + '%'
}
function fmtHours(h?: number) {
  if (h == null) return '—'
  if (h < 1) return Math.round(h * 60) + 'min'
  return h.toFixed(1) + 'h'
}
function fmtRecovery(days?: number) {
  if (days == null) return '—'
  if (days === 0) return '从不中断'
  return days.toFixed(1) + '天'
}
function fmtScore(v?: number | null) {
  if (v == null) return '—'
  return v.toFixed(1)
}
function barH(rate: number) {
  return Math.max(4, Math.round((rate || 0) * 100)) + 'rpx'
}
function barPct(val: number | undefined | null, max: number): string {
  if (val == null) return '0%'
  return Math.min(100, Math.round((val / max) * 100)) + '%'
}

// ── 数据加载 ──────────────────────────────────────────────
async function load() {
  try {
    if (isSharer) {
      // 分享者并行加载：行为轨迹 + 晋级进度 + 学分 + 同道者统计
      const [trajRes, promoRes, creditsRes, compRes] = await Promise.allSettled([
        http<TrajData>('/api/v1/learning/trajectory?days=30'),
        http<any>('/api/v1/promotion/check'),
        http<any>('/api/v1/learning/credits'),
        http<any>('/api/v1/companions/stats'),
      ])
      if (trajRes.status === 'fulfilled')    traj.value    = trajRes.value as TrajData
      if (promoRes.status === 'fulfilled') {
        // promotion/check 返回结构因后端版本不同，做兼容处理
        const d = promoRes.value as any
        promo.value = {
          growth_points:       d.growth_points       ?? d.points?.growth       ?? 0,
          contribution_points: d.contribution_points ?? d.points?.contribution ?? 0,
          influence_points:    d.influence_points    ?? d.points?.influence    ?? 0,
        }
      }
      if (creditsRes.status === 'fulfilled') credits.value        = creditsRes.value as any
      if (compRes.status === 'fulfilled')    companionStats.value = compRes.value   as any
    } else {
      // 成长者只加载轨迹
      const res = await http<TrajData>('/api/v1/learning/trajectory?days=30')
      traj.value = res as TrajData
    }
  } catch { /* graceful fallback */ }
  finally {
    loading.value    = false
    refreshing.value = false
  }
}

function onRefresh() { refreshing.value = true; load() }

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.reLaunch({ url: '/home/index' })
}
function goBecome() { uni.navigateTo({ url: '/become-sharer/index' }) }
function goApply()  { uni.navigateTo({ url: '/journey/promotion' }) }

onMounted(() => load())
</script>

<style scoped>
.traj-page { min-height: 100vh; background: #f5f6fa; }

/* ── 导航栏 ── */
.traj-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 88rpx; padding-top: env(safe-area-inset-top);
  background: linear-gradient(135deg, #1e3a5f 0%, #2d6a4f 100%);
  display: flex; align-items: center; padding-left: 28rpx;
}
/* 分享者：换用紫琥珀色调（"道"的暖意 vs "轨迹"的冷峻） */
.traj-nav--sharer {
  background: linear-gradient(135deg, #4c1d95 0%, #92400e 100%);
}
.traj-nav-back { color: #fff; font-size: 48rpx; padding-right: 16rpx; line-height: 1; }
.traj-nav-title { color: #fff; font-size: 32rpx; font-weight: 700; }
.traj-scroll { position: fixed; top: calc(88rpx + env(safe-area-inset-top)); bottom: 0; left: 0; right: 0; }
.traj-loading { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }

/* ── 教练之道 Hero 卡 ── */
.coach-hero {
  background: linear-gradient(135deg, #4c1d95 0%, #92400e 100%);
  padding: 40rpx 32rpx 32rpx;
  display: flex; align-items: center; justify-content: space-between; gap: 16rpx;
}
.coach-hero--ready {
  background: linear-gradient(135deg, #065f46 0%, #1d4ed8 100%);
}
.coach-hero-left { display: flex; align-items: center; gap: 20rpx; flex: 1; }
.coach-hero-emoji { font-size: 60rpx; flex-shrink: 0; }
.coach-hero-title { display: block; font-size: 30rpx; font-weight: 700; color: #fff; }
.coach-hero-sub   { display: block; font-size: 22rpx; color: rgba(255,255,255,0.8); margin-top: 4rpx; }
.coach-hero-btn {
  background: rgba(255,255,255,0.2); color: #fff; padding: 14rpx 24rpx;
  border-radius: 40rpx; font-size: 24rpx; font-weight: 600; white-space: nowrap; flex-shrink: 0;
}

/* ── 四维卡列表 ── */
.dim-list { padding: 16rpx 24rpx 0; }
.dim-card {
  background: #fff; border-radius: 20rpx; padding: 24rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.dim-card--manual { background: #fafafa; }
.dim-card-head { display: flex; align-items: center; gap: 12rpx; margin-bottom: 16rpx; }
.dim-icon { font-size: 36rpx; }
.dim-name { flex: 1; font-size: 28rpx; font-weight: 700; color: #1a1a2e; }
.dim-badge { padding: 4rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; font-weight: 600; }
.dim-badge--ok     { background: #dcfce7; color: #16a34a; }
.dim-badge--no     { background: #f3f4f6; color: #6b7280; }
.dim-badge--manual { background: #fef3c7; color: #92400e; }

.dim-rows { display: flex; flex-direction: column; gap: 14rpx; }
.dim-row { }
.dim-row-label { font-size: 22rpx; color: #6b7280; display: block; margin-bottom: 4rpx; }
.dim-row-val   { font-size: 24rpx; font-weight: 600; color: #1a1a2e; display: block; margin-bottom: 6rpx; }
.dim-row--manual { display: flex; align-items: center; justify-content: space-between; padding: 10rpx 0; border-bottom: 1rpx solid #f3f4f6; }
.dim-row--manual .dim-row-label { margin-bottom: 0; }
.dim-row-hint { font-size: 22rpx; color: #92400e; font-weight: 500; }

.dim-bar-bg   { height: 8rpx; background: #f3f4f6; border-radius: 4rpx; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 4rpx; }
.dim-bar--green  { background: #16a34a; }
.dim-bar--blue   { background: #1565c0; }
.dim-bar--orange { background: #d97706; }
.dim-bar--purple { background: #7c3aed; }

.dim-tip {
  display: block; font-size: 20rpx; color: #9ca3af;
  margin-top: 14rpx; line-height: 1.6;
}

/* ── 最优先行动卡 ── */
.next-card {
  background: linear-gradient(135deg, #ede9fe, #fef3c7);
  border-radius: 20rpx; padding: 24rpx; margin-bottom: 16rpx;
}
.next-title { font-size: 26rpx; font-weight: 700; color: #4c1d95; display: block; margin-bottom: 14rpx; }
.next-item  { display: flex; gap: 8rpx; margin-bottom: 10rpx; }
.next-dot   { color: #7c3aed; font-size: 28rpx; flex-shrink: 0; line-height: 1.5; }
.next-text  { font-size: 24rpx; color: #374151; line-height: 1.6; }

/* ── 证据分割线 ── */
.evidence-divider {
  display: flex; align-items: center; gap: 12rpx;
  padding: 8rpx 24rpx 16rpx;
}
.evidence-line  { flex: 1; height: 1rpx; background: #e5e7eb; }
.evidence-label { font-size: 20rpx; color: #9ca3af; white-space: nowrap; }

/* ── 评分卡（共用） ── */
.score-card {
  background: linear-gradient(135deg, #1e3a5f 0%, #2d6a4f 100%);
  padding: 40rpx 32rpx 32rpx;
  display: flex; align-items: center; gap: 40rpx;
}
/* sharer 进入时评分卡缩小（四维卡已是主角） */
.score-card--sharer {
  background: linear-gradient(135deg, #374151 0%, #4b5563 100%);
  padding: 28rpx 32rpx;
}
.score-ring-wrap { flex-shrink: 0; }
.score-ring {
  width: 160rpx; height: 160rpx; border-radius: 50%;
  border: 8rpx solid rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.1);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-num   { font-size: 56rpx; font-weight: 900; color: #fff; line-height: 1; }
.score-label { font-size: 20rpx; color: rgba(255,255,255,0.8); margin-top: 4rpx; }
.score-meta  { flex: 1; }
.score-meta-row  { display: flex; justify-content: space-between; margin-bottom: 12rpx; }
.score-meta-label { font-size: 24rpx; color: rgba(255,255,255,0.7); }
.score-meta-val   { font-size: 24rpx; color: #fff; font-weight: 600; }

/* ── 资质横幅（grower） ── */
.qualify-banner {
  margin: 20rpx 24rpx 0;
  padding: 20rpx 24rpx;
  border-radius: 20rpx;
  display: flex; align-items: center; gap: 16rpx;
}
.qualify-banner--yes { background: linear-gradient(135deg, #dcfce7, #bbf7d0); }
.qualify-banner--no  { background: #f9fafb; border: 2rpx solid #e5e7eb; }
.qualify-icon  { font-size: 44rpx; flex-shrink: 0; }
.qualify-body  { flex: 1; }
.qualify-title { font-size: 26rpx; font-weight: 700; color: #111; display: block; }
.qualify-sub   { font-size: 22rpx; color: #6b7280; display: block; margin-top: 4rpx; }

/* ── 4 指标卡（共用） ── */
.metric-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16rpx; margin: 20rpx 24rpx 0;
}
.metric-card {
  background: #fff; border-radius: 20rpx; padding: 24rpx 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.metric-icon { font-size: 36rpx; display: block; }
.metric-val  { font-size: 44rpx; font-weight: 900; display: block; margin: 8rpx 0 2rpx; }
.metric-key  { font-size: 22rpx; color: #6b7280; display: block; }
.metric-sub  { font-size: 20rpx; color: #9ca3af; display: block; margin-top: 4rpx; }
.metric-card--green  .metric-val { color: #16a34a; }
.metric-card--blue   .metric-val { color: #1565c0; }
.metric-card--orange .metric-val { color: #d97706; }
.metric-card--purple .metric-val { color: #7c3aed; }
.metric-bar-bg   { height: 8rpx; background: #f3f4f6; border-radius: 4rpx; margin-top: 12rpx; overflow: hidden; }
.metric-bar-fill { height: 100%; border-radius: 4rpx; }
.metric-bar-fill--green { background: #16a34a; }
.metric-bar-fill--blue  { background: #1565c0; }

/* ── 柱状图（共用） ── */
.chart-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.chart-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 24rpx; }
.bar-chart   { display: flex; align-items: flex-end; gap: 12rpx; height: 120rpx; }
.bar-col     { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8rpx; }
.bar-wrap    { flex: 1; display: flex; align-items: flex-end; width: 100%; }
.bar-fill    { width: 100%; border-radius: 6rpx 6rpx 0 0; min-height: 4rpx; }
.bar-fill--green { background: linear-gradient(180deg, #86efac, #16a34a); }
.bar-label   { font-size: 18rpx; color: #9ca3af; }

/* ── 评估改善（共用） ── */
.assess-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.assess-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 20rpx; }
.assess-row   { display: flex; align-items: center; gap: 16rpx; }
.assess-item  { flex: 1; text-align: center; }
.assess-num   { font-size: 52rpx; font-weight: 900; color: #374151; display: block; }
.assess-num--latest { color: #16a34a; }
.assess-lbl   { font-size: 22rpx; color: #6b7280; display: block; }
.assess-arrow { font-size: 36rpx; color: #9ca3af; }
.assess-delta { padding: 8rpx 20rpx; border-radius: 40rpx; font-size: 30rpx; font-weight: 800; }
.delta--pos { background: #dcfce7; color: #16a34a; }
.delta--neg { background: #fee2e2; color: #dc2626; }

/* ── 成长建议（grower，共用样式） ── */
.advice-card {
  background: #fff; margin: 16rpx 24rpx 0;
  border-radius: 20rpx; padding: 28rpx 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.advice-title { font-size: 28rpx; font-weight: 700; color: #111; display: block; margin-bottom: 16rpx; }
.advice-item  { display: flex; gap: 8rpx; margin-bottom: 12rpx; }
.advice-dot   { color: #7c3aed; font-size: 30rpx; flex-shrink: 0; line-height: 1.4; }
.advice-text  { font-size: 26rpx; color: #374151; line-height: 1.6; }

/* ── 底部申请按钮（sharer） ── */
.apply-footer {
  margin: 24rpx 24rpx 0; text-align: center;
}
.apply-btn {
  padding: 26rpx 0; border-radius: 20rpx;
  font-size: 30rpx; font-weight: 700; text-align: center;
}
.apply-btn--ready { background: linear-gradient(135deg, #065f46, #1d4ed8); color: #fff; }
.apply-btn--grey  { background: #f3f4f6; color: #6b7280; }
.apply-hint { font-size: 20rpx; color: #9ca3af; margin-top: 10rpx; display: block; }
</style>
