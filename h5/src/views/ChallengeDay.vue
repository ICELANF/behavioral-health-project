<template>
  <div class="page-container">
    <van-nav-bar
      :title="headerTitle"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <!-- Challenge completed congratulations -->
      <template v-else-if="challengeCompleted">
        <div class="congrats-card card">
          <div class="congrats-icon">&#127942;</div>
          <h2 class="congrats-title">恭喜完成挑战!</h2>
          <p class="congrats-desc">
            你已经坚持完成了全部 {{ progress.total_days || 0 }} 天的挑战，非常棒!
          </p>
          <div class="congrats-stats">
            <div class="stat-item">
              <div class="stat-value">{{ progress.total_days || 0 }}</div>
              <div class="stat-label">总天数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ progress.completed_days || 0 }}</div>
              <div class="stat-label">完成天数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ progress.max_streak || 0 }}</div>
              <div class="stat-label">最长连续</div>
            </div>
          </div>
          <van-button
            type="primary"
            block
            round
            @click="$router.push('/challenges')"
          >
            返回挑战列表
          </van-button>
        </div>
      </template>

      <!-- Normal day view -->
      <template v-else>
        <!-- Progress header -->
        <div class="day-header card">
          <div class="day-progress-bar">
            <van-progress
              :percentage="dayProgressPercent"
              stroke-width="6"
              color="#1989fa"
              track-color="#e8e8e8"
              :show-pivot="false"
            />
            <span class="day-progress-text">
              {{ progress.current_day || 0 }} / {{ progress.total_days || 0 }} 天
            </span>
          </div>
          <div class="day-topic" v-if="todayData.day_topic">
            {{ todayData.day_topic }}
          </div>
        </div>

        <!-- Push cards timeline -->
        <div class="push-timeline" v-if="pushes.length > 0">
          <div
            v-for="(push, pushIndex) in sortedPushes"
            :key="push.id || pushIndex"
            class="push-card card"
          >
            <!-- Time + tag row -->
            <div class="push-top">
              <div class="time-badge">
                <van-icon name="clock-o" size="12" />
                <span>{{ push.push_time || '--:--' }}</span>
              </div>
              <van-tag
                :color="pushTagColor(push.tag)"
                text-color="#fff"
                size="medium"
                round
              >
                {{ pushTagLabel(push.tag) }}
              </van-tag>
              <div class="read-indicator" v-if="push.is_read">
                <van-icon name="success" color="#07c160" size="16" />
              </div>
            </div>

            <!-- Management content (collapsible) -->
            <van-collapse v-model="push._expandedSections" class="push-collapse">
              <van-collapse-item
                v-if="push.management_content"
                :title="'管理内容'"
                :name="'mgmt-' + push.id"
                icon="notes-o"
              >
                <div class="content-block management-content">
                  {{ push.management_content }}
                </div>
              </van-collapse-item>

              <van-collapse-item
                v-if="push.behavior_guidance"
                :title="'行为指导'"
                :name="'behavior-' + push.id"
                icon="guide-o"
              >
                <div class="content-block behavior-content">
                  {{ push.behavior_guidance }}
                </div>
              </van-collapse-item>
            </van-collapse>

            <!-- Survey interaction -->
            <div v-if="push.survey" class="survey-section">
              <div class="survey-header">
                <van-icon name="edit" size="16" color="#1989fa" />
                <span>{{ push.survey.title || '互动问答' }}</span>
              </div>

              <div class="survey-body">
                <div
                  v-for="(question, qIndex) in push.survey.questions"
                  :key="question.id || qIndex"
                  class="survey-question"
                >
                  <div class="question-label">
                    {{ qIndex + 1 }}. {{ question.label }}
                  </div>

                  <!-- Rating type -->
                  <template v-if="question.type === 'rating'">
                    <div class="rating-wrapper">
                      <van-rate
                        v-if="(question.max || 5) <= 10"
                        v-model="surveyResponses[push.id][question.id]"
                        :count="question.max || 5"
                        allow-half
                        color="#ffd21e"
                        void-color="#c8c9cc"
                        size="24"
                      />
                      <van-stepper
                        v-else
                        v-model="surveyResponses[push.id][question.id]"
                        :min="question.min || 0"
                        :max="question.max || 100"
                        theme="round"
                      />
                    </div>
                  </template>

                  <!-- Text type -->
                  <template v-else-if="question.type === 'text'">
                    <van-field
                      v-model="surveyResponses[push.id][question.id]"
                      type="textarea"
                      :placeholder="question.placeholder || '请输入...'"
                      rows="3"
                      maxlength="500"
                      show-word-limit
                      autosize
                      class="survey-textarea"
                    />
                    <!-- Enhanced input toolbar -->
                    <div class="input-toolbar" v-if="!push.survey_submitted">
                      <div
                        v-if="speechSupported"
                        class="toolbar-btn"
                        :class="{ active: activeRecording === `${push.id}_${question.id}` }"
                        @click="toggleVoiceInput(push.id, question.id)"
                      >
                        <van-icon name="volume-o" size="18" />
                        <span>{{ activeRecording === `${push.id}_${question.id}` ? '停止' : '语音' }}</span>
                      </div>
                      <div class="toolbar-btn" @click="triggerImageUpload(push.id, question.id)">
                        <van-icon name="photograph" size="18" />
                        <span>图片</span>
                      </div>
                      <div class="toolbar-btn" @click="openDeviceDataPopup(push.id, question.id)">
                        <van-icon name="bar-chart-o" size="18" />
                        <span>健康数据</span>
                      </div>
                    </div>
                    <!-- Image upload (hidden trigger + preview) -->
                    <div
                      v-if="getEnhanced(push.id, question.id).images.length > 0"
                      class="image-preview-list"
                    >
                      <div
                        v-for="(img, imgIdx) in getEnhanced(push.id, question.id).images"
                        :key="imgIdx"
                        class="image-preview-item"
                      >
                        <van-image :src="img" width="60" height="60" fit="cover" radius="4" />
                        <van-icon
                          name="cross"
                          class="image-remove-btn"
                          @click="removeImage(push.id, question.id, imgIdx)"
                        />
                      </div>
                    </div>
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      style="display: none"
                      :ref="(el: any) => setFileInputRef(push.id, question.id, el)"
                      @change="handleImageSelected($event, push.id, question.id)"
                    />
                  </template>

                  <!-- Single choice -->
                  <template v-else-if="question.type === 'single_choice'">
                    <van-radio-group
                      v-model="surveyResponses[push.id][question.id]"
                      direction="vertical"
                      class="choice-group"
                    >
                      <van-radio
                        v-for="option in question.options"
                        :key="option.value"
                        :name="option.value"
                        icon-size="18"
                      >
                        {{ option.label }}
                      </van-radio>
                    </van-radio-group>
                  </template>

                  <!-- Multi choice -->
                  <template v-else-if="question.type === 'multi_choice'">
                    <van-checkbox-group
                      v-model="surveyResponses[push.id][question.id]"
                      direction="vertical"
                      class="choice-group"
                    >
                      <van-checkbox
                        v-for="option in question.options"
                        :key="option.value"
                        :name="option.value"
                        shape="square"
                        icon-size="18"
                      >
                        {{ option.label }}
                      </van-checkbox>
                    </van-checkbox-group>
                  </template>
                </div>
              </div>

              <van-button
                type="primary"
                size="small"
                round
                block
                :loading="submittingSurvey === push.id"
                :disabled="push.survey_submitted"
                @click="submitSurvey(push)"
                class="survey-submit-btn"
              >
                {{ push.survey_submitted ? '已提交' : '提交' }}
              </van-button>
            </div>

            <!-- Mark as read button (if not yet read and no survey, or just a read action) -->
            <div class="push-bottom" v-if="!push.is_read">
              <van-button
                plain
                type="primary"
                size="small"
                round
                :loading="markingReadId === push.id"
                @click="markRead(push)"
              >
                <van-icon name="eye-o" />
                <span style="margin-left:4px">标记已读</span>
              </van-button>
            </div>
          </div>
        </div>

        <van-empty
          v-if="!loading && pushes.length === 0"
          description="今天暂无推送内容"
        />

        <!-- Advance to next day button -->
        <div class="advance-section" v-if="pushes.length > 0">
          <van-button
            type="success"
            block
            round
            size="large"
            :loading="advancing"
            :disabled="!canAdvance"
            @click="advanceDay"
          >
            {{ advanceButtonText }}
          </van-button>
          <p class="advance-hint" v-if="!canAdvance && pushes.length > 0">
            请先查看所有推送内容
          </p>
        </div>
      </template>
    </div>

    <!-- Device data popup -->
    <van-popup
      v-model:show="deviceDataPopup.visible"
      position="bottom"
      round
      :style="{ maxHeight: '60vh' }"
    >
      <div class="device-data-popup">
        <div class="popup-header">
          <span class="popup-title">选择今日健康数据</span>
          <van-icon name="cross" size="18" @click="deviceDataPopup.visible = false" />
        </div>
        <van-loading v-if="deviceDataPopup.loading" class="popup-loading" />
        <div v-else-if="deviceDataItems.length === 0" class="popup-empty">
          暂无今日设备数据
        </div>
        <div v-else class="device-data-list">
          <div
            v-for="item in deviceDataItems"
            :key="item.type"
            class="device-data-item"
            @click="insertDeviceData(item)"
          >
            <div class="data-icon">
              <van-icon :name="item.icon" size="22" :color="item.color" />
            </div>
            <div class="data-info">
              <div class="data-label">{{ item.label }}</div>
              <div class="data-value">{{ item.displayText }}</div>
            </div>
            <van-icon name="arrow" size="14" color="#c8c9cc" />
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showLoadingToast } from 'vant'
import api from '@/api/index'

