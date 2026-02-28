<template>
  <view class="settings-page">

    <!-- 个人资料 -->
    <view class="settings-section px-4">
      <text class="settings-section__title">个人资料</text>
      <view class="settings-card bhp-card bhp-card--flat">

        <!-- 头像 -->
        <view class="settings-item" @tap="changeAvatar">
          <text class="settings-item__label">头像</text>
          <view class="settings-item__right">
            <view class="settings-avatar">
              <text class="settings-avatar__text">{{ displayInitial }}</text>
            </view>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>

        <!-- 显示名 -->
        <view class="settings-item" @tap="editName">
          <text class="settings-item__label">显示名称</text>
          <view class="settings-item__right">
            <text class="settings-item__value">{{ userStore.displayName }}</text>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>

        <!-- 用户名 -->
        <view class="settings-item settings-item--readonly">
          <text class="settings-item__label">用户名</text>
          <view class="settings-item__right">
            <text class="settings-item__value text-tertiary-color">{{ userStore.userInfo?.username || '—' }}</text>
          </view>
        </view>

        <!-- 邮箱 -->
        <view class="settings-item settings-item--readonly">
          <text class="settings-item__label">邮箱</text>
          <view class="settings-item__right">
            <text class="settings-item__value text-tertiary-color">{{ userStore.userInfo?.email || '未绑定' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 安全设置 -->
    <view class="settings-section px-4">
      <text class="settings-section__title">安全设置</text>
      <view class="settings-card bhp-card bhp-card--flat">

        <view class="settings-item" @tap="showChangePassword = true">
          <text class="settings-item__label">修改密码</text>
          <view class="settings-item__right">
            <text class="settings-item__hint text-tertiary-color">建议定期更换</text>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>

        <view class="settings-item" @tap="onWxBind">
          <text class="settings-item__label">微信绑定</text>
          <view class="settings-item__right">
            <view class="settings-badge" :class="wxBound ? 'settings-badge--on' : 'settings-badge--off'">
              <text>{{ wxBound ? '已绑定' : '未绑定' }}</text>
            </view>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 通知设置 -->
    <view class="settings-section px-4">
      <text class="settings-section__title">通知设置</text>
      <view class="settings-card bhp-card bhp-card--flat">
        <view class="settings-item" v-for="notif in notifItems" :key="notif.key">
          <text class="settings-item__label">{{ notif.label }}</text>
          <switch
            :checked="notif.enabled"
            color="var(--bhp-primary-500)"
            @change="toggleNotif(notif)"
          />
        </view>
      </view>
    </view>

    <!-- 关于 -->
    <view class="settings-section px-4">
      <text class="settings-section__title">关于</text>
      <view class="settings-card bhp-card bhp-card--flat">
        <view class="settings-item settings-item--readonly">
          <text class="settings-item__label">版本号</text>
          <text class="settings-item__value text-tertiary-color">v1.0.0</text>
        </view>
        <view class="settings-item" @tap="clearCache">
          <text class="settings-item__label">清除缓存</text>
          <view class="settings-item__right">
            <text class="settings-item__hint text-tertiary-color">{{ cacheSize }}</text>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>
        <view class="settings-item" @tap="onPrivacy">
          <text class="settings-item__label">隐私政策</text>
          <text class="settings-item__arrow">›</text>
        </view>
      </view>
    </view>

    <!-- 退出登录 -->
    <view class="settings-logout px-4">
      <view class="settings-logout__btn" @tap="handleLogout">
        <text>退出登录</text>
      </view>
    </view>

    <!-- 注销账号（危险操作，隐藏在最下方） -->
    <view class="settings-danger px-4">
      <text class="settings-danger__link" @tap="onDeactivate">注销账号</text>
    </view>

    <!-- 修改密码弹窗 -->
    <view class="pwd-overlay" v-if="showChangePassword" @tap.self="showChangePassword = false">
      <view class="pwd-modal">
        <text class="pwd-modal__title">修改密码</text>

        <view class="pwd-modal__field">
          <text class="pwd-modal__label">当前密码</text>
          <input
            class="pwd-modal__input"
            v-model="pwdForm.old"
            type="text"
            password
            placeholder="请输入当前密码"
            placeholder-class="pwd-input-placeholder"
          />
        </view>
        <view class="pwd-modal__field">
          <text class="pwd-modal__label">新密码</text>
          <input
            class="pwd-modal__input"
            v-model="pwdForm.new1"
            type="text"
            password
            placeholder="至少8位，含字母和数字"
            placeholder-class="pwd-input-placeholder"
          />
        </view>
        <view class="pwd-modal__field">
          <text class="pwd-modal__label">确认新密码</text>
          <input
            class="pwd-modal__input"
            v-model="pwdForm.new2"
            type="text"
            password
            placeholder="再次输入新密码"
            placeholder-class="pwd-input-placeholder"
          />
        </view>

        <view class="pwd-modal__actions">
          <view class="pwd-modal__cancel" @tap="showChangePassword = false">
            <text>取消</text>
          </view>
          <view
            class="pwd-modal__confirm"
            :class="{ 'pwd-modal__confirm--active': canSubmitPwd }"
            @tap="submitPassword"
          >
            <text v-if="!changingPwd">确认修改</text>
            <text v-else>修改中...</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 修改昵称弹窗 -->
    <view class="name-overlay" v-if="showEditName" @tap.self="showEditName = false">
      <view class="name-modal">
        <text class="name-modal__title">修改显示名称</text>
        <input
          class="name-modal__input"
          v-model="newName"
          type="text"
          placeholder="输入新名称"
          placeholder-class="pwd-input-placeholder"
          maxlength="20"
        />
        <view class="pwd-modal__actions">
          <view class="pwd-modal__cancel" @tap="showEditName = false">
            <text>取消</text>
          </view>
          <view
            class="pwd-modal__confirm"
            :class="{ 'pwd-modal__confirm--active': newName.trim() }"
            @tap="submitName"
          >
            <text v-if="!savingName">保存</text>
            <text v-else>保存中...</text>
          </view>
        </view>
      </view>
    </view>

    <view style="height: 40rpx"></view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import { profileApi } from '@/api/profile'

const userStore = useUserStore()

// ─── 计算 ─────────────────────────────────────────────────────
const displayInitial = computed(() =>
  (userStore.userInfo?.full_name || userStore.userInfo?.username || '用')[0]
)
const wxBound = computed(() => !!(
  userStore.userInfo?.wx_openid || userStore.userInfo?.wx_miniprogram_openid
))

// ─── 通知设置 ─────────────────────────────────────────────────
const notifItems = reactive([
  { key: 'learning',  label: '学习提醒', enabled: true },
  { key: 'companion', label: '同道消息', enabled: true },
  { key: 'promotion', label: '晋级通知', enabled: true },
])

function toggleNotif(item: typeof notifItems[0]) {
  item.enabled = !item.enabled
  uni.showToast({ title: item.enabled ? '已开启' : '已关闭', icon: 'none' })
}

// ─── 修改密码 ─────────────────────────────────────────────────
const showChangePassword = ref(false)
const changingPwd = ref(false)
const pwdForm = reactive({ old: '', new1: '', new2: '' })

const canSubmitPwd = computed(() =>
  pwdForm.old.length >= 1 && pwdForm.new1.length >= 8 && pwdForm.new1 === pwdForm.new2
)

async function submitPassword() {
  if (!canSubmitPwd.value || changingPwd.value) return
  if (pwdForm.new1 !== pwdForm.new2) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }
  changingPwd.value = true
  try {
    await profileApi.changePassword({ old_password: pwdForm.old, new_password: pwdForm.new1 })
    uni.showToast({ title: '密码修改成功', icon: 'success' })
    showChangePassword.value = false
    pwdForm.old = pwdForm.new1 = pwdForm.new2 = ''
  } catch (e: any) {
    const msg = e?.data?.detail || '修改失败，请检查当前密码'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    changingPwd.value = false
  }
}

// ─── 修改昵称 ─────────────────────────────────────────────────
const showEditName = ref(false)
const newName = ref('')
const savingName = ref(false)

function editName() {
  newName.value = userStore.userInfo?.full_name || ''
  showEditName.value = true
}

async function submitName() {
  if (!newName.value.trim() || savingName.value) return
  savingName.value = true
  try {
    await profileApi.updateProfile({ full_name: newName.value.trim() })
    await userStore.refreshUserInfo()
    uni.showToast({ title: '名称已更新', icon: 'success' })
    showEditName.value = false
  } catch (e: any) {
    uni.showToast({ title: e?.data?.detail || '更新失败', icon: 'none' })
  } finally {
    savingName.value = false
  }
}

// ─── 其他操作 ─────────────────────────────────────────────────
const cacheSize = ref('计算中...')

function changeAvatar() {
  uni.showToast({ title: '头像功能开发中', icon: 'none' })
}

function onWxBind() {
  if (wxBound.value) {
    uni.showToast({ title: '微信已绑定', icon: 'none' })
  } else {
    uni.showToast({ title: '绑定功能开发中', icon: 'none' })
  }
}

function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '将清除本地缓存数据，不影响账号数据。确认清除吗？',
    success: (res) => {
      if (res.confirm) {
        try {
          const keys = ['bhp_user_info']
          keys.forEach(k => uni.removeStorageSync(k))
          cacheSize.value = '0KB'
          uni.showToast({ title: '缓存已清除', icon: 'success' })
        } catch {
          uni.showToast({ title: '清除失败', icon: 'none' })
        }
      }
    }
  })
}

