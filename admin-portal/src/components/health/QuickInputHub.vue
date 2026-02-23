<template>
  <a-drawer
    :open="open"
    placement="bottom"
    :height="'75vh'"
    :closable="true"
    title="快速采集中心"
    @close="$emit('update:open', false)"
    class="quick-hub-drawer"
  >
    <!-- Mode selector tabs -->
    <div class="hub-modes">
      <div
        v-for="m in modes"
        :key="m.key"
        class="hub-mode-card"
        :class="{ active: activeMode === m.key }"
        @click="selectMode(m.key)"
      >
        <div class="mode-icon">{{ m.icon }}</div>
        <div class="mode-label">{{ m.label }}</div>
        <div class="mode-desc">{{ m.desc }}</div>
      </div>
    </div>

    <!-- ==================== Mode 1: Quick Record ==================== -->
    <div v-if="activeMode === 'record'" class="hub-panel">
      <!-- Data type pills -->
      <div class="pill-scroll">
        <div
          v-for="dt in dataTypes"
          :key="dt.id"
          class="type-pill"
          :class="{ active: recordType === dt.id }"
          @click="recordType = dt.id"
        >
          {{ dt.icon }} {{ dt.name }}
        </div>
      </div>

      <!-- Inline forms per type -->
      <div class="inline-form" v-if="recordType">
        <!-- Glucose -->
        <div v-if="recordType === 'glucose'">
          <div class="pill-scroll" style="margin-bottom:12px">
            <div
              v-for="opt in glucoseTimeOptions"
              :key="opt.value"
              class="type-pill small"
              :class="{ active: formData.glucoseTime === opt.value }"
              @click="formData.glucoseTime = opt.value"
            >
              {{ opt.label }}
            </div>
          </div>
          <BigNumberInput
            v-model="formData.glucoseValue"
            label="血糖值"
            icon="🩸"
            unit="mmol/L"
            :step="0.1"
            :quick-values="[5.0, 5.5, 6.0, 6.5, 7.0]"
          />
        </div>

        <!-- Weight -->
        <div v-if="recordType === 'weight'">
          <BigNumberInput
            v-model="formData.weightValue"
            label="体重"
            icon="⚖️"
            unit="kg"
            :step="0.1"
            :quick-values="[60, 65, 70, 75, 80]"
          />
        </div>

        <!-- Blood Pressure -->
        <div v-if="recordType === 'bloodPressure'">
          <div class="bp-inputs">
            <div class="bp-half">
              <div class="bp-label">收缩压 (高压)</div>
              <input v-model="formData.systolic" type="number" placeholder="120" class="bp-input" />
              <div class="bp-unit">mmHg</div>
            </div>
            <div class="bp-half">
              <div class="bp-label">舒张压 (低压)</div>
              <input v-model="formData.diastolic" type="number" placeholder="80" class="bp-input" />
              <div class="bp-unit">mmHg</div>
            </div>
          </div>
        </div>

        <!-- Exercise -->
        <div v-if="recordType === 'exercise'">
          <div class="pill-scroll" style="margin-bottom:12px">
            <div
              v-for="opt in exerciseTypeOptions"
              :key="opt.value"
              class="type-pill small"
              :class="{ active: formData.exerciseType === opt.value }"
              @click="formData.exerciseType = opt.value"
            >
              {{ opt.icon }} {{ opt.label }}
            </div>
          </div>
          <BigNumberInput
            v-model="formData.exerciseDuration"
            label="运动时长"
            icon="🏃"
            unit="分钟"
            :step="1"
            placeholder="30"
            :quick-values="[15, 30, 45, 60, 90]"
          />
        </div>

        <!-- Mood -->
        <div v-if="recordType === 'mood'">
          <div class="mood-row">
            <div
              v-for="mood in moodOptions"
              :key="mood.value"
              class="mood-chip"
              :class="{ active: formData.moodLevel === mood.value }"
              @click="formData.moodLevel = mood.value"
            >
              <span class="mood-emoji">{{ mood.emoji }}</span>
              <span class="mood-text">{{ mood.label }}</span>
            </div>
          </div>
          <textarea
            v-model="formData.moodNote"
            placeholder="补充说明（选填）..."
            class="hub-textarea"
            rows="3"
            maxlength="200"
          />
        </div>

        <!-- Meal -->
        <div v-if="recordType === 'meal'">
          <textarea
            v-model="formData.mealDescription"
            placeholder="描述今天的饮食..."
            class="hub-textarea"
            rows="4"
            maxlength="300"
          />
        </div>

        <!-- Submit button -->
        <button
          class="hub-submit-btn"
          :disabled="!isRecordValid || submitting"
          @click="submitRecord"
        >
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </div>
    </div>

    <!-- ==================== Mode 2: Photo Capture ==================== -->
    <div v-if="activeMode === 'photo'" class="hub-panel">
      <div v-if="!photoPreview && !photoResult" class="photo-capture-area" @click="triggerPhoto">
        <div class="capture-icon">📷</div>
        <div class="capture-text">点击拍照或选择图片</div>
        <div class="capture-hint">AI 将自动识别食物并分析营养成分</div>
      </div>

      <input
        ref="photoInputRef"
        type="file"
        accept="image/*"
        capture="environment"
        style="display:none"
        @change="onPhotoSelected"
      />

      <!-- Preview + loading -->
      <div v-if="photoPreview && !photoResult" class="photo-preview">
        <img :src="photoPreview" alt="preview" class="preview-img" />
        <div class="photo-loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">食物识别中...</div>
        </div>
      </div>

      <!-- Result card -->
      <div v-if="photoResult" class="photo-result">
        <img :src="photoPreview" alt="food" class="result-img" />
        <div class="result-card">
          <div class="result-name">{{ photoResult.food_name || '食物' }}</div>
          <div class="result-nutrients">
            <div class="nutrient-item">
              <span class="nutrient-label">热量</span>
              <span class="nutrient-value">{{ photoResult.calories || '--' }} kcal</span>
            </div>
            <div class="nutrient-item">
              <span class="nutrient-label">蛋白质</span>
              <span class="nutrient-value">{{ photoResult.protein || '--' }} g</span>
            </div>
            <div class="nutrient-item">
              <span class="nutrient-label">脂肪</span>
              <span class="nutrient-value">{{ photoResult.fat || '--' }} g</span>
            </div>
            <div class="nutrient-item">
              <span class="nutrient-label">碳水</span>
              <span class="nutrient-value">{{ photoResult.carbs || '--' }} g</span>
            </div>
          </div>
          <div v-if="photoResult.advice" class="result-advice">
            💡 {{ photoResult.advice }}
          </div>
        </div>
        <div class="result-actions">
          <button class="hub-submit-btn secondary" @click="resetPhoto">重新拍照</button>
          <button class="hub-submit-btn" @click="closeHub">完成</button>
        </div>
      </div>

      <!-- Error state -->
      <div v-if="photoError" class="photo-error">
        <div class="error-icon">⚠️</div>
        <div class="error-text">{{ photoError }}</div>
        <button class="hub-submit-btn secondary" @click="resetPhoto">重试</button>
      </div>
    </div>

    <!-- ==================== Mode 3: Voice Input ==================== -->
    <div v-if="activeMode === 'voice'" class="hub-panel">
      <!-- No mic at all -->
      <div v-if="!speechSupported && !mediaRecorderSupported" class="voice-unsupported">
        <div class="unsupported-icon">🎤</div>
        <div class="unsupported-text">当前浏览器不支持语音输入</div>
        <div class="unsupported-hint">请使用 Chrome 浏览器或升级到最新版</div>
      </div>

      <div v-else class="voice-area">
        <!-- Mode indicator when using server ASR -->
        <div v-if="!speechSupported" class="voice-mode-tag">服务端语音识别模式</div>

        <!-- Mic button -->
        <div
          class="mic-button"
          :class="{ recording: isRecording }"
          @click="toggleRecording"
        >
          <div class="mic-icon">🎤</div>
          <div v-if="isRecording" class="mic-pulse"></div>
        </div>
        <div class="mic-hint">
          {{ transcribing ? '语音转写中...' : isRecording ? '正在录音...' : '点击开始说话' }}
        </div>

        <!-- Transcribing indicator -->
        <div v-if="transcribing" class="transcribing-row">
          <div class="loading-spinner"></div>
          <span>识别中，请稍候...</span>
        </div>

        <!-- Transcript -->
        <textarea
          v-model="voiceText"
          placeholder="语音识别结果将显示在这里，也可以手动编辑..."
          class="hub-textarea"
          rows="4"
        />

        <!-- Category pills -->
        <div class="voice-category">
          <div class="category-label">记录类别</div>
          <div class="pill-scroll">
            <div
              v-for="cat in voiceCategories"
              :key="cat.value"
              class="type-pill small"
              :class="{ active: voiceCategory === cat.value }"
              @click="voiceCategory = cat.value"
            >
              {{ cat.icon }} {{ cat.label }}
            </div>
          </div>
        </div>

        <button
          class="hub-submit-btn"
          :disabled="!voiceText.trim() || submitting || transcribing"
          @click="submitVoice"
        >
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </div>
    </div>

    <!-- ==================== Mode 4: Ask AI ==================== -->
    <!-- Handled in selectMode directly -->
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { healthApi } from '@/api/health'
import BigNumberInput from './BigNumberInput.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'data-submitted'): void
}>()

