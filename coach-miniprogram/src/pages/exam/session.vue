<template>
  <view class="es-page">
    <!-- 顶部进度 -->
    <view class="es-header">
      <view class="es-header-left" @tap="confirmExit">
        <text class="es-exit-icon">✕</text>
      </view>
      <view class="es-progress-info">
        <text class="es-progress-text">{{ currentIndex + 1 }} / {{ questions.length }}</text>
      </view>
      <view class="es-timer">
        <text>⏱ {{ formatTime(timeLeft) }}</text>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="es-progress-bar">
      <view class="es-progress-fill" :style="{ width: progressPct + '%' }" />
    </view>

    <!-- 题目 -->
    <scroll-view v-if="currentQ" scroll-y class="es-body">
      <view class="es-question-card">
        <view class="es-q-type">{{ typeLabel(currentQ.question_type) }}</view>
        <text class="es-q-text">{{ currentQ.question_text }}</text>
      </view>

      <!-- 选项 -->
      <view class="es-options">
        <view v-for="opt in parsedOptions" :key="opt.key"
          class="es-option" :class="{ 'es-option--selected': isSelected(opt.key) }"
          @tap="selectOption(opt.key)">
          <view class="es-option-key">{{ opt.key }}</view>
          <text class="es-option-text">{{ opt.text }}</text>
        </view>
      </view>

      <view style="height:160rpx;"></view>
    </scroll-view>

    <!-- 空状态 -->
    <view v-else-if="!loading" class="es-empty">
      <text class="es-empty-icon">📝</text>
      <text class="es-empty-text">题目加载失败</text>
    </view>

    <!-- 底部操作 -->
    <view class="es-footer">
      <view class="es-btn es-btn--prev" :class="{ 'es-btn--disabled': currentIndex === 0 }" @tap="prevQ">
        <text>上一题</text>
      </view>
      <view v-if="currentIndex < questions.length - 1" class="es-btn es-btn--next" @tap="nextQ">
        <text>下一题</text>
      </view>
      <view v-else class="es-btn es-btn--submit" @tap="submitExam">
        <text>提交答案</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const BASE_URL = 'http://localhost:8000'
function getToken() { return uni.getStorageSync('access_token') || '' }

async function http<T = any>(url: string, opts: any = {}): Promise<T> {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url, method: opts.method || 'GET', data: opts.data,
      header: { 'Authorization': 'Bearer ' + getToken(), 'Content-Type': 'application/json' },
      success: (res: any) => {
        if (res.statusCode === 401) { uni.removeStorageSync('access_token'); uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('401')); return }
        res.statusCode < 300 ? resolve(res.data as T) : reject(new Error(`${res.statusCode}`))
      },
      fail: (e: any) => reject(e),
    })
  })
}

const questions = ref<any[]>([])
const answers = ref<Record<number, string>>({})
const currentIndex = ref(0)
const loading = ref(false)
const timeLeft = ref(1800) // 30 min default
let sessionId = 0, examId = 0, timer: any = null

const currentQ = computed(() => questions.value[currentIndex.value] || null)
const progressPct = computed(() => questions.value.length > 0 ? Math.round((currentIndex.value + 1) / questions.value.length * 100) : 0)

const parsedOptions = computed(() => {
  if (!currentQ.value?.options) return []
  const opts = typeof currentQ.value.options === 'string' ? JSON.parse(currentQ.value.options) : currentQ.value.options
  return (Array.isArray(opts) ? opts : []).map((o: string) => {
    const m = o.match(/^([A-D])[.、]\s*(.+)$/)
    return m ? { key: m[1], text: m[2] } : { key: o[0], text: o.slice(2).trim() }
  })
})

function typeLabel(t: string) { return { single: '单选题', multiple: '多选题', truefalse: '判断题' }[t] || '单选题' }
function isSelected(key: string) { return (answers.value[currentQ.value?.id] || '').includes(key) }

function selectOption(key: string) {
  if (!currentQ.value) return
  const id = currentQ.value.id
  const t = currentQ.value.question_type
  if (t === 'multiple') {
    const cur = answers.value[id] || ''
    answers.value[id] = cur.includes(key) ? cur.replace(key, '') : (cur + key)
  } else {
    answers.value[id] = key
  }
}

function prevQ() { if (currentIndex.value > 0) currentIndex.value-- }
function nextQ() { if (currentIndex.value < questions.value.length - 1) currentIndex.value++ }

