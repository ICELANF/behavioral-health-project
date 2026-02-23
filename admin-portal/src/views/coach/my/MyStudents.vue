<template>
  <div class="my-students">
    <div class="page-header">
      <h2>我的学员</h2>
      <div class="header-actions">
        <a-input-search v-model:value="searchText" placeholder="搜索学员" style="width: 200px" @search="loadStudents" allowClear />
        <a-select v-model:value="viewMode" style="width: 140px">
          <a-select-option value="list">列表视图</a-select-option>
          <a-select-option value="kanban">阶段看板</a-select-option>
          <a-select-option value="priority">优先级看板</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- Stats: 优先级统计 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :xs="12" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="紧急" :value="summary.by_priority?.urgent || 0" value-style="color: #ff4d4f" :loading="loading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="重要" :value="summary.by_priority?.important || 0" value-style="color: #fa8c16" :loading="loading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="常规" :value="summary.by_priority?.normal || 0" value-style="color: #1890ff" :loading="loading" />
        </a-card>
      </a-col>
      <a-col :xs="12" :sm="12" :lg="6">
        <a-card size="small">
          <a-statistic title="例行" :value="summary.by_priority?.routine || 0" :loading="loading" />
        </a-card>
      </a-col>
    </a-row>

    <!-- Classification Filter Bar -->
    <ClassificationFilterBar
      :filters="classificationCtrl.activeFilters.value"
      :active-preset="classificationCtrl.activePreset.value"
      :sort-by="classificationCtrl.filters.sort_by"
      @preset="onPreset"
      @filter="onFilter"
      @sort="onSort"
      @clear="onClear"
    />

    <!-- Kanban View (阶段) -->
    <div v-if="viewMode === 'kanban'" class="kanban-board">
      <div v-for="group in kanbanGroups" :key="group.key" class="kanban-column">
        <div class="column-header" :style="{ borderColor: group.color }">
          <span class="column-title">{{ group.title }}</span>
          <span class="column-count">{{ group.students.length }}</span>
        </div>
        <div class="column-body">
          <div v-for="s in group.students" :key="s.id" class="student-card" @click="router.push(`/coach/student-assessment/${s.id}`)">
            <div class="student-top">
              <a-avatar :size="32" :style="{ background: group.color }">{{ (s.name || '?')[0] }}</a-avatar>
              <div class="student-info">
                <span class="student-name">{{ s.name }}</span>
                <a-tag v-if="s.classification" :color="getTagColor('risk', s.classification.risk)" size="small">
                  {{ getValueLabel('risk', s.classification.risk) }}
                </a-tag>
              </div>
              <span v-if="s.classification" class="priority-dot" :style="{ background: getPriorityStyle(s.classification.priority_bucket).color }"></span>
            </div>
            <div class="student-metrics">
              <a-tag v-if="s.classification" :color="getTagColor('activity', s.classification.activity)" size="small">
                {{ getValueLabel('activity', s.classification.activity) }}
              </a-tag>
              <span v-if="s.classification" style="font-size: 11px; color: #999">{{ s.classification.priority_score?.toFixed(0) }}分</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Priority Kanban View (优先级) -->
    <div v-if="viewMode === 'priority'" class="kanban-board">
      <div v-for="group in priorityKanbanGroups" :key="group.key" class="kanban-column">
        <div class="column-header" :style="{ borderColor: group.color }">
          <span class="column-title">{{ group.title }}</span>
          <span class="column-count">{{ group.students.length }}</span>
        </div>
        <div class="column-body">
          <div v-for="s in group.students" :key="s.id" class="student-card" @click="router.push(`/coach/student-assessment/${s.id}`)">
            <div class="student-top">
              <a-avatar :size="32" :style="{ background: group.color }">{{ (s.name || '?')[0] }}</a-avatar>
              <div class="student-info">
                <span class="student-name">{{ s.name }}</span>
              </div>
            </div>
            <div class="student-metrics">
              <a-tag v-if="s.classification" :color="getTagColor('behavior', s.classification.behavior)" size="small">
                {{ getValueLabel('behavior', s.classification.behavior) }}
              </a-tag>
              <a-tag v-if="s.classification" :color="getTagColor('risk', s.classification.risk)" size="small">
                {{ getValueLabel('risk', s.classification.risk) }}
              </a-tag>
              <a-tag v-if="s.classification" :color="getTagColor('activity', s.classification.activity)" size="small">
                {{ getValueLabel('activity', s.classification.activity) }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-if="viewMode === 'list'" class="list-card-container">
      <a-spin v-if="loading" style="display: block; text-align: center; padding: 32px" />
      <a-empty v-else-if="allStudents.length === 0" description="暂无学员" />
      <ListCard
        v-for="s in allStudents"
        :key="s.id"
        @click="router.push(`/coach/student-assessment/${s.id}`)"
      >
        <template #avatar>
          <a-avatar :size="40">{{ (s.name || '?')[0] }}</a-avatar>
        </template>
        <template #title>
          <span>{{ s.name }}</span>
          <a-badge v-if="s.classification?.priority_bucket === 'urgent'" status="error" style="margin-left: 6px" />
          <a-badge v-else-if="s.classification?.priority_bucket === 'important'" status="warning" style="margin-left: 6px" />
        </template>
        <template #subtitle>
          <a-tag v-if="s.classification" :color="getTagColor('behavior', s.classification.behavior)" size="small">
            {{ getValueLabel('behavior', s.classification.behavior) }}
          </a-tag>
          <a-tag v-if="s.classification" :color="getTagColor('risk', s.classification.risk)" size="small">
            {{ getValueLabel('risk', s.classification.risk) }}
          </a-tag>
          <a-tag v-if="s.classification" :color="getTagColor('activity', s.classification.activity)" size="small">
            {{ getValueLabel('activity', s.classification.activity) }}
          </a-tag>
        </template>
        <template #meta>
          <span v-if="s.classification?.needs_detail?.length" style="color: #666; font-size: 12px">
            {{ s.classification.needs_detail.slice(0, 3).join(' · ') }}
          </span>
          <span style="color: #999; font-size: 12px">优先级 {{ s.classification?.priority_score?.toFixed(0) || '-' }}</span>
          <span v-if="s.lastActive" style="color: #999; font-size: 12px">最近: {{ s.lastActive }}</span>
        </template>
        <template #actions>
          <a-button size="small" type="link" @click.stop="router.push(`/coach/student-assessment/${s.id}`)">查看轨迹</a-button>
          <a-button size="small" type="link" @click.stop="goMessage(s.id)">发消息</a-button>
          <a-button size="small" type="link" @click.stop="goAssessment(s.id)">安排测评</a-button>
        </template>
      </ListCard>

      <!-- Pagination -->
      <div v-if="totalStudents > pageSize" style="display: flex; justify-content: flex-end; margin-top: 12px">
        <a-pagination
          v-model:current="currentPage"
          :page-size="pageSize"
          :total="totalStudents"
          size="small"
          @change="onPageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'
import ListCard from '@/components/core/ListCard.vue'
import ClassificationFilterBar from '@/components/coach/ClassificationFilterBar.vue'
import { useStudentClassification, getTagColor, getValueLabel, getPriorityStyle } from '@/composables/useStudentClassification'

const router = useRouter()
const classificationCtrl = useStudentClassification()

const searchText = ref('')
const viewMode = ref('list')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = 50
const totalStudents = ref(0)

const allStudents = ref<any[]>([])
const summary = ref<any>({})

const loadStudents = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize,
      sort_by: classificationCtrl.filters.sort_by,
    }
    if (searchText.value) params.search = searchText.value
    if (classificationCtrl.filters.behavior) params.behavior = classificationCtrl.filters.behavior
    if (classificationCtrl.filters.needs) params.needs = classificationCtrl.filters.needs
    if (classificationCtrl.filters.risk) params.risk = classificationCtrl.filters.risk
    if (classificationCtrl.filters.activity) params.activity = classificationCtrl.filters.activity
    if (classificationCtrl.filters.priority) params.priority = classificationCtrl.filters.priority

    const { data } = await request.get('/v1/coach/students', { params })
    allStudents.value = (data.students || []).map((s: any) => ({
      id: s.id,
      name: s.full_name || s.username,
      classification: s.classification || null,
      lastActive: s.last_active ? new Date(s.last_active).toLocaleDateString('zh-CN') : '-',
      adherenceRate: s.adherence_rate || 0,
    }))
    totalStudents.value = data.total || 0
    summary.value = data.classification_summary || {}
  } catch (e: any) {
    console.error('加载学员列表失败:', e)
  } finally {
    loading.value = false
  }
}