const router = useRouter()

// ── Mode definitions ──
const modes = [
  { key: 'record', icon: '📝', label: '快速记录', desc: '血糖/体重/血压' },
  { key: 'photo', icon: '📷', label: '拍一拍', desc: '食物识别' },
  { key: 'voice', icon: '🎤', label: '说一说', desc: '语音记录' },
  { key: 'ai', icon: '💬', label: '问AI', desc: 'AI健康助手' },
]
const activeMode = ref('record')

const selectMode = (key: string) => {
  if (key === 'ai') {
    emit('update:open', false)
    router.push('/client/chat-v2')
    return
  }
  activeMode.value = key
}

// Reset state when drawer closes
watch(() => props.open, (v) => {
  if (!v) {
    resetAllState()
  }
})

const resetAllState = () => {
  activeMode.value = 'record'
  recordType.value = ''
  submitting.value = false
  transcribing.value = false
  resetPhoto()
  voiceText.value = ''
  stopRecording()
}

// ══════════════════════════════════════════
// Mode 1: Quick Record
// ══════════════════════════════════════════
const dataTypes = [
  { id: 'glucose', icon: '🩸', name: '血糖' },
  { id: 'weight', icon: '⚖️', name: '体重' },
  { id: 'bloodPressure', icon: '💓', name: '血压' },
  { id: 'exercise', icon: '🏃', name: '运动' },
  { id: 'mood', icon: '😊', name: '心情' },
  { id: 'meal', icon: '🍽️', name: '饮食' },
]