interface SurveyQuestion {
  id: string
  type: 'rating' | 'text' | 'single_choice' | 'multi_choice'
  label: string
  placeholder?: string
  min?: number
  max?: number
  options?: { value: string; label: string }[]
}

interface Survey {
  title?: string
  questions: SurveyQuestion[]
}

interface Push {
  id: number
  push_time?: string
  tag?: string
  management_content?: string
  behavior_guidance?: string
  survey?: Survey | null
  is_read?: boolean
  survey_submitted?: boolean
  _expandedSections: string[]
}

interface ProgressInfo {
  current_day: number
  total_days: number
  completed_days: number
  max_streak: number
  status: string
}

interface EnhancedData {
  text: string
  images: string[]
  deviceData?: { type: string; value: number | string; unit: string; recordedAt: string }
}

interface DeviceDataItem {
  type: string
  label: string
  icon: string
  color: string
  displayText: string
  value: number | string
  unit: string
  recordedAt: string
}

const route = useRoute()
const router = useRouter()
const enrollmentId = route.params.id as string

const loading = ref(true)
const pushes = ref<Push[]>([])
const progress = reactive<ProgressInfo>({
  current_day: 0,
  total_days: 0,
  completed_days: 0,
  max_streak: 0,
  status: 'active',
})
const todayData = reactive<{ day_topic: string }>({ day_topic: '' })

