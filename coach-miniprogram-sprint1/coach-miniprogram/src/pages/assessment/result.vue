<template>
  <view class="result-page">

    <!-- 加载中 -->
    <template v-if="loading">
      <view class="px-4 pt-4">
        <view v-for="i in 4" :key="i" class="bhp-skeleton" style="height: 120rpx; margin-bottom: 16rpx; border-radius: var(--radius-lg);"></view>
      </view>
    </template>

    <template v-else-if="result">

      <!-- 英雄结果区 -->
      <view class="ar-hero" :style="{ background: heroGradient }">
        <text class="ar-hero__icon">{{ CATEGORY_ICON[result.category || ''] || '📊' }}</text>
        <text class="ar-hero__title">评估完成</text>
        <text class="ar-hero__assessment">{{ result.assessment_title }}</text>

        <!-- 分数（如果有） -->
        <view class="ar-hero__score-row" v-if="result.total_score != null">
          <view class="ar-hero__score-circle">
            <text class="ar-hero__score-val">{{ result.total_score }}</text>
            <text class="ar-hero__score-max" v-if="result.max_score"> / {{ result.max_score }}</text>
          </view>
        </view>

        <!-- 分类标签 -->
        <view class="ar-hero__category" v-if="result.category_label || result.category">
          <text>{{ result.category_label || CATEGORY_LABEL[result.category || ''] || result.category }}</text>
        </view>

        <!-- 提交时间 -->
        <text class="ar-hero__time">提交于 {{ formatDate(result.submitted_at) }}</text>
      </view>

      <!-- 结果解读 -->
      <view class="ar-interpretation px-4" v-if="result.interpretation">
        <view class="ar-section-card bhp-card bhp-card--flat">
          <text class="ar-section-title">📖 结果解读</text>
          <text class="ar-interpretation__text">{{ result.interpretation }}</text>
        </view>
      </view>

      <!-- 维度得分 -->
      <view class="ar-dimensions px-4" v-if="result.dimensions?.length">
        <view class="ar-section-card bhp-card bhp-card--flat">
          <text class="ar-section-title">📊 维度分析</text>
          <view
            v-for="dim in result.dimensions"
            :key="dim.name"
            class="ar-dim-row"
          >
            <view class="ar-dim-header">
              <text class="ar-dim-name">{{ dim.name }}</text>
              <view class="ar-dim-level" :class="`ar-level--${dim.level || 'moderate'}`" v-if="dim.level">
                <text>{{ LEVEL_LABEL[dim.level] || dim.level }}</text>
              </view>
              <text class="ar-dim-score">{{ dim.score }}<text class="ar-dim-max">/{{ dim.max_score }}</text></text>
            </view>
            <view class="ar-dim-bar">
              <view
                class="ar-dim-bar-fill"
                :style="{
                  width: Math.round((dim.score / dim.max_score) * 100) + '%',
                  background: dimColor(dim.level)
                }"
              ></view>
            </view>
            <text class="ar-dim-desc text-xs text-secondary-color" v-if="dim.description">{{ dim.description }}</text>
          </view>
        </view>
      </view>

      <!-- 健康建议 -->
      <view class="ar-recs px-4" v-if="result.recommendations?.length">
        <view class="ar-section-card bhp-card bhp-card--flat">
          <text class="ar-section-title">💡 改善建议</text>
          <view
            v-for="(rec, idx) in result.recommendations"
            :key="idx"
            class="ar-rec-item"
          >
            <view class="ar-rec-num">
              <text>{{ idx + 1 }}</text>
            </view>
            <text class="ar-rec-text">{{ rec }}</text>
          </view>
        </view>
      </view>

      <!-- 教练审核意见 -->
      <view class="ar-coach-note px-4" v-if="result.coach_note">
        <view class="ar-coach-note__card bhp-card bhp-card--flat">
          <text class="ar-section-title">👨‍⚕️ 教练意见</text>
          <text class="ar-coach-note__text">{{ result.coach_note }}</text>
          <text class="text-xs text-tertiary-color" v-if="result.reviewed_at">
            审核于 {{ formatDate(result.reviewed_at) }}
          </text>
        </view>
      </view>

      <!-- 等待审核提示 -->
      <view class="ar-pending px-4" v-else-if="justSubmitted">
        <view class="ar-pending__card">
          <text class="ar-pending__icon">⏳</text>
          <view class="ar-pending__body">
            <text class="ar-pending__title">等待教练审核</text>
            <text class="ar-pending__sub text-secondary-color">
              您的评估已提交，教练将尽快为您解读结果
            </text>
          </view>
        </view>
      </view>

      <!-- 底部操作 -->
      <view class="ar-actions px-4">
        <view class="ar-action-row">
          <view class="ar-btn ar-btn--secondary" @tap="goBack">
            <text>返回列表</text>
          </view>
          <view class="ar-btn ar-btn--primary" @tap="goHome">
            <text>回到首页</text>
          </view>
        </view>

        <!-- 相关推荐（若有改善建议，引导到学习中心） -->
        <view class="ar-recommend" v-if="result.recommendations?.length">
          <view class="ar-recommend__card bhp-card bhp-card--flat" @tap="goLearning">
            <view class="ar-recommend__icon-wrap">
              <text>📚</text>
            </view>
            <view class="ar-recommend__body">
              <text class="ar-recommend__title">查看相关学习内容</text>
              <text class="ar-recommend__sub text-xs text-secondary-color">根据评估结果为您推荐</text>
            </view>
            <text class="ar-recommend__arrow">›</text>
          </view>
        </view>
      </view>
    </template>

    <!-- 错误状态 -->
    <view class="ar-error px-4" v-else-if="!loading">
      <view class="ar-error__card bhp-card bhp-card--flat">
        <text class="ar-error__icon">⚠️</text>
        <text class="ar-error__title">结果加载失败</text>
        <text class="ar-error__sub text-secondary-color">您的答案已保存，请稍后重试</text>
        <view class="ar-btn ar-btn--secondary mt-4" @tap="load">
          <text>重新加载</text>
        </view>
      </view>
    </view>

    <view style="height: 60rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { myAssessmentApi, type AssessmentResult } from '@/api/assessment'

