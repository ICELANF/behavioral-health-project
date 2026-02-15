<template>
  <div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 16px;">
    <div style="font-size: 72px; opacity: 0.2;">404</div>
    <h2 style="margin: 0; font-size: 20px; color: #333;">页面未找到</h2>
    <p style="color: #999;">您访问的页面不存在</p>
    <a-button type="primary" @click="$router.push('/')">返回首页</a-button>
  </div>
</template>
<script setup lang="ts">
</script>