const markingReadId = ref<number | null>(null)
const submittingSurvey = ref<number | null>(null)
const advancing = ref(false)
const challengeCompleted = ref(false)

// Survey responses keyed by pushId -> questionId -> value
const surveyResponses = reactive<Record<number, Record<string, any>>>({})

// Enhanced responses: images + device data per text question
const enhancedResponses = reactive<Record<string, EnhancedData>>({})

// Voice input
const speechSupported = ref(false)
const activeRecording = ref<string | null>(null)
let recognitionInstance: any = null

// Image upload file input refs
const fileInputRefs: Record<string, HTMLInputElement | null> = {}

// Device data popup
const deviceDataPopup = reactive({
  visible: false,
  loading: false,
  pushId: 0,
  questionId: '',
})
const deviceDataItems = ref<DeviceDataItem[]>([])

// ---- helpers ----

function enhancedKey(pushId: number, questionId: string): string {
  return `${pushId}_${questionId}`
}

function getEnhanced(pushId: number, questionId: string): EnhancedData {
  const key = enhancedKey(pushId, questionId)
  if (!enhancedResponses[key]) {
    enhancedResponses[key] = { text: '', images: [] }
  }
  return enhancedResponses[key]
}

function setFileInputRef(pushId: number, questionId: string, el: HTMLInputElement | null) {
  fileInputRefs[enhancedKey(pushId, questionId)] = el
}

