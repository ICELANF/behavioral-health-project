<template>
  <PageShell
    :title="chatStore.isAnonymous ? 'AI 健康向导' : (currentExpertInfo?.name || '行健教练')"
    :show-back="true"
    :show-tab-bar="true"
    no-padding
  >
    <template #header-right v-if="!chatStore.isAnonymous">
      <van-popover
        v-model:show="showExpertPicker"
        :actions="expertActions"
        @select="onExpertSelect"
        placement="bottom-end"
      >
        <template #reference>
          <van-icon name="exchange" size="20" />
        </template>
      </van-popover>
    </template>

    <div class="chat-page">

    <!-- 体验模式提示条 -->
    <div v-if="chatStore.isAnonymous && !chatStore.trialExhausted" class="trial-banner">
      <van-icon name="info-o" size="14" />
      <span>体验对话 {{ chatStore.trialCount }}/{{ 3 }} — 注册解锁无限对话</span>
    </div>

    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div v-if="messages.length === 0" class="empty-state">
        <van-icon name="chat-o" size="64" color="#ddd" />
        <p>{{ chatStore.isAnonymous ? '你好！我是 AI 健康向导，有什么想聊的？' : ('开始与' + (currentExpertInfo?.name || '教练') + '对话吧') }}</p>
      </div>

      <template v-for="message in messages" :key="message.id">
        <MessageBubble
          :content="message.content"
          :is-user="message.role === 'user'"
          :expert="message.expert"
          :timestamp="message.timestamp"
          :image-url="message.imageUrl || ''"
          :citations="message.citations || []"
          :has-knowledge="message.hasKnowledge || false"
          :has-model-supplement="message.hasModelSupplement || false"
          :model-supplement-sections="message.modelSupplementSections || []"
          :source-stats="message.sourceStats || {}"
        />

        <!-- 任务卡片 -->
        <div v-if="message.tasks && message.tasks.length > 0" class="inline-tasks">
          <div class="tasks-label">推荐任务</div>
          <TaskCard
            v-for="task in message.tasks"
            :key="task.id"
            :task="task"
            @toggle="chatStore.toggleTaskComplete"
          />
        </div>
      </template>

      <!-- 加载中 -->
      <div v-if="isLoading && !isThinking" class="loading-indicator">
        <van-loading type="spinner" size="24" />
        <span>思考中...</span>
      </div>

      <!-- AI 食物识别中动画 -->
      <div v-if="isThinking" class="bhp-chat-bubble bhp-chat-bubble--assistant bhp-animate-in">
        <div class="bhp-typing-dots">
          <span></span><span></span><span></span>
        </div>
        <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
          食物识别中...
        </div>
      </div>
    </div>

    <!-- 体验用完：注册引导浮层 -->
    <div v-if="chatStore.trialExhausted" class="trial-exhausted-overlay">
      <div class="trial-exhausted-card">
        <van-icon name="smile-o" size="48" color="#1565C0" />
        <h3>体验已结束</h3>
        <p>注册成为成长者，解锁无限 AI 对话和个性化健康方案</p>
        <van-button type="primary" block round @click="goRegister">立即注册</van-button>
        <p class="trial-login-link" @click="goLogin">已有账号？去登录</p>
      </div>
    </div>

    <!-- 效能感滑块 (仅登录用户) -->
    <EfficacySlider v-if="!chatStore.isAnonymous" v-model="userStore.efficacyScore" />

    <!-- 图片预览条 -->
    <div v-if="pendingImage" class="image-preview-bar">
      <van-image :src="pendingImageUrl" width="60" height="60" fit="cover" radius="6" />
      <span class="preview-name">{{ pendingImage.name }}</span>
      <van-icon name="cross" size="18" class="preview-close" @click="clearPendingImage" />
    </div>

    <!-- 输入区域 -->
    <div class="input-area safe-area-bottom" v-if="!chatStore.trialExhausted">
      <van-button
        v-if="!chatStore.isAnonymous"
        icon="photo-o"
        size="small"
        round
        plain
        @click="triggerImagePicker"
      />
      <input
        ref="imageInput"
        type="file"
        accept="image/*"
        capture="environment"
        class="hidden-file-input"
        @change="onImageSelected"
      />
      <van-field
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ maxHeight: 100 }"
        :placeholder="chatStore.isAnonymous ? '试着问我一个健康问题...' : '输入您的问题...'"
        @keypress.enter.prevent="sendMessage"
      />
      <van-button
        type="primary"
        size="small"
        round
        :disabled="(!inputText.trim() && !pendingImage) || isLoading"
        @click="sendMessage"
      >
        发送
      </van-button>
    </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import TaskCard from '@/components/chat/TaskCard.vue'
