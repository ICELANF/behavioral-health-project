<template>
  <view class="rg-page">
    <!-- 顶部进度条 -->
    <view class="rg-topbar">
      <view class="rg-back" @tap="handleBack">←</view>
      <view class="rg-steps">
        <view v-for="n in 4" :key="n" class="rg-step-dot"
          :class="{ 'rg-step-dot--done': step > n, 'rg-step-dot--active': step === n }">
          <text class="rg-step-num">{{ n }}</text>
        </view>
        <view class="rg-step-line" v-for="n in 3" :key="'l'+n"
          :class="{ 'rg-step-line--done': step > n }" />
      </view>
      <view style="width:60rpx;"/>
    </view>

    <scroll-view scroll-y class="rg-scroll">

      <!-- ══════════════════════════════════════
           Step 1: 选择角色
      ══════════════════════════════════════ -->
      <view v-if="step === 1" class="rg-card rg-anim">
        <text class="rg-card-title">我是谁？</text>
        <text class="rg-card-sub">选择您在行健平台的身份</text>

        <view class="rg-roles">
          <view v-for="r in roles" :key="r.key" class="rg-role-item"
            :class="{ 'rg-role-item--active': form.role === r.key }"
            :style="form.role === r.key ? `border-color:${r.color};background:${r.bg}` : ''"
            @tap="form.role = r.key">
            <text class="rg-role-icon">{{ r.icon }}</text>
            <view class="rg-role-info">
              <text class="rg-role-name" :style="form.role === r.key ? `color:${r.color}` : ''">{{ r.name }}</text>
              <text class="rg-role-desc">{{ r.desc }}</text>
            </view>
            <view class="rg-role-check" :style="`background:${r.color}`" v-if="form.role === r.key">
              <text class="rg-check-mark">✓</text>
            </view>
          </view>
        </view>

        <view class="rg-next-btn" :class="{ 'rg-next-btn--disabled': !form.role }"
          :style="form.role ? `background:${currentRole?.color}` : ''" @tap="nextStep">
          下一步
        </view>
      </view>

      <!-- ══════════════════════════════════════
           Step 2: 账号信息
      ══════════════════════════════════════ -->
      <view v-if="step === 2" class="rg-card rg-anim">
        <text class="rg-card-title">创建账号</text>
        <text class="rg-card-sub">设置您的登录信息</text>

        <view class="rg-field">
          <text class="rg-label">真实姓名 *</text>
          <input class="rg-input" v-model="form.full_name" placeholder="请输入真实姓名" maxlength="20" />
        </view>
        <view class="rg-field">
          <text class="rg-label">用户名 *</text>
          <input class="rg-input" v-model="form.username" placeholder="字母/数字/下划线，3-30位" maxlength="30" />
        </view>
        <view class="rg-field">
          <text class="rg-label">邮箱 *</text>
          <input class="rg-input" v-model="form.email" placeholder="example@email.com" type="text" maxlength="60" />
        </view>
        <view class="rg-field">
          <text class="rg-label">手机号</text>
          <input class="rg-input" v-model="form.phone" placeholder="选填，用于找回密码" type="number" maxlength="11" />
        </view>
        <view class="rg-field">
          <text class="rg-label">密码 *</text>
          <input class="rg-input" v-model="form.password" placeholder="至少8位，含大小写字母和数字" password maxlength="50" />
        </view>
        <view class="rg-field">
          <text class="rg-label">确认密码 *</text>
          <input class="rg-input" v-model="form.confirmPwd" placeholder="再次输入密码" password maxlength="50" />
        </view>

        <view v-if="errMsg" class="rg-error"><text>{{ errMsg }}</text></view>

        <view class="rg-row-btns">
          <view class="rg-prev-btn" @tap="step=1">上一步</view>
          <view class="rg-next-btn rg-next-btn--sm" :style="`background:${currentRole?.color}`" @tap="nextStep">下一步</view>
        </view>
      </view>

      <!-- ══════════════════════════════════════
           Step 3: 角色专属信息
      ══════════════════════════════════════ -->
      <view v-if="step === 3" class="rg-card rg-anim">
        <text class="rg-card-title">完善档案</text>
        <text class="rg-card-sub">{{ currentRole?.profileHint }}</text>

        <!-- 性别（所有角色） -->
        <view class="rg-field">
          <text class="rg-label">性别</text>
          <view class="rg-gender-row">
            <view v-for="g in genders" :key="g.key" class="rg-gender-chip"
              :class="{ 'rg-gender-chip--active': form.gender === g.key }"
              :style="form.gender === g.key ? `background:${currentRole?.color};color:#fff;border-color:${currentRole?.color}` : ''"
              @tap="form.gender = g.key">{{ g.label }}</view>
          </view>
        </view>

        <!-- 成长者/分享者: 健康目标 -->
        <view v-if="isUserRole" class="rg-field">
          <text class="rg-label">健康目标（可多选）</text>
          <view class="rg-tag-row">
            <view v-for="g in healthGoals" :key="g" class="rg-tag"
              :class="{ 'rg-tag--active': selectedGoals.includes(g) }"
              :style="selectedGoals.includes(g) ? `background:${currentRole?.color};color:#fff;border-color:${currentRole?.color}` : ''"
              @tap="toggleGoal(g)">{{ g }}</view>
          </view>
        </view>

        <!-- 教练/督导/专家: 专业背景 -->
        <view v-if="isProfessionalRole" class="rg-field">
          <text class="rg-label">专业领域</text>
          <view class="rg-tag-row">
            <view v-for="s in specialties" :key="s" class="rg-tag"
              :class="{ 'rg-tag--active': form.specialty === s }"
              :style="form.specialty === s ? `background:${currentRole?.color};color:#fff;border-color:${currentRole?.color}` : ''"
              @tap="form.specialty = s">{{ s }}</view>
          </view>
        </view>

        <!-- 教练/督导: 从业年限 -->
        <view v-if="isProfessionalRole" class="rg-field">
          <text class="rg-label">从业年限</text>
          <picker :range="yearsOptions" :value="yearsIdx" @change="yearsIdx = $event.detail.value">
            <view class="rg-picker">{{ yearsOptions[yearsIdx] }}</view>
          </picker>
        </view>

        <view class="rg-row-btns">
          <view class="rg-prev-btn" @tap="step=2">上一步</view>
          <view class="rg-next-btn rg-next-btn--sm" :style="`background:${currentRole?.color}`" @tap="nextStep">下一步</view>
        </view>
      </view>

      <!-- ══════════════════════════════════════
           Step 4: 确认 & 提交
      ══════════════════════════════════════ -->
      <view v-if="step === 4" class="rg-card rg-anim">
        <text class="rg-card-title">确认注册</text>
        <text class="rg-card-sub">请确认您的信息后提交</text>

        <view class="rg-confirm-list">
          <view class="rg-confirm-row">
            <text class="rg-confirm-label">角色</text>
            <view class="rg-confirm-badge" :style="`background:${currentRole?.bg};color:${currentRole?.color};border-color:${currentRole?.color}`">
              {{ currentRole?.icon }} {{ currentRole?.name }}
            </view>
          </view>
          <view class="rg-confirm-row">
            <text class="rg-confirm-label">姓名</text>
            <text class="rg-confirm-value">{{ form.full_name }}</text>
          </view>
          <view class="rg-confirm-row">
            <text class="rg-confirm-label">用户名</text>
            <text class="rg-confirm-value">{{ form.username }}</text>
          </view>
          <view class="rg-confirm-row">
            <text class="rg-confirm-label">邮箱</text>
            <text class="rg-confirm-value">{{ form.email }}</text>
          </view>
          <view class="rg-confirm-row" v-if="form.phone">
            <text class="rg-confirm-label">手机</text>
            <text class="rg-confirm-value">{{ form.phone }}</text>
          </view>
          <view class="rg-confirm-row" v-if="form.gender">
            <text class="rg-confirm-label">性别</text>
            <text class="rg-confirm-value">{{ genders.find(g=>g.key===form.gender)?.label }}</text>
          </view>
          <view class="rg-confirm-row" v-if="selectedGoals.length">
            <text class="rg-confirm-label">健康目标</text>
            <text class="rg-confirm-value">{{ selectedGoals.join('、') }}</text>
          </view>
          <view class="rg-confirm-row" v-if="form.specialty">
            <text class="rg-confirm-label">专业领域</text>
            <text class="rg-confirm-value">{{ form.specialty }}</text>
          </view>
        </view>

        <view class="rg-agree-row" @tap="agreed = !agreed">
          <view class="rg-checkbox" :class="{ 'rg-checkbox--checked': agreed }"
            :style="agreed ? `background:${currentRole?.color};border-color:${currentRole?.color}` : ''">
            <text v-if="agreed" class="rg-check-icon">✓</text>
          </view>
          <text class="rg-agree-text">我已阅读并同意</text>
          <text class="rg-agree-link" :style="`color:${currentRole?.color}`">《用户协议》</text>
          <text class="rg-agree-text">和</text>
          <text class="rg-agree-link" :style="`color:${currentRole?.color}`">《隐私政策》</text>
        </view>

        <view v-if="errMsg" class="rg-error"><text>{{ errMsg }}</text></view>

        <view class="rg-submit-btn"
          :class="{ 'rg-submit-btn--loading': loading, 'rg-submit-btn--disabled': !agreed }"
          :style="agreed && !loading ? `background:${currentRole?.color}` : ''"
          @tap="doRegister">
          {{ loading ? '注册中…' : '立即注册' }}
        </view>

        <view class="rg-row-btns" style="margin-top:20rpx;">
          <view class="rg-prev-btn" style="flex:1;" @tap="step=3">上一步</view>
        </view>
      </view>

      <!-- 底部登录链接 -->
      <view class="rg-login-link" @tap="goLogin">
        <text class="rg-login-text">已有账号？</text>
        <text class="rg-login-btn">立即登录</text>
      </view>

      <view style="height:80rpx;"/>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { apiHost as API_HOST } from '@/api/request'