const recordType = ref('')
const submitting = ref(false)

const glucoseTimeOptions = [
  { label: '空腹', value: 'fasting' },
  { label: '早餐后', value: 'after_breakfast' },
  { label: '午餐前', value: 'before_lunch' },
  { label: '午餐后', value: 'after_lunch' },
  { label: '晚餐前', value: 'before_dinner' },
  { label: '晚餐后', value: 'after_dinner' },
  { label: '睡前', value: 'before_sleep' },
]

const exerciseTypeOptions = [
  { label: '步行', value: 'walking', icon: '🚶' },
  { label: '跑步', value: 'running', icon: '🏃' },
  { label: '骑行', value: 'cycling', icon: '🚴' },
  { label: '游泳', value: 'swimming', icon: '🏊' },
  { label: '瑜伽', value: 'yoga', icon: '🧘' },
  { label: '其他', value: 'other', icon: '💪' },
]

const moodOptions = [
  { value: 5, emoji: '😄', label: '很开心' },
  { value: 4, emoji: '🙂', label: '开心' },
  { value: 3, emoji: '😐', label: '一般' },
  { value: 2, emoji: '😔', label: '不太好' },
  { value: 1, emoji: '😢', label: '很难过' },
]

const formData = ref({
  glucoseValue: '' as string | number,
  glucoseTime: 'fasting',
  weightValue: '' as string | number,
  systolic: '',
  diastolic: '',
  exerciseType: 'walking',
  exerciseDuration: '' as string | number,
  moodLevel: 3,
  moodNote: '',
  mealDescription: '',
})

