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
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const activeCategory = ref('all')
const categories = [
  { key: 'all', label: '全部' },
  { key: 'mood', label: '情绪' },
  { key: 'stress', label: '压力' },
  { key: 'wellbeing', label: '幸福感' },
  { key: 'behavior', label: '行为' },
]

const recommended = ref([])
const allQuestionnaires = ref([])

const filteredQuestionnaires = computed(() => {
  if (activeCategory.value === 'all') return allQuestionnaires.value
  return allQuestionnaires.value.filter(q => q.category === activeCategory.value)
})

const completedRecords = ref([])

const iconMap = { phq9: '😔', gad7: '😰', pss10: '😤', who5: '😊', audit: '🍷', ipaq: '🏃', psqi: '😴', dass21: '📋' }
const colorMap = { phq9: '#e6f7ff', gad7: '#fff7e6', pss10: '#fff1f0', who5: '#f6ffed', audit: '#f9f0ff', ipaq: '#e6fffb', psqi: '#f0f5ff', dass21: '#fffbe6' }

const loadAssessments = async () => {
  if (!localStorage.getItem('admin_token')) return
  try {
    const [catalogRes, recordsRes] = await Promise.allSettled([
      request.get('v1/assessments'),
      request.get('v1/assessments/my-results'),
    ])
    if (catalogRes.status === 'fulfilled') {
      const items = catalogRes.value.data?.items || catalogRes.value.data || []
      allQuestionnaires.value = items.map((q) => ({
        id: q.id || q.code || '', name: q.name || q.title || '',
        description: q.description || '', icon: iconMap[q.code] || '📋',
        color: colorMap[q.code] || '#f5f5f5',
        questionCount: q.question_count ?? q.questionCount ?? 0,
        estimatedMin: q.estimated_min ?? q.estimatedMin ?? 5,
        category: q.category || 'mood', completedCount: q.completed_count ?? q.completedCount ?? 0,
      }))
      recommended.value = items.filter((q) => q.recommended).map((q) => ({
        id: q.id || q.code || '', name: q.name || q.title || '',
        description: q.description || '', icon: iconMap[q.code] || '📋',
        color: colorMap[q.code] || '#f5f5f5',
        questionCount: q.question_count ?? q.questionCount ?? 0,
        estimatedMin: q.estimated_min ?? q.estimatedMin ?? 5,
      }))
    } else {
      console.error('加载问卷目录失败:', catalogRes.reason)
    }
    if (recordsRes.status === 'fulfilled') {
      const items = recordsRes.value.data?.items || recordsRes.value.data || []
      completedRecords.value = items.map((r) => ({
        id: String(r.id), name: r.name || r.questionnaire_name || '',
        date: r.date || r.completed_at || '', score: r.score ?? 0, maxScore: r.max_score ?? r.maxScore ?? 100,
      }))
    } else {
      console.error('加载完成记录失败:', recordsRes.reason)
    }
  } catch (e) {
    console.error('加载测评数据失败:', e)
  }
}

onMounted(loadAssessments)

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
