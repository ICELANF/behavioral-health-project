<template>
  <div class="page-container">
    <van-nav-bar title="行为处方详情" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="rx">
        <!-- 头部卡: 阶段 + 强度 + 状态 -->
        <div class="card rx-header">
          <div class="rx-header-top">
            <van-tag :type="stageTagType" size="large">
              {{ stageLabel }}
            </van-tag>
            <van-tag plain :type="intensityTagType" size="medium">
              {{ intensityLabel }}
            </van-tag>
            <van-tag
              :type="rx.status === 'active' ? 'success' : 'warning'"
              size="medium"
              style="margin-left:auto"
            >
              {{ statusLabel }}
            </van-tag>
          </div>
          <div class="rx-domain">
            <van-icon name="label-o" size="16" color="#1989fa" />
            {{ domainLabel }}
          </div>
          <div class="rx-time">
            {{ formatTime(rx.created_at) }}
          </div>
        </div>

        <!-- 待审核门控: draft/pending 状态隐藏详细内容 -->
        <div v-if="isDraftOrPending" class="card rx-pending-gate">
          <van-icon name="clock-o" size="40" color="#faad14" />
          <p class="pending-title">处方内容待教练审核</p>
          <p class="pending-hint">教练审核通过后，处方详细内容将在此展示</p>
          <van-tag type="warning" size="medium">{{ statusLabel }}</van-tag>
        </div>

        <!-- 以下详细内容仅在非 draft/pending 状态展示 -->
        <template v-else>
        <!-- 目标行为卡 -->
        <div class="card rx-section">
          <div class="section-title">
            <van-icon name="aim" size="18" color="#1989fa" />
            目标行为
          </div>
          <div class="rx-target">{{ rx.target_behavior }}</div>
          <div class="rx-detail-row" v-if="rx.frequency_dose">
            <span class="detail-label">频次</span>
            <span>{{ rx.frequency_dose }}</span>
          </div>
          <div class="rx-detail-row" v-if="rx.trigger_cue">
            <span class="detail-label">触发线索</span>
            <span>{{ rx.trigger_cue }}</span>
          </div>
          <div class="rx-detail-row" v-if="rx.time_place">
            <span class="detail-label">时间/地点</span>
            <span>{{ rx.time_place }}</span>
          </div>
        </div>

        <!-- 策略卡 -->
        <div class="card rx-section" v-if="rx.domain">
          <div class="section-title">
            <van-icon name="chart-trending-o" size="18" color="#07c160" />
            处方策略
          </div>
          <div class="strategy-tags">
            <van-tag type="success" size="medium">{{ domainLabel }}</van-tag>
            <van-tag plain type="primary" size="medium" v-if="rx.difficulty_level">
              {{ intensityLabel }}强度
            </van-tag>
          </div>
        </div>

        <!-- 障碍预案卡 -->
        <div class="card rx-section" v-if="rx.obstacle_plan">
          <div class="section-title">
            <van-icon name="shield-o" size="18" color="#ff976a" />
            障碍预案
          </div>
          <div class="rx-obstacle">{{ rx.obstacle_plan }}</div>
        </div>

        <!-- 支持资源卡 -->
        <div class="card rx-section" v-if="rx.support_resource">
          <div class="section-title">
            <van-icon name="friends-o" size="18" color="#7c3aed" />
            支持资源
          </div>
          <div class="rx-support">{{ rx.support_resource }}</div>
        </div>

        <!-- 审核信息 -->
        <div class="card rx-section" v-if="rx.approved_by_review">
          <div class="section-title">
            <van-icon name="certificate" size="18" color="#07c160" />
            审核信息
          </div>
          <div class="rx-detail-row">
            <span class="detail-label">状态</span>
            <van-tag type="success" size="small">教练已审核</van-tag>
          </div>
        </div>
        </template>
      </template>

      <van-empty v-else-if="!loading" description="处方不存在或无权限查看" />

      <!-- TabBar 占位 -->
      <div style="height: 60px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { rxApi } from '@/api/rx'
