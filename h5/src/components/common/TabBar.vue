<template>
  <van-tabbar v-model="active" route>
    <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
    <van-tabbar-item icon="chat-o" to="/chat">对话</van-tabbar-item>
    <van-tabbar-item icon="bookmark-o" to="/learn">学习</van-tabbar-item>
    <van-tabbar-item icon="todo-list-o" to="/tasks">任务</van-tabbar-item>
    <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const active = ref(0)
</script>

<style lang="scss" scoped>
</style>
