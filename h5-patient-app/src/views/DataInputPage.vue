<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useAssessmentStore } from '@/stores/assessment'
import type { AssessmentInput } from '@/types'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()
const userStore = useUserStore()
const assessmentStore = useAssessmentStore()

// 表单数据
const formData = ref<AssessmentInput>({
  user_id: userStore.user?.id || 0,
  text_content: '',
  glucose_values: [],
  hrv_values: []
})

// 血糖值输入
const glucoseInput = ref('')
// HRV值输入
const hrvInput = ref('')

/**
 * 添加血糖值
 */
const addGlucose = () => {
  const value = parseFloat(glucoseInput.value)
  if (isNaN(value) || value <= 0) {
    showToast('请输入有效的血糖值')
    return
  }

  if (!formData.value.glucose_values) {
    formData.value.glucose_values = []
  }

  formData.value.glucose_values.push(value)
  glucoseInput.value = ''
  showToast('已添加')
}

/**
 * 删除血糖值
 */
const removeGlucose = (index: number) => {
  formData.value.glucose_values?.splice(index, 1)
}

/**
 * 添加HRV值
 */
const addHrv = () => {
  const value = parseFloat(hrvInput.value)
  if (isNaN(value) || value <= 0) {
    showToast('请输入有效的HRV值')
    return
  }

  if (!formData.value.hrv_values) {
    formData.value.hrv_values = []
  }

  formData.value.hrv_values.push(value)
  hrvInput.value = ''
  showToast('已添加')
}

/**
 * 删除HRV值
 */
const removeHrv = (index: number) => {
  formData.value.hrv_values?.splice(index, 1)
}

/**
 * 提交评估
 */
const onSubmit = async () => {
  // 验证至少有一项数据
  if (
    !formData.value.text_content &&
    (!formData.value.glucose_values || formData.value.glucose_values.length === 0) &&
    (!formData.value.hrv_values || formData.value.hrv_values.length === 0)
  ) {
    showToast('请至少填写一项数据')
    return
  }

  showConfirmDialog({
    title: '确认提交',
    message: '确定要提交评估数据吗？'
  })
    .then(async () => {
      try {
        const result = await assessmentStore.submitAssessment(formData.value)

        // 提交成功，跳转到结果页
        router.push(`/result/${result.assessment_id}`)
      } catch (error) {
        console.error('Submit error:', error)
      }
    })
    .catch(() => {
      // 取消
    })
}

/**
 * 返回首页
 */
const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="data-input-page page-container">
    <van-nav-bar title="数据录入" left-arrow @click-left="goBack" />

    <div class="content-wrapper">
      <van-form @submit="onSubmit">
        <!-- 心情日记 -->
        <van-cell-group title="心情日记" inset>
          <van-field
            v-model="formData.text_content"
            rows="4"
            autosize
            type="textarea"
            maxlength="500"
            placeholder="记录今天的心情、感受、遇到的事情...&#10;例如：今天工作压力很大，感觉很疲惫..."
            show-word-limit
          />
        </van-cell-group>

        <!-- 血糖值 -->
        <van-cell-group title="血糖值 (mmol/L)" inset>
          <van-field
            v-model="glucoseInput"
            type="number"
            placeholder="输入血糖测量值，如：6.5"
            clearable
          >
            <template #button>
              <van-button size="small" type="primary" @click="addGlucose">添加</van-button>
            </template>
          </van-field>

          <van-cell v-if="formData.glucose_values && formData.glucose_values.length > 0">
            <div class="value-list">
              <van-tag
                v-for="(value, index) in formData.glucose_values"
                :key="index"
                closeable
                type="primary"
                size="large"
                @close="removeGlucose(index)"
              >
                {{ value }} mmol/L
              </van-tag>
            </div>
          </van-cell>

          <van-cell v-else>
            <div class="empty-hint">暂无血糖数据</div>
          </van-cell>
        </van-cell-group>

        <!-- HRV值 -->
        <van-cell-group title="心率变异性 (HRV)" inset>
          <van-field
            v-model="hrvInput"
            type="number"
            placeholder="输入HRV测量值，如：65"
            clearable
          >
            <template #button>
              <van-button size="small" type="primary" @click="addHrv">添加</van-button>
            </template>
          </van-field>

          <van-cell v-if="formData.hrv_values && formData.hrv_values.length > 0">
            <div class="value-list">
              <van-tag
                v-for="(value, index) in formData.hrv_values"
                :key="index"
                closeable
                type="success"
                size="large"
                @close="removeHrv(index)"
              >
                {{ value }} ms
              </van-tag>
            </div>
          </van-cell>

          <van-cell v-else>
            <div class="empty-hint">暂无HRV数据</div>
          </van-cell>
        </van-cell-group>

        <!-- 数据说明 -->
        <van-notice-bar
          left-icon="info-o"
          color="#1989fa"
          background="#ecf9ff"
          style="margin: 16px"
        >
          提示：请至少填写一项数据（心情日记、血糖值或HRV值）
        </van-notice-bar>

        <!-- 提交按钮 -->
        <div class="button-group">
          <van-button
            round
            block
            type="primary"
            native-type="submit"
            :loading="assessmentStore.submitting"
            loading-text="提交中..."
          >
            提交评估
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<style scoped>
.data-input-page {
  min-height: 100vh;
}

.value-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}

.empty-hint {
  color: #969799;
  font-size: 14px;
  padding: 8px 0;
}
</style>
