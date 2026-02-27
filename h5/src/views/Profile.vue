<template>
  <PageShell title="个人中心" :show-tab-bar="true">
      <!-- 用户信息卡片 + 资料编辑 -->
      <div class="user-card card">
        <ProfileEditor />
        <div class="user-meta-row">
          <span class="role-tag" :class="'role--' + userStore.role">{{ userStore.roleLabel }}</span>
          <span class="growth-pts" v-if="userStore.growthPoints > 0">{{ userStore.growthPoints }} 积分</span>
          <span class="user-id">ID: {{ userStore.userId }}</span>
        </div>
        <div class="efficacy-badge" :style="{ backgroundColor: userStore.efficacyColor + '20', color: userStore.efficacyColor }">
          效能 {{ userStore.efficacyScore }}
        </div>
      </div>

      <!-- 穿戴设备数据 -->
      <div class="wearable-card card">
        <h3>穿戴设备</h3>
        <van-grid :column-num="4" :border="false">
          <van-grid-item>
            <template #icon>
              <van-icon name="fire-o" color="#ee0a24" size="24" />
            </template>
            <template #text>
              <div class="data-value">{{ userStore.wearableData.hr || '--' }}</div>
              <div class="data-label">心率</div>
            </template>
          </van-grid-item>
          <van-grid-item>
            <template #icon>
              <van-icon name="guide-o" color="#1989fa" size="24" />
            </template>
            <template #text>
              <div class="data-value">{{ userStore.wearableData.steps || '--' }}</div>
              <div class="data-label">步数</div>
            </template>
          </van-grid-item>
          <van-grid-item>
            <template #icon>
              <van-icon name="clock-o" color="#7c3aed" size="24" />
            </template>
            <template #text>
              <div class="data-value">{{ userStore.wearableData.sleep_hours || '--' }}</div>
              <div class="data-label">睡眠</div>
            </template>
          </van-grid-item>
          <van-grid-item>
            <template #icon>
              <van-icon name="chart-trending-o" color="#07c160" size="24" />
            </template>
            <template #text>
              <div class="data-value">{{ userStore.wearableData.hrv || '--' }}</div>
              <div class="data-label">HRV</div>
            </template>
          </van-grid-item>
        </van-grid>
      </div>

      <!-- 我的关注领域（原则二：关注问题直接导出任务） -->
      <div class="focus-card card">
        <div class="focus-header">
          <div class="focus-title">
            <van-icon name="flag-o" color="#07c160" />
            <span>我的关注领域</span>
          </div>
          <span class="focus-hint">影响 AI 任务推荐</span>
        </div>
        <div class="focus-tags">
          <van-tag
            v-for="domain in ALL_DOMAINS"
            :key="domain.value"
            :type="focusDomains.includes(domain.value) ? 'primary' : 'default'"
            size="medium"
            class="focus-tag"
            :class="{ active: focusDomains.includes(domain.value) }"
            @click="toggleFocusDomain(domain.value)"
          >
            {{ domain.label }}
          </van-tag>
        </div>
        <div class="focus-tip">
          <van-icon name="info-o" size="12" color="#999" />
          <span>选择你关注的健康问题，AI 将优先为你推荐相关任务</span>
        </div>
      </div>

      <!-- 功能菜单 -->
      <div class="menu-card card">
        <van-cell-group :border="false">
          <van-cell title="健康档案" icon="records-o" is-link @click="goTo('health-records')" />
          <van-cell title="历史报告" icon="description-o" is-link @click="goTo('history-reports')" />
          <van-cell title="数据同步" icon="replay" is-link @click="goTo('data-sync')" />
          <van-cell title="消息通知" icon="bell" is-link @click="goTo('notifications')" />
        </van-cell-group>
      </div>

      <!-- 设置菜单 -->
      <div class="menu-card card">
        <van-cell-group :border="false">
          <van-cell title="通知设置" icon="bell" is-link @click="goTo('notification-settings')" />
          <van-cell title="账号设置" icon="setting-o" is-link @click="goTo('account-settings')" />
          <van-cell title="隐私政策" icon="shield-o" is-link @click="goTo('privacy-policy')" />
          <van-cell title="关于我们" icon="info-o" is-link @click="goTo('about-us')" />
        </van-cell-group>
      </div>

      <!-- 退出按钮 -->
      <van-button plain type="danger" block round class="logout-btn" @click="handleLogout">
        退出登录
      </van-button>

      <!-- 版本信息 -->
      <div class="version-info">
        行健行为教练 v{{ appVersion }}
      </div>
  </PageShell>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showToast, showSuccessToast } from 'vant'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/api/index'
import PageShell from '@/components/common/PageShell.vue'
import ProfileEditor from '@/components/profile/ProfileEditor.vue'
import { APP_VERSION } from '@/config'

const router = useRouter()
const appVersion = APP_VERSION
const userStore = useUserStore()

// ────── 关注领域（原则二：关注问题直接导出任务） ──────
const ALL_DOMAINS = [
  { value: 'nutrition', label: '营养' },
  { value: 'exercise', label: '运动' },
  { value: 'sleep', label: '睡眠' },
  { value: 'emotion', label: '情绪' },
  { value: 'stress', label: '压力' },
  { value: 'cognitive', label: '认知' },
  { value: 'social', label: '社交' },
  { value: 'tcm', label: '中医' },
]

