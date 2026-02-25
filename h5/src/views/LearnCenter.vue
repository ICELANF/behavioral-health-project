<!--
  学习中心 — 内容浏览/发现 + 学习进度
  路由: /learn
  底部Tab: 学习
-->
<template>
  <div class="page-container">
    <van-nav-bar title="学习中心" />

    <div class="page-content learn-center">
      <!-- 学习进度卡片 -->
      <div class="progress-card card">
        <div class="progress-header">
          <div class="streak-badge" v-if="stats.streak > 0">
            <span class="streak-fire">🔥</span>
            <span class="streak-num">{{ stats.streak }}</span>
            <span class="streak-label">天</span>
          </div>
          <div class="progress-stats">
            <div class="stat-item">
              <span class="stat-value">{{ stats.totalMinutes }}</span>
              <span class="stat-label">分钟</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.totalPoints }}</span>
              <span class="stat-label">积分</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.level }}</span>
              <span class="stat-label">等级</span>
            </div>
          </div>
        </div>
        <van-progress
          :percentage="stats.levelProgress"
          stroke-width="6"
          color="linear-gradient(to right, #1989fa, #07c160)"
          track-color="#ebedf0"
          :show-pivot="false"
        />
        <div class="progress-hint">
          距下一级 <strong>{{ stats.nextLevel }}</strong> 还需 {{ stats.pointsToNext }} 成长积分
        </div>
      </div>

      <!-- 搜索栏 -->
      <van-search
        v-model="searchText"
        placeholder="搜索文章、课程、案例..."
        shape="round"
        @search="onSearch"
        @clear="onSearch"
      />

      <!-- 内容类型Tab -->
      <van-tabs v-model:active="activeTab" sticky offset-top="46" @change="onTabChange">
        <van-tab title="推荐" name="feed" />
        <van-tab title="文章" name="article" />
        <van-tab title="视频" name="video" />
        <van-tab title="课程" name="course" />
        <van-tab title="案例" name="case_study" />
        <van-tab title="卡片" name="card" />
      </van-tabs>

      <!-- 领域筛选 -->
      <div class="domain-filter" v-if="activeTab !== 'feed'">
        <van-tag
          v-for="d in domains"
          :key="d.value"
          :plain="selectedDomain !== d.value"
          :type="selectedDomain === d.value ? 'primary' : 'default'"
          round
          size="medium"
          @click="toggleDomain(d.value)"
        >
          {{ d.label }}
        </van-tag>
      </div>

      <!-- 内容列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="loadMore"
        >
          <div
            v-for="item in contentList"
            :key="item.id"
            class="content-card"
            @click="goDetail(item)"
          >
            <div class="content-card-body">
              <div class="content-info">
                <div class="content-type-tag">
                  <van-tag :type="typeTagColor(item.type)" size="small" plain round>
                    {{ typeLabel(item.type) }}
                  </van-tag>
                  <van-tag v-if="item.level > 0" color="#f5f5f5" text-color="#999" size="small" round>
                    L{{ item.level }}
                  </van-tag>
                </div>
                <h3 class="content-title">{{ item.title }}</h3>
                <p class="content-summary">{{ item.summary || stripHtml(item.body) }}</p>
                <div class="content-footer">
                  <span class="content-author">{{ item.author || '平台' }}</span>
                  <span class="content-stats">
                    👁 {{ item.view_count || 0 }}
                    · ❤ {{ item.like_count || 0 }}
                  </span>
                </div>
              </div>
              <div v-if="item.cover_url" class="content-cover">
                <img :src="item.cover_url" :alt="item.title" />
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <van-empty v-if="!loading && contentList.length === 0" description="暂无内容" />
        </van-list>
      </van-pull-refresh>
    </div>

    <TabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/index'
import { useUserStore } from '@/stores/user'
import TabBar from '@/components/common/TabBar.vue'

const router = useRouter()
const userStore = useUserStore()

// ---- 学习进度 ----
const stats = ref({
  totalMinutes: 0,
  totalPoints: 0,
  streak: 0,
  level: 'L0',
  nextLevel: 'L1',
  levelProgress: 0,
  pointsToNext: 100,
})

async function loadStats() {
  try {
    const userId = userStore.userId
    const [growerRes, coachRes]: any[] = await Promise.all([
      api.get(`/api/v1/learning/grower/stats/${userId}`).catch(() => null),
      api.get(`/api/v1/learning/coach/points/${userId}`).catch(() => null),
    ])
    if (growerRes) {
      stats.value.totalMinutes = growerRes.learning_time?.total_minutes || 0
      stats.value.totalPoints = growerRes.learning_points?.total_points || 0
      stats.value.streak = growerRes.streak?.current_streak || 0
    }
    if (coachRes) {
      stats.value.level = coachRes.current_level || 'L0'
      stats.value.nextLevel = coachRes.next_level || '最高'
      stats.value.levelProgress = coachRes.level_progress || 0
      const req = coachRes.next_level_requirements
      if (req) {
        const needed = Math.max(0, (req.min_growth || 0) - (coachRes.scores?.growth || 0))
        stats.value.pointsToNext = needed
      }
    }
  } catch { /* 静默 */ }
}

