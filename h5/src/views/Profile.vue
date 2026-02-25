<template>
  <div class="page-container">
    <van-nav-bar title="个人中心" />

    <div class="page-content">
      <!-- 用户信息卡片 -->
      <div class="user-card card">
        <div class="user-avatar">
          <van-icon name="user-circle-o" size="64" color="#1989fa" />
        </div>
        <div class="user-info">
          <h2>{{ userStore.name }}</h2>
          <p class="user-id">ID: {{ userStore.userId }}</p>
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
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { showConfirmDialog } from 'vant'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/api/index'
import TabBar from '@/components/common/TabBar.vue'
import { APP_VERSION } from '@/config'

const router = useRouter()
const appVersion = APP_VERSION
const userStore = useUserStore()

onMounted(async () => {
  // 刷新用户信息
  try {
    const me: any = await api.get('/api/v1/auth/me')
    if (me.username) userStore.name = me.username
    if (me.id) userStore.userId = me.id
    if (me.efficacy_score != null) userStore.efficacyScore = me.efficacy_score
  } catch { /* 使用缓存 */ }

  // 加载穿戴设备摘要
  try {
    const device: any = await api.get('/api/v1/mp/device/dashboard/today')
    if (device) {
      userStore.wearableData = {
        hr: device.heart_rate ?? device.hr,
        steps: device.steps,
        sleep_hours: device.sleep_hours,
        hrv: device.hrv,
      }
    }
  } catch { /* 使用缓存 */ }
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
  align-items: center;
  gap: $spacing-md;

  .user-avatar {
    flex-shrink: 0;
  }

  .user-info {
    flex: 1;

    h2 {
      font-size: $font-size-xl;
      margin-bottom: 4px;
    }

    .user-id {
      font-size: $font-size-sm;
      color: $text-color-secondary;
    }
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

.version-info {
  text-align: center;
  font-size: $font-size-xs;
  color: $text-color-placeholder;
  margin-top: $spacing-lg;
  padding-bottom: $spacing-lg;
}
</style>