const isRecordValid = computed(() => {
  switch (recordType.value) {
    case 'glucose':
      return !!formData.value.glucoseValue && parseFloat(String(formData.value.glucoseValue)) > 0
    case 'weight':
      return !!formData.value.weightValue && parseFloat(String(formData.value.weightValue)) > 0
    case 'bloodPressure':
      return !!formData.value.systolic && !!formData.value.diastolic
    case 'exercise':
      return !!formData.value.exerciseDuration && parseInt(String(formData.value.exerciseDuration)) > 0
    case 'mood':
      return !!formData.value.moodLevel
    case 'meal':
      return !!formData.value.mealDescription
    default:
      return false
  }
})

const submitRecord = async () => {
  submitting.value = true
  try {
    const ts = new Date().toISOString()
    switch (recordType.value) {
      case 'glucose':
        await healthApi.recordGlucose({
          value: parseFloat(String(formData.value.glucoseValue)),
          measurement_time: ts,
          meal_tag: formData.value.glucoseTime,
        })
        break
      case 'weight':
        await healthApi.recordWeight({
          value: parseFloat(String(formData.value.weightValue)),
          measurement_time: ts,
        })
        break
      case 'bloodPressure':
        await healthApi.recordBloodPressure({
          systolic: parseInt(formData.value.systolic),
          diastolic: parseInt(formData.value.diastolic),
          measurement_time: ts,
        })
        break
      case 'exercise':
        await healthApi.recordExercise({
          type: formData.value.exerciseType,
          duration: parseInt(String(formData.value.exerciseDuration)),
          note: `${formData.value.exerciseType} ${formData.value.exerciseDuration}分钟`,
        })
        break
      case 'mood':
        await healthApi.recordMood({
          score: formData.value.moodLevel,
          note: formData.value.moodNote,
        })
        break
      case 'meal':
        await healthApi.recordMeal({
          description: formData.value.mealDescription,
          note: formData.value.mealDescription,
        })
        break
    }
    emit('data-submitted')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// ══════════════════════════════════════════
// Mode 2: Photo Capture
// ══════════════════════════════════════════
const photoInputRef = ref<HTMLInputElement>()
const photoPreview = ref('')
const photoResult = ref<any>(null)
const photoError = ref('')

const triggerPhoto = () => {
  photoInputRef.value?.click()
}

const onPhotoSelected = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  // Show preview
  photoPreview.value = URL.createObjectURL(file)
  photoError.value = ''
  photoResult.value = null

  // Call API
  try {
    const fd = new FormData()
    fd.append('file', file)
    const result = await healthApi.recognizeFood(fd)
    photoResult.value = result
  } catch (e: any) {
    photoError.value = e?.response?.data?.detail || '识别失败，请重试'
    photoPreview.value = ''
  }
}

const resetPhoto = () => {
  photoPreview.value = ''
  photoResult.value = null
  photoError.value = ''
  if (photoInputRef.value) photoInputRef.value.value = ''
}

// ══════════════════════════════════════════
// Mode 3: Voice Input (Web Speech API primary + MediaRecorder→server ASR fallback)
// ══════════════════════════════════════════
const SpeechRecognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
const speechSupported = !!SpeechRecognitionClass
const mediaRecorderSupported = typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia

const isRecording = ref(false)
const transcribing = ref(false)
const voiceText = ref('')
const voiceCategory = ref('meal')
let recognition: any = null
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let mediaStream: MediaStream | null = null

const voiceCategories = [
  { value: 'meal', icon: '🍽️', label: '饮食记录' },
  { value: 'mood', icon: '😊', label: '心情日记' },
]

const toggleRecording = () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    speechSupported ? startWebSpeech() : startMediaRecorder()
  }
}

