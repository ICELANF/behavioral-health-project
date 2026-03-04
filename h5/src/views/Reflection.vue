<template>
  <div class="reflection-page">
    <van-nav-bar title="我的反思" left-arrow @click-left="goBack()" />

    <!-- 统计角标 -->
    <div class="stats-bar" v-if="stats">
      <span>已写 <strong>{{ stats.total_entries || 0 }}</strong> 篇</span>
      <span class="divider">·</span>
      <span>平均深度 <strong>{{ depthLabel(stats.avg_depth) }}</strong></span>
    </div>

    <!-- Section 1: 今日提示 -->
    <div class="section-card">
      <div class="section-title">今日写作提示</div>
      <van-loading v-if="loadingPrompt" size="20" />
      <template v-else-if="todayPrompt">
        <div class="prompt-text">{{ todayPrompt.content || todayPrompt.prompt_text || todayPrompt }}</div>
        <van-button
          v-if="!showEditor"
          type="primary"
          round
          size="small"
          class="start-btn"
          @click="openEditor(todayPrompt)"
        >
          开始写
        </van-button>
      </template>
      <div v-else class="prompt-empty">暂无提示，你可以直接写下今天的感悟</div>
      <van-button
        v-if="!showEditor"
        plain
        round
        size="small"
        class="free-btn"
        @click="openEditor(null)"
      >
        自由写作
      </van-button>
    </div>

    <!-- Section 2: 写日志（展开） -->
    <div class="section-card editor-card" v-if="showEditor">
      <div class="section-title">写日志</div>

      <van-field
        v-model="form.title"
        label="标题"
        placeholder="可选，简单描述今天的主题"
        clearable
      />

      <div class="type-row">
        <span class="type-label">类型</span>
        <van-radio-group v-model="form.journal_type" direction="horizontal">
          <van-radio name="freeform">自由写作</van-radio>
          <van-radio name="guided">引导式</van-radio>
        </van-radio-group>
      </div>

      <van-field
        v-model="form.content"
        type="textarea"
        :rows="6"
        placeholder="写下你今天的反思、感悟或观察…"
        maxlength="2000"
        show-word-limit
        class="content-field"
      />

      <div class="public-toggle-row">
        <span class="public-toggle-label">
          {{ form.is_public ? '🌐 公开分享（教练和同伴可见）' : '🔒 仅自己可见' }}
        </span>
        <van-switch v-model="form.is_public" size="20px" active-color="#722ed1" />
      </div>

      <div class="editor-actions">
        <van-button plain round size="small" @click="showEditor = false">取消</van-button>
        <van-button
          type="primary"
          round
          size="small"
          :loading="submitting"
          :disabled="!form.content.trim()"
          @click="submitEntry"
        >
          提交
        </van-button>
      </div>
    </div>

    <!-- Section 3: 历史日志 + 精华分享 Tab -->
    <div class="section-card">
      <div class="tab-row">
        <button class="tab-btn" :class="{ active: activeTab === 'my' }" @click="activeTab = 'my'">我的日志</button>
        <button class="tab-btn" :class="{ active: activeTab === 'public' }" @click="switchPublicTab">精华分享</button>
      </div>
      <div class="section-title" style="display:none">历史日志</div>
      <!-- 我的日志 -->
      <template v-if="activeTab === 'my'">
        <van-loading v-if="loadingEntries" size="20" />
        <van-empty v-else-if="!entries.length" description="还没有日志，写下第一篇吧" />
        <template v-else>
          <div
            v-for="entry in entries"
            :key="entry.id"
            class="entry-card"
            @click="viewEntry(entry)"
          >
            <div class="entry-header">
              <span class="entry-title">{{ entry.title || '无标题' }}</span>
              <span class="entry-public-badge" v-if="entry.is_public">公开 · 教练可见</span>
              <van-tag :color="depthColor(entry.depth_level)" size="small" text-color="#fff">
                {{ depthLabel(entry.depth_level) }}
              </van-tag>
            </div>
            <div class="entry-preview">{{ entry.content?.slice(0, 60) }}{{ (entry.content?.length || 0) > 60 ? '…' : '' }}</div>
            <div class="entry-date">{{ formatDate(entry.created_at) }}</div>
          </div>

          <div class="load-more" v-if="hasMore">
            <van-button plain round size="small" :loading="loadingMore" @click="loadMore">加载更多</van-button>
          </div>
        </template>
      </template>

      <!-- 精华分享（公开日志社区） -->
      <template v-if="activeTab === 'public'">
        <van-loading v-if="loadingPublic" size="20" />
        <van-empty v-else-if="!publicEntries.length" description="暂无精华分享，成为第一个分享者吧" />
        <template v-else>
          <div
            v-for="entry in publicEntries"
            :key="entry.id"
            class="entry-card"
            @click="viewEntry(entry)"
          >
            <div class="entry-header">
              <span class="entry-title">{{ entry.title || '无标题' }}</span>
              <van-tag :color="depthColor(entry.depth_level)" size="small" text-color="#fff">
                {{ depthLabel(entry.depth_level) }}
              </van-tag>
            </div>
            <div class="entry-author" v-if="entry.author_name">{{ entry.author_name }}</div>
            <div class="entry-preview">{{ entry.content?.slice(0, 80) }}{{ (entry.content?.length || 0) > 80 ? '…' : '' }}</div>
            <div class="entry-date">{{ formatDate(entry.created_at) }}</div>
          </div>
        </template>
      </template>
    </div>

    <!-- 详情弹窗 -->
    <van-popup
      v-model:show="showDetail"
      position="bottom"
      round
      :style="{ maxHeight: '80vh', overflowY: 'auto' }"
    >
      <div class="detail-popup" v-if="selectedEntry">
        <div class="detail-header">
          <span class="detail-title">{{ selectedEntry.title || '无标题' }}</span>
          <van-tag :color="depthColor(selectedEntry.depth_level)" size="small" text-color="#fff">
            {{ depthLabel(selectedEntry.depth_level) }}
          </van-tag>
        </div>
        <div class="detail-date">{{ formatDate(selectedEntry.created_at) }}</div>
        <div class="detail-content">{{ selectedEntry.content }}</div>
        <div class="detail-close">
          <van-button round plain size="small" @click="showDetail = false">关闭</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { useGoBack } from '@/composables/useGoBack'
