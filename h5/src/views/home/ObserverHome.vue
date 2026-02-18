<template>
  <!-- 
    Observer 试用墙首页
    飞轮目标: 转化 — 让Observer在3次免费对话中体验价值，推动完成评估升级为Grower
    替换: h5/src/views/home/index.vue (当Observer角色时渲染此组件)
  -->
  <div class="observer-home">
    <!-- ═══ 顶部: 今日剩余额度 (紧迫感) ═══ -->
    <div class="quota-banner" :class="{ 'quota-low': remaining <= 1, 'quota-zero': remaining <= 0 }">
      <div class="quota-inner">
        <div class="quota-dots">
          <span v-for="i in 3" :key="i" class="dot" :class="{ used: i > remaining }" />
        </div>
        <span class="quota-text" v-if="remaining > 0">
          今日还能对话 <strong>{{ remaining }}</strong> 次
        </span>
        <span class="quota-text urgent" v-else>
          今日对话次数已用完
        </span>
      </div>
    </div>

    <!-- ═══ 价值预览卡片 (展示升级后能解锁什么) ═══ -->
    <div class="hero-section">
      <h1 class="hero-title">你的AI健康伙伴</h1>
      <p class="hero-subtitle">
        完成健康评估，解锁专属健康管理方案
      </p>

      <!-- 核心CTA: 开始评估 -->
      <button class="cta-primary" @click="startAssessment" v-if="!assessmentStarted">
        <span class="cta-icon">📋</span>
        <span class="cta-content">
          <strong>开始健康评估</strong>
          <small>约10分钟 · 解锁全部功能</small>
        </span>
        <span class="cta-arrow">→</span>
      </button>

      <!-- 评估进行中: 继续评估 -->
      <button class="cta-primary cta-continue" @click="continueAssessment" v-else>
        <span class="cta-icon">📝</span>
        <span class="cta-content">
          <strong>继续评估</strong>
          <small>已完成 {{ assessmentProgress }}%</small>
        </span>
        <div class="progress-ring">
          <svg viewBox="0 0 36 36">
            <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            <path class="ring-fill" :stroke-dasharray="`${assessmentProgress}, 100`"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
          </svg>
        </div>
      </button>
    </div>

    <!-- ═══ 快速体验入口 (消耗免费次数的钩子) ═══ -->
    <div class="quick-try-section">
      <h2 class="section-title">先试试</h2>
      <div class="try-cards">
        <div class="try-card" @click="tryFeature('food')" :class="{ disabled: remaining <= 0 }">
          <span class="try-icon">📸</span>
          <span class="try-label">拍食物<br/>分析营养</span>
          <span class="try-badge free" v-if="remaining > 0">免费</span>
          <span class="try-badge locked" v-else>🔒</span>
        </div>
        <div class="try-card" @click="tryFeature('chat')" :class="{ disabled: remaining <= 0 }">
          <span class="try-icon">💬</span>
          <span class="try-label">问健康<br/>AI解答</span>
          <span class="try-badge free" v-if="remaining > 0">免费</span>
          <span class="try-badge locked" v-else>🔒</span>
        </div>
        <div class="try-card" @click="tryFeature('voice')" :class="{ disabled: remaining <= 0 }">
          <span class="try-icon">🎤</span>
          <span class="try-label">语音聊<br/>更方便</span>
          <span class="try-badge free" v-if="remaining > 0">免费</span>
          <span class="try-badge locked" v-else>🔒</span>
        </div>
      </div>
    </div>

    <!-- ═══ 升级对比 (解锁功能预览) ═══ -->
    <div class="upgrade-preview">
      <h2 class="section-title">完成评估后解锁</h2>
      <div class="unlock-list">
        <div class="unlock-item" v-for="item in unlockItems" :key="item.label">
          <span class="unlock-icon">{{ item.icon }}</span>
          <div class="unlock-info">
            <span class="unlock-label">{{ item.label }}</span>
            <span class="unlock-desc">{{ item.desc }}</span>
          </div>
          <span class="unlock-lock">🔒</span>
        </div>
      </div>

      <!-- 次级CTA -->
      <button class="cta-secondary" @click="startAssessment">
        立即解锁全部功能 →
      </button>
    </div>

    <!-- ═══ 社会证明 ═══ -->
    <div class="social-proof">
      <div class="proof-stat">
        <strong>{{ userCount.toLocaleString() }}+</strong>
        <span>人已在使用</span>
      </div>
      <div class="proof-divider" />
      <div class="proof-stat">
        <strong>92%</strong>
        <span>用户坚持21天</span>
      </div>
      <div class="proof-divider" />
      <div class="proof-stat">
        <strong>4.8</strong>
        <span>满意度评分</span>
      </div>
    </div>

    <!-- ═══ 用完次数后的全屏升级提示 ═══ -->
    <div class="upgrade-overlay" v-if="showUpgradePrompt" @click.self="showUpgradePrompt = false">
      <div class="upgrade-modal">
        <div class="modal-emoji">🌟</div>
        <h3>今天的体验结束了</h3>
        <p>完成健康评估，即可解锁<strong>无限对话</strong>和全部功能</p>
        <button class="cta-primary modal-cta" @click="startAssessment">
          <strong>现在就去评估</strong>
          <small>约10分钟 · 永久解锁</small>
        </button>
        <button class="modal-dismiss" @click="showUpgradePrompt = false">
          明天再来
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
// import { useUserStore } from '@/stores/user'
// import { observerQuotaApi } from '@/api/observer'

