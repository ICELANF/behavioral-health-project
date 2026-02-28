<template>
  <view class="cm-page">

    <!-- 导航栏 -->
    <view class="cm-navbar">
      <view class="cm-navbar__back" @tap="goBack"><text class="cm-navbar__arrow">&#8249;</text></view>
      <text class="cm-navbar__title">{{ chatStudent ? chatStudent.name : '消息中心' }}</text>
      <view class="cm-navbar__action" v-if="chatStudent" @tap="exitChat">
        <text class="cm-navbar__action-text">返回列表</text>
      </view>
      <view class="cm-navbar__placeholder" v-else></view>
    </view>

    <!-- ═══════════ 会话列表视图 ═══════════ -->
    <template v-if="!chatStudent">

      <!-- 搜索 -->
      <view class="cm-search">
        <view class="cm-search__box">
          <text class="cm-search__icon">🔍</text>
          <input class="cm-search__input" placeholder="搜索学员" :value="keyword" @input="onSearch" />
          <text v-if="keyword" class="cm-search__clear" @tap="keyword = ''">✕</text>
        </view>
      </view>

      <!-- Tab -->
      <view class="cm-tabs">
        <view v-for="tab in CONV_TABS" :key="tab.key" class="cm-tab" :class="{ 'cm-tab--active': convTab === tab.key }" @tap="convTab = tab.key">
          <text>{{ tab.label }}</text>
          <view class="cm-tab__badge" v-if="tab.key === 'unread' && unreadTotal > 0"><text>{{ unreadTotal > 99 ? '99+' : unreadTotal }}</text></view>
        </view>
      </view>

      <!-- 会话列表 -->
      <scroll-view scroll-y class="cm-body" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
        <template v-if="loading && !conversations.length">
          <view class="bhp-skeleton" v-for="i in 5" :key="i" style="height: 120rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
        </template>

        <template v-else-if="filteredConversations.length">
          <view v-for="conv in filteredConversations" :key="conv.student_id" class="cm-conv" @tap="openChat(conv)">
            <view class="cm-conv__avatar-wrap">
              <image class="cm-conv__avatar" :src="conv.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
              <view class="cm-conv__online" v-if="conv.is_online"></view>
            </view>
            <view class="cm-conv__body">
              <view class="cm-conv__row1">
                <text class="cm-conv__name">{{ conv.name }}</text>
                <text class="cm-conv__time">{{ formatTime(conv.last_message_at) }}</text>
              </view>
              <view class="cm-conv__row2">
                <text class="cm-conv__preview">{{ conv.last_message || '暂无消息' }}</text>
                <view class="cm-conv__unread" v-if="conv.unread_count > 0">
                  <text>{{ conv.unread_count > 99 ? '99+' : conv.unread_count }}</text>
                </view>
              </view>
              <view class="cm-conv__tags">
                <view class="cm-conv__tag cm-conv__tag--risk" v-if="conv.risk_level && conv.risk_level !== 'low'" :class="`cm-conv__tag--${conv.risk_level}`">
                  <text>{{ RISK_LABEL[conv.risk_level] || conv.risk_level }}</text>
                </view>
                <view class="cm-conv__tag cm-conv__tag--stage" v-if="conv.ttm_stage">
                  <text>{{ TTM_LABEL[conv.ttm_stage] || conv.ttm_stage }}</text>
                </view>
              </view>
            </view>
          </view>
        </template>

        <view v-else class="cm-empty">
          <text class="cm-empty__icon">💬</text>
          <text class="cm-empty__text">暂无会话</text>
          <text class="cm-empty__sub">您的学员消息将显示在这里</text>
        </view>
      </scroll-view>
    </template>

    <!-- ═══════════ 聊天视图 ═══════════ -->
    <template v-else>

      <!-- 学员信息条 -->
      <view class="cm-chat-header">
        <view class="cm-chat-header__info">
          <image class="cm-chat-header__avatar" :src="chatStudent.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
          <view>
            <text class="cm-chat-header__name">{{ chatStudent.name }}</text>
            <view class="cm-chat-header__tags">
              <view class="cm-conv__tag cm-conv__tag--risk" v-if="chatStudent.risk_level && chatStudent.risk_level !== 'low'" :class="`cm-conv__tag--${chatStudent.risk_level}`">
                <text>{{ RISK_LABEL[chatStudent.risk_level] || '' }}</text>
              </view>
              <view class="cm-conv__tag cm-conv__tag--stage" v-if="chatStudent.ttm_stage">
                <text>{{ TTM_LABEL[chatStudent.ttm_stage] || '' }}</text>
              </view>
            </view>
          </view>
        </view>
        <view class="cm-chat-header__actions">
          <view class="cm-header-btn" @tap="goStudentDetail"><text>查看详情</text></view>
        </view>
      </view>

      <!-- 消息列表 -->
      <scroll-view scroll-y class="cm-chat-body" :scroll-into-view="scrollAnchor" scroll-with-animation>
        <template v-if="msgLoading">
          <view class="bhp-skeleton" v-for="i in 3" :key="i" style="height: 80rpx; border-radius: var(--radius-lg); margin-bottom: 12rpx;"></view>
        </template>

        <view v-if="messages.length" class="cm-msg-list">
          <view v-for="(msg, idx) in messages" :key="msg.id || idx" :id="'msg-' + idx"
            class="cm-msg" :class="{ 'cm-msg--self': msg.sender === 'coach', 'cm-msg--system': msg.sender === 'system' }">

            <!-- 时间分割线 -->
            <view class="cm-msg__time-sep" v-if="showTimeSep(idx)">
              <text>{{ formatFullTime(msg.created_at) }}</text>
            </view>

            <!-- 系统消息 -->
            <view v-if="msg.sender === 'system'" class="cm-msg__system">
              <text>{{ msg.content }}</text>
            </view>

            <!-- 普通消息 -->
            <template v-else>
              <image v-if="msg.sender !== 'coach'" class="cm-msg__avatar"
                :src="chatStudent.avatar_url || '/static/default-avatar.png'" mode="aspectFill" />
              <view class="cm-msg__bubble" :class="`cm-msg__bubble--${msg.type || 'text'}`">
                <!-- AI推荐卡片 -->
                <view v-if="msg.type === 'ai_card'" class="cm-msg__ai-card">
                  <text class="cm-msg__ai-label">🤖 AI建议</text>
                  <text class="cm-msg__ai-content">{{ msg.content }}</text>
                  <view class="cm-msg__ai-actions" v-if="msg.sender === 'coach'">
                    <text class="cm-msg__ai-tag">已发送给学员</text>
                  </view>
                </view>
                <!-- 普通文本 -->
                <text v-else class="cm-msg__text">{{ msg.content }}</text>
              </view>
              <image v-if="msg.sender === 'coach'" class="cm-msg__avatar"
                :src="'/static/default-avatar.png'" mode="aspectFill" />
            </template>
          </view>
        </view>

        <view v-else-if="!msgLoading" class="cm-empty cm-empty--chat">
          <text class="cm-empty__icon">📝</text>
          <text class="cm-empty__text">暂无消息记录</text>
          <text class="cm-empty__sub">发送第一条消息开始沟通</text>
        </view>
      </scroll-view>

      <!-- 快捷回复 -->
      <view class="cm-quick" v-if="showQuickReply">
        <scroll-view scroll-x class="cm-quick__scroll">
          <view class="cm-quick__list">
            <view v-for="(tpl, i) in QUICK_REPLIES" :key="i" class="cm-quick__item" @tap="useQuickReply(tpl)">
              <text>{{ tpl }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 输入区 -->
      <view class="cm-input-bar">
        <view class="cm-input-bar__quick-toggle" @tap="showQuickReply = !showQuickReply">
          <text>{{ showQuickReply ? '⌨' : '⚡' }}</text>
        </view>
        <view class="cm-input-bar__wrap">
          <input class="cm-input-bar__input" v-model="inputText" placeholder="输入消息..."
            :adjust-position="true" confirm-type="send" @confirm="sendMessage" />
        </view>
        <view class="cm-input-bar__send" :class="{ 'cm-input-bar__send--active': inputText.trim() }" @tap="sendMessage">
          <text>发送</text>
        </view>
      </view>
    </template>

  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'

// ============================================================
// 内联 HTTP (分包零依赖)
// ============================================================
const BASE_URL = 'http://localhost:8000/api'

function _request<T = any>(method: 'GET' | 'POST', path: string, data?: any): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('access_token') || ''
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    const url = `${BASE_URL}/${path.replace(/^\//, '')}`
    uni.request({
      url, method, data, header: headers,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data as T)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('access_token'); uni.removeStorageSync('refresh_token'); uni.removeStorageSync('user_info')
          uni.reLaunch({ url: '/pages/auth/login' }); reject(new Error('Session expired'))
        } else {
          reject({ statusCode: res.statusCode, data: res.data })
        }
      },
      fail(err) { reject(err) },
    })
  })
}
function _get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
  if (params && Object.keys(params).length) {
    const qs = Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
    path = `${path}?${qs}`
  }
  return _request<T>('GET', path)
}
function _post<T = any>(path: string, data?: any): Promise<T> { return _request<T>('POST', path, data) }

