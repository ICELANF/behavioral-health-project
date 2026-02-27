<template>
  <div class="tabbar-wrap">
    <!-- Center FAB button (overlays on tabbar) -->
    <div class="center-fab" @click="showHub = true">
      <div class="fab-inner">
        <van-icon name="plus" size="22" color="#fff" />
      </div>
      <div class="fab-label">记录</div>
    </div>

    <van-tabbar v-model="activeTab" @change="onTabChange">
      <van-tabbar-item icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item icon="chat-o">对话</van-tabbar-item>
      <van-tabbar-item icon="bookmark-o">学习</van-tabbar-item>
      <van-tabbar-item icon="todo-list-o">任务</van-tabbar-item>
      <van-tabbar-item icon="user-o">我的</van-tabbar-item>
    </van-tabbar>

    <!-- QuickInputHub popup -->
    <QuickInputHub v-model:show="showHub" @submitted="onSubmitted" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QuickInputHub from '@/components/health/QuickInputHub.vue'

const route = useRoute()
const router = useRouter()
const showHub = ref(false)

const TAB_ROUTES = ['/', '/chat', '/learn', '/tasks', '/profile']

function getActiveTab(path: string): number {
  if (path === '/' || path.startsWith('/home/') || path === '/dashboard') return 0
  if (path.startsWith('/chat')) return 1
  if (path.startsWith('/learn')) return 2
  if (path.startsWith('/tasks')) return 3
  if (path.startsWith('/profile')) return 4
  return 0
}

const activeTab = ref(getActiveTab(route.path))

watch(() => route.path, (p) => { activeTab.value = getActiveTab(p) })

function onTabChange(idx: number) {
  router.push(TAB_ROUTES[idx])
}

const emit = defineEmits<{
  (e: 'data-submitted'): void
}>()

const onSubmitted = () => {
  emit('data-submitted')
}
</script>

<style lang="scss" scoped>
.tabbar-wrap {
  position: relative;
}

/* FAB floats above the middle "学习" tab */
.center-fab {
  position: fixed;
  bottom: 44px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1001;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.fab-inner {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(16, 185, 129, 0.4);
  transition: transform 0.15s;
}

.fab-inner:active {
  transform: scale(0.9);
}

.fab-label {
  font-size: 10px;
  color: #10b981;
  margin-top: 1px;
  font-weight: 500;
}
</style>
