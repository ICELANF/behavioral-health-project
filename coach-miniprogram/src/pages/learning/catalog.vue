<template>
  <view class="ct-page">

    <!-- 模块 Tab -->
    <view class="ct-modules">
      <view
        v-for="mod in MODULES"
        :key="mod.key"
        class="ct-module-tab"
        :class="{ 'ct-module-tab--active': activeModule === mod.key }"
        @tap="switchModule(mod.key)"
      >
        <text>{{ mod.label }}</text>
      </view>
    </view>

    <!-- 类型筛选 -->
    <scroll-view scroll-x class="ct-filters">
      <view class="ct-filter-row">
        <view
          v-for="f in FILTERS"
          :key="f.value"
          class="ct-filter"
          :class="{ 'ct-filter--active': activeFilter === f.value }"
          @tap="switchFilter(f.value)"
        >
          <text>{{ f.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 课程列表 -->
    <scroll-view scroll-y class="ct-list" enable-pull-down-refresh @refresherrefresh="onRefresh">
      <template v-if="loading">
        <view class="ct-skeleton" v-for="i in 4" :key="i">
          <view class="bhp-skeleton" style="height:200rpx;border-radius:var(--radius-lg);"></view>
        </view>
      </template>
      <template v-else-if="items.length">
        <view
          v-for="item in items"
          :key="item.id"
          class="ct-card-wrap"
          @tap="goContent(item)"
        >
          <view class="ct-card-lock" v-if="isLocked(item)">
            <view class="ct-card-lock__overlay">
              <text class="ct-card-lock__icon">🔒</text>
              <text class="ct-card-lock__text">需要 {{ item.required_role_label || ('L' + item.min_level) }} 解锁</text>
            </view>
          </view>
          <BHPCourseCard
            :title="item.title"
            :cover="item.cover_url"
            :type="item.content_type"
            :duration="item.estimated_minutes ? item.estimated_minutes + '分钟' : ''"
            :points="item.points"
          />
        </view>
      </template>
      <view v-else class="ct-empty">
        <text class="ct-empty__text">该分类下暂无课程</text>
      </view>
    </scroll-view>

  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import BHPCourseCard from '@/components/BHPCourseCard.vue'
import http from '@/api/request'

const userStore = useUserStore()

const MODULES = [
  { key: 'M1', label: 'M1 基础' },
  { key: 'M2', label: 'M2 进阶' },
  { key: 'M3', label: 'M3 专业' },
  { key: 'M4', label: 'M4 大师' },
]

const FILTERS = [
  { value: '',       label: '全部' },
  { value: 'video',  label: '视频' },
  { value: 'article', label: '图文' },
  { value: 'audio',  label: '音频' },
  { value: 'course', label: '课程' },
]

const activeModule = ref('M1')
const activeFilter = ref('')
const items        = ref<any[]>([])
const loading      = ref(false)

onMounted(() => {
  userStore.restoreFromStorage()
  loadCatalog()
})

function switchModule(mod: string) {
  activeModule.value = mod
  loadCatalog()
}

function switchFilter(f: string) {
  activeFilter.value = f
  loadCatalog()
}

async function loadCatalog() {
  loading.value = true
  try {
    const params: Record<string, any> = { module: activeModule.value, page_size: 50 }
    if (activeFilter.value) params.content_type = activeFilter.value
    const res = await http.get<{ items: any[] }>('/v1/content', params)
    items.value = res.items || []
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function onRefresh() {
  await loadCatalog()
  uni.stopPullDownRefresh()
}

function isLocked(item: any): boolean {
  const minLevel = item.min_level || 1
  return userStore.roleLevel < minLevel
}

function goContent(item: any) {
  if (isLocked(item)) {
    uni.showToast({ title: '等级不足，暂时无法访问', icon: 'none' })
    return
  }
  if (item.content_type === 'video') {
    uni.navigateTo({ url: `/pages/learning/video-player?content_id=${item.id}` })
  } else if (item.content_type === 'audio') {
    uni.navigateTo({ url: `/pages/learning/audio-player?content_id=${item.id}` })
  } else if (item.content_type === 'course') {
    uni.navigateTo({ url: `/pages/learning/course-detail?id=${item.id}` })
  } else {
    uni.navigateTo({ url: `/pages/learning/content-detail?id=${item.id}` })
  }
}
</script>

<style scoped>
.ct-page { background: var(--surface-secondary); min-height: 100vh; display: flex; flex-direction: column; }

/* 模块 Tab */
.ct-modules {
  display: flex; background: var(--surface);
  border-bottom: 1px solid var(--border-light); padding: 0 16rpx;
}
.ct-module-tab {
  flex: 1; text-align: center; padding: 20rpx 0;
  font-size: 26rpx; color: var(--text-secondary); cursor: pointer;
  border-bottom: 3px solid transparent; font-weight: 500;
}
.ct-module-tab--active { color: var(--bhp-primary-500); border-bottom-color: var(--bhp-primary-500); font-weight: 700; }

/* 类型筛选 */
.ct-filters { background: var(--surface); white-space: nowrap; padding: 12rpx 0; border-bottom: 1px solid var(--border-light); }
.ct-filter-row { display: flex; gap: 12rpx; padding: 0 32rpx; }
.ct-filter {
  font-size: 24rpx; font-weight: 500; color: var(--text-secondary);
  background: var(--bhp-gray-50); padding: 8rpx 24rpx; border-radius: var(--radius-full);
  cursor: pointer; flex-shrink: 0;
}
.ct-filter--active { background: var(--bhp-primary-500); color: #fff; font-weight: 600; }

/* 列表 */
.ct-list { flex: 1; padding: 16rpx 32rpx; }
.ct-card-wrap { margin-bottom: 20rpx; position: relative; }
.ct-skeleton { margin-bottom: 20rpx; }

/* 锁定 */
.ct-card-lock { position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 5; }
.ct-card-lock__overlay {
  width: 100%; height: 100%;
  background: rgba(255,255,255,0.75); border-radius: var(--radius-lg);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8rpx;
}
.ct-card-lock__icon { font-size: 48rpx; }
.ct-card-lock__text { font-size: 22rpx; font-weight: 600; color: var(--text-tertiary); }

/* 空状态 */
.ct-empty { display: flex; align-items: center; justify-content: center; padding-top: 120rpx; }
.ct-empty__text { font-size: 28rpx; color: var(--text-secondary); }
</style>
