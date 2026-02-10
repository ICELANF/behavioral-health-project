<template>
  <div class="quiz-editor">
    <a-page-header
      :title="isEdit ? '编辑视频测试' : '创建视频测试'"
      :sub-title="video?.title"
      @back="$router.back()"
    />

    <a-card>
      <a-form :model="form" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <!-- 基本信息 -->
        <a-form-item label="测试标题" required>
          <a-input v-model:value="form.title" placeholder="如：第1章知识点测试" />
        </a-form-item>

        <a-form-item label="测试说明">
          <a-textarea v-model:value="form.description" :rows="2" placeholder="对本测试的简要说明" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="及格分数" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
              <a-input-number v-model:value="form.pass_score" :min="0" :max="100" /> 分
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大尝试" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
              <a-input-number v-model:value="form.max_attempts" :min="0" /> 次 (0=无限)
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="答题时限" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
              <a-input-number v-model:value="form.time_limit_seconds" :min="0" /> 秒 (0=无限制)
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider>学习激励配置</a-divider>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="教练满分加成" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
              <a-input-number v-model:value="form.coach_points_bonus" :min="0" /> 积分
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="成长者满分加成" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
              <a-input-number v-model:value="form.grower_minutes_bonus" :min="0" /> 分钟
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider>测试题目</a-divider>

        <!-- 题目列表 -->
        <div class="questions-list">
          <div v-for="(question, index) in form.questions" :key="index" class="question-card">
            <div class="question-header">
              <span class="question-number">第 {{ index + 1 }} 题</span>
              <a-space>
                <a-button size="small" @click="moveQuestion(index, -1)" :disabled="index === 0">
                  <UpOutlined />
                </a-button>
                <a-button size="small" @click="moveQuestion(index, 1)" :disabled="index === form.questions.length - 1">
                  <DownOutlined />
                </a-button>
                <a-button size="small" danger @click="removeQuestion(index)">
                  <DeleteOutlined />
                </a-button>
              </a-space>
            </div>

            <a-form-item label="题型" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-radio-group v-model:value="question.type" @change="handleTypeChange(index)">
                <a-radio-button value="single">单选题</a-radio-button>
                <a-radio-button value="multiple">多选题</a-radio-button>
                <a-radio-button value="judge">判断题</a-radio-button>
              </a-radio-group>
              <a-input-number
                v-model:value="question.points"
                :min="1"
                :max="100"
                style="width: 80px; margin-left: 16px"
              />
              <span style="margin-left: 4px; color: #999">分</span>
            </a-form-item>

            <a-form-item label="题目内容" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-textarea v-model:value="question.content" :rows="2" placeholder="输入题目内容" />
            </a-form-item>

            <!-- 选项（非判断题） -->
            <template v-if="question.type !== 'judge'">
              <a-form-item label="选项" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
                <div class="options-list">
                  <div v-for="(option, optIndex) in question.options" :key="optIndex" class="option-item">
                    <a-checkbox
                      v-if="question.type === 'multiple'"
                      :checked="isCorrectAnswer(question, option.key)"
                      @change="toggleCorrectAnswer(index, option.key)"
                    />
                    <a-radio
                      v-else
                      :checked="question.correct_answer === option.key"
                      @change="setCorrectAnswer(index, option.key)"
                    />
                    <span class="option-key">{{ option.key }}</span>
                    <a-input v-model:value="option.content" placeholder="选项内容" style="flex: 1" />
                    <a-button
                      type="text"
                      size="small"
                      danger
                      @click="removeOption(index, optIndex)"
                      :disabled="question.options.length <= 2"
                    >
                      <DeleteOutlined />
                    </a-button>
                  </div>
                  <a-button type="dashed" size="small" @click="addOption(index)" :disabled="question.options.length >= 6">
                    <PlusOutlined /> 添加选项
                  </a-button>
                </div>
              </a-form-item>
            </template>

            <!-- 判断题答案 -->
            <template v-else>
              <a-form-item label="正确答案" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
                <a-radio-group v-model:value="question.correct_answer">
                  <a-radio value="true">正确 ✓</a-radio>
                  <a-radio value="false">错误 ✗</a-radio>
                </a-radio-group>
              </a-form-item>
            </template>

            <a-form-item label="答案解析" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-textarea v-model:value="question.explanation" :rows="2" placeholder="选填，答题后显示" />
            </a-form-item>
          </div>

          <!-- 添加题目 -->
          <a-button type="dashed" block @click="addQuestion" class="add-question-btn">
            <PlusOutlined /> 添加题目
          </a-button>
        </div>

        <!-- 提交按钮 -->
        <a-form-item :wrapper-col="{ offset: 4, span: 18 }" style="margin-top: 24px">
          <a-space>
            <a-button type="primary" @click="handleSave" :loading="saving">保存测试</a-button>
            <a-button @click="handlePreview">预览</a-button>
            <a-button @click="$router.back()">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 预览弹窗 -->
    <a-modal v-model:open="previewVisible" title="测试预览" width="600px" :footer="null">
      <div class="quiz-preview">
        <h3>{{ form.title }}</h3>
        <p v-if="form.description">{{ form.description }}</p>
        <a-divider />
        <div v-for="(q, i) in form.questions" :key="i" class="preview-question">
          <div class="preview-question-header">
            <span class="q-number">{{ i + 1 }}.</span>
            <span class="q-type">[{{ q.type === 'single' ? '单选' : q.type === 'multiple' ? '多选' : '判断' }}]</span>
            <span class="q-points">{{ q.points }}分</span>
          </div>
          <div class="q-content">{{ q.content }}</div>
          <div class="q-options">
            <template v-if="q.type !== 'judge'">
              <div v-for="opt in q.options" :key="opt.key" class="q-option">
                {{ opt.key }}. {{ opt.content }}
                <span v-if="isCorrectAnswer(q, opt.key)" class="correct-mark">✓</span>
              </div>
            </template>
            <template v-else>
              <div class="q-option">
                正确答案：{{ q.correct_answer === 'true' ? '正确 ✓' : '错误 ✗' }}
              </div>
            </template>
          </div>
          <div v-if="q.explanation" class="q-explanation">
            <strong>解析：</strong>{{ q.explanation }}
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined, UpOutlined, DownOutlined } from '@ant-design/icons-vue'
import type { VideoQuiz, QuizQuestion, VideoContent } from '@/types/content'

