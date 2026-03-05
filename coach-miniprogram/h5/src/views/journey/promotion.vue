<template>
  <view class="prom-page">
    <scroll-view scroll-y class="prom-scroll">
      <view class="prom-hero">
        <text class="prom-hero-icon">🚀</text>
        <text class="prom-hero-title">申请晋级</text>
        <text class="prom-hero-sub">当前：{{ levelName(currentLevel) }} → 目标：{{ levelName(targetLevel) }}</text>
      </view>

      <!-- 三级审核说明 -->
      <view class="prom-review-banner">
        <text class="prom-review-title">📋 三级审核流程</text>
        <view class="prom-review-steps">
          <view class="prom-review-step" :class="{ 'prom-review-step--active': true }">
            <text class="prom-review-step-num">1</text>
            <text class="prom-review-step-label">行为健康教练 初审</text>
          </view>
          <text class="prom-review-arrow">→</text>
          <view class="prom-review-step">
            <text class="prom-review-step-num">2</text>
            <text class="prom-review-step-label">行为健康促进师 复核</text>
          </view>
          <text class="prom-review-arrow">→</text>
          <view class="prom-review-step">
            <text class="prom-review-step-num">3</text>
            <text class="prom-review-step-label">≥2位大师 联合终审</text>
          </view>
        </view>
      </view>

      <!-- 晋级条件核查（按当前角色显示） -->
      <view v-if="requirements.length > 0" class="prom-reqs">
        <text class="prom-reqs-title">晋级条件核查</text>
        <view v-for="(req, i) in requirements" :key="i" class="prom-req-item"
          :class="{ 'prom-req-item--met': req.met }">
          <text class="prom-req-icon">{{ req.met ? '✅' : '⬜' }}</text>
          <view class="prom-req-body">
            <text class="prom-req-label">{{ req.label }}</text>
            <text class="prom-req-hint">{{ req.hint }}</text>
          </view>
        </view>
        <text v-if="reqsMet < requirements.length" class="prom-reqs-warn">
          ⚠️ 还有 {{ requirements.length - reqsMet }} 项条件未满足，仍可提交申请，但审核可能不通过
        </text>
      </view>

      <view class="prom-form">
        <view class="prom-field">
          <text class="prom-label">目标级别</text>
          <view class="prom-select-row">
            <view v-for="level in availableLevels" :key="level.key"
              class="prom-level-chip" :class="{ 'prom-level-chip--active': targetLevel === level.key }"
              @tap="targetLevel = level.key">
              {{ level.icon }} {{ level.name }}
            </view>
          </view>
        </view>

        <view class="prom-field">
          <text class="prom-label">申请理由 *</text>
          <textarea class="prom-textarea" v-model="reason"
            placeholder="请描述您的成长历程、核心能力和晋级理由（至少50字）..."
            :maxlength="800" />
          <text class="prom-char-count">{{ reason.length }}/800</text>
        </view>

        <view v-if="currentLevel === 'coach'" class="prom-field">
          <text class="prom-label">实践案例（晋级促进师必填）</text>
          <text class="prom-hint">请描述3个以上代表性案例，说明您的教练成效</text>
          <textarea class="prom-textarea" v-model="practiceCase"
            placeholder="案例1：学员XXX，…&#10;案例2：..."
            :maxlength="1200" />
          <text class="prom-char-count">{{ practiceCase.length }}/1200</text>
        </view>

        <view class="prom-field">
          <text class="prom-label">支持材料（可选）</text>
          <text class="prom-hint">认证证书、学习成果截图、同道者评价等</text>
          <view class="prom-upload-placeholder">
            <text>📎 上传材料功能即将上线</text>
          </view>
        </view>
      </view>

      <view class="prom-submit-btn"
        :class="{ 'prom-submit-btn--disabled': !canSubmit, 'prom-submit-btn--coach': currentLevel === 'coach' }"
        @tap="submitPromotion">
        <text>{{ submitting ? '提交中...' : '提交晋级申请' }}</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { httpReq as http } from '@/api/request'

const levelOrder = ['observer', 'grower', 'sharer', 'coach', 'promoter', 'master']
const levels = [
  { key: 'observer',  name: '观察员',         icon: '👁'  },
  { key: 'grower',    name: '成长者',         icon: '🌱'  },
  { key: 'sharer',    name: '分享者',         icon: '🤝'  },
  { key: 'coach',     name: '行为健康教练',   icon: '🎯'  },
  { key: 'promoter',  name: '行为健康促进师', icon: '🏅'  },
  { key: 'master',    name: '行为健康大师',   icon: '👑'  },
]

const currentLevel = ref('observer')
const targetLevel = ref('grower')
const reason = ref('')
const practiceCase = ref('')
const submitting = ref(false)

