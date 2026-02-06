<template>
  <div class="dynamic-tool-wrapper habit-card">
    <div class="tool-header">
      <span class="tool-icon">🎯</span>
      <span class="tool-title">习惯处方卡</span>
      <span v-if="type" class="tool-type">{{ type }}</span>
    </div>

    <div class="tool-body">
      <!-- 行为选择 -->
      <div class="section">
        <p class="section-label">选择行为领域：</p>
        <div class="domain-chips">
          <button
            v-for="d in domains"
            :key="d.key"
            class="domain-chip"
            :class="{ active: selectedDomain === d.key }"
            @click="selectedDomain = d.key"
          >{{ d.icon }} {{ d.label }}</button>
        </div>
      </div>

      <!-- 模板选择 -->
      <div v-if="selectedDomain" class="section">
        <p class="section-label">选择习惯模板或自定义：</p>
        <div class="template-list">
          <div
            v-for="t in currentTemplates"
            :key="t.id"
            class="template-card"
            :class="{ selected: selectedTemplate === t.id }"
            @click="selectTemplate(t)"
          >
            <span class="template-name">{{ t.name }}</span>
            <span class="template-time">{{ t.duration }}</span>
          </div>
          <div class="template-card custom" :class="{ selected: isCustom }" @click="enableCustom">
            <span class="template-name">+ 自定义习惯</span>
          </div>
        </div>
      </div>

      <!-- 习惯步骤编辑 -->
      <div class="section">
        <p class="section-label">微习惯步骤（{{ steps.length }}/{{ maxSteps }}步）：</p>
        <div class="steps-editor">
          <div v-for="(step, i) in steps" :key="i" class="step-item">
            <span class="step-num">Step {{ i + 1 }}</span>
            <input
              v-model="steps[i]"
              class="step-input"
              :placeholder="'描述第' + (i + 1) + '步...'"
            />
            <button v-if="steps.length > 1" class="step-remove" @click="removeStep(i)">×</button>
          </div>
          <button v-if="steps.length < maxSteps" class="add-step-btn" @click="addStep">+ 添加步骤</button>
        </div>
        <p class="habit-tip">原则: 小到不可能失败，2分钟内可完成</p>
      </div>

      <!-- 频次设定 -->
      <div class="section">
        <p class="section-label">执行频次：</p>
        <div class="freq-row">
          <select v-model="frequency.type" class="freq-select">
            <option value="daily">每天</option>
            <option value="weekly">每周</option>
            <option value="custom">自定义</option>
          </select>
          <template v-if="frequency.type === 'weekly'">
            <div class="weekday-chips">
              <button
                v-for="d in weekdays"
                :key="d.key"
                class="weekday-chip"
                :class="{ active: frequency.days.includes(d.key) }"
                @click="toggleWeekday(d.key)"
              >{{ d.label }}</button>
            </div>
          </template>
          <template v-if="frequency.type === 'custom'">
            <input v-model="frequency.customText" class="freq-input" placeholder="如：每3天1次" />
          </template>
        </div>
      </div>

      <!-- 提醒配置 -->
      <div class="section">
        <p class="section-label">提醒设置：</p>
        <div class="reminder-row">
          <label class="reminder-toggle">
            <input type="checkbox" v-model="reminder.enabled" />
            <span>开启提醒</span>
          </label>
          <input v-if="reminder.enabled" type="time" v-model="reminder.time" class="reminder-time" />
        </div>
        <div v-if="reminder.enabled" class="reminder-row">
          <input v-model="reminder.message" class="reminder-msg" placeholder="提醒语，如：该做拉伸啦！" />
        </div>
      </div>

      <!-- SMART 目标 -->
      <div class="section">
        <p class="section-label">SMART 目标：</p>
        <div class="smart-grid">
          <div v-for="s in smartFields" :key="s.key" class="smart-item">
            <span class="smart-letter" :style="{ background: s.color }">{{ s.letter }}</span>
            <input v-model="smartGoal[s.key]" class="smart-input" :placeholder="s.placeholder" />
          </div>
        </div>
      </div>

      <!-- 处方卡预览 -->
      <div v-if="showPreview" class="preview-card">
        <div class="preview-header">处方卡预览</div>
        <div class="preview-body">
          <p><strong>行为领域：</strong>{{ domainLabel }}</p>
          <p><strong>习惯名称：</strong>{{ habitName }}</p>
          <p v-for="(step, i) in steps.filter(s => s)" :key="i">
            <strong>Step {{ i + 1 }}：</strong>{{ step }}
          </p>
          <p><strong>频次：</strong>{{ frequencyText }}</p>
          <p v-if="reminder.enabled"><strong>提醒：</strong>{{ reminder.time }} - {{ reminder.message || '默认提醒' }}</p>
          <p v-if="smartGoal.specific"><strong>目标：</strong>{{ smartGoal.specific }}</p>
        </div>
      </div>
    </div>

    <div class="tool-actions">
      <button class="tool-btn" @click="showPreview = !showPreview">
        {{ showPreview ? '收起预览' : '预览处方卡' }}
      </button>
      <button class="tool-btn primary" @click="generateCard">生成处方卡</button>
      <button class="tool-btn" @click="$emit('action', { tool: 'habit', action: 'template' })">选模板</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'micro_habit' },
  maxSteps: { type: Number, default: 5 },
})
const emit = defineEmits(['action'])

