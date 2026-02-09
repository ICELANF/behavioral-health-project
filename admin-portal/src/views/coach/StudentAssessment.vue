<template>
  <div class="student-assessment">
    <a-page-header title="学员测评交互" @back="$router.back()" style="padding: 0 0 16px">
      <template #tags><a-tag color="blue">学员ID: {{ studentId }}</a-tag></template>
    </a-page-header>

    <!-- Loading -->
    <div v-if="loading" style="text-align: center; padding: 60px 0">
      <a-spin size="large" tip="加载测评数据..." />
    </div>

    <template v-if="!loading">
      <!-- Student Overview -->
      <a-card style="margin-bottom: 16px">
        <div class="student-overview">
          <a-avatar :size="48" style="background: #1890ff">{{ student.name ? student.name[0] : '?' }}</a-avatar>
          <div class="student-info">
            <h3>{{ student.name }}</h3>
            <div class="student-tags">
              <a-tag :color="stageColor(student.stage)">{{ student.stage_label }}</a-tag>
              <a-tag :color="riskColor(student.risk_level)">{{ student.risk_label }}</a-tag>
              <a-tag v-if="student.bpt6_type" color="purple">{{ bpt6Label(student.bpt6_type) }}</a-tag>
            </div>
          </div>
          <div class="student-stats">
            <div class="stat-item">
              <span class="stat-val">{{ student.assessment_count ?? 0 }}</span>
              <span class="stat-label">已完成测评</span>
            </div>
            <div class="stat-item">
              <span class="stat-val">{{ student.last_active ?? '--' }}</span>
              <span class="stat-label">最近活跃</span>
            </div>
            <div class="stat-item" v-if="student.spi_score != null">
              <span class="stat-val">{{ student.spi_score }}</span>
              <span class="stat-label">SPI得分</span>
            </div>
          </div>
        </div>
      </a-card>

      <!-- Tabs -->
      <a-tabs v-model:activeKey="activeTab">
        <!-- Assessment Records -->
        <a-tab-pane key="records" tab="测评记录">
          <a-empty v-if="assessmentRecords.length === 0" description="暂无测评记录" />
          <div v-for="record in assessmentRecords" :key="record.id" class="record-card">
            <div class="record-header">
              <span class="record-name">{{ record.primary_concern }}</span>
              <a-tag :color="riskTagColor(record.risk_level)">{{ record.risk_label }}</a-tag>
              <span class="record-date">{{ formatDate(record.created_at) }}</span>
            </div>
            <div class="record-score-bar">
              <div class="bar-bg">
                <div class="bar-fill" :style="{ width: (record.risk_score ?? 0) + '%', background: riskBarColor(record.risk_score) }"></div>
              </div>
              <span class="bar-text">风险 {{ record.risk_score ?? 0 }}/100</span>
            </div>

            <!-- Details collapse -->
            <a-collapse v-if="record.reasoning || (record.recommended_actions && record.recommended_actions.length)">
              <a-collapse-panel header="查看评估详情">
                <div v-if="record.reasoning" class="detail-section">
                  <strong>评估分析:</strong>
                  <p class="reasoning-text">{{ record.reasoning }}</p>
                </div>
                <div v-if="record.recommended_actions && record.recommended_actions.length" class="detail-section">
                  <strong>建议措施:</strong>
                  <ul class="action-list">
                    <li v-for="(action, i) in record.recommended_actions" :key="i">{{ action }}</li>
                  </ul>
                </div>
                <div v-if="record.severity_distribution && Object.keys(record.severity_distribution).length" class="detail-section">
                  <strong>严重性分布:</strong>
                  <div class="severity-tags">
                    <a-tag v-for="(count, level) in record.severity_distribution" :key="level"
                      :color="severityColor(level as string)">
                      {{ severityLabel(level as string) }}: {{ count }}
                    </a-tag>
                  </div>
                </div>
                <div v-if="record.primary_agent" class="detail-section">
                  <strong>主处理Agent:</strong> {{ record.primary_agent }}
                  <span v-if="record.secondary_agents?.length"> | 辅助: {{ record.secondary_agents.join(', ') }}</span>
                </div>
              </a-collapse-panel>
            </a-collapse>

            <!-- Coach annotation -->
            <div class="annotation-section">
              <a-textarea v-if="editingAnnotation === record.id" v-model:value="annotationText" :rows="2" placeholder="输入评估批注..." />
              <div class="annotation-actions">
                <a-button v-if="editingAnnotation !== record.id" size="small" type="link" @click="startAnnotation(record)">
                  添加批注
                </a-button>
                <template v-if="editingAnnotation === record.id">
                  <a-button size="small" type="primary" @click="saveAnnotation(record)">发送批注</a-button>
                  <a-button size="small" @click="editingAnnotation = null">取消</a-button>
                </template>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- Before/After Comparison -->
        <a-tab-pane key="compare" tab="前后对比">
          <a-card v-if="comparison">
            <a-row :gutter="16">
              <a-col :span="12">
                <h4>首次评估 <span class="compare-date">{{ formatDate(comparison.first?.date) }}</span></h4>
                <div class="compare-item">
                  <span class="compare-name">风险等级</span>
                  <a-tag :color="riskTagColor(comparison.first?.risk_level)">{{ comparison.first?.risk_label }}</a-tag>
                </div>
                <div class="compare-item">
                  <span class="compare-name">风险得分</span>
                  <span class="compare-score" style="color: #cf1322">{{ comparison.first?.risk_score ?? '--' }}/100</span>
                </div>
                <div class="compare-item">
                  <span class="compare-name">主要关切</span>
                  <span class="compare-score">{{ comparison.first?.primary_concern ?? '--' }}</span>
                </div>
              </a-col>
              <a-col :span="12">
                <h4>最新评估 <span class="compare-date">{{ formatDate(comparison.latest?.date) }}</span></h4>
                <div class="compare-item">
                  <span class="compare-name">风险等级</span>
                  <a-tag :color="riskTagColor(comparison.latest?.risk_level)">{{ comparison.latest?.risk_label }}</a-tag>
                </div>
                <div class="compare-item">
                  <span class="compare-name">风险得分</span>
                  <span class="compare-score" style="color: #389e0d">{{ comparison.latest?.risk_score ?? '--' }}/100</span>
                </div>
                <div class="compare-item">
                  <span class="compare-name">主要关切</span>
                  <span class="compare-score">{{ comparison.latest?.primary_concern ?? '--' }}</span>
                </div>
              </a-col>
            </a-row>

            <!-- Profile comparison -->
            <div v-if="comparison.profile" class="profile-comparison">
              <a-divider>行为画像</a-divider>
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-statistic title="当前阶段" :value="comparison.profile.stage_label" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="SPI得分" :value="comparison.profile.spi_score ?? '--'" />
                </a-col>
                <a-col :span="8">
                  <a-statistic title="改变潜力" :value="comparison.profile.capacity_total ?? '--'" />
                </a-col>
              </a-row>
            </div>

            <div class="compare-summary">
              <a-statistic title="风险改善率" :value="comparison.improvement_rate" suffix="%"
                :value-style="{ color: comparison.improvement_rate > 0 ? '#3f8600' : '#cf1322' }" />
            </div>
          </a-card>

          <!-- Stage history -->
          <a-card v-if="stageHistory.length" title="阶段变迁记录" style="margin-top: 16px">
            <a-timeline>
              <a-timeline-item v-for="(h, i) in stageHistory" :key="i"
                :color="h.is_transition ? 'green' : 'gray'">
                <span class="stage-time">{{ formatDate(h.date) }}</span>
                <a-tag v-if="h.is_transition" color="green">跃迁</a-tag>
                <span>{{ stageLabel(h.from_stage) }} → {{ stageLabel(h.to_stage) }}</span>
                <span v-if="h.belief_score != null" class="belief-score">信念: {{ (h.belief_score * 100).toFixed(0) }}%</span>
              </a-timeline-item>
            </a-timeline>
          </a-card>

          <a-empty v-if="!comparison && stageHistory.length === 0" description="需要至少两次测评才能进行对比" />
        </a-tab-pane>

        <!-- Follow-up -->
        <a-tab-pane key="followup" tab="随访记录">
          <a-card>
            <a-empty v-if="followUps.length === 0" description="暂无随访记录" />
            <div v-for="fu in followUps" :key="fu.id" class="followup-item">
              <a-tag :color="fu.status === 'completed' ? 'green' : fu.status === 'scheduled' ? 'blue' : 'orange'">
                {{ fu.status === 'completed' ? '已发送' : fu.status === 'scheduled' ? '已安排' : '待安排' }}
              </a-tag>
              <span class="fu-date">{{ formatDate(fu.date) }}</span>
              <span class="fu-type">{{ fu.type }}</span>
              <span class="fu-notes">{{ fu.content }}</span>
            </div>
            <a-divider />
            <div class="send-followup">
              <h4>发送随访消息</h4>
              <a-textarea v-model:value="newFollowupContent" :rows="2" placeholder="输入随访内容..." />
              <div style="margin-top: 8px; display: flex; gap: 8px;">
                <a-select v-model:value="newFollowupType" style="width: 120px">
                  <a-select-option value="text">普通消息</a-select-option>
                  <a-select-option value="encouragement">鼓励</a-select-option>
                  <a-select-option value="reminder">提醒</a-select-option>
                  <a-select-option value="advice">建议</a-select-option>
                </a-select>
                <a-button type="primary" :loading="sendingFollowup" @click="sendFollowup">发送</a-button>
              </div>
              <div class="quick-templates" style="margin-top: 8px;">
                <a-button v-for="tpl in quickTemplates" :key="tpl" size="small" @click="newFollowupContent = tpl">{{ tpl }}</a-button>
              </div>
            </div>
          </a-card>
        </a-tab-pane>
      </a-tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'

