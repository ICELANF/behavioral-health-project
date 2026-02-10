<template>
  <div class="chapters-page">
    <div class="page-header">
      <div>
        <a-breadcrumb>
          <a-breadcrumb-item><a @click="$router.push('/course/list')">课程列表</a></a-breadcrumb-item>
          <a-breadcrumb-item>{{ course.title }}</a-breadcrumb-item>
        </a-breadcrumb>
        <h2 style="margin-top: 8px">章节管理</h2>
      </div>
      <a-button type="primary" @click="showAddChapter">
        <template #icon><PlusOutlined /></template>
        添加章节
      </a-button>
    </div>

    <!-- 章节列表 -->
    <a-collapse v-model:activeKey="activeKeys" class="chapter-list">
      <a-collapse-panel v-for="(chapter, index) in chapters" :key="chapter.chapter_id" :header="null">
        <template #header>
          <div class="chapter-header">
            <div class="chapter-info">
              <span class="chapter-index">第{{ index + 1 }}章</span>
              <span class="chapter-title">{{ chapter.title }}</span>
              <a-tag v-if="chapter.video_id" color="green">视频已上传</a-tag>
              <a-tag v-else color="orange">待上传视频</a-tag>
              <a-tag color="blue">{{ chapter.quizzes?.length || 0 }} 道题目</a-tag>
            </div>
            <div class="chapter-actions" @click.stop>
              <a-button size="small" @click="editChapter(chapter)">编辑</a-button>
              <a-button size="small" type="primary" @click="showQuizModal(chapter)">
                管理题目
              </a-button>
              <a-button size="small" danger @click="deleteChapter(chapter)">删除</a-button>
            </div>
          </div>
        </template>

        <div class="chapter-content">
          <a-row :gutter="24">
            <!-- 视频上传区 -->
            <a-col :span="12">
              <a-card title="视频内容" size="small">
                <div v-if="chapter.video_url" class="video-preview">
                  <video :src="chapter.video_url" controls style="width: 100%; max-height: 200px" />
                  <div class="video-info">
                    <span>时长: {{ formatDuration(chapter.duration_seconds) }}</span>
                    <a-button size="small" @click="reuploadVideo(chapter)">重新上传</a-button>
                  </div>
                </div>
                <div v-else class="video-upload">
                  <a-upload
                    :customRequest="(options) => handleVideoUpload(options, chapter)"
                    accept="video/*"
                    :showUploadList="false"
                  >
                    <a-button>
                      <template #icon><UploadOutlined /></template>
                      上传视频
                    </a-button>
                  </a-upload>
                  <p class="upload-tip">支持 MP4、MOV 格式，建议 720P 以上</p>
                </div>
              </a-card>
            </a-col>

            <!-- 题目预览 -->
            <a-col :span="12">
              <a-card title="章节测验" size="small">
                <template #extra>
                  <a @click="showQuizModal(chapter)">编辑题目</a>
                </template>
                <div v-if="chapter.quizzes?.length" class="quiz-preview">
                  <div v-for="(quiz, qIndex) in chapter.quizzes.slice(0, 3)" :key="quiz.quiz_id" class="quiz-item">
                    <div class="quiz-index">{{ qIndex + 1 }}.</div>
                    <div class="quiz-content">
                      <div class="quiz-question">{{ quiz.question }}</div>
                      <a-tag :color="quizTypeColors[quiz.type]">{{ quizTypeLabels[quiz.type] }}</a-tag>
                    </div>
                  </div>
                  <div v-if="chapter.quizzes.length > 3" class="more-quizzes">
                    还有 {{ chapter.quizzes.length - 3 }} 道题目...
                  </div>
                </div>
                <a-empty v-else description="暂无题目">
                  <a-button type="primary" size="small" @click="showQuizModal(chapter)">
                    添加题目
                  </a-button>
                </a-empty>
              </a-card>
            </a-col>
          </a-row>

          <!-- 触发时机设置 -->
          <a-card title="测验触发设置" size="small" style="margin-top: 16px">
            <a-form layout="inline">
              <a-form-item label="触发时机">
                <a-select v-model:value="chapter.quiz_trigger" style="width: 200px">
                  <a-select-option value="after_video">视频结束后</a-select-option>
                  <a-select-option value="during_video">视频播放中(暂停)</a-select-option>
                  <a-select-option value="both">两者都有</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item v-if="chapter.quiz_trigger === 'during_video' || chapter.quiz_trigger === 'both'" label="弹出时间点">
                <a-input-number v-model:value="chapter.quiz_popup_time" :min="0" addon-after="秒" />
              </a-form-item>
              <a-form-item label="通过分数">
                <a-input-number v-model:value="chapter.pass_score" :min="0" :max="100" addon-after="分" />
              </a-form-item>
              <a-form-item label="允许重试">
                <a-switch v-model:checked="chapter.allow_retry" />
              </a-form-item>
            </a-form>
          </a-card>
        </div>
      </a-collapse-panel>
    </a-collapse>

    <a-empty v-if="!chapters.length" description="暂无章节">
      <a-button type="primary" @click="showAddChapter">添加第一个章节</a-button>
    </a-empty>

    <!-- 添加/编辑章节弹窗 -->
    <a-modal
      v-model:open="chapterModalVisible"
      :title="editingChapter ? '编辑章节' : '添加章节'"
      @ok="saveChapter"
    >
      <a-form :model="chapterForm" layout="vertical">
        <a-form-item label="章节标题" required>
          <a-input v-model:value="chapterForm.title" placeholder="请输入章节标题" />
        </a-form-item>
        <a-form-item label="章节描述">
          <a-textarea v-model:value="chapterForm.description" placeholder="请输入章节描述" :rows="3" />
        </a-form-item>
        <a-form-item label="学习目标">
          <a-textarea v-model:value="chapterForm.objectives" placeholder="请输入学习目标，每行一个" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 题目管理弹窗 -->
    <a-modal
      v-model:open="quizModalVisible"
      title="管理章节题目"
      width="900px"
      @ok="saveQuizzes"
    >
      <div class="quiz-editor">
        <div class="quiz-toolbar">
          <a-space>
            <a-button type="primary" @click="addQuiz('single')">
              <template #icon><PlusOutlined /></template>
              添加单选题
            </a-button>
            <a-button @click="addQuiz('multiple')">
              <template #icon><PlusOutlined /></template>
              添加多选题
            </a-button>
            <a-button @click="addQuiz('truefalse')">
              <template #icon><PlusOutlined /></template>
              添加判断题
            </a-button>
          </a-space>
          <span class="quiz-count">共 {{ currentQuizzes.length }} 道题目</span>
        </div>

        <a-divider />

        <div class="quiz-list">
          <div v-for="(quiz, index) in currentQuizzes" :key="quiz.quiz_id" class="quiz-edit-item">
            <div class="quiz-edit-header">
              <span class="quiz-num">第 {{ index + 1 }} 题</span>
              <a-tag :color="quizTypeColors[quiz.type]">{{ quizTypeLabels[quiz.type] }}</a-tag>
              <a-button size="small" danger type="text" @click="removeQuiz(index)">删除</a-button>
            </div>

            <a-form-item label="题目内容">
              <a-textarea v-model:value="quiz.question" :rows="2" placeholder="请输入题目内容" />
            </a-form-item>

            <!-- 选择题选项 -->
            <template v-if="quiz.type === 'single' || quiz.type === 'multiple'">
              <a-form-item label="选项">
                <div v-for="(opt, optIndex) in quiz.options" :key="optIndex" class="option-row">
                  <a-input v-model:value="quiz.options[optIndex]" :addon-before="String.fromCharCode(65 + optIndex)" style="flex: 1" />
                  <a-button v-if="quiz.options.length > 2" type="text" danger @click="removeOption(quiz, optIndex)">
                    删除
                  </a-button>
                </div>
                <a-button v-if="quiz.options.length < 6" type="dashed" block @click="addOption(quiz)">
                  添加选项
                </a-button>
              </a-form-item>

              <a-form-item label="正确答案">
                <a-select
                  v-if="quiz.type === 'single'"
                  v-model:value="quiz.answer"
                  placeholder="选择正确答案"
                  style="width: 200px"
                >
                  <a-select-option v-for="(opt, optIndex) in quiz.options" :key="optIndex" :value="optIndex">
                    {{ String.fromCharCode(65 + optIndex) }}. {{ opt }}
                  </a-select-option>
                </a-select>
                <a-checkbox-group v-else v-model:value="quiz.answers">
                  <a-checkbox v-for="(opt, optIndex) in quiz.options" :key="optIndex" :value="optIndex">
                    {{ String.fromCharCode(65 + optIndex) }}
                  </a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </template>

            <!-- 判断题 -->
            <template v-if="quiz.type === 'truefalse'">
              <a-form-item label="正确答案">
                <a-radio-group v-model:value="quiz.answer">
                  <a-radio :value="true">正确</a-radio>
                  <a-radio :value="false">错误</a-radio>
                </a-radio-group>
              </a-form-item>
            </template>

            <a-form-item label="答案解析">
              <a-textarea v-model:value="quiz.explanation" :rows="2" placeholder="请输入答案解析（可选）" />
            </a-form-item>

            <a-divider v-if="index < currentQuizzes.length - 1" />
          </div>

          <a-empty v-if="!currentQuizzes.length" description="暂无题目，请点击上方按钮添加" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { v4 as uuidv4 } from 'uuid'
