<template>
  <div class="min-h-screen bg-slate-50">
    <!-- Top bar -->
    <div class="h-16 bg-gradient-to-r from-slate-700 to-slate-600 flex items-center justify-between px-6 text-white shadow-xl">
      <div class="flex items-center gap-4">
        <span class="font-bold text-lg">主动健康·吃动守恒</span>
        <a-tag color="green" class="!text-xs">v16.2.0</a-tag>
      </div>
      <div class="flex items-center gap-4">
        <a-tabs v-model:activeKey="activeTab" class="expert-nav-tabs" size="small">
          <a-tab-pane key="audit" tab="待审队列" />
          <a-tab-pane key="trace" tab="决策回溯" />
          <a-tab-pane key="brain" tab="规则引擎" />
          <a-tab-pane key="profile" tab="个人档案" />
          <a-tab-pane key="contributions" tab="我的分享" />
          <a-tab-pane key="benefits" tab="我的权益" />
        </a-tabs>
        <UserAvatarPopover :size="36" theme="dark" />
      </div>
    </div>

    <!-- Content -->
    <div class="flex h-[calc(100vh-64px)]">
      <!-- Left: Patient queue (only for audit tab) -->
      <div v-if="activeTab === 'audit'" class="w-60 bg-white border-r border-slate-200 overflow-y-auto p-4">
        <div class="mb-3">
          <a-select v-model:value="riskFilter" placeholder="风险等级筛选" allow-clear class="w-full" size="small">
            <a-select-option value="CRITICAL">🔴 CRITICAL</a-select-option>
            <a-select-option value="HIGH">🟠 HIGH</a-select-option>
            <a-select-option value="MEDIUM">🟡 MEDIUM</a-select-option>
            <a-select-option value="LOW">🟢 LOW</a-select-option>
          </a-select>
        </div>
        <div v-for="item in filteredQueue" :key="item.id"
          @click="selectedCase = item"
          class="p-3 rounded-lg mb-2 cursor-pointer transition-all"
          :class="selectedCase?.id === item.id ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50 border border-transparent'"
        >
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" :class="riskColor(item.rawMetrics.riskLevel)" />
            <span class="text-sm font-medium text-slate-900">{{ item.patientId }}</span>
          </div>
          <div class="flex gap-2 mt-1">
            <a-tag :color="riskTagColor(item.rawMetrics.riskLevel)" class="!text-xs">
              {{ item.rawMetrics.riskLevel }}
            </a-tag>
            <span class="text-xs text-slate-400">{{ item.bapsProfile?.stage || '—' }}</span>
          </div>
        </div>
        <a-empty v-if="filteredQueue.length === 0" description="无待审案例" class="mt-8" />
      </div>

      <!-- Right: Detail panel -->
      <div class="flex-1 overflow-hidden">
        <DualSignPanel v-if="selectedCase && activeTab === 'audit'" :audit-case="selectedCase" />
        <LogicFlowBridge v-else-if="activeTab === 'trace'" />
        <div v-else-if="activeTab === 'brain'" class="flex items-center justify-center h-full text-slate-400">
          规则引擎功能开发中...
        </div>
        <div v-else-if="activeTab === 'profile'" class="personal-tab-wrap">
          <PersonalHealthProfile :embedded="true" />
        </div>
        <div v-else-if="activeTab === 'contributions'" class="personal-tab-wrap">
          <MyContributions />
        </div>
        <div v-else-if="activeTab === 'benefits'" class="personal-tab-wrap">
          <MyBenefits />
        </div>
        <div v-else class="flex items-center justify-center h-full text-slate-400">
          ← 请选择一个待审案例
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import DualSignPanel from './DualSignPanel.vue'
import LogicFlowBridge from '@/components/expert/LogicFlowBridge.vue'
import { fetchAuditQueue, type AuditCase } from '@/api/expert'
import { UserAvatarPopover, PersonalHealthProfile, MyContributions, MyBenefits } from '@/components/health'

const activeTab = ref('audit')
const riskFilter = ref<string>()
const auditQueue = ref<AuditCase[]>([])
const selectedCase = ref<AuditCase | null>(null)

const filteredQueue = computed(() => {
  if (!riskFilter.value) return auditQueue.value
  return auditQueue.value.filter(c => c.rawMetrics.riskLevel === riskFilter.value)
})

const riskColor = (level: string) => ({
  'bg-red-500': level === 'R3' || level === 'R4' || level === 'CRITICAL',
  'bg-orange-500': level === 'R2' || level === 'HIGH',
  'bg-yellow-500': level === 'R1' || level === 'MEDIUM',
  'bg-green-500': level === 'R0' || level === 'LOW',
})

const riskTagColor = (level: string) =>
  ['R3', 'R4', 'CRITICAL'].includes(level) ? 'red'
    : ['R2', 'HIGH'].includes(level) ? 'orange'
    : ['R1', 'MEDIUM'].includes(level) ? 'gold' : 'green'

onMounted(async () => {
  try {
    const { data } = await fetchAuditQueue()
    auditQueue.value = data?.items || []
    if (auditQueue.value.length) selectedCase.value = auditQueue.value[0]
  } catch { /* silent */ }
})
</script>

<style>
/* Dark tabs for expert panel */
.expert-dark-tabs .ant-tabs-tab { color: #94a3b8 !important; }
.expert-dark-tabs .ant-tabs-tab-active { color: #fff !important; }
.expert-dark-tabs .ant-tabs-ink-bar { background: #22c55e !important; }
.expert-nav-tabs .ant-tabs-tab { color: #cbd5e1 !important; }
.expert-nav-tabs .ant-tabs-tab-active { color: #fff !important; }
.expert-nav-tabs .ant-tabs-ink-bar { background: #22c55e !important; }
.expert-nav-tabs .ant-tabs-nav::before { border-bottom: none !important; }
</style>

<style scoped>
.personal-tab-wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  overflow-y: auto;
  height: 100%;
}
</style>
