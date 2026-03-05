<template>
  <PageShell :show-nav-bar="false" :show-tab-bar="true" no-padding>
    <div class="observer-home">
    <!-- 头部欢迎区 -->
    <div class="hero-section">
      <div class="hero-bg" />
      <div class="hero-content">
        <div class="avatar-ring">
          <van-image
            class="avatar"
            round
            width="56"
            height="56"
            :src="userInfo.avatar || defaultAvatar"
          />
          <div class="ring-badge ring-badge--l0">体验者</div>
        </div>
        <div class="greeting">
          <p class="greeting-sub">你好，开始了解自己</p>
          <h1 class="greeting-main">{{ greetingText }}</h1>
        </div>
      </div>
    </div>

    <!-- 情境式痛点入口（核心转化区）-->
    <div class="context-entry-section">
      <p class="section-hint">最近有没有这些困扰？</p>
      <div class="pain-tags">
        <button
          v-for="pain in painPoints"
          :key="pain.id"
          class="pain-tag"
          :class="{ active: selectedPain === pain.id }"
          @click="selectPain(pain)"
        >
          {{ pain.emoji }} {{ pain.label }}
        </button>
      </div>

      <!-- 主行动按钮 -->
      <div class="cta-block" v-if="selectedPain">
        <div class="cta-context-text">
          <span class="cta-context-emoji">{{ currentPain?.emoji }}</span>
          {{ currentPain?.followup }}
        </div>
        <van-button
          type="primary"
          block
          round
          class="cta-btn"
          @click="startAssessment"
        >
          3分钟了解你现在的行为阶段
          <van-icon name="arrow" />
        </van-button>
        <p class="cta-disclaimer">不打标签 · 只看结构 · 完全保密</p>
      </div>

      <div class="cta-block" v-else>
        <van-button
          type="primary"
          block
          round
          plain
          class="cta-btn cta-btn--default"
          @click="startAssessment"
        >
          开始行为阶段评估
        </van-button>
      </div>
    </div>

    <!-- TrustGuide 对话入口 -->
    <div class="trust-guide-card" @click="openChat">
      <div class="tg-icon">
        <div class="tg-pulse" />
        <van-icon name="chat-o" size="24" color="#4FA8D5" />
      </div>
      <div class="tg-text">
        <p class="tg-title">AI 健康向导</p>
        <p class="tg-desc">{{ chatIntroText }}</p>
      </div>
      <div class="tg-remaining">
        <span class="remaining-num">{{ remainingChats }}</span>
        <span class="remaining-label">次/今日</span>
      </div>
    </div>

    <!-- 今日微任务（仅1条）-->
    <div class="micro-task-card" v-if="todayTask">
      <div class="task-header">
        <span class="task-label">今日微行动</span>
        <van-tag type="success" v-if="todayTask.completed">已完成</van-tag>
      </div>
      <p class="task-content">{{ todayTask.content }}</p>
      <van-button
        v-if="!todayTask.completed"
        size="small"
        type="primary"
        round
        @click="completeTask"
      >
        完成打卡
      </van-button>
    </div>

    <!-- 晋级提示 -->
    <div class="upgrade-hint-card">
      <div class="upgrade-progress">
        <div class="upgrade-progress-fill" :style="{ width: upgradeProgress + '%' }" />
      </div>
      <p class="upgrade-text">
        完成首次行为评估，解锁「成长者」阶段
        <van-icon name="question-o" @click="showUpgradeInfo = true" />
      </p>
      <div class="upgrade-steps">
        <div
          v-for="(step, i) in upgradeSteps"
          :key="i"
          class="upgrade-step"
          :class="{ done: step.done }"
        >
          <van-icon :name="step.done ? 'success' : 'circle'" />
          <span>{{ step.label }}</span>
        </div>
      </div>
    </div>

    <!-- 平台价值底语（语义安全区）-->
    <div class="platform-manifesto">
      <p>我们限制的不是表达，而是伤害</p>
      <p>你的行为可以改变，你的身份不需要被定义</p>
    </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { showToast } from 'vant'
import api from '@/api/index'
import storage from '@/utils/storage'
import PageShell from '@/components/common/PageShell.vue'

