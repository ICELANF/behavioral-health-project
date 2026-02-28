<template>
  <view class="cert-page">

    <!-- 概览横幅 -->
    <view class="cert-banner px-4">
      <view class="cert-banner__card">
        <view class="cert-banner__left">
          <text class="cert-banner__count">{{ passedCount }}</text>
          <text class="cert-banner__label">已获认证</text>
        </view>
        <view class="cert-banner__divider"></view>
        <view class="cert-banner__right">
          <text class="cert-banner__next" v-if="nextCertLevel">
            下一认证：{{ LEVEL_META[nextCertLevel]?.label || nextCertLevel }}
          </text>
          <text class="cert-banner__next" v-else>已完成全部认证 🎉</text>
        </view>
      </view>
    </view>

    <!-- 认证等级列表 -->
    <view class="cert-list px-4">

      <!-- 骨架屏 -->
      <template v-if="loading">
        <view v-for="i in 5" :key="i" class="bhp-skeleton" style="height: 120rpx; margin-bottom: 12rpx; border-radius: var(--radius-lg);"></view>
      </template>

      <template v-else>
        <view
          v-for="levelKey in CERT_LEVELS"
          :key="levelKey"
          class="cert-item bhp-card bhp-card--flat"
          :class="{
            'cert-item--passed': certMap[levelKey],
            'cert-item--locked': !certMap[levelKey] && isLocked(levelKey)
          }"
        >
          <!-- 等级标志 -->
          <view
            class="cert-item__badge"
            :style="{ background: certMap[levelKey] ? LEVEL_META[levelKey].color : '#d1d5db' }"
          >
            <text class="cert-item__badge-text">{{ LEVEL_META[levelKey]?.icon || levelKey }}</text>
          </view>

          <!-- 信息 -->
          <view class="cert-item__body">
            <view class="cert-item__name-row">
              <text class="cert-item__name">{{ LEVEL_META[levelKey]?.label || levelKey }} 认证</text>
              <view
                class="cert-item__status"
                :class="certMap[levelKey] ? 'cert-status--passed' : isLocked(levelKey) ? 'cert-status--locked' : 'cert-status--pending'"
              >
                <text>{{ certMap[levelKey] ? '已认证' : isLocked(levelKey) ? '未解锁' : '可参考' }}</text>
              </view>
            </view>

            <template v-if="certMap[levelKey]">
              <text class="cert-item__date text-xs text-secondary-color">
                通过时间：{{ formatDate(certMap[levelKey].passed_at) }}
              </text>
              <text class="cert-item__score text-xs text-secondary-color">
                得分：{{ certMap[levelKey].score }}分
              </text>
              <text class="cert-item__no text-xs text-tertiary-color" v-if="certMap[levelKey].certificate_no">
                证书编号：{{ certMap[levelKey].certificate_no }}
              </text>
            </template>

            <template v-else-if="!isLocked(levelKey)">
              <text class="cert-item__hint text-xs text-primary-color">前往认证考试参加此级别认证 →</text>
            </template>

            <template v-else>
              <text class="cert-item__hint text-xs text-tertiary-color">达到 {{ LEVEL_META[levelKey]?.reqLabel }} 后解锁</text>
            </template>
          </view>

          <!-- 右侧装饰 -->
          <view class="cert-item__right" v-if="certMap[levelKey]">
            <text class="cert-item__check">✓</text>
          </view>
          <view class="cert-item__right" v-else-if="!isLocked(levelKey)">
            <view class="cert-item__go-btn" @tap="goExam(levelKey)">
              <text>去考试</text>
            </view>
          </view>
          <view class="cert-item__right" v-else>
            <text class="cert-item__lock">🔒</text>
          </view>
        </view>
      </template>
    </view>

    <!-- 说明 -->
    <view class="cert-note px-4">
      <view class="cert-note__card bhp-card bhp-card--flat">
        <text class="cert-note__title">📋 认证说明</text>
        <text class="cert-note__item">• 每级认证考试需要达到对应成长等级</text>
        <text class="cert-note__item">• 通过认证将颁发对应等级证书</text>
        <text class="cert-note__item">• 认证是晋级的必要条件之一</text>
        <text class="cert-note__item">• 证书永久有效，可随时查阅</text>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { profileApi, type CertificationRecord } from '@/api/profile'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// ─── 常量 ─────────────────────────────────────────────────────
const CERT_LEVELS = ['L1', 'L2', 'L3', 'L4', 'L5']

