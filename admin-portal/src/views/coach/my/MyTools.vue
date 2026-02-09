<template>
  <div class="my-tools">
    <div class="page-header">
      <h2>我的工具箱</h2>
    </div>

    <!-- Loading -->
    <div v-if="loading" style="text-align: center; padding: 60px 0">
      <a-spin size="large" tip="加载工具数据..." />
    </div>

    <template v-if="!loading">
      <!-- Tool Grid -->
      <div class="tools-grid">
        <div v-for="tool in tools" :key="tool.key" class="tool-card" :style="{ borderColor: tool.color }" @click="useTool(tool)">
          <div class="tool-icon" :style="{ background: tool.color + '18', color: tool.color }">
            {{ toolIcon(tool.key) }}
          </div>
          <div class="tool-info">
            <span class="tool-name">{{ tool.name }}</span>
            <span class="tool-desc">{{ tool.description }}</span>
          </div>
          <div class="tool-stats">
            <span class="stat-num">{{ tool.use_count }}</span>
            <span class="stat-label">本月</span>
          </div>
        </div>
      </div>

      <!-- Recent Usage -->
      <a-card title="最近活动" style="margin-top: 16px; margin-bottom: 16px">
        <a-empty v-if="recentActivity.length === 0" description="暂无活动记录" />
        <div v-for="item in recentActivity" :key="item.id" class="usage-item">
          <div class="usage-info">
            <span class="usage-name">{{ item.tool_name }}</span>
            <span class="usage-context">学员: {{ item.student }} &middot; {{ item.action }}</span>
          </div>
          <span class="usage-time">{{ item.time }}</span>
        </div>
      </a-card>

      <!-- Usage Statistics -->
      <a-card title="使用统计">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic title="本月总使用" :value="totalMonthUsage" suffix="次" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="最常用工具" :value="mostUsedTool" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="活跃天数" :value="activeDays" suffix="天" value-style="color: #3f8600" />
          </a-col>
        </a-row>
        <div class="usage-chart" style="margin-top: 16px">
          <div v-for="tool in tools" :key="tool.key" class="chart-item">
            <span class="chart-label">{{ tool.name }}</span>
            <div class="chart-bar-bg">
              <div class="chart-bar" :style="{ width: (tool.use_count / maxUseCount * 100) + '%', background: tool.color }"></div>
            </div>
            <span class="chart-count">{{ tool.use_count }}</span>
          </div>
        </div>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

const router = useRouter()

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const token = localStorage.getItem('token') || ''
const authHeaders: Record<string, string> = {
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
}

const loading = ref(true)
const tools = ref<any[]>([])
const recentActivity = ref<any[]>([])
const totalMonthUsage = ref(0)
const mostUsedTool = ref('--')
const activeDays = ref(0)

const maxUseCount = computed(() => Math.max(...tools.value.map(t => t.use_count), 1))

const toolIcon = (key: string) => {
  const icons: Record<string, string> = {
    message: '\u2709', encouragement: '\u2665', advice: '\u2605',
    reminder: '\u23F0', assessment: '\u2611', micro_action: '\u2699',
  }
  return icons[key] || '\u2022'
}

const loadData = async () => {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/v1/coach/my-tools-stats`, {
      headers: authHeaders,
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()

    tools.value = data.tools || []
    recentActivity.value = data.recent_activity || []
    totalMonthUsage.value = data.total_month_usage ?? 0
    mostUsedTool.value = data.most_used_tool || '--'

    // Calculate active days from recent activity timestamps
    const uniqueDays = new Set(
      recentActivity.value
        .filter((a: any) => a.time)
        .map((a: any) => a.time.includes('分钟') || a.time.includes('小时') ? 'today' : a.time)
    )
    activeDays.value = Math.max(uniqueDays.size, totalMonthUsage.value > 0 ? 1 : 0)
  } catch (e: any) {
    console.error('加载工具统计失败:', e)
    message.error('加载工具统计失败')
  } finally {
    loading.value = false
  }
}

const useTool = (tool: any) => {
  const routes: Record<string, string> = {
    message: '/coach/messages',
    encouragement: '/coach/messages',
    advice: '/coach/messages',
    reminder: '/coach/messages',
    assessment: '/coach/home',
    micro_action: '/coach/home',
  }
  const target = routes[tool.key]
  if (target) {
    router.push(target)
  } else {
    message.info(`正在打开 ${tool.name}...`)
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.tools-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tool-card { display: flex; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; cursor: pointer; border-left: 3px solid; transition: box-shadow 0.2s; }
.tool-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.tool-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.tool-info { flex: 1; }
.tool-name { display: block; font-size: 14px; font-weight: 600; color: #333; }
.tool-desc { font-size: 12px; color: #999; }
.tool-stats { text-align: center; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: #333; }
.stat-label { font-size: 11px; color: #999; }

.usage-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.usage-info { flex: 1; }
.usage-name { display: block; font-size: 13px; font-weight: 500; }
.usage-context { font-size: 12px; color: #999; }
.usage-time { font-size: 12px; color: #bbb; }

.chart-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.chart-label { min-width: 100px; font-size: 13px; color: #333; }
.chart-bar-bg { flex: 1; height: 16px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.chart-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
.chart-count { min-width: 30px; text-align: right; font-size: 13px; color: #999; }
</style>