function onPrivacy() {
  uni.showToast({ title: '隐私政策页面开发中', icon: 'none' })
}

function onDeactivate() {
  uni.showModal({
    title: '注销账号',
    content: '注销后所有数据将永久删除，无法恢复。如需帮助请联系管理员。',
    confirmText: '联系管理员',
    success: (res) => {
      if (res.confirm) uni.showToast({ title: '请联系平台客服', icon: 'none' })
    }
  })
}

function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmText: '退出',
    confirmColor: '#ef4444',
    success: async (res) => {
      if (res.confirm) await userStore.logout()
    }
  })
}
</script>

<style scoped>
.settings-page { background: var(--surface-secondary); min-height: 100vh; }

/* section */
.settings-section { padding-top: 20rpx; }
.settings-section__title {
  display: block;
  font-size: 24rpx; font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 10rpx;
  padding-left: 4rpx;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.settings-card { overflow: hidden; }

/* item */
.settings-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 28rpx 24rpx;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
}
.settings-item:last-child { border-bottom: none; }
.settings-item:active:not(.settings-item--readonly) { background: var(--surface-secondary); }
.settings-item--readonly { cursor: default; }

.settings-item__label { font-size: 28rpx; color: var(--text-primary); }
.settings-item__right { display: flex; align-items: center; gap: 12rpx; }
.settings-item__value { font-size: 26rpx; }
.settings-item__hint  { font-size: 24rpx; }
.settings-item__arrow { font-size: 32rpx; color: var(--text-tertiary); }

