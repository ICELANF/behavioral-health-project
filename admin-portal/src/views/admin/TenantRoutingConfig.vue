<template>
  <div class="tenant-routing-config">
    <a-page-header :title="`路由配置: ${tenantId}`" @back="$router.push('/admin/agent-templates')" sub-title="专家自定义路由规则 (优先于平台预置)" />

    <a-spin :spinning="loading">
      <!-- Agent 自定义关键词 -->
      <a-card title="Agent 路由关键词" :bordered="false" style="margin-top: 16px">
        <p style="color: #666; margin-bottom: 16px">专家为每个 Agent 定义的触发关键词, 匹配时获得加权得分 (优先于平台预置)</p>
        <a-table :dataSource="agentKeywords" :columns="kwColumns" :pagination="false" rowKey="agent_id" size="middle">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'custom_keywords'">
              <div>
                <a-tag v-for="(kw, idx) in record.custom_keywords" :key="idx" closable @close="removeKeyword(record, idx)">{{ kw }}</a-tag>
                <a-input
                  v-if="record._kwInputVisible"
                  :ref="el => kwInputRefs[record.agent_id] = el"
                  v-model:value="record._kwInputValue"
                  size="small"
                  style="width: 120px"
                  @blur="addKeyword(record)"
                  @pressEnter="addKeyword(record)"
                />
                <a-tag v-else style="cursor: pointer; border-style: dashed" @click="showKwInput(record)">
                  <PlusOutlined /> 添加
                </a-tag>
              </div>
            </template>
            <template v-if="column.key === 'keyword_boost'">
              <a-slider v-model:value="record.keyword_boost" :min="1.0" :max="3.0" :step="0.1" style="width: 120px; display: inline-block" />
              <span style="margin-left: 8px; color: #666">{{ record.keyword_boost }}x</span>
            </template>
            <template v-if="column.key === 'is_enabled'">
              <a-tag :color="record.is_enabled ? 'green' : 'default'">{{ record.is_enabled ? '启用' : '停用' }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 关联网络覆盖 -->
      <a-card title="关联网络覆盖" :bordered="false" style="margin-top: 16px">
        <p style="color: #666; margin-bottom: 16px">定义 Agent 之间的关联关系, 路由时补充协同 Agent (覆盖平台默认)</p>
        <a-form layout="vertical" style="max-width: 800px">
          <a-form-item v-for="(corr, idx) in correlationRows" :key="idx" :label="corr.source">
            <a-select v-model:value="corr.targets" mode="multiple" placeholder="选择关联 Agent" :options="agentSelectOptions" style="width: 100%" />
            <a-button type="link" size="small" danger @click="correlationRows.splice(idx, 1)" style="padding: 0">移除</a-button>
          </a-form-item>
          <a-button type="dashed" @click="addCorrelationRow"><PlusOutlined /> 添加关联规则</a-button>
        </a-form>
      </a-card>

      <!-- 冲突解决覆盖 -->
      <a-card title="冲突解决覆盖" :bordered="false" style="margin-top: 16px">
        <p style="color: #666; margin-bottom: 16px">当两个 Agent 结果冲突时, 指定哪个 Agent 优先</p>
        <a-table :dataSource="conflictRows" :columns="conflictColumns" :pagination="false" rowKey="_key" size="middle">
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'pair'">
              <a-select v-model:value="record.agentA" placeholder="Agent A" :options="agentSelectOptions" style="width: 140px" />
              <span style="margin: 0 8px">vs</span>
              <a-select v-model:value="record.agentB" placeholder="Agent B" :options="agentSelectOptions" style="width: 140px" />
            </template>
            <template v-if="column.key === 'winner'">
              <a-select v-model:value="record.winner" placeholder="优先方" style="width: 140px">
                <a-select-option :value="record.agentA">{{ record.agentA }}</a-select-option>
                <a-select-option :value="record.agentB">{{ record.agentB }}</a-select-option>
              </a-select>
            </template>
            <template v-if="column.key === 'action'">
              <a-button type="link" size="small" danger @click="conflictRows.splice(index, 1)">移除</a-button>
            </template>
          </template>
        </a-table>
        <a-button type="dashed" style="margin-top: 8px" @click="addConflictRow"><PlusOutlined /> 添加冲突规则</a-button>
      </a-card>

      <!-- 默认回退 Agent -->
      <a-card title="默认回退" :bordered="false" style="margin-top: 16px">
        <a-form layout="inline">
          <a-form-item label="回退 Agent">
            <a-select v-model:value="fallbackAgent" placeholder="无匹配时回退到..." :options="agentSelectOptions" style="width: 200px" />
          </a-form-item>
        </a-form>
      </a-card>

      <!-- 路由测试 -->
      <a-card title="路由测试" :bordered="false" style="margin-top: 16px">
        <a-form layout="inline">
          <a-form-item label="测试消息">
            <a-input v-model:value="testMessage" placeholder="输入一条用户消息..." style="width: 400px" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="runTest" :loading="testing">测试路由</a-button>
          </a-form-item>
        </a-form>
        <div v-if="testResult" style="margin-top: 16px">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="平台路由">
              <a-tag v-for="r in testResult.platform_routing" :key="r" color="blue">{{ r }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="租户路由">
              <a-tag v-for="r in testResult.tenant_routing" :key="r" color="green">{{ r }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="自定义关键词数">{{ testResult.tenant_ctx_summary?.custom_keywords_count }}</a-descriptions-item>
            <a-descriptions-item label="关联覆盖数">{{ testResult.tenant_ctx_summary?.correlations_overrides }}</a-descriptions-item>
            <a-descriptions-item label="冲突覆盖数">{{ testResult.tenant_ctx_summary?.conflicts_overrides }}</a-descriptions-item>
          </a-descriptions>
        </div>
      </a-card>

      <!-- 操作按钮 -->
      <div style="margin-top: 24px; text-align: right; padding-bottom: 24px">
        <a-space>
          <a-button @click="$router.back()">取消</a-button>
          <a-button type="primary" @click="handleSave" :loading="saving">保存路由配置</a-button>
        </a-space>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import request from '../../api/request'
import { agentTemplateApi } from '../../api/agent-template'

const route = useRoute()
const router = useRouter()
const tenantId = route.params.tenantId as string

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

// Agent 关键词表
const agentKeywords = ref<any[]>([])
const kwInputRefs: Record<string, any> = {}

const kwColumns = [
  { title: 'Agent', dataIndex: 'agent_id', width: 120 },
  { title: '显示名', dataIndex: 'display_name', width: 120 },
  { title: '自定义关键词', key: 'custom_keywords', width: 360 },
  { title: '加权倍数', key: 'keyword_boost', width: 200 },
  { title: '状态', key: 'is_enabled', width: 80 },
]

// 关联网络
const correlationRows = ref<{ source: string; targets: string[] }[]>([])

// 冲突解决
const conflictRows = ref<{ _key: string; agentA: string; agentB: string; winner: string }[]>([])
const conflictColumns = [
  { title: '冲突对', key: 'pair', width: 400 },
  { title: '优先方', key: 'winner', width: 160 },
  { title: '操作', key: 'action', width: 80 },
]

// 回退 Agent
const fallbackAgent = ref('behavior_rx')

// Agent 选项
const agentSelectOptions = ref<{ label: string; value: string }[]>([])

// 路由测试
const testMessage = ref('')
const testResult = ref<any>(null)

function showKwInput(record: any) {
  record._kwInputVisible = true
  nextTick(() => {
    const inputEl = kwInputRefs[record.agent_id]
    inputEl?.focus?.()
  })
}

function addKeyword(record: any) {
  const v = (record._kwInputValue || '').trim()
  if (v && !record.custom_keywords.includes(v)) {
    record.custom_keywords.push(v)
  }
  record._kwInputVisible = false
  record._kwInputValue = ''
}

function removeKeyword(record: any, idx: number) {
  record.custom_keywords.splice(idx, 1)
}

function addCorrelationRow() {
  correlationRows.value.push({ source: '', targets: [] })
}

function addConflictRow() {
  conflictRows.value.push({ _key: `c-${Date.now()}`, agentA: '', agentB: '', winner: '' })
}

async function loadData() {
  loading.value = true
  try {
    // 加载 Agent 选项
    const tplRes = await agentTemplateApi.list({ limit: 200 })
    agentSelectOptions.value = (tplRes.data.items || []).map((t: any) => ({
      label: `${t.display_name} (${t.agent_id})`,
      value: t.agent_id,
    }))

    // 加载路由配置
    const res = await request.get(`/v1/tenants/${tenantId}/routing`)
    const d = res.data.data

    // Agent 关键词
    agentKeywords.value = (d.agent_keywords || []).map((ak: any) => ({
      ...ak,
      _kwInputVisible: false,
      _kwInputValue: '',
    }))

    // 关联网络
    const corrObj = d.routing_correlations || {}
    correlationRows.value = Object.entries(corrObj).map(([source, targets]) => ({
      source,
      targets: targets as string[],
    }))

    // 冲突规则
    const confObj = d.routing_conflicts || {}
    conflictRows.value = Object.entries(confObj).map(([pairKey, winner]) => {
      const [a, b] = pairKey.split('|')
      return { _key: pairKey, agentA: a, agentB: b, winner: winner as string }
    })

    // 回退
    fallbackAgent.value = d.default_fallback_agent || 'behavior_rx'
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    // 构建关联 dict
    const corrDict: Record<string, string[]> = {}
    for (const row of correlationRows.value) {
      if (row.source && row.targets.length > 0) {
        corrDict[row.source] = row.targets
      }
    }

    // 构建冲突 dict
    const confDict: Record<string, string> = {}
    for (const row of conflictRows.value) {
      if (row.agentA && row.agentB && row.winner) {
        const key = [row.agentA, row.agentB].sort().join('|')
        confDict[key] = row.winner
      }
    }

    // 构建关键词更新
    const agentKws = agentKeywords.value.map(ak => ({
      agent_id: ak.agent_id,
      keywords: ak.custom_keywords,
      boost: ak.keyword_boost,
    }))

    await request.put(`/v1/tenants/${tenantId}/routing`, {
      routing_correlations: corrDict,
      routing_conflicts: confDict,
      default_fallback_agent: fallbackAgent.value,
      agent_keywords: agentKws,
    })
    message.success('路由配置已保存')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function runTest() {
  if (!testMessage.value.trim()) {
    message.warning('请输入测试消息')
    return
  }
  testing.value = true
  try {
    const res = await request.post(`/v1/tenants/${tenantId}/routing/test`, {
      message: testMessage.value,
    })
    testResult.value = res.data.data
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '测试失败')
  } finally {
    testing.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.tenant-routing-config { padding: 0; }
</style>
