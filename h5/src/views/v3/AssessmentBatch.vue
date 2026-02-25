<template>
  <div>
    <van-nav-bar :title="batchName" left-arrow @click-left="$router.back()" />

    <div v-if="!submitted" class="batch-content">
      <!-- 进度 -->
      <van-progress :percentage="questions.length ? Math.round((currentIdx + 1) / questions.length * 100) : 0" stroke-width="6" style="margin: 12px 16px;" />
      <div class="q-counter">第 {{ currentIdx + 1 }} / {{ questions.length }} 题</div>

      <!-- 当前题目 -->
      <div class="question-card" v-if="questions.length">
        <div class="q-text">{{ questions[currentIdx].text }}</div>
        <van-radio-group v-model="answers[currentIdx]" class="options">
          <van-cell-group inset>
            <van-cell v-for="(opt, oi) in questions[currentIdx].options" :key="oi"
              :title="opt.label" clickable @click="answers[currentIdx] = opt.value">
              <template #right-icon>
                <van-radio :name="opt.value" />
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>
      </div>

      <!-- 导航 -->
      <div class="nav-btns">
        <van-button plain @click="prev" :disabled="currentIdx === 0">上一题</van-button>
        <van-button type="primary" @click="next" v-if="currentIdx < questions.length - 1">下一题</van-button>
        <van-button type="primary" @click="submit" v-else :loading="submitting">提交</van-button>
      </div>
    </div>

    <!-- 提交成功 -->
    <div v-else style="text-align:center; padding:60px 20px;">
      <van-icon name="checked" size="64" color="#07c160" />
      <h3 style="margin:16px 0 8px">提交成功</h3>
      <p style="color:#999">用时 {{ Math.round(elapsed / 1000) }} 秒</p>
      <van-button type="primary" round style="margin-top:24px" @click="$router.push('/v3/assessment')">返回评估中心</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { assessmentApi } from '../../api/v3/index.js'

const props = defineProps({ batchId: String })

const batchName = ref('')
const questions = ref([])
const answers = ref([])
const currentIdx = ref(0)
const submitted = ref(false)
const submitting = ref(false)
const startTime = ref(Date.now())
const elapsed = ref(0)

onMounted(async () => {
  try {
    const res = await assessmentApi.batches()
    if (res?.data) {
      const batch = res.data.find(b => b.batch_id === props.batchId)
      if (batch) {
        batchName.value = batch.name
        questions.value = batch.questions || []
        answers.value = new Array(questions.value.length).fill(null)
      }
    }
  } catch (e) {
    console.error('[AssessmentBatch] load failed:', e)
  }
  startTime.value = Date.now()
})

function prev() { if (currentIdx.value > 0) currentIdx.value-- }
function next() {
  if (answers.value[currentIdx.value] == null) { showToast('请选择一个选项'); return }
  currentIdx.value++
}

async function submit() {
  if (answers.value.some(a => a == null)) { showToast('还有未完成的题目'); return }
  submitting.value = true
  elapsed.value = Date.now() - startTime.value
  try {
    await assessmentApi.submit(null, props.batchId, answers.value, Math.round(elapsed.value / 1000))
    submitted.value = true
  } catch { showToast('提交失败') }
  finally { submitting.value = false }
}
</script>

<style scoped>
.batch-content { padding-bottom: 100px; }
.q-counter { text-align: center; font-size: 13px; color: #999; }
.question-card { margin: 16px 12px; }
.q-text { font-size: 17px; font-weight: 500; line-height: 1.6; padding: 16px; background: #fff; border-radius: 8px; margin-bottom: 12px; }
.nav-btns { display: flex; justify-content: center; gap: 16px; padding: 20px; }
</style>