// ============================================================
// 常量
// ============================================================
const CONV_TABS = [
  { key: 'all',    label: '全部' },
  { key: 'unread', label: '未读' },
  { key: 'high',   label: '高风险' },
]

const RISK_LABEL: Record<string, string> = {
  high: '高风险', medium: '中风险', low: '低风险',
  R4: '高危', R3: '警惕', R2: '关注', R1: '正常',
}
const TTM_LABEL: Record<string, string> = {
  precontemplation: '前意向', contemplation: '意向',
  preparation: '准备', action: '行动',
  maintenance: '维持', termination: '终止',
}

const QUICK_REPLIES = [
  '收到，我来看看你的数据',
  '今天的微行动完成了吗？',
  '坚持得很好，继续保持！',
  '有什么不舒服的可以随时告诉我',
  '建议今天早点休息',
  '记得按时服药哦',
  '明天我们聊聊这周的情况',
]

// ============================================================
// 状态 — 会话列表
// ============================================================
const loading       = ref(false)
const refreshing    = ref(false)
const keyword       = ref('')
const convTab       = ref('all')
const conversations = ref<any[]>([])

const unreadTotal = computed(() => conversations.value.reduce((s, c) => s + (c.unread_count || 0), 0))

const filteredConversations = computed(() => {
  let list = conversations.value
  if (convTab.value === 'unread') list = list.filter(c => c.unread_count > 0)
  if (convTab.value === 'high') list = list.filter(c => ['high', 'R4', 'R3'].includes(c.risk_level))
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(c => (c.name || '').toLowerCase().includes(kw))
  }
  return list
})

