<template>
  <div class="my-tools">
    <div class="page-header">
      <h2>我的工具箱</h2>
    </div>

    <!-- Loading -->
    <div v-if="loading" style="text-align: center; padding: 60px 0">
      <a-spin size="large" tip="加载工具数据..." />
    </div>

    <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom: 16px" />

    <template v-if="!loading && !error">
      <!-- Tool Grid -->
      <div class="tools-grid">
        <div v-for="tool in tools" :key="tool.key" class="tool-card" :style="{ borderColor: tool.color }" @click="openDrawer(tool)">
          <div class="tool-icon" :style="{ background: tool.color + '18', color: tool.color }">
            {{ toolIcon(tool.key) }}
          </div>
          <div class="tool-info">
            <span class="tool-name">{{ tool.name }}</span>
            <span class="tool-desc">{{ tool.description }}</span>
          </div>
          <div class="tool-stats">
            <span class="stat-num">{{ tool.use_count }}</span>
            <span class="stat-label">本月</span>
          </div>
        </div>
      </div>

      <!-- Recent Usage -->
      <a-card title="最近活动" style="margin-top: 16px; margin-bottom: 16px">
        <a-empty v-if="recentActivity.length === 0" description="暂无活动记录" />
        <div v-for="item in recentActivity" :key="item.id" class="usage-item">
          <div class="usage-info">
            <span class="usage-name">{{ item.tool_name }}</span>
            <span class="usage-context">学员: {{ item.student }} &middot; {{ item.action }}</span>
          </div>
          <span class="usage-time">{{ item.time }}</span>
        </div>
      </a-card>

      <!-- Usage Statistics -->
      <a-card title="使用统计">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-statistic title="本月总使用" :value="totalMonthUsage" suffix="次" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="最常用工具" :value="mostUsedTool" />
          </a-col>
          <a-col :span="8">
            <a-statistic title="活跃天数" :value="activeDays" suffix="天" value-style="color: #3f8600" />
          </a-col>
        </a-row>
        <div class="usage-chart" style="margin-top: 16px">
          <div v-for="tool in tools" :key="tool.key" class="chart-item">
            <span class="chart-label">{{ tool.name }}</span>
            <div class="chart-bar-bg">
              <div class="chart-bar" :style="{ width: (tool.use_count / maxUseCount * 100) + '%', background: tool.color }"></div>
            </div>
            <span class="chart-count">{{ tool.use_count }}</span>
          </div>
        </div>
      </a-card>
    </template>

    <!-- ========== AI 干预助手抽屉 ========== -->
    <a-drawer
      :open="drawerVisible"
      :title="`AI干预助手 — ${activeTool?.name || ''}`"
      placement="right"
      :width="520"
      @close="closeDrawer"
      :destroyOnClose="true"
    >
      <!-- 选择学员 -->
      <div class="drawer-section">
        <div class="drawer-label">选择学员</div>
        <a-select
          v-model:value="selectedStudentId"
          placeholder="请选择学员"
          style="width: 100%"
          show-search
          :filter-option="filterStudentOption"
          @change="onStudentChange"
        >
          <a-select-option v-for="s in studentList" :key="s.student_id" :value="s.student_id">
            {{ s.student_name }}
          </a-select-option>
        </a-select>
      </div>

      <template v-if="selectedStudentId">
        <!-- 学员画像摘要 -->
        <div v-if="aiMeta.student_summary" class="drawer-section">
          <div class="student-summary">
            {{ aiMeta.student_summary }}
            <a-tag v-if="aiMeta.source" :color="aiMeta.source === 'llm' ? 'blue' : 'default'" style="margin-left: 8px">
              {{ aiMeta.source === 'llm' ? 'AI增强' : '规则引擎' }}
            </a-tag>
          </div>
        </div>

        <!-- AI 生成中 -->
        <div v-if="suggestionsLoading" class="drawer-section" style="text-align: center; padding: 24px 0">
          <a-spin tip="AI正在生成推送内容..." />
        </div>

        <template v-if="!suggestionsLoading">
          <!-- 工具特定字段 (测评/微行动在内容编辑前) -->
          <div v-if="activeToolKey === 'reminder'" class="drawer-section">
            <div class="drawer-label">提醒设置</div>
            <a-input v-model:value="reminderTitle" placeholder="提醒标题" style="margin-bottom: 8px" />
            <a-time-picker v-model:value="reminderTime" format="HH:mm" placeholder="每日提醒时间" style="width: 100%" value-format="HH:mm" />
          </div>

          <div v-if="activeToolKey === 'assessment'" class="drawer-section">
            <div class="drawer-label">量表选择</div>
            <a-select v-model:value="selectedScale" placeholder="选择评估量表" style="width: 100%">
              <a-select-option value="hf20">HF-20 快速筛查</a-select-option>
              <a-select-option value="hf50">HF-50 全面评估</a-select-option>
              <a-select-option value="ttm7">TTM-7 变化阶段</a-select-option>
              <a-select-option value="big5">Big-5 大五人格</a-select-option>
              <a-select-option value="bpt6">BPT-6 行为人格</a-select-option>
              <a-select-option value="capacity">行为能力评估</a-select-option>
              <a-select-option value="spi">SPI 自我践行指数</a-select-option>
            </a-select>
          </div>

          <div v-if="activeToolKey === 'micro_action'" class="drawer-section">
            <div class="drawer-label">微行动设置</div>
            <a-input v-model:value="microTitle" placeholder="任务标题" style="margin-bottom: 8px" />
            <a-select v-model:value="microDomain" placeholder="领域" style="width: 100%; margin-bottom: 8px">
              <a-select-option value="nutrition">营养管理</a-select-option>
              <a-select-option value="exercise">运动管理</a-select-option>
              <a-select-option value="sleep">睡眠管理</a-select-option>
              <a-select-option value="emotion">情绪管理</a-select-option>
              <a-select-option value="stress">压力管理</a-select-option>
              <a-select-option value="cognitive">认知管理</a-select-option>
              <a-select-option value="social">社交管理</a-select-option>
            </a-select>
            <a-row :gutter="8">
              <a-col :span="12">
                <a-select v-model:value="microFrequency" style="width: 100%">
                  <a-select-option value="每天">每天</a-select-option>
                  <a-select-option value="每周">每周</a-select-option>
                </a-select>
              </a-col>
              <a-col :span="12">
                <a-input-number v-model:value="microDays" :min="1" :max="90" placeholder="持续天数" style="width: 100%" addon-after="天" />
              </a-col>
            </a-row>
          </div>

          <!-- 推送内容编辑区（AI自动填入，促进师直接修订） -->
          <div class="drawer-section">
            <div class="drawer-label">推送内容 <span class="label-hint">（AI已生成，可直接修订）</span></div>
            <a-textarea
              v-model:value="editContent"
              :rows="5"
              placeholder="AI正在生成推送内容..."
              :maxlength="2000"
              show-count
            />
          </div>

          <!-- 备选方案（折叠，可切换） -->
          <div v-if="suggestions.length > 1" class="drawer-section">
            <a-collapse :bordered="false" style="background: transparent">
              <a-collapse-panel key="alt" header="换一种表达方式" :style="{ background: '#fafafa', borderRadius: '6px' }">
                <div class="alt-list">
                  <div
                    v-for="(sug, idx) in suggestions"
                    :key="idx"
                    class="alt-item"
                    :class="{ active: selectedSuggestionIdx === idx }"
                    @click="selectSuggestion(idx)"
                  >
                    <span class="alt-tag">方案{{ idx + 1 }}</span>
                    <span class="alt-text">{{ suggestionDisplayContent(sug) }}</span>
                    <span v-if="sug.reason" class="alt-reason">{{ sug.reason }}</span>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>

          <!-- 推送控制区 -->
          <div class="drawer-section push-actions">
            <a-space direction="vertical" :size="8" style="width: 100%">
              <a-button type="primary" block size="large" :loading="submitting" @click="handlePush('now')" :disabled="!canSubmit">
                立即推送
              </a-button>
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-button block @click="handlePush('queue')" :disabled="!canSubmit || submitting">
                    存入待推送队列
                  </a-button>
                </a-col>
                <a-col :span="12">
                  <a-button block @click="closeDrawer" :disabled="submitting">
                    放弃
                  </a-button>
                </a-col>
              </a-row>
            </a-space>
          </div>
        </template>
      </template>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'