async function submitExam() {
  uni.showModal({
    title: '确认提交',
    content: `已答 ${Object.keys(answers.value).length}/${questions.value.length} 题，确认提交吗？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        // Submit answers
        await Promise.allSettled(
          Object.entries(answers.value).map(([qId, ans]) =>
            http(`/api/v1/certification/sessions/${sessionId}/answer`, {
              method: 'POST', data: { question_id: Number(qId), answer: ans }
            })
          )
        )
        const fin = await http<any>(`/api/v1/certification/sessions/${sessionId}/finish`, { method: 'POST' })
        clearInterval(timer)
        uni.redirectTo({ url: '/pages/exam/result?session_id=' + sessionId })
      } catch {
        uni.showToast({ title: '提交失败，请重试', icon: 'none' })
      }
    }
  })
}

function confirmExit() {
  uni.showModal({
    title: '确认退出考试',
    content: '退出后本次答题进度将丢失',
    success: (res) => {
      if (res.confirm) { clearInterval(timer); uni.navigateBack() }
    }
  })
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60), sec = s % 60
  return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  sessionId = Number(page?.options?.session_id || 0)
  examId = Number(page?.options?.exam_id || 0)

  if (!sessionId) { uni.showToast({ title: '无效的考试会话', icon: 'none' }); uni.navigateBack(); return }

  loading.value = true
  try {
    const data = await http<any>(`/api/v1/certification/sessions/${sessionId}`)
    questions.value = data?.questions || []
    timeLeft.value = (data?.duration_minutes || 30) * 60
  } catch { questions.value = [] } finally { loading.value = false }

  // countdown timer
  timer = setInterval(() => {
    if (timeLeft.value > 0) timeLeft.value--
    else { clearInterval(timer); submitExam() }
  }, 1000)
})

onUnmounted(() => { clearInterval(timer) })
</script>

<style scoped>
.es-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }

.es-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 24rpx; padding-top: calc(16rpx + env(safe-area-inset-top));
  background: #fff; border-bottom: 1rpx solid #F0F0F0;
}
.es-exit-icon { font-size: 32rpx; color: #8E99A4; padding: 8rpx; }
.es-progress-text { font-size: 26rpx; font-weight: 600; color: #2C3E50; }
.es-timer { font-size: 24rpx; color: #5B6B7F; }

.es-progress-bar { height: 6rpx; background: #F0F0F0; }
.es-progress-fill { height: 100%; background: #2D8E69; transition: width 0.3s; }

.es-body { flex: 1; height: calc(100vh - 240rpx); }

.es-question-card { background: #fff; margin: 24rpx; padding: 28rpx; border-radius: 16rpx; }
.es-q-type { font-size: 20rpx; color: #2D8E69; background: #E8F8F0; display: inline-block; padding: 4rpx 12rpx; border-radius: 8rpx; margin-bottom: 16rpx; }
.es-q-text { display: block; font-size: 30rpx; color: #2C3E50; line-height: 1.6; font-weight: 600; }

.es-options { padding: 0 24rpx; }
.es-option { display: flex; align-items: flex-start; gap: 16rpx; background: #fff; border-radius: 16rpx; padding: 20rpx 24rpx; margin-bottom: 12rpx; border: 2rpx solid transparent; }
.es-option--selected { border-color: #2D8E69; background: #EAFAF2; }
.es-option-key { width: 44rpx; height: 44rpx; border-radius: 50%; background: #F0F0F0; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 700; color: #5B6B7F; flex-shrink: 0; }
.es-option--selected .es-option-key { background: #2D8E69; color: #fff; }
.es-option-text { flex: 1; font-size: 27rpx; color: #2C3E50; line-height: 1.5; }

.es-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16rpx; }
.es-empty-icon { font-size: 64rpx; }
.es-empty-text { font-size: 26rpx; color: #8E99A4; }

.es-footer {
  display: flex; gap: 12rpx; padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #fff; border-top: 1rpx solid #F0F0F0;
}
.es-btn { flex: 1; padding: 20rpx; border-radius: 16rpx; text-align: center; font-size: 28rpx; font-weight: 600; }
.es-btn--prev { background: #F5F6FA; color: #5B6B7F; border: 1rpx solid #E0E0E0; }
.es-btn--disabled { opacity: 0.4; }
.es-btn--next { background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); color: #fff; }
.es-btn--submit { background: linear-gradient(135deg, #E67E22 0%, #E74C3C 100%); color: #fff; }
</style>