const router = useRouter()
const userStore = useUserStore()
const userInfo = computed(() => {
  const authUser = storage.getAuthUser()
  return authUser || { username: userStore.name, avatar: '' }
})

const defaultAvatar = '/images/default-avatar.svg'
const selectedPain = ref<string | null>(null)
const showUpgradeInfo = ref(false)
const trialUsed = parseInt(localStorage.getItem('bhp_trial_chat_count') || '0', 10)
const remainingChats = ref(Math.max(0, 3 - trialUsed))
const upgradeProgress = ref(15)

const painPoints = [
  { id: 'sleep', emoji: '😴', label: '睡不好',
    followup: '睡眠困难往往有结构性原因，我们来找找' },
  { id: 'glucose', emoji: '📊', label: '血糖波动',
    followup: '血糖反复是行为模式问题，可以系统改善' },
  { id: 'weight', emoji: '⚖️', label: '体重控制不住',
    followup: '体重背后是习惯系统，先搞清楚你的阶段' },
  { id: 'procrastination', emoji: '🔁', label: '总是拖延',
    followup: '拖延是信号，不是性格问题，先做个评估' },
  { id: 'mood', emoji: '🌧️', label: '情绪低落',
    followup: '情绪和行为紧密相连，聊聊看？' },
  { id: 'stress', emoji: '😤', label: '压力很大',
    followup: '压力是可以被结构化管理的' },
]

const currentPain = computed(
  () => painPoints.find(p => p.id === selectedPain.value)
)

const greetingText = computed(() => {
  const hour = new Date().getHours()
  if (hour < 10) return '早安，新的开始'
  if (hour < 14) return '今天怎么样？'
  if (hour < 18) return '下午好，休息一下'
  return '晚上好，今日复盘'
})

const chatIntroText = computed(() => {
  if (remainingChats.value === 0) return '今日次数已用完，明日继续'
  return '有什么想聊的？我在'
})

const todayTask = ref<{ content: string; completed: boolean } | null>(null)

const upgradeSteps = ref([
  { label: '完成注册', done: true },
  { label: '首次行为评估', done: false },
  { label: '完成1次AI对话', done: false },
])

const selectPain = (pain: typeof painPoints[0]) => {
  selectedPain.value = selectedPain.value === pain.id ? null : pain.id
}

// 痛点 → h5-behavior 门(door)映射
const painDoorMap: Record<string, string> = {
  sleep: 'symptom', glucose: 'risk', weight: 'symptom',
  procrastination: 'growth', mood: 'growth', stress: 'growth',
}

const startAssessment = () => {
  // h5-behavior: 生产环境同域 /behavior/#/ ，开发期跨端口 3003
  const door = selectedPain.value ? painDoorMap[selectedPain.value] || '' : ''
  const hash = door ? `#/?door=${door}` : '#/'
  if (import.meta.env.PROD) {
    window.location.href = `${window.location.origin}/behavior/${hash}`
  } else {
    window.location.href = `http://localhost:3003/behavior/home/today${hash}`
  }
}

const openChat = () => {
  // 允许匿名用户体验 AI 健康向导（3 次免费体验）
  router.push('/chat')
}

const completeTask = async () => {
  if (!todayTask.value) return
  const token = storage.getToken()
  if (!token) {
    showToast('登录后即可记录打卡')
    setTimeout(() => router.push('/login?redirect=/home/observer'), 1200)
    return
  }
  todayTask.value.completed = true
  showToast({ message: '打卡成功！', type: 'success' })
  try {
    await api.post('/api/v1/observer/quota/consume', { action: 'checkin' })
  } catch { /* 乐观更新已生效，静默失败 */ }
}

onMounted(async () => {
  const token = storage.getToken()
  if (!token) return // 未登录观察员: 使用默认值，不触发 API 调用

  // 加载剩余对话次数（Observer 专属配额接口）
  try {
    const res: any = await api.get('/api/v1/observer/quota/today')
    remainingChats.value = res?.chat_remaining ?? 3
  } catch {}
})
</script>

<style scoped>
.observer-home {
  background: #F7F8FB;
}

