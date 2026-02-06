<template>
  <div class="student-assessment">
    <div class="page-header">
      <h2>学员测评交互</h2>
      <a-tag color="blue">学员ID: {{ studentId }}</a-tag>
    </div>

    <!-- Student Overview -->
    <a-card style="margin-bottom: 16px">
      <div class="student-overview">
        <a-avatar :size="48" style="background: #1890ff">{{ student.name[0] }}</a-avatar>
        <div class="student-info">
          <h3>{{ student.name }}</h3>
          <div class="student-tags">
            <a-tag :color="stageColor(student.stage)">{{ student.stage }}</a-tag>
            <a-tag :color="riskColor(student.risk)">{{ student.risk }}</a-tag>
          </div>
        </div>
        <div class="student-stats">
          <div class="stat-item">
            <span class="stat-val">{{ student.assessmentCount }}</span>
            <span class="stat-label">已完成测评</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">{{ student.lastActive }}</span>
            <span class="stat-label">最近活跃</span>
          </div>
        </div>
      </div>
    </a-card>

    <!-- Tabs -->
    <a-tabs v-model:activeKey="activeTab">
      <!-- Assessment Records -->
      <a-tab-pane key="records" tab="测评记录">
        <div v-for="record in assessmentRecords" :key="record.id" class="record-card">
          <div class="record-header">
            <span class="record-name">{{ record.name }}</span>
            <a-tag :color="levelTagColor(record.level)">{{ record.level }}</a-tag>
            <span class="record-date">{{ record.date }}</span>
          </div>
          <div class="record-score-bar">
            <div class="bar-bg">
              <div class="bar-fill" :style="{ width: (record.score / record.maxScore * 100) + '%', background: levelTagColor(record.level) }"></div>
            </div>
            <span class="bar-text">{{ record.score }}/{{ record.maxScore }}</span>
          </div>
          <div v-if="record.answers" class="record-details">
            <a-collapse>
              <a-collapse-panel header="查看回答详情">
                <div v-for="(ans, i) in record.answers" :key="i" class="answer-item">
                  <span class="answer-q">Q{{ i + 1 }}: {{ ans.question }}</span>
                  <span class="answer-a">选择: {{ ans.answer }} ({{ ans.score }}分)</span>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>
          <!-- Coach annotation -->
          <div class="annotation-section">
            <a-textarea v-if="editingAnnotation === record.id" v-model:value="annotationText" :rows="2" placeholder="输入评估批注..." />
            <p v-else-if="record.annotation" class="annotation-text">批注: {{ record.annotation }}</p>
            <div class="annotation-actions">
              <a-button v-if="editingAnnotation !== record.id" size="small" type="link" @click="startAnnotation(record)">
                {{ record.annotation ? '编辑批注' : '添加批注' }}
              </a-button>
              <template v-if="editingAnnotation === record.id">
                <a-button size="small" type="primary" @click="saveAnnotation(record)">保存</a-button>
                <a-button size="small" @click="editingAnnotation = null">取消</a-button>
              </template>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- Before/After Comparison -->
      <a-tab-pane key="compare" tab="前后对比">
        <a-card>
          <a-row :gutter="16">
            <a-col :span="12">
              <h4>入组时评估</h4>
              <div v-for="item in comparisonData.before" :key="item.name" class="compare-item">
                <span class="compare-name">{{ item.name }}</span>
                <span class="compare-score" style="color: #cf1322">{{ item.score }}/{{ item.max }}</span>
              </div>
            </a-col>
            <a-col :span="12">
              <h4>最新评估</h4>
              <div v-for="item in comparisonData.after" :key="item.name" class="compare-item">
                <span class="compare-name">{{ item.name }}</span>
                <span class="compare-score" style="color: #389e0d">{{ item.score }}/{{ item.max }}</span>
              </div>
            </a-col>
          </a-row>
          <div class="compare-summary">
            <a-statistic title="总体改善率" :value="improvementRate" suffix="%" :value-style="{ color: improvementRate > 0 ? '#3f8600' : '#cf1322' }" />
          </div>
        </a-card>
      </a-tab-pane>

      <!-- Follow-up -->
      <a-tab-pane key="followup" tab="随访安排">
        <a-card>
          <div v-for="fu in followUps" :key="fu.id" class="followup-item">
            <a-tag :color="fu.status === 'completed' ? 'green' : fu.status === 'scheduled' ? 'blue' : 'orange'">
              {{ fu.status === 'completed' ? '已完成' : fu.status === 'scheduled' ? '已安排' : '待安排' }}
            </a-tag>
            <span class="fu-date">{{ fu.date }}</span>
            <span class="fu-type">{{ fu.type }}</span>
            <span class="fu-notes">{{ fu.notes }}</span>
          </div>
          <a-button type="dashed" block style="margin-top: 12px" @click="scheduleFollowUp">+ 安排新随访</a-button>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'

const route = useRoute()
const studentId = route.params.id || '1'