/* 头像缩略图 */
.settings-avatar {
  width: 56rpx; height: 56rpx;
  border-radius: 50%;
  background: var(--bhp-primary-100, #d1fae5);
  display: flex; align-items: center; justify-content: center;
}
.settings-avatar__text { font-size: 26rpx; color: var(--bhp-primary-700, #047857); font-weight: 700; }

/* badge */
.settings-badge {
  font-size: 20rpx; font-weight: 600;
  padding: 4rpx 14rpx;
  border-radius: var(--radius-full);
}
.settings-badge--on  { background: var(--bhp-success-50, #f0fdf4); color: var(--bhp-success-600, #16a34a); }
.settings-badge--off { background: var(--bhp-gray-100); color: var(--text-tertiary); }

/* 退出 */
.settings-logout { padding-top: 32rpx; }
.settings-logout__btn {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 28rpx;
  text-align: center;
  font-size: 28rpx; color: var(--bhp-error-500, #ef4444); font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border-light);
}
.settings-logout__btn:active { opacity: 0.75; }

/* 注销 */
.settings-danger { padding-top: 16rpx; text-align: center; }
.settings-danger__link {
  font-size: 24rpx; color: var(--text-tertiary);
  text-decoration: underline;
  cursor: pointer;
}

/* ── 修改密码弹窗 ── */
.pwd-overlay, .name-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  padding: 0 48rpx;
}

.pwd-modal, .name-modal {
  background: var(--surface);
  border-radius: var(--radius-xl, 24rpx);
  padding: 40rpx 32rpx;
  width: 100%;
}

.pwd-modal__title, .name-modal__title {
  display: block;
  font-size: 32rpx; font-weight: 700;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 32rpx;
}

.pwd-modal__field { margin-bottom: 20rpx; }
.pwd-modal__label {
  display: block;
  font-size: 24rpx; color: var(--text-secondary);
  margin-bottom: 8rpx;
}
.pwd-modal__input, .name-modal__input {
  width: 100%;
  height: 72rpx;
  background: var(--bhp-gray-50, #f9fafb);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0 20rpx;
  font-size: 28rpx;
  color: var(--text-primary);
  box-sizing: border-box;
}
.name-modal__input { margin-bottom: 24rpx; }
.pwd-input-placeholder { color: var(--text-tertiary); font-size: 26rpx; }

.pwd-modal__actions {
  display: flex; gap: 16rpx;
  margin-top: 32rpx;
}
.pwd-modal__cancel {
  flex: 1;
  height: 80rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-100);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; color: var(--text-secondary);
  cursor: pointer;
}
.pwd-modal__confirm {
  flex: 1;
  height: 80rpx;
  border-radius: var(--radius-lg);
  background: var(--bhp-gray-200);
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; color: var(--text-tertiary); font-weight: 600;
}
.pwd-modal__confirm--active {
  background: var(--bhp-primary-500);
  color: #fff;
  cursor: pointer;
}
.pwd-modal__confirm--active:active { opacity: 0.8; }
</style>
