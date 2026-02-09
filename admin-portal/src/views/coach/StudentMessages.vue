<template>
  <div class="student-messages">
    <a-page-header title="学员消息" sub-title="与学员沟通交流" />

    <a-row :gutter="16">
      <!-- 左侧：学员列表 -->
      <a-col :span="8">
        <a-card title="学员列表" size="small">
          <a-spin :spinning="loadingStudents">
            <div class="student-list">
              <div
                v-for="s in students"
                :key="s.student_id"
                class="student-item"
                :class="{ active: selectedStudent?.student_id === s.student_id }"
                @click="selectStudent(s)"
              >
                <a-avatar :size="36">{{ (s.student_name || '?')[0] }}</a-avatar>
                <div class="student-info">
                  <div class="student-name">{{ s.student_name }}</div>
                  <div class="student-preview">{{ s.last_message || '暂无消息' }}</div>
                </div>
                <a-badge v-if="s.unread_count" :count="s.unread_count" />
              </div>
              <a-empty v-if="!loadingStudents && students.length === 0" description="暂无学员消息" />
            </div>
          </a-spin>
        </a-card>
      </a-col>

      <!-- 右侧：消息历史 -->
      <a-col :span="16">
        <a-card :title="selectedStudent ? `与 ${selectedStudent.student_name} 的消息` : '选择一个学员'" size="small">
          <template v-if="selectedStudent">
            <!-- 消息列表 -->
            <div class="message-list" ref="messageListRef">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-item"
              >
                <div class="message-bubble coach">
                  <div class="message-content">{{ msg.content }}</div>
                  <div class="message-meta">
                    <a-tag v-if="msg.message_type !== 'text'" :color="typeColor(msg.message_type)" size="small">
                      {{ typeLabel(msg.message_type) }}
                    </a-tag>
                    <span class="message-time">{{ formatTime(msg.created_at) }}</span>
                    <a-tag v-if="msg.is_read" color="green" size="small">已读</a-tag>
                    <a-tag v-else size="small">未读</a-tag>
                  </div>
                </div>
              </div>
              <a-empty v-if="messages.length === 0" description="暂无消息记录" />
            </div>

            <!-- 快捷鼓励模板 -->
            <div class="quick-templates">
              <span class="template-label">快捷:</span>
              <a-tag
                v-for="(tpl, idx) in quickTemplates"
                :key="idx"
                class="template-tag"
                @click="inputMessage = tpl"
              >
                {{ tpl }}
              </a-tag>
            </div>

            <!-- 消息输入 -->
            <div class="message-input">
              <a-select v-model:value="messageType" style="width: 100px" size="small">
                <a-select-option value="text">文字</a-select-option>
                <a-select-option value="encouragement">鼓励</a-select-option>
                <a-select-option value="reminder">提醒</a-select-option>
                <a-select-option value="advice">建议</a-select-option>
              </a-select>
              <a-textarea
                v-model:value="inputMessage"
                placeholder="输入消息..."
                :auto-size="{ minRows: 1, maxRows: 4 }"
                @pressEnter="sendMessage"
              />
              <a-button type="primary" @click="sendMessage" :loading="sending">
                发送
              </a-button>
            </div>

            <!-- 创建提醒按钮 -->
            <div class="reminder-section">
              <a-button @click="showReminderModal = true" size="small">
                <template #icon><clock-circle-outlined /></template>
                为学员创建提醒
              </a-button>
            </div>
          </template>
        </a-card>
      </a-col>
    </a-row>

    <!-- 创建提醒弹窗 -->
    <a-modal
      v-model:open="showReminderModal"
      title="为学员创建提醒"
      @ok="createReminder"
      :confirm-loading="creatingReminder"
    >
      <a-form layout="vertical">
        <a-form-item label="提醒类型">
          <a-select v-model:value="reminderForm.type">
            <a-select-option value="behavior">行为提醒</a-select-option>
            <a-select-option value="medication">用药提醒</a-select-option>
            <a-select-option value="visit">随访提醒</a-select-option>
            <a-select-option value="assessment">评估提醒</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="提醒标题">
          <a-input v-model:value="reminderForm.title" placeholder="例如：记得今天散步10分钟" />
        </a-form-item>
        <a-form-item label="提醒内容">
          <a-textarea v-model:value="reminderForm.content" :rows="3" />
        </a-form-item>
        <a-form-item label="提醒时间（每天）">
          <a-input v-model:value="reminderForm.cron_time" placeholder="HH:MM 例如 08:00" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { ClockCircleOutlined } from '@ant-design/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const token = localStorage.getItem('admin_token')
