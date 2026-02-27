<template>
  <div class="page-shell">
    <!-- 顶部安全区 -->
    <div class="safe-top" />

    <!-- 导航栏 -->
    <van-nav-bar
      v-if="showNavBar"
      :title="title"
      :left-arrow="shouldShowBack"
      @click-left="onBack"
    >
      <template #right v-if="$slots['header-right']">
        <slot name="header-right" />
      </template>
    </van-nav-bar>

    <!-- 导航栏下方额外插槽 -->
    <slot name="header-extra" />

    <!-- 可滚动内容区 -->
    <div
      class="page-shell__body"
      :class="{
        'page-shell__body--no-pad': noPadding,
        'page-shell__body--with-tabbar': showTabBar
      }"
    >
      <slot />
    </div>

    <!-- 底部 TabBar -->
    <TabBar v-if="showTabBar" />

    <!-- 底部安全区 (非 TabBar 页面) -->
    <div v-if="!showTabBar" class="safe-bottom-spacer" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import TabBar from '@/components/common/TabBar.vue'

const props = withDefaults(defineProps<{
  title?: string
  showBack?: boolean | null
  showNavBar?: boolean
  showTabBar?: boolean
  noPadding?: boolean
}>(), {
  title: '',
  showBack: null,
  showNavBar: true,
  showTabBar: false,
  noPadding: false,
})

const router = useRouter()
const route = useRoute()

// Tab 页面路径 — 这些页面默认不显示返回键
const TAB_PATHS = ['/', '/home', '/chat', '/learn', '/tasks', '/profile']

const shouldShowBack = computed(() => {
  if (props.showBack !== null) return props.showBack
  // 自动检测: Tab 页 = false, 其他 = true
  return !TAB_PATHS.some(p => route.path === p || route.path.startsWith(p + '/'))
})

function onBack() {
  if (shouldShowBack.value) {
    router.back()
  }
}
</script>

<style scoped>
.page-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg, #f8fafc);
}

.safe-top {
  padding-top: env(safe-area-inset-top, 0px);
}

.page-shell__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.page-shell__body--no-pad {
  padding: 0;
}

.page-shell__body--with-tabbar {
  padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
}

.safe-bottom-spacer {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
</style>