// ─── 常量 ─────────────────────────────────────────────────────
const CATEGORY_ICON: Record<string, string> = {
  high_risk:     '🔴',
  moderate_risk: '🟡',
  low_risk:      '🟢',
  normal:        '✅',
  positive:      '😊',
  negative:      '😔',
  mild:          '🟡',
  moderate:      '🟠',
  severe:        '🔴',
}

const CATEGORY_LABEL: Record<string, string> = {
  high_risk:     '高风险',
  moderate_risk: '中等风险',
  low_risk:      '低风险',
  normal:        '正常范围',
  positive:      '积极',
  negative:      '消极',
  mild:          '轻度',
  moderate:      '中度',
  severe:        '重度',
}

const CATEGORY_GRADIENTS: Record<string, string> = {
  high_risk:     'linear-gradient(135deg, #ff4d4f, #f5222d)',
  moderate_risk: 'linear-gradient(135deg, #fa8c16, #d46b08)',
  low_risk:      'linear-gradient(135deg, #52c41a, #389e0d)',
  normal:        'linear-gradient(135deg, #52c41a, #10b981)',
  positive:      'linear-gradient(135deg, #52c41a, #10b981)',
  negative:      'linear-gradient(135deg, #8c8c8c, #595959)',
  mild:          'linear-gradient(135deg, #fa8c16, #faad14)',
  moderate:      'linear-gradient(135deg, #fa541c, #fa8c16)',
  severe:        'linear-gradient(135deg, #f5222d, #cf1322)',
}

const DEFAULT_GRADIENT = 'linear-gradient(135deg, #722ed1, #1890ff)'

const LEVEL_LABEL: Record<string, string> = {
  high:     '高', moderate: '中', low: '低', normal: '正常'
}
const LEVEL_COLORS: Record<string, string> = {
  high:     '#ff4d4f', moderate: '#fa8c16', low: '#52c41a', normal: '#52c41a'
}