const focusDomains = ref<string[]>([])
let focusSaveTimer: ReturnType<typeof setTimeout> | null = null

function toggleFocusDomain(domain: string) {
  const idx = focusDomains.value.indexOf(domain)
  if (idx === -1) {
    if (focusDomains.value.length >= 5) {
      showToast('最多选择5个关注领域')
      return
    }
    focusDomains.value.push(domain)
  } else {
    if (focusDomains.value.length <= 1) {
      showToast('至少保留1个关注领域')
      return
    }
    focusDomains.value.splice(idx, 1)
  }
  // 防抖自动保存（600ms 后触发）
  if (focusSaveTimer) clearTimeout(focusSaveTimer)
  focusSaveTimer = setTimeout(saveFocusDomains, 600)
}

async function saveFocusDomains() {
  try {
    await api.patch('/api/v1/micro-actions/focus-areas', { domains: focusDomains.value })
    showSuccessToast('关注领域已更新')
  } catch {
    showToast('保存失败，请重试')
  }
}

async function loadFocusDomains() {
  try {
    // 从 task-pool 接口拿 focus_domains（不额外增加接口）
    const pool: any = await api.get('/api/v1/micro-actions/task-pool')
    if (pool?.focus_domains?.length) {
      focusDomains.value = pool.focus_domains
    } else {
      focusDomains.value = ['nutrition', 'exercise', 'sleep']
    }
  } catch {
    focusDomains.value = ['nutrition', 'exercise', 'sleep']
  }
}

// goProfile removed — ProfileEditor handles avatar upload inline

onMounted(async () => {
  // 并行加载：用户信息 + 设备数据 + 关注领域
  const [meRes, deviceRes] = await Promise.allSettled([
    api.get('/api/v1/auth/me'),
    api.get('/api/v1/mp/device/dashboard/today'),
  ])

  if (meRes.status === 'fulfilled') {
    const me: any = meRes.value
    if (me.username) userStore.name = me.username
    if (me.id) userStore.userId = String(me.id)
    if (me.efficacy_score != null) userStore.efficacyScore = me.efficacy_score
    if (me.role) userStore.role = me.role.toLowerCase()
    if (me.avatar !== undefined) userStore.avatar = me.avatar || ''
    if (me.growth_points != null) userStore.growthPoints = me.growth_points
  }

  if (deviceRes.status === 'fulfilled' && deviceRes.value) {
    const device: any = deviceRes.value
    userStore.wearableData = {
      hr: device.heart_rate ?? device.hr,
      steps: device.steps,
      sleep_hours: device.sleep_hours,
      hrv: device.hrv,
    }
  }

  await loadFocusDomains()
})

function goTo(name: string) {
  router.push({ name })
}

function handleLogout() {
  showConfirmDialog({
    title: '确认退出',
    message: '退出后需要重新登录，确定退出吗？',
  }).then(() => {
    userStore.logout()
  }).catch(() => {})
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;

  .user-meta-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
  }

  .role-tag {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 10px;
    color: #fff;
    background: #10b981;
  }
  .role--observer { background: #f59e0b; }
  .role--grower   { background: #10b981; }
  .role--sharer   { background: #7c3aed; }
  .role--coach    { background: #3b82f6; }
  .role--promoter { background: #6366f1; }

  .growth-pts {
    font-size: $font-size-sm;
    color: #d97706;
    font-weight: 500;
  }

  .user-id {
    font-size: $font-size-sm;
    color: $text-color-secondary;
  }

  .efficacy-badge {
    padding: 4px 12px;
    border-radius: 16px;
    font-size: $font-size-sm;
    font-weight: 500;
  }
}

.wearable-card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }

  .data-value {
    font-size: $font-size-lg;
    font-weight: bold;
    color: $text-color;
  }

  .data-label {
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }
}

.menu-card {
  padding: 0;

  :deep(.van-cell-group) {
    background-color: transparent;
  }

  :deep(.van-cell) {
    padding: $spacing-md;
  }
}

.logout-btn {
  margin-top: $spacing-md;
}

// ────── 关注领域卡片（原则二） ──────
.focus-card {
  .focus-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;

    .focus-title {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: $font-size-lg;
      font-weight: 600;
      color: $text-color;
    }

    .focus-hint {
      font-size: $font-size-xs;
      color: $text-color-placeholder;
    }
  }

  .focus-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;

    .focus-tag {
      cursor: pointer;
      transition: all 0.2s;
      border-radius: 16px;
      padding: 4px 14px;
      font-size: $font-size-sm;

      &.active {
        transform: scale(1.05);
        box-shadow: 0 2px 6px rgba(7, 193, 96, 0.25);
      }
    }
  }

  .focus-tip {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: $font-size-xs;
    color: $text-color-placeholder;
    line-height: 1.4;
  }
}

.version-info {
  text-align: center;
  font-size: $font-size-xs;
  color: $text-color-placeholder;
  margin-top: $spacing-lg;
  padding-bottom: $spacing-lg;
}
</style>
