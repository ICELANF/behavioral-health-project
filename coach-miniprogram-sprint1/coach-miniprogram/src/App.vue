<script setup lang="ts">
import { onLaunch, onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onLaunch(() => {
  // App 启动：从本地恢复登录状态
  userStore.restoreFromStorage()
})

onShow(() => {
  // App 从后台唤起：静默刷新用户信息（积分/级别可能有变化）
  if (userStore.isLoggedIn) {
    userStore.refreshUserInfo().catch(() => {})
  }
})
</script>