const domains = [
  { key: 'exercise', label: '运动', icon: '🏃' },
  { key: 'diet', label: '饮食', icon: '🥗' },
  { key: 'sleep', label: '睡眠', icon: '😴' },
  { key: 'stress', label: '减压', icon: '🧘' },
  { key: 'medication', label: '用药', icon: '💊' },
  { key: 'social', label: '社交', icon: '👥' },
]

const templateMap = {
  exercise: [
    { id: 'e1', name: '饭后散步5分钟', duration: '2分钟', steps: ['穿好鞋子走到门口', '沿小区步道走一圈', '回来做3次深呼吸'] },
    { id: 'e2', name: '起床拉伸', duration: '2分钟', steps: ['站立伸展双臂', '左右转体各5次', '踮脚站立10秒'] },
  ],
  diet: [
    { id: 'd1', name: '多喝一杯水', duration: '1分钟', steps: ['准备水杯放在桌上', '每次坐下时喝一口', '记录饮水次数'] },
    { id: 'd2', name: '增加一份蔬菜', duration: '2分钟', steps: ['准备一种绿叶蔬菜', '午餐时先吃蔬菜', '拍照记录'] },
  ],
  sleep: [
    { id: 's1', name: '睡前放手机', duration: '1分钟', steps: ['设定手机关机时间', '将手机放在卧室外', '阅读纸质书5分钟'] },
  ],
  stress: [
    { id: 'st1', name: '一分钟呼吸', duration: '1分钟', steps: ['闭眼坐好', '深吸4秒-屏息4秒-呼出6秒', '重复3次'] },
  ],
  medication: [
    { id: 'm1', name: '按时服药打卡', duration: '1分钟', steps: ['将药盒放在固定位置', '设定闹钟提醒', '服药后打卡记录'] },
  ],
  social: [
    { id: 'so1', name: '每天问候一个人', duration: '2分钟', steps: ['打开通讯录', '发一条问候消息', '记录对方回复'] },
  ],
}

const weekdays = [
  { key: 'mon', label: '一' }, { key: 'tue', label: '二' }, { key: 'wed', label: '三' },
  { key: 'thu', label: '四' }, { key: 'fri', label: '五' }, { key: 'sat', label: '六' }, { key: 'sun', label: '日' },
]

const smartFields = [
  { key: 'specific', letter: 'S', placeholder: '具体做什么？', color: '#3b82f6' },
  { key: 'measurable', letter: 'M', placeholder: '如何衡量？', color: '#10b981' },
  { key: 'achievable', letter: 'A', placeholder: '是否可实现？', color: '#f59e0b' },
  { key: 'relevant', letter: 'R', placeholder: '与目标相关？', color: '#ef4444' },
  { key: 'timeBound', letter: 'T', placeholder: '截止时间？', color: '#8b5cf6' },
]

const selectedDomain = ref(null)
const selectedTemplate = ref(null)
const isCustom = ref(false)
const steps = ref(['', '', ''])
const habitName = ref('')
const showPreview = ref(false)

const frequency = reactive({ type: 'daily', days: [], customText: '' })
const reminder = reactive({ enabled: true, time: '08:00', message: '' })
const smartGoal = reactive({ specific: '', measurable: '', achievable: '', relevant: '', timeBound: '' })

const currentTemplates = computed(() => templateMap[selectedDomain.value] || [])
const domainLabel = computed(() => domains.find(d => d.key === selectedDomain.value)?.label || '')
const frequencyText = computed(() => {
  if (frequency.type === 'daily') return '每天'
  if (frequency.type === 'weekly') return `每周 ${frequency.days.join('/')}`
  return frequency.customText || '自定义'
})

const selectTemplate = (t) => {
  selectedTemplate.value = t.id
  isCustom.value = false
  habitName.value = t.name
  steps.value = [...t.steps]
  while (steps.value.length < 3) steps.value.push('')
}

const enableCustom = () => {
  selectedTemplate.value = null
  isCustom.value = true
  habitName.value = ''
  steps.value = ['', '', '']
}

