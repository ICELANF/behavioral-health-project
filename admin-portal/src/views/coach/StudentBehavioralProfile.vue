<template>
  <div class="student-behavioral-profile">
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/coach/my/students">我的学员</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>行为画像</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <!-- 顶部: 学员信息 + 阶段仪表盘 -->
      <a-row :gutter="16">
        <a-col :xs="24" :lg="8">
          <a-card :bordered="false" title="学员信息">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="姓名">{{ data.student?.full_name || data.student?.username }}</a-descriptions-item>
              <a-descriptions-item label="ID">{{ data.student?.id }}</a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="16">
          <a-card :bordered="false" title="行为阶段">
            <div class="stage-dashboard">
              <div class="stage-current">
                <div class="stage-badge" :class="stageClass">
                  {{ profile?.stage?.current || 'S0' }}
                </div>
                <div class="stage-info">
                  <h3>{{ profile?.stage?.name || '未评估' }}</h3>
                  <p>{{ profile?.stage?.description }}</p>
                  <a-space>
                    <a-tag v-if="profile?.stage?.stability" :color="stabilityColor">
                      {{ stabilityLabel }}
                    </a-tag>
                    <a-tag v-if="profile?.stage?.confidence">
                      置信度: {{ (profile.stage.confidence * 100).toFixed(0) }}%
                    </a-tag>
                  </a-space>
                </div>
              </div>
              <!-- 阶段进度条 -->
              <div class="stage-progress">
                <div
                  v-for="s in stages"
                  :key="s.code"
                  class="stage-step"
                  :class="{ active: s.code === profile?.stage?.current, passed: stageIndex(s.code) < stageIndex(profile?.stage?.current) }"
                >
                  <div class="step-dot" />
                  <div class="step-label">{{ s.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 第二行: 行为类型 + 心理层级 + 交互模式 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :xs="24" :md="12" :lg="8">
          <a-card :bordered="false" title="行为类型 (BPT-6)">
            <a-statistic :value="bpt6Label" :value-style="{ fontSize: '20px', fontWeight: 600 }" />
            <div v-if="profile?.behavior_type?.scores" style="margin-top: 12px">
              <div v-for="(score, dim) in profile.behavior_type.scores" :key="dim" class="dim-bar">
                <span class="dim-label">{{ dim }}</span>
                <a-progress :percent="Math.min(100, score * 10)" :show-info="false" size="small" />
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :xs="24" :md="12" :lg="8">
          <a-card :bordered="false" title="心理层级 & 交互模式">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="心理层级">
                <a-tag :color="psychLevelColor">{{ psychLevelLabel }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="交互模式">
                <a-tag :color="modeColor">{{ modeLabel }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="SPI 分数">
                {{ profile?.spi?.score?.toFixed(1) || '--' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <a-col :xs="24" :md="12" :lg="8">
          <a-card :bordered="false" title="改变潜力 (CAPACITY)">
            <a-statistic title="总分" :value="profile?.capacity?.total || '--'" />
            <div style="margin-top: 8px">
              <div v-if="profile?.capacity?.weak?.length">
                <span style="color: #ff4d4f; font-size: 12px">弱项: </span>
                <a-tag v-for="w in profile.capacity.weak" :key="w" color="red" size="small">{{ w }}</a-tag>
              </div>
              <div v-if="profile?.capacity?.strong?.length" style="margin-top: 4px">
                <span style="color: #52c41a; font-size: 12px">强项: </span>
                <a-tag v-for="s in profile.capacity.strong" :key="s" color="green" size="small">{{ s }}</a-tag>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 第三行: 风险标记 + 教练推荐动作 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :xs="24" :lg="8">
          <a-card :bordered="false" title="风险标记">
            <a-empty v-if="!profile?.risk_flags?.length" description="无风险标记" :image-style="{ height: '40px' }" />
            <div v-else>
              <a-alert
                v-for="flag in profile.risk_flags"
                :key="flag"
                :message="riskFlagLabel(flag)"
                :type="riskFlagType(flag)"
                show-icon
                style="margin-bottom: 8px"
              />
            </div>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="16">
          <a-card :bordered="false" title="推荐教练动作">
            <a-list :data-source="data.coach_actions || []" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :description="item.action">
                    <template #title>
                      <a-tag :color="priorityColor(item.priority)">{{ item.priority }}</a-tag>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>

      <!-- 第四行: 领域干预矩阵 -->
      <a-card :bordered="false" title="领域干预策略" style="margin-top: 16px">
        <a-empty v-if="!interventions.length" description="暂无干预计划" />
        <a-collapse v-else>
          <a-collapse-panel
            v-for="di in interventions"
            :key="di.domain"
            :header="`${di.domain_name} (${di.rx_name})`"
          >
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="阶段策略">{{ di.stage_strategy }}</a-descriptions-item>
              <a-descriptions-item label="语气">{{ di.tone }}</a-descriptions-item>
              <a-descriptions-item label="核心目标" :span="2">{{ di.core_goal }}</a-descriptions-item>
              <a-descriptions-item label="难度">{{ di.difficulty_level }}</a-descriptions-item>
              <a-descriptions-item label="强度系数">{{ di.intensity_multiplier }}</a-descriptions-item>
            </a-descriptions>

            <a-divider orientation="left" plain>推荐行为</a-divider>
            <a-tag v-for="d in di.do_list" :key="d" color="green" style="margin-bottom: 4px">{{ d }}</a-tag>

            <a-divider orientation="left" plain>禁忌行为</a-divider>
            <a-tag v-for="d in di.dont_list" :key="d" color="red" style="margin-bottom: 4px">{{ d }}</a-tag>

            <a-divider orientation="left" plain>建议模板</a-divider>
            <div v-for="(script, key) in di.scripts" :key="key" style="margin-bottom: 8px">
              <strong>{{ key }}:</strong> {{ script }}
            </div>

            <a-divider orientation="left" plain>具体建议</a-divider>
            <a-list :data-source="di.advice" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :title="item.title" :description="item.description" />
                </a-list-item>
              </template>
            </a-list>
          </a-collapse-panel>
        </a-collapse>
      </a-card>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const route = useRoute()
const studentId = route.params.id as string

const loading = ref(false)
const data = ref<any>({})

const profile = computed(() => data.value?.behavioral_profile || {})
const interventions = computed(() => data.value?.intervention_plan?.domain_interventions || [])

const stages = [
  { code: 'S0', label: 'S0 无觉' },
  { code: 'S1', label: 'S1 抗拒' },
  { code: 'S2', label: 'S2 被动' },
  { code: 'S3', label: 'S3 接受' },
  { code: 'S4', label: 'S4 尝试' },
  { code: 'S5', label: 'S5 践行' },
  { code: 'S6', label: 'S6 内化' },
]

function stageIndex(code: string | undefined) {
  if (!code) return -1
  return stages.findIndex(s => s.code === code)
}

const stageClass = computed(() => {
  const s = profile.value?.stage?.current
  if (!s) return 'stage-unknown'
  const idx = stageIndex(s)
  if (idx <= 1) return 'stage-early'
  if (idx <= 3) return 'stage-mid'
  return 'stage-late'
})

const stabilityColor = computed(() => {
  const v = profile.value?.stage?.stability
  if (v === 'stable') return 'green'
  if (v === 'semi_stable') return 'orange'
  return 'red'
})

const stabilityLabel = computed(() => {
  const map: Record<string, string> = { stable: '稳定', semi_stable: '半稳定', unstable: '不稳定' }
  return map[profile.value?.stage?.stability] || '未知'
})

const BPT6_NAMES: Record<string, string> = {
  action: '行动型', knowledge: '知识型', emotion: '情绪型',
  relation: '关系型', environment: '环境型', mixed: '混合型',
}
const bpt6Label = computed(() => BPT6_NAMES[profile.value?.behavior_type?.primary] || '未评估')

const PSYCH_LEVELS: Record<string, { label: string; color: string }> = {
  L1: { label: 'L1 需大量支持', color: 'red' },
  L2: { label: 'L2 需中度支持', color: 'orange' },
  L3: { label: 'L3 基本就绪', color: 'blue' },
  L4: { label: 'L4 高度就绪', color: 'green' },
  L5: { label: 'L5 自驱型', color: 'purple' },
}
const psychLevelColor = computed(() => PSYCH_LEVELS[profile.value?.psychological_level]?.color || 'default')
const psychLevelLabel = computed(() => PSYCH_LEVELS[profile.value?.psychological_level]?.label || '未评估')

const MODE_MAP: Record<string, { label: string; color: string }> = {
  empathy: { label: '共情模式', color: 'blue' },
  challenge: { label: '挑战模式', color: 'orange' },
  execution: { label: '执行模式', color: 'green' },
}
const modeColor = computed(() => MODE_MAP[profile.value?.interaction_mode]?.color || 'default')
const modeLabel = computed(() => MODE_MAP[profile.value?.interaction_mode]?.label || '未确定')

function riskFlagLabel(flag: string) {
  const map: Record<string, string> = {
    dropout_risk: '流失风险 - 学员可能中断行为改变',
    relapse_risk: '回退风险 - 学员可能退回上一阶段',
    low_confidence_risk: '低信心风险 - SPI分数偏低',
  }
  return map[flag] || flag
}

function riskFlagType(flag: string) {
  if (flag === 'dropout_risk') return 'error'
  if (flag === 'relapse_risk') return 'warning'
  return 'info'
}

function priorityColor(p: string) {
  if (p === 'urgent') return 'red'
  if (p === 'high') return 'orange'
  return 'blue'
}

async function loadProfile() {
  loading.value = true
  try {
    const res = await request.get(`/v1/coach/students/${studentId}/behavioral-profile`)
    data.value = res.data
  } catch (e: any) {
    data.value = {}
    message.error('加载行为画像失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.stage-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stage-current {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stage-badge {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.stage-early { background: linear-gradient(135deg, #ff6b6b, #ee5a24); }
.stage-mid { background: linear-gradient(135deg, #ffa502, #e1b12c); }
.stage-late { background: linear-gradient(135deg, #2ed573, #1abc9c); }
.stage-unknown { background: #bbb; }

.stage-info h3 { margin: 0 0 4px 0; }
.stage-info p { margin: 0 0 8px 0; color: #666; font-size: 13px; }

.stage-progress {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.stage-progress::before {
  content: '';
  position: absolute;
  top: 8px;
  left: 20px;
  right: 20px;
  height: 2px;
  background: #e8e8e8;
}

.stage-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  z-index: 1;
}

.step-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #e8e8e8;
  border: 2px solid #fff;
}

.stage-step.passed .step-dot { background: #52c41a; }
.stage-step.active .step-dot { background: #1890ff; box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.2); }

.step-label { font-size: 11px; color: #999; }
.stage-step.active .step-label { color: #1890ff; font-weight: 600; }
.stage-step.passed .step-label { color: #52c41a; }

.dim-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.dim-label {
  width: 80px;
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
}

@media (max-width: 640px) {
  .student-behavioral-profile { padding: 8px !important; }
  .stage-current { flex-direction: column; align-items: flex-start; gap: 12px; }
  .stage-badge { width: 48px; height: 48px; font-size: 16px; }
  .stage-progress { flex-wrap: wrap; gap: 4px; justify-content: flex-start; }
  .step-label { font-size: 10px; }
  .ant-btn { min-height: 44px; }
  h2, h3 { font-size: 16px; }
  .ant-card { margin-bottom: 12px !important; }
  .dim-label { width: 60px; font-size: 11px; }
}
</style>
