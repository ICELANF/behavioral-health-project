<template>
  <div class="page-container">
    <van-nav-bar :title="title" left-arrow @click-left="$router.back()">
      <template #right>
        <van-icon name="bar-chart-o" size="20" @click="$router.push(`/program/${eid}/progress`)" />
        <van-icon name="clock-o" size="20" style="margin-left:12px" @click="$router.push(`/program/${eid}/timeline`)" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <van-loading v-if="loading" class="loading" />

      <template v-else-if="data">
        <!-- 进度条 -->
        <div class="progress-card">
          <div class="progress-header">
            <span class="day-label">Day {{ data.current_day }}</span>
            <span class="day-total">/ {{ data.total_days }} 天</span>
            <van-tag v-if="data.is_milestone" type="warning" size="small" round style="margin-left:8px">里程碑日</van-tag>
          </div>
          <van-progress
            :percentage="data.progress_pct"
            stroke-width="8"
            color="linear-gradient(to right, #1989fa, #07c160)"
            track-color="#ebedf0"
            pivot-text=""
            :show-pivot="false"
          />
          <div class="progress-pct">{{ data.progress_pct }}%</div>
        </div>

        <!-- 推送卡片列表 -->
        <div v-for="(push, idx) in data.pushes" :key="push.slot" class="push-card" :class="{ answered: push.answered }">
          <div class="push-header">
            <div class="push-slot">
              <span class="slot-icon">{{ slotIcon(push.slot) }}</span>
              <span class="slot-label">{{ slotLabel(push.slot) }}</span>
              <span v-if="push.time" class="slot-time">{{ push.time }}</span>
            </div>
            <van-tag v-if="push.answered" type="success" size="small" round>已完成</van-tag>
            <van-tag v-else-if="push.is_core" type="primary" size="small" round>核心</van-tag>
          </div>

          <!-- 知识内容 -->
          <div v-if="push.content?.knowledge" class="push-knowledge">
            {{ push.content.knowledge }}
          </div>
          <div v-if="push.content?.behavior_guide" class="push-guide">
            {{ push.content.behavior_guide }}
          </div>

          <!-- 微调查 -->
          <template v-if="push.survey && push.survey.questions && !push.answered">
            <div class="survey-section">
              <div class="survey-title">{{ push.survey.title || '请回答以下问题' }}</div>
              <div v-for="q in push.survey.questions" :key="q.id" class="survey-question">
                <div class="q-text">{{ q.text }}</div>
                <!-- scale -->
                <van-rate
                  v-if="q.type === 'scale'"
                  v-model="answers[push.slot][q.id]"
                  :count="q.max || 5"
                  allow-half
                  color="#ffd21e"
                  size="22"
                />
                <!-- choice -->
                <van-radio-group
                  v-else-if="q.type === 'choice'"
                  v-model="answers[push.slot][q.id]"
                  direction="horizontal"
                >
                  <van-radio
                    v-for="opt in q.options"
                    :key="opt.value || opt"
                    :name="opt.value || opt"
                    style="margin-bottom:6px"
                  >{{ opt.label || opt }}</van-radio>
                </van-radio-group>
                <!-- open_text -->
                <van-field
                  v-else-if="q.type === 'open_text'"
                  v-model="answers[push.slot][q.id]"
                  type="textarea"
                  rows="2"
                  :placeholder="q.placeholder || '请输入...'"
                  autosize
                />
                <!-- photo -->
                <van-uploader
                  v-else-if="q.type === 'photo'"
                  v-model="photoFiles[push.slot]"
                  :max-count="3"
                  :after-read="(f: any) => onPhotoRead(f, push.slot)"
                />
                <!-- fallback: text -->
                <van-field
                  v-else
                  v-model="answers[push.slot][q.id]"
                  :placeholder="q.placeholder || '请输入'"
                />
              </div>
              <van-button
                type="primary"
                round
                block
                size="small"
                :loading="submitting === push.slot"
                style="margin-top: 12px"
                @click="submitSurvey(push, idx)"
              >提交</van-button>
            </div>
          </template>

          <!-- 已回答 + 推荐 -->
          <template v-if="push.answered && push.recommended_content?.length">
            <div class="recs-section">
              <div class="recs-title">为你推荐</div>
              <div v-for="(rec, ri) in push.recommended_content" :key="ri" class="rec-item">
                <van-icon v-if="rec.type === 'positive_feedback'" name="like-o" color="#07c160" />
                <van-icon v-else-if="rec.type === 'coach_alert'" name="warning-o" color="#ee0a24" />
                <van-icon v-else name="bookmark-o" color="#1989fa" />
                <span>{{ rec.reason || rec.message || '推荐内容' }}</span>
              </div>
            </div>
          </template>
        </div>
      </template>

      <van-empty v-else description="暂无内容" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { programApi } from '@/api/program'
