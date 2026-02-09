<template>
  <div class="grid grid-cols-2 gap-0 h-[calc(100vh-140px)] shadow-2xl rounded-2xl overflow-hidden">
    <!-- Left: Raw Truth (dark) -->
    <div class="flex flex-col bg-gradient-to-br from-slate-600 via-slate-500 to-slate-600 p-6 overflow-y-auto relative">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-white font-bold text-lg flex items-center gap-2">
          <span class="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
          底层行为证据
          <span class="text-slate-400 text-sm font-normal">Raw Truth</span>
        </h2>
        <span class="px-3 py-1 bg-red-600 text-white text-xs font-black rounded-lg shadow-lg tracking-wider">
          RISK: {{ auditCase.rawMetrics.riskLevel }}
        </span>
      </div>

      <a-tabs v-model:activeKey="rawTab" class="expert-dark-tabs" size="small">
        <a-tab-pane key="baps" tab="BAPS 评估">
          <div class="space-y-3 mt-4" v-if="auditCase.rawMetrics.bigFive">
            <div class="text-xs text-amber-400 uppercase tracking-wider font-bold mb-2">
              ⚠ 以下内容仅限专业人员可见，严禁直接展示给用户
            </div>
            <div v-for="(value, key) in auditCase.rawMetrics.bigFive" :key="key" class="flex items-center gap-3">
              <span class="text-slate-200 text-sm w-24">{{ bigFiveLabels[key] }}: {{ value }}</span>
              <div class="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-500" :style="{ width: `${value}%` }" />
              </div>
            </div>
          </div>
          <div v-if="auditCase.bapsProfile" class="mt-4 bg-slate-700/50 p-4 rounded-xl border border-slate-500/40">
            <pre class="text-xs text-slate-300 font-mono whitespace-pre-wrap">{{ JSON.stringify(auditCase.bapsProfile, null, 2) }}</pre>
          </div>
        </a-tab-pane>

        <a-tab-pane key="clinical" tab="临床数据">
          <div class="bg-slate-700/50 p-4 rounded-xl border border-red-400/40 mt-4">
            <p class="text-xs text-red-400 uppercase mb-2 tracking-wider font-bold">原始诊断建议 (L5 Output)</p>
            <p class="text-sm font-mono text-slate-200 leading-relaxed">{{ auditCase.originalL5Output }}</p>
          </div>
          <CGMChart class="mt-4" :cv="auditCase.rawMetrics.cgmCV" />
          <div class="grid grid-cols-2 gap-3 mt-4">
            <MetricCard label="PHQ-9 原始分" :value="auditCase.rawMetrics.phq9" unit="分" />
            <MetricCard label="CGM 节律" :value="auditCase.rawMetrics.cgmTrend" />
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- Right: Growth Journey (light) -->
    <div class="flex flex-col bg-gradient-to-br from-green-50 via-white to-green-50 p-6 overflow-y-auto">
      <h2 class="text-green-900 font-bold text-lg mb-2 flex items-center gap-2">
        叙事改写预览
        <span class="text-green-600 text-sm font-normal">Growth Journey</span>
      </h2>
      <div class="h-1 w-16 bg-gradient-to-r from-green-500 to-green-300 rounded-full mb-6" />

      <div class="flex-1">
        <a-textarea
          v-model:value="editedNarrative"
          :rows="8"
          placeholder="编辑发送给用户的文字..."
          class="!rounded-xl !border-green-200 !text-lg !leading-loose"
        />
        <div class="mt-4 bg-green-100/50 p-6 rounded-2xl border-2 border-green-200/50">
          <p class="text-sm text-slate-500 mb-2">实时预览（用户端视角）：</p>
          <p class="text-base text-green-900 leading-relaxed italic">{{ editedNarrative }}</p>
        </div>
        <div v-if="editedNarrative" class="mt-2 flex items-center gap-2 text-sm text-green-600">
          <span class="w-4 h-4 bg-green-500 rounded flex items-center justify-center text-white text-xs">✓</span>
          内容已脱敏，可以发布
        </div>
      </div>

      <div class="mt-6 pt-6 border-t-2 border-green-200">
        <p class="text-xs text-slate-500 mb-3 uppercase tracking-wide font-bold">双专家审核签名</p>
        <div class="flex gap-3 mb-4">
          <button
            v-for="sign in signButtons" :key="sign.key"
            @click="signs[sign.key] = !signs[sign.key]"
            class="flex-1 p-3 rounded-xl border-2 transition-all flex items-center justify-center gap-2"
            :class="signs[sign.key]
              ? 'border-green-500 bg-green-50 text-green-800 shadow-md'
              : 'border-slate-200 bg-slate-50 text-slate-500 hover:bg-slate-100'"
          >
            <span
              class="w-4 h-4 rounded-full border-2 flex items-center justify-center"
              :class="signs[sign.key] ? 'bg-green-500 border-green-500' : 'border-slate-300'"
            >
              <span v-if="signs[sign.key]" class="text-white text-xs">✓</span>
            </span>
            <span class="text-sm font-bold">{{ sign.label }}</span>
          </button>
        </div>

        <a-button
          type="primary"
          block
          size="large"
          :disabled="!signs.master || !signs.secondary"
          :loading="publishing"
          @click="handlePublish"
          class="!rounded-xl !h-12 !font-bold !text-base"
          :class="{ '!bg-green-600 !border-green-600': signs.master && signs.secondary }"
        >
          {{ publishStatus === 'success' ? '✓ 发布成功' : publishStatus === 'error' ? '✗ 发布失败' : '发布至用户终端' }}
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import CGMChart from '@/components/expert/CGMChart.vue'
import MetricCard from '@/components/expert/MetricCard.vue'
import { publishAuditResult, type AuditCase } from '@/api/expert'

const props = defineProps<{ auditCase: AuditCase }>()

const bigFiveLabels: Record<string, string> = { N: '神经质(N)', E: '外向性(E)', O: '开放性(O)', A: '宜人性(A)', C: '尽责性(C)' }
const rawTab = ref('clinical')
const editedNarrative = ref(props.auditCase.narrativeL6Preview)
const signs = reactive({ master: false, secondary: false })
const publishing = ref(false)
const publishStatus = ref<'idle' | 'success' | 'error'>('idle')

const signButtons = [
  { key: 'master' as const, label: '主签专家 (专业性)' },
  { key: 'secondary' as const, label: '副签专家 (合规性)' },
]

const handlePublish = async () => {
  if (!signs.master || !signs.secondary) return
  publishing.value = true
  try {
    await publishAuditResult({
      caseId: props.auditCase.id,
      patientId: props.auditCase.patientId,
      masterSignerId: 'current_expert_id',
      secondarySignerId: 'secondary_expert_id',
      originalL5Output: props.auditCase.originalL5Output,
      approvedL6Output: editedNarrative.value,
      riskLevel: props.auditCase.rawMetrics.riskLevel,
    })
    publishStatus.value = 'success'
    message.success('已发布至用户终端')
  } catch {
    publishStatus.value = 'error'
    message.error('发布失败，请重试')
  } finally {
    publishing.value = false
    setTimeout(() => { publishStatus.value = 'idle' }, 3000)
  }
}
</script>