// ── 角色定义 ──────────────────────────────────────────
const roles = [
  {
    key: 'grower',
    name: '成长者',
    icon: '🌱',
    desc: '改变生活方式，建立健康行为习惯',
    color: '#27AE60',
    bg: '#EAF9F1',
    profileHint: '告诉我们您的健康目标',
  },
  {
    key: 'sharer',
    name: '分享者',
    icon: '🤝',
    desc: '帮助身边的人一起走向健康',
    color: '#3498DB',
    bg: '#EAF4FB',
    profileHint: '您将分享健康经验，帮助他人',
  },
  {
    key: 'coach',
    name: '健康教练',
    icon: '👨‍🏫',
    desc: '专业指导学员实现行为改变',
    color: '#2D8E69',
    bg: '#E8F6EF',
    profileHint: '填写您的专业背景',
  },
  {
    key: 'supervisor',
    name: '督导专家',
    icon: '🔍',
    desc: '督导教练工作，审核健康数据',
    color: '#E67E22',
    bg: '#FEF5EB',
    profileHint: '填写您的专业背景',
  },
]

const genders = [
  { key: 'male', label: '男' },
  { key: 'female', label: '女' },
  { key: 'other', label: '保密' },
]

const healthGoals = ['控制血糖', '减重塑形', '改善睡眠', '降低血压', '增强体能', '戒烟限酒', '减压放松', '整体提升']

