<template>
  <div class="tabbar-wrap">
    <!-- Center FAB button (overlays on tabbar) -->
    <div class="center-fab" @click="showHub = true">
      <div class="fab-inner">
        <van-icon name="plus" size="22" color="#fff" />
      </div>
      <div class="fab-label">记录</div>
    </div>

    <van-tabbar v-model="active" route>
      <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
      <van-tabbar-item icon="chat-o" to="/chat">对话</van-tabbar-item>
      <van-tabbar-item icon="bookmark-o" to="/learn">学习</van-tabbar-item>
      <van-tabbar-item icon="todo-list-o" to="/tasks">任务</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
    </van-tabbar>

    <!-- QuickInputHub popup -->
    <QuickInputHub v-model:show="showHub" @submitted="onSubmitted" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import QuickInputHub from '@/components/health/QuickInputHub.vue'

const active = ref(0)
const showHub = ref(false)

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
