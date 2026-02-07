<!--
  专家工作室页面 — 白标客户界面
  路由: /studio/:tenantId
-->
<template>
  <div class="studio" :class="brandClass" :style="brandVars">
    <van-loading v-if="loading" class="studio-loading" size="24px" />

    <template v-else-if="tenant">
      <!-- 品牌头部 -->
      <van-nav-bar :title="tenant.brand_name" left-arrow @click-left="goBack">
        <template #right>
          <span style="font-size:20px">👤</span>
        </template>
      </van-nav-bar>

      <div class="studio-main">
        <!-- 欢迎卡片 -->
        <div class="welcome-card" v-if="tenant.welcome_message">
          <p>{{ tenant.welcome_message }}</p>
        </div>

        <!-- 专家介绍 -->
        <van-cell-group inset class="intro-group">
          <div class="intro-header">
            <span class="intro-avatar">{{ tenant.brand_avatar }}</span>
            <div>
              <div class="intro-name">{{ tenant.expert_title }}</div>
              <div class="intro-credentials">
                <van-tag
                  v-for="cred in (tenant.expert_credentials || []).slice(0, 3)"
                  :key="cred"
                  plain
                  round
                  size="medium"
                  color="#999"
                >
                  {{ cred }}
                </van-tag>
              </div>
            </div>
          </div>
          <p class="intro-text">
            {{ showFullIntro ? tenant.expert_self_intro : truncatedIntro }}
          </p>
          <span
            v-if="tenant.expert_self_intro && tenant.expert_self_intro.length > 80"
            class="link-btn"
            @click="showFullIntro = !showFullIntro"
          >
            {{ showFullIntro ? '收起' : '了解更多' }}
          </span>
        </van-cell-group>

        <!-- AI 助手列表 -->
        <div class="section-title">我的 AI 助手</div>
        <div class="agents-list">
          <van-cell
            v-for="agent in agents"
            :key="agent.agent_id"
            :title="agent.display_name || agentMeta(agent.agent_id).name"
            :label="agent.greeting ? truncate(agent.greeting, 40) : ''"
            is-link
            @click="openChat(agent)"
          >
            <template #icon>
              <span class="agent-icon">{{ agent.display_avatar || agentMeta(agent.agent_id).avatar }}</span>
            </template>
          </van-cell>
        </div>

        <!-- 服务包 -->
        <template v-if="tenant.service_packages && tenant.service_packages.length">
          <div class="section-title">服务方案</div>
          <div class="packages-grid">
            <div
              v-for="pkg in tenant.service_packages"
              :key="pkg.id"
              class="package-card"
              :class="{ 'package-featured': pkg.id === 'premium' }"
            >
              <div class="pkg-name">{{ pkg.name }}</div>
              <div class="pkg-price">
                <span v-if="pkg.price === 0" class="price-free">免费体验</span>
                <template v-else>
                  <span class="price-amount">¥{{ pkg.price }}</span>
                  <span class="price-duration">/ {{ pkg.duration_days }}天</span>
                </template>
              </div>
              <ul class="pkg-features">
                <li v-for="feat in (pkg.features || [])" :key="feat">✓ {{ feat }}</li>
              </ul>
              <van-button
                block
                round
                size="small"
                :type="pkg.price === 0 ? 'default' : 'primary'"
                :color="pkg.price !== 0 ? (tenant.brand_colors?.primary || '#2563EB') : undefined"
              >
                {{ pkg.price === 0 ? '免费体验' : '立即购买' }}
              </van-button>
            </div>
          </div>
        </template>
      </div>

      <!-- 底部导航 -->
      <van-tabbar v-model="activeTab" :active-color="tenant.brand_colors?.primary || '#2563EB'">
        <van-tabbar-item name="home" icon="home-o">首页</van-tabbar-item>
        <van-tabbar-item name="chat" icon="chat-o">对话</van-tabbar-item>
        <van-tabbar-item name="learn" icon="bookmark-o">学习</van-tabbar-item>
        <van-tabbar-item name="me" icon="contact">我的</van-tabbar-item>
      </van-tabbar>
    </template>

    <!-- 未找到 -->
    <van-empty v-else description="工作室不存在或已关闭">
      <van-button round type="primary" size="small" @click="$router.push({ name: 'expert-hub' })">
        返回专家列表
      </van-button>
    </van-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTenantStore, AGENT_META } from '@/stores/tenant'