// ─── 状态 ─────────────────────────────────────────────────────
const result       = ref<AssessmentResult | null>(null)
const loading      = ref(false)
const assignmentId = ref(0)
const justSubmitted = ref(false)

// ─── 计算 ─────────────────────────────────────────────────────
const heroGradient = computed(() => {
  const cat = result.value?.category || ''
  return CATEGORY_GRADIENTS[cat] || DEFAULT_GRADIENT
})

// ─── 生命周期 ─────────────────────────────────────────────────
onMounted(load)

async function load() {
  const pages = getCurrentPages()
  const cur = pages[pages.length - 1] as any
  assignmentId.value = Number(cur?.options?.id || 0)
  justSubmitted.value = cur?.options?.just_submitted === '1'

  if (!assignmentId.value) return

  loading.value = true
  try {
    result.value = await myAssessmentApi.result(assignmentId.value)
  } catch (e: any) {
    // 刚提交时可能还未有结果，显示等待状态
    if (justSubmitted.value) {
      result.value = {
        assignment_id: assignmentId.value,
        assessment_title: '评估已提交',
        assessment_type: 'custom',
        submitted_at: new Date().toISOString(),
      }
    }
  } finally {
    loading.value = false
  }
}

// ─── 方法 ─────────────────────────────────────────────────────
function dimColor(level?: string): string {
  return LEVEL_COLORS[level || ''] || '#722ed1'
}

function formatDate(s: string): string {
  if (!s) return ''
  try {
    const d = new Date(s)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return s }
}

function goBack() {
  uni.navigateBack()
}

function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

function goLearning() {
  uni.navigateTo({ url: '/pages/learning/index' })
}
</script>

<style scoped>
.result-page { background: var(--surface-secondary); min-height: 100vh; }

