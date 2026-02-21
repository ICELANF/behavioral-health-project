<template>
  <!-- 3-step onboarding guide for new users -->
  <div class="onboarding-guide">
    <van-swipe :autoplay="0" :show-indicators="true" @change="onSlideChange">
      <!-- Step 1: Welcome -->
      <van-swipe-item>
        <div class="step-content">
          <div class="step-emoji">🌿</div>
          <h1 class="step-title">欢迎来到行健平台</h1>
          <p class="step-desc">
            AI + 专业教练，陪你养成健康好习惯
          </p>
          <div class="step-features">
            <div class="feature-item">
              <span class="feature-icon">🧠</span>
              <span>AI 个性化健康评估</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📋</span>
              <span>每日行为处方</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">👥</span>
              <span>专业健康教练陪伴</span>
            </div>
          </div>
          <p class="step-hint">← 左滑开始 →</p>
        </div>
      </van-swipe-item>

      <!-- Step 2: Try it -->
      <van-swipe-item>
        <div class="step-content">
          <div class="step-emoji">📸</div>
          <h1 class="step-title">体验一下</h1>
          <p class="step-desc">
            拍一张你的午餐，AI 帮你分析营养
          </p>
          <button class="try-btn" @click="tryAction">
            <span>打开相机拍食物</span>
            <span class="try-badge">免费体验</span>
          </button>
          <button class="try-btn secondary" @click="tryChatAction">
            <span>和 AI 聊聊健康</span>
          </button>
        </div>
      </van-swipe-item>

      <!-- Step 3: Set goal -->
      <van-swipe-item>
        <div class="step-content">
          <div class="step-emoji">🎯</div>
          <h1 class="step-title">设定目标</h1>
          <p class="step-desc">
            完成健康评估，解锁专属方案
          </p>
          <div class="goal-options">
            <div
              v-for="goal in goals"
              :key="goal.key"
              class="goal-card"
              :class="{ selected: selectedGoal === goal.key }"
              @click="selectedGoal = goal.key"
            >
              <span class="goal-icon">{{ goal.icon }}</span>
              <span class="goal-label">{{ goal.label }}</span>
            </div>
          </div>
          <button class="cta-start" @click="finishOnboarding">
            开始健康评估 →
          </button>
          <button class="skip-btn" @click="skipOnboarding">
            稍后再说
          </button>
        </div>
      </van-swipe-item>
    </van-swipe>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { track } from '@/utils/tracker'

const router = useRouter()
const currentStep = ref(0)
const selectedGoal = ref('')

const goals = [
  { key: 'glucose', icon: '🩸', label: '控制血糖' },
  { key: 'weight', icon: '⚖️', label: '减重塑形' },
  { key: 'sleep', icon: '😴', label: '改善睡眠' },
  { key: 'exercise', icon: '🏃', label: '规律运动' },
]

function onSlideChange(index: number) {
  currentStep.value = index
  track('onboarding_step', { step: index })
}

function tryAction() {
  track('onboarding_try', { type: 'food_scan' })
  router.push({ path: '/chat', query: { action: 'camera', type: 'food' } })
}

function tryChatAction() {
  track('onboarding_try', { type: 'chat' })
  router.push('/chat')
}

function finishOnboarding() {
  localStorage.setItem('bhp_onboarding_done', '1')
  track('onboarding_complete', { goal: selectedGoal.value })
  router.push('/v3/assessment/start')
}

function skipOnboarding() {
  localStorage.setItem('bhp_onboarding_done', '1')
  track('onboarding_skip', { step: currentStep.value })
  router.push('/home/observer')
}
</script>

<style scoped>
.onboarding-guide {
  min-height: 100vh;
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 60%);
}

:deep(.van-swipe) {
  height: 100vh;
}

.step-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 24px;
  text-align: center;
}

.step-emoji {
  font-size: 64px;
  margin-bottom: 20px;
}

.step-title {
  font-size: 24px;
  font-weight: 800;
  color: #111827;
  margin: 0 0 12px;
}

.step-desc {
  font-size: 15px;
  color: #6b7280;
  margin: 0 0 32px;
  max-width: 280px;
}

.step-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: #374151;
}

.feature-icon {
  font-size: 20px;
}

.step-hint {
  font-size: 13px;
  color: #9ca3af;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.try-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  max-width: 280px;
  padding: 14px 20px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  border-radius: 14px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.try-btn.secondary {
  background: #f3f4f6;
  color: #374151;
}

.try-badge {
  font-size: 11px;
  background: rgba(255,255,255,0.25);
  padding: 2px 8px;
  border-radius: 6px;
}

.goal-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 24px;
  width: 100%;
  max-width: 300px;
}

.goal-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.goal-card.selected {
  border-color: #10b981;
  background: #ecfdf5;
}

.goal-icon {
  font-size: 28px;
}

.goal-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.cta-start {
  width: 100%;
  max-width: 300px;
  padding: 14px;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  border-radius: 14px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  margin-bottom: 12px;
}

.skip-btn {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
  padding: 8px;
}
</style>
