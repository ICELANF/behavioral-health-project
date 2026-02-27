<template>
  <div class="grower-onboarding">
    <van-nav-bar title="完善健康档案" />

    <van-steps :active="currentStep" finish-icon="success" class="ob-steps">
      <van-step>基本信息</van-step>
      <van-step>健康目标</van-step>
      <van-step>推荐计划</van-step>
    </van-steps>

    <!-- Step 1: 基本信息 -->
    <div v-if="currentStep === 0" class="step-panel">
      <p class="panel-desc">填写基本信息，帮助我们更好地为您制定健康方案</p>

      <van-cell-group inset>
        <van-field label="性别" input-align="right">
          <template #input>
            <van-radio-group v-model="profile.gender" direction="horizontal">
              <van-radio name="male">男</van-radio>
              <van-radio name="female">女</van-radio>
            </van-radio-group>
          </template>
        </van-field>

        <van-field
          v-model="profile.birth_year"
          label="出生年份"
          placeholder="如 1985"
          type="digit"
          maxlength="4"
          input-align="right"
        />

        <van-field label="身高 (cm)" input-align="right">
          <template #input>
            <van-stepper v-model="profile.height" :min="100" :max="250" :step="1" />
          </template>
        </van-field>

        <van-field label="体重 (kg)" input-align="right">
          <template #input>
            <van-stepper v-model="profile.weight" :min="30" :max="200" :step="0.5" :decimal-length="1" />
          </template>
        </van-field>
      </van-cell-group>

      <div class="step-actions">
        <van-button type="primary" block round @click="nextStep">下一步</van-button>
        <van-button plain block round class="skip-btn" @click="skipAll">稍后完善</van-button>
      </div>
    </div>

    <!-- Step 2: 健康目标 -->
    <div v-if="currentStep === 1" class="step-panel">
      <p class="panel-desc">选择您当前最关注的健康目标（可多选）</p>

      <div class="goal-grid">
        <div
          v-for="goal in goalOptions"
          :key="goal.key"
          class="goal-chip"
          :class="{ active: selectedGoals.includes(goal.key) }"
          @click="toggleGoal(goal.key)"
        >
          <span class="goal-icon">{{ goal.icon }}</span>
          <span class="goal-text">{{ goal.label }}</span>
        </div>
      </div>

      <div class="step-actions">
        <van-button type="primary" block round @click="nextStep">下一步</van-button>
        <van-button plain block round @click="currentStep = 0">上一步</van-button>
      </div>
    </div>

    <!-- Step 3: 推荐计划 -->
    <div v-if="currentStep === 2" class="step-panel">
      <p class="panel-desc">根据您的目标，推荐以下健康计划</p>

      <div v-if="recommendedPrograms.length === 0" class="empty-tip">
        暂无匹配计划，您可以稍后在「方案」页面选择
      </div>

      <div v-for="prog in recommendedPrograms" :key="prog.id" class="program-card">
        <div class="prog-header">
          <span class="prog-name">{{ prog.title || prog.name }}</span>
          <van-tag type="primary" size="medium">{{ prog.total_days || prog.duration_days }}天</van-tag>
        </div>
        <p class="prog-desc">{{ prog.description }}</p>
        <van-button
          size="small"
          type="primary"
          round
          :loading="enrollingId === prog.id"
          :disabled="enrolledIds.includes(prog.id)"
          @click="enrollProgram(prog.id)"
        >
          {{ enrolledIds.includes(prog.id) ? '已加入' : '加入计划' }}
        </van-button>
      </div>

      <div class="step-actions">
        <van-button type="primary" block round :loading="finishing" @click="finishOnboarding">
          {{ enrolledIds.length > 0 ? '开始健康之旅' : '跳过，直接进入' }}
        </van-button>
        <van-button plain block round @click="currentStep = 1">上一步</van-button>
      </div>
    </div>

    <!-- 完成后兜底: 如果跳转失败，仍能手动进入 -->
    <div v-if="currentStep >= 3" class="step-panel">
      <div class="finish-hero">
        <div class="finish-icon">🎉</div>
        <p class="finish-text">健康档案已完善！</p>
        <van-button type="primary" block round @click="forceNavigate">进入首页</van-button>
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

// Step 1: 基本信息
const profile = reactive({
  gender: '',
  birth_year: '',
  height: 170,
  weight: 65,
})