import type { RxPrescription } from '@/types/rx'
import { TTM_STAGES, INTENSITY_LABELS, DOMAIN_LABELS } from '@/types/rx'

const route = useRoute()
const loading = ref(true)
const rx = ref<RxPrescription | null>(null)

const stageLabel = computed(() => {
  if (!rx.value) return ''
  return TTM_STAGES[rx.value.cultivation_stage] || rx.value.cultivation_stage || '启动期'
})

const stageTagType = computed(() => {
  const s = rx.value?.cultivation_stage || ''
  if (['S0', 'S1'].includes(s)) return 'warning'
  if (['S2', 'S3', 'startup'].includes(s)) return 'primary'
  if (['S4', 'S5', 'S6'].includes(s)) return 'success'
  return 'primary'
})

const intensityLabel = computed(() => {
  if (!rx.value) return ''
  return INTENSITY_LABELS[rx.value.difficulty_level] || rx.value.difficulty_level || '中等'
})

const intensityTagType = computed(() => {
  const d = rx.value?.difficulty_level || ''
  if (['minimal', 'low', 'easy'].includes(d)) return 'success'
  if (['moderate', 'medium'].includes(d)) return 'primary'
  return 'warning'
})

const domainLabel = computed(() => {
  if (!rx.value) return ''
  return DOMAIN_LABELS[rx.value.domain] || rx.value.domain || '综合'
})

const isDraftOrPending = computed(() => {
  const s = rx.value?.status
  return s === 'draft' || s === 'pending'
})

const statusLabel = computed(() => {
  const m: Record<string, string> = {
    active: '进行中', draft: '待审核', completed: '已完成',
    paused: '已暂停', cancelled: '已取消',
  }
  return m[rx.value?.status || ''] || rx.value?.status || ''
})

function formatTime(str: string | null) {
  if (!str) return ''
  const d = new Date(str)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour}小时前`
  return str.replace('T', ' ').slice(0, 16)
}

onMounted(async () => {
  const rxId = route.params.id as string
  if (!rxId) {
    loading.value = false
    return
  }
  try {
    const res: any = await rxApi.getDetail(rxId)
    rx.value = res
  } catch {
    rx.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading { text-align: center; padding: 60px 0; }

.card {
  background: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-md;
  margin-bottom: $spacing-sm;
  box-shadow: $shadow-sm;
}

.rx-header {
  .rx-header-top {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    flex-wrap: wrap;
  }

  .rx-domain {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: $spacing-sm;
    font-size: $font-size-md;
    color: $text-color;
  }

  .rx-time {
    font-size: $font-size-xs;
    color: $text-color-placeholder;
    margin-top: 4px;
  }
}

.rx-section {
  .section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-color;
    margin-bottom: $spacing-sm;
  }

  .rx-target {
    font-size: 16px;
    font-weight: 500;
    color: #1a1a1a;
    margin-bottom: $spacing-xs;
    line-height: 1.5;
  }

  .rx-detail-row {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    padding: 6px 0;
    font-size: $font-size-md;
    border-bottom: 1px solid $border-color;

    &:last-child { border-bottom: none; }

    .detail-label {
      flex-shrink: 0;
      width: 80px;
      color: $text-color-secondary;
      font-size: $font-size-sm;
    }
  }

  .strategy-tags {
    display: flex;
    gap: $spacing-xs;
    flex-wrap: wrap;
  }

  .rx-pending-gate {
    text-align: center;
    padding: $spacing-lg $spacing-md;

    .pending-title {
      font-size: 16px;
      font-weight: 600;
      color: $text-color;
      margin: $spacing-sm 0 4px;
    }

    .pending-hint {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-bottom: $spacing-sm;
    }
  }

  .rx-obstacle, .rx-support {
    font-size: $font-size-md;
    color: $text-color;
    line-height: 1.6;
    padding: $spacing-xs $spacing-sm;
    background: $background-color;
    border-radius: $border-radius;
  }
}
</style>
