<template>
  <div class="my-certification">
    <div class="page-header">
      <h2>我的认证</h2>
    </div>

    <!-- Loading -->
    <div v-if="loading" style="text-align: center; padding: 60px 0">
      <a-spin size="large" tip="加载认证信息..." />
    </div>

    <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom: 16px" />

    <template v-if="!loading && !error">
      <!-- Current Level -->
      <a-card class="level-card" style="margin-bottom: 16px">
        <div class="current-level">
          <div class="level-badge" :style="{ background: currentLevel.color }">
            {{ currentLevel.code }}
          </div>
          <div class="level-info">
            <h3>{{ currentLevel.name }}</h3>
            <p class="level-desc">{{ currentLevel.description }}</p>
            <p class="level-since">认证时间: {{ currentLevel.since ?? '--' }}</p>
          </div>
        </div>

        <!-- Upgrade progress -->
        <div v-if="nextLevel.code" class="upgrade-section">
          <div class="upgrade-header">
            <span>升级至 {{ nextLevel.name }}</span>
            <span class="upgrade-pct">{{ upgradeProgress }}%</span>
          </div>
          <a-progress :percent="upgradeProgress" :stroke-color="{ from: currentLevel.color, to: '#722ed1' }" :show-info="false" />
          <div class="upgrade-requirements">
            <div v-for="req in requirements" :key="req.label" class="req-item" :class="{ completed: req.completed }">
              <span class="req-check">{{ req.completed ? '\u2713' : '\u25CB' }}</span>
              <span class="req-label">{{ req.label }}</span>
              <span class="req-value">{{ req.current }} / {{ req.target }}</span>
            </div>
          </div>
          <a-button type="primary" :disabled="upgradeProgress < 100" block style="margin-top: 12px">
            {{ upgradeProgress >= 100 ? '申请晋级' : '未达到晋级条件' }}
          </a-button>
        </div>

        <div v-else class="upgrade-section" style="text-align: center;">
          <a-result status="success" title="已达最高等级" sub-title="恭喜！您已达到行为健康教练最高认证等级。" />
        </div>
      </a-card>

      <!-- Real Stats -->
      <a-card title="执业数据" style="margin-bottom: 16px">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-statistic title="服务学员数" :value="stats.total_students" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="发送消息数" :value="stats.total_messages" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="学员测评数" :value="stats.total_assessments" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="风险改善学员" :value="stats.improved_students" :value-style="{ color: '#3f8600' }" />
          </a-col>
        </a-row>
      </a-card>

      <!-- Level Roadmap -->
      <a-card title="认证路径">
        <a-steps :current="levelIndex" direction="vertical" size="small">
          <a-step v-for="(lv, i) in levelRoadmap" :key="lv.code" :title="`${lv.code} ${lv.name}`"
            :description="lv.desc"
            :status="i < levelIndex ? 'finish' : i === levelIndex ? 'process' : 'wait'" />
        </a-steps>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'

import request from '@/api/request'

const loading = ref(true)
const error = ref('')

const currentLevel = ref<any>({ code: '--', name: '加载中', description: '', color: '#d9d9d9', since: null })
const nextLevel = ref<any>({ code: null, name: '' })
const upgradeProgress = ref(0)
const requirements = ref<any[]>([])
const stats = ref({ total_students: 0, total_messages: 0, total_assessments: 0, improved_students: 0 })

const levelRoadmap = [
  { code: 'L0', name: '观察员', desc: '入门阶段，学习基础知识' },
  { code: 'L1', name: '成长者', desc: '行为养成践行者·效果的唯一承载体' },
  { code: 'L2', name: '分享者', desc: '同伴支持者·经验传递与陪伴者' },
  { code: 'L3', name: '教练', desc: '系统翻译者·行为改变实施者' },
  { code: 'L4', name: '促进师', desc: '行为健康促进专家·督导与培训者' },
  { code: 'L5', name: '大师', desc: '行为健康领域权威·体系构建者' },
]

const levelIndex = ref(0)

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await request.get('/v1/coach/my-certification')

    currentLevel.value = data.current_level || currentLevel.value
    nextLevel.value = data.next_level || { code: null, name: '' }
    upgradeProgress.value = data.upgrade_progress ?? 0
    requirements.value = data.requirements || []
    stats.value = data.stats || stats.value

    const idx = levelRoadmap.findIndex(l => l.code === currentLevel.value.code)
    levelIndex.value = idx >= 0 ? idx : 0
  } catch (e: any) {
    console.error('加载认证数据失败:', e)
    error.value = '加载认证数据失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }

.current-level { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.level-badge { width: 64px; height: 64px; border-radius: 50%; color: #fff; font-size: 24px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.level-info h3 { margin: 0 0 4px; font-size: 18px; }
.level-desc { margin: 0; font-size: 13px; color: #666; }
.level-since { margin: 2px 0 0; font-size: 12px; color: #999; }

.upgrade-section { background: #fafafa; border-radius: 8px; padding: 16px; }
.upgrade-header { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; font-weight: 500; }
.upgrade-pct { color: #1890ff; }
.upgrade-requirements { margin-top: 12px; }
.req-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.req-item.completed { color: #389e0d; }
.req-check { font-size: 14px; min-width: 20px; }
.req-label { flex: 1; }
.req-value { font-weight: 500; }

@media (max-width: 640px) {
  .my-certification { padding: 8px !important; }
  .current-level { flex-direction: column; align-items: flex-start; gap: 12px; }
  .level-badge { width: 48px; height: 48px; font-size: 18px; }
  .level-info h3 { font-size: 16px; }
  .upgrade-section { padding: 12px; }
  .req-item { font-size: 12px; gap: 6px; }
  .ant-btn { min-height: 44px; }
  h2 { font-size: 16px; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>