// ── Kanban: stage groups ──
const kanbanGroups = computed(() => {
  const groups = [
    { key: 'precontemplation', title: '前意识期', color: '#8c8c8c' },
    { key: 'contemplation', title: '意识期', color: '#faad14' },
    { key: 'preparation', title: '准备期', color: '#1890ff' },
    { key: 'action', title: '行动期', color: '#52c41a' },
    { key: 'maintenance', title: '维持期', color: '#389e0d' },
    { key: 'relapse', title: '复发', color: '#ff4d4f' },
    { key: 'growth', title: '成长', color: '#722ed1' },
  ]
  return groups.map(g => ({
    ...g,
    students: allStudents.value.filter(s => s.classification?.behavior === g.key),
  })).filter(g => g.students.length > 0)
})

// ── Kanban: priority groups ──
const priorityKanbanGroups = computed(() => {
  const groups = [
    { key: 'urgent', title: '紧急', color: '#ff4d4f' },
    { key: 'important', title: '重要', color: '#fa8c16' },
    { key: 'normal', title: '常规', color: '#1890ff' },
    { key: 'routine', title: '例行', color: '#8c8c8c' },
  ]
  return groups.map(g => ({
    ...g,
    students: allStudents.value.filter(s => s.classification?.priority_bucket === g.key),
  }))
})

