<template>
  <div class="dashboard">
    <div class="header">
      <div class="header-top">
        <div class="avatar-ring">{{ initials }}</div>
        <div style="flex:1">
          <div class="header-name">{{ store.profile?.display_name || '专家' }}</div>
          <div class="header-sub">{{ store.config?.companion_name || '行诊智伴' }} &middot; {{ store.profile?.specialty || '专科' }}</div>
        </div>
        <button class="online-btn" :class="{ on: isOnline }" @click="goOnline">
          {{ isOnline ? '在线' : '离线' }}
        </button>
      </div>
    </div>

    <div class="content">
      <div class="stat-row fu">
        <div class="stat-card" @click="router.push('/knowledge/pending')">
          <div class="stat-num" style="color:var(--xzb-amber)">{{ db?.pending_knowledge_confirmations || 0 }}</div>
          <div class="stat-label">待确认知识</div>
        </div>
        <div class="stat-card" @click="router.push('/rx/templates')">
          <div class="stat-num" style="color:var(--xzb-blue)">{{ db?.pending_rx_reviews || 0 }}</div>
          <div class="stat-label">待审处方</div>
        </div>
        <div class="stat-card" @click="router.push('/chat')">
          <div class="stat-num" style="color:var(--xzb-green)">{{ db?.active_seekers || 0 }}</div>
          <div class="stat-label">活跃求助者</div>
        </div>
        <div class="stat-card" @click="router.push('/knowledge/health')">
          <div class="stat-num" style="color:var(--xzb-primary)">{{ healthPct }}%</div>
          <div class="stat-label">知识库健康</div>
        </div>
      </div>

      <div class="card fu fu-1">
        <div class="card-title">快捷操作</div>
        <div class="action-grid">
          <div class="action-item" @click="router.push('/seekers')">
            <div class="action-icon" style="background:var(--xzb-primary-l);color:var(--xzb-primary)">S</div>
            <div class="action-text">服务对象</div>
          </div>
          <div class="action-item" @click="router.push('/knowledge/upload')">
            <div class="action-icon" style="background:var(--xzb-gold-l);color:var(--xzb-gold)">+</div>
            <div class="action-text">上传知识</div>
          </div>
          <div class="action-item" @click="router.push('/faq')">
            <div class="action-icon" style="background:#EEF4FF;color:var(--xzb-blue)">Q</div>
            <div class="action-text">问题库</div>
          </div>
          <div class="action-item" @click="router.push('/rx/templates')">
            <div class="action-icon" style="background:#F3F0FF;color:var(--xzb-purple)">Rx</div>
            <div class="action-text">处方模板</div>
          </div>
        </div>
        <div class="action-grid" style="margin-top:8px">
          <div class="action-item" @click="router.push('/knowledge/rules')">
            <div class="action-icon" style="background:var(--xzb-gold-l);color:var(--xzb-gold)">R</div>
            <div class="action-text">规则编辑</div>
          </div>
          <div class="action-item" @click="router.push('/chat')">
            <div class="action-icon" style="background:var(--xzb-primary-l);color:var(--xzb-primary)">M</div>
            <div class="action-text">对话监控</div>
          </div>
          <div class="action-item" @click="router.push('/med-circle')">
            <div class="action-icon" style="background:#EEF4FF;color:var(--xzb-blue)">H</div>
            <div class="action-text">医道汇</div>
          </div>
          <div class="action-item" @click="router.push('/config')">
            <div class="action-icon" style="background:#F3F0FF;color:var(--xzb-purple)">C</div>
            <div class="action-text">智伴配置</div>
          </div>
        </div>
      </div>

      <div class="card fu fu-2">
        <div class="card-title">
          知识库健康度
          <span class="chip chip--teal">{{ healthPct }}%</span>
        </div>
        <div class="health-bar">
          <div class="health-fill" :style="{ width: healthPct + '%' }" />
        </div>
        <div style="font-size:12px;color:var(--sub);margin-top:8px">
          覆盖率反映已确认知识占比，建议保持 80% 以上。
        </div>
      </div>

      <div class="card fu fu-2" v-if="!store.profile" style="text-align:center;padding:24px">
        <div style="font-size:40px;margin-bottom:12px">XZB</div>
        <div style="font-size:15px;font-weight:700;margin-bottom:6px">欢迎使用行诊智伴工作站</div>
        <div style="font-size:13px;color:var(--sub);line-height:1.6;margin-bottom:16px">
          完成 10 分钟 MVEP 初始化，让 AI 智伴学习您的专业风格和知识体系。
        </div>
        <button class="btn-gold" @click="router.push('/onboarding')">开始 MVEP 初始化</button>
      </div>
    </div>
    <div style="height:70px" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useExpertStore } from '@/stores/expert'
import { setOnline } from '@/api/xzb'

const router = useRouter()
const store = useExpertStore()
const isOnline = ref(false)

const db = computed(() => store.dashboard)
const healthPct = computed(() => Math.round((db.value?.knowledge_health_score || 0) * 100))
const initials = computed(() => {
  const name = store.profile?.display_name || 'X'
  return name.slice(0, 1)
})

async function goOnline() {
  try {
    await setOnline()
    isOnline.value = true
  } catch { /* ignore */ }
}

onMounted(() => { store.loadAll() })
</script>

<style scoped>
.header {
  background: var(--grad-header); color: white; padding: 20px 16px 16px;
}
.header-top { display: flex; align-items: center; gap: 12px; }
.avatar-ring {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,.2); border: 2px solid rgba(255,255,255,.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 900;
}
.header-name { font-size: 17px; font-weight: 800; }
.header-sub { font-size: 12px; opacity: .8; margin-top: 2px; }
.online-btn {
  padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700;
  border: 1.5px solid rgba(255,255,255,.4); background: transparent; color: white;
  cursor: pointer; transition: all .2s;
}
.online-btn.on { background: var(--xzb-green); border-color: var(--xzb-green); }
.content { padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.stat-card {
  background: var(--card); border-radius: var(--radius-sm); padding: 14px 8px;
  text-align: center; box-shadow: var(--shadow-card); cursor: pointer;
}
.stat-num { font-size: 24px; font-weight: 900; }
.stat-label { font-size: 10px; color: var(--sub); margin-top: 4px; font-weight: 600; }
.action-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.action-item { text-align: center; cursor: pointer; }
.action-icon {
  width: 44px; height: 44px; border-radius: 12px; margin: 0 auto 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 900;
}
.action-text { font-size: 11px; color: var(--ink); font-weight: 600; }
.health-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.health-fill { height: 100%; background: var(--grad-header); border-radius: 4px; transition: width .8s; }
</style>
