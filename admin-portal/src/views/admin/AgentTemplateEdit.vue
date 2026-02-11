<template>
  <div class="agent-template-edit">
    <a-page-header :title="isCreate ? '创建 Agent' : `编辑 Agent: ${form.display_name}`" @back="$router.push('/admin/agent-templates')" />

    <a-card :bordered="false" style="margin-top: 16px" :loading="loading">
      <a-form :model="form" layout="vertical" style="max-width: 800px">
        <!-- agent_id -->
        <a-form-item label="Agent ID" required>
          <a-input v-model:value="form.agent_id" :disabled="!isCreate" placeholder="小写字母开头, 仅含小写字母/数字/下划线" />
          <div v-if="isCreate" style="color: #999; font-size: 12px; margin-top: 4px">创建后不可修改</div>
        </a-form-item>

        <!-- display_name -->
        <a-form-item label="显示名称" required>
          <a-input v-model:value="form.display_name" placeholder="如: 睡眠专家" />
        </a-form-item>

        <!-- description -->
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" :rows="2" placeholder="Agent 功能描述" />
        </a-form-item>

        <!-- keywords -->
        <a-form-item label="路由关键词">
          <div>
            <a-tag v-for="(kw, idx) in form.keywords" :key="idx" closable @close="form.keywords.splice(idx, 1)">{{ kw }}</a-tag>
            <a-input
              v-if="kwInputVisible"
              ref="kwInputRef"
              v-model:value="kwInputValue"
              size="small"
              style="width: 120px"
              @blur="handleAddKeyword"
              @pressEnter="handleAddKeyword"
            />
            <a-tag v-else style="cursor: pointer; border-style: dashed" @click="showKwInput">
              <PlusOutlined /> 添加
            </a-tag>
          </div>
        </a-form-item>

        <!-- system_prompt -->
        <a-form-item label="System Prompt (LLM)">
          <a-textarea v-model:value="form.system_prompt" :rows="6" style="font-family: monospace" placeholder="LLM 系统提示词, 定义 Agent 人设和输出格式" />
        </a-form-item>

        <a-row :gutter="24">
          <a-col :span="8">
            <a-form-item label="优先级 (0=最高)">
              <a-input-number v-model:value="form.priority" :min="0" :max="10" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="基础权重">
              <a-slider v-model:value="form.base_weight" :min="0" :max="1" :step="0.05" />
              <div style="text-align: center; color: #666">{{ form.base_weight }}</div>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="LLM 增强">
              <a-switch v-model:checked="form.enable_llm" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- correlations -->
        <a-form-item label="关联 Agent">
          <a-select v-model:value="form.correlations" mode="multiple" placeholder="选择关联的 Agent" :options="agentOptions" />
        </a-form-item>

        <!-- conflict_wins_over -->
        <a-form-item label="冲突优先于">
          <a-select v-model:value="form.conflict_wins_over" mode="multiple" placeholder="冲突时优先于哪些 Agent" :options="agentOptions" />
        </a-form-item>

        <!-- 信息 -->
        <a-form-item v-if="!isCreate" label="模板信息">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="类型">
              <a-tag :color="form.agent_type === 'dynamic_llm' ? 'cyan' : 'purple'">{{ form.agent_type }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="预置">
              <a-tag v-if="form.is_preset" color="blue">预置</a-tag>
              <a-tag v-else color="green">自定义</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">{{ form.created_at }}</a-descriptions-item>
            <a-descriptions-item label="更新时间">{{ form.updated_at }}</a-descriptions-item>
          </a-descriptions>
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSave" :loading="saving">保存</a-button>
            <a-button @click="$router.push('/admin/agent-templates')">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { agentTemplateApi } from '../../api/agent-template'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)

const isCreate = computed(() => route.name === 'AgentTemplateCreate')

const form = reactive({
  agent_id: '',
  display_name: '',
  description: '',
  keywords: [] as string[],
  data_fields: [] as string[],
  correlations: [] as string[],
  priority: 5,
  base_weight: 0.8,
  enable_llm: true,
  system_prompt: '',
  conflict_wins_over: [] as string[],
  agent_type: 'dynamic_llm',
  is_preset: false,
  created_at: '',
  updated_at: '',
})

const agentOptions = ref<{ label: string; value: string }[]>([])

// keyword input
const kwInputVisible = ref(false)
const kwInputValue = ref('')
const kwInputRef = ref<any>(null)

function showKwInput() {
  kwInputVisible.value = true
  nextTick(() => kwInputRef.value?.focus())
}

function handleAddKeyword() {
  const v = kwInputValue.value.trim()
  if (v && !form.keywords.includes(v)) {
    form.keywords.push(v)
  }
  kwInputVisible.value = false
  kwInputValue.value = ''
}

async function loadAgentOptions() {
  try {
    const res = await agentTemplateApi.list({ limit: 200 })
    agentOptions.value = (res.data.items || []).map((t: any) => ({
      label: `${t.display_name} (${t.agent_id})`,
      value: t.agent_id,
    }))
  } catch {
    // ignore
  }
}

async function loadTemplate() {
  const agentId = route.params.agentId as string
  if (!agentId) return
  loading.value = true
  try {
    const res = await agentTemplateApi.get(agentId)
    const data = res.data
    Object.assign(form, {
      agent_id: data.agent_id,
      display_name: data.display_name,
      description: data.description || '',
      keywords: data.keywords || [],
      data_fields: data.data_fields || [],
      correlations: data.correlations || [],
      priority: data.priority,
      base_weight: data.base_weight,
      enable_llm: data.enable_llm,
      system_prompt: data.system_prompt || '',
      conflict_wins_over: data.conflict_wins_over || [],
      agent_type: data.agent_type,
      is_preset: data.is_preset,
      created_at: data.created_at,
      updated_at: data.updated_at,
    })
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!form.agent_id || !form.display_name) {
    message.warning('请填写 Agent ID 和显示名称')
    return
  }
  saving.value = true
  try {
    const payload = {
      agent_id: form.agent_id,
      display_name: form.display_name,
      description: form.description,
      keywords: form.keywords,
      data_fields: form.data_fields,
      correlations: form.correlations,
      priority: form.priority,
      base_weight: form.base_weight,
      enable_llm: form.enable_llm,
      system_prompt: form.system_prompt,
      conflict_wins_over: form.conflict_wins_over,
    }
    if (isCreate.value) {
      await agentTemplateApi.create(payload)
      message.success('创建成功')
    } else {
      const { agent_id, ...updatePayload } = payload
      await agentTemplateApi.update(form.agent_id, updatePayload)
      message.success('保存成功')
    }
    router.push('/admin/agent-templates')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadAgentOptions()
  if (!isCreate.value) {
    loadTemplate()
  }
})
</script>

<style scoped>
.agent-template-edit { padding: 0; }
</style>
