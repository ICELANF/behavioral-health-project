<template>
  <div class="portal-page">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <div class="hero-bg" />
      <div class="hero-content">
        <div class="hero-logo">
          <van-icon name="shield-o" size="40" color="#fff" />
        </div>
        <h1 class="hero-title">行为健康数字平台</h1>
        <p class="hero-slogan">科学评估 · 精准干预 · 持续成长</p>
        <div class="hero-tags">
          <span class="hero-tag">AI 驱动</span>
          <span class="hero-tag">专业教练</span>
          <span class="hero-tag">行为处方</span>
        </div>
      </div>
    </div>

    <!-- 已登录快捷入口 -->
    <div v-if="isLoggedIn" class="logged-in-bar" @click="goHome">
      <van-icon name="home-o" size="16" />
      <span>你已登录，进入首页</span>
      <van-icon name="arrow" size="14" />
    </div>

    <!-- 平台简介卡片 -->
    <div class="intro-card">
      <h2 class="section-title">关于平台</h2>
      <p class="intro-text">
        我们通过 AI 行为评估、个性化行为处方和专业教练陪伴，帮助你建立可持续的健康行为模式。
        从观察到行动，从个人到团队，每个人都能找到适合自己的成长路径。
      </p>
      <div class="keyword-tags">
        <span class="keyword-tag">AI 评估</span>
        <span class="keyword-tag">行为处方</span>
        <span class="keyword-tag">教练陪伴</span>
        <span class="keyword-tag">同伴支持</span>
      </div>
    </div>

    <!-- 角色体系 -->
    <div class="roles-section">
      <h2 class="section-title">成长路径</h2>

      <!-- 体验与成长 -->
      <div class="role-group">
        <div class="role-group-header">
          <span class="role-group-label">体验与成长</span>
        </div>
        <div
          v-for="role in experienceRoles"
          :key="role.key"
          class="role-card"
          @click="handleRoleAction(role)"
        >
          <div class="role-left">
            <span class="role-emoji">{{ role.emoji }}</span>
            <span class="role-level" :style="{ background: role.levelBg, color: role.levelColor }">
              {{ role.levelLabel }}
            </span>
          </div>
          <div class="role-center">
            <div class="role-name">{{ role.name }}</div>
            <div class="role-desc">{{ role.desc }}</div>
          </div>
          <button
            class="role-action"
            :class="role.actionClass"
          >
            {{ role.actionText }}
            <van-icon name="arrow" size="12" />
          </button>
        </div>
      </div>

      <!-- 专业服务 -->
      <div class="role-group">
        <div class="role-group-header">
          <span class="role-group-label">专业服务</span>
        </div>
        <div
          v-for="role in professionalRoles"
          :key="role.key"
          class="role-card"
          @click="handleRoleAction(role)"
        >
          <div class="role-left">
            <span class="role-emoji">{{ role.emoji }}</span>
            <span class="role-level" :style="{ background: role.levelBg, color: role.levelColor }">
              {{ role.levelLabel }}
            </span>
          </div>
          <div class="role-center">
            <div class="role-name">{{ role.name }}</div>
            <div class="role-desc">{{ role.desc }}</div>
          </div>
          <button class="role-action role-action--login">
            登录 <van-icon name="arrow" size="12" />
          </button>
        </div>
      </div>

      <!-- 平台管理 -->
      <div class="role-group">
        <div class="role-group-header">
          <span class="role-group-label">平台管理</span>
        </div>
        <div
          class="role-card"
          @click="goLogin"
        >
          <div class="role-left">
            <span class="role-emoji">🔧</span>
            <span class="role-level" style="background:#ffebee;color:#c62828">L99</span>
          </div>
          <div class="role-center">
            <div class="role-name">管理员</div>
            <div class="role-desc">系统管理、数据监控、用户管理</div>
          </div>
          <button class="role-action role-action--login">
            登录 <van-icon name="arrow" size="12" />
          </button>
        </div>
      </div>
    </div>

    <!-- 开发模式快捷入口 -->
    <div v-if="isDev" class="dev-quick-login">
      <div class="dev-header">
        <span class="dev-title">角色切换</span>
        <span class="dev-hint">开发测试专用</span>
      </div>
      <div class="dev-role-group">
        <div class="dev-role-group-label">基础</div>
        <div class="dev-role-buttons">
          <div class="dev-role-btn" @click="quickLogin('observer')">
            <div class="dev-role-icon" style="background:#e8f5e9;color:#43a047">L0</div>
            <span>观察员</span>
          </div>
          <div class="dev-role-btn" @click="quickLogin('grower')">
            <div class="dev-role-icon" style="background:#e3f2fd;color:#1e88e5">L1</div>
            <span>成长者</span>
          </div>
          <div class="dev-role-btn" @click="quickLogin('sharer')">
            <div class="dev-role-icon" style="background:#fff3e0;color:#fb8c00">L2</div>
            <span>分享者</span>
          </div>
        </div>
      </div>
      <div class="dev-role-group">
        <div class="dev-role-group-label">进阶</div>
        <div class="dev-role-buttons">
          <div class="dev-role-btn" @click="quickLogin('coach')">
            <div class="dev-role-icon" style="background:#e8eaf6;color:#5c6bc0">L3</div>
            <span>教练</span>
          </div>
          <div class="dev-role-btn" @click="quickLogin('promoter')">
            <div class="dev-role-icon" style="background:#fce4ec;color:#e53935">L4</div>
            <span>促进师</span>
          </div>
          <div class="dev-role-btn" @click="quickLogin('supervisor')">
            <div class="dev-role-icon" style="background:#f3e5f5;color:#8e24aa">L4</div>
            <span>督导</span>
          </div>
          <div class="dev-role-btn" @click="quickLogin('master')">
            <div class="dev-role-icon" style="background:#fff8e1;color:#f9a825">L5</div>
            <span>大师</span>
          </div>
        </div>
      </div>
      <div class="dev-role-group">
        <div class="dev-role-group-label">管理</div>
        <div class="dev-role-buttons">
          <div class="dev-role-btn" @click="quickLogin('admin')">
            <div class="dev-role-icon" style="background:#ffebee;color:#c62828">99</div>
            <span>管理员</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部 -->
    <div class="portal-footer">
      <div class="footer-links">
        <router-link to="/privacy-policy">隐私政策</router-link>
        <span class="footer-dot">·</span>
        <router-link to="/about-us">关于我们</router-link>
      </div>
      <p class="footer-copy">&copy; 2026 行为健康数字平台</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { showLoadingToast, closeToast, showToast } from 'vant'