// 晋级条件核查列表
interface Req { label: string; hint: string; met: boolean }
const requirements = ref<Req[]>([])
const reqsMet = computed(() => requirements.value.filter(r => r.met).length)

const availableLevels = computed(() => {
  const idx = levelOrder.indexOf(currentLevel.value)
  // 只允许晋升到紧邻的下一级
  const next = levelOrder[idx + 1]
  return next ? [levels.find(l => l.key === next)!].filter(Boolean) : []
})
const canSubmit = computed(() => {
  const minLen = currentLevel.value === 'coach' ? 50 : 20
  return reason.value.length >= minLen && !submitting.value
})

function levelName(k: string) { return levels.find(l => l.key === k)?.name || k }

// 构建角色对应的条件检查列表（用于展示，不阻断提交）
function buildRequirements(level: string, statusData: any) {
  if (level === 'sharer') {
    // 分享者 → 行为健康教练
    const p = statusData?.points || {}
    const c = statusData?.companions || {}
    requirements.value = [
      { label: '成长积分 ≥ 800', hint: `当前：${p.growth ?? '—'}`, met: (p.growth ?? 0) >= 800 },
      { label: '贡献积分 ≥ 200', hint: `当前：${p.contribution ?? '—'}`, met: (p.contribution ?? 0) >= 200 },
      { label: '影响力积分 ≥ 50', hint: `当前：${p.influence ?? '—'}`, met: (p.influence ?? 0) >= 50 },
      { label: '总学分 ≥ 800', hint: `当前：${statusData?.credits ?? '—'}`, met: (statusData?.credits ?? 0) >= 800 },
      { label: '已毕业同道者 ≥ 4 名', hint: `当前：${c.graduated ?? '—'}`, met: (c.graduated ?? 0) >= 4 },
      { label: '带教质量评分 ≥ 3.5', hint: `当前：${c.avg_quality ?? '—'}`, met: (c.avg_quality ?? 0) >= 3.5 },
      { label: '通过 L3 认证考试', hint: '需先通过行为健康教练认证考试', met: statusData?.coach_exam_passed ?? false },
    ]
  } else if (level === 'coach') {
    // 行为健康教练 → 行为健康促进师
    const p = statusData?.points || {}
    const c = statusData?.companions || {}
    requirements.value = [
      { label: '成长积分 ≥ 2000', hint: `当前：${p.growth ?? '—'}`, met: (p.growth ?? 0) >= 2000 },
      { label: '贡献积分 ≥ 500',  hint: `当前：${p.contribution ?? '—'}`, met: (p.contribution ?? 0) >= 500 },
      { label: '影响力积分 ≥ 150', hint: `当前：${p.influence ?? '—'}`, met: (p.influence ?? 0) >= 150 },
      { label: '总学分 ≥ 2000', hint: `当前：${statusData?.credits ?? '—'}`, met: (statusData?.credits ?? 0) >= 2000 },
      { label: '已毕业 L2 同道者 ≥ 4 名', hint: `当前：${c.graduated ?? '—'}`, met: (c.graduated ?? 0) >= 4 },
      { label: '带教质量评分 ≥ 4.0', hint: `当前：${c.avg_quality ?? '—'}`, met: (c.avg_quality ?? 0) >= 4.0 },
      { label: '通过 L4 认证考试', hint: '需先通过行为健康促进师认证考试', met: statusData?.promoter_exam_passed ?? false },
    ]
  } else {
    requirements.value = []
  }
}

async function loadOverview() {
  try {
    const [overRes, promoRes] = await Promise.allSettled([
      http<any>('/api/v1/journey/overview'),
      http<any>('/api/v1/promotion/check'),
    ])
    if (overRes.status === 'fulfilled') {
      currentLevel.value = overRes.value?.current_level || 'observer'
      const nextIdx = levelOrder.indexOf(currentLevel.value) + 1
      targetLevel.value = levelOrder[nextIdx] || currentLevel.value
    }
    const statusData = promoRes.status === 'fulfilled' ? promoRes.value : null
    buildRequirements(currentLevel.value, statusData)
  } catch (e) { console.warn('[journey/promotion] overview:', e) }
}

async function submitPromotion() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const fullStatement = currentLevel.value === 'coach' && practiceCase.value.trim()
      ? `${reason.value}\n\n【实践案例】\n${practiceCase.value}`
      : reason.value
    await http('/api/v1/promotion/sharer-apply', {
      method: 'POST',
      data: { target_role: targetLevel.value, statement: fullStatement, dim_ready: reqsMet.value }
    })
    uni.showToast({ title: '申请已提交，等待审核', icon: 'success', duration: 2000 })
    setTimeout(() => uni.navigateBack(), 2200)
  } catch {
    uni.showToast({ title: '提交失败，请重试', icon: 'none' })
  } finally { submitting.value = false }
}