import request from '@/api/request'

const route = useRoute()
const courseId = route.params.courseId as string

const course = ref({ title: '加载中...' } as any)
const chapters = ref<any[]>([])
const activeKeys = ref<string[]>([])

const chapterModalVisible = ref(false)
const quizModalVisible = ref(false)
const editingChapter = ref<any>(null)
const currentChapter = ref<any>(null)
const currentQuizzes = ref<any[]>([])

const chapterForm = reactive({
  title: '',
  description: '',
  objectives: ''
})

const quizTypeLabels: Record<string, string> = {
  single: '单选题',
  multiple: '多选题',
  truefalse: '判断题'
}

const quizTypeColors: Record<string, string> = {
  single: 'blue',
  multiple: 'green',
  truefalse: 'orange'
}

onMounted(async () => {
  try {
    const { data } = await request.get(`/v1/content-manage/${courseId}`)
    if (data) {
      course.value = { title: data.title || '未命名课程', ...data }
    }
  } catch (e) {
    console.error('Load course failed:', e)
    course.value = { title: '加载失败' }
  }
  // Chapters are managed locally for this course until a chapters API is available
  if (chapters.value.length === 0) {
    chapters.value = [
      {
        chapter_id: uuidv4(),
        title: '第一章',
        video_id: '',
        video_url: '',
        duration_seconds: 0,
        quiz_trigger: 'after_video',
        pass_score: 80,
        allow_retry: true,
        quizzes: []
      }
    ]
  }
  activeKeys.value = [chapters.value[0]?.chapter_id]
})

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}分${secs}秒`
}

const showAddChapter = () => {
  editingChapter.value = null
  chapterForm.title = ''
  chapterForm.description = ''
  chapterForm.objectives = ''
  chapterModalVisible.value = true
}

const editChapter = (chapter: any) => {
  editingChapter.value = chapter
  chapterForm.title = chapter.title
  chapterForm.description = chapter.description || ''
  chapterForm.objectives = chapter.objectives || ''
  chapterModalVisible.value = true
}

const saveChapter = () => {
  if (!chapterForm.title) {
    message.error('请输入章节标题')
    return
  }

  if (editingChapter.value) {
    editingChapter.value.title = chapterForm.title
    editingChapter.value.description = chapterForm.description
    editingChapter.value.objectives = chapterForm.objectives
    message.success('章节已更新')
  } else {
    const newChapter = {
      chapter_id: uuidv4(),
      title: chapterForm.title,
      description: chapterForm.description,
      objectives: chapterForm.objectives,
      video_id: '',
      video_url: '',
      duration_seconds: 0,
      quiz_trigger: 'after_video',
      pass_score: 80,
      allow_retry: true,
      quizzes: []
    }
    chapters.value.push(newChapter)
    activeKeys.value.push(newChapter.chapter_id)
    message.success('章节已添加')
  }
  chapterModalVisible.value = false
}

const deleteChapter = (chapter: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除章节「${chapter.title}」吗？`,
    okType: 'danger',
    onOk() {
      const index = chapters.value.findIndex(c => c.chapter_id === chapter.chapter_id)
      if (index > -1) {
        chapters.value.splice(index, 1)
        message.success('章节已删除')
      }
    }
  })
}

