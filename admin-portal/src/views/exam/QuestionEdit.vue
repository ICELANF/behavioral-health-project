<template>
  <div class="question-edit">
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/question/bank">题库管理</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>{{ isEdit ? '编辑题目' : '创建题目' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-form :model="formState" :rules="formRules" ref="formRef" layout="vertical">
        <a-row :gutter="24">
          <!-- 左侧：主要内容 -->
          <a-col :span="16">
            <a-card title="题目信息" :bordered="false">
              <!-- 第一行：类型、等级、难度 -->
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="题目类型" name="type">
                    <a-select v-model:value="formState.type" placeholder="选择题目类型" @change="handleTypeChange">
                      <a-select-option value="single">
                        <FormOutlined /> 单选题
                      </a-select-option>
                      <a-select-option value="multiple">
                        <CheckSquareOutlined /> 多选题
                      </a-select-option>
                      <a-select-option value="truefalse">
                        <CheckCircleOutlined /> 判断题
                      </a-select-option>
                      <a-select-option value="short_answer">
                        <EditOutlined /> 简答题
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="认证等级" name="level">
                    <a-select v-model:value="formState.level" placeholder="选择认证等级">
                      <a-select-option value="L0">L0 观察员</a-select-option>
                      <a-select-option value="L1">L1 成长者</a-select-option>
                      <a-select-option value="L2">L2 分享者</a-select-option>
                      <a-select-option value="L3">L3 教练</a-select-option>
                      <a-select-option value="L4">L4 促进师</a-select-option>
                      <a-select-option value="L5">L5 大师</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="难度等级" name="difficulty">
                    <a-rate v-model:value="formState.difficulty" :count="5" allow-half />
                    <span class="difficulty-text">{{ difficultyLabels[formState.difficulty] }}</span>
                  </a-form-item>
                </a-col>
              </a-row>

              <!-- 题目内容 -->
              <a-form-item label="题目内容" name="content">
                <a-textarea
                  v-model:value="formState.content"
                  placeholder="请输入题目内容"
                  :rows="4"
                  show-count
                  :maxlength="1000"
                />
              </a-form-item>

              <!-- 选项编辑器 (单选/多选时显示) -->
              <a-form-item
                v-if="showOptions"
                label="选项"
                name="options"
                :rules="[{ validator: validateOptions, trigger: 'change' }]"
              >
                <div class="options-editor">
                  <div
                    v-for="(option, index) in formState.options"
                    :key="index"
                    class="option-item"
                  >
                    <div class="option-selector">
                      <a-checkbox
                        v-if="formState.type === 'multiple'"
                        :checked="isOptionSelected(index)"
                        @change="toggleMultipleAnswer(index)"
                      />
                      <a-radio
                        v-else
                        :checked="formState.answer === index"
                        @click="formState.answer = index"
                      />
                    </div>
                    <span class="option-label">{{ String.fromCharCode(65 + index) }}.</span>
                    <a-input
                      v-model:value="formState.options[index]"
                      placeholder="请输入选项内容"
                      class="option-input"
                    />
                    <a-button
                      type="text"
                      danger
                      :disabled="formState.options.length <= 2"
                      @click="removeOption(index)"
                    >
                      <template #icon><DeleteOutlined /></template>
                    </a-button>
                  </div>
                  <a-button
                    type="dashed"
                    block
                    :disabled="formState.options.length >= 8"
                    @click="addOption"
                  >
                    <template #icon><PlusOutlined /></template>
                    添加选项
                  </a-button>
                  <div class="option-hint">
                    <InfoCircleOutlined />
                    {{ formState.type === 'multiple' ? '勾选多个正确答案' : '点击选择正确答案' }}
                  </div>
                </div>
              </a-form-item>

              <!-- 判断题答案 -->
              <a-form-item v-if="formState.type === 'truefalse'" label="正确答案" name="answer">
                <a-radio-group v-model:value="formState.answer">
                  <a-radio :value="true">
                    <CheckOutlined style="color: #52c41a" /> 正确
                  </a-radio>
                  <a-radio :value="false">
                    <CloseOutlined style="color: #ff4d4f" /> 错误
                  </a-radio>
                </a-radio-group>
              </a-form-item>

              <!-- 简答题参考答案 -->
              <a-form-item v-if="formState.type === 'short_answer'" label="参考答案" name="referenceAnswer">
                <a-textarea
                  v-model:value="formState.referenceAnswer"
                  placeholder="请输入参考答案（用于阅卷参考）"
                  :rows="4"
                />
              </a-form-item>

              <!-- 答案解析 -->
              <a-form-item label="答案解析">
                <a-textarea
                  v-model:value="formState.explanation"
                  placeholder="请输入答案解析，帮助学员理解"
                  :rows="3"
                />
              </a-form-item>
            </a-card>
          </a-col>

          <!-- 右侧：设置 -->
          <a-col :span="8">
            <a-card title="题目设置" :bordered="false" style="margin-bottom: 16px">
              <a-form-item label="默认分值" name="default_score">
                <a-input-number
                  v-model:value="formState.default_score"
                  :min="1"
                  :max="100"
                  style="width: 100%"
                >
                  <template #addonAfter>分</template>
                </a-input-number>
              </a-form-item>

              <a-form-item label="题目分类">
                <a-select
                  v-model:value="formState.category"
                  placeholder="选择分类"
                  allowClear
                >
                  <a-select-option value="behavior_science">行为科学</a-select-option>
                  <a-select-option value="motivation_interview">动机访谈</a-select-option>
                  <a-select-option value="chronic_disease">慢病管理</a-select-option>
                  <a-select-option value="nutrition">营养学</a-select-option>
                  <a-select-option value="psychology">心理学</a-select-option>
                  <a-select-option value="coaching_skill">教练技能</a-select-option>
                </a-select>
              </a-form-item>

              <a-form-item label="题目状态">
                <a-radio-group v-model:value="formState.status">
                  <a-radio value="active">启用</a-radio>
                  <a-radio value="inactive">禁用</a-radio>
                </a-radio-group>
              </a-form-item>
            </a-card>

            <a-card title="标签管理" :bordered="false" style="margin-bottom: 16px">
              <div class="tags-container">
                <a-tag
                  v-for="tag in formState.tags"
                  :key="tag"
                  closable
                  @close="removeTag(tag)"
                >
                  {{ tag }}
                </a-tag>
                <a-input
                  v-if="tagInputVisible"
                  ref="tagInputRef"
                  v-model:value="tagInputValue"
                  size="small"
                  style="width: 100px"
                  @blur="handleTagInputConfirm"
                  @keyup.enter="handleTagInputConfirm"
                />
                <a-tag v-else class="add-tag" @click="showTagInput">
                  <PlusOutlined /> 添加标签
                </a-tag>
              </div>
              <div class="common-tags">
                <span class="label">常用标签：</span>
                <a-tag
                  v-for="tag in commonTags"
                  :key="tag"
                  :class="{ selected: formState.tags.includes(tag) }"
                  @click="toggleCommonTag(tag)"
                >
                  {{ tag }}
                </a-tag>
              </div>
            </a-card>

            <!-- 操作按钮 -->
            <a-card :bordered="false">
              <a-space direction="vertical" style="width: 100%">
                <a-button type="primary" block :loading="saving" @click="handleSave">
                  <template #icon><SaveOutlined /></template>
                  {{ isEdit ? '保存修改' : '创建题目' }}
                </a-button>
                <a-button block @click="handlePreview">
                  <template #icon><EyeOutlined /></template>
                  预览效果
                </a-button>
                <a-button block @click="handleCancel">取消</a-button>
              </a-space>
            </a-card>
          </a-col>
        </a-row>
      </a-form>
    </a-spin>

    <!-- 预览弹窗 -->
    <a-modal
      v-model:open="previewVisible"
      title="题目预览"
      :footer="null"
      width="700px"
    >
      <div class="question-preview">
        <div class="preview-header">
          <a-tag :color="levelColors[formState.level]">{{ formState.level }}</a-tag>
          <a-tag :color="typeColors[formState.type]">{{ typeLabels[formState.type] }}</a-tag>
          <a-rate :value="formState.difficulty" disabled :count="5" style="font-size: 14px" />
          <span class="score">{{ formState.default_score }}分</span>
        </div>
        <div class="preview-content">
          <p class="question-text">{{ formState.content }}</p>

          <!-- 单选/多选选项 -->
          <div v-if="showOptions" class="preview-options">
            <div
              v-for="(option, index) in formState.options"
              :key="index"
              :class="['preview-option', { correct: isAnswerCorrect(index) }]"
            >
              <span class="option-letter">{{ String.fromCharCode(65 + index) }}</span>
              <span class="option-text">{{ option }}</span>
              <CheckOutlined v-if="isAnswerCorrect(index)" class="correct-icon" />
            </div>
          </div>

          <!-- 判断题 -->
          <div v-if="formState.type === 'truefalse'" class="preview-truefalse">
            <span :class="['tf-option', { correct: formState.answer === true }]">
              <CheckOutlined /> 正确
            </span>
            <span :class="['tf-option', { correct: formState.answer === false }]">
              <CloseOutlined /> 错误
            </span>
          </div>
        </div>

        <a-divider />
        <div class="preview-explanation" v-if="formState.explanation">
          <strong>答案解析：</strong>
          <p>{{ formState.explanation }}</p>
        </div>

        <div class="preview-tags" v-if="formState.tags.length > 0">
          <strong>标签：</strong>
          <a-tag v-for="tag in formState.tags" :key="tag">{{ tag }}</a-tag>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  EyeOutlined,
  CheckOutlined,
  CloseOutlined,
  FormOutlined,
  CheckSquareOutlined,
  CheckCircleOutlined,
  EditOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'