// ---- computed ----

const headerTitle = computed(() => {
  if (challengeCompleted.value) return '挑战完成'
  if (todayData.day_topic) {
    return `第${progress.current_day}天 - ${todayData.day_topic}`
  }
  return `第${progress.current_day}天`
})

const dayProgressPercent = computed(() => {
  if (progress.total_days === 0) return 0
  return Math.min(100, Math.round((progress.current_day / progress.total_days) * 100))
})

const sortedPushes = computed(() => {
  return [...pushes.value].sort((a, b) => {
    const timeA = a.push_time || '00:00'
    const timeB = b.push_time || '00:00'
    return timeA.localeCompare(timeB)
  })
})

const canAdvance = computed(() => {
  if (pushes.value.length === 0) return false
  return pushes.value.every(p => p.is_read)
})

const advanceButtonText = computed(() => {
  if (progress.current_day >= progress.total_days) {
    return '完成挑战'
  }
  return '完成今天'
})

// ---- push tag helpers ----

function pushTagColor(tag?: string): string {
  const map: Record<string, string> = {
    core: '#fa8c16',
    optional: '#52c41a',
    assessment: '#722ed1',
    info: '#1989fa',
  }
  return map[tag || ''] || '#999'
}

function pushTagLabel(tag?: string): string {
  const map: Record<string, string> = {
    core: '核心',
    optional: '可选',
    assessment: '评估',
    info: '说明',
  }
  return map[tag || ''] || tag || '推送'
}

// ---- survey init ----

function initSurveyResponses(pushList: Push[]) {
  for (const push of pushList) {
    if (push.survey && push.survey.questions && !surveyResponses[push.id]) {
      surveyResponses[push.id] = {}
      for (const q of push.survey.questions) {
        if (q.type === 'multi_choice') {
          surveyResponses[push.id][q.id] = []
        } else if (q.type === 'rating') {
          surveyResponses[push.id][q.id] = q.min || 0
        } else {
          surveyResponses[push.id][q.id] = ''
        }
      }
    }
    if (!push._expandedSections) {
      push._expandedSections = []
    }
  }
}

// ---- data loading ----

async function loadToday() {
  loading.value = true
  try {
    const [todayRes, progressRes] = await Promise.all([
      api.get(`/api/v1/challenges/enrollments/${enrollmentId}/today`),
      api.get(`/api/v1/challenges/enrollments/${enrollmentId}/progress`),
    ])

    const todayPayload = todayRes as any
    const progressPayload = progressRes as any

    progress.current_day = progressPayload.current_day || 0
    progress.total_days = progressPayload.duration_days || progressPayload.total_days || 0
    progress.completed_days = progressPayload.completed_days || 0
    progress.max_streak = progressPayload.max_streak || 0
    progress.status = progressPayload.status || 'active'

    if (progress.status === 'completed') {
      challengeCompleted.value = true
      return
    }

    todayData.day_topic = todayPayload.day_topic || ''

    const rawPushes: any[] = todayPayload.pushes || todayPayload.items || []
    pushes.value = rawPushes.map((p: any) => ({
      id: p.push_id || p.id,
      push_time: p.push_time || p.time,
      tag: p.tag || p.type,
      management_content: p.management_content || p.content,
      behavior_guidance: p.behavior_guidance || p.guidance,
      survey: p.survey || null,
      is_read: p.is_read || p.status === 'read' || false,
      survey_submitted: p.survey_completed || p.survey_submitted || false,
      _expandedSections: [],
    }))

    initSurveyResponses(pushes.value)
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '加载失败'
    showToast(msg)
    pushes.value = []
  } finally {
    loading.value = false
  }
}