const route = useRoute()
const studentId = route.params.id as string

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const token = localStorage.getItem('token') || ''
const authHeaders: Record<string, string> = {
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
}

const loading = ref(true)
const activeTab = ref('records')
const editingAnnotation = ref<number | null>(null)
const annotationText = ref('')

const student = ref<any>({
  name: '', stage: '', stage_label: '加载中', risk_level: null,
  risk_label: '--', assessment_count: 0, last_active: '--',
  spi_score: null, bpt6_type: null,
})
const assessmentRecords = ref<any[]>([])
const comparison = ref<any>(null)
const stageHistory = ref<any[]>([])
const followUps = ref<any[]>([])

// Follow-up form
const newFollowupContent = ref('')
const newFollowupType = ref('text')
const sendingFollowup = ref(false)
const quickTemplates = [
  '加油，继续保持！',
  '今天的任务完成了吗？',
  '最近感觉怎么样？有什么困难吗？',
  '记得按时完成今日微行动哦',
]

const STAGE_LABEL: Record<string, string> = {
  S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
  S4: '行动期', S5: '坚持期', S6: '融入期',
}

const stageColor = (s: string) => {
  const map: Record<string, string> = {
    S0: 'red', S1: 'volcano', S2: 'orange', S3: 'gold',
    S4: 'green', S5: 'blue', S6: 'purple', unknown: 'default',
  }
  return map[s] || 'default'
}

