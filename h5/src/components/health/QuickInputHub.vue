<template>
  <van-popup
    :show="show"
    position="bottom"
    round
    closeable
    :style="{ height: '75vh' }"
    @click-close-icon="close"
    @click-overlay="close"
  >
    <div class="hub-container">
      <div class="hub-title">快速采集中心</div>

      <!-- Mode selector -->
      <div class="hub-modes">
        <div
          v-for="m in modes"
          :key="m.key"
          class="mode-card"
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

        <!-- Inline forms -->
        <div v-if="recordType" class="inline-form">
          <!-- Glucose -->
          <div v-if="recordType === 'glucose'">
            <div class="pill-scroll sub">
              <div
                v-for="opt in glucoseTimeOptions"
                :key="opt.value"
                class="type-pill small"
                :class="{ active: form.glucoseTime === opt.value }"
                @click="form.glucoseTime = opt.value"
              >
                {{ opt.label }}
              </div>
            </div>
            <div class="big-input-wrap">
              <input
                v-model="form.glucoseValue"
                type="number"
                inputmode="decimal"
                placeholder="6.0"
                class="big-input"
              />
              <span class="big-unit">mmol/L</span>
            </div>
            <div class="quick-vals">
              <span v-for="v in [5.0,5.5,6.0,6.5,7.0]" :key="v" class="qv" @click="form.glucoseValue = v">{{ v }}</span>
            </div>
          </div>

          <!-- Weight -->
          <div v-if="recordType === 'weight'">
            <div class="big-input-wrap">
              <input v-model="form.weightValue" type="number" inputmode="decimal" placeholder="65" class="big-input" />
              <span class="big-unit">kg</span>
            </div>
            <div class="quick-vals">
              <span v-for="v in [55,60,65,70,75,80]" :key="v" class="qv" @click="form.weightValue = v">{{ v }}</span>
            </div>
          </div>

          <!-- Blood Pressure -->
          <div v-if="recordType === 'bloodPressure'" class="bp-row">
            <div class="bp-half">
              <div class="bp-label">收缩压</div>
              <input v-model="form.systolic" type="number" inputmode="numeric" placeholder="120" class="bp-input" />
              <div class="bp-unit">mmHg</div>
            </div>
            <div class="bp-half">
              <div class="bp-label">舒张压</div>
              <input v-model="form.diastolic" type="number" inputmode="numeric" placeholder="80" class="bp-input" />
              <div class="bp-unit">mmHg</div>
            </div>
          </div>

          <!-- Exercise -->
          <div v-if="recordType === 'exercise'">
            <div class="pill-scroll sub">
              <div
                v-for="opt in exerciseTypes"
                :key="opt.value"
                class="type-pill small"
                :class="{ active: form.exerciseType === opt.value }"
                @click="form.exerciseType = opt.value"
              >
                {{ opt.icon }} {{ opt.label }}
              </div>
            </div>
            <div class="big-input-wrap">
              <input v-model="form.exerciseDuration" type="number" inputmode="numeric" placeholder="30" class="big-input" />
              <span class="big-unit">分钟</span>
            </div>
            <div class="quick-vals">
              <span v-for="v in [15,30,45,60,90]" :key="v" class="qv" @click="form.exerciseDuration = v">{{ v }}</span>
            </div>
          </div>

          <!-- Mood -->
          <div v-if="recordType === 'mood'">
            <div class="mood-row">
              <div
                v-for="m in moodOptions"
                :key="m.value"
                class="mood-chip"
                :class="{ active: form.moodLevel === m.value }"
                @click="form.moodLevel = m.value"
              >
                <span class="mood-emoji">{{ m.emoji }}</span>
                <span class="mood-text">{{ m.label }}</span>
              </div>
            </div>
            <textarea v-model="form.moodNote" placeholder="补充说明（选填）..." class="hub-textarea" rows="3" maxlength="200" />
          </div>

          <!-- Meal -->
          <div v-if="recordType === 'meal'">
            <textarea v-model="form.mealDescription" placeholder="描述今天的饮食..." class="hub-textarea" rows="4" maxlength="300" />
          </div>

          <van-button type="success" block round :loading="submitting" :disabled="!isValid" @click="submitRecord">
            提交
          </van-button>
        </div>
      </div>

      <!-- ==================== Mode 2: Photo ==================== -->
      <div v-if="activeMode === 'photo'" class="hub-panel">
        <div v-if="!photoPreview && !photoResult" class="photo-area" @click="$refs.photoInput.click()">
          <div class="photo-icon">📷</div>
          <div class="photo-text">点击拍照或选择图片</div>
          <div class="photo-hint">AI 将自动识别食物并分析营养成分</div>
        </div>

        <input ref="photoInput" type="file" accept="image/*" capture="environment" style="display:none" @change="onPhoto" />

        <div v-if="photoPreview && !photoResult && !photoError" class="photo-preview">
          <img :src="photoPreview" class="preview-img" />
          <div class="loading-row">
            <van-loading type="spinner" color="#10b981" />
            <span>食物识别中...</span>
          </div>
        </div>

        <div v-if="photoResult" class="photo-result">
          <img :src="photoPreview" class="preview-img small" />
          <div class="result-card">
            <div class="result-name">{{ photoResult.food_name || '食物' }}</div>
            <div class="result-grid">
              <div class="rg-item"><span class="rg-label">热量</span><span class="rg-val">{{ photoResult.calories || '--' }} kcal</span></div>
              <div class="rg-item"><span class="rg-label">蛋白质</span><span class="rg-val">{{ photoResult.protein || '--' }} g</span></div>
              <div class="rg-item"><span class="rg-label">脂肪</span><span class="rg-val">{{ photoResult.fat || '--' }} g</span></div>
              <div class="rg-item"><span class="rg-label">碳水</span><span class="rg-val">{{ photoResult.carbs || '--' }} g</span></div>
            </div>
            <div v-if="photoResult.advice" class="result-advice">💡 {{ photoResult.advice }}</div>
          </div>
          <div class="btn-row">
            <van-button plain round size="small" @click="resetPhoto">重新拍照</van-button>
            <van-button type="success" round size="small" @click="close">完成</van-button>
          </div>
        </div>

        <div v-if="photoError" class="photo-error-box">
          <div>⚠️ {{ photoError }}</div>
          <van-button plain round size="small" @click="resetPhoto">重试</van-button>
        </div>
      </div>

      <!-- ==================== Mode 3: Voice ==================== -->
      <div v-if="activeMode === 'voice'" class="hub-panel">
        <!-- No mic access at all -->
        <div v-if="!speechSupported && !mediaRecorderSupported" class="unsupported">
          <div class="unsup-icon">🎤</div>
          <div>当前浏览器不支持语音输入</div>
          <div class="unsup-hint">请使用 Chrome 浏览器或升级到最新版</div>
        </div>

        <div v-else class="voice-area">
          <!-- Mode indicator -->
          <div v-if="!speechSupported" class="voice-mode-tag">服务端语音识别</div>

          <div class="mic-btn" :class="{ recording: isRecording }" @click="toggleRecording">
            <span class="mic-emoji">🎤</span>
            <div v-if="isRecording" class="mic-pulse"></div>
          </div>
          <div class="mic-hint">
            {{ transcribing ? '语音转写中...' : isRecording ? '正在录音...' : '点击开始说话' }}
          </div>

          <!-- Transcribing spinner -->
          <div v-if="transcribing" class="loading-row" style="margin-bottom:12px">
            <van-loading type="spinner" color="#10b981" size="20" />
            <span>识别中，请稍候...</span>
          </div>

          <textarea v-model="voiceText" placeholder="语音识别结果将显示在这里..." class="hub-textarea" rows="4" />

          <div class="pill-scroll sub">
            <div
              v-for="c in voiceCategories"
              :key="c.value"
              class="type-pill small"
              :class="{ active: voiceCategory === c.value }"
              @click="voiceCategory = c.value"
            >
              {{ c.icon }} {{ c.label }}
            </div>
          </div>

          <van-button type="success" block round :loading="submitting" :disabled="!voiceText.trim() || transcribing" @click="submitVoice">
            提交
          </van-button>
        </div>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { healthApi } from '@/api/health'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'submitted'): void
}>()