const handleVideoUpload = async (options: any, chapter: any) => {
  const { file, onSuccess, onError } = options

  message.loading('视频处理中...', 0)
  // Use local blob URL for preview; production would upload to CDN
  const localUrl = URL.createObjectURL(file)
  const video = document.createElement('video')
  video.preload = 'metadata'
  video.onloadedmetadata = () => {
    message.destroy()
    chapter.video_id = 'v' + Date.now()
    chapter.video_url = localUrl
    chapter.duration_seconds = Math.round(video.duration)
    message.success('视频已加载')
    onSuccess?.()
  }
  video.onerror = () => {
    message.destroy()
    message.error('视频文件无法解析')
    onError?.(new Error('Invalid video'))
  }
  video.src = localUrl
}

const reuploadVideo = (chapter: any) => {
  chapter.video_id = ''
  chapter.video_url = ''
  chapter.duration_seconds = 0
}

const showQuizModal = (chapter: any) => {
  currentChapter.value = chapter
  currentQuizzes.value = JSON.parse(JSON.stringify(chapter.quizzes || []))
  quizModalVisible.value = true
}

const addQuiz = (type: 'single' | 'multiple' | 'truefalse') => {
  const newQuiz: any = {
    quiz_id: uuidv4(),
    type,
    question: '',
    explanation: ''
  }

  if (type === 'single') {
    newQuiz.options = ['', '', '', '']
    newQuiz.answer = 0
  } else if (type === 'multiple') {
    newQuiz.options = ['', '', '', '']
    newQuiz.answers = []
  } else {
    newQuiz.answer = true
  }

  currentQuizzes.value.push(newQuiz)
}

