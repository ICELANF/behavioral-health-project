<template>
  <div class="content-sharing">
    <div class="page-header">
      <h2>内容分享</h2>
    </div>

    <a-steps :current="currentStep" :direction="isMobile ? 'vertical' : 'horizontal'" style="margin-bottom: 24px">
      <a-step title="选择内容" />
      <a-step title="选择学员" />
      <a-step title="个性化消息" />
      <a-step title="确认发送" />
    </a-steps>

    <!-- Step 1: Select Content -->
    <div v-if="currentStep === 0">
      <a-card title="选择要分享的内容">
        <a-spin v-if="loadingContent" tip="加载内容..." />
        <a-tabs v-else v-model:activeKey="contentTab">
          <a-tab-pane key="course" tab="课程">
            <a-empty v-if="courses.length === 0" description="暂无课程内容" />
            <div v-for="item in courses" :key="item.id" class="content-item" :class="{ selected: selectedContent?.id === item.id }" @click="selectContent(item)">
              <span class="content-icon">📚</span>
              <div class="content-info">
                <span class="content-name">{{ item.title }}</span>
                <span class="content-meta">{{ item.chapters }} 章节 · {{ item.duration }}</span>
              </div>
              <span v-if="selectedContent?.id === item.id" class="check-mark">✓</span>
            </div>
          </a-tab-pane>
          <a-tab-pane key="article" tab="文章">
            <a-empty v-if="articles.length === 0" description="暂无文章内容" />
            <div v-for="item in articles" :key="item.id" class="content-item" :class="{ selected: selectedContent?.id === item.id }" @click="selectContent(item)">
              <span class="content-icon">📄</span>
              <div class="content-info">
                <span class="content-name">{{ item.title }}</span>
                <span class="content-meta">{{ item.readTime }} 阅读</span>
              </div>
              <span v-if="selectedContent?.id === item.id" class="check-mark">✓</span>
            </div>
          </a-tab-pane>
          <a-tab-pane key="intervention" tab="干预包">
            <a-empty v-if="interventions.length === 0" description="暂无干预包" />
            <div v-for="item in interventions" :key="item.id" class="content-item" :class="{ selected: selectedContent?.id === item.id }" @click="selectContent(item)">
              <span class="content-icon">📦</span>
              <div class="content-info">
                <span class="content-name">{{ item.title }}</span>
                <span class="content-meta">{{ item.taskCount }} 个任务 · {{ item.domain }}</span>
              </div>
              <span v-if="selectedContent?.id === item.id" class="check-mark">✓</span>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>

    <!-- Step 2: Select Students -->
    <div v-if="currentStep === 1">
      <a-card title="选择接收学员">
        <a-empty v-if="students.length === 0" description="暂无学员数据" />
        <template v-else>
        <a-input-search v-model:value="studentSearch" placeholder="搜索学员" style="margin-bottom: 12px" />
        <a-checkbox-group v-model:value="selectedStudentIds" style="width: 100%">
          <div v-for="s in filteredStudents" :key="s.id" class="student-check-item">
            <a-checkbox :value="s.id">
              <div class="student-check-info">
                <a-avatar :size="28">{{ s.name[0] }}</a-avatar>
                <span>{{ s.name }}</span>
                <a-tag size="small">{{ s.stage }}</a-tag>
              </div>
            </a-checkbox>
          </div>
        </a-checkbox-group>
        <div style="margin-top: 8px">
          <a-button size="small" @click="selectAllStudents">全选</a-button>
          <a-button size="small" style="margin-left: 8px" @click="selectedStudentIds = []">清空</a-button>
        </div>
        </template>
      </a-card>
    </div>

    <!-- Step 3: Personalize Message -->
    <div v-if="currentStep === 2">
      <a-card title="个性化消息">
        <a-form layout="vertical">
          <a-form-item label="附言">
            <a-textarea v-model:value="personalMessage" :rows="4" placeholder="给学员的个性化消息..." />
          </a-form-item>
          <a-form-item label="发送方式">
            <a-radio-group v-model:value="sendMode">
              <a-radio value="now">立即发送</a-radio>
              <a-radio value="scheduled">定时发送</a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="sendMode === 'scheduled'" label="发送时间">
            <a-date-picker v-model:value="scheduledTime" show-time placeholder="选择发送时间" style="width: 100%" />
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- Step 4: Confirm -->
    <div v-if="currentStep === 3">
      <a-card title="确认发送">
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="内容">{{ selectedContent?.title }}</a-descriptions-item>
          <a-descriptions-item label="接收学员">{{ selectedStudentIds.length }} 人</a-descriptions-item>
          <a-descriptions-item label="附言">{{ personalMessage || '无' }}</a-descriptions-item>
          <a-descriptions-item label="发送方式">{{ sendMode === 'now' ? '立即发送' : '定时发送' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- Tracking status after send -->
      <a-card v-if="sent" title="阅读追踪" style="margin-top: 16px">
        <div v-for="s in trackingData" :key="s.id" class="tracking-item">
          <a-avatar :size="24">{{ s.name[0] }}</a-avatar>
          <span class="tracking-name">{{ s.name }}</span>
          <a-tag :color="s.sent ? 'green' : 'red'" size="small">{{ s.sent ? '已发送' : '发送失败' }}</a-tag>
        </div>
      </a-card>
    </div>

    <!-- Navigation -->
    <div class="step-actions">
      <a-button v-if="currentStep > 0" @click="currentStep--">上一步</a-button>
      <a-button v-if="currentStep < 3" type="primary" :disabled="!canNext" @click="currentStep++">下一步</a-button>
      <a-button v-if="currentStep === 3 && !sent" type="primary" :loading="sending" @click="sendContent">
        {{ sendMode === 'now' ? '立即发送' : '确认定时' }}
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'
import { useResponsive } from '@/composables/useResponsive'

const { isMobile } = useResponsive()

const currentStep = ref(0)
const contentTab = ref('course')
const selectedContent = ref<any>(null)
const selectedStudentIds = ref<string[]>([])
const studentSearch = ref('')
const personalMessage = ref('')
const sendMode = ref('now')
const scheduledTime = ref(null)
const sent = ref(false)
const sending = ref(false)
const loadingContent = ref(false)

const courses = ref<any[]>([])
const articles = ref<any[]>([])
const interventions = ref<any[]>([])
const students = ref<any[]>([])

const STAGE_LABELS: Record<string, string> = {
  S0: '觉醒期', S1: '松动期', S2: '探索期', S3: '准备期',
  S4: '行动期', S5: '坚持期', S6: '融入期',
}

async function loadContent() {
  loadingContent.value = true
  try {
    const [courseRes, articleRes] = await Promise.all([
      request.get('/v1/content', { params: { type: 'course', page_size: 50 } }),
      request.get('/v1/content', { params: { type: 'article', page_size: 50 } }),
    ])
    courses.value = (courseRes.data.items || []).map((item: any) => ({
      id: item.id,
      title: item.title,
      type: 'course',
      chapters: item.chapter_count || '--',
      duration: item.duration || '--',
    }))
    articles.value = (articleRes.data.items || []).map((item: any) => ({
      id: item.id,
      title: item.title,
      type: 'article',
      readTime: item.read_time || '5分钟',
    }))
    // Load intervention packs from program templates
    try {
      const intRes = await request.get('/v1/programs/templates')
      interventions.value = (intRes.data?.items || intRes.data || []).map((t: any) => ({
        id: t.id,
        title: t.name || t.title,
        type: 'intervention',
        taskCount: t.task_count || t.steps?.length || '--',
        domain: t.domain || t.category || '综合',
      }))
    } catch {
      interventions.value = []
    }
  } catch (e) {
    console.error('加载内容列表失败:', e)
    message.error('加载内容列表失败')
  } finally {
    loadingContent.value = false
  }
}

async function loadStudents() {
  try {
    const res = await request.get('/v1/coach/dashboard')
    students.value = (res.data.students || []).map((s: any) => ({
      id: String(s.id),
      name: s.name,
      stage: STAGE_LABELS[s.stage] || s.stage || '未评估',
    }))
  } catch (e) {
    console.error('加载学员列表失败:', e)
  }
}

const filteredStudents = computed(() => {
  if (!studentSearch.value) return students.value
  return students.value.filter(s => s.name.includes(studentSearch.value))
})

const canNext = computed(() => {
  if (currentStep.value === 0) return !!selectedContent.value
  if (currentStep.value === 1) return selectedStudentIds.value.length > 0
  return true
})

const trackingData = ref<any[]>([])

const selectContent = (item: any) => { selectedContent.value = item }
const selectAllStudents = () => { selectedStudentIds.value = students.value.map(s => s.id) }

const sendContent = async () => {
  sending.value = true
  try {
    const content = selectedContent.value
    const msgContent = personalMessage.value
      ? `[内容分享] ${content.title}\n${personalMessage.value}`
      : `[内容分享] ${content.title}`

    // 逐个发送消息给选中学员
    const results = await Promise.allSettled(
      selectedStudentIds.value.map(id =>
        request.post('/v1/coach/messages', {
          student_id: Number(id),
          content: msgContent,
          message_type: 'advice',
        })
      )
    )
    const successCount = results.filter(r => r.status === 'fulfilled').length
    sent.value = true
    trackingData.value = selectedStudentIds.value.map(id => {
      const s = students.value.find(st => st.id === id)
      const succeeded = results[selectedStudentIds.value.indexOf(id)]?.status === 'fulfilled'
      return { id, name: s?.name || '', read: false, sent: succeeded, readTime: '' }
    })
    message.success(`已发送给 ${successCount}/${selectedStudentIds.value.length} 位学员`)
  } catch (e) {
    message.error('发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  loadContent()
  loadStudents()
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.content-item { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid #f0f0f0; border-radius: 8px; margin-bottom: 8px; cursor: pointer; }
.content-item:hover { background: #fafafa; }
.content-item.selected { border-color: #1890ff; background: #e6f7ff; }
.content-icon { font-size: 24px; }
.content-info { flex: 1; }
.content-name { display: block; font-size: 14px; font-weight: 500; }
.content-meta { font-size: 12px; color: #999; }
.check-mark { color: #1890ff; font-size: 18px; font-weight: 700; }

.student-check-item { padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.student-check-info { display: inline-flex; align-items: center; gap: 8px; }

.tracking-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f5f5f5; }
.tracking-name { flex: 1; font-size: 13px; }
.tracking-time { font-size: 12px; color: #999; }

.step-actions { margin-top: 20px; display: flex; gap: 8px; justify-content: flex-end; }

@media (max-width: 640px) {
  .content-item { flex-direction: column; align-items: flex-start; }
  .step-actions { flex-direction: column; }
  .step-actions .ant-btn { width: 100%; }
}
</style>