// Step 2: 健康目标
const goalOptions = [
  { key: 'glucose_control', icon: '🩸', label: '血糖控制' },
  { key: 'weight_loss', icon: '⚖️', label: '减重管理' },
  { key: 'sleep_improve', icon: '😴', label: '睡眠改善' },
  { key: 'exercise_regular', icon: '🏃', label: '运动规律' },
  { key: 'stress_manage', icon: '🧘', label: '压力管理' },
  { key: 'medication_adherence', icon: '💊', label: '用药依从' },
]
const selectedGoals = ref<string[]>([])

function toggleGoal(key: string) {
  const idx = selectedGoals.value.indexOf(key)
  if (idx >= 0) {
    selectedGoals.value.splice(idx, 1)
  } else {
    selectedGoals.value.push(key)
  }
}

// Step 3: 推荐计划
const recommendedPrograms = ref<any[]>([])
const enrollingId = ref('')
const enrolledIds = ref<string[]>([])
const finishing = ref(false)

async function nextStep() {
  if (currentStep.value === 0) {
    // 保存基本信息到后端
    await saveProfile()
  }
  if (currentStep.value === 1) {
    // 保存目标 + 加载推荐计划
    await saveGoals()
    await loadPrograms()
  }
  currentStep.value++
}

async function saveProfile() {
  try {
    const age = profile.birth_year
      ? new Date().getFullYear() - parseInt(profile.birth_year)
      : undefined
    await api.put('/api/v1/assessment/profile/me', {
      gender: profile.gender || undefined,
      age: age,
      height: profile.height,
      weight: profile.weight,
    })
  } catch {
    // 非阻塞 — 保存失败不影响继续
  }
}

async function saveGoals() {
  if (selectedGoals.value.length === 0) return
  try {
    await api.put('/api/v1/assessment/profile/me', {
      goals: selectedGoals.value,
    })
  } catch {
    // 非阻塞
  }
}

async function loadPrograms() {
  try {
    const res: any = await api.get('/api/v1/programs/templates', {
      params: { page_size: 5 }
    })
    const raw = res?.data?.items || res?.items || res?.data || res || []
    const items = Array.isArray(raw) ? raw : []
    recommendedPrograms.value = items.slice(0, 3)
  } catch {
    recommendedPrograms.value = []
  }
}

async function enrollProgram(programId: string) {
  enrollingId.value = programId
  try {
    await api.post('/api/v1/programs/enroll', { template_id: programId })
    enrolledIds.value.push(programId)
    showToast({ message: '已加入计划', type: 'success' })
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    if (detail === 'already_enrolled') {
      enrolledIds.value.push(programId)
      showToast({ message: '您已加入该计划', type: 'success' })
    } else {
      showToast('加入失败，请稍后重试')
    }
  } finally {
    enrollingId.value = ''
  }
}

async function finishOnboarding() {
  finishing.value = true
  localStorage.setItem('bhp_grower_onboarding_done', '1')
  showToast({ message: '欢迎成为成长者！', type: 'success' })
  try {
    await router.replace('/home/today')
  } catch {
    // 路由跳转失败兜底
    currentStep.value = 3
    finishing.value = false
  }
}

function forceNavigate() {
  localStorage.setItem('bhp_grower_onboarding_done', '1')
  window.location.href = '/'
}

function skipAll() {
  localStorage.setItem('bhp_grower_onboarding_done', '1')
  router.replace('/home/today')
}

onMounted(async () => {
  // 如果已完成引导，直接跳转
  if (localStorage.getItem('bhp_grower_onboarding_done')) {
    try {
      await router.replace('/home/today')
    } catch {
      window.location.href = '/'
    }
    return
  }
  // 加载已加入的计划，避免重复加入
  try {
    const res: any = await api.get('/api/v1/programs/my')
    const myPrograms = Array.isArray(res) ? res : (res?.data || [])
    enrolledIds.value = myPrograms
      .filter((p: any) => ['active', 'paused'].includes(p.status))
      .map((p: any) => p.template_id)
      .filter(Boolean)
  } catch {
    // 非阻塞
  }
})
</script>

<style scoped>
.grower-onboarding {
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

/* Goal grid */
.goal-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 0 8px;
}

.goal-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 12px;
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.goal-chip.active {
  border-color: #10b981;
  background: #ecfdf5;
}

.goal-icon {
  font-size: 22px;
}

.goal-text {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

/* Program cards */
.program-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.prog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.prog-name {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.prog-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 12px;
  line-height: 1.5;
}

.empty-tip {
  text-align: center;
  padding: 32px 16px;
  color: #9ca3af;
  font-size: 14px;
}

/* Finish hero */
.finish-hero {
  text-align: center;
  padding: 48px 24px;
}

.finish-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.finish-text {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 28px;
}
</style>
