<script setup lang="ts">
/**
 * 数据输入表单组件（备用）
 * 当前版本的功能已在 DataInputPage 中实现
 * 此组件保留用于未来的模块化重构
 */
import { ref } from 'vue'

interface Props {
  modelValue: {
    text_content?: string
    glucose_values?: number[]
    hrv_values?: number[]
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'submit'])

const formData = ref(props.modelValue)

const onSubmit = () => {
  emit('update:modelValue', formData.value)
  emit('submit', formData.value)
}
</script>

<template>
  <div class="data-input-form">
    <van-form @submit="onSubmit">
      <slot :formData="formData" />

      <div class="button-group">
        <van-button round block type="primary" native-type="submit">
          提交
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.data-input-form {
  width: 100%;
}
</style>