// ---- mark read ----

async function markRead(push: Push) {
  markingReadId.value = push.id
  try {
    await api.post(`/api/v1/challenges/enrollments/${enrollmentId}/read/${push.id}`)
    push.is_read = true
    showToast({ message: '已标记已读', position: 'bottom' })
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '操作失败'
    showToast(msg)
  } finally {
    markingReadId.value = null
  }
}

// ---- submit survey (enhanced) ----

async function submitSurvey(push: Push) {
  if (!push.survey || push.survey_submitted) return

  const responses = surveyResponses[push.id]
  if (!responses) {
    showToast('请先填写问卷')
    return
  }

  const hasEmptyRequired = push.survey.questions.some(q => {
    const val = responses[q.id]
    if (q.type === 'text') return !val || (val as string).trim() === ''
    if (q.type === 'multi_choice') return !val || (val as string[]).length === 0
    if (q.type === 'single_choice') return val === '' || val === undefined || val === null
    if (q.type === 'rating') return val === 0 || val === undefined || val === null
    return false
  })

  if (hasEmptyRequired) {
    showToast('请完成所有问题')
    return
  }

  // Build final responses: merge enhanced data for text questions
  const finalResponses: Record<string, any> = {}
  for (const q of push.survey.questions) {
    const val = responses[q.id]
    if (q.type === 'text') {
      const enhanced = getEnhanced(push.id, q.id)
      const hasImages = enhanced.images.length > 0
      const hasDeviceData = !!enhanced.deviceData
      if (hasImages || hasDeviceData) {
        finalResponses[q.id] = {
          text: val,
          ...(hasImages ? { images: enhanced.images } : {}),
          ...(hasDeviceData ? { deviceData: enhanced.deviceData } : {}),
        }
      } else {
        finalResponses[q.id] = val
      }
    } else {
      finalResponses[q.id] = val
    }
  }

  submittingSurvey.value = push.id
  try {
    await api.post(
      `/api/v1/challenges/enrollments/${enrollmentId}/survey/${push.id}`,
      { responses: finalResponses }
    )
    push.survey_submitted = true
    showSuccessToast('提交成功')

    if (!push.is_read) {
      push.is_read = true
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '提交失败'
    showToast(msg)
  } finally {
    submittingSurvey.value = null
  }
}

// ---- advance day ----

async function advanceDay() {
  if (!canAdvance.value) {
    showToast('请先查看所有推送内容')
    return
  }

  advancing.value = true
  try {
    const res: any = await api.post(`/api/v1/challenges/enrollments/${enrollmentId}/advance`)

    if (res.completed || res.status === 'completed') {
      challengeCompleted.value = true
      showSuccessToast('挑战完成!')
    } else {
      showSuccessToast('进入下一天!')
      await loadToday()
    }
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '操作失败'
    showToast(msg)
  } finally {
    advancing.value = false
  }
}

// ---- voice input ----

function initSpeechRecognition() {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (SpeechRecognition) {
    speechSupported.value = true
  }
}

function toggleVoiceInput(pushId: number, questionId: string) {
  const key = `${pushId}_${questionId}`

  // If currently recording this field, stop
  if (activeRecording.value === key) {
    if (recognitionInstance) {
      recognitionInstance.stop()
    }
    activeRecording.value = null
    return
  }

  // Stop any existing recording
  if (recognitionInstance) {
    recognitionInstance.stop()
  }

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    showToast('当前浏览器不支持语音输入')
    return
  }

  const recognition = new SpeechRecognition()
  recognition.lang = 'zh-CN'
  recognition.continuous = false
  recognition.interimResults = false

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript
    if (transcript && surveyResponses[pushId]) {
      const current = surveyResponses[pushId][questionId] || ''
      surveyResponses[pushId][questionId] = current ? `${current} ${transcript}` : transcript
    }
  }

  recognition.onend = () => {
    activeRecording.value = null
    recognitionInstance = null
  }

  recognition.onerror = (event: any) => {
    if (event.error !== 'aborted') {
      showToast('语音识别失败，请重试')
    }
    activeRecording.value = null
    recognitionInstance = null
  }

  recognitionInstance = recognition
  activeRecording.value = key
  recognition.start()
  showToast({ message: '请开始说话...', position: 'bottom', duration: 1500 })
}

