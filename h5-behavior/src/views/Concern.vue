<template>
  <div class="screen">
    <div class="land-bg" style="opacity:.4">
      <div class="orb" :style="{ background: accent, width: '220px', height: '220px', top: '-60px', right: '-60px', opacity: '.12', position:'absolute', borderRadius:'50%', filter:'blur(60px)' }" />
    </div>
    <div class="concern-wrap">
      <div class="concern-back" @click="$router.back()">← 返回</div>

      <div class="concern-head fu">
        <div class="concern-icon">{{ doorData.icon }}</div>
        <div class="concern-title">在继续之前，<br />先听听你内心的声音</div>
        <div class="concern-sub">写下来，或者按住麦克风说出来。至少填一项。</div>
      </div>

      <div class="concern-fields">
        <div v-for="(q, i) in QUESTIONS" :key="q.key"
          :class="['concern-field', 'fu', `d${i + 1}`]">
          <div class="field-label">
            <span class="field-emoji">{{ q.emoji }}</span>
            <span class="field-prompt">{{ q.prompt }}</span>
            <button class="voice-btn"
              :class="{ recording: recording === q.key }"
              @pointerdown.prevent="startVoice(q.key)"
              @pointerup.prevent="stopVoice(q.key)"
              @pointerleave="cancelVoice(q.key)"
              :title="recording === q.key ? '松开结束' : '按住说话'">
              <span class="voice-icon">{{ recording === q.key ? '...' : '🎤' }}</span>
              <span v-if="recording === q.key" class="voice-pulse" />
            </button>
          </div>
          <textarea
            v-model="store.concerns[q.key]"
            :placeholder="q.placeholder"
            class="field-input"
            :style="focused === q.key ? { borderColor: accent, boxShadow: `0 0 0 3px ${accent}18` } : {}"
            rows="2"
            maxlength="200"
            @focus="focused = q.key"
            @blur="focused = ''"
          />
          <!-- emotion tag from voice -->
          <div v-if="emotions[q.key]" class="emotion-tag"
            :style="{ background: emotionColor(emotions[q.key]) + '12', color: emotionColor(emotions[q.key]) }">
            {{ emotionLabel(emotions[q.key]) }}
          </div>
          <div class="field-hints">
            <span v-for="h in q.hints" :key="h" class="hint-tag"
              @click="appendHint(q.key, h)">{{ h }}</span>
          </div>
        </div>
      </div>

      <div class="concern-count fu d5">
        已填 {{ filledCount }} / 4 项
      </div>

      <button class="btn-main fu d5" :disabled="filledCount === 0"
        :style="filledCount > 0
          ? { background: `linear-gradient(135deg, ${accent}, ${accent}cc)`, color: '#fff', width: '100%', boxShadow: `0 6px 20px ${accent}40` }
          : { width: '100%' }"
        @click="$router.push('/scene')">
        {{ filledCount > 0 ? '继续 →' : '请至少填写一项' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAssessmentStore } from '@/stores/assessment'
import { DOORS } from '@/data/doors'
import http from '@/api/request'

const store = useAssessmentStore()
const doorData = computed(() => DOORS.find(d => d.key === store.door) || DOORS[0])
const accent = computed(() => doorData.value.color)
const focused = ref('')
const recording = ref<string | null>(null)

// Per-field emotion detected from voice
const emotions = reactive<Record<string, string>>({})

const QUESTIONS = [
  {
    key: 'worry' as const,
    emoji: '😟',
    prompt: '我最担心的……',
    placeholder: '写下让你焦虑或害怕的事',
    hints: ['健康恶化', '家人', '失控', '未来'],
  },
  {
    key: 'confusion' as const,
    emoji: '🤔',
    prompt: '我最困惑的……',
    placeholder: '写下让你想不明白的事',
    hints: ['为什么反复', '找不到方法', '不知从何开始', '矛盾'],
  },
  {
    key: 'desire' as const,
    emoji: '✨',
    prompt: '我最渴望的……',
    placeholder: '写下你最想要的改变',
    hints: ['精力充沛', '体重正常', '睡个好觉', '心态平和'],
  },
  {
    key: 'aversion' as const,
    emoji: '😤',
    prompt: '我最厌恶的……',
    placeholder: '写下你最不想再经历的事',
    hints: ['反弹', '被说教', '吃药', '失眠'],
  },
]

const filledCount = computed(() =>
  Object.values(store.concerns).filter(v => v.trim().length > 0).length
)

function appendHint(key: string, hint: string) {
  const k = key as keyof typeof store.concerns
  const cur = store.concerns[k] || ''
  if (!cur.includes(hint)) {
    store.concerns[k] = cur ? cur + '、' + hint : hint
  }
}

// --- Voice recording via MediaRecorder ---
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let recordStream: MediaStream | null = null

async function startVoice(key: string) {
  try {
    recordStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(recordStream, { mimeType: getSupportedMime() })
    audioChunks = []
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = () => handleRecordingDone(key)
    mediaRecorder.start()
    recording.value = key
  } catch {
    // Mic permission denied — fallback silently
    recording.value = null
  }
}

function stopVoice(key: string) {
  if (recording.value === key && mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
}

function cancelVoice(key: string) {
  if (recording.value === key && mediaRecorder?.state === 'recording') {
    mediaRecorder.stop()
  }
}

function getSupportedMime(): string {
  const types = ['audio/webm', 'audio/mp4', 'audio/ogg']
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) return t
  }
  return 'audio/webm'
}

