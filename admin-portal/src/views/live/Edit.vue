<template>
  <div class="live-edit">
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item><router-link to="/live/list">直播管理</router-link></a-breadcrumb-item>
      <a-breadcrumb-item>{{ isEdit ? '编辑直播' : '创建直播' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-form :model="formState" :rules="formRules" ref="formRef" layout="vertical">
        <a-row :gutter="24">
          <!-- 左侧：基本信息 -->
          <a-col :span="16">
            <a-card title="基本信息" :bordered="false">
              <a-form-item label="直播标题" name="title">
                <a-input
                  v-model:value="formState.title"
                  placeholder="请输入直播标题"
                  :maxlength="50"
                  show-count
                />
              </a-form-item>

              <a-form-item label="直播简介" name="description">
                <a-textarea
                  v-model:value="formState.description"
                  placeholder="请输入直播简介，让学员了解直播内容"
                  :rows="4"
                  :maxlength="500"
                  show-count
                />
              </a-form-item>

              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="讲师" name="instructor_id">
                    <a-select
                      v-model:value="formState.instructor_id"
                      placeholder="选择讲师"
                      show-search
                      :filter-option="filterInstructor"
                    >
                      <a-select-option v-for="ins in instructors" :key="ins.id" :value="ins.id">
                        <div style="display: flex; align-items: center; gap: 8px">
                          <a-avatar :size="24">{{ ins.name[0] }}</a-avatar>
                          {{ ins.name }}
                          <a-tag :color="levelColors[ins.level]" size="small">{{ ins.level }}</a-tag>
                        </div>
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="学习受众" name="audience">
                    <a-select v-model:value="formState.audience" placeholder="谁来观看">
                      <a-select-option value="client"><span style="color:#1890ff">●</span> 服务对象</a-select-option>
                      <a-select-option value="coach"><span style="color:#52c41a">●</span> 教练</a-select-option>
                      <a-select-option value="both"><span style="color:#722ed1">●</span> 双受众</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="认证等级" name="level">
                    <a-select v-model:value="formState.level" placeholder="选择适用等级">
                      <a-select-option value="L0">L0 观察员</a-select-option>
                      <a-select-option value="L1">L1 成长者</a-select-option>
                      <a-select-option value="L2">L2 分享者</a-select-option>
                      <a-select-option value="L3">L3 教练</a-select-option>
                      <a-select-option value="L4">L4 促进师</a-select-option>
                      <a-select-option value="L5">L5 大师</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
            </a-card>

            <a-card title="时间设置" :bordered="false" style="margin-top: 16px">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="直播日期" name="date">
                    <a-date-picker
                      v-model:value="formState.date"
                      style="width: 100%"
                      :disabled-date="disabledDate"
                      placeholder="选择直播日期"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="开始时间" name="time">
                    <a-time-picker
                      v-model:value="formState.time"
                      style="width: 100%"
                      format="HH:mm"
                      :minute-step="15"
                      placeholder="选择开始时间"
                    />
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="预计时长" name="duration_minutes">
                <a-radio-group v-model:value="formState.duration_minutes" button-style="solid">
                  <a-radio-button :value="30">30分钟</a-radio-button>
                  <a-radio-button :value="60">1小时</a-radio-button>
                  <a-radio-button :value="90">1.5小时</a-radio-button>
                  <a-radio-button :value="120">2小时</a-radio-button>
                  <a-radio-button :value="180">3小时</a-radio-button>
                </a-radio-group>
                <div style="margin-top: 8px">
                  <span style="color: #999">或自定义：</span>
                  <a-input-number
                    v-model:value="formState.duration_minutes"
                    :min="15"
                    :max="480"
                    :step="15"
                    style="width: 100px"
                  />
                  <span style="margin-left: 8px; color: #999">分钟</span>
                </div>
              </a-form-item>
            </a-card>
          </a-col>

          <!-- 右侧：封面和设置 -->
          <a-col :span="8">
            <a-card title="直播封面" :bordered="false">
              <a-upload
                v-model:file-list="coverFileList"
                list-type="picture-card"
                :max-count="1"
                :before-upload="handleCoverUpload"
                accept="image/*"
                class="cover-uploader"
              >
                <div v-if="!coverFileList.length">
                  <PlusOutlined />
                  <div style="margin-top: 8px">上传封面</div>
                </div>
              </a-upload>
              <p class="upload-tip">建议尺寸: 800x450px，JPG/PNG格式</p>
            </a-card>

            <a-card title="直播设置" :bordered="false" style="margin-top: 16px">
              <a-form-item label="是否录制">
                <a-switch v-model:checked="formState.enable_recording" />
                <span style="margin-left: 8px; color: #999">录制直播内容用于回放</span>
              </a-form-item>

              <a-form-item label="允许回放">
                <a-switch v-model:checked="formState.enable_replay" :disabled="!formState.enable_recording" />
                <span style="margin-left: 8px; color: #999">直播结束后提供回放</span>
              </a-form-item>

              <a-form-item label="互动设置">
                <a-checkbox-group v-model:value="formState.interaction_options">
                  <a-checkbox value="chat">开启聊天</a-checkbox>
                  <a-checkbox value="question">开启提问</a-checkbox>
                  <a-checkbox value="poll">开启投票</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-card>

            <a-card title="开播提醒" :bordered="false" style="margin-top: 16px">
              <a-form-item label="发送提醒">
                <a-switch v-model:checked="formState.enable_reminder" />
              </a-form-item>

              <a-form-item v-if="formState.enable_reminder" label="提醒时间">
                <a-checkbox-group v-model:value="formState.reminder_times">
                  <a-checkbox value="1d">开播前1天</a-checkbox>
                  <a-checkbox value="1h">开播前1小时</a-checkbox>
                  <a-checkbox value="15m">开播前15分钟</a-checkbox>
                </a-checkbox-group>
              </a-form-item>
            </a-card>
          </a-col>
        </a-row>

        <!-- 底部操作按钮 -->
        <div class="form-actions">
          <a-space>
            <a-button @click="handleCancel">取消</a-button>
            <a-button @click="handleSaveDraft" :loading="saving">保存草稿</a-button>
            <a-button type="primary" @click="handlePublish" :loading="saving">
              {{ isEdit ? '保存修改' : '立即发布' }}
            </a-button>
          </a-space>
        </div>
      </a-form>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import dayjs, { Dayjs } from 'dayjs'

const route = useRoute()
const router = useRouter()

// 是否编辑模式
const isEdit = computed(() => !!route.params.id)
const liveId = computed(() => route.params.id as string)

// 状态
const loading = ref(false)
const saving = ref(false)
const formRef = ref()
const coverFileList = ref<any[]>([])

// 讲师列表
const instructors = ref([
  { id: 'C001', name: '张三', level: 'L2' },
  { id: 'C003', name: '王五', level: 'L3' },
  { id: 'C005', name: '孙七', level: 'L4' }
])

// 常量
const levelColors: Record<string, string> = {
  L0: 'blue',
  L1: 'green',
  L2: 'orange',
  L3: 'red',
  L4: 'purple',
  L5: 'gold'
}

// 表单数据
const formState = reactive({
  title: '',
  description: '',
  instructor_id: undefined as string | undefined,
  audience: 'both' as string,
  level: 'L0',
  date: null as Dayjs | null,
  time: null as Dayjs | null,
  duration_minutes: 60,
  cover_url: '',
  enable_recording: true,
  enable_replay: true,
  interaction_options: ['chat', 'question'] as string[],
  enable_reminder: true,
  reminder_times: ['1h', '15m'] as string[]
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入直播标题' },
    { min: 5, message: '标题至少5个字符' }
  ],
  instructor_id: [{ required: true, message: '请选择讲师' }],
  level: [{ required: true, message: '请选择认证等级' }],
  date: [{ required: true, message: '请选择直播日期' }],
  time: [{ required: true, message: '请选择开始时间' }],
  duration_minutes: [{ required: true, message: '请设置直播时长' }]
}

// 禁用过去的日期
const disabledDate = (current: Dayjs) => {
  return current && current < dayjs().startOf('day')
}

// 讲师搜索过滤
const filterInstructor = (input: string, option: any) => {
  const ins = instructors.value.find(i => i.id === option.value)
  return ins?.name.toLowerCase().includes(input.toLowerCase())
}

// 封面上传
const handleCoverUpload = (file: File) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    formState.cover_url = e.target?.result as string
    coverFileList.value = [{
      uid: '-1',
      name: file.name,
      status: 'done',
      url: formState.cover_url
    }]
  }
  reader.readAsDataURL(file)
  return false
}