// ============================================================
// 状态 — 聊天
// ============================================================
const chatStudent    = ref<any>(null)
const messages       = ref<any[]>([])
const msgLoading     = ref(false)
const inputText      = ref('')
const showQuickReply = ref(false)
const scrollAnchor   = ref('')

// ============================================================
// 生命周期
// ============================================================
onMounted(() => loadConversations())

// ============================================================
// 数据加载 — 会话列表
// ============================================================
async function loadConversations() {
  loading.value = true
  try {
    const res = await _get<any>('v1/coach/students-with-messages')
    conversations.value = (res.students || res.items || []).map(normalizeConv)
  } catch {
    // fallback: 从 dashboard 学员列表构造
    try {
      const dash = await _get<any>('v1/coach/dashboard')
      conversations.value = (dash.students || []).map((s: any) => normalizeConv({
        student_id: s.id,
        student_name: s.name || s.full_name || s.username,
        avatar_url: s.avatar_url,
        last_message: s.latest_note || '',
        last_message_at: s.last_active_at || s.updated_at || '',
        unread_count: 0,
        risk_level: s.risk_level,
        ttm_stage: s.ttm_stage,
        is_online: false,
      }))
    } catch {
      conversations.value = []
    }
  } finally {
    loading.value = false
  }
}

function normalizeConv(c: any): any {
  return {
    student_id: c.student_id || c.id,
    name: c.student_name || c.name || c.full_name || c.username || '学员',
    avatar_url: c.avatar_url || '',
    last_message: c.last_message || c.latest_note || '',
    last_message_at: c.last_message_at || c.updated_at || '',
    unread_count: c.unread_count || 0,
    risk_level: c.risk_level || '',
    ttm_stage: c.ttm_stage || '',
    is_online: c.is_online || false,
  }
}

