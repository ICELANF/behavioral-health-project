<template>
  <div class="sharer-onboarding">
    <van-nav-bar title="欢迎成为分享者" />

    <van-steps :active="currentStep" finish-icon="success" class="ob-steps">
      <van-step>晋升庆祝</van-step>
      <van-step>能力解锁</van-step>
      <van-step>开始行动</van-step>
    </van-steps>

    <!-- Step 1: 庆祝+身份 -->
    <div v-if="currentStep === 0" class="step-panel">
      <div class="celebrate-hero">
        <div class="celebrate-emoji">🎉</div>
        <h2 class="celebrate-title">恭喜晋升为分享者！</h2>
        <p class="celebrate-desc">
          您已经累积了丰富的健康管理经验，现在您可以帮助更多人走上健康之路。
        </p>
        <div class="badge-card">
          <span class="badge-icon">💬</span>
          <div class="badge-info">
            <span class="badge-role">分享者 · Level 2</span>
            <span class="badge-motto">分享经验，引领成长</span>
          </div>
        </div>
        <div class="achievement-row">
          <div class="ach-item">
            <span class="ach-num">{{ achievementData.growth }}</span>
            <span class="ach-label">成长积分</span>
          </div>
          <div class="ach-item">
            <span class="ach-num">{{ achievementData.contribution }}</span>
            <span class="ach-label">贡献积分</span>
          </div>
          <div class="ach-item">
            <span class="ach-num">{{ achievementData.streak }}</span>
            <span class="ach-label">最长连续</span>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <van-button type="primary" block round @click="currentStep = 1">
          了解分享者任务 →
        </van-button>
      </div>
    </div>

    <!-- Step 2: 能力解锁 -->
    <div v-if="currentStep === 1" class="step-panel">
      <p class="panel-desc">作为分享者，您解锁了以下能力</p>

      <div class="unlock-grid">
        <div class="unlock-card" v-for="item in unlockItems" :key="item.icon">
          <span class="unlock-icon">{{ item.icon }}</span>
          <span class="unlock-title">{{ item.title }}</span>
          <span class="unlock-desc">{{ item.desc }}</span>
        </div>
      </div>

      <div class="mission-card">
        <h3 class="mission-title">核心使命</h3>
        <p class="mission-text">引领 <strong>4位</strong> 同道者 · 分享 <strong>10篇</strong> 健康故事</p>
      </div>

      <div class="step-actions">
        <van-button type="primary" block round @click="currentStep = 2">下一步</van-button>
        <van-button plain block round @click="currentStep = 0">上一步</van-button>
      </div>
    </div>

    <!-- Step 3: 第一步行动 -->
    <div v-if="currentStep === 2" class="step-panel">
      <p class="panel-desc">选择您的第一步行动</p>

      <div class="first-action-cards">
        <div class="fa-card" @click="goCompanions">
          <span class="fa-icon">🤝</span>
          <span class="fa-title">邀请同道者</span>
          <span class="fa-desc">找到第一位您想帮助的伙伴</span>
        </div>
        <div class="fa-card" @click="goContribute">
          <span class="fa-icon">📝</span>
          <span class="fa-title">写第一篇经验</span>
          <span class="fa-desc">分享您的健康管理故事</span>
        </div>
      </div>

      <div class="step-actions">
        <van-button type="primary" block round @click="finishOnboarding">
          进入分享者首页
        </van-button>
        <van-button plain block round class="skip-btn" @click="skipOnboarding">
          稍后再说
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'

const router = useRouter()
const currentStep = ref(0)

// 成就数据 (从API获取)
const achievementData = reactive({
  growth: 0,
  contribution: 0,
  streak: 0,
})

// 能力解锁卡片
const unlockItems = [
  { icon: '📝', title: '发布经验', desc: '分享您的健康管理心得和技巧' },
  { icon: '🤝', title: '引领新成员', desc: '作为导师帮助观察者成长' },
  { icon: '💬', title: '社群答疑', desc: '回答社群中的健康问题' },
  { icon: '⭐', title: '影响力积分', desc: '被点赞、收藏都会积累影响力' },
]

function goCompanions() {
  finishOnboarding()
  router.replace({ path: '/my-companions', query: { action: 'invite' } })
}