import api from '@/api/index'

const route = useRoute()
const eid = route.params.id as string

const loading = ref(true)
const data = ref<any>(null)
const title = ref('今日方案')
const submitting = ref('')
const answers = reactive<Record<string, Record<string, any>>>({})
const photoFiles = reactive<Record<string, any[]>>({})
const photoUrls = reactive<Record<string, string[]>>({})

const slotIcon = (s: string) => {
  const m: Record<string, string> = { morning: '\u{2600}', noon: '\u{1F324}', evening: '\u{1F319}', immediate: '\u{26A1}' }
  return m[s] || '\u{1F4E8}'
}
const slotLabel = (s: string) => {
  const m: Record<string, string> = { morning: '早间', noon: '午间', evening: '晚间', immediate: '即时' }
  return m[s] || s
}

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await programApi.getToday(eid)
    data.value = res
    title.value = res.template_title || '今日方案'
    // init answers
    for (const push of res.pushes || []) {
      if (!push.answered) {
        answers[push.slot] = {}
        photoFiles[push.slot] = []
        photoUrls[push.slot] = []
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const onPhotoRead = async (file: any, slot: string) => {
  if (!file.file) return
  const formData = new FormData()
  formData.append('file', file.file)
  try {
    const res: any = await api.post('/api/v1/upload/survey-image', formData)
    if (!photoUrls[slot]) photoUrls[slot] = []
    photoUrls[slot].push(res.url || res.image_url)
  } catch (e: any) {
    showFailToast('图片上传失败')
    const idx = photoFiles[slot]?.indexOf(file)
    if (idx >= 0) photoFiles[slot].splice(idx, 1)
  }
}

const submitSurvey = async (push: any, _idx: number) => {
  submitting.value = push.slot
  try {
    const res: any = await programApi.submitInteraction(eid, {
      day_number: data.value.current_day,
      slot: push.slot,
      survey_answers: answers[push.slot] || {},
      photo_urls: photoUrls[push.slot] || [],
    })
    if (res.success) {
      showSuccessToast('提交成功')
      await loadData()
    }
  } catch (e: any) {
    showFailToast(e?.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = ''
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { min-height: 100vh; background: #f5f5f5; }
.page-content { padding: 12px; }
.loading { text-align: center; padding: 60px 0; }

.progress-card {
  background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.progress-header { display: flex; align-items: baseline; margin-bottom: 10px; }
.day-label { font-size: 24px; font-weight: 700; color: #1989fa; }
.day-total { font-size: 14px; color: #999; margin-left: 4px; }
.progress-pct { text-align: right; font-size: 12px; color: #999; margin-top: 4px; }

.push-card {
  background: #fff; border-radius: 12px; padding: 14px; margin-bottom: 10px;
  border-left: 4px solid #1989fa; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.push-card.answered { border-left-color: #07c160; opacity: 0.85; }
.push-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.push-slot { display: flex; align-items: center; gap: 6px; }
.slot-icon { font-size: 18px; }
.slot-label { font-size: 14px; font-weight: 600; color: #333; }
.slot-time { font-size: 12px; color: #999; }

.push-knowledge { font-size: 14px; color: #333; line-height: 1.6; margin-bottom: 8px; }
.push-guide { font-size: 13px; color: #666; line-height: 1.5; padding: 8px 10px; background: #f6ffed; border-radius: 8px; margin-bottom: 8px; }

.survey-section { border-top: 1px solid #f0f0f0; padding-top: 12px; margin-top: 8px; }
.survey-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px; }
.survey-question { margin-bottom: 14px; }
.q-text { font-size: 13px; color: #333; margin-bottom: 6px; }

.recs-section { border-top: 1px solid #f0f0f0; padding-top: 10px; margin-top: 8px; }
.recs-title { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 6px; }
.rec-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #666; margin-bottom: 4px; }
</style>