// ---- image upload ----

function triggerImageUpload(pushId: number, questionId: string) {
  const enhanced = getEnhanced(pushId, questionId)
  if (enhanced.images.length >= 3) {
    showToast('最多上传3张图片')
    return
  }
  const key = enhancedKey(pushId, questionId)
  const input = fileInputRefs[key]
  if (input) {
    input.value = ''
    input.click()
  }
}

async function handleImageSelected(event: Event, pushId: number, questionId: string) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return

  if (file.size > 5 * 1024 * 1024) {
    showToast('图片大小不能超过5MB')
    return
  }

  const enhanced = getEnhanced(pushId, questionId)
  if (enhanced.images.length >= 3) {
    showToast('最多上传3张图片')
    return
  }

  const toast = showLoadingToast({ message: '上传中...', forbidClick: true, duration: 0 })
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res: any = await api.post('/api/v1/upload/survey-image', formData)
    enhanced.images.push(res.url)
    showToast({ message: '上传成功', position: 'bottom' })
  } catch (err: any) {
    const msg = err?.response?.data?.detail || '上传失败'
    showToast(msg)
  } finally {
    toast.close()
  }
}

function removeImage(pushId: number, questionId: string, index: number) {
  const enhanced = getEnhanced(pushId, questionId)
  enhanced.images.splice(index, 1)
}

// ---- device data ----

async function openDeviceDataPopup(pushId: number, questionId: string) {
  deviceDataPopup.pushId = pushId
  deviceDataPopup.questionId = questionId
  deviceDataPopup.visible = true
  deviceDataPopup.loading = true
  deviceDataItems.value = []

  try {
    const res: any = await api.get('/api/v1/mp/device/dashboard/today')
    const items: DeviceDataItem[] = []

    if (res.glucose?.current != null) {
      items.push({
        type: 'glucose',
        label: '血糖',
        icon: 'fire-o',
        color: '#fa8c16',
        displayText: `${res.glucose.current} mmol/L`,
        value: res.glucose.current,
        unit: 'mmol/L',
        recordedAt: res.glucose.recorded_at || new Date().toISOString(),
      })
    }

    if (res.weight?.weight_kg != null) {
      items.push({
        type: 'weight',
        label: '体重',
        icon: 'balance-o',
        color: '#1989fa',
        displayText: `${res.weight.weight_kg} kg`,
        value: res.weight.weight_kg,
        unit: 'kg',
        recordedAt: res.weight.recorded_at || new Date().toISOString(),
      })
    }

    if (res.sleep?.duration_hours != null) {
      const score = res.sleep.score != null ? ` (评分${res.sleep.score})` : ''
      items.push({
        type: 'sleep',
        label: '睡眠',
        icon: 'hotel-o',
        color: '#722ed1',
        displayText: `${res.sleep.duration_hours}小时${score}`,
        value: res.sleep.duration_hours,
        unit: '小时',
        recordedAt: res.sleep.recorded_at || new Date().toISOString(),
      })
    }

    if (res.activity?.steps != null) {
      items.push({
        type: 'activity',
        label: '活动',
        icon: 'smile-o',
        color: '#52c41a',
        displayText: `${res.activity.steps}步`,
        value: res.activity.steps,
        unit: '步',
        recordedAt: res.activity.recorded_at || new Date().toISOString(),
      })
    }

    deviceDataItems.value = items
  } catch (err: any) {
    showToast('获取设备数据失败')
  } finally {
    deviceDataPopup.loading = false
  }
}

