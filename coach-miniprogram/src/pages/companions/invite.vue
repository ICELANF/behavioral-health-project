<template>
  <view class="inv-page">
    <scroll-view scroll-y class="inv-scroll">
      <view class="inv-intro">
        <text class="inv-intro-icon">🤝</text>
        <text class="inv-intro-title">邀请同道者</text>
        <text class="inv-intro-sub">邀请志同道合的朋友一起行健成长</text>
      </view>

      <!-- 搜索用户 -->
      <view class="inv-search-section">
        <text class="inv-label">搜索用户</text>
        <view class="inv-search-bar">
          <input class="inv-search-input" v-model="searchText"
            placeholder="输入用户名或姓名" @confirm="searchUser" />
          <view class="inv-search-btn" @tap="searchUser">
            <text>搜索</text>
          </view>
        </view>
      </view>

      <!-- 搜索结果 -->
      <view v-if="searchResults.length > 0" class="inv-results">
        <view v-for="user in searchResults" :key="user.id" class="inv-user-card">
          <view class="inv-user-avatar" :style="{ background: avatarColor(user.name || user.username) }">
            {{ (user.name || user.username || '?')[0] }}
          </view>
          <view class="inv-user-info">
            <text class="inv-user-name">{{ user.name || user.username }}</text>
            <text class="inv-user-level">{{ levelName(user.level) }}</text>
          </view>
          <view class="inv-send-btn" @tap="sendInvite(user)">
            <text>邀请</text>
          </view>
        </view>
      </view>

      <!-- 邀请消息 -->
      <view class="inv-message-section">
        <text class="inv-label">邀请消息（可选）</text>
        <textarea class="inv-message-input" v-model="message"
          placeholder="写一段邀请语..." :maxlength="200" />
      </view>

      <!-- 操作说明 -->
      <view class="inv-tips">
        <text class="inv-tips-title">什么是同道者？</text>
        <text class="inv-tips-text">同道者是互相监督、共同进步的健康伙伴。建立同道关系后，你们可以互相查看进度、互相鼓励。</text>
      </view>

      <view style="height:80rpx;"></view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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

const searchText = ref('')
const message = ref('我邀请你成为我的同道者，一起健康成长！')
const searchResults = ref<any[]>([])

const colorPool = ['#3498DB','#E74C3C','#27AE60','#9B59B6','#E67E22','#1ABC9C']
function avatarColor(name: string): string {
  if (!name) return '#8E99A4'
  let h = 0; for (const c of name) h = c.charCodeAt(0) + ((h << 5) - h)
  return colorPool[Math.abs(h) % colorPool.length]
}
function levelName(k: string) { return { observer:'观察者', grower:'成长者', sharer:'分享者' }[k] || (k || '用户') }

async function searchUser() {
  if (!searchText.value.trim()) return
  try {
    const res = await http<any>(`/api/v1/users/search?q=${encodeURIComponent(searchText.value)}`)
    searchResults.value = res?.items || []
    if (!searchResults.value.length) uni.showToast({ title: '未找到该用户', icon: 'none' })
  } catch {
    uni.showToast({ title: '搜索失败', icon: 'none' })
    searchResults.value = []
  }
}

async function sendInvite(user: any) {
  try {
    await http('/api/v1/companions/invite', {
      method: 'POST',
      data: { user_id: user.id, message: message.value }
    })
    uni.showToast({ title: '邀请已发送', icon: 'success' })
    searchResults.value = searchResults.value.filter(u => u.id !== user.id)
  } catch {
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}
</script>

<style scoped>
.inv-page { min-height: 100vh; background: #F5F6FA; }
.inv-scroll { height: 100vh; }

.inv-intro { text-align: center; background: linear-gradient(135deg, #2D8E69 0%, #3BAF7C 100%); padding: 48rpx 32rpx; color: #fff; padding-top: calc(48rpx + env(safe-area-inset-top)); }
.inv-intro-icon { display: block; font-size: 64rpx; margin-bottom: 16rpx; }
.inv-intro-title { display: block; font-size: 36rpx; font-weight: 700; margin-bottom: 8rpx; }
.inv-intro-sub { display: block; font-size: 24rpx; opacity: 0.85; }

.inv-search-section, .inv-message-section { background: #fff; margin: 16rpx 24rpx; border-radius: 16rpx; padding: 20rpx 24rpx; }
.inv-label { display: block; font-size: 26rpx; font-weight: 600; color: #2C3E50; margin-bottom: 12rpx; }
.inv-search-bar { display: flex; gap: 12rpx; }
.inv-search-input { flex: 1; background: #F5F6FA; border-radius: 12rpx; padding: 14rpx 20rpx; font-size: 28rpx; }
.inv-search-btn { background: #2D8E69; color: #fff; border-radius: 12rpx; padding: 14rpx 24rpx; font-size: 26rpx; white-space: nowrap; }
.inv-message-input { width: 100%; min-height: 120rpx; background: #F5F6FA; border-radius: 12rpx; padding: 14rpx; font-size: 26rpx; color: #2C3E50; box-sizing: border-box; }

.inv-results { margin: 0 24rpx 16rpx; background: #fff; border-radius: 16rpx; padding: 8rpx 0; }
.inv-user-card { display: flex; align-items: center; gap: 16rpx; padding: 16rpx 24rpx; border-bottom: 1rpx solid #F8F8F8; }
.inv-user-card:last-child { border-bottom: none; }
.inv-user-avatar { width: 72rpx; height: 72rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 28rpx; font-weight: 700; flex-shrink: 0; }
.inv-user-info { flex: 1; }
.inv-user-name { display: block; font-size: 28rpx; font-weight: 600; color: #2C3E50; }
.inv-user-level { font-size: 22rpx; color: #8E99A4; }
.inv-send-btn { background: #2D8E69; color: #fff; border-radius: 10rpx; padding: 8rpx 20rpx; font-size: 24rpx; }

.inv-tips { margin: 0 24rpx; background: #EEF4FF; border-radius: 16rpx; padding: 20rpx 24rpx; }
.inv-tips-title { display: block; font-size: 24rpx; font-weight: 700; color: #3498DB; margin-bottom: 8rpx; }
.inv-tips-text { font-size: 22rpx; color: #5B6B7F; line-height: 1.6; }
</style>
