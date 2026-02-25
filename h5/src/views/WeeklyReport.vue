<!--
  周报页面 — 查看本周行为分析报告
  路由: /weekly-report
-->
<template>
  <div class="page-container">
    <van-nav-bar
      title="行为周报"
      left-arrow
      @click-left="router.back()"
    />

    <div class="page-content weekly-report-page">
      <van-loading v-if="loading" class="report-loading" size="24px" vertical>
        加载中...
      </van-loading>

      <div v-else-if="!report" class="empty-state">
        <van-empty description="暂无周报数据" image="search">
          <template #description>
            <p>周报在每周日晚自动生成</p>
            <p class="empty-hint">坚持完成每日任务，下周就能看到你的报告</p>
          </template>
        </van-empty>
      </div>

      <template v-else>
        <!-- 周期标题 -->
        <div class="week-header card">
          <div class="week-range">{{ report.week_start }} ~ {{ report.week_end }}</div>
          <div class="week-label">行为分析周报</div>
        </div>

        <!-- 核心指标 -->
        <div class="metrics-grid">
          <div class="metric-card card">
            <div class="metric-icon" style="background: #e6f7ff">
              <van-icon name="todo-list-o" size="22" color="#1890ff" />
            </div>
            <div class="metric-value">{{ report.completion_pct }}%</div>
            <div class="metric-label">任务完成率</div>
            <div class="metric-detail">{{ report.tasks_completed }}/{{ report.tasks_total }}</div>
          </div>
          <div class="metric-card card">
            <div class="metric-icon" style="background: #fff7e6">
              <van-icon name="clock-o" size="22" color="#fa8c16" />
            </div>
            <div class="metric-value">{{ report.learning_minutes }}</div>
            <div class="metric-label">学习分钟</div>
          </div>
          <div class="metric-card card">
            <div class="metric-icon" style="background: #f6ffed">
              <van-icon name="gem-o" size="22" color="#52c41a" />
            </div>
            <div class="metric-value">{{ report.points_earned }}</div>
            <div class="metric-label">获得积分</div>
          </div>
          <div class="metric-card card">
            <div class="metric-icon" style="background: #fff1f0">
              <van-icon name="fire-o" size="22" color="#f5222d" />
            </div>
            <div class="metric-value">{{ report.streak_days }}</div>
            <div class="metric-label">完成天数</div>
          </div>
        </div>

        <!-- 签到与活动 -->
        <div class="detail-card card">
          <div class="detail-row">
            <span class="detail-label">签到次数</span>
            <span class="detail-value">{{ report.checkin_count }} 次</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">活动记录</span>
            <span class="detail-value">{{ report.activity_count }} 条</span>
          </div>
        </div>

        <!-- 高频标签 -->
        <div v-if="report.highlights && report.highlights.length" class="highlights-card card">
          <h4>本周高频行为</h4>
          <div class="highlight-tags">
            <van-tag
              v-for="h in report.highlights"
              :key="h.tag"
              type="primary"
              round
              size="medium"
            >
              {{ h.tag }} × {{ h.count }}
            </van-tag>
          </div>
        </div>

        <!-- 建议 -->
        <div v-if="report.suggestions && report.suggestions.length" class="suggestions-card card">
          <h4>本周建议 <AiContentBadge :review-status="report.review_status" compact /></h4>
          <div v-for="(s, i) in report.suggestions" :key="i" class="suggestion-item">
            <van-icon name="bulb-o" color="#faad14" size="16" />
            <span>{{ s }}</span>
          </div>
        </div>

        <!-- 历史周报 -->
        <div v-if="historyList.length > 1" class="history-card card">
          <h4>历史周报</h4>
          <div
            v-for="item in historyList"
            :key="item.week_start"
            class="history-item"
            :class="{ active: item.week_start === report.week_start }"
            @click="loadReport(item.week_start)"
          >
            <span>{{ item.week_start }} ~ {{ item.week_end }}</span>
            <span class="history-pct">{{ item.completion_pct }}%</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import AiContentBadge from '@/components/common/AiContentBadge.vue'
import request from '@/api/request'

const router = useRouter()

const loading = ref(true)
const report = ref<any>(null)
const historyList = ref<any[]>([])

const loadLatest = async () => {
  loading.value = true
  try {
    const res = await request.get('/v1/weekly-reports/latest')
    report.value = res.data || null
  } catch (e: any) {
    if (e.response?.status !== 404) {
      showToast('加载周报失败')
    }
    report.value = null
  } finally {
    loading.value = false
  }
}

const loadReport = async (weekStart: string) => {
  loading.value = true
  try {
    const res = await request.get(`/v1/weekly-reports/${weekStart}`)
    report.value = res.data || null
  } catch {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

const loadHistory = async () => {
  try {
    const res = await request.get('/v1/weekly-reports', { params: { limit: 8 } })
    const data = res.data
    historyList.value = data.reports || data.items || []
  } catch {
    historyList.value = []
  }
}

onMounted(async () => {
  await loadLatest()
  loadHistory()
})
</script>

<style scoped>
.weekly-report-page {
  padding: 12px;
}
.report-loading {
  padding: 60px 0;
}
.empty-state {
  padding: 40px 0;
}
.empty-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}
.week-header {
  text-align: center;
}
.week-range {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}
.week-label {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}
.metric-card {
  text-align: center;
  padding: 14px 8px;
}
.metric-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  margin-bottom: 8px;
}
.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}
.metric-label {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.metric-detail {
  font-size: 11px;
  color: #bbb;
  margin-top: 2px;
}
.detail-card .detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}
.detail-card .detail-row:last-child {
  border-bottom: none;
}
.detail-label {
  color: #666;
  font-size: 14px;
}
.detail-value {
  color: #333;
  font-weight: 600;
  font-size: 14px;
}
.highlights-card h4,
.suggestions-card h4,
.history-card h4 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #333;
}
.highlight-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}
.history-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
  font-size: 13px;
  color: #666;
  cursor: pointer;
}
.history-item:last-child {
  border-bottom: none;
}
.history-item.active {
  color: #1890ff;
  font-weight: 600;
}
.history-pct {
  font-weight: 600;
}
</style>