const { goBack } = useGoBack()
import { ref, reactive, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import api from '@/api/index'

const loadingPrompt = ref(false)
const loadingEntries = ref(false)
const loadingMore = ref(false)
const loadingPublic = ref(false)
const submitting = ref(false)
const showEditor = ref(false)
const showDetail = ref(false)
const activeTab = ref<'my' | 'public'>('my')

const todayPrompt = ref<any>(null)
const stats = ref<any>(null)
const entries = ref<any[]>([])
const publicEntries = ref<any[]>([])
const selectedEntry = ref<any>(null)
const hasMore = ref(false)
const page = ref(0)
const PAGE_SIZE = 10

const form = reactive({
  title: '',
  content: '',
  journal_type: 'freeform' as 'freeform' | 'guided',
  prompt_id: null as string | null,
  is_public: false,
})

function depthLabel(depth?: string) {
  const map: Record<string, string> = {
    surface: '表层', pattern: '规律', insight: '洞见', identity: '身份'
  }
  return map[depth || ''] || '表层'
}

function depthColor(depth?: string) {
  const map: Record<string, string> = {
    surface: '#8c8c8c', pattern: '#1890ff', insight: '#52c41a', identity: '#722ed1'
  }
  return map[depth || ''] || '#8c8c8c'
}

function formatDate(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function openEditor(prompt: any) {
  form.title = ''
  form.content = prompt?.content || prompt?.prompt_text || ''
  form.journal_type = prompt ? 'guided' : 'freeform'
  form.prompt_id = prompt?.id || null
  form.is_public = false
  showEditor.value = true
}

async function switchPublicTab() {
  activeTab.value = 'public'
  if (publicEntries.value.length > 0) return
  loadingPublic.value = true
  try {
    const res: any = await api.get('/api/v1/reflection/entries', {
      params: { is_public: true, limit: 20 }
    })
    publicEntries.value = Array.isArray(res) ? res : (res?.items || [])
  } catch {
    publicEntries.value = []
  } finally {
    loadingPublic.value = false
  }
}

function viewEntry(entry: any) {
  selectedEntry.value = entry
  showDetail.value = true
}

async function loadPrompt() {
  loadingPrompt.value = true
  try {
    const res: any = await api.get('/api/v1/reflection/prompts')
    const list = Array.isArray(res) ? res : (res?.items || [])
    if (list.length) {
      todayPrompt.value = list[Math.floor(Math.random() * list.length)]
    }
  } catch {
    todayPrompt.value = null
  } finally {
    loadingPrompt.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await api.get('/api/v1/reflection/stats')
  } catch {
    stats.value = null
  }
}

async function loadEntries(reset = false) {
  if (reset) {
    page.value = 0
    entries.value = []
  }
  loadingEntries.value = reset
  loadingMore.value = !reset
  try {
    const res: any = await api.get('/api/v1/reflection/entries', {
      params: { skip: page.value * PAGE_SIZE, limit: PAGE_SIZE }
    })
    const list = Array.isArray(res) ? res : (res?.items || [])
    entries.value = reset ? list : [...entries.value, ...list]
    hasMore.value = list.length === PAGE_SIZE
    page.value++
  } catch {
    // silent
  } finally {
    loadingEntries.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  loadEntries(false)
}

async function submitEntry() {
  if (!form.content.trim()) return
  submitting.value = true
  try {
    await api.post('/api/v1/reflection/entries', {
      title: form.title || undefined,
      content: form.content,
      journal_type: form.journal_type,
      prompt_id: form.prompt_id || undefined,
      is_public: form.is_public,
    })
    showSuccessToast('日志已保存')
    showEditor.value = false
    form.title = ''
    form.content = ''
    form.prompt_id = null
    await Promise.allSettled([loadEntries(true), loadStats()])
  } catch {
    showFailToast('保存失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadPrompt()
  loadStats()
  loadEntries(true)
})
</script>

<style scoped>
.reflection-page {
  min-height: 100vh;
  background: #f7f8fa;
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  font-size: 13px;
  color: #555;
  border-bottom: 1px solid #f0f0f0;
}
.stats-bar strong { color: #722ed1; }
.divider { color: #d9d9d9; }

.section-card {
  margin: 12px 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #222;
}

.prompt-text {
  font-size: 15px;
  line-height: 1.7;
  color: #333;
  background: #fafafa;
  padding: 12px;
  border-radius: 8px;
  border-left: 3px solid #722ed1;
  margin-bottom: 10px;
}

.prompt-empty {
  font-size: 13px;
  color: #999;
  margin-bottom: 10px;
}

.start-btn { margin-right: 8px; }
.free-btn { }

/* editor */
.editor-card { }
.type-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 10px 0;
}
.type-label {
  font-size: 14px;
  color: #646566;
  min-width: 40px;
}
.content-field { margin-top: 8px; }
.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

/* public toggle */
.public-toggle-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-top: 1px solid #f5f5f5; margin-top: 8px;
}
.public-toggle-label { font-size: 13px; color: #555; }

/* tabs */
.tab-row {
  display: flex; gap: 4px; margin-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}
.tab-btn {
  flex: 1; background: none; border: none; padding: 10px;
  font-size: 14px; color: #999; cursor: pointer; font-weight: 600;
  border-bottom: 2px solid transparent; margin-bottom: -2px;
  transition: all 0.2s;
}
.tab-btn.active { color: #722ed1; border-bottom-color: #722ed1; }

/* history */
.entry-public-badge {
  font-size: 11px; color: #722ed1; background: #f9f0ff;
  padding: 1px 6px; border-radius: 4px; margin-right: 4px; flex-shrink: 0;
}
.entry-author { font-size: 12px; color: #722ed1; margin-bottom: 4px; }
.entry-card {
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
}
.entry-card:last-child { border-bottom: none; }
.entry-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.entry-title {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.entry-preview {
  font-size: 13px;
  color: #777;
  line-height: 1.5;
  margin-bottom: 4px;
}
.entry-date {
  font-size: 12px;
  color: #bbb;
}
.load-more {
  text-align: center;
  padding: 12px 0 4px;
}

/* detail popup */
.detail-popup {
  padding: 20px 16px 32px;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.detail-title {
  font-size: 17px;
  font-weight: 700;
  flex: 1;
}
.detail-date {
  font-size: 12px;
  color: #bbb;
  margin-bottom: 16px;
}
.detail-content {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
  margin-bottom: 20px;
}
.detail-close {
  text-align: center;
}
</style>