onMounted(() => { loadOverview() })
</script>

<style scoped>
.prom-page { min-height: 100vh; background: #F5F6FA; }
.prom-scroll { height: 100vh; }

.prom-hero {
  display: flex; flex-direction: column; align-items: center; padding: 48rpx 32rpx;
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff;
  padding-top: calc(48rpx + env(safe-area-inset-top));
}
.prom-hero-icon { font-size: 64rpx; margin-bottom: 16rpx; }
.prom-hero-title { font-size: 40rpx; font-weight: 700; margin-bottom: 12rpx; }
.prom-hero-sub { font-size: 24rpx; opacity: 0.85; }

.prom-form { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 24rpx; }
.prom-field { margin-bottom: 28rpx; }
.prom-label { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 12rpx; }
.prom-hint { display: block; font-size: 22rpx; color: #8E99A4; margin-bottom: 10rpx; }
.prom-select-row { display: flex; flex-wrap: wrap; gap: 12rpx; }
.prom-level-chip { padding: 10rpx 20rpx; border-radius: 20rpx; font-size: 24rpx; background: #F5F6FA; color: #5B6B7F; border: 1rpx solid #E0E0E0; }
.prom-level-chip--active { background: #2D8E69; color: #fff; border-color: #2D8E69; }
.prom-textarea { width: 100%; min-height: 200rpx; background: #F8F9FA; border-radius: 12rpx; padding: 16rpx; font-size: 26rpx; color: #2C3E50; border: 1rpx solid #E0E0E0; box-sizing: border-box; }
.prom-char-count { display: block; text-align: right; font-size: 20rpx; color: #BDC3C7; margin-top: 8rpx; }
.prom-upload-placeholder { background: #F8F9FA; border: 2rpx dashed #D0D5DD; border-radius: 12rpx; padding: 32rpx; text-align: center; font-size: 24rpx; color: #8E99A4; }

.prom-submit-btn { margin: 0 24rpx; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); border-radius: 16rpx; padding: 24rpx; text-align: center; color: #fff; font-size: 32rpx; font-weight: 700; }
.prom-submit-btn--disabled { opacity: 0.5; }
.prom-submit-btn--coach { background: linear-gradient(135deg, #7B3FA0 0%, #9B59B6 100%); }

/* 三级审核流程 banner */
.prom-review-banner { background: #fff; margin: 24rpx; border-radius: 16rpx; padding: 24rpx; border-left: 6rpx solid #2D8E69; }
.prom-review-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.prom-review-steps { display: flex; align-items: center; flex-wrap: wrap; gap: 8rpx; }
.prom-review-step { display: flex; align-items: center; gap: 8rpx; padding: 8rpx 16rpx; border-radius: 20rpx; background: #F5F6FA; border: 1rpx solid #E0E0E0; }
.prom-review-step--active { background: #E8F5EF; border-color: #2D8E69; }
.prom-review-step-num { width: 32rpx; height: 32rpx; border-radius: 50%; background: #BDC3C7; color: #fff; font-size: 18rpx; font-weight: 700; text-align: center; line-height: 32rpx; }
.prom-review-step--active .prom-review-step-num { background: #2D8E69; }
.prom-review-step-label { font-size: 22rpx; color: #5B6B7F; }
.prom-review-step--active .prom-review-step-label { color: #2D8E69; font-weight: 600; }
.prom-review-arrow { font-size: 24rpx; color: #BDC3C7; }

/* 晋级条件核查 */
.prom-reqs { background: #fff; margin: 0 24rpx 24rpx; border-radius: 16rpx; padding: 24rpx; }
.prom-reqs-title { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 16rpx; }
.prom-req-item { display: flex; align-items: flex-start; gap: 12rpx; padding: 12rpx 0; border-bottom: 1rpx solid #F5F6FA; }
.prom-req-item:last-child { border-bottom: none; }
.prom-req-item--met .prom-req-label { color: #2D8E69; }
.prom-req-icon { font-size: 28rpx; flex-shrink: 0; margin-top: 2rpx; }
.prom-req-body { flex: 1; }
.prom-req-label { display: block; font-size: 26rpx; color: #2C3E50; margin-bottom: 4rpx; }
.prom-req-hint { display: block; font-size: 22rpx; color: #8E99A4; }
.prom-reqs-warn { display: block; margin-top: 16rpx; font-size: 22rpx; color: #E67E22; background: #FEF9EE; padding: 12rpx 16rpx; border-radius: 8rpx; line-height: 1.6; }
</style>