const LEVEL_META: Record<string, {
  label: string; icon: string; color: string; reqLabel: string; minRoleLevel: number
}> = {
  L1: { label: 'L1 成长者', icon: '🌱', color: '#52c41a', reqLabel: 'L0 观察员',   minRoleLevel: 1 },
  L2: { label: 'L2 分享者', icon: '💧', color: '#1890ff', reqLabel: 'L1 成长者',  minRoleLevel: 2 },
  L3: { label: 'L3 教练',   icon: '⚡', color: '#722ed1', reqLabel: 'L2 分享者',  minRoleLevel: 3 },
  L4: { label: 'L4 促进师', icon: '🔥', color: '#eb2f96', reqLabel: 'L3 教练',    minRoleLevel: 4 },
  L5: { label: 'L5 大师',   icon: '👑', color: '#faad14', reqLabel: 'L4 促进师',  minRoleLevel: 5 },
}

// ─── 状态 ─────────────────────────────────────────────────────
const certs    = ref<CertificationRecord[]>([])
const loading  = ref(false)

// ─── 计算 ─────────────────────────────────────────────────────
const certMap = computed(() => {
  const map: Record<string, CertificationRecord> = {}
  certs.value.forEach(c => { map[c.level] = c })
  return map
})

const passedCount = computed(() =>
  CERT_LEVELS.filter(l => certMap.value[l]).length
)

const nextCertLevel = computed(() =>
  CERT_LEVELS.find(l => !certMap.value[l] && !isLocked(l)) ||
  CERT_LEVELS.find(l => !certMap.value[l]) || null
)

// ─── 方法 ─────────────────────────────────────────────────────
function isLocked(levelKey: string): boolean {
  const meta = LEVEL_META[levelKey]
  if (!meta) return false
  return userStore.roleLevel < meta.minRoleLevel
}

onMounted(loadCerts)

async function loadCerts() {
  loading.value = true
  try {
    const data = await profileApi.myCertifications()
    certs.value = Array.isArray(data) ? data : []
  } catch { /* 静默：无认证记录 */ } finally {
    loading.value = false
  }
}

function goExam(levelKey: string) {
  uni.navigateTo({ url: '/pages/exam/index' })
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return dateStr }
}
</script>

<style scoped>
.cert-page { background: var(--surface-secondary); min-height: 100vh; }

/* 横幅 */
.cert-banner { padding-top: 16rpx; }
.cert-banner__card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  border-radius: var(--radius-lg);
  padding: 24rpx 32rpx;
  gap: 24rpx;
}
.cert-banner__left { display: flex; flex-direction: column; align-items: center; gap: 4rpx; }
.cert-banner__count { font-size: 52rpx; font-weight: 700; color: #fff; line-height: 1; }
.cert-banner__label { font-size: 22rpx; color: rgba(255,255,255,0.8); }
.cert-banner__divider { width: 1px; height: 60rpx; background: rgba(255,255,255,0.3); }
.cert-banner__right { flex: 1; }
.cert-banner__next { font-size: 26rpx; color: #fff; font-weight: 500; }

/* 认证列表 */
.cert-list { padding-top: 16rpx; }

.cert-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 12rpx;
  transition: opacity 0.2s;
}
.cert-item--locked { opacity: 0.6; }

.cert-item__badge {
  width: 72rpx; height: 72rpx;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cert-item__badge-text { font-size: 32rpx; }

.cert-item__body { flex: 1; overflow: hidden; }
.cert-item__name-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 6rpx; }
.cert-item__name { font-size: 28rpx; font-weight: 600; color: var(--text-primary); }

.cert-item__status {
  font-size: 20rpx; font-weight: 700;
  padding: 3rpx 12rpx;
  border-radius: var(--radius-full);
}
.cert-status--passed  { background: var(--bhp-success-50, #f0fdf4); color: var(--bhp-success-600, #16a34a); }
.cert-status--locked  { background: var(--bhp-gray-100); color: var(--text-tertiary); }
.cert-status--pending { background: var(--bhp-warn-50, #fffbeb); color: var(--bhp-warn-600, #d97706); }

.cert-item__date  { display: block; }
.cert-item__score { display: block; }
.cert-item__no    { display: block; }
.cert-item__hint  { display: block; margin-top: 4rpx; }

.cert-item__right { flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.cert-item__check { font-size: 40rpx; color: var(--bhp-success-500, #22c55e); font-weight: 700; }
.cert-item__lock  { font-size: 32rpx; }

.cert-item__go-btn {
  background: var(--bhp-primary-500);
  color: #fff;
  font-size: 22rpx; font-weight: 600;
  padding: 8rpx 20rpx;
  border-radius: var(--radius-full);
  cursor: pointer;
}
.cert-item__go-btn:active { opacity: 0.8; }

/* 说明 */
.cert-note { padding-top: 16rpx; }
.cert-note__card { padding: 20rpx 24rpx; }
.cert-note__title { display: block; font-size: 26rpx; font-weight: 700; color: var(--text-primary); margin-bottom: 12rpx; }
.cert-note__item  { display: block; font-size: 24rpx; color: var(--text-secondary); line-height: 1.8; }
</style>
