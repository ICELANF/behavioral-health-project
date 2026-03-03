<template>
  <div class="platform-overview">
    <a-page-header title="H5 / 小程序管理" sub-title="平台健康状态与部署管理" style="padding: 0 0 16px" />

    <!-- 刷新按钮 -->
    <div style="display:flex; justify-content:flex-end; margin-bottom:16px">
      <a-button :loading="loading" @click="loadAll">
        <template #icon><ReloadOutlined /></template>
        刷新
      </a-button>
    </div>

    <!-- 系统健康 -->
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card title="🖥️ 系统健康状态" :loading="healthLoading">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="8">
              <a-statistic
                title="数据库"
                :value="health.database === 'healthy' ? '正常' : '异常'"
                :value-style="{ color: health.database === 'healthy' ? '#52c41a' : '#ff4d4f' }"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="health.database === 'healthy'" style="color:#52c41a" />
                  <CloseCircleOutlined v-else style="color:#ff4d4f" />
                </template>
              </a-statistic>
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-statistic
                title="Redis 缓存"
                :value="health.redis === 'healthy' ? '正常' : '异常'"
                :value-style="{ color: health.redis === 'healthy' ? '#52c41a' : '#ff4d4f' }"
              >
                <template #prefix>
                  <CheckCircleOutlined v-if="health.redis === 'healthy'" style="color:#52c41a" />
                  <CloseCircleOutlined v-else style="color:#ff4d4f" />
                </template>
              </a-statistic>
            </a-col>
            <a-col :xs="24" :sm="8">
              <a-statistic
                title="API 路由数"
                :value="health.routes || '--'"
                suffix="条"
                :value-style="{ color: '#1677ff' }"
              />
            </a-col>
          </a-row>
          <a-divider style="margin: 12px 0" />
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12">
              <div class="health-badge">
                <a-tag :color="health.status === 'healthy' ? 'green' : 'red'" style="font-size:14px; padding:4px 12px">
                  综合状态: {{ health.status === 'healthy' ? '✅ 健康' : '❌ 异常' }}
                </a-tag>
                <span v-if="health.checked_at" style="color:#999; font-size:12px; margin-left:8px">
                  检测时间: {{ health.checked_at }}
                </span>
              </div>
            </a-col>
            <a-col :xs="24" :sm="12">
              <div class="health-badge">
                <a-tag :color="contractOk ? 'green' : 'orange'" style="font-size:14px; padding:4px 12px">
                  前端合约: {{ contractSummary }}
                </a-tag>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <!-- 平台数据 -->
    <a-row :gutter="[16, 16]" style="margin-top:16px">
      <a-col :xs="24" :sm="12">
        <a-card title="📱 各平台活跃用户 (DAU)" :loading="statsLoading">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic title="小程序" :value="stats.miniprogram_dau ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="H5" :value="stats.h5_dau ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="管理后台" :value="stats.admin_dau ?? '--'" />
            </a-col>
          </a-row>
          <a-divider style="margin: 12px 0" />
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic title="总用户数" :value="stats.total_users ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="教练数" :value="stats.total_coaches ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="今日新增" :value="stats.today_new_users ?? '--'" />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-card title="📋 内容发布状态" :loading="statsLoading">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic title="已发布" :value="stats.published_content ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="待审核" :value="stats.pending_review ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="草稿" :value="stats.draft_content ?? '--'" />
            </a-col>
          </a-row>
          <a-divider style="margin: 12px 0" />
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic title="课程数" :value="stats.total_courses ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="直播场次" :value="stats.total_lives ?? '--'" />
            </a-col>
            <a-col :span="8">
              <a-statistic title="题库题目" :value="stats.total_questions ?? '--'" />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <!-- 前端合约详情 -->
    <a-row :gutter="[16, 16]" style="margin-top:16px">
      <a-col :span="24">
        <a-card title="🔗 前后端接口合约" :loading="contractLoading">
          <a-table
            :dataSource="contractItems"
            :columns="contractColumns"
            :pagination="false"
            size="small"
            :scroll="{ x: 600 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="record.status === 'ok' ? 'green' : 'red'">
                  {{ record.status === 'ok' ? '✅ 已实现' : '❌ 缺失' }}
                </a-tag>
              </template>
              <template v-if="column.key === 'path'">
                <code style="font-size:12px">{{ record.method }} {{ record.path }}</code>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 部署信息 -->
    <a-row :gutter="[16, 16]" style="margin-top:16px">
      <a-col :xs="24" :sm="12">
        <a-card title="🚀 部署信息 (Coach 小程序)">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="平台">微信小程序 (uni-app + Vue3)</a-descriptions-item>
            <a-descriptions-item label="AppID">wx7da71ddbc7890598</a-descriptions-item>
            <a-descriptions-item label="构建产物">dist/dev/mp-weixin → 微信开发者工具导入</a-descriptions-item>
            <a-descriptions-item label="构建命令">npm run dev:mp-weixin</a-descriptions-item>
            <a-descriptions-item label="API 代理">http://localhost:8000</a-descriptions-item>
          </a-descriptions>
          <a-divider style="margin: 12px 0" />
          <div style="color:#666; font-size:13px">
            <InfoCircleOutlined style="color:#1677ff; margin-right:4px" />
            生产部署需替换 config/env.ts → BASE_URL 为 https://api.xingjian.health
          </div>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-card title="🌐 部署信息 (BHP H5)">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="平台">微信公众号 H5 (Vant + Vue3)</a-descriptions-item>
            <a-descriptions-item label="角色">Observer / Grower / Sharer</a-descriptions-item>
            <a-descriptions-item label="构建命令">npx vite build</a-descriptions-item>
            <a-descriptions-item label="Dev 端口">:3002</a-descriptions-item>
            <a-descriptions-item label="API 代理">http://localhost:8000</a-descriptions-item>
          </a-descriptions>
          <a-divider style="margin: 12px 0" />
          <div style="color:#666; font-size:13px">
            <InfoCircleOutlined style="color:#1677ff; margin-right:4px" />
            构建: vue-tsc 在 Node v24 下有问题，使用 npx vite build（跳过类型检查）
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速跳转 -->
    <a-row :gutter="[16, 16]" style="margin-top:16px">
      <a-col :span="24">
        <a-card title="⚡ 快速跳转">
          <a-space wrap>
            <a-button @click="$router.push('/admin/analytics')">📊 数据分析</a-button>
            <a-button @click="$router.push('/content/review')">📋 内容审核</a-button>
            <a-button @click="$router.push('/admin/content-manage')">📤 内容发布</a-button>
            <a-button @click="$router.push('/admin/user-management')">👥 用户管理</a-button>
            <a-button @click="$router.push('/coach/list')">🤝 教练管理</a-button>
            <a-button @click="$router.push('/safety/dashboard')">🛡️ 安全仪表盘</a-button>
            <a-button @click="$router.push('/admin/command-center')" type="primary">
              🖥️ 打开全局指挥中心
            </a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const healthLoading = ref(true)
