<template>
  <div class="profile-page">
    <div class="content">
      <!-- Profile header -->
      <div class="profile-hero fu">
        <div class="avatar">👦</div>
        <div class="profile-info">
          <h3>{{ store.userName }}同学</h3>
          <p>课题参与者 · 干预组</p>
        </div>
        <div class="profile-badge">成长者</div>
      </div>

      <!-- Basic info -->
      <div class="card fu fu-1">
        <div class="card-title">📋 基本档案</div>
        <div v-for="[k, v] in profileItems" :key="k" class="info-row">
          <span class="info-key">{{ k }}</span>
          <span class="info-val">{{ v }}</span>
        </div>
      </div>

      <!-- Settings -->
      <div class="card fu fu-2">
        <div class="card-title">⚙️ 设置</div>
        <div v-for="m in menus" :key="m.label" class="menu-item">
          <div class="menu-icon" :style="{ background: m.bg }">{{ m.icon }}</div>
          <div class="menu-label">{{ m.label }}</div>
          <div class="menu-arrow">›</div>
        </div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { useVisionStore } from '@/stores/vision'
const store = useVisionStore()

const profileItems: [string, string][] = [
  ['当前等效球镜', '-0.75 D（轻度近视）'],
  ['眼轴长度', '24.2 mm'],
  ['基线检查日期', '2025-09-01'],
  ['下次检查', '2026-03-15'],
  ['监护人', '张女士'],
]

const menus = [
  { icon: '🔔', bg: '#E3F2FD', label: '提醒设置' },
  { icon: '👨‍👩‍👦', bg: '#E8F5E9', label: '家长绑定' },
  { icon: '📤', bg: '#FFF3E0', label: '导出我的数据' },
  { icon: '❓', bg: '#F3E5F5', label: '课题说明与知情同意书' },
]
</script>

<style scoped>
.content { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.profile-hero {
  background: var(--grad-header); border-radius: 18px;
  padding: 20px; display: flex; align-items: center; gap: 14px;
}
.avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: rgba(255,255,255,.25); display: flex;
  align-items: center; justify-content: center;
  font-size: 28px; border: 3px solid rgba(255,255,255,.4);
}
.profile-info h3 { font-size: 16px; font-weight: 700; color: white; }
.profile-info p { font-size: 12px; color: rgba(255,255,255,.8); margin-top: 2px; }
.profile-badge {
  margin-left: auto; background: var(--gold); color: #7A4F00;
  font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 20px;
}
.info-row {
  display: flex; justify-content: space-between;
  padding: 9px 0; border-bottom: 1px solid #F2F7F6; font-size: 13px;
}
.info-key { color: var(--sub); }
.info-val { color: var(--ink); font-weight: 500; }
.menu-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 4px; border-bottom: 1px solid #F2F7F6; cursor: pointer;
}
.menu-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.menu-label { font-size: 14px; color: var(--ink); font-weight: 500; flex: 1; }
.menu-arrow { font-size: 16px; color: var(--sub); }
</style>