import type { AgentMapping } from '@/stores/tenant'

const route = useRoute()
const router = useRouter()
const store = useTenantStore()

const showFullIntro = ref(false)
const activeTab = ref('home')
const loading = computed(() => store.loading)
const tenant = computed(() => store.currentTenant)
const agents = computed(() => store.currentAgents)

const brandClass = computed(() => {
  const themeId = tenant.value?.brand_theme_id
  return themeId && themeId !== 'default' ? `theme-${themeId}` : ''
})

const brandVars = computed(() => {
  const colors = tenant.value?.brand_colors
  if (!colors) return {}
  return {
    '--brand-primary': colors.primary,
    '--brand-accent': colors.accent,
    '--brand-bg': colors.bg,
    '--brand-text': colors.text,
  } as any
})

const truncatedIntro = computed(() => {
  const intro = tenant.value?.expert_self_intro || ''
  return intro.length > 80 ? intro.slice(0, 80) + '...' : intro
})

function agentMeta(agentId: string) {
  return AGENT_META[agentId] || { name: agentId, avatar: '🤖' }
}

function truncate(str: string, len: number) {
  return str.length > len ? str.slice(0, len) + '...' : str
}

function openChat(agent: AgentMapping) {
  router.push({
    name: 'chat',
    query: {
      tenant: route.params.tenantId as string,
      agent: agent.agent_id,
    },
  })
}

function goBack() {
  router.push({ name: 'expert-hub' })
}

onMounted(() => {
  const tid = route.params.tenantId as string
  if (tid) {
    store.fetchTenantPublic(tid)
  }
})

onUnmounted(() => {
  store.clearBrandTheme()
})
</script>

<style scoped>
.studio {
  min-height: 100vh;
  background: var(--brand-bg, #f7f8fa);
  padding-bottom: 60px;
}

.studio-loading {
  display: flex;
  justify-content: center;
  padding-top: 40vh;
}

.studio-main {
  padding: 12px 16px;
}

.welcome-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
  border-left: 4px solid var(--brand-primary, #3b82f6);
  font-size: 13px;
  line-height: 1.6;
  color: #646566;
}

.intro-group {
  padding: 16px !important;
  margin-bottom: 16px;
}

.intro-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.intro-avatar { font-size: 32px; }

.intro-name {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.intro-credentials {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.intro-text {
  font-size: 13px;
  color: #969799;
  line-height: 1.6;
}

.link-btn {
  color: var(--brand-primary, #3b82f6);
  font-size: 13px;
  cursor: pointer;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  margin: 16px 0 10px;
}

.agents-list {
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 8px;
}

.agent-icon {
  font-size: 24px;
  margin-right: 10px;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.package-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #ebedf0;
}

.package-featured {
  border-color: var(--brand-primary, #3b82f6);
  box-shadow: 0 0 0 1px var(--brand-primary, #3b82f6);
}

.pkg-name {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 6px;
}

.price-free {
  color: var(--brand-primary, #3b82f6);
  font-weight: 600;
  font-size: 14px;
}

.price-amount {
  font-size: 20px;
  font-weight: 700;
  color: var(--brand-primary, #323233);
}

.price-duration {
  font-size: 12px;
  color: #969799;
}

.pkg-features {
  list-style: none;
  padding: 0;
  margin: 8px 0 12px;
}

.pkg-features li {
  font-size: 12px;
  color: #969799;
  padding: 2px 0;
}
</style>