function goContribute() {
  finishOnboarding()
  router.replace('/contribute')
}

function finishOnboarding() {
  localStorage.setItem('bhp_sharer_onboarding_done', '1')
  showToast({ message: '欢迎成为分享者！', type: 'success' })
  router.replace('/home/sharer')
}

function skipOnboarding() {
  localStorage.setItem('bhp_sharer_onboarding_done', '1')
  router.replace('/home/sharer')
}

onMounted(async () => {
  // 如果已完成引导，直接跳转
  if (localStorage.getItem('bhp_sharer_onboarding_done')) {
    router.replace('/home/sharer')
    return
  }

  // 加载成就数据
  try {
    const [streakRes, checkRes] = await Promise.allSettled([
      api.get('/api/v1/user/streak'),
      api.get('/api/v1/promotion/sharer-check'),
    ])
    if (streakRes.status === 'fulfilled') {
      const data = streakRes.value as any
      achievementData.streak = data.longest_streak || data.current_streak || 0
    }
    if (checkRes.status === 'fulfilled') {
      const data = checkRes.value as any
      achievementData.growth = data.growth_points || 0
      achievementData.contribution = data.contribution_points || 0
    }
  } catch { /* non-blocking */ }
})
</script>

<style scoped>
.sharer-onboarding {
  min-height: 100vh;
  background: #f7f8fa;
}

.ob-steps {
  padding: 16px 20px;
  background: #fff;
}

.step-panel {
  padding: 20px 16px;
}

.panel-desc {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  margin: 0 0 20px;
}

.step-actions {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 16px;
}

.skip-btn {
  color: #9ca3af !important;
  border-color: #e5e7eb !important;
}

/* ── Step 1: 庆祝 ── */
.celebrate-hero {
  text-align: center;
  padding: 16px 0;
}
.celebrate-emoji { font-size: 56px; margin-bottom: 12px; }
.celebrate-title { font-size: 24px; font-weight: 800; color: #111827; margin: 0 0 8px; }
.celebrate-desc { font-size: 14px; color: #6b7280; line-height: 1.6; margin: 0 0 20px; padding: 0 16px; }

.badge-card {
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  border-radius: 16px; padding: 16px 20px; margin: 0 16px 20px;
}
.badge-icon { font-size: 32px; }
.badge-info { display: flex; flex-direction: column; }
.badge-role { font-size: 16px; font-weight: 700; color: #5b21b6; }
.badge-motto { font-size: 13px; color: #7c3aed; margin-top: 2px; }

.achievement-row { display: flex; justify-content: center; gap: 24px; }
.ach-item { display: flex; flex-direction: column; align-items: center; }
.ach-num { font-size: 22px; font-weight: 800; color: #111827; }
.ach-label { font-size: 12px; color: #9ca3af; margin-top: 2px; }

/* ── Step 2: 解锁 ── */
.unlock-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 0 8px;
  margin-bottom: 20px;
}
.unlock-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 6px; padding: 16px 12px;
  background: #fff; border: 2px solid #e5e7eb; border-radius: 12px;
  text-align: center;
}
.unlock-icon { font-size: 28px; }
.unlock-title { font-size: 14px; font-weight: 700; color: #374151; }
.unlock-desc { font-size: 12px; color: #9ca3af; line-height: 1.4; }

.mission-card {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-radius: 14px; padding: 16px 20px; margin: 0 8px; text-align: center;
}
.mission-title { font-size: 14px; font-weight: 700; color: #065f46; margin: 0 0 6px; }
.mission-text { font-size: 14px; color: #047857; margin: 0; line-height: 1.5; }

/* ── Step 3: 行动 ── */
.first-action-cards {
  display: flex; flex-direction: column; gap: 12px; padding: 0 8px;
}
.fa-card {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  background: #fff; border: 2px solid #e5e7eb; border-radius: 14px;
  padding: 20px 16px; cursor: pointer; transition: all 0.2s;
}
.fa-card:active { border-color: #10b981; background: #ecfdf5; transform: scale(0.98); }
.fa-icon { font-size: 32px; }
.fa-title { font-size: 16px; font-weight: 700; color: #111827; }
.fa-desc { font-size: 13px; color: #6b7280; }
</style>
