<template>
  <div class="page-container">
    <van-nav-bar title="历史报告" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="report">
        <!-- 综合评分 -->
        <div class="card score-card">
          <h3>综合行为健康评估</h3>
          <div class="score-circle">
            <van-circle
              v-model:current-rate="animatedScore"
              :rate="report.overall_score || 0"
              :speed="60"
              :stroke-width="60"
              size="120px"
              :color="scoreColor"
              layer-color="#f0f0f0"
            >
              <div class="score-text">
                <span class="score-num">{{ report.overall_score || '--' }}</span>
                <span class="score-label">综合分</span>
              </div>
            </van-circle>
          </div>
          <div class="score-detail" v-if="report.stress_score !== undefined">
            <div class="detail-item">
              <span class="detail-label">压力指数</span>
              <van-progress :percentage="report.stress_score" :color="report.stress_score > 70 ? '#ee0a24' : '#1989fa'" stroke-width="8" />
            </div>
            <div class="detail-item">
              <span class="detail-label">疲劳指数</span>
              <van-progress :percentage="report.fatigue_score || 0" :color="(report.fatigue_score || 0) > 70 ? '#ee0a24' : '#07c160'" stroke-width="8" />
            </div>
          </div>
        </div>

        <!-- 风险等级 -->
        <div class="card" v-if="report.risk_level">
          <h3>风险等级</h3>
          <van-tag :type="riskType" size="large">{{ riskLabel }}</van-tag>
        </div>

        <!-- 建议 -->
        <div class="card" v-if="report.recommendations?.length">
          <h3>健康建议</h3>
          <div class="rec-list">
            <div class="rec-item" v-for="(rec, idx) in report.recommendations" :key="idx">
              <van-icon name="checked" color="#07c160" />
              <span>{{ rec }}</span>
            </div>
          </div>
        </div>

        <!-- 报告章节 -->
        <div class="card" v-if="chapters.length">
          <h3>报告详情</h3>
          <van-collapse v-model="activeChapter">
            <van-collapse-item
              v-for="(ch, idx) in chapters"
              :key="idx"
              :title="ch.title || `第${idx + 1}章`"
              :name="idx"
            >
              <div class="chapter-content">{{ ch.content || ch.text || '暂无内容' }}</div>
            </van-collapse-item>
          </van-collapse>
        </div>
      </template>

      <van-empty v-else description="暂无报告数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchFullReport } from '@/api/report'
import dashboardApi from '@/api/dashboard'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)
const report = ref<any>(null)
const chapters = ref<any[]>([])
const activeChapter = ref<number[]>([])
const animatedScore = ref(0)

const scoreColor = computed(() => {
  const s = report.value?.overall_score || 0
  if (s >= 70) return '#07c160'
  if (s >= 40) return '#ff976a'
  return '#ee0a24'
})

const riskLabel = computed(() => {
  const map: Record<string, string> = { low: '低风险', medium: '中等风险', high: '高风险' }
  return map[report.value?.risk_level] || report.value?.risk_level || '--'
})

const riskType = computed((): 'success' | 'warning' | 'danger' => {
  const map: Record<string, 'success' | 'warning' | 'danger'> = { low: 'success', medium: 'warning', high: 'danger' }
  return map[report.value?.risk_level] || 'warning'
})

onMounted(async () => {
  loading.value = true
  try {
    // 尝试获取完整报告
    const res: any = await fetchFullReport()
    if (res?.chapters) {
      chapters.value = res.chapters
    }
    // 获取dashboard数据作为综合评分
    const dashRes: any = await dashboardApi.getDashboard(userStore.userId)
    report.value = dashRes
  } catch {
    // 如果报告接口失败，单独尝试 dashboard
    try {
      const dashRes: any = await dashboardApi.getDashboard(userStore.userId)
      report.value = dashRes
    } catch {
      report.value = null
    }
  } finally {
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.loading {
  text-align: center;
  padding: 60px 0;
}

.card {
  h3 {
    font-size: $font-size-lg;
    margin-bottom: $spacing-md;
  }
}

.score-card {
  text-align: center;
}

.score-circle {
  display: flex;
  justify-content: center;
  margin: $spacing-md 0;
}

.score-text {
  display: flex;
  flex-direction: column;
  align-items: center;

  .score-num {
    font-size: 28px;
    font-weight: bold;
    color: $text-color;
  }

  .score-label {
    font-size: $font-size-xs;
    color: $text-color-secondary;
  }
}

.score-detail {
  margin-top: $spacing-md;

  .detail-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-sm;

    .detail-label {
      font-size: $font-size-sm;
      color: $text-color-secondary;
      width: 70px;
      flex-shrink: 0;
    }

    :deep(.van-progress) {
      flex: 1;
    }
  }
}

.rec-list {
  .rec-item {
    display: flex;
    align-items: flex-start;
    gap: $spacing-sm;
    padding: $spacing-xs 0;
    font-size: $font-size-md;
    line-height: 1.5;
  }
}

.chapter-content {
  font-size: $font-size-md;
  color: $text-color;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
