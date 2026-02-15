<!--
  App.vue — 根组件
  只负责渲染 router-view
-->

<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#2d8e69', borderRadius: 8 } }">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
</script>