const router = useRouter()

const close = () => emit('update:show', false)

// ── Modes ──
const modes = [
  { key: 'record', icon: '📝', label: '快速记录', desc: '血糖/体重/血压' },
  { key: 'photo', icon: '📷', label: '拍一拍', desc: '食物识别' },
  { key: 'voice', icon: '🎤', label: '说一说', desc: '语音记录' },
  { key: 'ai', icon: '💬', label: '问AI', desc: 'AI健康助手' },
]
const activeMode = ref('record')

const selectMode = (key: string) => {
  if (key === 'ai') {
    close()
    router.push('/chat')
    return
  }
  activeMode.value = key
}

watch(() => props.show, (v) => {
  if (!v) resetAll()
})

const resetAll = () => {
  activeMode.value = 'record'
  recordType.value = ''
  submitting.value = false
  transcribing.value = false
  resetPhoto()
  voiceText.value = ''
  stopRecording()
}

// ══════════════════════════════════════
// Mode 1: Quick Record
// ══════════════════════════════════════
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
const exerciseTypes = [
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

const form = ref({
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

const isValid = computed(() => {
  switch (recordType.value) {
    case 'glucose': return !!form.value.glucoseValue && parseFloat(String(form.value.glucoseValue)) > 0
    case 'weight': return !!form.value.weightValue && parseFloat(String(form.value.weightValue)) > 0
    case 'bloodPressure': return !!form.value.systolic && !!form.value.diastolic
    case 'exercise': return !!form.value.exerciseDuration && parseInt(String(form.value.exerciseDuration)) > 0
    case 'mood': return !!form.value.moodLevel
    case 'meal': return !!form.value.mealDescription
    default: return false
  }
})

const submitRecord = async () => {
  submitting.value = true
  try {
    const ts = new Date().toISOString()
    switch (recordType.value) {
      case 'glucose':
        await healthApi.recordGlucose({ value: parseFloat(String(form.value.glucoseValue)), measurement_time: ts, meal_tag: form.value.glucoseTime })
        break
      case 'weight':
        await healthApi.recordWeight({ value: parseFloat(String(form.value.weightValue)), measurement_time: ts })
        break
      case 'bloodPressure':
        await healthApi.recordBloodPressure({ systolic: parseInt(form.value.systolic), diastolic: parseInt(form.value.diastolic), measurement_time: ts })
        break
      case 'exercise':
        await healthApi.recordExercise({ type: form.value.exerciseType, duration: parseInt(String(form.value.exerciseDuration)), note: `${form.value.exerciseType} ${form.value.exerciseDuration}分钟` })
        break
      case 'mood':
        await healthApi.recordMood({ score: form.value.moodLevel, note: form.value.moodNote })
        break
      case 'meal':
        await healthApi.recordMeal({ description: form.value.mealDescription, note: form.value.mealDescription })
        break
    }
    showToast({ message: '记录成功', type: 'success' })
    emit('submitted')
    close()
  } catch (e: any) {
    showToast({ message: e?.response?.data?.detail || '提交失败', type: 'fail' })
  } finally {
    submitting.value = false
  }
}

// ══════════════════════════════════════
// Mode 2: Photo
// ══════════════════════════════════════
const photoPreview = ref('')
const photoResult = ref<any>(null)
const photoError = ref('')

const onPhoto = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  photoPreview.value = URL.createObjectURL(file)
  photoError.value = ''
  photoResult.value = null
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
}

// ══════════════════════════════════════
// Mode 3: Voice (Web Speech API primary + MediaRecorder→server ASR fallback)
// ══════════════════════════════════════
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
    let t = ''
    for (let i = 0; i < event.results.length; i++) t += event.results[i][0].transcript
    voiceText.value = t
  }
  recognition.onerror = () => { isRecording.value = false }
  recognition.onend = () => { isRecording.value = false }
  recognition.start()
  isRecording.value = true
}