import type { QuestionType, CertificationLevel } from '../../types/exam'
import { questionApi } from '../../api/question'

const route = useRoute()
const router = useRouter()

// 是否编辑模式
const isEdit = computed(() => !!route.params.id)
const questionId = computed(() => route.params.id as string)

// 加载状态
const loading = ref(false)
const saving = ref(false)
const previewVisible = ref(false)

// 表单引用
const formRef = ref()

// 表单数据
const formState = reactive({
  type: 'single' as QuestionType,
  level: 'L1' as CertificationLevel,
  difficulty: 3,
  content: '',
  options: ['', '', '', ''],
  answer: 0 as number | boolean | number[],
  referenceAnswer: '',
  explanation: '',
  default_score: 2,
  category: undefined as string | undefined,
  status: 'active' as 'active' | 'inactive',
  tags: [] as string[]
})

// 表单验证规则
const formRules = {
  type: [{ required: true, message: '请选择题目类型' }],
  level: [{ required: true, message: '请选择认证等级' }],
  content: [{ required: true, message: '请输入题目内容' }],
  difficulty: [{ required: true, message: '请设置难度等级' }],
  default_score: [{ required: true, message: '请设置默认分值' }]
}

// 验证选项
const validateOptions = async (_rule: any, value: string[]) => {
  if (!showOptions.value) return Promise.resolve()

  const validOptions = value.filter(opt => opt.trim() !== '')
  if (validOptions.length < 2) {
    return Promise.reject('至少需要2个有效选项')
  }

  // 验证是否选择了答案
  if (formState.type === 'single' && typeof formState.answer !== 'number') {
    return Promise.reject('请选择正确答案')
  }
  if (formState.type === 'multiple') {
    const answers = formState.answer as number[]
    if (!Array.isArray(answers) || answers.length === 0) {
      return Promise.reject('请选择至少一个正确答案')
    }
  }

  return Promise.resolve()
}

