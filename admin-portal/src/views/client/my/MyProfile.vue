<template>
  <div class="personal-center">
    <!-- 顶栏 -->
    <div class="center-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>个人中心</h2>
      <button class="logout-btn" @click="doLogout">退出登录</button>
    </div>

    <!-- 个人健康档案 -->
    <div class="panel" :class="{ open: openMap.profile }">
      <div class="panel-bar" @click="toggle('profile')">
        <span class="panel-icon">📋</span>
        <span class="panel-name">个人健康档案</span>
        <span class="panel-desc">头像·基本信息·病程·用药·过敏·紧急联系人</span>
        <span class="arrow" :class="{ expanded: openMap.profile }">▾</span>
      </div>
      <div v-show="openMap.profile" class="panel-body">
        <PersonalHealthProfile :embedded="true" />
      </div>
    </div>

    <!-- 我的分享 (L3 分享者+) -->
    <div v-if="level >= 3" class="panel" :class="{ open: openMap.contributions }">
      <div class="panel-bar" @click="toggle('contributions')">
        <span class="panel-icon">📝</span>
        <span class="panel-name">我的分享</span>
        <span class="panel-desc">等级进度·投稿记录·同道者</span>
        <span class="arrow" :class="{ expanded: openMap.contributions }">▾</span>
      </div>
      <div v-show="openMap.contributions" class="panel-body">
        <MyContributions />
      </div>
    </div>

    <!-- 我的权益 (L3 分享者+) -->
    <div v-if="level >= 3" class="panel" :class="{ open: openMap.benefits }">
      <div class="panel-bar" @click="toggle('benefits')">
        <span class="panel-icon">🎁</span>
        <span class="panel-name">我的权益</span>
        <span class="panel-desc">当前权益·积分指南·晋级条件</span>
        <span class="arrow" :class="{ expanded: openMap.benefits }">▾</span>
      </div>
      <div v-show="openMap.benefits" class="panel-body">
        <MyBenefits />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { PersonalHealthProfile, MyContributions, MyBenefits } from '@/components/health'
import { useCurrentUser } from '@/composables/useCurrentUser'

const { handleLogout } = useCurrentUser()
const doLogout = () => handleLogout()

const level = parseInt(localStorage.getItem('admin_level') || '0', 10)

const openMap = reactive<Record<string, boolean>>({
  profile: true,
  contributions: false,
  benefits: false,
})

function toggle(key: string) {
  openMap[key] = !openMap[key]
}
</script>

<style scoped>
.personal-center {
  max-width: 900px;
  margin: 0 auto;
  padding: 16px;
}

.center-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.center-header h2 {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}
.back-btn, .logout-btn {
  padding: 6px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.logout-btn {
  color: #dc2626;
  border-color: #dc2626;
}
.logout-btn:hover {
  background: #fef2f2;
}

/* Panels */
.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.panel.open {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.panel-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.panel-bar:hover {
  background: #f9fafb;
}

.panel-icon {
  font-size: 22px;
  flex-shrink: 0;
}
.panel-name {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}
.panel-desc {
  flex: 1;
  font-size: 12px;
  color: #9ca3af;
  margin-left: 4px;
}
.arrow {
  font-size: 16px;
  color: #9ca3af;
  transition: transform 0.2s;
  flex-shrink: 0;
}
.arrow.expanded {
  transform: rotate(180deg);
}

.panel-body {
  padding: 0 20px 20px;
  border-top: 1px solid #f3f4f6;
}
</style>