// ============================================================
// 数据加载 — 聊天消息
// ============================================================
async function loadMessages(studentId: number | string) {
  msgLoading.value = true
  messages.value = []
  try {
    const res = await _get<any>(`v1/coach/messages/${studentId}`, { page_size: 50 })
    messages.value = res.messages || res.items || []
  } catch {
    // 后端暂未实现，使用本地存储的消息
    const key = `coach_msg_${studentId}`
    try {
      const stored = uni.getStorageSync(key)
      messages.value = stored ? JSON.parse(stored) : []
    } catch {
      messages.value = []
    }
  } finally {
    msgLoading.value = false
    scrollToBottom()
  }
}

function saveLocalMessages(studentId: number | string) {
  const key = `coach_msg_${studentId}`
  // 最多存100条
  const toSave = messages.value.slice(-100)
  try { uni.setStorageSync(key, JSON.stringify(toSave)) } catch {}
}

// ============================================================
// 交互
// ============================================================
function onSearch(e: any) { keyword.value = e.detail?.value || '' }

async function onRefresh() {
  refreshing.value = true
  await loadConversations()
  refreshing.value = false
}

function openChat(conv: any) {
  chatStudent.value = conv
  loadMessages(conv.student_id)
}

function exitChat() {
  chatStudent.value = null
  messages.value = []
  inputText.value = ''
  showQuickReply.value = false
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !chatStudent.value) return
  const studentId = chatStudent.value.student_id

  const newMsg = {
    id: 'local_' + Date.now(),
    sender: 'coach',
    content: text,
    type: 'text',
    created_at: new Date().toISOString(),
  }
  messages.value.push(newMsg)
  inputText.value = ''
  scrollToBottom()

  // 尝试发送到后端
  try {
    await _post('v1/coach/messages', { student_id: Number(studentId), content: text, message_type: 'text' })
  } catch {
    // 后端暂未实现，仅本地保存
  }
  saveLocalMessages(studentId)

  // 更新会话列表预览
  const conv = conversations.value.find(c => c.student_id === studentId)
  if (conv) {
    conv.last_message = text
    conv.last_message_at = newMsg.created_at
  }
}

function useQuickReply(tpl: string) {
  inputText.value = tpl
  showQuickReply.value = false
}

function goStudentDetail() {
  if (!chatStudent.value) return
  uni.navigateTo({ url: `/pages/coach/students/detail?id=${chatStudent.value.student_id}` })
}

function goBack() {
  if (chatStudent.value) { exitChat(); return }
  uni.navigateBack({ fail: () => uni.switchTab({ url: '/pages/home/index' }) })
}

function scrollToBottom() {
  nextTick(() => {
    if (messages.value.length) scrollAnchor.value = 'msg-' + (messages.value.length - 1)
  })
}