const router = useRouter()
// const userStore = useUserStore()

// ── 状态 ──
const dailyUsed = ref(0)
const assessmentStarted = ref(false)
const assessmentProgress = ref(0)
const showUpgradePrompt = ref(false)
const userCount = ref(12847) // 从后端获取

const remaining = computed(() => Math.max(0, 3 - dailyUsed.value))

const unlockItems = [
  { icon: '🎤', label: '无限语音对话', desc: '方言也能听懂' },
  { icon: '📸', label: '无限食物识别', desc: '每餐拍一拍，营养全掌握' },
  { icon: '📊', label: '个人健康仪表盘', desc: '看到你的改变趋势' },
  { icon: '📋', label: '专属行为处方', desc: 'AI为你定制每日行动' },
  { icon: '🏃', label: '运动视频分析', desc: '纠正动作，避免受伤' },
  { icon: '⌚', label: '穿戴设备联动', desc: '血糖/心率异常即时提醒' },
]

// ── 方法 ──
function startAssessment() {
  router.push('/v3/assessment/start')
}

function continueAssessment() {
  router.push('/v3/assessment/continue')
}

function tryFeature(type: string) {
  if (remaining.value <= 0) {
    showUpgradePrompt.value = true
    return
  }
  switch (type) {
    case 'food':
      router.push({ path: '/chat', query: { action: 'camera', type: 'food' } })
      break
    case 'chat':
      router.push('/chat')
      break
    case 'voice':
      router.push({ path: '/chat', query: { action: 'voice' } })
      break
  }
}

onMounted(async () => {
  // const quota = await observerQuotaApi.getToday()
  // dailyUsed.value = quota.used
  // assessmentStarted.value = quota.assessmentStarted
  // assessmentProgress.value = quota.assessmentProgress
})
</script>

<style scoped>
.observer-home {
  min-height: 100vh;
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 40%);
  padding-bottom: env(safe-area-inset-bottom, 20px);
}