// 难度标签
const difficultyLabels: Record<number, string> = {
  1: '简单',
  2: '较易',
  3: '中等',
  4: '较难',
  5: '困难'
}

// 类型标签和颜色
const typeLabels: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  truefalse: '判断题',
  short_answer: '简答题'
}

const typeColors: Record<string, string> = {
  single: 'blue',
  multiple: 'green',
  truefalse: 'orange',
  short_answer: 'purple'
}

const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple'
}

// 常用标签
const commonTags = ['行为科学', 'TTM模型', '动机访谈', 'COM-B', '糖尿病', '高血压', '体重管理', '教练技能']

// 标签输入
const tagInputVisible = ref(false)
const tagInputValue = ref('')
const tagInputRef = ref()

// 是否显示选项编辑器
const showOptions = computed(() => {
  return formState.type === 'single' || formState.type === 'multiple'
})

// 处理类型变更
const handleTypeChange = (type: QuestionType) => {
  if (type === 'single') {
    formState.answer = 0
    if (formState.options.length < 2) {
      formState.options = ['', '', '', '']
    }
  } else if (type === 'multiple') {
    formState.answer = []
    if (formState.options.length < 2) {
      formState.options = ['', '', '', '']
    }
  } else if (type === 'truefalse') {
    formState.answer = true
    formState.options = []
  } else {
    formState.answer = 0
    formState.options = []
  }
}

// 添加选项
const addOption = () => {
  if (formState.options.length < 8) {
    formState.options.push('')
  }
}

// 删除选项
const removeOption = (index: number) => {
  if (formState.options.length <= 2) return

  formState.options.splice(index, 1)

  // 更新答案索引
  if (formState.type === 'single') {
    if (formState.answer === index) {
      formState.answer = 0
    } else if ((formState.answer as number) > index) {
      formState.answer = (formState.answer as number) - 1
    }
  } else if (formState.type === 'multiple') {
    const answers = formState.answer as number[]
    formState.answer = answers
      .filter(a => a !== index)
      .map(a => a > index ? a - 1 : a)
  }
}

