<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Card,
  Form,
  FormItem,
  Input,
  Select,
  Switch,
  Button,
  Space,
  Tag,
  Divider,
  message,
  Alert
} from 'ant-design-vue'
import {
  SaveOutlined,
  ArrowLeftOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import type { PromptTemplate } from '@/types'
import { TTM_STAGES, TRIGGER_DOMAINS } from '@/constants'
import request from '@/api/request'
import { sanitizeHtml } from '@/utils/sanitize'

const router = useRouter()
const route = useRoute()

const isEdit = computed(() => !!route.params.id)
const pageTitle = computed(() => isEdit.value ? '编辑 Prompt 模板' : '新建 Prompt 模板')

// 分类选项
const categories = [
  { value: 'greeting', label: '开场问候' },
  { value: 'assessment', label: '评估询问' },
  { value: 'education', label: '健康教育' },
  { value: 'motivation', label: '动机激励' },
  { value: 'goal_setting', label: '目标设定' },
  { value: 'follow_up', label: '随访跟进' },
  { value: 'crisis', label: '危机干预' }
]

// 表单数据
const formState = reactive<Partial<PromptTemplate>>({
  name: '',
  description: '',
  category: undefined,
  content: '',
  variables: [],
  ttm_stage: undefined,
  trigger_domain: undefined,
  is_active: true
})

// 新变量输入
const newVariable = ref('')
const loading = ref(false)

// 从内容中提取变量
const extractedVariables = computed(() => {
  const matches = formState.content?.match(/\{\{(\w+)\}\}/g) || []
  return [...new Set(matches.map(m => m.replace(/\{\{|\}\}/g, '')))]
})

// 预览内容（替换变量为示例值）
const previewContent = computed(() => {
  let content = formState.content || ''
  // Static preview fixtures — never persisted, only used for template variable rendering preview
  const sampleValues: Record<string, string> = {
    name: '用户',
    value: '8.5',
    activity: '散步',
    duration: '30',
    medication: '二甲双胍',
    date: new Date().toISOString().slice(0, 10),
    goal: '每天运动30分钟'
  }

  extractedVariables.value.forEach(v => {
    const regex = new RegExp(`\\{\\{${v}\\}\\}`, 'g')
    content = content.replace(regex, `<span class="variable-preview">${sampleValues[v] || `[${v}]`}</span>`)
  })
  return content
})

const sanitizedPreview = computed(() => sanitizeHtml(previewContent.value))

// 加载数据
onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try {
      const res = await request.get(`/v1/prompts/${route.params.id}`)
      const data = res.data
      if (data) {
        Object.assign(formState, {
          name: data.name || '',
          description: data.description || '',
          category: data.category,
          content: data.content || '',
          variables: data.variables || [],
          ttm_stage: data.ttm_stage,
          trigger_domain: data.trigger_domain,
          is_active: data.is_active ?? true
        })
      }
    } catch (e) {
      console.error('加载Prompt模板失败:', e)
      message.error('加载模板失败')
    }
    loading.value = false
  }
})

// 添加变量
const handleAddVariable = () => {
  if (!newVariable.value) return
  if (formState.variables?.includes(newVariable.value)) {
    message.warning('变量已存在')
    return
  }
  formState.variables = [...(formState.variables || []), newVariable.value]
  newVariable.value = ''
}

// 移除变量
const handleRemoveVariable = (variable: string) => {
  formState.variables = formState.variables?.filter(v => v !== variable)
}

// 格式化变量显示
const formatVariable = (v: string) => {
  return '{{' + v + '}}'
}

// 插入变量到内容
const handleInsertVariable = (variable: string) => {
  formState.content = (formState.content || '') + formatVariable(variable)
}

// 同步提取的变量
const handleSyncVariables = () => {
  formState.variables = extractedVariables.value
  message.success('已同步变量')
}

// 保存
const handleSave = async () => {
  if (!formState.name) {
    message.error('请输入模板名称')
    return
  }
  if (!formState.category) {
    message.error('请选择分类')
    return
  }
  if (!formState.content) {
    message.error('请输入模板内容')
    return
  }

  loading.value = true
  try {
    if (isEdit.value) {
      await request.put(`/v1/prompts/${route.params.id}`, formState)
    } else {
      await request.post('/v1/prompts', formState)
    }
    message.success('保存成功')
    router.push('/prompts/list')
  } catch (e) {
    console.error('保存Prompt模板失败:', e)
    message.error('保存失败')
  }
  loading.value = false
}

