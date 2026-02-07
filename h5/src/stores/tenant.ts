/**
 * 租户状态管理 (Pinia Store)
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/index'

// === 类型定义 ===

export interface BrandColors {
  primary: string
  accent: string
  bg: string
  text: string
}

export interface AgentMapping {
  id: number
  tenant_id: string
  agent_id: string
  display_name: string
  display_avatar: string
  greeting: string
  tone: string
  bio: string
  is_enabled: boolean
  is_primary: boolean
  sort_order: number
}

export interface ServicePackage {
  id: string
  name: string
  price: number
  duration_days: number
  features: string[]
}

export interface ExpertTenant {
  id: string
  expert_user_id: number
  brand_name: string
  brand_tagline: string
  brand_avatar: string
  brand_logo_url: string
  brand_colors: BrandColors
  brand_theme_id: string
  custom_domain: string
  expert_title: string
  expert_self_intro: string
  expert_specialties: string[]
  expert_credentials: string[]
  enabled_agents: string[]
  agent_persona_overrides: Record<string, any>
  service_packages: ServicePackage[]
  welcome_message: string
  status: string
  tier: string
  max_clients: number
  revenue_share_expert: number
  created_at: string
  updated_at: string
  client_count_active: number
  client_count_total: number
  agent_mappings: AgentMapping[]
}

export interface ExpertTenantSummary {
  id: string
  brand_name: string
  brand_tagline: string
  brand_avatar: string
  brand_logo_url: string
  brand_colors: BrandColors
  brand_theme_id: string
  expert_title: string
  expert_specialties: string[]
  enabled_agents: string[]
  status: string
  client_count_active: number
}

export interface TenantClient {
  id: number
  tenant_id: string
  user_id: number
  source: string
  service_package: string
  status: string
  enrolled_at: string
  graduated_at: string | null
  total_sessions: number
  last_active_at: string | null
  notes: string
}

export interface TenantStats {
  clients: {
    active: number
    graduated: number
    paused: number
    exited: number
    total: number
  }
  new_this_month: number
}

// === Agent 元数据 (前端静态) ===

export const AGENT_META: Record<string, { name: string; avatar: string; category: string }> = {
  sleep:         { name: '睡眠管理', avatar: '🌙', category: '专科' },
  glucose:       { name: '血糖管理', avatar: '📊', category: '专科' },
  stress:        { name: '压力管理', avatar: '🧘', category: '专科' },
  mental:        { name: '心理支持', avatar: '💚', category: '专科' },
  nutrition:     { name: '营养指导', avatar: '🥗', category: '专科' },
  exercise:      { name: '运动指导', avatar: '🏃', category: '专科' },
  tcm:           { name: '中医养生', avatar: '🌿', category: '专科' },
  crisis:        { name: '安全守护', avatar: '🛡️', category: '系统' },
  motivation:    { name: '动机激发', avatar: '🔥', category: '专科' },
  behavior_rx:   { name: '行为处方', avatar: '🎯', category: '整合' },
  weight:        { name: '体重管理', avatar: '⚖️', category: '整合' },
  cardiac_rehab: { name: '心脏康复', avatar: '❤️', category: '整合' },
}

// === Store ===

export const useTenantStore = defineStore('tenant', () => {
  const hubList = ref<ExpertTenantSummary[]>([])
  const currentTenant = ref<ExpertTenant | null>(null)
  const currentClients = ref<TenantClient[]>([])
  const currentStats = ref<TenantStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeTenants = computed(() =>
    hubList.value.filter(t => t.status === 'active')
  )

  const currentAgents = computed(() => {
    if (!currentTenant.value) return []
    return currentTenant.value.agent_mappings
      .filter(m => m.is_enabled)
      .sort((a, b) => a.sort_order - b.sort_order)
  })

  const totalHubClients = computed(() =>
    hubList.value.reduce((sum, t) => sum + t.client_count_active, 0)
  )

  const API_BASE = '/api/v1/tenants'

  async function fetchHub() {
    loading.value = true
    error.value = null
    try {
      const res: any = await api.get(`${API_BASE}/hub`)
      if (res.success) {
        hubList.value = res.data
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchTenant(tenantId: string) {
    loading.value = true
    error.value = null
    try {
      const res: any = await api.get(`${API_BASE}/${tenantId}`)
      if (res.success) {
        currentTenant.value = res.data
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchTenantPublic(tenantId: string) {
    loading.value = true
    try {
      const res: any = await api.get(`${API_BASE}/${tenantId}/public`)
      if (res.success) {
        currentTenant.value = res.data
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchClients(tenantId: string, status?: string) {
    try {
      const params: any = {}
      if (status) params.status = status
      const res: any = await api.get(`${API_BASE}/${tenantId}/clients`, { params })
      if (res.success) {
        currentClients.value = res.data
      }
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function fetchStats(tenantId: string) {
    try {
      const res: any = await api.get(`${API_BASE}/${tenantId}/stats`)
      if (res.success) {
        currentStats.value = res.data
      }
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function updateTenant(tenantId: string, data: Partial<ExpertTenant>) {
    try {
      const res: any = await api.patch(`${API_BASE}/${tenantId}`, data)
      if (res.success) {
        currentTenant.value = res.data
      }
      return res
    } catch (e: any) {
      error.value = e.message
      return { success: false, error: e.message }
    }
  }

  async function addClient(tenantId: string, userId: number, servicePackage = 'trial') {
    try {
      const res: any = await api.post(`${API_BASE}/${tenantId}/clients`, {
        user_id: userId,
        service_package: servicePackage,
      })
      return res
    } catch (e: any) {
      return { success: false, error: e.message }
    }
  }

  function applyBrandTheme(colors: BrandColors) {
    const root = document.documentElement
    root.style.setProperty('--brand-primary', colors.primary)
    root.style.setProperty('--brand-accent', colors.accent)
    root.style.setProperty('--brand-bg', colors.bg)
    root.style.setProperty('--brand-text', colors.text)
  }

  function clearBrandTheme() {
    const root = document.documentElement
    root.style.removeProperty('--brand-primary')
    root.style.removeProperty('--brand-accent')
    root.style.removeProperty('--brand-bg')
    root.style.removeProperty('--brand-text')
  }

  function $reset() {
    hubList.value = []
    currentTenant.value = null
    currentClients.value = []
    currentStats.value = null
    loading.value = false
    error.value = null
    clearBrandTheme()
  }

  return {
    hubList, currentTenant, currentClients, currentStats, loading, error,
    activeTenants, currentAgents, totalHubClients,
    fetchHub, fetchTenant, fetchTenantPublic, fetchClients, fetchStats,
    updateTenant, addClient,
    applyBrandTheme, clearBrandTheme, $reset,
  }
})
