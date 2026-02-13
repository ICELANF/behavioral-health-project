<!--
  RxComputeForm.vue — 处方计算表单
  ===================================
  三维上下文输入: TTM阶段 × BigFive人格 × CAPACITY能力
  支持手动输入 + 从评估数据导入
-->

<template>
  <div class="rx-form">
    <div class="form-header">
      <h3>
        <medicine-box-outlined /> 计算行为处方
      </h3>
      <a-button size="small" @click="ctx.reset()">重置</a-button>
    </div>

    <a-form layout="vertical" class="form-body">
      <!-- 维度 1: TTM -->
      <div class="form-section">
        <div class="section-title">
          <step-forward-outlined /> 维度一: TTM 行为改变阶段
        </div>

        <a-form-item label="当前阶段 (S0-S6)">
          <a-slider
            v-model:value="ctx.ttmStage.value"
            :min="0"
            :max="6"
            :marks="ttmMarks"
            :tooltip-visible="true"
          />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="阶段就绪度">
              <a-slider
                v-model:value="ctx.stageReadiness.value"
                :min="0"
                :max="1"
                :step="0.05"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="阶段稳定度">
              <a-slider
                v-model:value="ctx.stageStability.value"
                :min="0"
                :max="1"
                :step="0.05"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- 维度 2: BigFive -->
      <div class="form-section">
        <div class="section-title">
          <user-outlined /> 维度二: BigFive 五因子人格
        </div>

        <a-row :gutter="12">
          <a-col :span="12" v-for="trait in bigFiveTraits" :key="trait.key">
            <a-form-item :label="`${trait.label} (${trait.key})`">
              <a-slider
                v-model:value="ctx.personality.value[trait.key]"
                :min="0"
                :max="100"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <BigFiveRadar :profile="ctx.personality.value" :size="200" class="radar-preview" />
      </div>

      <!-- 维度 3: CAPACITY -->
      <div class="form-section">
        <div class="section-title">
          <dashboard-outlined /> 维度三: 能力与效能
        </div>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="CAPACITY 综合能力">
              <a-slider
                v-model:value="ctx.capacityScore.value"
                :min="0"
                :max="1"
                :step="0.05"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="自我效能感">
              <a-slider
                v-model:value="ctx.selfEfficacy.value"
                :min="0"
                :max="1"
                :step="0.05"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>

      <!-- 附加上下文 -->
      <div class="form-section">
        <div class="section-title">
          <profile-outlined /> 附加上下文
        </div>

        <a-form-item label="近期依从率">
          <a-slider
            v-model:value="ctx.recentAdherence.value"
            :min="0"
            :max="1"
            :step="0.05"
          />
        </a-form-item>

        <a-form-item label="风险级别">
          <a-radio-group v-model:value="ctx.riskLevel.value" button-style="solid" size="small">
            <a-radio-button value="low">低</a-radio-button>
            <a-radio-button value="normal">正常</a-radio-button>
            <a-radio-button value="elevated">偏高</a-radio-button>
            <a-radio-button value="high">高</a-radio-button>
            <a-radio-button value="critical">危急</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="活跃障碍">
          <a-select
            v-model:value="ctx.activeBarriers.value"
            mode="tags"
            placeholder="输入障碍标签"
            :options="barrierOptions"
          />
        </a-form-item>
      </div>

      <!-- 计算选项 -->
      <div class="form-section">
        <div class="section-title">
          <setting-outlined /> 计算选项
        </div>

        <a-form-item label="指定 Agent (可选)">
          <a-select
            v-model:value="selectedAgent"
            placeholder="自动选择"
            allow-clear
          >
            <a-select-option
              v-for="agent in agentOptions"
              :key="agent.value"
              :value="agent.value"
            >
              {{ agent.icon }} {{ agent.label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="强制策略 (可选)">
          <a-select
            v-model:value="forceStrategy"
            placeholder="自动推荐"
            allow-clear
            :options="strategyOptions"
          />
        </a-form-item>
      </div>

      <!-- 提交 -->
      <div class="form-actions">
        <a-button
          type="primary"
          size="large"
          block
          :loading="computing"
          @click="handleCompute"
        >
          <thunderbolt-outlined /> 生成行为处方
        </a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, toRef } from 'vue'
import {
  MedicineBoxOutlined,
  StepForwardOutlined,
  UserOutlined,
  DashboardOutlined,
  ProfileOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useRxStore } from '../../stores/rxStore'
import { useRxContextBuilder } from '../../composables/useRx'
import BigFiveRadar from './BigFiveRadar.vue'
import type { ExpertAgentType, RxStrategyType } from '../../types/rx'
import { AGENT_LABELS, STRATEGY_LABELS } from '../../types/rx'

interface Props {
  userId: string
}

const props = defineProps<Props>()
const emit = defineEmits(['computed'])

const store = useRxStore()
const ctx = useRxContextBuilder(toRef(props, 'userId'))

const computing = ref(false)
const selectedAgent = ref<ExpertAgentType | undefined>()
const forceStrategy = ref<RxStrategyType | undefined>()

// TTM 刻度标签
const ttmMarks = {
  0: 'S0',
  1: 'S1',
  2: 'S2',
  3: 'S3',
  4: 'S4',
  5: 'S5',
  6: 'S6',
}

// BigFive 配置
const bigFiveTraits = [
  { key: 'O' as const, label: '开放性' },
  { key: 'C' as const, label: '尽责性' },
  { key: 'E' as const, label: '外向性' },
  { key: 'A' as const, label: '宜人性' },
  { key: 'N' as const, label: '神经质' },
]

// Agent 选项
const agentOptions = Object.entries(AGENT_LABELS).map(([value, info]) => ({
  value,
  label: info.name,
  icon: info.icon,
}))

// 策略选项
const strategyOptions = Object.entries(STRATEGY_LABELS).map(([value, label]) => ({
  value,
  label,
}))

// 障碍预设选项
const barrierOptions = [
  '时间不足', '动力缺乏', '知识欠缺', '环境制约',
  '社交压力', '情绪困扰', '身体限制', '经济因素',
  '认知偏差', '习惯惯性',
].map((b) => ({ value: b, label: b }))

// 计算处方
async function handleCompute() {
  computing.value = true
  try {
    const result = await store.computePrescription(ctx.context.value, {
      agentType: selectedAgent.value,
      forceStrategy: forceStrategy.value,
    })
    message.success(`处方已生成 (${Math.round(result.computation_time_ms)}ms)`)
    emit('computed', result)
  } catch (e: any) {
    message.error(e.message || '计算失败')
  } finally {
    computing.value = false
  }
}
</script>

<style scoped>
.rx-form {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px;
  border-bottom: 1px solid #f0f0f0;
}

.form-header h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-body {
  padding: 18px;
}

.form-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #f0f0f0;
}

.form-section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.radar-preview {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.form-actions {
  padding-top: 8px;
}
</style>