/* 头部英雄区 */
.hero-section {
  position: relative;
  padding: 52px 20px 24px;
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #0A2744 0%, #1565C0 60%, #1976D2 100%);
  border-radius: 0 0 32px 32px;
}
.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}
.avatar-ring {
  position: relative;
  flex-shrink: 0;
}
.avatar {
  border: 2px solid rgba(255,255,255,0.4);
  border-radius: 50%;
}
.ring-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  background: #FF9800;
  color: #fff;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
  font-weight: 600;
}
.greeting {
  color: #fff;
}
.greeting-sub {
  font-size: 12px;
  opacity: 0.75;
  margin: 0 0 4px;
}
.greeting-main {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  letter-spacing: -0.3px;
}

/* 情境入口 */
.context-entry-section {
  margin: 20px 16px 0;
  background: #fff;
  border-radius: 20px;
  padding: 20px 16px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}
.section-hint {
  font-size: 15px;
  color: #333;
  font-weight: 600;
  margin: 0 0 14px;
}
.pain-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}
.pain-tag {
  padding: 8px 14px;
  border-radius: 20px;
  border: 1.5px solid #E0E0E0;
  background: #F5F5F5;
  font-size: 13px;
  color: #555;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}
.pain-tag.active {
  border-color: #1565C0;
  background: #E3F0FF;
  color: #1565C0;
  font-weight: 600;
}
.cta-context-text {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.cta-context-emoji {
  font-size: 18px;
}
.cta-btn {
  --van-button-primary-background: #1565C0;
  --van-button-primary-border-color: #1565C0;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
}
.cta-btn--default {
  --van-button-plain-color: #999;
  --van-button-border-color: #ddd;
}
.cta-disclaimer {
  text-align: center;
  font-size: 11px;
  color: #aaa;
  margin: 8px 0 0;
}

/* TrustGuide 卡片 */
.trust-guide-card {
  margin: 12px 16px 0;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  cursor: pointer;
  active-transition: opacity 0.1s;
}
.trust-guide-card:active { opacity: 0.8; }
.tg-icon {
  position: relative;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #E8F4FD;
  border-radius: 12px;
}
.tg-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  border: 2px solid #4FA8D5;
  animation: pulse 2s ease infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50%       { opacity: 0.2; transform: scale(1.08); }
}
.tg-text { flex: 1; }
.tg-title { font-size: 14px; font-weight: 600; color: #222; margin: 0 0 2px; }
.tg-desc  { font-size: 12px; color: #888; margin: 0; }
.tg-remaining {
  text-align: center;
}
.remaining-num {
  font-size: 22px;
  font-weight: 700;
  color: #1565C0;
  line-height: 1;
  display: block;
}
.remaining-label { font-size: 10px; color: #aaa; }

/* 微任务卡片 */
.micro-task-card {
  margin: 12px 16px 0;
  background: linear-gradient(135deg, #E8F5E9, #F1F8E9);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.04);
}
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.task-label { font-size: 11px; color: #4CAF50; font-weight: 600; letter-spacing: 0.5px; }
.task-content { font-size: 14px; color: #333; margin: 0 0 10px; line-height: 1.6; }

/* 晋级提示 */
.upgrade-hint-card {
  margin: 12px 16px 0;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.04);
}
.upgrade-progress {
  height: 4px;
  background: #eee;
  border-radius: 2px;
  margin-bottom: 12px;
  overflow: hidden;
}
.upgrade-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1565C0, #42A5F5);
  border-radius: 2px;
  transition: width 0.6s ease;
}
.upgrade-text {
  font-size: 13px;
  color: #555;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.upgrade-steps { display: flex; gap: 16px; flex-wrap: wrap; }
.upgrade-step {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #aaa;
}
.upgrade-step.done { color: #4CAF50; }

/* 底部宣言 */
.platform-manifesto {
  margin: 24px 16px 0;
  padding: 16px;
  border-left: 3px solid #1565C0;
  background: rgba(21,101,192,0.04);
  border-radius: 0 12px 12px 0;
}
.platform-manifesto p {
  font-size: 12px;
  color: #888;
  margin: 0;
  line-height: 2;
}
</style>
