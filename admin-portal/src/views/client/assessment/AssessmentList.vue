<template>
  <div class="assessment-list">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">← 返回</button>
      <h2>测评中心</h2>
    </div>

    <!-- Recommended -->
    <div v-if="recommended.length > 0" class="section">
      <h3 class="section-title">推荐测评</h3>
      <div v-for="item in recommended" :key="item.id" class="assess-card recommended" @click="$router.push(`/client/assessment/take/${item.id}`)">
        <div class="assess-badge">推荐</div>
        <div class="assess-icon" :style="{ background: item.color }">{{ item.icon }}</div>
        <div class="assess-info">
          <span class="assess-name">{{ item.name }}</span>
          <span class="assess-desc">{{ item.description }}</span>
          <div class="assess-meta">
            <span>{{ item.questionCount }} 题</span>
            <span>约 {{ item.estimatedMin }} 分钟</span>
          </div>
        </div>
        <span class="assess-arrow">→</span>
      </div>
    </div>

    <!-- Available questionnaires -->
    <div class="section">
      <h3 class="section-title">可用问卷目录</h3>
      <div class="category-tabs">
        <button v-for="cat in categories" :key="cat.key" class="cat-tab" :class="{ active: activeCategory === cat.key }" @click="activeCategory = cat.key">
          {{ cat.label }}
        </button>
      </div>
      <div v-for="item in filteredQuestionnaires" :key="item.id" class="assess-card" @click="$router.push(`/client/assessment/take/${item.id}`)">
        <div class="assess-icon" :style="{ background: item.color }">{{ item.icon }}</div>
        <div class="assess-info">
          <span class="assess-name">{{ item.name }}</span>
          <span class="assess-desc">{{ item.description }}</span>
          <div class="assess-meta">
            <span>{{ item.questionCount }} 题</span>
            <span>约 {{ item.estimatedMin }} 分钟</span>
            <span v-if="item.completedCount > 0" class="completed-badge">已完成 {{ item.completedCount }} 次</span>
          </div>
        </div>
        <span class="assess-arrow">→</span>
      </div>
    </div>

    <!-- Completed records -->
    <div class="section">
      <h3 class="section-title">已完成记录</h3>
      <div v-for="record in completedRecords" :key="record.id" class="record-card" @click="$router.push(`/client/assessment/result/${record.id}`)">
        <div class="record-left">
          <span class="record-name">{{ record.name }}</span>
          <span class="record-date">{{ record.date }}</span>
        </div>
        <div class="record-right">
          <span class="record-score" :style="{ color: scoreColor(record.score, record.maxScore) }">{{ record.score }}/{{ record.maxScore }}</span>
        </div>
      </div>
      <p v-if="completedRecords.length === 0" class="empty-text">暂无记录</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeCategory = ref('all')
const categories = [
  { key: 'all', label: '全部' },
  { key: 'mood', label: '情绪' },
  { key: 'stress', label: '压力' },
  { key: 'wellbeing', label: '幸福感' },
  { key: 'behavior', label: '行为' },
]

const recommended = ref([
  { id: 'phq9', name: 'PHQ-9 抑郁筛查', description: '患者健康问卷-9项，评估抑郁症状严重程度', icon: '😔', color: '#e6f7ff', questionCount: 9, estimatedMin: 3 },
])