const riskColor = (r: string | null) => {
  const map: Record<string, string> = {
    R0: 'green', R1: 'lime', R2: 'orange', R3: 'red', R4: 'magenta',
  }
  return r ? (map[r] || 'default') : 'default'
}

const riskTagColor = (r: string | null) => {
  const map: Record<string, string> = {
    R0: '#389e0d', R1: '#7cb305', R2: '#d4b106', R3: '#d46b08', R4: '#cf1322',
  }
  return r ? (map[r] || '#999') : '#999'
}

const riskBarColor = (score: number | null) => {
  if (score == null) return '#d9d9d9'
  if (score <= 20) return '#389e0d'
  if (score <= 40) return '#7cb305'
  if (score <= 60) return '#d4b106'
  if (score <= 80) return '#d46b08'
  return '#cf1322'
}

const severityColor = (level: string) => {
  const map: Record<string, string> = { critical: 'red', high: 'orange', moderate: 'gold', low: 'green' }
  return map[level] || 'default'
}

const severityLabel = (level: string) => {
  const map: Record<string, string> = { critical: '危急', high: '高', moderate: '中', low: '低' }
  return map[level] || level
}

const bpt6Label = (t: string) => {
  const map: Record<string, string> = {
    action: '行动型', knowledge: '认知型', emotion: '情感型',
    relation: '关系型', environment: '环境型', mixed: '混合型',
  }
  return map[t] || t
}