const addStep = () => { if (steps.value.length < props.maxSteps) steps.value.push('') }
const removeStep = (i) => { steps.value.splice(i, 1) }

const toggleWeekday = (key) => {
  const idx = frequency.days.indexOf(key)
  if (idx > -1) frequency.days.splice(idx, 1)
  else frequency.days.push(key)
}

const generateCard = () => {
  emit('action', {
    tool: 'habit',
    action: 'create',
    data: {
      domain: selectedDomain.value,
      name: habitName.value,
      steps: steps.value.filter(s => s),
      frequency: { ...frequency },
      reminder: { ...reminder },
      smartGoal: { ...smartGoal },
      timestamp: new Date().toISOString(),
    }
  })
}
</script>

<style scoped>
.habit-card { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; }
.tool-header { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.tool-icon { font-size: 16px; }
.tool-title { font-weight: 600; font-size: 13px; color: #16a34a; }
.tool-type { font-size: 11px; background: #dcfce7; color: #15803d; padding: 1px 6px; border-radius: 4px; }
.tool-body { font-size: 12px; color: #666; }
.section { margin-bottom: 10px; }
.section-label { font-size: 12px; font-weight: 600; color: #333; margin-bottom: 4px; }

.domain-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.domain-chip { font-size: 11px; padding: 3px 8px; border: 1px solid #bbf7d0; border-radius: 12px; background: #fff; cursor: pointer; color: #16a34a; }
.domain-chip.active { background: #16a34a; color: #fff; border-color: #16a34a; }

.template-list { display: flex; flex-wrap: wrap; gap: 6px; }
.template-card { padding: 6px 10px; border: 1px solid #bbf7d0; border-radius: 6px; background: #fff; cursor: pointer; }
.template-card.selected { border-color: #16a34a; background: #dcfce7; }
.template-card.custom { border-style: dashed; }
.template-name { font-size: 11px; color: #333; }
.template-time { font-size: 10px; color: #999; margin-left: 4px; }

.steps-editor { margin-top: 4px; }
.step-item { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.step-num { font-weight: 600; color: #16a34a; min-width: 44px; font-size: 11px; }
.step-input { flex: 1; padding: 4px 8px; border: 1px solid #bbf7d0; border-radius: 4px; font-size: 12px; background: #fff; }
.step-remove { width: 20px; height: 20px; border: none; background: #fecaca; color: #dc2626; border-radius: 50%; cursor: pointer; font-size: 12px; line-height: 1; }
.add-step-btn { font-size: 11px; color: #16a34a; border: 1px dashed #bbf7d0; background: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; width: 100%; margin-top: 4px; }
.habit-tip { font-size: 11px; color: #16a34a; font-style: italic; margin-top: 4px; }

.freq-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.freq-select { padding: 4px 8px; border: 1px solid #bbf7d0; border-radius: 4px; font-size: 12px; background: #fff; }
.freq-input { padding: 4px 8px; border: 1px solid #bbf7d0; border-radius: 4px; font-size: 12px; flex: 1; }
.weekday-chips { display: flex; gap: 4px; }
.weekday-chip { width: 24px; height: 24px; border: 1px solid #bbf7d0; border-radius: 50%; font-size: 10px; background: #fff; cursor: pointer; color: #16a34a; display: flex; align-items: center; justify-content: center; }
.weekday-chip.active { background: #16a34a; color: #fff; border-color: #16a34a; }

.reminder-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.reminder-toggle { display: flex; align-items: center; gap: 4px; font-size: 12px; cursor: pointer; }
.reminder-time { padding: 3px 6px; border: 1px solid #bbf7d0; border-radius: 4px; font-size: 12px; }
.reminder-msg { flex: 1; padding: 4px 8px; border: 1px solid #bbf7d0; border-radius: 4px; font-size: 12px; width: 100%; }

.smart-grid { display: flex; flex-direction: column; gap: 4px; }
.smart-item { display: flex; align-items: center; gap: 6px; }
.smart-letter { width: 20px; height: 20px; border-radius: 50%; color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.smart-input { flex: 1; padding: 3px 8px; border: 1px solid #e5e7eb; border-radius: 4px; font-size: 11px; }

.preview-card { background: #fff; border: 2px solid #16a34a; border-radius: 8px; overflow: hidden; margin-top: 8px; }
.preview-header { background: #16a34a; color: #fff; padding: 6px 10px; font-size: 12px; font-weight: 600; }
.preview-body { padding: 10px; font-size: 12px; }
.preview-body p { margin: 3px 0; color: #333; }

.tool-actions { display: flex; gap: 8px; margin-top: 10px; }
.tool-btn { font-size: 12px; padding: 4px 12px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; background: #fff; }
.tool-btn.primary { background: #16a34a; color: #fff; border-color: #16a34a; }
</style>