// 判断选项是否被选中（多选）
const isOptionSelected = (index: number) => {
  if (formState.type !== 'multiple') return false
  return (formState.answer as number[]).includes(index)
}

// 切换多选答案
const toggleMultipleAnswer = (index: number) => {
  if (formState.type !== 'multiple') return

  const answers = formState.answer as number[]
  const idx = answers.indexOf(index)
  if (idx > -1) {
    answers.splice(idx, 1)
  } else {
    answers.push(index)
    answers.sort((a, b) => a - b)
  }
}

// 判断是否是正确答案
const isAnswerCorrect = (index: number) => {
  if (formState.type === 'single') {
    return formState.answer === index
  } else if (formState.type === 'multiple') {
    return (formState.answer as number[]).includes(index)
  }
  return false
}

// 标签管理
const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

const handleTagInputConfirm = () => {
  const value = tagInputValue.value.trim()
  if (value && !formState.tags.includes(value)) {
    formState.tags.push(value)
  }
  tagInputVisible.value = false
  tagInputValue.value = ''
}

const removeTag = (tag: string) => {
  const index = formState.tags.indexOf(tag)
  if (index > -1) {
    formState.tags.splice(index, 1)
  }
}

const toggleCommonTag = (tag: string) => {
  if (formState.tags.includes(tag)) {
    removeTag(tag)
  } else {
    formState.tags.push(tag)
  }
}

// 预览
const handlePreview = () => {
  previewVisible.value = true
}

// 保存
const handleSave = async () => {
  try {
    await formRef.value?.validate()

    saving.value = true

    if (isEdit.value) {
      const questionId = route.params.id as string
      await questionApi.update(questionId, formState)
    } else {
      await questionApi.create(formState)
    }

    message.success(isEdit.value ? '题目已更新' : '题目已创建')
    router.push('/question/bank')
  } catch (error) {
    console.error('Validation failed:', error)
  } finally {
    saving.value = false
  }
}

// 取消
const handleCancel = () => {
  router.push('/question/bank')
}

// 加载题目数据
const loadQuestion = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    const questionId = route.params.id as string
    const res = await questionApi.get(questionId)
    const q = res.data?.data || res.data
    if (q) {
      Object.assign(formState, {
        type: q.type || 'single',
        level: q.level || 'L1',
        difficulty: q.difficulty || 1,
        content: q.content || '',
        options: q.options || ['', '', '', ''],
        answer: q.answer ?? null,
        explanation: q.explanation || '',
        default_score: q.default_score || 1,
        category: q.category || '',
        status: q.status || 'draft',
        tags: q.tags || []
      })
    }
  } catch (e) {
    console.error('加载题目失败:', e)
    message.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadQuestion()
})
</script>

<style scoped>
.question-edit {
  padding: 0;
}

.difficulty-text {
  margin-left: 8px;
  color: #666;
  font-size: 13px;
}

.options-editor {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.option-selector {
  flex-shrink: 0;
}

.option-label {
  font-weight: 500;
  color: #666;
  width: 24px;
  flex-shrink: 0;
}

.option-input {
  flex: 1;
}

.option-hint {
  margin-top: 12px;
  color: #999;
  font-size: 13px;
}

.option-hint :deep(.anticon) {
  margin-right: 4px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.add-tag {
  border-style: dashed;
  cursor: pointer;
}

.common-tags {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e8e8e8;
}

.common-tags .label {
  font-size: 12px;
  color: #999;
  margin-right: 8px;
}

.common-tags .ant-tag {
  cursor: pointer;
  margin: 2px;
}

.common-tags .ant-tag.selected {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}

/* 预览样式 */
.question-preview {
  padding: 16px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.preview-header .score {
  margin-left: auto;
  font-weight: 500;
  color: #1890ff;
}

.preview-content .question-text {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 16px;
}

.preview-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-option {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.preview-option.correct {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.preview-option .option-letter {
  font-weight: 500;
  margin-right: 12px;
  color: #666;
}

.preview-option .option-text {
  flex: 1;
}

.preview-option .correct-icon {
  color: #52c41a;
}

.preview-truefalse {
  display: flex;
  gap: 24px;
}

.tf-option {
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.tf-option.correct {
  background: #f6ffed;
  border-color: #b7eb8f;
  color: #52c41a;
}

.preview-explanation {
  color: #666;
  font-size: 14px;
}

.preview-tags {
  margin-top: 12px;
}

.preview-tags strong {
  margin-right: 8px;
}
</style>