// 取消
const handleCancel = () => {
  router.push('/live/list')
}

// 保存草稿
const handleSaveDraft = async () => {
  saving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    message.success('草稿已保存')
  } finally {
    saving.value = false
  }
}

// 发布
const handlePublish = async () => {
  try {
    await formRef.value?.validate()

    saving.value = true
    await new Promise(resolve => setTimeout(resolve, 1000))

    message.success(isEdit.value ? '直播已更新' : '直播已创建')
    router.push('/live/list')
  } catch (error) {
    console.error('Validation failed:', error)
  } finally {
    saving.value = false
  }
}

// 加载直播数据
const loadLiveData = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))

    // 模拟数据
    formState.title = '动机访谈技术实战演练'
    formState.description = '通过案例演示和互动练习，掌握动机访谈的核心技术。'
    formState.instructor_id = 'C003'
    formState.level = 'L1'
    formState.date = dayjs('2026-01-25')
    formState.time = dayjs('2026-01-25 19:00')
    formState.duration_minutes = 120
    formState.enable_recording = true
    formState.enable_replay = true
    formState.interaction_options = ['chat', 'question']
    formState.enable_reminder = true
    formState.reminder_times = ['1h', '15m']
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLiveData()
})
</script>

<style scoped>
.live-edit {
  padding: 0;
}

.cover-uploader :deep(.ant-upload-list-item-container) {
  width: 100% !important;
  height: 150px !important;
}

.cover-uploader :deep(.ant-upload.ant-upload-select) {
  width: 100% !important;
  height: 150px !important;
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