import EfficacySlider from '@/components/chat/EfficacySlider.vue'
import PageShell from '@/components/common/PageShell.vue'
import api from '@/api/index'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const chatStore = useChatStore()

const inputText = ref('')
const showExpertPicker = ref(false)
const messageListRef = ref<HTMLElement>()
const imageInput = ref<HTMLInputElement | null>(null)
const pendingImage = ref<File | null>(null)
const pendingImageUrl = ref('')
const isThinking = ref(false)

const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.isLoading)
const currentExpertInfo = computed(() => chatStore.currentExpertInfo)

const expertActions = computed(() =>
  chatStore.experts.map(e => ({
    text: e.name,
    value: e.id
  }))
)

function onExpertSelect(action: { text: string; value: string }) {
  chatStore.setCurrentExpert(action.value)
  showExpertPicker.value = false
}

function goRegister() {
  router.push('/register?from=chat&upgrade=grower')
}

function goLogin() {
  router.push('/login?redirect=/chat')
}

function triggerImagePicker() {
  imageInput.value?.click()
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.readAsDataURL(file)
  })
}

function onImageSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  pendingImage.value = file
  pendingImageUrl.value = URL.createObjectURL(file)
  // Reset input so same file can be re-selected
  input.value = ''
}

function clearPendingImage() {
  if (pendingImageUrl.value) {
    URL.revokeObjectURL(pendingImageUrl.value)
  }
  pendingImage.value = null
  pendingImageUrl.value = ''
}

async function sendMessage() {
  const text = inputText.value.trim()
  const hasImage = !!pendingImage.value

  if (!text && !hasImage) return
  if (isLoading.value) return

  if (hasImage) {
    await sendImageMessage(text)
  } else {
    inputText.value = ''
    // 匿名体验 vs 已登录
    if (chatStore.isAnonymous) {
      await chatStore.sendTrialMessage(text)
    } else {
      await chatStore.sendMessage(text)
    }
  }
  scrollToBottom()
}