// ── Web Speech API (primary, Chrome) ──
const startWebSpeech = () => {
  if (!SpeechRecognitionClass) return
  recognition = new SpeechRecognitionClass()
  recognition.lang = 'zh-CN'
  recognition.continuous = true
  recognition.interimResults = true

  recognition.onresult = (event: any) => {
    let transcript = ''
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript
    }
    voiceText.value = transcript
  }

  recognition.onerror = (event: any) => {
    console.error('Speech recognition error:', event.error)
    isRecording.value = false
  }

  recognition.onend = () => {
    isRecording.value = false
  }

  recognition.start()
  isRecording.value = true
}

// ── MediaRecorder → server ASR (fallback) ──
const startMediaRecorder = async () => {
  if (!mediaRecorderSupported) return
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    const mimeType = getSupportedMimeType()
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType })
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = async () => {
      mediaStream?.getTracks().forEach(t => t.stop())
      mediaStream = null
      if (audioChunks.length === 0) return
      transcribing.value = true
      try {
        const blob = new Blob(audioChunks, { type: audioChunks[0].type || 'audio/webm' })
        const ext = blob.type.includes('mp4') ? 'm4a' : 'webm'
        const fd = new FormData()
        fd.append('file', blob, `recording.${ext}`)
        fd.append('language', 'zh')
        const result = await healthApi.transcribeAudio(fd)
        const text = result?.data?.text || result?.text || ''
        if (text) voiceText.value = (voiceText.value ? voiceText.value + ' ' : '') + text
        else message.warning('未识别到语音内容')
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '语音识别失败')
      } finally {
        transcribing.value = false
      }
    }
    mediaRecorder.start()
    isRecording.value = true
  } catch (e) {
    message.error('无法访问麦克风，请检查权限')
  }
}

const getSupportedMimeType = (): string => {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  for (const t of types) { if (MediaRecorder.isTypeSupported(t)) return t }
  return 'audio/webm'
}

const stopRecording = () => {
  // Web Speech
  if (recognition) {
    try { recognition.stop() } catch {}
    recognition = null
  }
  // MediaRecorder
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    try { mediaRecorder.stop() } catch {}
  }
  mediaRecorder = null
  isRecording.value = false
}

const submitVoice = async () => {
  if (!voiceText.value.trim()) return
  submitting.value = true
  try {
    if (voiceCategory.value === 'meal') {
      await healthApi.recordMeal({
        description: voiceText.value.trim(),
        note: voiceText.value.trim(),
      })
    } else {
      await healthApi.recordMood({
        score: 3,
        note: voiceText.value.trim(),
      })
    }
    emit('data-submitted')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

const closeHub = () => {
  emit('update:open', false)
}
</script>

<style scoped>
/* ── Mode selector grid ── */
.hub-modes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.hub-mode-card {
  text-align: center;
  padding: 14px 6px 10px;
  border-radius: 14px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s;
}

.hub-mode-card:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.hub-mode-card.active {
  border-color: #10b981;
  background: #ecfdf5;
  box-shadow: 0 2px 8px rgba(16,185,129,0.15);
}

.mode-icon {
  font-size: 28px;
  margin-bottom: 4px;
}

.mode-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.mode-desc {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

/* ── Hub panel ── */
.hub-panel {
  padding: 4px 0;
}

/* ── Pill scroll ── */
.pill-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 16px;
  -webkit-overflow-scrolling: touch;
}

.pill-scroll::-webkit-scrollbar {
  display: none;
}

.type-pill {
  flex-shrink: 0;
  padding: 8px 16px;
  border-radius: 20px;
  border: 2px solid #e5e7eb;
  background: #fff;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.type-pill.small {
  padding: 6px 12px;
  font-size: 13px;
}

.type-pill:hover {
  border-color: #10b981;
}

.type-pill.active {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

/* ── Inline form ── */
.inline-form {
  animation: fadeInUp 0.25s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── BP inputs ── */
.bp-inputs {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.bp-half {
  flex: 1;
  text-align: center;
}

.bp-label {
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

.bp-input {
  width: 100%;
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px 8px;
  outline: none;
  transition: border-color 0.2s;
  color: #1f2937;
  background: #fff;
}

.bp-input:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.1);
}

/* Chrome, Safari, Edge, Opera */
.bp-input::-webkit-outer-spin-button,
.bp-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.bp-input[type=number] {
  -moz-appearance: textfield;
}

.bp-unit {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 4px;
}

/* ── Mood row ── */
.mood-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  justify-content: space-between;
}

.mood-chip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 4px;
  border-radius: 12px;
  border: 2px solid transparent;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s;
}

.mood-chip:hover {
  background: #f3f4f6;
}

.mood-chip.active {
  background: #f0fdf4;
  border-color: #10b981;
}

.mood-emoji {
  font-size: 24px;
}

.mood-text {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
}

/* ── Textarea ── */
.hub-textarea {
  width: 100%;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

.hub-textarea:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16,185,129,0.1);
}

.hub-textarea::placeholder {
  color: #d1d5db;
}

/* ── Submit button ── */
.hub-submit-btn {
  width: 100%;
  margin-top: 16px;
  padding: 14px;
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  cursor: pointer;
  transition: all 0.2s;
}

.hub-submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16,185,129,0.3);
}

