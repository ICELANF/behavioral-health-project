<!--
  LearningView.vue — 学习成长
  学习统计 + 内容列表 + 分类筛选 + 学时记录
  对接: learningApi.getStats() + contentApi.list()
-->

<template>
  <div class="learning-view">
    <div class="page-header">
      <h2 class="page-title">学习成长</h2>
      <p class="page-desc">循序渐进，构建行为健康知识体系</p>
    </div>

    <!-- 学习统计 -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-icon" style="background:#eef8f4;">📖</div>
        <div>
          <div class="stat-val">{{ stats?.total_minutes || 0 }}</div>
          <div class="stat-lbl">学习分钟</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#f0f0ff;">🎯</div>
        <div>
          <div class="stat-val">{{ stats?.completed_count || 0 }}</div>
          <div class="stat-lbl">已完成课程</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#fff8ee;">🔥</div>
        <div>
          <div class="stat-val">{{ stats?.streak_days || 0 }}</div>
          <div class="stat-lbl">连续学习天</div>
        </div>
      </div>
    </div>

    <!-- 内容列表 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">课程内容</h3>
        <a-select v-model:value="filter.category" placeholder="全部分类" style="width: 140px;" allow-clear @change="loadContent">
          <a-select-option value="behavioral">行为健康</a-select-option>
          <a-select-option value="nutrition">营养饮食</a-select-option>
          <a-select-option value="exercise">运动锻炼</a-select-option>
          <a-select-option value="psychology">心理调适</a-select-option>
          <a-select-option value="tcm">中医养生</a-select-option>
        </a-select>
      </div>

      <a-spin :spinning="contentLoading">
        <div v-if="contentList.length" class="content-list">
          <div v-for="item in contentList" :key="item.id" class="content-item" @click="viewContent(item)">
            <div class="content-level" :class="'l' + (item.content_level || 1)">
              M{{ item.content_level || 1 }}
            </div>
            <div class="content-info">
              <div class="content-title">{{ item.title }}</div>
              <div class="content-meta">
                <span>{{ item.category || '通用' }}</span>
                <span v-if="item.duration_minutes">· {{ item.duration_minutes }}分钟</span>
              </div>
            </div>
            <div class="content-status">
              <a-tag v-if="item.completed" color="success">已学</a-tag>
              <right-outlined v-else style="color:#ccc;" />
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无内容" />
      </a-spin>

      <div class="load-more" v-if="contentTotal > contentList.length">
        <a-button @click="loadMore" :loading="contentLoading">加载更多</a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { learningApi, contentApi } from '@/api'
import { RightOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const authStore = useAuthStore()
const stats = ref<any>(null)
const contentList = ref<any[]>([])
const contentTotal = ref(0)
const contentLoading = ref(false)
const page = ref(1)
const filter = reactive({ category: undefined as string | undefined })

async function loadContent() {
  contentLoading.value = true
  page.value = 1
  try {
    const res = await contentApi.list({ category: filter.category, page: 1 })
    contentList.value = res.items || []
    contentTotal.value = res.total || 0
  } catch {}
  contentLoading.value = false
}

async function loadMore() {
  contentLoading.value = true
  page.value++
  try {
    const res = await contentApi.list({ category: filter.category, page: page.value })
    contentList.value.push(...(res.items || []))
  } catch {}
  contentLoading.value = false
}

function viewContent(item: any) {
  message.info(`打开课程：${item.title}（详情页开发中）`)
}

onMounted(async () => {
  const userId = authStore.user?.id
  if (userId) {
    const [s] = await Promise.allSettled([learningApi.getStats(userId)])
    if (s.status === 'fulfilled') {
      const raw = s.value
      // 后端返回嵌套结构: {learning_time: {total_minutes}, streak: {current_streak}}
      // 视图层平铺: {total_minutes, completed_count, streak_days}
      stats.value = {
        total_minutes: raw.learning_time?.total_minutes ?? raw.total_minutes ?? 0,
        completed_count: raw.learning_points?.total_points ?? raw.completed_count ?? 0,
        streak_days: raw.streak?.current_streak ?? raw.streak_days ?? 0,
      }
    }
  }
  await loadContent()
})
</script>

<style scoped>
.learning-view { max-width: 800px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #999; margin: 0; }

.stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border-radius: 14px; padding: 18px; display: flex; align-items: center; gap: 12px; border: 1px solid #f0f0f0; }
.stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat-val { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.stat-lbl { font-size: 12px; color: #999; }

.card { background: #fff; border-radius: 14px; padding: 24px; border: 1px solid #f0f0f0; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.card-title { font-size: 16px; font-weight: 600; margin: 0; }

.content-list { display: flex; flex-direction: column; }
.content-item { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-bottom: 1px solid #fafafa; cursor: pointer; transition: background .15s; }
.content-item:last-child { border-bottom: none; }
.content-item:hover { background: #fafafa; margin: 0 -12px; padding-left: 12px; padding-right: 12px; border-radius: 8px; }
.content-level { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #fff; flex-shrink: 0; }
.content-level.l1 { background: #94a3b8; }
.content-level.l2 { background: #7dd3fc; }
.content-level.l3 { background: #60a5fa; }
.content-level.l4 { background: #a78bfa; }
.content-level.l5 { background: #fbbf24; }
.content-level.l6 { background: #f87171; }
.content-info { flex: 1; }
.content-title { font-size: 14px; font-weight: 500; color: #333; }
.content-meta { font-size: 12px; color: #bbb; margin-top: 2px; }
.content-status { flex-shrink: 0; }

.load-more { text-align: center; margin-top: 16px; }
</style>
