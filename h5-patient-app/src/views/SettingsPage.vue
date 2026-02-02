<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAssessmentStore } from '@/stores/assessment'
import { showConfirmDialog, showSuccessToast, showDialog } from 'vant'

const router = useRouter()
const userStore = useUserStore()
const assessmentStore = useAssessmentStore()

// 设置项
const notificationEnabled = ref(true)
const autoBackup = ref(true)
const reminderTime = ref('09:00')
const showReminderPicker = ref(false)

/**
 * 切换通知
 */
const onNotificationChange = (value: boolean) => {
  showSuccessToast(value ? '已开启通知' : '已关闭通知')
}

/**
 * 切换自动备份
 */
const onAutoBackupChange = (value: boolean) => {
  showSuccessToast(value ? '已开启自动备份' : '已关闭自动备份')
}

/**
 * 确认提醒时间
 */
const onConfirmTime = (value: string) => {
  reminderTime.value = value
  showReminderPicker.value = false
  showSuccessToast(`已设置提醒时间为 ${value}`)
}

/**
 * 清除缓存数据
 */
const clearCache = () => {
  showConfirmDialog({
    title: '清除缓存',
    message: '确定要清除所有缓存数据吗？这不会删除您的评估记录。'
  })
    .then(() => {
      // 清除缓存但保留用户数据和评估历史
      showSuccessToast('缓存已清除')
    })
    .catch(() => {
      // 取消
    })
}

/**
 * 清除所有数据
 */
const clearAllData = () => {
  showConfirmDialog({
    title: '清除所有数据',
    message: '警告：这将删除所有评估记录和设置，且不可恢复！',
    confirmButtonText: '确定删除',
    confirmButtonColor: '#ee0a24'
  })
    .then(() => {
      assessmentStore.clearHistory()
      assessmentStore.clearCurrent()
      showSuccessToast('所有数据已清除')
    })
    .catch(() => {
      // 取消
    })
}

/**
 * 关于应用
 */
const showAbout = () => {
  showDialog({
    title: '关于应用',
    message: `
      行为健康评估平台 v0.1.0

      这是一个基于AI的行为健康评估系统，
      通过分析您的生理和行为数据，
      提供个性化的健康建议。

      © 2026 行为健康团队
    `,
    confirmButtonText: '我知道了'
  })
}

/**
 * 用户协议
 */
const showAgreement = () => {
  showDialog({
    title: '用户协议',
    message: `
      1. 隐私保护
      我们重视您的隐私，所有数据仅用于健康评估。

      2. 数据安全
      您的数据经过加密存储和传输。

      3. 免责声明
      本应用提供的建议仅供参考，不能替代专业医疗诊断。

      4. 使用限制
      请勿滥用本应用，遵守使用规范。
    `,
    confirmButtonText: '我已阅读'
  })
}

/**
 * 隐私政策
 */
const showPrivacy = () => {
  showDialog({
    title: '隐私政策',
    message: `
      信息收集：
      - 基本信息（用户名、邮箱）
      - 健康数据（血糖、HRV等）
      - 使用日志

      信息使用：
      - 提供健康评估服务
      - 改进算法和建议
      - 数据统计分析

      信息保护：
      - 数据加密存储
      - 严格访问控制
      - 不会向第三方出售数据
    `,
    confirmButtonText: '我知道了'
  })
}

/**
 * 意见反馈
 */
const showFeedback = () => {
  showDialog({
    title: '意见反馈',
    message: '感谢您的反馈！请发送邮件至 feedback@health.com 或在应用内留言。',
    confirmButtonText: '好的'
  })
}

/**
 * 退出登录
 */
const handleLogout = () => {
  showConfirmDialog({
    title: '确认退出',
    message: '确定要退出登录吗？'
  })
    .then(async () => {
      await userStore.logout()
      router.replace('/login')
    })
    .catch(() => {
      // 取消
    })
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="settings-page page-container">
    <van-nav-bar title="个人设置" left-arrow @click-left="goBack" />

    <div class="content-wrapper">
      <!-- 个人信息 -->
      <van-cell-group title="个人信息" inset>
        <van-cell title="用户名" :value="userStore.user?.username" />
        <van-cell title="邮箱" :value="userStore.user?.email" />
        <van-cell title="角色" :value="userStore.userRole === 'patient' ? '患者' :
                                       userStore.userRole === 'coach' ? '教练' : '管理员'" />
        <van-cell title="注册时间" :value="userStore.user?.created_at ? new Date(userStore.user.created_at).toLocaleDateString('zh-CN') : '-'" />
      </van-cell-group>

      <!-- 通知设置 -->
      <van-cell-group title="通知设置" inset>
        <van-cell title="评估提醒">
          <template #right-icon>
            <van-switch
              v-model="notificationEnabled"
              size="24"
              @change="onNotificationChange"
            />
          </template>
        </van-cell>
        <van-cell
          title="提醒时间"
          is-link
          :value="reminderTime"
          @click="showReminderPicker = true"
        />
        <van-cell title="自动备份">
          <template #right-icon>
            <van-switch
              v-model="autoBackup"
              size="24"
              @change="onAutoBackupChange"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 数据管理 -->
      <van-cell-group title="数据管理" inset>
        <van-cell
          title="评估次数"
          :value="`${assessmentStore.history.length}次`"
        />
        <van-cell
          title="清除缓存"
          is-link
          @click="clearCache"
        />
        <van-cell
          title="清除所有数据"
          is-link
          @click="clearAllData"
          title-class="danger-text"
        />
      </van-cell-group>

      <!-- 关于 -->
      <van-cell-group title="关于" inset>
        <van-cell title="应用版本" value="v0.1.0 Beta" />
        <van-cell title="关于应用" is-link @click="showAbout" />
        <van-cell title="用户协议" is-link @click="showAgreement" />
        <van-cell title="隐私政策" is-link @click="showPrivacy" />
        <van-cell title="意见反馈" is-link @click="showFeedback" />
      </van-cell-group>

      <!-- 退出登录 -->
      <div class="logout-section">
        <van-button
          type="danger"
          block
          round
          @click="handleLogout"
        >
          退出登录
        </van-button>
      </div>

      <!-- 时间选择器 -->
      <van-popup v-model:show="showReminderPicker" position="bottom">
        <van-time-picker
          :model-value="reminderTime"
          title="选择提醒时间"
          @confirm="onConfirmTime"
          @cancel="showReminderPicker = false"
        />
      </van-popup>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content-wrapper {
  padding: 16px;
  padding-bottom: 32px;
}

.logout-section {
  margin-top: 24px;
  padding: 0 16px;
}

:deep(.danger-text) {
  color: #ee0a24;
}
</style>