const headers = { Authorization: `Bearer ${token}` }

const loadingStudents = ref(false)
const students = ref<any[]>([])
const selectedStudent = ref<any>(null)
const messages = ref<any[]>([])
const messageListRef = ref<HTMLElement>()

const inputMessage = ref('')
const messageType = ref('text')
const sending = ref(false)

const quickTemplates = [
  '加油，你做得很好！',
  '今天记得完成微行动哦',
  '坚持就是胜利！',
  '有什么困难随时跟我说',
  '你的进步我都看到了',
]

function typeLabel(type: string) {
  return { encouragement: '鼓励', reminder: '提醒', advice: '建议', text: '消息' }[type] || type
}
function typeColor(type: string) {
  return { encouragement: 'green', reminder: 'orange', advice: 'blue' }[type] || 'default'
}
function formatTime(str: string) {
  if (!str) return ''
  return str.replace('T', ' ').slice(0, 16)
}

async function loadStudents() {
  loadingStudents.value = true
  try {
    const res = await axios.get(`${API_BASE}/v1/coach/students-with-messages`, { headers })
    students.value = res.data.students || []
  } catch {
    students.value = []
  } finally {
    loadingStudents.value = false
  }
}

async function selectStudent(s: any) {
  selectedStudent.value = s
  try {
    const res = await axios.get(`${API_BASE}/v1/coach/messages/${s.student_id}`, { headers })
    messages.value = res.data.messages || []
    await nextTick()
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim() || !selectedStudent.value) return
  sending.value = true
  try {
    await axios.post(`${API_BASE}/v1/coach/messages`, {
      student_id: selectedStudent.value.student_id,
      content: inputMessage.value,
      message_type: messageType.value,
    }, { headers })
    inputMessage.value = ''
    message.success('发送成功')
    await selectStudent(selectedStudent.value)
  } catch {
    message.error('发送失败')
  } finally {
    sending.value = false
  }
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

// 提醒
const showReminderModal = ref(false)
const creatingReminder = ref(false)
const reminderForm = reactive({
  type: 'behavior',
  title: '',
  content: '',
  cron_time: '08:00',
})

async function createReminder() {
  if (!reminderForm.title || !selectedStudent.value) return
  creatingReminder.value = true
  try {
    await axios.post(`${API_BASE}/v1/coach/reminders`, {
      student_id: selectedStudent.value.student_id,
      type: reminderForm.type,
      title: reminderForm.title,
      content: reminderForm.content,
      cron_expr: reminderForm.cron_time || null,
    }, { headers })
    message.success('提醒创建成功')
    showReminderModal.value = false
    reminderForm.title = ''
    reminderForm.content = ''
  } catch {
    message.error('创建失败')
  } finally {
    creatingReminder.value = false
  }
}

onMounted(loadStudents)
</script>

<style scoped>
.student-messages {
  padding: 16px;
}

.student-list {
  max-height: 600px;
  overflow-y: auto;
}

.student-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  border-radius: 6px;

  &:hover { background: #f5f5f5; }
  &.active { background: #e6f4ff; }

  .student-info {
    flex: 1;
    overflow: hidden;

    .student-name { font-weight: 500; font-size: 14px; }
    .student-preview {
      font-size: 12px;
      color: #999;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.message-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px 0;
}

.message-item {
  margin-bottom: 12px;
}

.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  background: #e6f4ff;

  &.coach {
    margin-left: auto;
    background: #e6f4ff;
  }

  .message-content {
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .message-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
    font-size: 11px;
    color: #999;
  }
}

.quick-templates {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin: 10px 0;

  .template-label {
    font-size: 12px;
    color: #999;
  }

  .template-tag {
    cursor: pointer;
    &:hover { color: #1890ff; }
  }
}

.message-input {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 8px;

  .ant-input { flex: 1; }
}

.reminder-section {
  margin-top: 12px;
  text-align: right;
}
</style>
