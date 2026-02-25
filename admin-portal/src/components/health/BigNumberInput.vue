<template>
  <div class="big-number-input" :class="{ focused: isFocused, error: !!errorMessage }">
    <!-- 标签 -->
    <div class="input-header">
      <div class="input-icon" v-if="icon">{{ icon }}</div>
      <div class="input-label-group">
        <div class="input-label">{{ label }}</div>
        <div v-if="subtitle" class="input-subtitle">{{ subtitle }}</div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-wrapper">
      <input
        ref="inputRef"
        v-model="inputValue"
        :type="inputType"
        :placeholder="placeholder"
        :step="step"
        :min="min"
        :max="max"
        :disabled="disabled"
        class="big-input"
        @focus="handleFocus"
        @blur="handleBlur"
        @input="handleInput"
      />
      <div class="input-unit">{{ unit }}</div>
    </div>

    <!-- 智能提示 -->
    <div v-if="hint" class="smart-hint">
      <div class="hint-icon">💡</div>
      <div class="hint-text" v-html="sanitizeHtml(hint || '')"></div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-message">
      ⚠️ {{ errorMessage }}
    </div>

    <!-- 快速填充按钮（可选） -->
    <div v-if="quickValues && quickValues.length > 0" class="quick-values">
      <div class="quick-values-label">快速填充：</div>
      <div class="quick-values-buttons">
        <div
          v-for="value in quickValues"
          :key="value"
          class="quick-value-btn"
          @click="setQuickValue(value)"
        >
          {{ value }}
        </div>
      </div>
    </div>

    <!-- 历史对比（可选） -->
    <div v-if="historicalValue" class="historical-compare">
      <div class="compare-label">上次记录</div>
      <div class="compare-value">{{ historicalValue }} {{ unit }}</div>
      <div v-if="showDiff && diff !== null" class="compare-diff" :class="diffClass">
        {{ diffText }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { sanitizeHtml } from '@/utils/sanitize'

interface Props {
  modelValue: string | number
  label: string
  subtitle?: string
  icon?: string
  unit: string
  placeholder?: string
  hint?: string
  errorMessage?: string
  historicalValue?: string | number
  quickValues?: number[]
  inputType?: 'number' | 'text'
  step?: string | number
  min?: string | number
  max?: string | number
  disabled?: boolean
  showDiff?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string | number): void
  (e: 'focus'): void
  (e: 'blur'): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '0.0',
  inputType: 'number',
  step: '0.1',
  disabled: false,
  showDiff: true
})

const emit = defineEmits<Emits>()

const inputRef = ref<HTMLInputElement>()
const isFocused = ref(false)
const inputValue = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  inputValue.value = newVal
})

const handleFocus = () => {
  isFocused.value = true
  emit('focus')
}

const handleBlur = () => {
  isFocused.value = false
  emit('blur')
}

const handleInput = () => {
  emit('update:modelValue', inputValue.value)
}

const setQuickValue = (value: number) => {
  inputValue.value = value
  emit('update:modelValue', value)
  inputRef.value?.focus()
}

// 计算差值
const diff = computed(() => {
  if (!props.historicalValue || !inputValue.value) return null
  const current = parseFloat(String(inputValue.value))
  const historical = parseFloat(String(props.historicalValue))
  if (isNaN(current) || isNaN(historical)) return null
  return current - historical
})

const diffClass = computed(() => {
  if (diff.value === null) return ''
  if (diff.value > 0) return 'diff-up'
  if (diff.value < 0) return 'diff-down'
  return 'diff-same'
})

const diffText = computed(() => {
  if (diff.value === null) return ''
  if (diff.value > 0) return `↑ 增加 ${Math.abs(diff.value).toFixed(1)}`
  if (diff.value < 0) return `↓ 减少 ${Math.abs(diff.value).toFixed(1)}`
  return '→ 保持不变'
})
</script>

<style scoped>
.big-number-input {
  width: 100%;
  padding: 20px;
  background: #fff;
  border-radius: 20px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s;
}

.big-number-input.focused {
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.1);
}

.big-number-input.error {
  border-color: #ef4444;
}

/* 标签 */
.input-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.input-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.input-label-group {
  flex: 1;
}

.input-label {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.input-subtitle {
  font-size: 14px;
  color: #6b7280;
}

/* 输入框 */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.big-input {
  flex: 1;
  font-size: 48px;
  font-weight: 700;
  color: #1f2937;
  border: none;
  outline: none;
  background: transparent;
  padding: 0;
  text-align: center;
}

.big-input::placeholder {
  color: #d1d5db;
}

.big-input:disabled {
  color: #9ca3af;
  cursor: not-allowed;
}

/* Chrome, Safari, Edge, Opera - 隐藏数字输入的上下箭头 */
.big-input::-webkit-outer-spin-button,
.big-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox - 隐藏数字输入的上下箭头 */
.big-input[type=number] {
  -moz-appearance: textfield;
}

.input-unit {
  font-size: 24px;
  font-weight: 600;
  color: #6b7280;
  flex-shrink: 0;
}

/* 智能提示 */
.smart-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 12px;
  border: 1px solid #bfdbfe;
}

.hint-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.hint-text {
  font-size: 14px;
  color: #1e40af;
  line-height: 1.5;
}

.hint-text :deep(strong) {
  font-weight: 700;
  color: #1e3a8a;
}

/* 错误提示 */
.error-message {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 13px;
  color: #dc2626;
  font-weight: 500;
}

/* 快速填充 */
.quick-values {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.quick-values-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.quick-values-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-value-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-value-btn:hover {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
  transform: translateY(-2px);
}

/* 历史对比 */
.historical-compare {
  margin-top: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.compare-label {
  font-size: 12px;
  color: #9ca3af;
}

.compare-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.compare-diff {
  font-size: 13px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 8px;
  margin-left: auto;
}

.compare-diff.diff-up {
  background: #fee2e2;
  color: #dc2626;
}

.compare-diff.diff-down {
  background: #dcfce7;
  color: #16a34a;
}

.compare-diff.diff-same {
  background: #f3f4f6;
  color: #6b7280;
}
</style>