const removeQuiz = (index: number) => {
  currentQuizzes.value.splice(index, 1)
}

const addOption = (quiz: any) => {
  quiz.options.push('')
}

const removeOption = (quiz: any, index: number) => {
  quiz.options.splice(index, 1)
  // 调整答案索引
  if (quiz.type === 'single' && quiz.answer >= index) {
    quiz.answer = Math.max(0, quiz.answer - 1)
  } else if (quiz.type === 'multiple') {
    quiz.answers = quiz.answers.filter((a: number) => a !== index).map((a: number) => a > index ? a - 1 : a)
  }
}

const saveQuizzes = () => {
  // 验证题目
  for (const quiz of currentQuizzes.value) {
    if (!quiz.question.trim()) {
      message.error('请填写所有题目内容')
      return
    }
    if ((quiz.type === 'single' || quiz.type === 'multiple') && quiz.options.some((o: string) => !o.trim())) {
      message.error('请填写所有选项内容')
      return
    }
    if (quiz.type === 'multiple' && (!quiz.answers || quiz.answers.length === 0)) {
      message.error('多选题请至少选择一个正确答案')
      return
    }
  }

  currentChapter.value.quizzes = currentQuizzes.value
  message.success('题目已保存')
  quizModalVisible.value = false
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.chapter-list {
  background: transparent;
}

.chapter-list :deep(.ant-collapse-item) {
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-index {
  color: #1890ff;
  font-weight: 500;
}

.chapter-title {
  font-weight: 500;
}

.chapter-actions {
  display: flex;
  gap: 8px;
}

.chapter-content {
  padding: 16px 0;
}

.video-preview {
  text-align: center;
}

.video-info {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.video-upload {
  text-align: center;
  padding: 20px;
}

.upload-tip {
  margin-top: 8px;
  color: #999;
  font-size: 12px;
}

.quiz-preview .quiz-item {
  display: flex;
  margin-bottom: 12px;
}

.quiz-index {
  color: #1890ff;
  font-weight: 500;
  margin-right: 8px;
}

.quiz-question {
  margin-bottom: 4px;
}

.more-quizzes {
  color: #999;
  font-size: 12px;
}

.quiz-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quiz-count {
  color: #666;
}

.quiz-edit-item {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.quiz-edit-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.quiz-num {
  font-weight: 500;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