const activeTab = ref('records')
const editingAnnotation = ref<string | null>(null)
const annotationText = ref('')

const student = ref({
  name: '张伟',
  stage: '行动期',
  risk: '低风险',
  assessmentCount: 6,
  lastActive: '今天',
})

const stageColor = (s: string) => {
  const map: Record<string, string> = { '前思考期': 'red', '思考期': 'orange', '准备期': 'gold', '行动期': 'green', '维持期': 'blue' }
  return map[s] || 'default'
}
const riskColor = (r: string) => {
  const map: Record<string, string> = { '高风险': 'red', '中风险': 'orange', '低风险': 'green' }
  return map[r] || 'default'
}
const levelTagColor = (l: string) => {
  const map: Record<string, string> = { '正常': '#389e0d', '轻度': '#d4b106', '中度': '#d46b08', '重度': '#cf1322' }
  return map[l] || '#999'
}

const assessmentRecords = ref([
  {
    id: 'a1', name: 'PHQ-9 抑郁筛查', date: '2025-01-15', score: 5, maxScore: 27, level: '正常', annotation: '症状明显改善，继续保持',
    answers: [
      { question: '做事时提不起劲或没有兴趣', answer: '好几天', score: 1 },
      { question: '感到心情低落、沮丧或绝望', answer: '完全不会', score: 0 },
      { question: '入睡困难或睡眠过多', answer: '好几天', score: 1 },
    ]
  },
  {
    id: 'a2', name: 'GAD-7 焦虑评估', date: '2025-01-10', score: 8, maxScore: 21, level: '轻度', annotation: '',
    answers: [
      { question: '感觉紧张、不安或急躁', answer: '好几天', score: 1 },
      { question: '不能够停止或控制担忧', answer: '一半以上的天数', score: 2 },
    ]
  },
  { id: 'a3', name: 'PSS-10 压力感知', date: '2024-12-28', score: 22, maxScore: 40, level: '中度', annotation: '压力来源主要是工作，已建议调整策略', answers: null },
])

const comparisonData = ref({
  before: [
    { name: 'PHQ-9', score: 14, max: 27 },
    { name: 'GAD-7', score: 12, max: 21 },
    { name: 'PSS-10', score: 28, max: 40 },
  ],
  after: [
    { name: 'PHQ-9', score: 5, max: 27 },
    { name: 'GAD-7', score: 8, max: 21 },
    { name: 'PSS-10', score: 22, max: 40 },
  ],
})

const improvementRate = ref(38)

const followUps = ref([
  { id: '1', date: '2025-01-20', type: 'PHQ-9 复评', status: 'scheduled', notes: '2周后复评抑郁症状' },
  { id: '2', date: '2025-01-15', type: '电话随访', status: 'completed', notes: '确认运动习惯执行情况' },
  { id: '3', date: '2025-01-25', type: 'GAD-7 复评', status: 'pending', notes: '' },
])

const startAnnotation = (record: any) => {
  editingAnnotation.value = record.id
  annotationText.value = record.annotation || ''
}

const saveAnnotation = (record: any) => {
  record.annotation = annotationText.value
  editingAnnotation.value = null
  message.success('批注已保存')
}

const scheduleFollowUp = () => {
  followUps.value.push({
    id: `fu_${Date.now()}`,
    date: '待定',
    type: '新随访',
    status: 'pending',
    notes: '',
  })
  message.info('随访已添加，请编辑详情')
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; }

.student-overview { display: flex; align-items: center; gap: 16px; }
.student-info h3 { margin: 0 0 4px; }
.student-tags { display: flex; gap: 4px; }
.student-stats { margin-left: auto; display: flex; gap: 16px; }
.stat-item { text-align: center; }
.stat-val { display: block; font-size: 18px; font-weight: 600; color: #333; }
.stat-label { font-size: 12px; color: #999; }

.record-card { background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.record-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.record-name { font-size: 14px; font-weight: 600; flex: 1; }
.record-date { font-size: 12px; color: #999; }
.record-score-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.bar-bg { flex: 1; height: 8px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-text { font-size: 13px; font-weight: 600; min-width: 60px; text-align: right; }

.answer-item { display: flex; flex-direction: column; gap: 2px; padding: 4px 0; border-bottom: 1px solid #f5f5f5; }
.answer-q { font-size: 12px; color: #666; }
.answer-a { font-size: 12px; color: #1890ff; }

.annotation-section { margin-top: 8px; }
.annotation-text { font-size: 12px; color: #666; font-style: italic; margin: 0 0 4px; padding: 4px 8px; background: #fafafa; border-radius: 4px; }
.annotation-actions { display: flex; gap: 4px; }

.compare-item { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #f5f5f5; }
.compare-name { font-size: 13px; }
.compare-score { font-size: 14px; font-weight: 600; }
.compare-summary { text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }

.followup-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.fu-date { color: #333; min-width: 90px; }
.fu-type { color: #1890ff; min-width: 100px; }
.fu-notes { color: #999; flex: 1; }
</style>