async function handleRecordingDone(key: string) {
  recording.value = null
  // Release mic
  recordStream?.getTracks().forEach(t => t.stop())
  recordStream = null

  if (audioChunks.length === 0) return
  const blob = new Blob(audioChunks, { type: getSupportedMime() })
  if (blob.size < 1000) return // too short, ignore

  // Send to ASR
  const formData = new FormData()
  formData.append('file', blob, `concern_${key}.webm`)

  try {
    const res = await http.post('/v1/audio/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })
    const text = res.data?.text || ''
    if (text) {
      const k = key as keyof typeof store.concerns
      const cur = store.concerns[k]
      store.concerns[k] = cur ? cur + text : text
    }
    // If backend returns emotion, capture it
    if (res.data?.emotion) {
      emotions[key] = res.data.emotion
    }
  } catch {
    // ASR not available — try browser SpeechRecognition fallback
    fallbackSpeechRecognition(key)
  }

  // Store audio blob for later upload with assessment
  store.voiceBlobs[key] = blob
}

// Browser SpeechRecognition fallback (no emotion detection)
function fallbackSpeechRecognition(_key: string) {
  // Already recorded, blob is saved. Text won't be auto-filled
  // but the audio is preserved for backend processing
}

// Emotion display helpers
function emotionLabel(emo: string): string {
  const map: Record<string, string> = {
    anxious: '焦虑', sad: '低落', angry: '愤怒', hopeful: '期待',
    frustrated: '挫败', calm: '平静', fearful: '恐惧', neutral: '平静',
  }
  return map[emo] || emo
}

function emotionColor(emo: string): string {
  const map: Record<string, string> = {
    anxious: '#F5A623', sad: '#4C6EF5', angry: '#F56565', hopeful: '#00B8A0',
    frustrated: '#F56565', calm: '#06D6A0', fearful: '#F5A623', neutral: '#94A8B0',
  }
  return map[emo] || '#94A8B0'
}
</script>

<style scoped>
.concern-wrap {
  flex: 1; padding: 24px 22px 40px; display: flex; flex-direction: column;
  position: relative; z-index: 2;
}
.concern-back {
  font-size: 13px; color: var(--sub); cursor: pointer; margin-bottom: 16px; padding: 6px 0;
}
.concern-head { text-align: center; margin-bottom: 24px; }
.concern-icon { font-size: 40px; margin-bottom: 8px; }
.concern-title {
  font-family: 'ZCOOL XiaoWei', serif; font-size: 22px; color: var(--ink);
  line-height: 1.4; margin-bottom: 6px;
}
.concern-sub { font-size: 12px; color: var(--muted); line-height: 1.5; }

.concern-fields { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }

.concern-field {
  background: var(--card); border-radius: 18px; padding: 16px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}
.field-label {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
}
.field-emoji { font-size: 20px; }
.field-prompt {
  font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 600; color: var(--ink);
  flex: 1;
}

/* Voice button */
.voice-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none;
  background: var(--bg-m); cursor: pointer; position: relative;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s; flex-shrink: 0;
}
.voice-btn:active, .voice-btn.recording {
  background: rgba(245,101,101,.12);
}
.voice-btn.recording {
  box-shadow: 0 0 0 4px rgba(245,101,101,.15);
}
.voice-icon { font-size: 16px; z-index: 1; }
.voice-pulse {
  position: absolute; inset: -4px; border-radius: 50%;
  border: 2px solid var(--rose);
  animation: voicePulse 1s ease infinite;
}
@keyframes voicePulse {
  0% { transform: scale(1); opacity: .6; }
  100% { transform: scale(1.5); opacity: 0; }
}

.field-input {
  width: 100%; border: 1.5px solid var(--border); border-radius: 12px;
  padding: 12px 14px; font-size: 14px; color: var(--ink); line-height: 1.6;
  background: var(--bg); resize: none; outline: none;
  font-family: 'Noto Sans SC', sans-serif; transition: all .2s;
}
.field-input::placeholder { color: var(--muted); font-size: 13px; }
.field-input:focus { background: #fff; }

/* Emotion tag */
.emotion-tag {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 8px; margin-top: 6px;
}

.field-hints {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
}
.hint-tag {
  font-size: 11px; color: var(--sub); padding: 4px 10px;
  border-radius: 10px; background: var(--bg-m); cursor: pointer;
  transition: all .2s; border: 1px solid transparent;
}
.hint-tag:active { transform: scale(.95); border-color: var(--border-m); }

.concern-count {
  text-align: center; font-size: 12px; color: var(--muted);
  margin-bottom: 12px;
}
</style>