const route = useRoute()
const router = useRouter()

const videoId = computed(() => route.params.videoId as string)
const quizId = computed(() => route.params.quizId as string)
const isEdit = computed(() => !!quizId.value)

const saving = ref(false)
const previewVisible = ref(false)
const video = ref<VideoContent | null>(null)

interface QuestionForm {
  question_id: string
  type: 'single' | 'multiple' | 'judge'
  content: string
  options: { key: string; content: string }[]
  correct_answer: string | string[]
  explanation: string
  points: number
}

const form = reactive({
  title: '',
  description: '',
  pass_score: 60,
  max_attempts: 3,
  time_limit_seconds: 0,
  coach_points_bonus: 5,
  grower_minutes_bonus: 5,
  questions: [] as QuestionForm[]
})

// 添加题目
const addQuestion = () => {
  form.questions.push({
    question_id: `q_${Date.now()}`,
    type: 'single',
    content: '',
    options: [
      { key: 'A', content: '' },
      { key: 'B', content: '' },
      { key: 'C', content: '' },
      { key: 'D', content: '' }
    ],
    correct_answer: '',
    explanation: '',
    points: 10
  })
}

// 删除题目
const removeQuestion = (index: number) => {
  form.questions.splice(index, 1)
}

// 移动题目
const moveQuestion = (index: number, direction: number) => {
  const newIndex = index + direction
  const temp = form.questions[index]
  form.questions[index] = form.questions[newIndex]
  form.questions[newIndex] = temp
}

// 题型变化处理
const handleTypeChange = (index: number) => {
  const q = form.questions[index]
  if (q.type === 'judge') {
    q.options = [
      { key: 'true', content: '正确' },
      { key: 'false', content: '错误' }
    ]
    q.correct_answer = 'true'
  } else {
    q.options = [
      { key: 'A', content: '' },
      { key: 'B', content: '' },
      { key: 'C', content: '' },
      { key: 'D', content: '' }
    ]
    q.correct_answer = q.type === 'multiple' ? [] : ''
  }
}

// 添加选项
const addOption = (qIndex: number) => {
  const q = form.questions[qIndex]
  const nextKey = String.fromCharCode(65 + q.options.length) // A, B, C, D, E, F
  q.options.push({ key: nextKey, content: '' })
}

