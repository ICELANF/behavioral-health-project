<template>
  <div class="course-list">
    <div class="page-header">
      <h2>课程列表</h2>
      <a-space>
        <a-switch v-model:checked="onlyAccessible" checked-children="只看可学习" un-checked-children="全部" @change="fetchCourses" />
        <a-button type="primary" @click="$router.push('/course/create')">
          <template #icon><PlusOutlined /></template>
          创建课程
        </a-button>
      </a-space>
    </div>

    <!-- 筛选 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="[12, 12]">
        <a-col :span="3">
          <a-select v-model:value="filters.audience" placeholder="学习受众" allowClear style="width: 100%">
            <a-select-option value="client"><span style="color:#1890ff">●</span> 服务对象</a-select-option>
            <a-select-option value="coach"><span style="color:#52c41a">●</span> 教练</a-select-option>
            <a-select-option value="both"><span style="color:#722ed1">●</span> 双受众</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select v-model:value="filters.source" placeholder="内容来源" allowClear style="width: 100%">
            <a-select-option v-for="(config, key) in CONTENT_SOURCE_CONFIG" :key="key" :value="key">
              <span :style="{ color: config.color }">●</span> {{ config.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select v-model:value="filters.level" placeholder="认证等级" allowClear style="width: 100%">
            <a-select-option value="L0">L0 观察员</a-select-option>
            <a-select-option value="L1">L1 成长者</a-select-option>
            <a-select-option value="L2">L2 分享者</a-select-option>
            <a-select-option value="L3">L3 教练</a-select-option>
            <a-select-option value="L4">L4 促进师</a-select-option>
            <a-select-option value="L5">L5 大师</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select v-model:value="filters.domain" placeholder="内容领域" allowClear style="width: 100%">
            <a-select-option v-for="(domain, key) in TRIGGER_DOMAINS" :key="key" :value="key">
              {{ domain.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filters.category" placeholder="课程类别" allowClear style="width: 100%">
            <a-select-option value="case">案例学习</a-select-option>
            <a-select-option value="skill">核心技能</a-select-option>
            <a-select-option value="practice">实践练习</a-select-option>
            <a-select-option value="knowledge">知识体系</a-select-option>
            <a-select-option value="method">方法体系</a-select-option>
            <a-select-option value="value">观念心智</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-select v-model:value="filters.status" placeholder="状态" allowClear style="width: 100%">
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending">待审核</a-select-option>
            <a-select-option value="published">已上架</a-select-option>
            <a-select-option value="offline">已下架</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-input-search v-model:value="filters.keyword" placeholder="搜索课程名称" @search="fetchCourses" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 统计卡片 -->
    <a-row :gutter="16" style="margin-bottom: 16px">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="全部课程" :value="stats.total" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="官方课程" :value="stats.platform" :value-style="{ color: '#1890ff' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="专家课程" :value="stats.expert" :value-style="{ color: '#722ed1' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic title="待审核" :value="stats.pending" :value-style="{ color: '#faad14' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 课程列表 -->
    <a-spin :spinning="loading">
      <div class="list-card-container">
        <ListCard
          v-for="record in filteredCourses"
          :key="record.course_id"
          :class="{ 'locked-card': record.access_status && !record.access_status.accessible }"
        >
          <template #avatar>
            <div class="cover-wrapper">
              <a-image :src="record.cover_url || defaultCover" :width="80" :preview="false" style="border-radius: 6px" />
              <div v-if="record.access_status && !record.access_status.accessible" class="lock-overlay" @click="showLockTip(record)">
                <LockOutlined class="lock-icon" />
              </div>
            </div>
          </template>
          <template #title>
            <span>
              {{ record.title }}
              <LockOutlined v-if="record.access_status && !record.access_status.accessible" style="color: #faad14; margin-left: 4px; font-size: 12px" />
            </span>
          </template>
          <template #subtitle>
            <div class="course-tags">
              <a-tag :color="audienceColors[record.audience]" size="small">
                {{ audienceLabels[record.audience] || '未设置' }}
              </a-tag>
              <a-tag :color="getSourceColor(record.source)" size="small">
                {{ getSourceLabel(record.source) }}
              </a-tag>
              <a-tag :color="levelColors[record.level]" size="small">{{ record.level }}</a-tag>
              <a-tag v-if="record.access_status && !record.access_status.accessible" color="warning" size="small">
                {{ record.access_status.unlock_level }} {{ record.access_status.unlock_level_label }} 解锁
              </a-tag>
              <a-tag size="small">{{ categoryLabels[record.category] }}</a-tag>
              <a-tag v-if="record.domain" size="small" color="cyan">{{ getDomainLabel(record.domain) }}</a-tag>
            </div>
          </template>
          <template #meta>
            <div class="author-cell">
              <a-avatar :src="record.author_avatar" :size="20">
                {{ record.author_name?.charAt(0) }}
              </a-avatar>
              <span class="author-name">{{ record.author_name }}</span>
              <CheckCircleFilled v-if="record.author_verified" class="verified-icon" />
            </div>
            <span class="meta-divider">|</span>
            <span><BookOutlined /> {{ record.chapter_count || 0 }} 章节</span>
            <span><ClockCircleOutlined /> {{ record.duration_minutes || 0 }} 分钟</span>
            <span><EyeOutlined /> {{ formatNumber(record.view_count || 0) }}</span>
            <span><UserOutlined /> {{ formatNumber(record.enroll_count || 0) }}</span>
            <span v-if="record.avg_rating"><StarFilled style="color: #faad14" /> {{ record.avg_rating }}</span>
            <span class="meta-divider">|</span>
            <a-badge
              :status="statusMap[record.status]?.badge"
              :text="statusMap[record.status]?.text"
            />
            <a-tag v-if="record.review_status === 'pending'" color="orange" size="small">待审核</a-tag>
          </template>
          <template #actions>
            <a-space>
              <a @click="$router.push(`/course/chapters/${record.course_id}`)">章节</a>
              <a @click="$router.push(`/course/edit/${record.course_id}`)">编辑</a>
              <a-dropdown>
                <a>更多</a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item v-if="record.status === 'draft'" @click="handlePublish(record)">
                      上架
                    </a-menu-item>
                    <a-menu-item v-if="record.status === 'published'" @click="handleOffline(record)">
                      下架
                    </a-menu-item>
                    <a-menu-item v-if="record.review_status === 'pending'" @click="handleReview(record)">
                      <span style="color: #faad14">审核</span>
                    </a-menu-item>
                    <a-menu-item @click="handlePreview(record)">预览</a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="handleDelete(record)">删除</a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </ListCard>
      </div>
      <div v-if="filteredCourses.length === 0 && !loading" style="text-align: center; padding: 40px; color: #999">
        暂无课程数据
      </div>
    </a-spin>
    <div style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 个课程`"
        @change="onPaginationChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  CheckCircleFilled,
  BookOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  UserOutlined,
  StarFilled,
  LockOutlined
} from '@ant-design/icons-vue'
import { CONTENT_SOURCE_CONFIG } from '@/types/content'
import type { ContentSource } from '@/types/content'
import { TRIGGER_DOMAINS } from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { fetchContentList } from '@/api/course'
import ListCard from '@/components/core/ListCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const onlyAccessible = ref(false)
const defaultCover = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="90" fill="none"><rect width="160" height="90" rx="4" fill="#f0f2f5"/><text x="80" y="50" text-anchor="middle" fill="#bfbfbf" font-size="14" font-family="sans-serif">暂无封面</text></svg>')

const filters = reactive({
  audience: undefined as string | undefined,
  source: undefined as ContentSource | undefined,
  level: undefined as string | undefined,
  domain: undefined as string | undefined,
  category: undefined as string | undefined,
  status: undefined as string | undefined,
  keyword: ''
})

const stats = reactive({
  total: 0,
  platform: 0,
  expert: 0,
  pending: 0
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 个课程`
})

const audienceLabels: Record<string, string> = { client: '服务对象', coach: '教练', both: '双受众' }
const audienceColors: Record<string, string> = { client: '#1890ff', coach: '#52c41a', both: '#722ed1' }

const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple',
  L5: 'gold'
}

const levelLabels: Record<string, string> = {
  L0: '观察员',
  L1: '成长者',
  L2: '分享者',
  L3: '教练',
  L4: '促进师',
  L5: '大师'
}

const categoryLabels: Record<string, string> = {
  knowledge: '知识体系',
  method: '方法体系',
  skill: '核心技能',
  value: '观念心智',
  practice: '实践练习',
  case: '案例学习'
}

const statusMap: Record<string, { badge: string; text: string }> = {
  draft: { badge: 'default', text: '草稿' },
  pending: { badge: 'warning', text: '待审核' },
  published: { badge: 'success', text: '已上架' },
  offline: { badge: 'error', text: '已下架' }
}

// columns removed — now using ListCard layout

// 辅助函数
const getSourceLabel = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.label || source
const getSourceColor = (source: ContentSource) => CONTENT_SOURCE_CONFIG[source]?.color || '#666'
const getDomainLabel = (domain: string) => (TRIGGER_DOMAINS as any)[domain]?.label || domain
const formatNumber = (num: number) => {
  if (num >= 10000) return (num / 10000).toFixed(1) + 'w'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k'
  return num.toString()
}

// 前端等级门控：用 userLevel 计算 access_status
const getUserLevel = () => authStore.userLevel || 0

const computeAccessStatus = (level: string) => {
  const levelMap: Record<string, number> = { L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5 }
  const required = levelMap[level] ?? 0
  const userLv = getUserLevel()
  if (userLv >= required) {
    return { accessible: true, reason: null, unlock_level: null, unlock_level_label: null }
  }
  return {
    accessible: false,
    reason: `需完成${level} ${levelLabels[level] || level}才能解锁`,
    unlock_level: level,
    unlock_level_label: levelLabels[level] || level,
  }
}

const courses = ref<any[]>([])

// 计算后的课程列表（带 access_status）
const filteredCourses = computed(() => {
  let list = courses.value.map(c => ({
    ...c,
    access_status: c.access_status || computeAccessStatus(c.level || 'L0')
  }))
  if (onlyAccessible.value) {
    list = list.filter(c => c.access_status.accessible)
  }
  return list
})

const fetchCourses = async () => {
  loading.value = true

  try {
  const apiData = await fetchContentList({
    page: pagination.current,
    page_size: pagination.pageSize,
    type: 'course',
    source: filters.source || undefined,
    domain: filters.domain || undefined,
    level: filters.level || undefined,
    audience: filters.audience || undefined,
    keyword: filters.keyword || undefined,
  })

  if (apiData && apiData.items) {
    // API 返回数据已包含 access_status
    courses.value = apiData.items.map((item: any, idx: number) => ({
      course_id: item.id || String(idx),
      title: item.title,
      source: item.source,
      audience: item.audience || 'client',
      level: item.level || 'L0',
      domain: item.domain,
      author_name: item.author?.name || '未知',
      author_verified: item.author?.verified || false,
      view_count: item.view_count || 0,
      like_count: item.like_count || 0,
      duration: item.duration,
      is_free: item.is_free,
      access_status: item.access_status,
      status: 'published',
      cover_url: item.cover_url || '',
      chapter_count: item.chapter_count || item.sections?.length || 0,
      duration_minutes: item.duration ? Math.round(item.duration / 60) : 0,
      enroll_count: item.enroll_count || item.collect_count || 0,
      updated_at: item.updated_at || '',
    }))
    pagination.total = apiData.total

    // 动态更新统计
    const items = apiData.items || []
    stats.total = apiData.total || items.length
    stats.platform = items.filter((i: any) => i.source === 'platform').length
    stats.expert = items.filter((i: any) => i.source === 'expert').length
    stats.pending = items.filter((i: any) => i.review_status === 'pending').length
  }
  } catch (e) {
    console.error('加载课程列表失败:', e)
  }

  loading.value = false
}

const showLockTip = (record: any) => {
  const status = record.access_status
  if (status && !status.accessible) {
    Modal.info({
      title: '内容未解锁',
      content: status.reason || `完成当前等级后解锁此内容`,
    })
  }
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchCourses()
}

const onPaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
  fetchCourses()
}

const handlePublish = (record: any) => {
  Modal.confirm({
    title: '确认上架',
    content: `确定要上架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'published'
      message.success('上架成功')
    }
  })
}

const handleOffline = (record: any) => {
  Modal.confirm({
    title: '确认下架',
    content: `确定要下架课程「${record.title}」吗？`,
    onOk() {
      record.status = 'offline'
      message.success('下架成功')
    }
  })
}

const handleReview = (record: any) => {
  router.push(`/content/review?id=${record.course_id}&type=course`)
}

const handlePreview = (record: any) => {
  window.open(`/course/edit/${record.course_id || record.id}`, '_blank')
}

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除课程「${record.title}」吗？此操作不可恢复。`,
    okType: 'danger',
    onOk() {
      const index = courses.value.findIndex(c => c.course_id === record.course_id)
      if (index > -1) {
        courses.value.splice(index, 1)
        message.success('删除成功')
      }
    }
  })
}

onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.course-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.author-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.author-name {
  font-size: 13px;
}

.verified-icon {
  color: #1890ff;
  font-size: 12px;
  margin-left: 2px;
}

.meta-divider {
  color: #d9d9d9;
  margin: 0 4px;
}

/* Lock styles */
.cover-wrapper {
  position: relative;
  display: inline-block;
}

.lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 6px;
}

.lock-icon {
  color: #fff;
  font-size: 24px;
}

.locked-card {
  opacity: 0.7;
}
</style>
