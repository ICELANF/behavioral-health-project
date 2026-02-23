<template>
  <div class="live-list">
    <div class="page-header">
      <h2>直播管理</h2>
      <a-button type="primary" @click="$router.push('/live/create')">
        <template #icon><PlusOutlined /></template>
        创建直播
      </a-button>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日直播" :value="todayLives" :value-style="{ color: '#1890ff' }">
            <template #prefix><VideoCameraOutlined /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="正在直播" :value="livingCount" :value-style="{ color: '#52c41a' }">
            <template #suffix>
              <span class="live-indicator"></span>
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="本周预约" :value="weekScheduled" :value-style="{ color: '#722ed1' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="累计观看人次" :value="totalViewers" :value-style="{ color: '#faad14' }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选区域 -->
    <a-card style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="5">
          <a-select
            v-model:value="filters.status"
            placeholder="直播状态"
            allowClear
            style="width: 100%"
          >
            <a-select-option value="scheduled">未开始</a-select-option>
            <a-select-option value="live">直播中</a-select-option>
            <a-select-option value="ended">已结束</a-select-option>
            <a-select-option value="cancelled">已取消</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filters.level"
            placeholder="认证等级"
            allowClear
            style="width: 100%"
          >
            <a-select-option value="L0">L0 公众</a-select-option>
            <a-select-option value="L1">L1 初级</a-select-option>
            <a-select-option value="L2">L2 中级</a-select-option>
            <a-select-option value="L3">L3 高级</a-select-option>
            <a-select-option value="L4">L4 督导</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-range-picker
            v-model:value="filters.dateRange"
            style="width: 100%"
            :placeholder="['开始日期', '结束日期']"
          />
        </a-col>
        <a-col :span="5">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索直播标题/讲师"
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 直播列表 -->
    <a-spin :spinning="loading">
      <a-empty v-if="!loading && lives.length === 0" description="直播功能即将上线，敬请期待" style="padding: 60px 0" />
      <div v-else class="list-card-container">
        <ListCard
          v-for="record in filteredLives"
          :key="record.live_id"
          @click="viewLive(record)"
        >
          <template #avatar>
            <div class="live-cover">
              <img v-if="record.cover_url" :src="record.cover_url" alt="封面" />
              <div v-else class="cover-placeholder">
                <VideoCameraOutlined />
              </div>
              <div v-if="record.status === 'live'" class="live-badge">
                <span class="live-dot"></span> 直播中
              </div>
            </div>
          </template>
          <template #title>
            <span>{{ record.title }}</span>
          </template>
          <template #subtitle>
            <div class="instructor-cell">
              <a-avatar :size="20">{{ record.instructor_name?.[0] }}</a-avatar>
              <span>{{ record.instructor_name }}</span>
            </div>
          </template>
          <template #meta>
            <a-tag :color="levelColors[record.level]">{{ record.level }}</a-tag>
            <a-badge :status="statusBadges[record.status]" :text="statusLabels[record.status]" />
            <span class="meta-divider">|</span>
            <span><ClockCircleOutlined /> {{ formatDateTime(record.scheduled_at) }}</span>
            <span><FieldTimeOutlined /> {{ record.duration_minutes }}分钟</span>
            <span v-if="record.status === 'live' || record.status === 'ended'">
              <EyeOutlined /> {{ record.viewer_count || 0 }}
            </span>
          </template>
          <template #actions>
            <a-space>
              <a @click.stop="viewLive(record)">详情</a>
              <template v-if="record.status === 'scheduled'">
                <a @click.stop="editLive(record)">编辑</a>
                <a style="color: #ff4d4f" @click.stop="cancelLive(record)">取消</a>
              </template>
              <template v-else-if="record.status === 'live'">
                <a style="color: #52c41a" @click.stop="enterLiveRoom(record)">进入直播间</a>
              </template>
              <template v-else-if="record.status === 'ended'">
                <a v-if="record.replay_url" @click.stop="viewReplay(record)">查看回放</a>
                <a-popconfirm title="确定删除该直播记录吗？" @confirm="deleteLive(record)">
                  <a style="color: #ff4d4f" @click.stop>删除</a>
                </a-popconfirm>
              </template>
            </a-space>
          </template>
        </ListCard>
      </div>
    </a-spin>
    <div v-if="filteredLives.length > 0" style="display: flex; justify-content: flex-end; margin-top: 16px">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-size-changer
        :show-total="(total: number) => `共 ${total} 条记录`"
        @change="onPaginationChange"
      />
    </div>

    <!-- 直播详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="直播详情"
      width="700px"
      :footer="null"
    >
      <template v-if="currentLive">
        <div class="live-detail-header">
          <div class="detail-cover">
            <img v-if="currentLive.cover_url" :src="currentLive.cover_url" alt="封面" />
            <div v-else class="cover-placeholder large">
              <VideoCameraOutlined style="font-size: 48px" />
            </div>
          </div>
          <div class="detail-info">
            <h3>{{ currentLive.title }}</h3>
            <a-badge :status="statusBadges[currentLive.status]" :text="statusLabels[currentLive.status]" />
          </div>
        </div>

        <a-descriptions :column="2" bordered size="small" style="margin-top: 16px">
          <a-descriptions-item label="讲师">{{ currentLive.instructor_name }}</a-descriptions-item>
          <a-descriptions-item label="认证等级">
            <a-tag :color="levelColors[currentLive.level]">{{ currentLive.level }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ formatDateTime(currentLive.scheduled_at) }}</a-descriptions-item>
          <a-descriptions-item label="时长">{{ currentLive.duration_minutes }} 分钟</a-descriptions-item>
          <a-descriptions-item label="观看人数" v-if="currentLive.status !== 'scheduled'">
            {{ currentLive.viewer_count || 0 }} 人
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ currentLive.created_at }}</a-descriptions-item>
          <a-descriptions-item label="直播简介" :span="2">
            {{ currentLive.description || '暂无简介' }}
          </a-descriptions-item>
        </a-descriptions>

        <div class="detail-actions" style="margin-top: 16px; text-align: right">
          <a-space>
            <a-button v-if="currentLive.status === 'scheduled'" @click="editLive(currentLive)">
              <EditOutlined /> 编辑
            </a-button>
            <a-button v-if="currentLive.status === 'live'" type="primary" @click="enterLiveRoom(currentLive)">
              <PlayCircleOutlined /> 进入直播间
            </a-button>
            <a-button v-if="currentLive.replay_url" @click="viewReplay(currentLive)">
              <PlaySquareOutlined /> 查看回放
            </a-button>
          </a-space>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import request from '../../api/request'
