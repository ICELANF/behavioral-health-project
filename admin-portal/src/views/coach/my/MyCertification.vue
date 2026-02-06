<template>
  <div class="my-certification">
    <div class="page-header">
      <h2>我的认证</h2>
    </div>

    <!-- Current Level -->
    <a-card class="level-card" style="margin-bottom: 16px">
      <div class="current-level">
        <div class="level-badge" :style="{ background: currentLevel.color }">
          {{ currentLevel.badge }}
        </div>
        <div class="level-info">
          <h3>{{ currentLevel.name }}</h3>
          <p class="level-desc">{{ currentLevel.description }}</p>
          <p class="level-since">认证时间: {{ currentLevel.since }}</p>
        </div>
      </div>

      <!-- Upgrade progress -->
      <div class="upgrade-section">
        <div class="upgrade-header">
          <span>升级至 {{ nextLevel.name }}</span>
          <span class="upgrade-pct">{{ upgradeProgress }}%</span>
        </div>
        <a-progress :percent="upgradeProgress" :stroke-color="{ from: currentLevel.color, to: nextLevel.color }" :show-info="false" />
        <div class="upgrade-requirements">
          <div v-for="req in requirements" :key="req.label" class="req-item" :class="{ completed: req.completed }">
            <span class="req-check">{{ req.completed ? '✓' : '○' }}</span>
            <span class="req-label">{{ req.label }}</span>
            <span class="req-value">{{ req.current }} / {{ req.target }}</span>
          </div>
        </div>
        <a-button type="primary" :disabled="upgradeProgress < 100" block style="margin-top: 12px">
          {{ upgradeProgress >= 100 ? '申请晋级' : '未达到晋级条件' }}
        </a-button>
      </div>
    </a-card>

    <!-- Completed Courses -->
    <a-card title="已完成课程" style="margin-bottom: 16px">
      <div v-for="course in completedCourses" :key="course.id" class="course-item">
        <div class="course-info">
          <span class="course-name">{{ course.name }}</span>
          <span class="course-date">完成于 {{ course.completedDate }}</span>
        </div>
        <div class="course-right">
          <a-tag :color="course.required ? 'blue' : 'default'">{{ course.required ? '必修' : '选修' }}</a-tag>
          <span class="course-score">{{ course.score }}分</span>
        </div>
      </div>
    </a-card>

    <!-- Exam History -->
    <a-card title="考试记录">
      <a-table :dataSource="examHistory" :columns="examColumns" rowKey="id" size="small" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'result'">
            <a-tag :color="record.passed ? 'green' : 'red'">{{ record.passed ? '通过' : '未通过' }}</a-tag>
          </template>
          <template v-if="column.key === 'score'">
            <span :style="{ color: record.passed ? '#389e0d' : '#cf1322', fontWeight: 600 }">{{ record.score }}</span> / {{ record.total }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const currentLevel = ref({
  badge: 'L2',
  name: '中级健康教练',
  description: '具备独立开展行为健康干预的能力，可指导初级教练',
  color: '#1890ff',
  since: '2024-08-15',
})

const nextLevel = ref({
  name: '高级健康教练 (L3)',
  color: '#722ed1',
})

const requirements = ref([
  { label: '服务学员数', current: 28, target: 30, completed: false },
  { label: '干预成功率', current: 74, target: 70, completed: true },
  { label: '必修课程完成', current: 5, target: 5, completed: true },
  { label: '督导评分', current: 4.2, target: 4.0, completed: true },
  { label: '通过L3考试', current: 0, target: 1, completed: false },
])

const upgradeProgress = computed(() => {
  const completed = requirements.value.filter(r => r.completed).length
  return Math.round((completed / requirements.value.length) * 100)
})

const completedCourses = ref([
  { id: '1', name: '行为健康教练核心能力', completedDate: '2024-12-20', required: true, score: 92 },
  { id: '2', name: '动机访谈技术进阶', completedDate: '2024-11-15', required: true, score: 88 },
  { id: '3', name: 'TTM模型在慢病管理中的应用', completedDate: '2024-10-28', required: true, score: 95 },
  { id: '4', name: '压力管理与正念技术', completedDate: '2024-10-10', required: false, score: 90 },
  { id: '5', name: '营养学基础与饮食干预', completedDate: '2024-09-20', required: true, score: 85 },
])

const examHistory = ref([
  { id: '1', name: 'L2认证考试', date: '2024-08-10', score: 86, total: 100, passed: true },
  { id: '2', name: 'L1认证考试', date: '2024-03-15', score: 92, total: 100, passed: true },
  { id: '3', name: 'L0入门考试', date: '2024-01-20', score: 78, total: 100, passed: true },
])

const examColumns = [
  { title: '考试名称', dataIndex: 'name' },
  { title: '考试日期', dataIndex: 'date', width: 120 },
  { title: '成绩', key: 'score', width: 100 },
  { title: '结果', key: 'result', width: 80 },
]
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.current-level { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.level-badge { width: 64px; height: 64px; border-radius: 50%; color: #fff; font-size: 24px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.level-info h3 { margin: 0 0 4px; font-size: 18px; }
.level-desc { margin: 0; font-size: 13px; color: #666; }
.level-since { margin: 2px 0 0; font-size: 12px; color: #999; }

.upgrade-section { background: #fafafa; border-radius: 8px; padding: 16px; }
.upgrade-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; font-weight: 500; }
.upgrade-pct { color: #1890ff; }
.upgrade-requirements { margin-top: 12px; }
.req-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.req-item.completed { color: #389e0d; }
.req-check { font-size: 14px; min-width: 20px; }
.req-label { flex: 1; }
.req-value { font-weight: 500; }

.course-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.course-name { font-size: 14px; font-weight: 500; display: block; }
.course-date { font-size: 12px; color: #999; }
.course-right { display: flex; align-items: center; gap: 8px; }
.course-score { font-size: 14px; font-weight: 600; color: #1890ff; }
</style>