const stageLabel = (s: string) => STAGE_LABEL[s] || s

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '--'
  try {
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return dateStr
  }
}

// Load data
const loadData = async () => {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/v1/coach/students/${studentId}/assessment-detail`, {
      headers: authHeaders,
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()

    student.value = data.student || student.value
    assessmentRecords.value = data.assessments || []
    comparison.value = data.comparison || null
    stageHistory.value = data.stage_history || []
    followUps.value = data.followups || []
  } catch (e: any) {
    console.error('加载测评数据失败:', e)
    message.error('加载测评数据失败')
  } finally {
    loading.value = false
  }
}

// Annotation → send as coach message with type "annotation"
const startAnnotation = (record: any) => {
  editingAnnotation.value = record.id
  annotationText.value = ''
}

const saveAnnotation = async (record: any) => {
  if (!annotationText.value.trim()) return
  try {
    const resp = await fetch(`${API_BASE}/v1/coach/messages`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        student_id: Number(studentId),
        content: `[测评批注 ${record.assessment_id}] ${annotationText.value}`,
        message_type: 'advice',
      }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    editingAnnotation.value = null
    message.success('批注已发送')
    // Refresh followups
    await loadData()
  } catch (e) {
    message.error('保存批注失败')
  }
}

// Send follow-up message
const sendFollowup = async () => {
  if (!newFollowupContent.value.trim()) {
    message.warning('请输入消息内容')
    return
  }
  sendingFollowup.value = true
  try {
    const resp = await fetch(`${API_BASE}/v1/coach/messages`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        student_id: Number(studentId),
        content: newFollowupContent.value,
        message_type: newFollowupType.value,
      }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    newFollowupContent.value = ''
    message.success('消息已发送')
    await loadData()
  } catch (e) {
    message.error('发送失败')
  } finally {
    sendingFollowup.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; }

.student-overview { display: flex; align-items: center; gap: 16px; }
.student-info h3 { margin: 0 0 4px; }
.student-tags { display: flex; gap: 4px; flex-wrap: wrap; }
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
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.bar-text { font-size: 13px; font-weight: 600; min-width: 80px; text-align: right; }

.detail-section { margin-bottom: 12px; }
.detail-section strong { display: block; margin-bottom: 4px; color: #333; font-size: 13px; }
.reasoning-text { font-size: 13px; color: #666; line-height: 1.6; margin: 4px 0; white-space: pre-wrap; }
.action-list { padding-left: 20px; margin: 4px 0; }
.action-list li { font-size: 13px; color: #333; margin-bottom: 4px; }
.severity-tags { display: flex; gap: 4px; flex-wrap: wrap; }

.annotation-section { margin-top: 8px; }
.annotation-actions { display: flex; gap: 4px; margin-top: 4px; }

.compare-date { font-size: 12px; color: #999; font-weight: normal; }
.compare-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.compare-name { font-size: 13px; color: #666; }
.compare-score { font-size: 14px; font-weight: 600; }
.compare-summary { text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.profile-comparison { margin-top: 16px; }

.stage-time { font-size: 12px; color: #999; margin-right: 8px; }
.belief-score { font-size: 12px; color: #1890ff; margin-left: 8px; }

.followup-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.fu-date { color: #333; min-width: 90px; }
.fu-type { color: #1890ff; min-width: 60px; }
.fu-notes { color: #666; flex: 1; }

.send-followup { margin-top: 8px; }
.send-followup h4 { margin: 0 0 8px; }
.quick-templates { display: flex; flex-wrap: wrap; gap: 4px; }
</style>
