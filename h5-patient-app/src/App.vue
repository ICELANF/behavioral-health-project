<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

onMounted(() => {
  // 应用启动时尝试恢复登录状态
  userStore.checkLoginStatus()
})
</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
  background-color: #f7f8fa;
}
</style>