const allQuestionnaires = ref([
  { id: 'phq9', name: 'PHQ-9 抑郁筛查', description: '评估过去两周的抑郁症状', icon: '😔', color: '#e6f7ff', questionCount: 9, estimatedMin: 3, category: 'mood', completedCount: 2 },
  { id: 'gad7', name: 'GAD-7 焦虑评估', description: '广泛性焦虑障碍7项量表', icon: '😰', color: '#fff7e6', questionCount: 7, estimatedMin: 3, category: 'mood', completedCount: 1 },
  { id: 'pss10', name: 'PSS-10 压力感知', description: '感知压力量表10项版', icon: '😤', color: '#fff1f0', questionCount: 10, estimatedMin: 5, category: 'stress', completedCount: 1 },
  { id: 'who5', name: 'WHO-5 幸福指数', description: 'WHO五项幸福感指数', icon: '😊', color: '#f6ffed', questionCount: 5, estimatedMin: 2, category: 'wellbeing', completedCount: 1 },
  { id: 'audit', name: 'AUDIT 饮酒评估', description: '酒精使用障碍识别测试', icon: '🍷', color: '#f9f0ff', questionCount: 10, estimatedMin: 5, category: 'behavior', completedCount: 0 },
  { id: 'ipaq', name: 'IPAQ 体力活动', description: '国际体力活动问卷-短版', icon: '🏃', color: '#e6fffb', questionCount: 7, estimatedMin: 4, category: 'behavior', completedCount: 0 },
  { id: 'psqi', name: 'PSQI 睡眠质量', description: '匹兹堡睡眠质量指数', icon: '😴', color: '#f0f5ff', questionCount: 19, estimatedMin: 8, category: 'wellbeing', completedCount: 0 },
  { id: 'dass21', name: 'DASS-21 综合评估', description: '抑郁-焦虑-压力量表21项', icon: '📋', color: '#fffbe6', questionCount: 21, estimatedMin: 10, category: 'mood', completedCount: 0 },
])

const filteredQuestionnaires = computed(() => {
  if (activeCategory.value === 'all') return allQuestionnaires.value
  return allQuestionnaires.value.filter(q => q.category === activeCategory.value)
})

const completedRecords = ref([
  { id: 'r1', name: 'GAD-7 焦虑评估', date: '2025-01-15', score: 8, maxScore: 21 },
  { id: 'r2', name: 'PHQ-9 抑郁筛查', date: '2025-01-10', score: 5, maxScore: 27 },
  { id: 'r3', name: 'WHO-5 幸福指数', date: '2025-01-05', score: 56, maxScore: 100 },
  { id: 'r4', name: 'PSS-10 压力感知', date: '2024-12-28', score: 22, maxScore: 40 },
])

const scoreColor = (score, max) => {
  const pct = score / max
  if (pct >= 0.7) return '#cf1322'
  if (pct >= 0.4) return '#d4b106'
  return '#389e0d'
}
</script>

<style scoped>
.assessment-list { max-width: 600px; margin: 0 auto; padding: 16px; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-header h2 { flex: 1; margin: 0; font-size: 18px; }
.back-btn { padding: 6px 16px; border: 1px solid #d9d9d9; border-radius: 6px; background: #fff; cursor: pointer; }

.section { margin-bottom: 20px; }
.section-title { font-size: 15px; font-weight: 600; color: #333; margin: 0 0 12px; }

.category-tabs { display: flex; gap: 6px; margin-bottom: 12px; overflow-x: auto; }
.cat-tab { padding: 4px 14px; border: 1px solid #d9d9d9; border-radius: 16px; background: #fff; cursor: pointer; font-size: 13px; white-space: nowrap; }
.cat-tab.active { background: #1890ff; color: #fff; border-color: #1890ff; }

.assess-card { display: flex; align-items: center; gap: 12px; padding: 14px; background: #fff; border: 1px solid #f0f0f0; border-radius: 10px; margin-bottom: 8px; cursor: pointer; position: relative; }
.assess-card:hover { background: #fafafa; }
.assess-card.recommended { border-color: #91d5ff; background: #e6f7ff; }
.assess-badge { position: absolute; top: 0; right: 0; background: #1890ff; color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 0 10px 0 6px; }
.assess-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.assess-info { flex: 1; }
.assess-name { display: block; font-size: 14px; font-weight: 600; color: #333; }
.assess-desc { font-size: 12px; color: #999; }
.assess-meta { display: flex; gap: 8px; margin-top: 4px; font-size: 11px; color: #bbb; }
.completed-badge { color: #1890ff; }
.assess-arrow { font-size: 18px; color: #ccc; }

.record-card { display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px; margin-bottom: 6px; cursor: pointer; }
.record-card:hover { background: #fafafa; }
.record-name { display: block; font-size: 14px; font-weight: 500; color: #333; }
.record-date { font-size: 12px; color: #999; }
.record-score { font-size: 16px; font-weight: 600; }
.empty-text { text-align: center; color: #ccc; padding: 16px; }
</style>
