<!--
  专家Hub页面 — 公开的专家工作室目录
  路由: /expert-hub
-->
<template>
  <div class="expert-hub">
    <van-nav-bar title="专家工作室" />

    <div class="hub-subtitle">
      {{ activeTenants.length }} 位专家 · {{ totalClients }} 位客户正在服务中
    </div>

    <van-search
      v-model="searchQuery"
      placeholder="搜索专家、专长..."
      shape="round"
    />

    <van-loading v-if="loading" class="hub-loading" size="24px" vertical>
      加载中...
    </van-loading>

    <div v-else class="hub-grid">
      <div
        v-for="expert in filteredExperts"
        :key="expert.id"
        class="expert-card"
        :style="{ borderColor: (expert.brand_colors?.primary || '#2563EB') + '30' }"
        @click="enterStudio(expert.id)"
      >
        <div class="card-avatar" :style="{ background: expert.brand_colors?.primary || '#2563EB' }">
          {{ expert.brand_avatar }}
        </div>
        <div class="card-body">
          <h3 class="card-name">{{ expert.brand_name }}</h3>
          <p class="card-title">{{ expert.expert_title }}</p>
          <p class="card-tagline">{{ expert.brand_tagline }}</p>
          <div class="card-tags">
            <van-tag
              v-for="spec in (expert.expert_specialties || []).slice(0, 3)"
              :key="spec"
              plain
              round
              size="medium"
              :color="expert.brand_colors?.accent || '#3B82F6'"
            >
              {{ spec }}
            </van-tag>
          </div>
          <div class="card-meta">
            <span>🤖 {{ (expert.enabled_agents || []).length }} 个AI助手</span>
            <span>👥 {{ expert.client_count_active }} 位客户</span>
          </div>
        </div>
        <van-button
          block
          round
          :color="expert.brand_colors?.primary || '#2563EB'"
          size="small"
          class="enter-btn"
        >
          进入工作室
        </van-button>
      </div>
    </div>

    <van-empty v-if="!loading && filteredExperts.length === 0" description="暂无匹配的专家工作室" />

    <!-- 申请入驻入口 -->
    <div class="apply-entry">
      <div class="apply-card" @click="router.push('/expert-register')">
        <div class="apply-icon">🚀</div>
        <div class="apply-text">
          <h4>成为入驻专家</h4>
          <p>开通您的专属工作室，获得 AI Agent 助手</p>
        </div>
        <van-icon name="arrow" color="#969799" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTenantStore } from '@/stores/tenant'
import type { ExpertTenantSummary } from '@/stores/tenant'

const router = useRouter()
const store = useTenantStore()

const searchQuery = ref('')
const loading = computed(() => store.loading)
const activeTenants = computed(() => store.activeTenants)
const totalClients = computed(() => store.totalHubClients)

const filteredExperts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return activeTenants.value
  return activeTenants.value.filter((t: ExpertTenantSummary) =>
    t.brand_name.toLowerCase().includes(q) ||
    t.expert_title?.toLowerCase().includes(q) ||
    (t.expert_specialties || []).some((s: string) => s.toLowerCase().includes(q))
  )
})

function enterStudio(tenantId: string) {
  router.push({ name: 'expert-studio', params: { tenantId } })
}

onMounted(() => {
  store.fetchHub()
})
</script>

<style scoped>
.expert-hub {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 16px;
}

.hub-subtitle {
  text-align: center;
  font-size: 13px;
  color: #969799;
  padding: 8px 0 4px;
}

.hub-loading {
  padding: 60px 0;
}

.hub-grid {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.expert-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  flex-direction: column;
}

.card-avatar {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  margin-bottom: 12px;
}

.card-body { flex: 1; }

.card-name {
  font-size: 17px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 4px;
}

.card-title {
  font-size: 12px;
  color: #969799;
  margin-bottom: 6px;
}

.card-tagline {
  font-size: 13px;
  color: #646566;
  margin-bottom: 10px;
  line-height: 1.5;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #969799;
  margin-bottom: 14px;
}

.enter-btn {
  margin-top: auto;
}

.apply-entry {
  padding: 16px;
}

.apply-card {
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  border: 1px solid #BFDBFE;
  border-radius: 14px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
}

.apply-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.apply-text {
  flex: 1;
}

.apply-text h4 {
  font-size: 15px;
  font-weight: 600;
  color: #1E40AF;
  margin: 0 0 4px;
}

.apply-text p {
  font-size: 12px;
  color: #6B7280;
  margin: 0;
}
</style>