function insertDeviceData(item: DeviceDataItem) {
  const { pushId, questionId } = deviceDataPopup

  // Append formatted text to textarea
  if (surveyResponses[pushId]) {
    const current = surveyResponses[pushId][questionId] || ''
    const insertText = `[${item.label}: ${item.displayText}]`
    surveyResponses[pushId][questionId] = current ? `${current}\n${insertText}` : insertText
  }

  // Store structured device data
  const enhanced = getEnhanced(pushId, questionId)
  enhanced.deviceData = {
    type: item.type,
    value: item.value,
    unit: item.unit,
    recordedAt: item.recordedAt,
  }

  deviceDataPopup.visible = false
  showToast({ message: `已插入${item.label}数据`, position: 'bottom' })
}

// ---- lifecycle ----

watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      challengeCompleted.value = false
      pushes.value = []
      loadToday()
    }
  }
)

onMounted(() => {
  initSpeechRecognition()
  loadToday()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading {
  text-align: center;
  padding: 60px 0;
}

// Congratulations card
.congrats-card {
  text-align: center;
  padding: 40px $spacing-lg;

  .congrats-icon {
    font-size: 64px;
    margin-bottom: $spacing-md;
  }

  .congrats-title {
    font-size: 22px;
    font-weight: 700;
    color: $text-color;
    margin-bottom: $spacing-xs;
  }

  .congrats-desc {
    font-size: $font-size-md;
    color: $text-color-secondary;
    line-height: 1.6;
    margin-bottom: $spacing-lg;
  }

  .congrats-stats {
    display: flex;
    justify-content: space-around;
    margin-bottom: $spacing-lg;
    padding: $spacing-md 0;
    border-top: 1px solid #f0f0f0;
    border-bottom: 1px solid #f0f0f0;

    .stat-item {
      text-align: center;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #1989fa;
    }

    .stat-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }
}

// Day header
.day-header {
  .day-progress-bar {
    display: flex;
    align-items: center;
    gap: $spacing-sm;

    :deep(.van-progress) {
      flex: 1;
    }
  }

  .day-progress-text {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .day-topic {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $text-color;
    margin-top: $spacing-sm;
    line-height: 1.4;
  }
}

// Push timeline
.push-timeline {
  position: relative;
  padding-left: 4px;

  &::before {
    content: '';
    position: absolute;
    left: 20px;
    top: 24px;
    bottom: 24px;
    width: 2px;
    background: #e8e8e8;
  }
}

.push-card {
  position: relative;
  margin-left: 12px;
  margin-bottom: $spacing-sm;

  .push-top {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    margin-bottom: $spacing-sm;
  }

  .time-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    background: #f7f8fa;
    border-radius: 16px;
    font-size: $font-size-sm;
    color: $text-color;
    font-weight: 500;
  }

  .read-indicator {
    margin-left: auto;
    display: flex;
    align-items: center;
  }

  .push-collapse {
    margin-bottom: $spacing-sm;

    :deep(.van-collapse-item) {
      margin-bottom: 0;
    }

    :deep(.van-collapse-item__title) {
      padding: 10px 0;
      font-size: $font-size-md;
    }

    :deep(.van-collapse-item__wrapper) {
      .van-collapse-item__content {
        padding: 0 0 $spacing-sm;
      }
    }

    :deep(.van-cell) {
      padding-left: 0;
      padding-right: 0;
    }

    :deep(.van-cell::after) {
      left: 0;
      right: 0;
    }
  }

  .content-block {
    font-size: $font-size-md;
    color: $text-color;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .management-content {
    padding: $spacing-sm;
    background: #fffbe6;
    border-radius: $border-radius;
    border-left: 3px solid #faad14;
  }

  .behavior-content {
    padding: $spacing-sm;
    background: #f6ffed;
    border-radius: $border-radius;
    border-left: 3px solid #52c41a;
  }

  .push-bottom {
    display: flex;
    justify-content: flex-end;
    padding-top: $spacing-xs;
  }
}

// Survey section
.survey-section {
  margin-top: $spacing-sm;
  padding: $spacing-md;
  background: #f0f5ff;
  border-radius: $border-radius;
  border: 1px solid #d6e4ff;

  .survey-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: $font-size-md;
    font-weight: 600;
    color: #1989fa;
    margin-bottom: $spacing-sm;
  }

  .survey-body {
    margin-bottom: $spacing-md;
  }

  .survey-question {
    margin-bottom: $spacing-md;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .question-label {
    font-size: $font-size-md;
    color: $text-color;
    font-weight: 500;
    margin-bottom: $spacing-xs;
    line-height: 1.5;
  }

  .rating-wrapper {
    background: #f7f8fa;
    border-radius: 8px;
    padding: 8px 12px;
  }

  .survey-textarea {
    border-radius: $border-radius;
    overflow: hidden;

    :deep(.van-field__body) {
      background: #fff;
      border-radius: $border-radius;
    }
  }

  .choice-group {
    padding: $spacing-xs 0;

    :deep(.van-radio),
    :deep(.van-checkbox) {
      padding: 6px 0;
    }

    :deep(.van-radio__label),
    :deep(.van-checkbox__label) {
      font-size: $font-size-md;
      color: $text-color;
    }
  }

  .survey-submit-btn {
    margin-top: $spacing-sm;
  }
}

// Enhanced input toolbar
.input-toolbar {
  display: flex;
  gap: 0;
  margin-top: 6px;
  background: #f7f8fa;
  border-radius: 8px;
  overflow: hidden;

  .toolbar-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 0;
    font-size: 12px;
    color: #666;
    cursor: pointer;
    transition: background 0.2s;

    &:not(:last-child) {
      border-right: 1px solid #eee;
    }

    &:active {
      background: #eee;
    }

    &.active {
      color: #ee0a24;
      background: #fff1f0;
    }
  }
}

// Image preview
.image-preview-list {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;

  .image-preview-item {
    position: relative;

    .image-remove-btn {
      position: absolute;
      top: -6px;
      right: -6px;
      width: 18px;
      height: 18px;
      background: rgba(0, 0, 0, 0.6);
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      cursor: pointer;
      z-index: 1;
    }
  }
}

// Device data popup
.device-data-popup {
  padding: 16px;

  .popup-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;

    .popup-title {
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }
  }

  .popup-loading {
    text-align: center;
    padding: 30px 0;
  }

  .popup-empty {
    text-align: center;
    padding: 30px 0;
    color: #999;
    font-size: 14px;
  }

  .device-data-list {
    .device-data-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 0;
      cursor: pointer;

      &:not(:last-child) {
        border-bottom: 1px solid #f5f5f5;
      }

      &:active {
        opacity: 0.7;
      }

      .data-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: #f7f8fa;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .data-info {
        flex: 1;
        min-width: 0;

        .data-label {
          font-size: 14px;
          color: #333;
          font-weight: 500;
        }

        .data-value {
          font-size: 13px;
          color: #666;
          margin-top: 2px;
        }
      }
    }
  }
}

// Advance section
.advance-section {
  padding: $spacing-md 0 $spacing-lg;

  .advance-hint {
    text-align: center;
    font-size: $font-size-sm;
    color: $text-color-placeholder;
    margin-top: $spacing-xs;
  }
}

:deep(.van-empty) {
  padding: 40px 0;
}
</style>
