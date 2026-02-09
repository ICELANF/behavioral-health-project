<template>
  <div class="module-manage">
    <a-page-header title="课程模块管理" sub-title="管理学分体系课程模块" />

    <!-- 筛选栏 -->
    <a-card class="mb-4">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select v-model:value="filters.module_type" placeholder="模块类型" allowClear style="width:100%">
            <a-select-option value="M1_BEHAVIOR">M1 行为处方</a-select-option>
            <a-select-option value="M2_LIFESTYLE">M2 生活方式</a-select-option>
            <a-select-option value="M3_MINDSET">M3 心智成长</a-select-option>
            <a-select-option value="M4_COACHING">M4 教练技术</a-select-option>
            <a-select-option value="ELECTIVE">选修</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filters.target_role" placeholder="目标角色" allowClear style="width:100%">
            <a-select-option value="OBSERVER">观察者</a-select-option>
            <a-select-option value="GROWER">成长者</a-select-option>
            <a-select-option value="SHARER">分享者</a-select-option>
            <a-select-option value="COACH">教练</a-select-option>
            <a-select-option value="PROMOTER">推广者</a-select-option>
            <a-select-option value="MASTER">大师</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-checkbox v-model:checked="filters.include_inactive">包含停用</a-checkbox>
        </a-col>
        <a-col :span="8" style="text-align:right">
          <a-space>
            <a-button @click="loadModules">查询</a-button>
            <a-button type="primary" @click="openCreate">新建模块</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 表格 -->
    <a-table
      :columns="columns"
      :data-source="modules"
      :loading="loading"
      :pagination="{ current: page, pageSize, total, onChange: onPageChange }"
      row-key="id"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_active'">
          <a-tag :color="record.is_active ? 'green' : 'red'">{{ record.is_active ? '启用' : '停用' }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="openEdit(record)">编辑</a>
            <a-popconfirm title="确认停用?" @confirm="handleDelete(record.id)">
              <a style="color:red" v-if="record.is_active">停用</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑模块' : '新建模块'"
      @ok="handleSave"
      :confirmLoading="saving"
      width="640px"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="模块编码" required>
              <a-input v-model:value="form.code" :disabled="!!editingId" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="模块名称" required>
              <a-input v-model:value="form.title" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" :rows="2" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="模块类型">
              <a-select v-model:value="form.module_type">
                <a-select-option value="M1_BEHAVIOR">M1 行为处方</a-select-option>
                <a-select-option value="M2_LIFESTYLE">M2 生活方式</a-select-option>
                <a-select-option value="M3_MINDSET">M3 心智成长</a-select-option>
                <a-select-option value="M4_COACHING">M4 教练技术</a-select-option>
                <a-select-option value="ELECTIVE">选修</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="干预层级">
              <a-select v-model:value="form.tier" allowClear>
                <a-select-option value="T1_PRESCRIPTION">T1 处方级</a-select-option>
                <a-select-option value="T2_LIFESTYLE">T2 生活方式</a-select-option>
                <a-select-option value="T3_GROWTH">T3 成长</a-select-option>
                <a-select-option value="T4_RESEARCH">T4 研究</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="目标角色">
              <a-select v-model:value="form.target_role" allowClear>
                <a-select-option value="OBSERVER">观察者</a-select-option>
                <a-select-option value="GROWER">成长者</a-select-option>
                <a-select-option value="SHARER">分享者</a-select-option>
                <a-select-option value="COACH">教练</a-select-option>
                <a-select-option value="PROMOTER">推广者</a-select-option>
                <a-select-option value="MASTER">大师</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="学分值">
              <a-input-number v-model:value="form.credit_value" :min="0" :max="100" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="理论占比">
              <a-input-number v-model:value="form.theory_ratio" :min="0" :max="1" :step="0.1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="排序">
              <a-input-number v-model:value="form.sort_order" :min="0" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="前置模块">
          <a-input v-model:value="form.prereq_modules" placeholder="逗号分隔模块编码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { creditApi } from '@/api/credit-promotion'

const loading = ref(false)
const saving = ref(false)
const modules = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const modalVisible = ref(false)
const editingId = ref('')

const filters = reactive({
  module_type: undefined as string | undefined,
  target_role: undefined as string | undefined,
  include_inactive: false,
})

const form = reactive({
  code: '',
  title: '',
  description: '',
  module_type: 'M1_BEHAVIOR',
  elective_cat: undefined as string | undefined,
  tier: undefined as string | undefined,
  target_role: undefined as string | undefined,
  credit_value: 5,
  theory_ratio: undefined as number | undefined,
  prereq_modules: '',
  content_ref: '',
  sort_order: 0,
})

const columns = [
  { title: '编码', dataIndex: 'code', key: 'code', width: 120 },
  { title: '名称', dataIndex: 'title', key: 'title' },
  { title: '类型', dataIndex: 'module_type', key: 'module_type', width: 120 },
  { title: '层级', dataIndex: 'tier', key: 'tier', width: 120 },
  { title: '角色', dataIndex: 'target_role', key: 'target_role', width: 100 },
  { title: '学分', dataIndex: 'credit_value', key: 'credit_value', width: 70 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

async function loadModules() {
  loading.value = true
  try {
    const res = await creditApi.adminListModules({
      module_type: filters.module_type,
      target_role: filters.target_role,
      include_inactive: filters.include_inactive,
      skip: (page.value - 1) * pageSize,
      limit: pageSize,
    })
    modules.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadModules()
}

function openCreate() {
  editingId.value = ''
  Object.assign(form, {
    code: '', title: '', description: '', module_type: 'M1_BEHAVIOR',
    elective_cat: undefined, tier: undefined, target_role: undefined,
    credit_value: 5, theory_ratio: undefined, prereq_modules: '', content_ref: '', sort_order: 0,
  })
  modalVisible.value = true
}

function openEdit(record: any) {
  editingId.value = record.id
  Object.assign(form, {
    code: record.code,
    title: record.title,
    description: record.description || '',
    module_type: record.module_type,
    elective_cat: record.elective_cat,
    tier: record.tier,
    target_role: record.target_role,
    credit_value: record.credit_value,
    theory_ratio: record.theory_ratio,
    prereq_modules: record.prereq_modules || '',
    content_ref: record.content_ref || '',
    sort_order: record.sort_order || 0,
  })
  modalVisible.value = true
}

async function handleSave() {
  if (!form.code || !form.title) {
    message.warning('编码和名称不能为空')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await creditApi.adminUpdateModule(editingId.value, { ...form })
      message.success('模块已更新')
    } else {
      await creditApi.adminCreateModule({ ...form })
      message.success('模块已创建')
    }
    modalVisible.value = false
    loadModules()
  } catch (e) {
    console.error('保存失败', e)
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await creditApi.adminDeleteModule(id)
    message.success('模块已停用')
    loadModules()
  } catch (e) {
    console.error('停用失败', e)
  }
}

onMounted(loadModules)
</script>

<style scoped>
.module-manage { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
</style>