import storage from '@/utils/storage'
import { useUserStore } from '@/stores/user'
import api from '@/api/index'

const router = useRouter()
const userStore = useUserStore()
const isDev = import.meta.env.DEV

const isLoggedIn = computed(() => !!storage.getToken())

interface RoleItem {
  key: string
  emoji: string
  levelLabel: string
  levelBg: string
  levelColor: string
  name: string
  desc: string
  actionText: string
  actionClass: string
  target: string
}

const experienceRoles: RoleItem[] = [
  {
    key: 'observer',
    emoji: '👀',
    levelLabel: 'L0',
    levelBg: '#e8f5e9',
    levelColor: '#43a047',
    name: '观察员',
    desc: '无需注册，浏览学习内容、体验AI对话',
    actionText: '免费体验',
    actionClass: 'role-action--observer',
    target: '/home/observer',
  },
  {
    key: 'grower',
    emoji: '🌱',
    levelLabel: 'L1',
    levelBg: '#e3f2fd',
    levelColor: '#1e88e5',
    name: '成长者',
    desc: '个性化行为处方、每日打卡',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
  {
    key: 'sharer',
    emoji: '💬',
    levelLabel: 'L2',
    levelBg: '#fff3e0',
    levelColor: '#fb8c00',
    name: '分享者',
    desc: '分享成长经验，引领新成员入门',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
]

const professionalRoles: RoleItem[] = [
  {
    key: 'coach',
    emoji: '🎯',
    levelLabel: 'L3',
    levelBg: '#e8eaf6',
    levelColor: '#5c6bc0',
    name: '教练',
    desc: '一对一行为健康辅导，带领学习小组',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
  {
    key: 'promoter',
    emoji: '⭐',
    levelLabel: 'L4',
    levelBg: '#fce4ec',
    levelColor: '#e53935',
    name: '促进师',
    desc: '培养教练团队，开发课程内容',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
  {
    key: 'supervisor',
    emoji: '🛡️',
    levelLabel: 'L4',
    levelBg: '#f3e5f5',
    levelColor: '#8e24aa',
    name: '督导',
    desc: '督导教练实践，确保服务质量',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
  {
    key: 'master',
    emoji: '👑',
    levelLabel: 'L5',
    levelBg: '#fff8e1',
    levelColor: '#f9a825',
    name: '大师',
    desc: '推动行为健康事业发展和标准建设',
    actionText: '登录',
    actionClass: 'role-action--login',
    target: '/login',
  },
]

function handleRoleAction(role: RoleItem) {
  router.push(role.target)
}

function goLogin() {
  router.push('/login')
}

function goHome() {
  router.push('/')
}

// ── 开发环境快速登录 ──
const demoAccounts: Record<string, { password: string }> = isDev ? {
  observer:   { password: 'Observer@2026' },
  grower:     { password: 'Grower@2026' },
  sharer:     { password: 'Sharer@2026' },
  coach:      { password: 'Coach@2026' },
  promoter:   { password: 'Promoter@2026' },
  supervisor: { password: 'Supervisor@2026' },
  master:     { password: 'Master@2026' },
  admin:      { password: 'Admin@2026' },
} : {}

async function quickLogin(role: string) {
  if (!isDev) return
  const account = demoAccounts[role]
  if (!account) return

  showLoadingToast({ message: '登录中...', forbidClick: true })
  try {
    const params = new URLSearchParams()
    params.append('username', role)
    params.append('password', account.password)

    const res: any = await api.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    storage.setToken(res.access_token)
    if (res.refresh_token) {
      localStorage.setItem('refresh_token', res.refresh_token)
    }
    if (res.user) {
      storage.setAuthUser(res.user)
      userStore.setUserInfo({
        id: String(res.user.id),
        name: res.user.full_name || res.user.username,
      })
      const ROLE_LEVELS: Record<string, number> = {
        observer: 1, grower: 2, sharer: 3, coach: 4,
        promoter: 5, supervisor: 5, master: 6, admin: 99,
      }
      const userRole = (res.user.role || 'observer').toLowerCase()
      localStorage.setItem('bhp_role_level', String(res.user.role_level || ROLE_LEVELS[userRole] || 1))
    }
    closeToast()
    showToast({ message: '登录成功', type: 'success' })
    router.replace('/')
  } catch (e: any) {
    closeToast()
    showToast(e.response?.data?.detail || '登录失败')
  }
}
</script>

<style scoped>
.portal-page {
  min-height: 100vh;
  background: #f7f8fb;
  padding-bottom: 24px;
}

/* ── Hero ── */
.hero-section {
  position: relative;
  padding: 56px 20px 32px;
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
  text-align: center;
  color: #fff;
}
.hero-logo {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(8px);
}
.hero-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: 1px;
}
.hero-slogan {
  font-size: 14px;
  opacity: 0.85;
  margin: 0 0 16px;
}
.hero-tags {
  display: flex;
  justify-content: center;
  gap: 10px;
}
.hero-tag {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  font-size: 12px;
  backdrop-filter: blur(4px);
}

/* ── 已登录入口 ── */
.logged-in-bar {
  margin: 12px 16px 0;
  padding: 12px 16px;
  background: #e3f2fd;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1565C0;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}
.logged-in-bar .van-icon:last-child {
  margin-left: auto;
}

/* ── 平台简介 ── */
.intro-card {
  margin: 16px 16px 0;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}
.section-title {
  font-size: 17px;
  font-weight: 700;
  color: #222;
  margin: 0 0 12px;
}
.intro-text {
  font-size: 14px;
  color: #555;
  line-height: 1.8;
  margin: 0 0 14px;
}
.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.keyword-tag {
  padding: 4px 12px;
  background: #f0f7ff;
  color: #1565C0;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* ── 角色体系 ── */
.roles-section {
  margin: 20px 16px 0;
}
.roles-section > .section-title {
  margin-bottom: 16px;
}

.role-group {
  margin-bottom: 16px;
}
.role-group-header {
  margin-bottom: 10px;
}
.role-group-label {
  font-size: 13px;
  font-weight: 600;
  color: #888;
  padding-left: 4px;
}

.role-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 14px;
  padding: 14px 14px;
  margin-bottom: 8px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.role-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.role-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-right: 12px;
  flex-shrink: 0;
}
.role-emoji {
  font-size: 28px;
  line-height: 1;
}
.role-level {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 8px;
  white-space: nowrap;
}

.role-center {
  flex: 1;
  min-width: 0;
}
.role-name {
  font-size: 15px;
  font-weight: 600;
  color: #222;
  margin-bottom: 2px;
}
.role-desc {
  font-size: 12px;
  color: #888;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s;
  font-family: inherit;
}
.role-action:active {
  opacity: 0.7;
}

.role-action--observer {
  background: #e8f5e9;
  color: #2e7d32;
}
.role-action--login {
  background: #e3f2fd;
  color: #1565C0;
}

/* ── 开发模式快捷入口 ── */
.dev-quick-login {
  margin: 20px 16px 0;
  background: #fff;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  border: 1px dashed #ddd;
}
.dev-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.dev-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.dev-hint {
  font-size: 11px;
  color: #bbb;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 10px;
}
.dev-role-group {
  margin-bottom: 10px;
}
.dev-role-group:last-child {
  margin-bottom: 0;
}
.dev-role-group-label {
  font-size: 11px;
  color: #bbb;
  margin-bottom: 6px;
  padding-left: 2px;
}
.dev-role-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.dev-role-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px 6px 6px;
  border: 1px solid #eee;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #333;
  font-weight: 500;
}
.dev-role-btn:active {
  background: #f0f7ff;
  border-color: #1989fa;
}
.dev-role-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

/* ── 底部 ── */
.portal-footer {
  margin-top: 32px;
  text-align: center;
  padding: 0 16px;
}
.footer-links {
  font-size: 13px;
  margin-bottom: 8px;
}
.footer-links a {
  color: #1565C0;
  text-decoration: none;
}
.footer-dot {
  margin: 0 8px;
  color: #ccc;
}
.footer-copy {
  font-size: 11px;
  color: #bbb;
  margin: 0;
}
</style>