// 删除选项
const removeOption = (qIndex: number, optIndex: number) => {
  form.questions[qIndex].options.splice(optIndex, 1)
  // 重新编排选项 key
  form.questions[qIndex].options.forEach((opt, i) => {
    opt.key = String.fromCharCode(65 + i)
  })
}

// 设置正确答案（单选）
const setCorrectAnswer = (qIndex: number, key: string) => {
  form.questions[qIndex].correct_answer = key
}

// 切换正确答案（多选）
const toggleCorrectAnswer = (qIndex: number, key: string) => {
  const q = form.questions[qIndex]
  const answers = (q.correct_answer as string[]) || []
  const index = answers.indexOf(key)
  if (index > -1) {
    answers.splice(index, 1)
  } else {
    answers.push(key)
  }
  q.correct_answer = answers
}

// 判断是否为正确答案
const isCorrectAnswer = (q: QuestionForm, key: string) => {
  if (Array.isArray(q.correct_answer)) {
    return q.correct_answer.includes(key)
  }
  return q.correct_answer === key
}

// 保存
const handleSave = async () => {
  // 验证
  if (!form.title) {
    message.error('请输入测试标题')
    return
  }
  if (form.questions.length === 0) {
    message.error('请至少添加一道题目')
    return
  }
  for (let i = 0; i < form.questions.length; i++) {
    const q = form.questions[i]
    if (!q.content) {
      message.error(`第 ${i + 1} 题内容不能为空`)
      return
    }
    if (q.type !== 'judge') {
      if (q.options.some(o => !o.content)) {
        message.error(`第 ${i + 1} 题选项内容不能为空`)
        return
      }
    }
    if (!q.correct_answer || (Array.isArray(q.correct_answer) && q.correct_answer.length === 0)) {
      message.error(`第 ${i + 1} 题请设置正确答案`)
      return
    }
  }

  saving.value = true
  try {
    const payload = {
      title: form.title,
      description: form.description,
      pass_score: form.pass_score,
      max_attempts: form.max_attempts,
      time_limit_seconds: form.time_limit_seconds,
      coach_points_bonus: form.coach_points_bonus,
      grower_minutes_bonus: form.grower_minutes_bonus,
      questions: form.questions.map(q => ({
        type: q.type,
        content: q.content,
        options: q.type !== 'judge' ? q.options : undefined,
        correct_answer: q.correct_answer,
        explanation: q.explanation,
        points: q.points,
      })),
    }
    const url = isEdit.value
      ? `/v1/content/video/${videoId.value}/quiz/${quizId.value}`
      : `/v1/content/video/${videoId.value}/quiz`
    if (isEdit.value) {
      await import('@/api/request').then(m => m.default.put(url, payload))
    } else {
      await import('@/api/request').then(m => m.default.post(url, payload))
    }
    message.success('保存成功')
    router.back()
  } catch (e) {
    console.error('Save quiz failed:', e)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 预览
const handlePreview = () => {
  previewVisible.value = true
}

onMounted(() => {
  // 如果没有题目，添加一道默认题目
  if (form.questions.length === 0) {
    addQuestion()
  }
})
</script>

<style scoped>
.quiz-editor {
  padding: 24px;
}

.questions-list {
  margin-bottom: 24px;
}

.question-card {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.question-number {
  font-weight: 600;
  font-size: 16px;
  color: #1890ff;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-key {
  width: 24px;
  font-weight: 500;
  color: #666;
}

.add-question-btn {
  height: 48px;
  font-size: 15px;
}

/* 预览样式 */
.quiz-preview h3 {
  margin-bottom: 8px;
}

.preview-question {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e8e8e8;
}

.preview-question-header {
  margin-bottom: 8px;
}

.q-number {
  font-weight: 600;
  margin-right: 8px;
}

.q-type {
  color: #1890ff;
  font-size: 12px;
  margin-right: 8px;
}

.q-points {
  color: #999;
  font-size: 12px;
}

.q-content {
  font-size: 15px;
  margin-bottom: 12px;
}

.q-options {
  padding-left: 20px;
}

.q-option {
  margin-bottom: 6px;
  color: #666;
}

.correct-mark {
  color: #52c41a;
  margin-left: 8px;
}

.q-explanation {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f6ffed;
  border-radius: 4px;
  font-size: 13px;
  color: #52c41a;
}
</style>