const specialties = ['代谢综合征', '糖尿病管理', '运动康复', '营养干预', '心理辅导', '生活方式医学', '老年健康', '青少年健康']

const yearsOptions = ['1年以下', '1-3年', '3-5年', '5-10年', '10年以上']

// ── 状态 ──────────────────────────────────────────────
const step = ref(1)
const agreed = ref(false)
const loading = ref(false)
const errMsg = ref('')
const yearsIdx = ref(0)
const selectedGoals = ref<string[]>([])

const form = ref({
  role: '',
  full_name: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPwd: '',
  gender: '',
  specialty: '',
})

const currentRole = computed(() => roles.find(r => r.key === form.value.role))
const isUserRole = computed(() => ['grower', 'sharer'].includes(form.value.role))
const isProfessionalRole = computed(() => ['coach', 'supervisor', 'master'].includes(form.value.role))

function toggleGoal(g: string) {
  const idx = selectedGoals.value.indexOf(g)
  if (idx >= 0) selectedGoals.value.splice(idx, 1)
  else if (selectedGoals.value.length < 5) selectedGoals.value.push(g)
}

// ── 验证 ──────────────────────────────────────────────
function validateStep(): string {
  const f = form.value
  if (step.value === 1) {
    if (!f.role) return '请选择您的角色'
  }
  if (step.value === 2) {
    if (!f.full_name.trim()) return '请输入真实姓名'
    if (!f.username.trim()) return '请输入用户名'
    if (!/^[a-zA-Z0-9_]{3,30}$/.test(f.username)) return '用户名只能含字母、数字、下划线，3-30位'
    if (!f.email.trim()) return '请输入邮箱'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) return '邮箱格式不正确'
    if (f.phone && !/^1\d{10}$/.test(f.phone)) return '手机号格式不正确'
    if (!f.password) return '请输入密码'
    if (f.password.length < 8) return '密码至少8位'
    if (!/[a-z]/.test(f.password)) return '密码须包含小写字母'
    if (!/[A-Z]/.test(f.password)) return '密码须包含大写字母'
    if (!/[0-9]/.test(f.password)) return '密码须包含数字'
    if (f.password !== f.confirmPwd) return '两次密码不一致'
  }
  return ''
}

