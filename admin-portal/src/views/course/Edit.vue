<template>
  <div class="course-edit">
    <div class="page-header">
      <a-breadcrumb>
        <a-breadcrumb-item><a @click="$router.push('/course/list')">课程列表</a></a-breadcrumb-item>
        <a-breadcrumb-item>{{ isEdit ? '编辑课程' : '创建课程' }}</a-breadcrumb-item>
      </a-breadcrumb>
    </div>

    <a-form :model="formState" layout="vertical" @finish="handleSubmit">
      <a-row :gutter="24">
        <a-col :span="16">
          <a-card title="基本信息">
            <a-form-item label="课程名称" name="title" :rules="[{ required: true, message: '请输入课程名称' }]">
              <a-input v-model:value="formState.title" placeholder="请输入课程名称" />
            </a-form-item>

            <a-form-item label="课程简介" name="description">
              <a-textarea v-model:value="formState.description" :rows="4" placeholder="请输入课程简介" />
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="认证等级" name="level" :rules="[{ required: true, message: '请选择认证等级' }]">
                  <a-select v-model:value="formState.level" placeholder="选择等级">
                    <a-select-option value="L0">L0 公众学习</a-select-option>
                    <a-select-option value="L1">L1 初级教练</a-select-option>
                    <a-select-option value="L2">L2 中级教练</a-select-option>
                    <a-select-option value="L3">L3 高级教练</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="课程类别" name="category" :rules="[{ required: true, message: '请选择课程类别' }]">
                  <a-select v-model:value="formState.category" placeholder="选择类别">
                    <a-select-option value="knowledge">知识体系 (Knowledge)</a-select-option>
                    <a-select-option value="method">方法体系 (Method)</a-select-option>
                    <a-select-option value="skill">核心技能 (Skill)</a-select-option>
                    <a-select-option value="value">观念心智 (Value)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="课程价格" name="price">
                  <a-input-number v-model:value="formState.price" :min="0" :precision="2" style="width: 100%">
                    <template #addonBefore>¥</template>
                  </a-input-number>
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="学习目标">
              <div v-for="(obj, index) in formState.objectives" :key="index" class="objective-row">
                <a-input v-model:value="formState.objectives[index]" placeholder="请输入学习目标" />
                <a-button v-if="formState.objectives.length > 1" type="text" danger @click="removeObjective(index)">
                  删除
                </a-button>
              </div>
              <a-button type="dashed" block @click="addObjective">
                <template #icon><PlusOutlined /></template>
                添加学习目标
              </a-button>
            </a-form-item>

            <a-form-item label="前置课程">
              <a-select
                v-model:value="formState.prerequisites"
                mode="multiple"
                placeholder="选择前置课程（可选）"
                :options="availableCourses"
              />
            </a-form-item>
          </a-card>

          <a-card title="考核设置" style="margin-top: 16px">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="章节测验通过分数">
                  <a-input-number v-model:value="formState.quiz_pass_score" :min="0" :max="100" addon-after="分" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="允许测验重试">
                  <a-switch v-model:checked="formState.allow_quiz_retry" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="必须按顺序学习">
                  <a-switch v-model:checked="formState.sequential_learning" />
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="关联考试">
              <a-select
                v-model:value="formState.related_exam"
                placeholder="选择关联的认证考试（可选）"
                allowClear
              >
                <a-select-option value="EXM-L0-T01">L0 入门知识测验</a-select-option>
                <a-select-option value="EXM-L1-T01">L1 理论机考</a-select-option>
                <a-select-option value="EXM-L2-T01">L2 理论考试</a-select-option>
              </a-select>
            </a-form-item>
          </a-card>
        </a-col>

        <a-col :span="8">
          <a-card title="课程封面">
            <a-upload
              v-model:file-list="coverFileList"
              list-type="picture-card"
              :max-count="1"
              :customRequest="handleCoverUpload"
              @preview="handleCoverPreview"
            >
              <div v-if="!coverFileList.length">
                <PlusOutlined />
                <div style="margin-top: 8px">上传封面</div>
              </div>
            </a-upload>
            <p class="upload-tip">建议尺寸: 800x450px，JPG/PNG格式</p>
          </a-card>

          <a-card title="课程标签" style="margin-top: 16px">
            <a-select
              v-model:value="formState.tags"
              mode="tags"
              placeholder="输入标签后回车"
              style="width: 100%"
            />
          </a-card>

          <a-card title="发布设置" style="margin-top: 16px">
            <a-form-item label="课程状态">
              <a-radio-group v-model:value="formState.status">
                <a-radio value="draft">草稿</a-radio>
                <a-radio value="published">立即发布</a-radio>
              </a-radio-group>
            </a-form-item>

            <a-form-item label="可见范围">
              <a-select v-model:value="formState.visibility">
                <a-select-option value="all">所有用户</a-select-option>
                <a-select-option value="registered">注册用户</a-select-option>
                <a-select-option value="paid">付费用户</a-select-option>
              </a-select>
            </a-form-item>
          </a-card>
        </a-col>
      </a-row>

      <div class="form-actions">
        <a-space>
          <a-button @click="$router.back()">取消</a-button>
          <a-button type="primary" html-type="submit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建课程' }}
          </a-button>
        </a-space>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const submitting = ref(false)
const coverFileList = ref<any[]>([])

const formState = reactive({
  title: '',
  description: '',
  level: undefined as string | undefined,
  category: undefined as string | undefined,
  price: 0,
  objectives: [''],
  prerequisites: [] as string[],
  quiz_pass_score: 80,
  allow_quiz_retry: true,
  sequential_learning: true,
  related_exam: undefined as string | undefined,
  tags: [] as string[],
  status: 'draft',
  visibility: 'all'
})

const availableCourses = [
  { value: 'c1', label: '行为健康入门' },
  { value: 'c2', label: '慢病与代谢基础认知' }
]

onMounted(() => {
  if (isEdit.value) {
    // TODO: 加载课程数据
    formState.title = '行为健康入门'
    formState.level = 'L0'
    formState.category = 'knowledge'
  }
})

const addObjective = () => {
  formState.objectives.push('')
}

const removeObjective = (index: number) => {
  formState.objectives.splice(index, 1)
}

const handleCoverUpload = (options: any) => {
  const { file, onSuccess } = options
  // TODO: 上传到OSS
  setTimeout(() => {
    coverFileList.value = [{
      uid: '-1',
      name: file.name,
      status: 'done',
      url: URL.createObjectURL(file)
    }]
    onSuccess?.()
  }, 1000)
}

const handleCoverPreview = (file: any) => {
  window.open(file.url)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    // TODO: 调用API保存课程
    await new Promise(resolve => setTimeout(resolve, 1000))
    message.success(isEdit.value ? '课程已更新' : '课程已创建')
    router.push('/course/list')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.objective-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.upload-tip {
  color: #999;
  font-size: 12px;
  margin-top: 8px;
}

.form-actions {
  margin-top: 24px;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}
</style>