.hub-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hub-submit-btn.secondary {
  background: #f3f4f6;
  color: #4b5563;
}

.hub-submit-btn.secondary:hover:not(:disabled) {
  background: #e5e7eb;
  box-shadow: none;
}

/* ── Photo capture ── */
.photo-capture-area {
  text-align: center;
  padding: 48px 20px;
  border: 2px dashed #d1d5db;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
}

.photo-capture-area:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.capture-icon {
  font-size: 56px;
  margin-bottom: 12px;
}

.capture-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.capture-hint {
  font-size: 13px;
  color: #9ca3af;
}

/* Photo preview + loading */
.photo-preview {
  text-align: center;
}

.preview-img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 16px;
  margin-bottom: 16px;
}

.photo-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 15px;
  font-weight: 500;
  color: #4b5563;
}

/* Photo result */
.photo-result {
  animation: fadeInUp 0.3s ease;
}

.result-img {
  width: 100%;
  max-height: 160px;
  object-fit: cover;
  border-radius: 14px;
  margin-bottom: 12px;
}

.result-card {
  background: #f9fafb;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 12px;
}

.result-name {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
}

.result-nutrients {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.nutrient-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: #fff;
  border-radius: 10px;
}

.nutrient-label {
  font-size: 13px;
  color: #6b7280;
}

.nutrient-value {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.result-advice {
  font-size: 13px;
  color: #059669;
  padding: 10px 12px;
  background: #ecfdf5;
  border-radius: 10px;
  line-height: 1.5;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.result-actions .hub-submit-btn {
  flex: 1;
}

/* Photo error */
.photo-error {
  text-align: center;
  padding: 32px;
}

.error-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.error-text {
  font-size: 14px;
  color: #dc2626;
  margin-bottom: 16px;
}

/* ── Voice input ── */
.voice-unsupported {
  text-align: center;
  padding: 48px 20px;
}

.unsupported-icon {
  font-size: 56px;
  margin-bottom: 12px;
  opacity: 0.4;
}

.unsupported-text {
  font-size: 16px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 4px;
}

.unsupported-hint {
  font-size: 13px;
  color: #9ca3af;
}

.voice-area {
  text-align: center;
}

.mic-button {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.mic-button:hover {
  background: #e5e7eb;
}

.mic-button.recording {
  background: #fee2e2;
}

.mic-icon {
  font-size: 36px;
}

.mic-pulse {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 3px solid #ef4444;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

.mic-hint {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
}

.voice-category {
  margin-top: 12px;
  text-align: left;
}

.category-label {
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 8px;
}

/* Voice mode tag (server ASR indicator) */
.voice-mode-tag {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 12px;
  background: #dbeafe;
  color: #2563eb;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 14px;
}

/* Transcribing indicator */
.transcribing-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  font-size: 14px;
  color: #4b5563;
  margin-bottom: 8px;
}
</style>