import {
  PlusOutlined,
  VideoCameraOutlined,
  ClockCircleOutlined,
  FieldTimeOutlined,
  EyeOutlined,
  EditOutlined,
  PlayCircleOutlined,
  PlaySquareOutlined
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import ListCard from '@/components/core/ListCard.vue'

const router = useRouter()

// 接口定义
interface LiveSession {
  live_id: string
  title: string
  description?: string
  instructor_name: string
  instructor_id: string
  level: string
  cover_url?: string
  scheduled_at: string
  duration_minutes: number
  status: 'scheduled' | 'live' | 'ended' | 'cancelled'
  viewer_count?: number
  replay_url?: string
  created_at: string
}

// 状态
const loading = ref(false)
const detailVisible = ref(false)
const currentLive = ref<LiveSession | null>(null)

// 筛选条件
const filters = reactive({
  status: undefined as string | undefined,
  level: undefined as string | undefined,
  dateRange: null as any,
  keyword: ''
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条记录`
})

// columns removed — now using ListCard layout

// 常量
const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple'
}

const statusLabels: Record<string, string> = {
  scheduled: '未开始',
  live: '直播中',
  ended: '已结束',
  cancelled: '已取消'
}

const statusBadges: Record<string, 'default' | 'processing' | 'success' | 'error'> = {
  scheduled: 'default',
  live: 'processing',
  ended: 'success',
  cancelled: 'error'
}

const lives = ref<LiveSession[]>([])

const loadLives = async () => {
  loading.value = true
  try {
    const res = await request.get('v1/live/sessions')
    lives.value = res.data?.items || res.data || []
  } catch {
    // Live streaming backend not yet available — show empty state
    lives.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadLives)

// 计算属性
const todayLives = computed(() => {
  const today = dayjs().format('YYYY-MM-DD')
  return lives.value.filter(l => l.scheduled_at.startsWith(today)).length
})

const livingCount = computed(() => lives.value.filter(l => l.status === 'live').length)

const weekScheduled = computed(() => {
  const weekStart = dayjs().startOf('week')
  const weekEnd = dayjs().endOf('week')
  return lives.value.filter(l => {
    const date = dayjs(l.scheduled_at)
    return date.isAfter(weekStart) && date.isBefore(weekEnd) && l.status === 'scheduled'
  }).length
})

const totalViewers = computed(() => {
  return lives.value.reduce((sum, l) => sum + (l.viewer_count || 0), 0)
})

const filteredLives = computed(() => {
  let result = [...lives.value]

  if (filters.status) {
    result = result.filter(l => l.status === filters.status)
  }
  if (filters.level) {
    result = result.filter(l => l.level === filters.level)
  }
  if (filters.dateRange && filters.dateRange[0] && filters.dateRange[1]) {
    const start = dayjs(filters.dateRange[0]).startOf('day')
    const end = dayjs(filters.dateRange[1]).endOf('day')
    result = result.filter(l => {
      const date = dayjs(l.scheduled_at)
      return date.isAfter(start) && date.isBefore(end)
    })
  }
  if (filters.keyword) {
    const kw = filters.keyword.toLowerCase()
    result = result.filter(l =>
      l.title.toLowerCase().includes(kw) ||
      l.instructor_name.toLowerCase().includes(kw)
    )
  }

  pagination.total = result.length
  return result
})

// 方法
const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

const handleSearch = () => {
  pagination.current = 1
}

const resetFilters = () => {
  filters.status = undefined
  filters.level = undefined
  filters.dateRange = null
  filters.keyword = ''
  pagination.current = 1
}

const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

const onPaginationChange = (page: number, pageSize: number) => {
  pagination.current = page
  pagination.pageSize = pageSize
}

const viewLive = (record: LiveSession) => {
  currentLive.value = record
  detailVisible.value = true
}

const editLive = (record: LiveSession) => {
  router.push(`/live/edit/${record.live_id}`)
}

const cancelLive = (record: LiveSession) => {
  Modal.confirm({
    title: '取消直播',
    content: `确定要取消直播「${record.title}」吗？取消后将无法恢复。`,
    okText: '确认取消',
    okType: 'danger',
    onOk: async () => {
      try {
        await request.post(`v1/live/sessions/${record.live_id}/cancel`)
        message.success('直播已取消')
        await loadLives()
      } catch (e) {
        console.error('取消直播失败:', e)
        message.error('取消直播失败')
      }
    }
  })
}

const enterLiveRoom = (record: LiveSession) => {
  Modal.info({
    title: `直播间: ${record.title}`,
    content: `讲师: ${record.instructor_name} | 观看人数: ${record.viewer_count || 0}`,
    okText: '关闭',
  })
}

const viewReplay = (record: LiveSession) => {
  if (record.replay_url) {
    window.open(record.replay_url, '_blank')
  }
}

const deleteLive = async (record: LiveSession) => {
  try {
    await request.delete(`v1/live/sessions/${record.live_id}`)
    message.success('直播记录已删除')
    await loadLives()
  } catch (e) {
    console.error('删除直播失败:', e)
    message.error('删除直播失败')
  }
}
</script>

<style scoped>
.list-card-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.live-list {
  padding: 0;
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

.stats-row {
  margin-bottom: 16px;
}

.live-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
  margin-left: 8px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.live-cover {
  position: relative;
  width: 100px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.live-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 24px;
}

.cover-placeholder.large {
  height: 150px;
}

.live-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: #ff4d4f;
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

.meta-divider {
  color: #d9d9d9;
  margin: 0 4px;
}

.instructor-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.live-detail-header {
  display: flex;
  gap: 16px;
}

.detail-cover {
  width: 200px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.detail-info h3 {
  margin: 0 0 8px 0;
}
</style>