async function sendImageMessage(text: string) {
  const file = pendingImage.value!

  // Convert to data URL for persistent display (blob URLs break on reload)
  const dataUrl = await fileToDataUrl(file)

  // Add user message with image
  chatStore.messages.push({
    id: 'msg_' + Date.now(),
    role: 'user',
    content: text || '识别这张图片',
    imageUrl: dataUrl,
    timestamp: Date.now(),
  })
  inputText.value = ''
  clearPendingImage()

  isThinking.value = true
  chatStore.isLoading = true
  await nextTick()
  scrollToBottom()

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('meal_type', 'lunch')

    // Do NOT set Content-Type manually — axios auto-sets multipart boundary
    const res: any = await api.post('/api/v1/food/recognize', formData, {
      timeout: 120000,
    })

    // Build response text from food recognition result
    const lines: string[] = []
    if (res.food_name) lines.push(`识别结果: ${res.food_name}`)
    if (res.calories != null) lines.push(`热量: ${Number(res.calories).toFixed(1)} kcal`)
    if (res.protein != null) lines.push(`蛋白质: ${Number(res.protein).toFixed(1)} g`)
    if (res.fat != null) lines.push(`脂肪: ${Number(res.fat).toFixed(1)} g`)
    if (res.carbs != null) lines.push(`碳水: ${Number(res.carbs).toFixed(1)} g`)
    if (res.fiber != null) lines.push(`膳食纤维: ${Number(res.fiber).toFixed(1)} g`)
    if (res.advice) lines.push(`\n营养建议: ${res.advice}`)
    if (res.foods?.length) {
      lines.push('\n食物明细:')
      res.foods.forEach((f: any) => lines.push(`  - ${f.name} ${f.portion || ''} ${f.calories || ''} kcal`))
    }

    const resultText = lines.length > 0 ? lines.join('\n') : '已收到图片，但暂时无法识别内容。'

    chatStore.messages.push({
      id: 'msg_' + Date.now(),
      role: 'assistant',
      content: resultText,
      imageUrl: res.image_url || '',
      expert: currentExpertInfo.value?.name,
      timestamp: Date.now(),
    })
  } catch (err: any) {
    // 401 → interceptor already redirects to login, don't show error in chat
    if (err?.response?.status === 401) return
    const detail = err?.response?.data?.detail || '图片分析失败，请重试'
    chatStore.messages.push({
      id: 'msg_' + Date.now(),
      role: 'assistant',
      content: detail,
      timestamp: Date.now(),
    })
    showToast({ message: detail, type: 'fail' })
  } finally {
    isThinking.value = false
    chatStore.isLoading = false
  }
}

onMounted(() => {
  const action = route.query.action as string
  if (action === 'camera') {
    nextTick(() => triggerImagePicker())
  }
})

onUnmounted(() => {
  if (pendingImageUrl.value) {
    URL.revokeObjectURL(pendingImageUrl.value)
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Clean up stale blob: imageUrls from persisted messages on load
;(() => {
  chatStore.messages.forEach(msg => {
    if (msg.imageUrl && msg.imageUrl.startsWith('blob:')) {
      msg.imageUrl = ''
    }
  })
})()
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.chat-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.trial-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(90deg, #E3F0FF, #F0F7FF);
  color: #1565C0;
  font-size: 13px;
  font-weight: 500;
  border-bottom: 1px solid #BBDEFB;
}

.trial-exhausted-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.trial-exhausted-card {
  background: #fff;
  border-radius: 20px;
  padding: 32px 24px;
  text-align: center;
  max-width: 320px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

  h3 {
    font-size: 18px;
    color: #333;
    margin: 16px 0 8px;
  }

  p {
    font-size: 14px;
    color: #666;
    margin: 0 0 20px;
    line-height: 1.6;
  }

  .trial-login-link {
    margin-top: 12px;
    font-size: 13px;
    color: #1989fa;
    cursor: pointer;

    &:active {
      opacity: 0.7;
    }
  }
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-md;
  background-color: $background-color;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: $text-color-placeholder;

  p {
    margin-top: $spacing-md;
  }
}

.inline-tasks {
  margin: $spacing-sm 0 $spacing-md 0;
  padding: $spacing-sm;
  background-color: rgba($primary-color, 0.05);
  border-radius: $border-radius;

  .tasks-label {
    font-size: $font-size-sm;
    color: $text-color-secondary;
    margin-bottom: $spacing-xs;
  }
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  color: $text-color-secondary;
  font-size: $font-size-sm;
  padding: $spacing-sm;
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: $spacing-xs;
  padding: $spacing-sm $spacing-md;
  background-color: $background-color-light;
  border-top: 1px solid $border-color;

  .van-field {
    flex: 1;
    background-color: $background-color;
    border-radius: 20px;
    padding: 4px 12px;

    :deep(.van-field__control) {
      min-height: 32px;
    }
  }
}

.hidden-file-input {
  display: none;
}

.image-preview-bar {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-xs $spacing-md;
  background-color: $background-color;
  border-top: 1px solid $border-color;

  .preview-name {
    flex: 1;
    font-size: $font-size-sm;
    color: $text-color-secondary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .preview-close {
    color: $text-color-secondary;
    cursor: pointer;
    flex-shrink: 0;
  }
}
</style>