// ── Filter events ──
function onPreset(preset: any) {
  classificationCtrl.applyPreset(preset)
  currentPage.value = 1
  loadStudents()
}

function onFilter(dimension: string, value: string) {
  classificationCtrl.setFilter(dimension, value)
  currentPage.value = 1
  loadStudents()
}

function onSort(val: string) {
  classificationCtrl.filters.sort_by = val
  currentPage.value = 1
  loadStudents()
}

function onClear() {
  classificationCtrl.clearFilters()
  currentPage.value = 1
  loadStudents()
}

function onPageChange(page: number) {
  currentPage.value = page
  loadStudents()
}

const goMessage = (studentId: number) => {
  router.push({ path: '/coach/messages', query: { student_id: studentId } })
}

const goAssessment = (studentId: number) => {
  router.push(`/coach/student-assessment/${studentId}`)
}

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 8px; }

.kanban-board { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.kanban-column { min-width: 200px; flex: 1; background: #fafafa; border-radius: 8px; }
.column-header { padding: 10px 12px; font-weight: 600; font-size: 14px; border-top: 3px solid; display: flex; justify-content: space-between; align-items: center; }
.column-count { background: #e8e8e8; padding: 1px 8px; border-radius: 10px; font-size: 12px; font-weight: 400; }
.column-body { padding: 8px; max-height: 500px; overflow-y: auto; }
.student-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 6px; padding: 10px; margin-bottom: 8px; cursor: pointer; transition: box-shadow 0.2s; }
.student-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.student-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.student-info { flex: 1; display: flex; align-items: center; gap: 6px; }
.student-name { font-size: 13px; font-weight: 500; }
.student-metrics { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.priority-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 768px) {
  .kanban-board { flex-direction: column !important; }
  .kanban-column { min-width: 100% !important; }
}
@media (max-width: 640px) {
  .header-actions { flex-direction: column; width: 100%; }
  .header-actions .ant-input-search,
  .header-actions .ant-select { width: 100% !important; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>
