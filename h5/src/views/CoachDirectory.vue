<!--
  教练目录页面 — 公开页面，搜索 + 教练卡片列表
  路由: /coach-directory
-->
<template>
  <div class="page-container">
    <van-nav-bar
      title="教练目录"
      left-arrow
      @click-left="router.back()"
    />

    <div class="page-content coach-directory-page">
      <!-- 搜索栏 -->
      <van-search
        v-model="keyword"
        placeholder="搜索教练姓名、专长..."
        shape="round"
        @search="onSearch"
        @clear="onSearch"
      />

      <!-- 加载状态 -->
      <van-loading v-if="loading" class="dir-loading" size="24px" vertical>
        加载中...
      </van-loading>

      <!-- 教练列表 -->
      <div v-else class="coach-list">
        <div
          v-for="coach in filteredCoaches"
          :key="coach.id"
          class="coach-card card"
          @click="goToChat(coach)"
        >
          <div class="coach-avatar">
            <van-icon name="manager-o" size="36" :color="avatarColor(coach.id)" />
          </div>
          <div class="coach-info">
            <div class="coach-name-row">
              <span class="coach-name">{{ coach.username || coach.name }}</span>
              <van-tag type="primary" size="small" round>
                {{ coach.title || '教练' }}
              </van-tag>
            </div>
            <div v-if="coach.specialties?.length" class="coach-specialties">
              <van-tag
                v-for="spec in coach.specialties.slice(0, 3)"
                :key="spec"
                plain
                round
                size="small"
                color="#1989fa"
              >
                {{ spec }}
              </van-tag>
            </div>
            <div class="coach-desc" v-if="coach.bio">{{ coach.bio }}</div>
            <div class="coach-meta">
              <span v-if="coach.specialties?.length">
                {{ coach.specialties.length }} 项专长
              </span>
            </div>
          </div>
          <van-icon name="arrow" color="#c8c9cc" class="coach-arrow" />
        </div>
      </div>

      <!-- 空状态 -->
      <van-empty
        v-if="!loading && filteredCoaches.length === 0"
        description="暂无匹配的教练"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'

const router = useRouter()

const loading = ref(true)
const keyword = ref('')
const coaches = ref<any[]>([])

// 搜索过滤
const filteredCoaches = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return coaches.value
  return coaches.value.filter((c: any) =>
    (c.username || c.name || '').toLowerCase().includes(q) ||
    (c.title || '').toLowerCase().includes(q) ||
    (c.bio || '').toLowerCase().includes(q) ||
    (c.specialties || []).some((s: string) => s.toLowerCase().includes(q))
  )
})

function onSearch() {
  // 筛选由 computed 自动处理
}

// 头像颜色
function avatarColor(id: number | string): string {
  const colors = ['#1989fa', '#07c160', '#7c3aed', '#f59e0b', '#ee0a24', '#10b981']
  const idx = typeof id === 'number' ? id : (id?.toString().charCodeAt(0) || 0)
  return colors[idx % colors.length]
}

// 跳转对话
function goToChat(coach: any) {
  router.push({
    path: '/chat',
    query: { coachId: coach.id }
  })
}

// 加载教练列表
async function loadCoaches() {
  loading.value = true
  try {
    const res: any = await api.get('/api/v1/coach/directory')
    coaches.value = res.coaches || res || []
  } catch (err) {
    console.error('加载教练目录失败:', err)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCoaches()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.dir-loading {
  padding: 80px 0;
}

.coach-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.coach-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;

  &:active {
    opacity: 0.8;
  }
}

.coach-avatar {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: #f0f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.coach-info {
  flex: 1;
  min-width: 0;
}

.coach-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.coach-name {
  font-size: 16px;
  font-weight: 600;
  color: $text-color;
}

.coach-title {
  font-size: $font-size-sm;
  color: $text-color-secondary;
  margin-bottom: 6px;
}

.coach-specialties {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 6px;
}

.coach-desc {
  font-size: $font-size-sm;
  color: #646566;
  line-height: 1.4;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.coach-meta {
  display: flex;
  gap: 12px;
  font-size: $font-size-xs;
  color: $text-color-secondary;

  span {
    display: flex;
    align-items: center;
    gap: 2px;
  }
}

.coach-arrow {
  flex-shrink: 0;
  margin-top: 16px;
}
</style>
