<template>
  <div class="profile-page">
    <div class="header">
      <div class="avatar-ring">{{ initials }}</div>
      <div class="profile-name">{{ store.profile?.display_name || '专家' }}</div>
      <div class="profile-sub">{{ store.profile?.specialty || '专科' }}</div>
      <div style="display:flex;gap:6px;margin-top:8px;justify-content:center;flex-wrap:wrap">
        <span v-for="t in (store.profile?.domain_tags || []).slice(0,4)" :key="t"
          class="chip chip--teal">{{ t }}</span>
      </div>
    </div>
    <div class="content">
      <div class="card fu">
        <div class="card-title">智伴信息</div>
        <div class="info-row">
          <span class="info-label">智伴名称</span>
          <span class="info-val">{{ store.config?.companion_name || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">沟通风格</span>
          <span class="info-val">{{ store.config?.comm_style || '默认' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">自动开方</span>
          <span class="info-val">{{ store.config?.auto_rx_enabled ? '开启' : '关闭' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">中医权重</span>
          <span class="info-val">{{ store.profile?.tcm_weight ?? '-' }}</span>
        </div>
      </div>

      <div class="card fu fu-1">
        <div class="menu-item" @click="router.push('/config')">智伴配置</div>
        <div class="menu-item" @click="router.push('/knowledge/health')">知识库健康度</div>
        <div class="menu-item" @click="router.push('/onboarding')">重新初始化 MVEP</div>
        <div class="menu-item" style="color:var(--xzb-red)" @click="logout">退出登录</div>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useExpertStore } from '@/stores/expert'

const router = useRouter()
const store = useExpertStore()

const initials = computed(() => (store.profile?.display_name || 'X').slice(0, 1))

function logout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}

onMounted(() => { store.loadAll() })
</script>

<style scoped>
.header {
  background: var(--grad-header); color: white;
  padding: 32px 20px 24px; text-align: center;
}
.avatar-ring {
  width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 12px;
  background: rgba(255,255,255,.2); border: 2px solid rgba(255,255,255,.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 900;
}
.profile-name { font-size: 20px; font-weight: 900; }
.profile-sub { font-size: 13px; opacity: .8; margin-top: 2px; }
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.info-row {
  display: flex; justify-content: space-between; padding: 10px 0;
  border-bottom: 1px dashed var(--border); font-size: 13px;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: var(--sub); font-weight: 600; }
.info-val { color: var(--ink); font-weight: 700; }
.menu-item {
  padding: 14px 0; border-bottom: 1px dashed var(--border);
  font-size: 14px; font-weight: 600; cursor: pointer;
}
.menu-item:last-child { border-bottom: none; }
</style>
