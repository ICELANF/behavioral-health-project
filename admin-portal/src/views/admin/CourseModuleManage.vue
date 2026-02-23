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

    <!-- 列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="modules.length === 0 && !loading" description="暂无课程模块" />
        <ListCard v-for="m in modules" :key="m.id">
          <template #title>
            <span style="font-family: monospace; color: #1890ff">{{ m.code }}</span>
            <span style="margin-left: 8px">{{ m.title }}</span>
          </template>
          <template #subtitle>{{ m.description || '暂无描述' }}</template>
          <template #meta>
            <a-tag color="blue" size="small">{{ m.module_type }}</a-tag>
            <a-tag v-if="m.tier" size="small">{{ m.tier }}</a-tag>
            <a-tag v-if="m.target_role" color="purple" size="small">{{ m.target_role }}</a-tag>
            <span>{{ m.credit_value }} 学分</span>
            <a-tag :color="m.is_active ? 'green' : 'red'" size="small">{{ m.is_active ? '启用' : '停用' }}</a-tag>
          </template>
          <template #actions>
            <a-button type="link" size="small" @click="openEdit(m)">编辑</a-button>
            <a-popconfirm v-if="m.is_active" title="确认停用?" @confirm="handleDelete(m.id)">
              <a-button type="link" size="small" danger>停用</a-button>
            </a-popconfirm>
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="page"
        :page-size="pageSize"
        :total="total"
        show-size-changer
        :show-total="(t: number) => `共 ${t} 条`"
        @change="onPageChange"
      />
    </div>

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
import ListCard from '@/components/core/ListCard.vue'

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

// columns removed — now using ListCard layout

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
.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
