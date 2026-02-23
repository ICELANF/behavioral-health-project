<template>
  <div class="coach-student-list-page">
    <div class="page-header">
      <a-button type="text" @click="$router.push('/coach-portal')">
        <LeftOutlined /> 返回工作台
      </a-button>
      <h2>待跟进学员 ({{ filteredStudents.length }})</h2>
    </div>

    <!-- 搜索条 -->
    <a-input-search
      v-model:value="keyword"
      :placeholder="searchScope.placeholder.value"
      allow-clear
      style="margin-bottom: 12px"
      @search="() => {}"
    />

    <!-- 紧凑分类过滤 (预设 + 风险 + 活跃度) -->
    <ClassificationFilterBar
      :filters="clsFilters.activeFilters.value"
      :active-preset="clsFilters.activePreset.value"
      :sort-by="clsFilters.filters.sort_by"
      :visible-dimensions="['risk', 'activity']"
      @preset="onPreset"
      @filter="onFilter"
      @sort="onSort"
      @clear="onClear"
    />

    <div v-if="loading" style="text-align:center;padding:60px 0">
      <a-spin size="large" tip="加载学员数据..." />
    </div>

    <a-alert v-else-if="error" type="error" :message="error" show-icon style="margin-bottom: 16px" />

    <a-empty v-else-if="filteredStudents.length === 0" description="暂无待跟进学员" />

    <div v-else class="list-container">
      <ListCard
        v-for="student in filteredStudents"
        :key="student.id"
        @click="openDetail(student)"
      >
        <template #avatar>
          <div class="avatar-wrap">
            <a-avatar :size="48" :src="student.avatar">
              {{ student.name?.charAt(0) }}
            </a-avatar>
            <span class="stage-badge" :class="student.stage">
              {{ stageLabel(student.stage) }}
            </span>
          </div>
        </template>
        <template #title>{{ student.name }}</template>
        <template #subtitle>{{ student.condition }}</template>
        <template #meta>
          <span class="meta-item">
            <ClockCircleOutlined /> {{ student.lastContact }}
          </span>
          <a-tag v-if="student.classification" :color="getTagColor('risk', student.classification.risk)" size="small">
            {{ getValueLabel('risk', student.classification.risk) }}
          </a-tag>
          <a-tag v-if="student.classification" :color="getTagColor('activity', student.classification.activity)" size="small">
            {{ getValueLabel('activity', student.classification.activity) }}
          </a-tag>
          <a-tag v-if="student.priority === 'urgent'" color="red" size="small">紧急</a-tag>
          <a-tag v-else-if="student.priority === 'important'" color="orange" size="small">重要</a-tag>
          <a-tag v-if="student.healthData?.fastingGlucose" size="small">
            空腹 {{ student.healthData.fastingGlucose }} mmol/L
          </a-tag>
        </template>
        <template #actions>
          <a-button type="primary" size="small" @click.stop="$router.push(`/coach/student-assessment/${student.id}`)">
            查看测评
          </a-button>
          <a-button size="small" @click.stop="$router.push(`/coach/student-profile/${student.id}`)">
            行为画像
          </a-button>
        </template>
      </ListCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { LeftOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'
import ListCard from '@/components/core/ListCard.vue'
import ClassificationFilterBar from '@/components/coach/ClassificationFilterBar.vue'
import { useSearchScope } from '@/composables/useSearchScope'
import { useStudentClassification, getTagColor, getValueLabel } from '@/composables/useStudentClassification'

const router = useRouter()
const searchScope = useSearchScope()
const clsFilters = useStudentClassification()

const loading = ref(false)
const error = ref('')
const students = ref<any[]>([])
const keyword = ref('')

const filteredStudents = computed(() => {
  if (!keyword.value.trim()) return students.value
  const kw = keyword.value.trim().toLowerCase()
  return students.value.filter(s =>
    (s.name || '').toLowerCase().includes(kw) ||
    (s.condition || '').toLowerCase().includes(kw)
  )
})

const stageLabels: Record<string, string> = {
  S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
  S4: '行动期', S5: '坚持期', S6: '融入期',
}
const stageLabel = (s: string) => stageLabels[s] || s || '未评估'

function openDetail(student: any) {
  router.push(`/coach/student-assessment/${student.id}`)
}

// ── Filter event handlers ──
function onPreset(preset: any) {
  clsFilters.applyPreset(preset)
  fetchStudents()
}
function onFilter(dimension: string, value: string) {
  clsFilters.setFilter(dimension, value)
  fetchStudents()
}
function onSort(val: string) {
  clsFilters.filters.sort_by = val
  fetchStudents()
}
function onClear() {
  clsFilters.clearFilters()
  fetchStudents()
}

async function fetchStudents() {
  loading.value = true
  error.value = ''
  try {
    // Use /v1/coach/students with classification filters
    const params: any = { sort_by: clsFilters.filters.sort_by }
    if (clsFilters.filters.risk) params.risk = clsFilters.filters.risk
    if (clsFilters.filters.activity) params.activity = clsFilters.filters.activity
    if (clsFilters.filters.behavior) params.behavior = clsFilters.filters.behavior
    if (clsFilters.filters.needs) params.needs = clsFilters.filters.needs
    if (clsFilters.filters.priority) params.priority = clsFilters.filters.priority

    const res = await request.get('/v1/coach/students', { params })
    const data = res.data
    students.value = (data.students || []).map((st: any) => ({
      id: st.id,
      name: st.full_name || st.username,
      avatar: (st.profile || {}).avatar || '',
      condition: (st.profile || {}).condition || '行为健康管理',
      stage: st.current_stage || 'unknown',
      lastContact: st.last_active ? new Date(st.last_active).toLocaleDateString('zh-CN') : '未知',
      priority: st.classification?.priority_bucket || 'normal',
      healthData: {
        fastingGlucose: (st.profile || {}).fasting_glucose ?? null,
        postprandialGlucose: (st.profile || {}).postprandial_glucose ?? null,
        weight: (st.profile || {}).weight ?? null,
        exerciseMinutes: (st.profile || {}).exercise_minutes ?? 0,
      },
      microAction7d: { completed: 0, total: 0 },
      riskFlags: st.classification?.risk_flags || [],
      classification: st.classification || null,
    }))
  } catch (e: any) {
    error.value = '加载学员数据失败，请稍后重试'
    console.error('CoachStudentList fetch error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStudents()
})
</script>

<style scoped>
.coach-student-list-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.list-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.avatar-wrap {
  position: relative;
}
.stage-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  color: #fff;
  white-space: nowrap;
  background: #999;
}
.stage-badge.S0, .stage-badge.S1 { background: #ff4d4f; }
.stage-badge.S2, .stage-badge.S3 { background: #faad14; }
.stage-badge.S4, .stage-badge.S5 { background: #52c41a; }
.stage-badge.S6 { background: #1890ff; }
.meta-item {
  font-size: 12px;
  color: #999;
}
</style>
