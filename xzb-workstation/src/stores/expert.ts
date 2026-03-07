import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMyProfile, getMyConfig, getDashboard } from '@/api/xzb'

export interface ExpertProfile {
  id: string
  display_name: string
  specialty: string
  tcm_weight: number
  domain_tags: string[]
  style_profile: Record<string, number>
}

export interface CompanionConfig {
  companion_name: string
  greeting: string
  comm_style: string
  boundary_stmt: string
  auto_rx_enabled: boolean
  dormant_mode: boolean
}

export interface DashboardData {
  pending_knowledge_confirmations: number
  pending_rx_reviews: number
  active_seekers: number
  knowledge_health_score: number
  recent_conversations: unknown[]
}

export const useExpertStore = defineStore('expert', () => {
  const profile = ref<ExpertProfile | null>(null)
  const config = ref<CompanionConfig | null>(null)
  const dashboard = ref<DashboardData | null>(null)
  const loading = ref(false)

  async function loadProfile() {
    try {
      const res = await getMyProfile()
      profile.value = res.data
    } catch { /* not registered yet */ }
  }

  async function loadConfig() {
    try {
      const res = await getMyConfig()
      config.value = res.data
    } catch { /* no config yet */ }
  }

  async function loadDashboard() {
    loading.value = true
    try {
      const res = await getDashboard()
      dashboard.value = res.data
    } catch { /* expert not set up */ }
    loading.value = false
  }

  async function loadAll() {
    await Promise.allSettled([loadProfile(), loadConfig(), loadDashboard()])
  }

  return { profile, config, dashboard, loading, loadProfile, loadConfig, loadDashboard, loadAll }
})