// ---- 搜索 ----
const searchText = ref('')

function onSearch() {
  page.value = 1
  contentList.value = []
  finished.value = false
  loadMore()
}

// ---- Tab & 领域 ----
const activeTab = ref('feed')
const selectedDomain = ref('')

const domains = [
  { label: '全部', value: '' },
  { label: '情绪管理', value: 'emotion' },
  { label: '睡眠改善', value: 'sleep' },
  { label: '营养健康', value: 'nutrition' },
  { label: '运动康复', value: 'exercise' },
  { label: '正念减压', value: 'mindfulness' },
  { label: '中医养生', value: 'tcm' },
  { label: '代谢管理', value: 'metabolic' },
]

function toggleDomain(value: string) {
  selectedDomain.value = selectedDomain.value === value ? '' : value
  onSearch()
}

function onTabChange() {
  selectedDomain.value = ''
  onSearch()
}

// ---- 内容列表 ----
const contentList = ref<any[]>([])
const loading = ref(true)
const refreshing = ref(false)
const finished = ref(false)
const page = ref(1)
const pageSize = 10

async function loadMore() {
  loading.value = true
  try {
    let res: any
    const params: any = {
      page: page.value,
      page_size: pageSize,
      keyword: searchText.value || undefined,
      domain: selectedDomain.value || undefined,
    }
    if (activeTab.value === 'feed') {
      // 推荐Tab: 按热度排序
      params.sort_by = 'view_count'
    } else {
      params.type = activeTab.value
    }
    res = await api.get('/api/v1/content', { params })
    const items = res?.items || []
    if (page.value === 1) {
      contentList.value = items
    } else {
      contentList.value.push(...items)
    }
    if (items.length < pageSize) {
      finished.value = true
    }
    page.value++
  } catch {
    finished.value = true
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function onRefresh() {
  page.value = 1
  finished.value = false
  loadMore()
}

// ---- 导航 ----
function goDetail(item: any) {
  router.push(`/content/${item.type || 'article'}/${item.id}`)
}

// ---- 工具 ----
function typeLabel(t: string): string {
  const map: Record<string, string> = {
    article: '文章', video: '视频', course: '课程',
    case_study: '案例', card: '卡片', audio: '音频',
  }
  return map[t] || t
}

function typeTagColor(t: string): string {
  const map: Record<string, string> = {
    article: 'primary', video: 'success', course: 'warning',
    case_study: 'danger', card: 'default', audio: 'primary',
  }
  return map[t] || 'default'
}

function stripHtml(html: string): string {
  if (!html) return ''
  return html.replace(/<[^>]*>/g, '').substring(0, 80)
}

onMounted(() => {
  loadStats()
  loadMore()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.learn-center {
  padding-bottom: 60px;
}

.progress-card {
  background: linear-gradient(135deg, #1989fa 0%, #07c160 100%);
  color: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-md;

  .progress-header {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-sm;
  }

  .streak-badge {
    display: flex;
    align-items: baseline;
    gap: 2px;
    background: rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 4px 12px;

    .streak-fire { font-size: 16px; }
    .streak-num { font-size: 20px; font-weight: 700; }
    .streak-label { font-size: 11px; opacity: 0.8; }
  }

  .progress-stats {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-around;
  }

  .stat-item {
    text-align: center;
    .stat-value { display: block; font-size: 18px; font-weight: 700; }
    .stat-label { display: block; font-size: 11px; opacity: 0.8; }
  }

  .stat-divider {
    width: 1px;
    height: 24px;
    background: rgba(255,255,255,0.3);
  }

  :deep(.van-progress) {
    margin: $spacing-sm 0 6px;
  }
  :deep(.van-progress__portion) {
    border-radius: 3px;
  }

  .progress-hint {
    font-size: 11px;
    opacity: 0.85;
    strong { font-weight: 600; }
  }
}

.domain-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: $spacing-sm $spacing-md;
}

.content-card {
  padding: $spacing-sm $spacing-md;
  border-bottom: 1px solid $border-color;
  background: #fff;

  &:active { background: #f7f8fa; }

  .content-card-body {
    display: flex;
    gap: $spacing-sm;
  }

  .content-info {
    flex: 1;
    min-width: 0;
  }

  .content-type-tag {
    display: flex;
    gap: 4px;
    margin-bottom: 4px;
  }

  .content-title {
    font-size: 15px;
    font-weight: 600;
    color: $text-color;
    line-height: 1.4;
    margin: 0 0 4px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .content-summary {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    line-height: 1.4;
    margin: 0 0 6px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .content-footer {
    display: flex;
    justify-content: space-between;
    font-size: $font-size-xs;
    color: $text-color-placeholder;
  }

  .content-cover {
    flex-shrink: 0;
    width: 100px;
    height: 75px;
    border-radius: 6px;
    overflow: hidden;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}
</style>