/* 英雄区 */
.ar-hero {
  display: flex; flex-direction: column; align-items: center;
  padding: 56rpx 48rpx 40rpx; gap: 16rpx;
}
.ar-hero__icon       { font-size: 72rpx; }
.ar-hero__title      { font-size: 40rpx; font-weight: 700; color: #fff; }
.ar-hero__assessment { font-size: 24rpx; color: rgba(255,255,255,0.8); text-align: center; }

.ar-hero__score-row { margin: 8rpx 0; }
.ar-hero__score-circle {
  background: rgba(255,255,255,0.2);
  border: 4rpx solid rgba(255,255,255,0.5);
  border-radius: 50%;
  width: 140rpx; height: 140rpx;
  display: flex; align-items: center; justify-content: center;
  flex-direction: column;
}
.ar-hero__score-val { font-size: 52rpx; font-weight: 700; color: #fff; line-height: 1; }
.ar-hero__score-max { font-size: 22rpx; color: rgba(255,255,255,0.7); }

.ar-hero__category {
  background: rgba(255,255,255,0.25);
  border-radius: var(--radius-full);
  padding: 8rpx 28rpx;
  font-size: 26rpx; color: #fff; font-weight: 600;
}
.ar-hero__time { font-size: 22rpx; color: rgba(255,255,255,0.7); }

/* 公共 section */
.ar-section-card { padding: 24rpx; margin-top: 16rpx; }
.ar-section-title { display: block; font-size: 28rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 16rpx; }

/* 解读 */
.ar-interpretation { padding-top: 4rpx; }
.ar-interpretation__text { font-size: 26rpx; color: var(--text-primary); line-height: 1.7; }

/* 维度 */
.ar-dimensions { padding-top: 4rpx; }
.ar-dim-row { margin-bottom: 20rpx; }
.ar-dim-row:last-child { margin-bottom: 0; }
.ar-dim-header { display: flex; align-items: center; gap: 10rpx; margin-bottom: 8rpx; }
.ar-dim-name   { flex: 1; font-size: 26rpx; font-weight: 600; color: var(--text-primary); }
.ar-dim-level  {
  font-size: 18rpx; font-weight: 700;
  padding: 2rpx 10rpx; border-radius: var(--radius-full);
}
.ar-level--high     { background: #fff1f0; color: #cf1322; }
.ar-level--moderate { background: #fff7e6; color: #d46b08; }
.ar-level--low, .ar-level--normal { background: #f6ffed; color: #389e0d; }
.ar-dim-score  { font-size: 26rpx; font-weight: 700; color: var(--text-primary); }
.ar-dim-max    { font-size: 20rpx; color: var(--text-tertiary); font-weight: 400; }
.ar-dim-bar    { height: 14rpx; background: var(--bhp-gray-100); border-radius: var(--radius-full); overflow: hidden; margin-bottom: 6rpx; }
.ar-dim-bar-fill { height: 100%; border-radius: var(--radius-full); transition: width 0.5s ease; }
.ar-dim-desc   { display: block; }

/* 建议 */
.ar-recs { padding-top: 4rpx; }
.ar-rec-item { display: flex; align-items: flex-start; gap: 16rpx; margin-bottom: 16rpx; }
.ar-rec-item:last-child { margin-bottom: 0; }
.ar-rec-num {
  width: 36rpx; height: 36rpx; border-radius: 50%;
  background: var(--bhp-primary-500); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 18rpx; font-weight: 700; flex-shrink: 0; margin-top: 2rpx;
}
.ar-rec-text { font-size: 26rpx; color: var(--text-primary); line-height: 1.6; flex: 1; }

/* 教练意见 */
.ar-coach-note { padding-top: 4rpx; }
.ar-coach-note__card { background: var(--bhp-primary-50); border: 1px solid var(--bhp-primary-100, #d1fae5); }
.ar-coach-note__text { font-size: 26rpx; color: var(--text-primary); line-height: 1.6; margin-bottom: 8rpx; }

/* 等待审核 */
.ar-pending { padding-top: 16rpx; }
.ar-pending__card {
  display: flex; align-items: center; gap: 16rpx;
  background: var(--bhp-warn-50, #fffbeb);
  border: 1px solid var(--bhp-warn-200, #fde68a);
  border-radius: var(--radius-lg); padding: 20rpx 24rpx;
}
.ar-pending__icon { font-size: 40rpx; }
.ar-pending__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--bhp-warn-700, #b45309); margin-bottom: 4rpx; }
.ar-pending__sub   { font-size: 22rpx; }

/* 操作 */
.ar-actions { padding-top: 16rpx; }
.ar-action-row { display: flex; gap: 16rpx; margin-bottom: 16rpx; }
.ar-btn {
  flex: 1; height: 88rpx;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; font-weight: 600; cursor: pointer;
}
.ar-btn:active { opacity: 0.8; }
.ar-btn--primary   { background: var(--bhp-primary-500); color: #fff; }
.ar-btn--secondary { background: var(--bhp-gray-100); color: var(--text-secondary); }
.mt-4 { margin-top: 16rpx; }

/* 推荐 */
.ar-recommend { }
.ar-recommend__card {
  display: flex; align-items: center; gap: 16rpx;
  padding: 20rpx 24rpx; cursor: pointer;
}
.ar-recommend__card:active { opacity: 0.8; }
.ar-recommend__icon-wrap {
  width: 72rpx; height: 72rpx; border-radius: var(--radius-lg);
  background: var(--bhp-primary-50);
  display: flex; align-items: center; justify-content: center;
  font-size: 32rpx;
}
.ar-recommend__body { flex: 1; }
.ar-recommend__title { display: block; font-size: 26rpx; font-weight: 600; color: var(--text-primary); margin-bottom: 4rpx; }
.ar-recommend__arrow { font-size: 32rpx; color: var(--text-tertiary); }

/* 错误 */
.ar-error { padding-top: 40rpx; }
.ar-error__card {
  padding: 40rpx; display: flex; flex-direction: column; align-items: center; gap: 12rpx;
}
.ar-error__icon  { font-size: 64rpx; }
.ar-error__title { font-size: 30rpx; font-weight: 600; color: var(--text-primary); }
.ar-error__sub   { font-size: 24rpx; text-align: center; }
</style>