// 返回列表
const handleBack = () => {
  router.push('/prompts/list')
}
</script>

<template>
  <div class="prompt-edit-page">
    <Card :title="pageTitle" :bordered="false" :loading="loading">
      <template #extra>
        <Space>
          <Button @click="handleBack">
            <template #icon><ArrowLeftOutlined /></template>
            返回
          </Button>
          <Button type="primary" @click="handleSave" :loading="loading">
            <template #icon><SaveOutlined /></template>
            保存
          </Button>
        </Space>
      </template>

      <Form layout="vertical" :model="formState" style="max-width: 800px">
        <!-- 基本信息 -->
        <div class="section-title">基本信息</div>

        <FormItem label="模板名称" required>
          <Input
            v-model:value="formState.name"
            placeholder="请输入模板名称"
            :maxlength="50"
            show-count
          />
        </FormItem>

        <FormItem label="模板描述">
          <Input
            v-model:value="formState.description"
            placeholder="请输入模板描述"
            :maxlength="200"
            show-count
          />
        </FormItem>

        <Space :size="16" style="width: 100%">
          <FormItem label="分类" required style="width: 200px">
            <Select
              v-model:value="formState.category"
              placeholder="请选择分类"
              :options="categories"
            />
          </FormItem>

          <FormItem label="TTM阶段" style="width: 200px">
            <Select
              v-model:value="formState.ttm_stage"
              placeholder="请选择阶段"
              allow-clear
            >
              <a-select-option
                v-for="(config, key) in TTM_STAGES"
                :key="key"
                :value="key"
              >
                {{ config.label }}
              </a-select-option>
            </Select>
          </FormItem>

          <FormItem label="触发域" style="width: 200px">
            <Select
              v-model:value="formState.trigger_domain"
              placeholder="请选择触发域"
              allow-clear
            >
              <a-select-option
                v-for="(config, key) in TRIGGER_DOMAINS"
                :key="key"
                :value="key"
              >
                {{ config.label }}
              </a-select-option>
            </Select>
          </FormItem>
        </Space>

        <Divider />

        <!-- 模板内容 -->
        <div class="section-title">模板内容</div>

        <FormItem label="变量管理">
          <div class="variable-section">
            <Space wrap>
              <Tag
                v-for="v in formState.variables"
                :key="v"
                color="blue"
                closable
                @close="handleRemoveVariable(v)"
                @click="handleInsertVariable(v)"
                style="cursor: pointer"
              >
                {{ formatVariable(v) }}
              </Tag>
            </Space>
            <div class="variable-input">
              <Input
                v-model:value="newVariable"
                placeholder="添加变量名"
                style="width: 150px"
                @press-enter="handleAddVariable"
              />
              <Button @click="handleAddVariable">
                <template #icon><PlusOutlined /></template>
              </Button>
              <Button v-if="extractedVariables.length" @click="handleSyncVariables">
                同步变量
              </Button>
            </div>
          </div>
          <div class="variable-hint">
            提示：点击变量可插入到内容中，使用双花括号包裹变量名的格式
          </div>
        </FormItem>

        <FormItem label="Prompt 内容" required>
          <Input.TextArea
            v-model:value="formState.content"
            placeholder="请输入 Prompt 内容，使用 {{变量名}} 插入变量"
            :rows="6"
            :maxlength="2000"
            show-count
          />
        </FormItem>

        <!-- 预览 -->
        <FormItem label="效果预览">
          <Alert type="info" class="preview-alert">
            <template #message>
              <div v-html="sanitizedPreview" class="preview-content"></div>
            </template>
          </Alert>
        </FormItem>

        <Divider />

        <!-- 状态设置 -->
        <FormItem label="启用状态">
          <Switch v-model:checked="formState.is_active" />
          <span style="margin-left: 8px">{{ formState.is_active ? '已启用' : '已停用' }}</span>
        </FormItem>
      </Form>
    </Card>
  </div>
</template>

<style scoped>
.prompt-edit-page {
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  color: #1890ff;
}

.variable-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-input {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.variable-hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.preview-alert {
  background: #f6f8fa;
}

.preview-content {
  line-height: 1.8;
}

:deep(.variable-preview) {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  padding: 0 4px;
  color: #1890ff;
}
</style>