// ============================================================
// 工具函数
// ============================================================
function showTimeSep(idx: number): boolean {
  if (idx === 0) return true
  const prev = messages.value[idx - 1]
  const cur = messages.value[idx]
  if (!prev?.created_at || !cur?.created_at) return false
  return new Date(cur.created_at).getTime() - new Date(prev.created_at).getTime() > 5 * 60 * 1000
}

function formatTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return dateStr.slice(0, 10)
}

function formatFullTime(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const today = new Date().toISOString().slice(0, 10)
  const dateKey = dateStr.slice(0, 10)
  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (dateKey === today) return `今天 ${time}`
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (dateKey === yesterday) return `昨天 ${time}`
  return `${dateKey.slice(5).replace('-', '/')} ${time}`
}
</script>

<style scoped>
.cm-page { background: var(--surface-secondary, #f9fafb); min-height: 100vh; display: flex; flex-direction: column; }

/* ═══ 导航栏 ═══ */
.cm-navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 24rpx; background: var(--surface, #fff);
  border-bottom: 1px solid var(--border-light, #e5e7eb);
  padding-top: calc(88rpx + env(safe-area-inset-top));
}
.cm-navbar__back { width: 56rpx; height: 56rpx; display: flex; align-items: center; justify-content: center; }
.cm-navbar__arrow { font-size: 48rpx; font-weight: 300; color: var(--text-primary, #111827); line-height: 1; }
.cm-navbar__back:active { opacity: 0.5; }
.cm-navbar__title { font-size: 34rpx; font-weight: 800; color: var(--text-primary, #111827); flex: 1; text-align: center; }
.cm-navbar__placeholder { width: 56rpx; }
.cm-navbar__action { padding: 8rpx 16rpx; }
.cm-navbar__action-text { font-size: 24rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981); }
.cm-navbar__action:active { opacity: 0.6; }

/* ═══ 搜索 ═══ */
.cm-search { padding: 12rpx 32rpx; background: var(--surface, #fff); }
.cm-search__box {
  display: flex; align-items: center; gap: 8rpx;
  background: var(--surface-secondary, #f3f4f6); border-radius: var(--radius-full, 999rpx);
  padding: 12rpx 20rpx;
}
.cm-search__icon { font-size: 24rpx; }
.cm-search__input { flex: 1; font-size: 26rpx; color: var(--text-primary); }
.cm-search__clear { font-size: 24rpx; color: var(--text-tertiary, #9ca3af); padding: 4rpx 8rpx; }

/* ═══ Tab ═══ */
.cm-tabs {
  display: flex; background: var(--surface, #fff); padding: 0 32rpx;
  border-bottom: 1px solid var(--border-light, #e5e7eb);
}
.cm-tab {
  flex: 1; text-align: center; padding: 20rpx 0; position: relative;
  font-size: 26rpx; font-weight: 500; color: var(--text-tertiary, #9ca3af);
}
.cm-tab--active { color: var(--bhp-primary-500, #10b981); font-weight: 700; border-bottom: 4rpx solid var(--bhp-primary-500, #10b981); }
.cm-tab__badge {
  position: absolute; top: 8rpx; right: 16rpx;
  min-width: 28rpx; height: 28rpx; border-radius: 14rpx;
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 6rpx;
}

/* ═══ 会话列表 ═══ */
.cm-body { flex: 1; padding: 12rpx 32rpx; }

.cm-conv {
  display: flex; align-items: flex-start; gap: 16rpx;
  background: var(--surface, #fff); border-radius: var(--radius-lg, 16rpx);
  padding: 24rpx; margin-bottom: 12rpx;
  border: 1px solid var(--border-light, #e5e7eb);
}
.cm-conv:active { background: var(--surface-secondary, #f9fafb); }
.cm-conv__avatar-wrap { position: relative; flex-shrink: 0; }
.cm-conv__avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: var(--bhp-gray-100, #f3f4f6); }
.cm-conv__online {
  position: absolute; bottom: 2rpx; right: 2rpx;
  width: 20rpx; height: 20rpx; border-radius: 50%;
  background: #10b981; border: 3rpx solid var(--surface, #fff);
}
.cm-conv__body { flex: 1; overflow: hidden; }
.cm-conv__row1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6rpx; }
.cm-conv__name { font-size: 28rpx; font-weight: 700; color: var(--text-primary, #111827); }
.cm-conv__time { font-size: 20rpx; color: var(--text-tertiary, #9ca3af); flex-shrink: 0; }
.cm-conv__row2 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.cm-conv__preview {
  font-size: 24rpx; color: var(--text-secondary, #6b7280); flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cm-conv__unread {
  min-width: 32rpx; height: 32rpx; border-radius: 16rpx;
  background: #ef4444; color: #fff; font-size: 18rpx; font-weight: 700;
  display: flex; align-items: center; justify-content: center; padding: 0 8rpx;
  flex-shrink: 0; margin-left: 12rpx;
}
.cm-conv__tags { display: flex; gap: 8rpx; flex-wrap: wrap; }
.cm-conv__tag {
  font-size: 20rpx; font-weight: 600; padding: 2rpx 10rpx; border-radius: var(--radius-full, 999rpx);
}
.cm-conv__tag--risk { background: #fef2f2; color: #dc2626; }
.cm-conv__tag--high, .cm-conv__tag--R4 { background: #fef2f2; color: #dc2626; }
.cm-conv__tag--medium, .cm-conv__tag--R3 { background: #fffbeb; color: #d97706; }
.cm-conv__tag--R2 { background: #eff6ff; color: #2563eb; }
.cm-conv__tag--stage { background: rgba(16,185,129,0.1); color: #059669; }

/* ═══ 聊天头部 ═══ */
.cm-chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16rpx 32rpx; background: var(--surface, #fff);
  border-bottom: 1px solid var(--border-light, #e5e7eb);
}
.cm-chat-header__info { display: flex; align-items: center; gap: 16rpx; }
.cm-chat-header__avatar { width: 64rpx; height: 64rpx; border-radius: 50%; background: #f3f4f6; }
.cm-chat-header__name { font-size: 26rpx; font-weight: 700; color: var(--text-primary); display: block; }
.cm-chat-header__tags { display: flex; gap: 8rpx; margin-top: 4rpx; }
.cm-chat-header__actions { flex-shrink: 0; }
.cm-header-btn {
  font-size: 22rpx; font-weight: 600; color: var(--bhp-primary-500, #10b981);
  padding: 8rpx 20rpx; border-radius: var(--radius-full, 999rpx);
  background: rgba(16,185,129,0.08);
}
.cm-header-btn:active { opacity: 0.7; }

/* ═══ 聊天消息区 ═══ */
.cm-chat-body { flex: 1; padding: 16rpx 32rpx; }
.cm-msg-list { padding-bottom: 32rpx; }

.cm-msg { display: flex; align-items: flex-start; gap: 12rpx; margin-bottom: 16rpx; }
.cm-msg--self { flex-direction: row-reverse; }
.cm-msg--system { justify-content: center; }

.cm-msg__avatar { width: 56rpx; height: 56rpx; border-radius: 50%; flex-shrink: 0; background: #f3f4f6; }
.cm-msg__bubble {
  max-width: 70%; padding: 16rpx 24rpx; border-radius: 20rpx;
  background: var(--surface, #fff); border: 1px solid var(--border-light, #e5e7eb);
  word-break: break-all;
}
.cm-msg--self .cm-msg__bubble {
  background: var(--bhp-primary-500, #10b981); border-color: var(--bhp-primary-500, #10b981);
}
.cm-msg__text { font-size: 28rpx; line-height: 1.6; color: var(--text-primary, #111827); }
.cm-msg--self .cm-msg__text { color: #fff; }

.cm-msg__system {
  font-size: 22rpx; color: var(--text-tertiary, #9ca3af);
  background: rgba(0,0,0,0.04); padding: 6rpx 20rpx; border-radius: var(--radius-full, 999rpx);
}

.cm-msg__time-sep {
  width: 100%; text-align: center; margin: 20rpx 0 12rpx;
  font-size: 20rpx; color: var(--text-tertiary, #9ca3af);
}

/* AI卡片 */
.cm-msg__bubble--ai_card { background: #f0fdf4; border-color: #bbf7d0; }
.cm-msg--self .cm-msg__bubble--ai_card { background: #f0fdf4; border-color: #bbf7d0; }
.cm-msg__ai-card { }
.cm-msg__ai-label { font-size: 22rpx; font-weight: 700; color: #059669; display: block; margin-bottom: 8rpx; }
.cm-msg__ai-content { font-size: 26rpx; color: var(--text-primary, #111827); line-height: 1.6; display: block; }
.cm-msg__ai-actions { margin-top: 8rpx; }
.cm-msg__ai-tag { font-size: 20rpx; color: #059669; font-weight: 600; }
.cm-msg--self .cm-msg__ai-content { color: var(--text-primary, #111827); }

/* ═══ 快捷回复 ═══ */
.cm-quick { background: var(--surface, #fff); border-top: 1px solid var(--border-light, #e5e7eb); padding: 12rpx 0; }
.cm-quick__scroll { white-space: nowrap; }
.cm-quick__list { display: inline-flex; gap: 12rpx; padding: 0 24rpx; }
.cm-quick__item {
  flex-shrink: 0; font-size: 24rpx; font-weight: 500;
  color: var(--bhp-primary-500, #10b981);
  background: rgba(16,185,129,0.08); padding: 10rpx 20rpx;
  border-radius: var(--radius-full, 999rpx); white-space: nowrap;
}
.cm-quick__item:active { opacity: 0.6; }

/* ═══ 输入栏 ═══ */
.cm-input-bar {
  display: flex; align-items: center; gap: 12rpx;
  padding: 16rpx 24rpx; background: var(--surface, #fff);
  border-top: 1px solid var(--border-light, #e5e7eb);
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
}
.cm-input-bar__quick-toggle {
  width: 56rpx; height: 56rpx; display: flex; align-items: center; justify-content: center;
  font-size: 32rpx; flex-shrink: 0;
}
.cm-input-bar__quick-toggle:active { opacity: 0.5; }
.cm-input-bar__wrap {
  flex: 1; background: var(--surface-secondary, #f3f4f6);
  border-radius: var(--radius-full, 999rpx); padding: 12rpx 24rpx;
}
.cm-input-bar__input { font-size: 28rpx; color: var(--text-primary); width: 100%; }
.cm-input-bar__send {
  flex-shrink: 0; font-size: 26rpx; font-weight: 700;
  color: var(--text-tertiary, #9ca3af); padding: 12rpx 20rpx;
  border-radius: var(--radius-full, 999rpx);
}
.cm-input-bar__send--active { color: #fff; background: var(--bhp-primary-500, #10b981); }
.cm-input-bar__send:active { opacity: 0.7; }

/* ═══ 空状态 ═══ */
.cm-empty {
  display: flex; flex-direction: column; align-items: center;
  padding: 120rpx 32rpx; gap: 12rpx;
}
.cm-empty--chat { padding: 80rpx 32rpx; }
.cm-empty__icon { font-size: 80rpx; }
.cm-empty__text { font-size: 28rpx; font-weight: 600; color: var(--text-secondary, #6b7280); }
.cm-empty__sub { font-size: 24rpx; color: var(--text-tertiary, #9ca3af); }

/* ═══ 骨架 ═══ */
.bhp-skeleton {
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
</style>