function nextStep() {
  errMsg.value = validateStep()
  if (errMsg.value) return
  step.value++
  errMsg.value = ''
}

function handleBack() {
  if (step.value > 1) {
    step.value--
    errMsg.value = ''
  } else {
    goLogin()
  }
}

// ── 注册提交 ──────────────────────────────────────────
async function doRegister() {
  if (!agreed.value) { errMsg.value = '请先同意用户协议和隐私政策'; return }
  if (loading.value) return
  loading.value = true
  errMsg.value = ''

  try {
    const payload: any = {
      username: form.value.username.trim(),
      email: form.value.email.trim(),
      password: form.value.password,
      full_name: form.value.full_name.trim(),
      role: form.value.role,
    }
    if (form.value.phone) payload.phone = form.value.phone
    if (form.value.gender) payload.gender = form.value.gender
    if (selectedGoals.value.length) payload.health_goals = selectedGoals.value.join(',')
    if (form.value.specialty) payload.specialty = form.value.specialty

    const res = await new Promise<any>((resolve, reject) => {
      uni.request({
        url: API_HOST + '/api/v1/auth/register',
        method: 'POST',
        data: payload,
        header: { 'Content-Type': 'application/json' },
        success: (r: any) => {
          if (r.statusCode >= 200 && r.statusCode < 300) resolve(r.data)
          else {
            const detail = r.data?.detail || r.data?.message || `注册失败(${r.statusCode})`
            reject(new Error(typeof detail === 'string' ? detail : JSON.stringify(detail)))
          }
        },
        fail: (e: any) => reject(new Error(e?.errMsg || '网络错误')),
      })
    })

    // 存储 token 和用户信息
    if (res.access_token) {
      uni.setStorageSync('access_token', res.access_token)
      uni.setStorageSync('refresh_token', res.refresh_token || '')
    }
    if (res.user) {
      uni.setStorageSync('user_info', res.user)
    }

    uni.showToast({ title: '注册成功！', icon: 'success', duration: 1500 })
    setTimeout(() => uni.reLaunch({ url: '/pages/home/index' }), 1500)

  } catch (e: any) {
    errMsg.value = e?.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}

function goLogin() {
  uni.redirectTo({ url: '/pages/auth/login' })
}
</script>

<style scoped>
.rg-page { min-height: 100vh; background: #F5F6FA; display: flex; flex-direction: column; }

/* 顶部导航 */
.rg-topbar {
  display: flex; align-items: center; padding: 0 24rpx;
  padding-top: calc(44rpx + env(safe-area-inset-top));
  background: #fff; height: calc(100rpx + env(safe-area-inset-top));
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
  position: sticky; top: 0; z-index: 10;
}
.rg-back { font-size: 40rpx; padding: 16rpx; color: #5B6B7F; }
.rg-steps {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 0;
}
.rg-step-dot {
  width: 44rpx; height: 44rpx; border-radius: 50%;
  background: #E8ECF0; display: flex; align-items: center; justify-content: center;
  z-index: 1; position: relative;
}
.rg-step-dot--active { background: #2D8E69; }
.rg-step-dot--done { background: #A8D5BE; }
.rg-step-num { font-size: 22rpx; font-weight: 700; color: #fff; }
.rg-step-line { flex: 1; height: 4rpx; background: #E8ECF0; max-width: 60rpx; }
.rg-step-line--done { background: #A8D5BE; }

/* 滚动区 */
.rg-scroll { flex: 1; }

/* 卡片 */
.rg-card { margin: 32rpx 24rpx; background: #fff; border-radius: 24rpx; padding: 40rpx 32rpx; box-shadow: 0 8rpx 32rpx rgba(0,0,0,0.06); }
.rg-anim { animation: fadeUp 0.25s ease; }
@keyframes fadeUp { from { opacity:0; transform:translateY(20rpx); } to { opacity:1; transform:none; } }

.rg-card-title { display: block; font-size: 40rpx; font-weight: 700; color: #2C3E50; }
.rg-card-sub { display: block; font-size: 26rpx; color: #8E99A4; margin-top: 8rpx; margin-bottom: 36rpx; }

/* 角色卡片 */
.rg-roles { display: flex; flex-direction: column; gap: 20rpx; margin-bottom: 40rpx; }
.rg-role-item {
  display: flex; align-items: center; gap: 24rpx;
  border: 3rpx solid #E8ECF0; border-radius: 20rpx; padding: 28rpx 24rpx;
  transition: all 0.2s; position: relative;
}
.rg-role-item--active { box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.08); }
.rg-role-icon { font-size: 52rpx; }
.rg-role-info { flex: 1; }
.rg-role-name { display: block; font-size: 30rpx; font-weight: 700; color: #2C3E50; margin-bottom: 6rpx; }
.rg-role-desc { display: block; font-size: 24rpx; color: #8E99A4; line-height: 1.4; }
.rg-role-check { width: 40rpx; height: 40rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.rg-check-mark { font-size: 22rpx; color: #fff; font-weight: 700; }

/* 表单字段 */
.rg-field { margin-bottom: 28rpx; }
.rg-label { display: block; font-size: 26rpx; font-weight: 600; color: #5B6B7F; margin-bottom: 12rpx; }
.rg-input {
  width: 100%; height: 88rpx; border: 2rpx solid #E8ECF0; border-radius: 16rpx;
  padding: 0 24rpx; font-size: 28rpx; color: #2C3E50; background: #FAFBFC;
  box-sizing: border-box;
}
.rg-picker {
  height: 88rpx; border: 2rpx solid #E8ECF0; border-radius: 16rpx;
  padding: 0 24rpx; font-size: 28rpx; color: #2C3E50; background: #FAFBFC;
  display: flex; align-items: center;
}

/* 性别选择 */
.rg-gender-row { display: flex; gap: 16rpx; }
.rg-gender-chip {
  flex: 1; text-align: center; padding: 18rpx 0; border-radius: 14rpx;
  border: 2rpx solid #E8ECF0; font-size: 26rpx; color: #5B6B7F; background: #FAFBFC;
}
.rg-gender-chip--active { font-weight: 600; }

/* 标签选择 */
.rg-tag-row { display: flex; flex-wrap: wrap; gap: 16rpx; }
.rg-tag {
  padding: 14rpx 24rpx; border-radius: 36rpx; border: 2rpx solid #E8ECF0;
  font-size: 24rpx; color: #5B6B7F; background: #FAFBFC;
}
.rg-tag--active { font-weight: 600; }

/* 确认信息 */
.rg-confirm-list { margin-bottom: 32rpx; }
.rg-confirm-row { display: flex; align-items: center; justify-content: space-between; padding: 18rpx 0; border-bottom: 1rpx solid #F0F2F5; }
.rg-confirm-label { font-size: 26rpx; color: #8E99A4; }
.rg-confirm-value { font-size: 26rpx; color: #2C3E50; font-weight: 500; max-width: 340rpx; text-align: right; }
.rg-confirm-badge { font-size: 24rpx; font-weight: 600; padding: 8rpx 20rpx; border-radius: 24rpx; border: 2rpx solid; }

/* 协议勾选 */
.rg-agree-row { display: flex; align-items: center; gap: 12rpx; margin-bottom: 28rpx; }
.rg-checkbox { width: 36rpx; height: 36rpx; border-radius: 8rpx; border: 2rpx solid #BDC3C7; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rg-checkbox--checked { }
.rg-check-icon { font-size: 22rpx; color: #fff; font-weight: 700; }
.rg-agree-text { font-size: 24rpx; color: #8E99A4; }
.rg-agree-link { font-size: 24rpx; font-weight: 600; }

/* 错误提示 */
.rg-error { background: #FFF0F0; border-radius: 12rpx; padding: 16rpx 20rpx; margin-bottom: 20rpx; }
.rg-error text { font-size: 26rpx; color: #E74C3C; }

/* 按钮 */
.rg-next-btn {
  width: 100%; height: 96rpx; background: #2D8E69;
  border-radius: 48rpx; display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 32rpx; font-weight: 700;
  box-shadow: 0 8rpx 24rpx rgba(45,142,105,0.3);
}
.rg-next-btn--sm { flex: 2; width: auto; border-radius: 48rpx; }
.rg-next-btn--disabled { background: #BDC3C7 !important; box-shadow: none; }
.rg-prev-btn {
  flex: 1; height: 96rpx; background: #F0F2F5; border-radius: 48rpx;
  display: flex; align-items: center; justify-content: center;
  font-size: 30rpx; color: #5B6B7F; font-weight: 600;
}
.rg-row-btns { display: flex; gap: 20rpx; margin-top: 8rpx; }

.rg-submit-btn {
  width: 100%; height: 96rpx; border-radius: 48rpx;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 32rpx; font-weight: 700;
  box-shadow: 0 8rpx 24rpx rgba(45,142,105,0.3);
}
.rg-submit-btn--disabled { background: #BDC3C7 !important; box-shadow: none; }
.rg-submit-btn--loading { opacity: 0.7; }

/* 登录链接 */
.rg-login-link { display: flex; justify-content: center; align-items: center; gap: 8rpx; padding: 24rpx; }
.rg-login-text { font-size: 26rpx; color: #8E99A4; }
.rg-login-btn { font-size: 26rpx; color: #2D8E69; font-weight: 600; }
</style>