import request from '@/api/request'

// ── 页面数据 ──────────────────────────────────────────
const loading = ref(true)
const error = ref('')
const tools = ref<any[]>([])
const recentActivity = ref<any[]>([])
const totalMonthUsage = ref(0)
const mostUsedTool = ref('--')
const activeDays = ref(0)

const maxUseCount = computed(() => Math.max(...tools.value.map(t => t.use_count), 1))

const toolIcon = (key: string) => {
  const icons: Record<string, string> = {
    message: '\u2709', encouragement: '\u2665', advice: '\u2605',
    reminder: '\u23F0', assessment: '\u2611', micro_action: '\u2699',
  }
  return icons[key] || '\u2022'
}

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await request.get('/v1/coach/my-tools-stats')
    tools.value = data.tools || []
    recentActivity.value = data.recent_activity || []
    totalMonthUsage.value = data.total_month_usage ?? 0
    mostUsedTool.value = data.most_used_tool || '--'
    const uniqueDays = new Set(
      recentActivity.value
        .filter((a: any) => a.time)
        .map((a: any) => a.time.includes('分钟') || a.time.includes('小时') ? 'today' : a.time)
    )
    activeDays.value = Math.max(uniqueDays.size, totalMonthUsage.value > 0 ? 1 : 0)
  } catch (e: any) {
    console.error('加载工具统计失败:', e)
    error.value = '加载工具统计失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// ── 抽屉状态 ──────────────────────────────────────────
const drawerVisible = ref(false)
const activeTool = ref<any>(null)
const activeToolKey = computed(() => activeTool.value?.key || '')

const studentList = ref<any[]>([])
const selectedStudentId = ref<number | undefined>(undefined)

const suggestions = ref<any[]>([])
const suggestionsLoading = ref(false)
const selectedSuggestionIdx = ref(-1)
const aiMeta = ref<any>({})

const editContent = ref('')

// 提醒
const reminderTitle = ref('')
const reminderTime = ref<any>(null)

// 测评
const selectedScale = ref<string | undefined>(undefined)

// 微行动
const microTitle = ref('')
const microDomain = ref('exercise')
const microFrequency = ref('每天')
const microDays = ref(7)

const submitting = ref(false)

const TOOL_MESSAGE_TYPE: Record<string, string> = {
  message: 'text',
  encouragement: 'encouragement',
  advice: 'advice',
}

// ── 能否提交 ─────────────────────────────────────────
const canSubmit = computed(() => {
  if (!selectedStudentId.value) return false
  const key = activeToolKey.value
  if (key === 'assessment') return !!selectedScale.value
  if (key === 'micro_action') return !!microTitle.value.trim()
  return !!editContent.value.trim()
})

// ── 打开 / 关闭 ─────────────────────────────────────
const openDrawer = async (tool: any) => {
  activeTool.value = tool
  resetDrawerFields()
  drawerVisible.value = true
  await loadStudents()
}

const closeDrawer = () => {
  drawerVisible.value = false
  activeTool.value = null
  resetDrawerFields()
}

const resetDrawerFields = () => {
  selectedStudentId.value = undefined
  suggestions.value = []
  suggestionsLoading.value = false
  selectedSuggestionIdx.value = -1
  aiMeta.value = {}
  editContent.value = ''
  reminderTitle.value = ''
  reminderTime.value = null
  selectedScale.value = undefined
  microTitle.value = ''
  microDomain.value = 'exercise'
  microFrequency.value = '每天'
  microDays.value = 7
}

// ── 加载学员 ─────────────────────────────────────────
const loadStudents = async () => {
  try {
    const { data } = await request.get('/v1/coach/students-with-messages')
    studentList.value = data.students || []
  } catch (e) {
    console.error('加载学员列表失败:', e)
    studentList.value = []
  }
}

const filterStudentOption = (input: string, option: any) => {
  const student = studentList.value.find(s => s.student_id === option.value)
  return student?.student_name?.toLowerCase().includes(input.toLowerCase()) ?? false
}

// ── 选学员 → AI自动生成内容填入编辑区 ─────────────────
const onStudentChange = () => {
  suggestions.value = []
  selectedSuggestionIdx.value = -1
  editContent.value = ''
  reminderTitle.value = ''
  reminderTime.value = null
  selectedScale.value = undefined
  microTitle.value = ''
  if (selectedStudentId.value) {
    loadAndAutoFill()
  }
}

const loadAndAutoFill = async () => {
  if (!selectedStudentId.value || !activeToolKey.value) return

  suggestionsLoading.value = true
  suggestions.value = []
  aiMeta.value = {}

  try {
    const key = activeToolKey.value
    let url = ''
    if (key === 'message' || key === 'encouragement' || key === 'advice') {
      url = `/v1/coach/messages/ai-suggestions/${selectedStudentId.value}?message_type=${TOOL_MESSAGE_TYPE[key] || 'text'}`
    } else if (key === 'reminder') {
      url = `/v1/coach/reminders/ai-suggestions/${selectedStudentId.value}?reminder_type=behavior`
    } else if (key === 'assessment') {
      url = `/v1/coach/assessment/ai-suggestions/${selectedStudentId.value}`
    } else if (key === 'micro_action') {
      url = `/v1/coach/micro-actions/ai-suggestions/${selectedStudentId.value}`
    }
    if (!url) return

    const { data } = await request.get(url)
    suggestions.value = data.suggestions || []
    aiMeta.value = { source: data.meta?.source || 'rules', student_summary: data.student_summary || '' }

    // 自动填入第一条建议
    if (suggestions.value.length > 0) {
      selectSuggestion(0)
    }
  } catch (e) {
    console.error('AI建议加载失败:', e)
  } finally {
    suggestionsLoading.value = false
  }
}

// ── 建议展示 ─────────────────────────────────────────
const suggestionDisplayContent = (sug: any) => {
  const key = activeToolKey.value
  if (key === 'assessment') return sug.title || sug.scale || ''
  if (key === 'micro_action') return `${sug.title}${sug.frequency ? ` (${sug.frequency})` : ''}`
  if (key === 'reminder') return `${sug.title} — ${sug.content || ''}`
  return sug.content || ''
}

// ── 选择备选方案 → 替换编辑区 ────────────────────────
const selectSuggestion = (idx: number) => {
  selectedSuggestionIdx.value = idx
  const sug = suggestions.value[idx]
  if (!sug) return
  const key = activeToolKey.value

  if (key === 'message' || key === 'encouragement' || key === 'advice') {
    editContent.value = sug.content || ''
  } else if (key === 'reminder') {
    reminderTitle.value = sug.title || ''
    editContent.value = sug.content || ''
    if (sug.cron_time) reminderTime.value = dayjs(sug.cron_time, 'HH:mm')
  } else if (key === 'assessment') {
    selectedScale.value = sug.scale || undefined
    editContent.value = sug.reason || ''
  } else if (key === 'micro_action') {
    microTitle.value = sug.title || ''
    editContent.value = sug.description || ''
    microDomain.value = sug.domain || 'exercise'
    microFrequency.value = sug.frequency || '每天'
    microDays.value = sug.duration_days || 7
  }
}

// ── 推送 / 入队 ─────────────────────────────────────
const handlePush = async (mode: 'now' | 'queue') => {
  if (!canSubmit.value || submitting.value) return
  const autoApprove = mode === 'now'

  submitting.value = true
  try {
    const key = activeToolKey.value

    if (key === 'message' || key === 'encouragement' || key === 'advice') {
      await request.post('/v1/coach/messages', {
        student_id: selectedStudentId.value,
        content: editContent.value,
        message_type: TOOL_MESSAGE_TYPE[key] || 'text',
        auto_approve: autoApprove,
      })
    } else if (key === 'reminder') {
      const timeStr = reminderTime.value
        ? (typeof reminderTime.value === 'string' ? reminderTime.value : dayjs(reminderTime.value).format('HH:mm'))
        : '09:00'
      await request.post('/v1/coach/reminders', {
        student_id: selectedStudentId.value,
        title: reminderTitle.value || '教练提醒',
        content: editContent.value,
        type: 'behavior',
        cron_expr: `0 ${timeStr.split(':')[1] || '0'} ${timeStr.split(':')[0] || '9'} * * *`,
        auto_approve: autoApprove,
      })
    } else if (key === 'assessment') {
      // 测评指派本身就是直接操作，不走队列
      const scaleVal = selectedScale.value
      const scales = scaleVal && ['ttm7', 'big5', 'bpt6', 'capacity', 'spi'].includes(scaleVal) ? [scaleVal] : []
      const preset = scaleVal && ['hf20', 'hf50'].includes(scaleVal) ? scaleVal : null
      await request.post('/v1/assessment-assignments/assign', {
        student_id: selectedStudentId.value,
        scales: scales,
        question_preset: preset,
        note: editContent.value || undefined,
      })
    } else if (key === 'micro_action') {
      await request.post('/v1/micro-actions/coach-assign', {
        student_id: selectedStudentId.value,
        title: microTitle.value,
        description: editContent.value,
        domain: microDomain.value,
        frequency: microFrequency.value,
        duration_days: microDays.value,
        auto_approve: autoApprove,
      })
    }

    message.success(autoApprove ? '已推送给学员' : '已存入待推送队列')
    closeDrawer()
    loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '操作失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.tools-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tool-card { display: flex; align-items: center; gap: 12px; padding: 16px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; cursor: pointer; border-left: 3px solid; transition: box-shadow 0.2s; }
.tool-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.tool-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.tool-info { flex: 1; }
.tool-name { display: block; font-size: 14px; font-weight: 600; color: #333; }
.tool-desc { font-size: 12px; color: #999; }
.tool-stats { text-align: center; }
.stat-num { display: block; font-size: 18px; font-weight: 700; color: #333; }
.stat-label { font-size: 11px; color: #999; }

.usage-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.usage-info { flex: 1; }
.usage-name { display: block; font-size: 13px; font-weight: 500; }
.usage-context { font-size: 12px; color: #999; }
.usage-time { font-size: 12px; color: #bbb; }

.chart-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.chart-label { min-width: 100px; font-size: 13px; color: #333; }
.chart-bar-bg { flex: 1; height: 16px; background: #f5f5f5; border-radius: 4px; overflow: hidden; }
.chart-bar { height: 100%; border-radius: 4px; transition: width 0.3s; }
.chart-count { min-width: 30px; text-align: right; font-size: 13px; color: #999; }

/* ── 抽屉 ── */
.drawer-section { margin-bottom: 16px; }
.drawer-label { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 8px; display: flex; align-items: center; }
.label-hint { font-weight: 400; color: #999; font-size: 12px; margin-left: 6px; }
.student-summary { font-size: 12px; color: #555; padding: 8px 12px; background: #f6f8fa; border-radius: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }

/* ── 备选方案列表 ── */
.alt-list { display: flex; flex-direction: column; gap: 6px; }
.alt-item {
  display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px;
  border: 1px solid #e8e8e8; border-radius: 4px; cursor: pointer; transition: all 0.15s;
  flex-wrap: wrap;
}
.alt-item:hover { border-color: #1890ff; background: #f0f7ff; }
.alt-item.active { border-color: #1890ff; background: #e6f4ff; }
.alt-tag { font-size: 11px; color: #1890ff; background: #e6f4ff; border-radius: 3px; padding: 1px 6px; flex-shrink: 0; }
.alt-text { font-size: 13px; color: #333; flex: 1; min-width: 0; word-break: break-all; }
.alt-reason { font-size: 11px; color: #999; width: 100%; padding-left: 50px; }

/* ── 推送按钮区 ── */
.push-actions { padding-top: 8px; border-top: 1px solid #f0f0f0; }

@media (max-width: 640px) {
  .my-tools { padding: 8px !important; }
  .page-header h2 { font-size: 16px; }
  .tools-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .tool-card { padding: 12px; gap: 8px; }
  .tool-icon { width: 36px; height: 36px; font-size: 18px; }
  .tool-name { font-size: 13px; }
  .stat-num { font-size: 16px; }
  .ant-btn { min-height: 44px; }
  .chart-label { min-width: 70px; font-size: 12px; }
  .usage-item { flex-wrap: wrap; gap: 6px; }
}
</style>