/* ── 额度横幅 ── */
.quota-banner {
  padding: 12px 16px;
  background: #f0fdf4;
  border-bottom: 1px solid #bbf7d0;
  position: sticky; top: 0; z-index: 10;
}
.quota-banner.quota-low { background: #fef9c3; border-color: #fde68a; }
.quota-banner.quota-zero { background: #fef2f2; border-color: #fecaca; }
.quota-inner { display: flex; align-items: center; justify-content: center; gap: 10px; }
.quota-dots { display: flex; gap: 6px; }
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--bhp-brand-primary, #10b981);
  transition: all 0.3s;
}
.dot.used { background: #d1d5db; }
.quota-text { font-size: 13px; color: #374151; }
.quota-text.urgent { color: #dc2626; font-weight: 600; }

/* ── 英雄区 ── */
.hero-section { padding: 32px 20px 24px; text-align: center; }
.hero-title {
  font-size: 26px; font-weight: 800; color: #111827;
  margin: 0 0 8px;
}
.hero-subtitle { font-size: 15px; color: #6b7280; margin: 0 0 24px; }

/* ── CTA按钮 ── */
.cta-primary {
  display: flex; align-items: center; gap: 12px;
  width: 100%; padding: 16px 20px;
  background: linear-gradient(135deg, #10b981, #059669);
  border: none; border-radius: 16px; color: #fff;
  cursor: pointer; text-align: left;
  box-shadow: 0 4px 16px rgba(16,185,129,0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}
.cta-primary:active { transform: scale(0.98); }
.cta-icon { font-size: 28px; }
.cta-content { flex: 1; }
.cta-content strong { display: block; font-size: 16px; }
.cta-content small { font-size: 12px; opacity: 0.85; }
.cta-arrow { font-size: 20px; opacity: 0.8; }

.cta-continue { background: linear-gradient(135deg, #3b82f6, #2563eb); box-shadow: 0 4px 16px rgba(59,130,246,0.3); }
.progress-ring { width: 40px; height: 40px; }
.progress-ring svg { transform: rotate(-90deg); }
.ring-bg { fill: none; stroke: rgba(255,255,255,0.2); stroke-width: 3; }
.ring-fill { fill: none; stroke: #fff; stroke-width: 3; stroke-linecap: round; }

/* ── 快速体验 ── */
.quick-try-section { padding: 0 20px 24px; }
.section-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }
.try-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.try-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
  padding: 16px 8px; text-align: center; cursor: pointer;
  position: relative; transition: all 0.2s;
}
.try-card:active { transform: scale(0.96); background: #f9fafb; }
.try-card.disabled { opacity: 0.5; pointer-events: none; }
.try-icon { font-size: 28px; display: block; margin-bottom: 6px; }
.try-label { font-size: 12px; color: #374151; line-height: 1.4; }
.try-badge {
  position: absolute; top: 6px; right: 6px; font-size: 10px;
  padding: 2px 6px; border-radius: 6px; font-weight: 600;
}
.try-badge.free { background: #dcfce7; color: #16a34a; }
.try-badge.locked { background: #f3f4f6; }

/* ── 解锁预览 ── */
.upgrade-preview { padding: 0 20px 24px; }
.unlock-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.unlock-item {
  display: flex; align-items: center; gap: 12px;
  background: #f9fafb; border-radius: 12px; padding: 12px 14px;
}
.unlock-icon { font-size: 22px; flex-shrink: 0; }
.unlock-info { flex: 1; }
.unlock-label { display: block; font-size: 14px; font-weight: 600; color: #111827; }
.unlock-desc { font-size: 12px; color: #6b7280; }
.unlock-lock { font-size: 14px; opacity: 0.4; }

.cta-secondary {
  display: block; width: 100%; padding: 14px;
  background: #fff; border: 2px solid var(--bhp-brand-primary, #10b981);
  border-radius: 12px; color: var(--bhp-brand-primary, #10b981);
  font-size: 15px; font-weight: 700; cursor: pointer;
  transition: all 0.2s;
}
.cta-secondary:active { background: #ecfdf5; }

/* ── 社会证明 ── */
.social-proof {
  display: flex; align-items: center; justify-content: center;
  padding: 20px; gap: 16px;
}
.proof-stat { text-align: center; }
.proof-stat strong { display: block; font-size: 18px; color: #111827; }
.proof-stat span { font-size: 11px; color: #6b7280; }
.proof-divider { width: 1px; height: 28px; background: #e5e7eb; }

/* ── 升级弹窗 ── */
.upgrade-overlay {
  position: fixed; inset: 0; z-index: 999;
  background: rgba(0,0,0,0.5); display: flex; align-items: flex-end;
  animation: fadeIn 0.2s;
}
.upgrade-modal {
  width: 100%; background: #fff; border-radius: 24px 24px 0 0;
  padding: 32px 24px env(safe-area-inset-bottom, 24px);
  text-align: center; animation: slideUp 0.3s;
}
.modal-emoji { font-size: 48px; margin-bottom: 12px; }
.upgrade-modal h3 { font-size: 20px; font-weight: 800; margin: 0 0 8px; color: #111827; }
.upgrade-modal p { font-size: 14px; color: #6b7280; margin: 0 0 20px; }
.modal-cta { justify-content: center; margin-bottom: 12px; }
.modal-dismiss {
  background: none; border: none; color: #9ca3af; font-size: 14px;
  cursor: pointer; padding: 8px;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
</style>
