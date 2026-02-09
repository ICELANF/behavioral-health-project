<template>
  <div class="flex flex-col lg:flex-row gap-6 p-6 bg-slate-50 rounded-2xl border border-slate-200 shadow-lg">
    <!-- Left: Code panel -->
    <div class="flex-1 bg-[#1e1e1e] rounded-xl p-5 font-mono text-sm">
      <div class="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
        <div class="flex gap-1.5">
          <div class="w-2.5 h-2.5 rounded-full bg-red-500" />
          <div class="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <div class="w-2.5 h-2.5 rounded-full bg-green-500" />
        </div>
        <span class="text-white/40 text-xs ml-2">spi_mapping.json</span>
      </div>
      <div class="space-y-1">
        <code class="text-white/40">{</code>
        <div
          v-for="(value, key) in rules" :key="key"
          class="py-1 px-2 rounded-md transition-all duration-300"
          :class="activeKey === key ? 'bg-green-500/15 border-l-[3px] border-green-400 translate-x-1' : 'border-l-[3px] border-transparent'"
        >
          <span class="text-blue-400">  "{{ key }}"</span>
          <span class="text-white">: </span>
          <span class="text-amber-200">"{{ value }}"</span>
          <span class="text-white">,</span>
          <span v-if="activeKey === key" class="ml-2 inline-block w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
        </div>
        <code class="text-white/40">}</code>
      </div>
    </div>

    <!-- Right: Interpretation panel -->
    <div class="flex-1 space-y-3">
      <div
        v-for="item in interpretations" :key="item.key"
        @mouseenter="activeKey = item.key"
        @mouseleave="activeKey = null"
        class="cursor-pointer transition-all duration-300 p-4 rounded-xl border-2"
        :class="activeKey === item.key
          ? `border-green-500 ${item.bg} shadow-md scale-[1.02]`
          : 'border-white bg-white hover:border-slate-200 shadow-sm'"
      >
        <div class="flex items-center gap-3 mb-1">
          <component :is="item.icon" class="w-4 h-4" :class="activeKey === item.key ? item.color : 'text-slate-400'" />
          <h4 class="text-sm font-bold" :class="activeKey === item.key ? 'text-slate-900' : 'text-slate-600'">
            {{ item.title }}
          </h4>
        </div>
        <p class="text-xs ml-7 leading-relaxed" :class="activeKey === item.key ? 'text-slate-700' : 'text-slate-500'">
          {{ item.desc }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { BulbOutlined, CodeOutlined, ArrowRightOutlined } from '@ant-design/icons-vue'
import type { DecisionRules } from '@/api/expert'

const props = withDefaults(defineProps<{ decisionRules?: DecisionRules }>(), {
  decisionRules: () => ({
    trigger: 'CGM_HIGH_VOLATILITY',
    logic: "IF val > 10.0 AND trend == 'UP' THEN SET RISK = R3",
    octopus_clamp: 'LIMIT_TASKS = 1',
    narrative_override: 'CONVERT_TO_EMPATHY',
  }),
})

const activeKey = ref<string | null>(null)
const rules = computed(() => props.decisionRules)

const interpretations = [
  { key: 'trigger', icon: BulbOutlined, title: '感知层：识别异常', desc: '系统通过传感器发现用户的血糖正在剧烈波动。', color: 'text-blue-500', bg: 'bg-blue-50' },
  { key: 'logic', icon: CodeOutlined, title: '判定层：风险分级', desc: '基于临床规则，判定当前处于中高风险(R3)状态。', color: 'text-amber-500', bg: 'bg-amber-50' },
  { key: 'octopus_clamp', icon: ArrowRightOutlined, title: '保护层：效能钳制', desc: 'Octopus 引擎介入，自动隐藏复杂任务，为用户减负。', color: 'text-purple-500', bg: 'bg-purple-50' },
  { key: 'narrative_override', icon: ArrowRightOutlined, title: '叙事层：语境转换', desc: '强制切换为"陪伴式"话术，用关怀替代医疗指令。', color: 'text-green-500', bg: 'bg-green-50' },
]
</script>
