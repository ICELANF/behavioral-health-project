<template>
  <div class="companion-manage">
    <a-page-header title="同道者关系管理" sub-title="查看和管理带教关系" />

    <!-- 筛选栏 -->
    <a-card class="mb-4">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select v-model:value="filters.status" placeholder="状态筛选" allowClear style="width:100%">
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="graduated">已毕业</a-select-option>
            <a-select-option value="dropped">已退出</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-input-number v-model:value="filters.mentor_id" placeholder="导师ID" style="width:100%" />
        </a-col>
        <a-col :span="12" style="text-align:right">
          <a-button type="primary" @click="loadRelations">查询</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <a-empty v-if="relations.length === 0 && !loading" description="暂无同道者关系" />
        <ListCard v-for="r in relations" :key="r.id">
          <template #avatar>
            <a-avatar :size="40" style="background: #1890ff">{{ (r.mentor_name || '?')[0] }}</a-avatar>
          </template>
          <template #title>
            <span>{{ r.mentor_name || `ID ${r.mentor_id}` }}</span>
            <span style="color: #999; margin: 0 6px">→</span>
            <span>{{ r.mentee_name || `ID ${r.mentee_id}` }}</span>
          </template>
          <template #subtitle>
            导师角色: {{ r.mentor_role || '-' }} · 学员角色: {{ r.mentee_role || '-' }}
          </template>
          <template #meta>
            <a-tag :color="statusColor(r.status)">{{ statusLabel(r.status) }}</a-tag>
            <span>质量分: {{ r.quality_score ? r.quality_score.toFixed(1) : '-' }}</span>
            <span style="color: #999">开始: {{ r.started_at || '-' }}</span>
            <span v-if="r.graduated_at" style="color: #999">毕业: {{ r.graduated_at }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { companionApi } from '@/api/credit-promotion'
import ListCard from '@/components/core/ListCard.vue'

const loading = ref(false)
const relations = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({
  status: undefined as string | undefined,
  mentor_id: undefined as number | undefined,
})

// columns removed — now using ListCard layout

function statusColor(s: string) {
  return s === 'active' ? 'blue' : s === 'graduated' ? 'green' : 'red'
}

function statusLabel(s: string) {
  return s === 'active' ? '进行中' : s === 'graduated' ? '已毕业' : '已退出'
}

async function loadRelations() {
  loading.value = true
  try {
    const res = await companionApi.adminListAll({
      status: filters.status,
      mentor_id: filters.mentor_id,
      skip: (page.value - 1) * pageSize,
      limit: pageSize,
    })
    relations.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadRelations()
}

onMounted(loadRelations)
</script>

<style scoped>
.companion-manage { padding: 16px; }
.mb-4 { margin-bottom: 16px; }
.list-card-container { display: flex; flex-direction: column; gap: 10px; }
</style>
