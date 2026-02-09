<!--
  知识投稿页面 — 用户提交知识内容 + 我的投稿列表
  路由: /contribute
-->
<template>
  <div class="page-container">
    <van-nav-bar
      title="知识投稿"
      left-arrow
      @click-left="router.back()"
    />

    <div class="page-content contribute-page">
      <!-- 投稿表单 -->
      <div class="submit-card card">
        <h3 class="form-title">提交投稿</h3>
        <van-form @submit="onSubmit" ref="formRef">
          <van-cell-group inset>
            <van-field
              v-model="form.title"
              label="标题"
              placeholder="请输入文章标题"
              :rules="[{ required: true, message: '请输入标题' }]"
              maxlength="100"
              show-word-limit
            />

            <van-field
              v-model="form.domain"
              is-link
              readonly
              label="领域"
              placeholder="请选择领域"
              :rules="[{ required: true, message: '请选择领域' }]"
              @click="showDomainPicker = true"
            />

            <van-field
              v-model="form.body"
              label="正文"
              type="textarea"
              placeholder="请输入内容正文..."
              :rules="[{ required: true, message: '请输入正文内容' }]"
              rows="6"
              autosize
              maxlength="5000"
              show-word-limit
            />
          </van-cell-group>

          <div class="submit-btn-area">
            <van-button
              type="primary"
              block
              round
              native-type="submit"
              :loading="submitting"
              loading-text="提交中..."
            >
              提交投稿
            </van-button>
          </div>
        </van-form>
      </div>

      <!-- 领域选择器 -->
      <van-popup v-model:show="showDomainPicker" position="bottom" round>
        <van-picker
          :columns="domainOptions"
          @confirm="onDomainConfirm"
          @cancel="showDomainPicker = false"
          title="选择领域"
        />
      </van-popup>

      <!-- 我的投稿列表 -->
      <div class="my-contributions card">
        <h3 class="section-title">我的投稿</h3>

        <van-loading v-if="loadingList" size="20" />

        <van-empty v-else-if="contributions.length === 0" description="暂无投稿记录" image="search" />

        <div v-else class="contribution-list">
          <div
            v-for="item in contributions"
            :key="item.id"
            class="contribution-item"
          >
            <div class="contribution-header">
              <span class="contribution-title">{{ item.title }}</span>
              <van-tag
                :type="statusTagType(item.review_status)"
                size="small"
                round
              >
                {{ statusLabel(item.review_status) }}
              </van-tag>
            </div>
            <div class="contribution-meta">
              <van-tag plain size="small" color="#969799">{{ item.domain }}</van-tag>
              <span class="contribution-time">{{ formatDate(item.created_at) }}</span>
            </div>
            <div class="contribution-preview">
              {{ truncate(item.body, 80) }}
            </div>
            <div v-if="item.reviewer_comment" class="reviewer-comment">
              <van-icon name="chat-o" size="12" color="#1989fa" />
              <span>审核意见: {{ item.reviewer_comment }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api/index'

const router = useRouter()

// 表单
const formRef = ref()
const submitting = ref(false)
const showDomainPicker = ref(false)

const form = reactive({
  title: '',
  body: '',
  domain: ''
})

const domainOptions = [
  { text: '代谢健康', value: 'metabolic' },
  { text: '睡眠管理', value: 'sleep' },
  { text: '情绪调节', value: 'emotion' },
  { text: '运动康复', value: 'exercise' },
  { text: '营养膳食', value: 'nutrition' },
  { text: '中医养生', value: 'tcm' },
  { text: '行为改变', value: 'behavior' },
  { text: '心理动机', value: 'motivation' },
  { text: '心脏康复', value: 'cardiac' },
  { text: '综合健康', value: 'general' }
]

let selectedDomainValue = ''

function onDomainConfirm({ selectedOptions }: any) {
  const option = selectedOptions?.[0]
  if (option) {
    form.domain = option.text
    selectedDomainValue = option.value
  }
  showDomainPicker.value = false
}

// 提交投稿
async function onSubmit() {
  submitting.value = true
  try {
    await api.post('/api/v1/contributions/submit', {
      title: form.title,
      body: form.body,
      domain: selectedDomainValue || form.domain
    })
    showToast({ message: '投稿成功', type: 'success' })
    // 重置表单
    form.title = ''
    form.body = ''
    form.domain = ''
    selectedDomainValue = ''
    // 刷新列表
    loadMyContributions()
  } catch (err) {
    console.error('投稿失败:', err)
    showToast('投稿失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 我的投稿
const loadingList = ref(true)
const contributions = ref<any[]>([])

async function loadMyContributions() {
  loadingList.value = true
  try {
    const res: any = await api.get('/api/v1/contributions/my')
    contributions.value = res.contributions || res || []
  } catch (err) {
    console.error('加载投稿列表失败:', err)
  } finally {
    loadingList.value = false
  }
}

// 审核状态
function statusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '未通过',
    published: '已发布'
  }
  return map[status] || status || '待审核'
}

function statusTagType(status: string): 'primary' | 'success' | 'warning' | 'danger' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'danger'> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    published: 'primary'
  }
  return map[status] || 'warning'
}

function formatDate(time: string): string {
  if (!time) return ''
  const d = new Date(time)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function truncate(text: string, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

onMounted(() => {
  loadMyContributions()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.submit-card {
  .form-title {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }

  :deep(.van-cell-group--inset) {
    margin: 0;
  }

  :deep(.van-field__label) {
    width: 3.2em;
  }
}

.submit-btn-area {
  padding: $spacing-md 0 0;
}

.my-contributions {
  .section-title {
    font-size: $font-size-lg;
    margin-bottom: $spacing-sm;
  }
}

.contribution-list {
  .contribution-item {
    padding: 12px 0;
    border-bottom: 1px solid $border-color;

    &:last-child {
      border-bottom: none;
    }
  }

  .contribution-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 6px;
  }

  .contribution-title {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-color;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .contribution-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .contribution-time {
    font-size: $font-size-xs;
    color: $text-color-placeholder;
  }

  .contribution-preview {
    font-size: $font-size-sm;
    color: #646566;
    line-height: 1.5;
    margin-bottom: 4px;
  }

  .reviewer-comment {
    display: flex;
    align-items: flex-start;
    gap: 4px;
    font-size: $font-size-xs;
    color: $primary-color;
    background: rgba($primary-color, 0.06);
    padding: 8px;
    border-radius: 6px;
    margin-top: 6px;
    line-height: 1.4;
  }
}
</style>