const statsLoading = ref(true)
const contractLoading = ref(true)

const health = ref<Record<string, any>>({})
const stats = ref<Record<string, any>>({})
const contractItems = ref<any[]>([])

const contractOk = computed(() =>
  contractItems.value.length > 0 &&
  contractItems.value.every(i => i.status === 'ok')
)
const contractSummary = computed(() => {
  const total = contractItems.value.length
  const ok = contractItems.value.filter(i => i.status === 'ok').length
  if (total === 0) return '加载中...'
  return `${ok}/${total} 已实现`
})

const contractColumns = [
  { title: '模块', dataIndex: 'module', key: 'module', width: 100 },
  { title: '接口', key: 'path', width: 240 },
  { title: '状态', key: 'status', width: 100 },
  { title: '备注', dataIndex: 'note', key: 'note' },
]

async function loadHealth() {
  healthLoading.value = true
  try {
    const res = await request.get('v1/system/health')
    const d = res.data
    // checks.database / checks.redis may be plain strings ("healthy") or objects ({status:...})
    const dbVal = d.checks?.database
    const rdVal = d.checks?.redis
    health.value = {
      status: d.status,
      database: typeof dbVal === 'string' ? dbVal : (dbVal?.status ?? 'unknown'),
      redis:    typeof rdVal === 'string' ? rdVal : (rdVal?.status ?? 'unknown'),
      routes:   d.total_routes ?? d.route_count ?? d.checks?.route_modules?.route_count ?? '--',
      checked_at: (d.timestamp ?? d.checked_at)
        ? new Date(d.timestamp ?? d.checked_at).toLocaleString('zh-CN') : ''
    }
  } catch {
    health.value = { status: 'error', database: 'unknown', redis: 'unknown' }
  } finally {
    healthLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  try {
    const res = await request.get('v1/analytics/admin/overview')
    const d = res.data
    stats.value = {
      total_users: d.total_users ?? d.users?.total,
      total_coaches: d.total_coaches ?? d.coaches?.total,
      today_new_users: d.today_new_users ?? d.new_users_today,
      published_content: d.published_content ?? d.content?.published,
      pending_review: d.pending_review ?? d.content?.pending,
      draft_content: d.draft_content ?? d.content?.draft,
      total_courses: d.total_courses ?? d.courses?.total,
      total_lives: d.total_lives ?? d.lives?.total,
      total_questions: d.total_questions ?? d.questions?.total,
      miniprogram_dau: d.miniprogram_dau ?? d.dau?.miniprogram ?? '--',
      h5_dau: d.h5_dau ?? d.dau?.h5 ?? '--',
      admin_dau: d.admin_dau ?? d.dau?.admin ?? '--',
    }
  } catch {
    // analytics endpoint may not have all fields — graceful fallback
    stats.value = {}
  } finally {
    statsLoading.value = false
  }
}

async function loadContract() {
  contractLoading.value = true
  try {
    const res = await request.get('v1/system/routes/frontend-contract')
    const d = res.data
    // Response: { matched_endpoints:[{method,path,status:"LIVE"}], missing_endpoints:[...],
    //             matched:42, total_frontend_endpoints:42, coverage:"100%" }
    const items: any[] = []
    const extractModule = (path: string) => {
      // "/api/v1/auth/login" → "auth"
      const parts = path.replace(/^\/api\/v1\//, '').split('/')
      return parts[0] || '--'
    }
    for (const ep of (d.matched_endpoints ?? [])) {
      items.push({
        key: `ok-${ep.path}`,
        module: ep.module ?? extractModule(ep.path),
        method: ep.method || 'GET',
        path: ep.path,
        status: 'ok',
        note: ep.status === 'LIVE' ? 'LIVE' : (ep.status ?? '')
      })
    }
    for (const ep of (d.missing_endpoints ?? [])) {
      items.push({
        key: `miss-${ep.path}`,
        module: ep.module ?? extractModule(ep.path),
        method: ep.method || 'GET',
        path: ep.path,
        status: 'missing',
        note: ep.note ?? ''
      })
    }
    contractItems.value = items
  } catch {
    contractItems.value = []
  } finally {
    contractLoading.value = false
  }
}

async function loadAll() {
  loading.value = true
  await Promise.allSettled([loadHealth(), loadStats(), loadContract()])
  loading.value = false
}

onMounted(() => { loadAll() })
</script>

<style scoped>
.platform-overview {
  padding: 4px 0;
}
.health-badge {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
