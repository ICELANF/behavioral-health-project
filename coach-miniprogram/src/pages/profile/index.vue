<template>
  <view class="prof-page">
    <!-- 个人信息头 -->
    <view class="prof-header">
      <view class="prof-avatar">{{ (userInfo.name || '?')[0] }}</view>
      <view class="prof-info">
        <text class="prof-name">{{ userInfo.name }}</text>
        <text class="prof-role">{{ userInfo.role_label }}</text>
      </view>
      <view class="prof-edit" @tap="editProfile">编辑</view>
    </view>

    <scroll-view scroll-y class="prof-scroll">
      <!-- 个人成就概览 -->
      <view class="prof-stats">
        <view class="prof-stat-item" @tap="goPage('/pages/learning/index')">
          <text class="prof-stat-num">{{ userInfo.learning_credits || 0 }}</text>
          <text class="prof-stat-label">学习积分 ›</text>
        </view>
        <view class="prof-stat-item">
          <text class="prof-stat-num">{{ userInfo.joined_days || 0 }}</text>
          <text class="prof-stat-label">加入天数</text>
        </view>
        <view class="prof-stat-item" @tap="goPage('/pages/profile-extra/certification')">
          <text class="prof-stat-num">{{ userInfo.cert_count || 0 }}</text>
          <text class="prof-stat-label">获得认证 ›</text>
        </view>
      </view>

      <!-- 个人成长（我自己的成就数据） -->
      <view class="prof-section-label">个人成长</view>
      <view class="prof-menu">
        <view class="prof-menu-item" @tap="goPage('/pages/learning/index')">
          <text class="prof-menu-icon">📚</text>
          <text class="prof-menu-text">学习成长</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/profile-extra/performance')">
          <text class="prof-menu-icon">📈</text>
          <text class="prof-menu-text">我的绩效</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/profile-extra/leaderboard')">
          <text class="prof-menu-icon">🏅</text>
          <text class="prof-menu-text">积分排行</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/profile-extra/certification')">
          <text class="prof-menu-icon">🏆</text>
          <text class="prof-menu-text">我的认证</text>
          <text class="prof-menu-arrow">›</text>
        </view>
      </view>

      <!-- 教练工作台（多学员汇总工具，非个人数据） -->
      <view class="prof-section-label">教练工作台</view>
      <view class="prof-menu">
        <view class="prof-menu-item" @tap="goPage('/pages/coach/analytics/index')">
          <text class="prof-menu-icon">📊</text>
          <text class="prof-menu-text">工作数据</text>
          <text class="prof-menu-sub">我的学员汇总</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/coach/assessment/index')">
          <text class="prof-menu-icon">📋</text>
          <text class="prof-menu-text">评估管理</text>
          <text class="prof-menu-sub">学员评估任务</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/coach/promotion/index')">
          <text class="prof-menu-icon">🎖</text>
          <text class="prof-menu-text">晋级申请审核</text>
          <text class="prof-menu-sub">成长者→分享者申请</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="goPage('/pages/coach/contributions/index')">
          <text class="prof-menu-icon">✍️</text>
          <text class="prof-menu-text">内容投稿审核</text>
          <text class="prof-menu-sub">学员投稿的经验分享</text>
          <text class="prof-menu-arrow">›</text>
        </view>
      </view>

      <!-- 系统 -->
      <view class="prof-menu">
        <view class="prof-menu-item" @tap="goPage('/pages/profile-extra/settings')">
          <text class="prof-menu-icon">⚙️</text>
          <text class="prof-menu-text">账号设置</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item" @tap="showAbout">
          <text class="prof-menu-icon">ℹ️</text>
          <text class="prof-menu-text">关于</text>
          <text class="prof-menu-arrow">›</text>
        </view>
        <view class="prof-menu-item prof-menu-item--danger" @tap="doLogout">
          <text class="prof-menu-icon">🚪</text>
          <text class="prof-menu-text" style="color:#E74C3C;">退出登录</text>
          <text class="prof-menu-arrow">›</text>
        </view>
      </view>

      <!-- 版本号 -->
      <view class="prof-version">
        <text>行健平台 v5.0 · 教练版</text>
      </view>

      <view style="height:120rpx;"></view>
    </scroll-view>
  </view>

  <!-- 编辑资料 Modal -->
  <view v-if="showEditModal" class="edit-mask" @tap="showEditModal = false">
    <view class="edit-sheet" @tap.stop>
      <view class="edit-sheet-title">编辑个人资料</view>

      <view class="edit-field">
        <text class="edit-label">姓名</text>
        <input class="edit-input" v-model="editForm.full_name" placeholder="请输入姓名" maxlength="20" />
      </view>

      <view class="edit-field">
        <text class="edit-label">用户名</text>
        <input class="edit-input edit-input--disabled" :value="userInfo.username" disabled placeholder="用户名不可修改" />
      </view>

      <view class="edit-field">
        <text class="edit-label">角色</text>
        <input class="edit-input edit-input--disabled" :value="userInfo.role_label" disabled />
      </view>

      <view class="edit-actions">
        <view class="edit-btn edit-btn--cancel" @tap="showEditModal = false">取消</view>
        <view class="edit-btn edit-btn--save" :class="{ 'edit-btn--saving': saving }" @tap="saveProfile">
          {{ saving ? '保存中…' : '保存' }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { httpReq as http } from '@/api/request'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const userInfo = ref<any>({ name: '教练', role_label: '行为健康教练', username: '' })
const showEditModal = ref(false)
const saving = ref(false)
const editForm = ref({ full_name: '' })

async function loadProfile() {
  try {
    const stored = uni.getStorageSync('user_info')
    if (stored) {
      const u = typeof stored === 'string' ? JSON.parse(stored) : stored
      userInfo.value = {
        name: u.full_name || u.display_name || u.username || u.nickname || '教练',
        role_label: ({ coach:'行为健康教练', promoter:'行为健康促进师', supervisor:'行为健康促进师', master:'行为健康大师', admin:'管理员', sharer:'分享者', grower:'成长者', observer:'观察员' } as Record<string,string>)[(u.role||'').toLowerCase()] || u.role || '用户',
        learning_credits: 0,
        joined_days: 0,
        cert_count: 0,
      }
    }
  } catch (e) { console.warn('[profile/index] loadProfile:', e) }

  // 从后端获取基本信息
  try {
    const res = await http<any>('/api/v1/auth/me')
    if (res) {
      const joinedDays = res.created_at
        ? Math.floor((Date.now() - new Date(res.created_at).getTime()) / 86400000)
        : 0
      userInfo.value = {
        ...userInfo.value,
        name: res.full_name || res.display_name || res.username || userInfo.value.name,
        username: res.username || '',
        role_label: ({ coach:'行为健康教练', promoter:'行为健康促进师', supervisor:'行为健康促进师', master:'行为健康大师', admin:'管理员', sharer:'分享者', grower:'成长者', observer:'观察员' } as Record<string,string>)[(res.role||'').toLowerCase()] || res.role || userInfo.value.role_label,
        joined_days: joinedDays,
      }
    }
  } catch (e) { console.warn('[profile/index] me:', e) }

  // 个人学习积分
  try {
    const credits = await http<any>('/api/v1/learning/credits')
    userInfo.value.learning_credits = credits.total_credits ?? credits.credits ?? 0
  } catch (e) { console.warn('[profile/index] credits:', e) }

  // 获得认证数
  try {
    const sessions = await http<any>('/api/v1/certification/sessions/my?status=passed')
    userInfo.value.cert_count = sessions.total ?? (sessions.items || []).length ?? 0
  } catch (e) { console.warn('[profile/index] certs:', e) }
}

function editProfile() {
  editForm.value.full_name = userInfo.value.name || ''
  showEditModal.value = true
}

async function saveProfile() {
  if (saving.value) return
  const name = editForm.value.full_name.trim()
  if (!name) { uni.showToast({ title: '姓名不能为空', icon: 'none' }); return }
  saving.value = true
  try {
    const res = await http<any>('/api/v1/auth/profile', {
      method: 'PUT',
      data: { full_name: name },
    })
    const savedName: string = (res && res.full_name) ? res.full_name : name
    userInfo.value.name = savedName
    // 同步更新本地缓存（非关键，单独容错）
    try {
      const stored = uni.getStorageSync('user_info')
      if (stored) {
        const u = typeof stored === 'string' ? JSON.parse(stored) : stored
        u.full_name = savedName
        uni.setStorageSync('user_info', JSON.stringify(u))
      }
    } catch (e2) { console.warn('[profile] storage sync:', e2) }
    showEditModal.value = false
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e) {
    console.error('[profile] saveProfile error:', e)
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function goPage(url: string) {
  uni.navigateTo({ url })
}

function showAbout() {
  uni.showModal({
    title: '关于',
    content: '行健平台 v5.0\n行为健康促进与慢病逆转\n\n© 2026 BehaviorOS',
    showCancel: false,
  })
}

function doLogout() {
  uni.showModal({
    title: '确认退出',
    content: '退出后需要重新登录',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()               // 清除 access_token / refresh_token / user_info
        uni.reLaunch({ url: '/pages/auth/login' })
      }
    }
  })
}

onShow(() => { loadProfile() })
</script>

<style scoped>
.prof-page { min-height: 100vh; background: #F5F6FA; }
.prof-header {
  display: flex; align-items: center; gap: 20rpx;
  padding: 32rpx; padding-top: calc(80rpx + env(safe-area-inset-top));
  background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%);
  color: #fff;
}
.prof-avatar { width: 96rpx; height: 96rpx; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 40rpx; font-weight: 700; }
.prof-info { flex: 1; }
.prof-name { display: block; font-size: 36rpx; font-weight: 700; }
.prof-role { display: block; font-size: 24rpx; opacity: 0.85; margin-top: 4rpx; }
.prof-edit { font-size: 24rpx; padding: 8rpx 20rpx; background: rgba(255,255,255,0.2); border-radius: 8rpx; }

.prof-scroll { height: calc(100vh - 240rpx); }

.prof-stats { display: flex; margin: 24rpx; background: #fff; border-radius: 16rpx; padding: 24rpx 0; }
.prof-stat-item { flex: 1; text-align: center; border-right: 1rpx solid #F0F0F0; }
.prof-stat-item:last-child { border-right: none; }
.prof-stat-num { display: block; font-size: 40rpx; font-weight: 700; color: #2D8E69; }
.prof-stat-label { display: block; font-size: 22rpx; color: #8E99A4; margin-top: 4rpx; }

.prof-menu { margin: 0 24rpx 24rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.prof-menu-item { display: flex; align-items: center; gap: 16rpx; padding: 28rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.prof-menu-item:last-child { border-bottom: none; }
.prof-menu-icon { font-size: 32rpx; }
.prof-menu-text { flex: 1; font-size: 28rpx; color: #2C3E50; }
.prof-menu-arrow { font-size: 28rpx; color: #CCC; }

.prof-section-label { font-size: 22rpx; color: #8E99A4; padding: 8rpx 24rpx 4rpx; font-weight: 500; letter-spacing: 2rpx; }
.prof-menu-sub { font-size: 20rpx; color: #BDC3C7; margin-left: 4rpx; }

.prof-version { text-align: center; padding: 32rpx; font-size: 24rpx; color: #BDC3C7; }

/* 编辑 Modal */
.edit-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: flex-end; }
.edit-sheet { width: 100%; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 40rpx 32rpx calc(48rpx + env(safe-area-inset-bottom)); }
.edit-sheet-title { font-size: 34rpx; font-weight: 700; color: #2C3E50; text-align: center; margin-bottom: 40rpx; }
.edit-field { margin-bottom: 32rpx; }
.edit-label { display: block; font-size: 28rpx; color: #5B6B7F; margin-bottom: 12rpx; font-weight: 500; }
.edit-input { width: 100%; padding: 16rpx 24rpx; background: #F5F6FA; border-radius: 12rpx; font-size: 28rpx; color: #2C3E50; box-sizing: border-box; }
.edit-input--disabled { color: #BDC3C7; }
.edit-actions { display: flex; gap: 20rpx; margin-top: 40rpx; }
.edit-btn { flex: 1; text-align: center; padding: 26rpx 0; border-radius: 16rpx; font-size: 30rpx; font-weight: 600; }
.edit-btn--cancel { background: #F0F0F0; color: #5B6B7F; }
.edit-btn--save { background: #2D8E69; color: #fff; }
.edit-btn--saving { background: #8DC9B3; }
</style>