// ── MediaRecorder → server ASR (fallback) ──
const startMediaRecorder = async () => {
  if (!mediaRecorderSupported) return
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType: getSupportedMimeType() })
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = async () => {
      // Release mic
      mediaStream?.getTracks().forEach(t => t.stop())
      mediaStream = null
      if (audioChunks.length === 0) return
      // Send to server ASR
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
        else showToast({ message: '未识别到语音内容', type: 'fail' })
      } catch (e: any) {
        showToast({ message: e?.response?.data?.detail || '语音识别失败', type: 'fail' })
      } finally {
        transcribing.value = false
      }
    }
    mediaRecorder.start()
    isRecording.value = true
  } catch (e) {
    showToast({ message: '无法访问麦克风，请检查权限', type: 'fail' })
  }
}

const getSupportedMimeType = (): string => {
  const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  for (const t of types) { if (MediaRecorder.isTypeSupported(t)) return t }
  return 'audio/webm'
}

const stopRecording = () => {
  // Web Speech
  if (recognition) { try { recognition.stop() } catch {} recognition = null }
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
      await healthApi.recordMeal({ description: voiceText.value.trim(), note: voiceText.value.trim() })
    } else {
      await healthApi.recordMood({ score: 3, note: voiceText.value.trim() })
    }
    showToast({ message: '记录成功', type: 'success' })
    emit('submitted')
    close()
  } catch (e: any) {
    showToast({ message: e?.response?.data?.detail || '提交失败', type: 'fail' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.hub-container {
  padding: 16px 16px 32px;
  overflow-y: auto;
  max-height: calc(75vh - 16px);
}

.hub-title {
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 16px;
  color: #1f2937;
}

/* ── Mode selector ── */
.hub-modes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.mode-card {
  text-align: center;
  padding: 12px 4px 8px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
  transition: all 0.2s;
}

.mode-card.active {
  border-color: #10b981;
  background: #ecfdf5;
}

.mode-icon { font-size: 24px; }
.mode-label { font-size: 13px; font-weight: 600; color: #1f2937; margin-top: 2px; }
.mode-desc { font-size: 10px; color: #9ca3af; }

/* ── Hub panel ── */
.hub-panel { padding: 4px 0; }

/* ── Pill scroll ── */
.pill-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 12px;
  -webkit-overflow-scrolling: touch;
}
.pill-scroll::-webkit-scrollbar { display: none; }
.pill-scroll.sub { margin-bottom: 12px; }

.type-pill {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: 20px;
  border: 2px solid #e5e7eb;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  white-space: nowrap;
  transition: all 0.15s;
}
.type-pill.small { padding: 6px 10px; font-size: 12px; }
.type-pill.active { background: #10b981; border-color: #10b981; color: #fff; }

/* ── Inline form ── */
.inline-form { animation: fadeUp 0.2s ease; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* ── Big number input ── */
.big-input-wrap {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
}
.big-input {
  width: 140px;
  font-size: 40px;
  font-weight: 700;
  text-align: center;
  border: none;
  border-bottom: 3px solid #10b981;
  outline: none;
  background: transparent;
  color: #1f2937;
  padding: 4px 0;
}
.big-input::-webkit-outer-spin-button,
.big-input::-webkit-inner-spin-button { -webkit-appearance: none; }
.big-input[type=number] { -moz-appearance: textfield; }
.big-unit { font-size: 14px; color: #9ca3af; font-weight: 500; }

/* ── Quick values ── */
.quick-vals {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 16px;
}
.qv {
  padding: 4px 12px;
  border-radius: 12px;
  background: #f3f4f6;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

/* ── BP row ── */
.bp-row { display: flex; gap: 12px; margin-bottom: 16px; }
.bp-half { flex: 1; text-align: center; }
.bp-label { font-size: 12px; font-weight: 600; color: #4b5563; margin-bottom: 6px; }
.bp-input {
  width: 100%;
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 4px;
  outline: none;
  color: #1f2937;
  background: #fff;
}
.bp-input:focus { border-color: #10b981; }
.bp-input::-webkit-outer-spin-button,
.bp-input::-webkit-inner-spin-button { -webkit-appearance: none; }
.bp-input[type=number] { -moz-appearance: textfield; }
.bp-unit { font-size: 11px; color: #9ca3af; margin-top: 4px; }

/* ── Mood ── */
.mood-row { display: flex; gap: 6px; margin-bottom: 12px; justify-content: space-between; }
.mood-chip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 2px;
  border-radius: 10px;
  border: 2px solid transparent;
  background: #f9fafb;
  transition: all 0.15s;
}
.mood-chip.active { background: #ecfdf5; border-color: #10b981; }
.mood-emoji { font-size: 22px; }
.mood-text { font-size: 10px; color: #6b7280; }

/* ── Textarea ── */
.hub-textarea {
  width: 100%;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
  resize: none;
  outline: none;
  margin-bottom: 12px;
  font-family: inherit;
}
.hub-textarea:focus { border-color: #10b981; }
.hub-textarea::placeholder { color: #d1d5db; }

/* ── Photo ── */
.photo-area {
  text-align: center;
  padding: 40px 16px;
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  background: #fafafa;
}
.photo-icon { font-size: 48px; margin-bottom: 8px; }
.photo-text { font-size: 15px; font-weight: 600; color: #1f2937; }
.photo-hint { font-size: 12px; color: #9ca3af; margin-top: 4px; }

.photo-preview { text-align: center; }
.preview-img { width: 100%; max-height: 180px; object-fit: cover; border-radius: 12px; margin-bottom: 12px; }
.preview-img.small { max-height: 120px; }
.loading-row { display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; color: #4b5563; }

.photo-result { animation: fadeUp 0.3s ease; }
.result-card { background: #f9fafb; border-radius: 12px; padding: 14px; margin-bottom: 12px; }
.result-name { font-size: 16px; font-weight: 700; color: #1f2937; margin-bottom: 10px; }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
.rg-item { display: flex; justify-content: space-between; padding: 6px 8px; background: #fff; border-radius: 8px; }
.rg-label { font-size: 12px; color: #6b7280; }
.rg-val { font-size: 12px; font-weight: 600; color: #1f2937; }
.result-advice { font-size: 12px; color: #059669; padding: 8px 10px; background: #ecfdf5; border-radius: 8px; line-height: 1.5; }

.btn-row { display: flex; gap: 10px; }
.btn-row .van-button { flex: 1; }

.photo-error-box { text-align: center; padding: 24px; color: #dc2626; font-size: 14px; }

/* ── Voice ── */
.unsupported { text-align: center; padding: 40px 16px; }
.unsup-icon { font-size: 48px; margin-bottom: 8px; opacity: 0.4; }
.unsup-hint { font-size: 12px; color: #9ca3af; margin-top: 4px; }

.voice-area { text-align: center; }
.mic-btn {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  position: relative;
  transition: all 0.2s;
}
.mic-btn.recording { background: #fee2e2; }
.mic-emoji { font-size: 32px; }
.mic-pulse {
  position: absolute;
  width: 100%; height: 100%;
  border-radius: 50%;
  border: 3px solid #ef4444;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}
.mic-hint { font-size: 13px; color: #6b7280; margin-bottom: 12px; }

/* Voice mode tag */
.voice-mode-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  background: #dbeafe;
  color: #2563eb;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 12px;
}
</style>
