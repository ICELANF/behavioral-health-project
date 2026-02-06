<template>
  <div class="dynamic-tool-wrapper empathy-guide">
    <div class="tool-header">
      <span class="tool-icon">💜</span>
      <span class="tool-title">同理心倾听指南 · OARS</span>
      <span v-if="type" class="tool-type">{{ type }}</span>
    </div>

    <!-- 场景选择 -->
    <div class="tool-body">
      <div class="scene-selector">
        <p class="section-label">选择对话场景：</p>
        <div class="scene-chips">
          <button
            v-for="s in scenes"
            :key="s.key"
            class="scene-chip"
            :class="{ active: activeScene === s.key }"
            @click="activeScene = s.key"
          >{{ s.label }}</button>
        </div>
      </div>

      <!-- OARS 步骤卡片 -->
      <div class="oars-steps">
        <div
          v-for="(step, i) in oarsSteps"
          :key="step.key"
          class="oars-card"
          :class="{ expanded: expandedStep === step.key }"
          @click="expandedStep = expandedStep === step.key ? null : step.key"
        >
          <div class="oars-header">
            <span class="oars-badge">{{ step.letter }}</span>
            <span class="oars-name">{{ step.name }}</span>
            <span class="oars-toggle">{{ expandedStep === step.key ? '−' : '+' }}</span>
          </div>
          <div v-if="expandedStep === step.key" class="oars-body">
            <p class="oars-desc">{{ step.description }}</p>
            <div class="template-section">
              <p class="template-label">话术模板：</p>
              <div v-for="(t, j) in getTemplates(step.key)" :key="j" class="template-item">
                <span class="template-bullet">•</span>
                <span class="template-text">"{{ t }}"</span>
                <button class="copy-btn" @click.stop="copyTemplate(t)">复制</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 注意事项 -->
      <div class="guidelines">
        <p class="section-label">对话原则：</p>
        <ul class="guide-list">
          <li><strong class="dont">不</strong>主动推送任何健康任务</li>
          <li><strong class="dont">不</strong>使用说教或纠正性语言</li>
          <li><strong class="do">要</strong>使用开放式提问</li>
          <li><strong class="do">要</strong>认可和反映情绪</li>
        </ul>
      </div>

      <div v-if="timeout" class="timeout-hint">
        建议倾听时长: ≥ {{ Math.floor(timeout / 60) }} 分钟
      </div>

      <!-- 使用记录 -->
      <div v-if="usageLog.length > 0" class="usage-section">
        <p class="section-label">最近使用记录：</p>
        <div v-for="(log, i) in usageLog" :key="i" class="usage-item">
          <span class="usage-time">{{ log.time }}</span>
          <span class="usage-scene">{{ log.scene }}</span>
          <span class="usage-duration">{{ log.duration }}分钟</span>
        </div>
      </div>
    </div>

    <div class="tool-actions">
      <button class="tool-btn primary" @click="startListening">进入倾听模式</button>
      <button v-if="isListening" class="tool-btn warn" @click="stopListening">结束倾听</button>
    </div>

    <!-- 倾听计时器 -->
    <div v-if="isListening" class="listening-overlay">
      <div class="pulse-circle"></div>
      <p class="listening-text">倾听中... {{ formatTime(listenElapsed) }}</p>
      <p class="listening-hint">{{ currentHint }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'

const props = defineProps({
  type: { type: String, default: 'passive_listen' },
  timeout: { type: Number, default: 600 },
})
const emit = defineEmits(['action'])

const scenes = [
  { key: 'resistance', label: '阻抗/回避期' },
  { key: 'ambivalence', label: '矛盾犹豫期' },
  { key: 'crisis', label: '情绪危机' },
  { key: 'relapse', label: '复发回退' },
]

const oarsSteps = [
  { key: 'O', letter: 'O', name: '开放式提问 (Open Questions)', description: '使用不能只用"是/否"回答的问题，鼓励对方分享更多想法和感受。' },
  { key: 'A', letter: 'A', name: '肯定 (Affirmations)', description: '发现并肯定对方的优点、努力和积极变化，增强其自我效能感。' },
  { key: 'R', letter: 'R', name: '反映式倾听 (Reflections)', description: '用自己的话复述对方的意思和情感，让对方感受到被理解。' },
  { key: 'S', letter: 'S', name: '总结 (Summaries)', description: '将对话中的关键内容整合起来回馈给对方，确认理解是否正确。' },
]

const templateMap = {
  resistance: {
    O: ['你现在感觉怎么样？', '是什么让你今天来到这里？', '你心目中理想的生活是什么样的？'],
    A: ['你能来这里本身就很不容易', '我看到你一直在努力应对', '你对自己的健康有很好的觉察'],
    R: ['听起来你感到很疲惫', '你似乎对改变有些犹豫', '我能感受到这对你来说很困难'],
    S: ['让我总结一下你说的...', '所以目前的情况是...你觉得是这样吗？'],
  },
  ambivalence: {
    O: ['关于改变，你最担心的是什么？', '如果情况没有变化，你觉得会怎样？', '你曾经成功改变过什么习惯？'],
    A: ['你能思考这个问题说明你很有上进心', '你之前的经历说明你有能力改变'],
    R: ['一方面你想改变，另一方面又担心...', '你内心有两种声音在拉扯'],
    S: ['你提到了想改变的原因，也说了担忧...'],
  },
  crisis: {
    O: ['你现在安全吗？', '是什么让你感到特别痛苦？', '你身边有可以支持你的人吗？'],
    A: ['你愿意说出来非常勇敢', '你在这么困难的时候还在寻求帮助'],
    R: ['你现在感到非常痛苦和无助', '这件事对你的打击很大'],
    S: ['我听到了你说的这些，你现在最需要的是...'],
  },
  relapse: {
    O: ['这次的情况和上次有什么不同？', '在复发之前发生了什么？', '你从这次经历中学到了什么？'],
    A: ['复发是改变过程中正常的一部分', '你能意识到并来寻求帮助就很了不起'],
    R: ['你对自己感到失望，但又不想放弃', '这次的经历让你对触发因素有了新认识'],
    S: ['从你说的来看，触发因素是...你的应对计划可以调整为...'],
  },
}

const activeScene = ref('resistance')
const expandedStep = ref(null)
const isListening = ref(false)
const listenElapsed = ref(0)
const usageLog = ref([])
let listenTimer = null

const hints = [
  '保持沉默也是一种倾听...',
  '注意对方的语气和表情...',
  '不要急于给建议...',
  '试着反映你听到的情感...',
  '用"嗯"、"我理解"等给予回应...',
]
const currentHint = computed(() => hints[Math.floor(listenElapsed.value / 15) % hints.length])

const getTemplates = (stepKey) => {
  return templateMap[activeScene.value]?.[stepKey] || []
}

const copyTemplate = (text) => {
  navigator.clipboard?.writeText(text)
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const startListening = () => {
  isListening.value = true
  listenElapsed.value = 0
  emit('action', { tool: 'empathy', action: 'start_listen', scene: activeScene.value })
  listenTimer = setInterval(() => { listenElapsed.value++ }, 1000)
}

const stopListening = () => {
  if (listenTimer) clearInterval(listenTimer)
  isListening.value = false
  const scene = scenes.find(s => s.key === activeScene.value)
  usageLog.value.unshift({
    time: new Date().toLocaleTimeString(),
    scene: scene?.label || activeScene.value,
    duration: Math.floor(listenElapsed.value / 60),
  })
  if (usageLog.value.length > 5) usageLog.value.pop()
  emit('action', {
    tool: 'empathy',
    action: 'end_listen',
    data: { scene: activeScene.value, duration: listenElapsed.value },
  })
}

onBeforeUnmount(() => { if (listenTimer) clearInterval(listenTimer) })
</script>

<style scoped>
.empathy-guide { background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 12px; position: relative; }
.tool-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.tool-icon { font-size: 16px; }
.tool-title { font-weight: 600; font-size: 13px; color: #7c3aed; }
.tool-type { font-size: 11px; background: #ede9fe; color: #6d28d9; padding: 1px 6px; border-radius: 4px; }
.tool-body { font-size: 12px; color: #666; }
.section-label { font-size: 12px; font-weight: 600; color: #333; margin-bottom: 6px; }

.scene-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.scene-chip { font-size: 11px; padding: 3px 10px; border: 1px solid #e9d5ff; border-radius: 12px; background: #fff; cursor: pointer; color: #7c3aed; }
.scene-chip.active { background: #7c3aed; color: #fff; border-color: #7c3aed; }

.oars-steps { margin-bottom: 10px; }
.oars-card { background: #fff; border: 1px solid #e9d5ff; border-radius: 6px; margin-bottom: 4px; cursor: pointer; overflow: hidden; }
.oars-header { display: flex; align-items: center; gap: 6px; padding: 8px; }
.oars-badge { width: 22px; height: 22px; border-radius: 50%; background: #7c3aed; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.oars-name { flex: 1; font-size: 12px; font-weight: 500; color: #333; }
.oars-toggle { font-size: 14px; color: #7c3aed; font-weight: 600; }
.oars-body { padding: 0 8px 8px; }
.oars-desc { font-size: 11px; color: #666; margin-bottom: 6px; }
.template-label { font-size: 11px; font-weight: 600; color: #7c3aed; margin-bottom: 4px; }
.template-item { display: flex; align-items: center; gap: 4px; padding: 2px 0; }
.template-bullet { color: #7c3aed; }
.template-text { flex: 1; font-size: 11px; color: #444; font-style: italic; }
.copy-btn { font-size: 10px; padding: 1px 6px; border: 1px solid #e9d5ff; border-radius: 3px; background: #faf5ff; color: #7c3aed; cursor: pointer; }

.guide-list { padding-left: 16px; margin: 0 0 8px; }
.guide-list li { padding: 2px 0; color: #444; font-size: 12px; }
.dont { color: #dc2626; }
.do { color: #16a34a; }
.timeout-hint { font-size: 11px; color: #7c3aed; margin-bottom: 8px; }

.usage-section { margin-top: 8px; }
.usage-item { display: flex; gap: 8px; font-size: 11px; padding: 3px 0; border-bottom: 1px dashed #e9d5ff; }
.usage-time { color: #999; min-width: 60px; }
.usage-scene { flex: 1; color: #666; }
.usage-duration { color: #7c3aed; font-weight: 500; }

.tool-actions { display: flex; gap: 8px; margin-top: 10px; }
.tool-btn { font-size: 12px; padding: 4px 12px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; background: #fff; }
.tool-btn.primary { background: #7c3aed; color: #fff; border-color: #7c3aed; }
.tool-btn.warn { background: #f59e0b; color: #fff; border-color: #f59e0b; }

.listening-overlay { margin-top: 10px; text-align: center; padding: 16px; background: rgba(124, 58, 237, 0.05); border-radius: 8px; border: 1px solid #e9d5ff; }
.pulse-circle { width: 40px; height: 40px; border-radius: 50%; background: rgba(124, 58, 237, 0.2); margin: 0 auto 8px; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: 0.5; } }
.listening-text { font-size: 14px; font-weight: 600; color: #7c3aed; margin-bottom: 4px; }
.listening-hint { font-size: 11px; color: #999; font-style: italic; }
</style>
