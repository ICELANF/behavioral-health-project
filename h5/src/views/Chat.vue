<template>
  <div class="page-container chat-page">
    <!-- 顶部导航 -->
    <van-nav-bar
      :title="currentExpertInfo?.name || '行健教练'"
      left-arrow
      @click-left="$router.back()"
    >
      <template #right>
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
    </van-nav-bar>

    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div v-if="messages.length === 0" class="empty-state">
        <van-icon name="chat-o" size="64" color="#ddd" />
        <p>开始与{{ currentExpertInfo?.name }}对话吧</p>
      </div>

      <template v-for="message in messages" :key="message.id">
        <MessageBubble
          :content="message.content"
          :is-user="message.role === 'user'"
          :expert="message.expert"
          :timestamp="message.timestamp"
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
      <div v-if="isLoading" class="loading-indicator">
        <van-loading type="spinner" size="24" />
        <span>思考中...</span>
      </div>
    </div>

    <!-- 效能感滑块 -->
    <EfficacySlider v-model="userStore.efficacyScore" />

    <!-- 输入区域 -->
    <div class="input-area safe-area-bottom">
      <van-button
        icon="photo-o"
        size="small"
        round
        plain
        @click="showWearablePopup = true"
      />
      <van-field
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ maxHeight: 100 }"
        placeholder="输入您的问题..."
        @keypress.enter.prevent="sendMessage"
      />
      <van-button
        type="primary"
        size="small"
        round
        :disabled="!inputText.trim() || isLoading"
        @click="sendMessage"
      >
        发送
      </van-button>
    </div>

    <!-- 穿戴数据弹窗 -->
    <van-popup
      v-model:show="showWearablePopup"
      position="bottom"
      round
      :style="{ maxHeight: '60%' }"
    >
      <div class="wearable-popup">
        <h3>穿戴设备数据</h3>
        <van-cell-group inset>
          <van-field
            v-model.number="wearableForm.hr"
            label="心率"
            type="digit"
            placeholder="请输入"
          >
            <template #button>bpm</template>
          </van-field>
          <van-field
            v-model.number="wearableForm.steps"
            label="步数"
            type="digit"
            placeholder="请输入"
          >
            <template #button>步</template>
          </van-field>
          <van-field
            v-model.number="wearableForm.sleep_hours"
            label="睡眠"
            type="number"
            placeholder="请输入"
          >
            <template #button>小时</template>
          </van-field>
          <van-field
            v-model.number="wearableForm.hrv"
            label="HRV"
            type="digit"
            placeholder="请输入"
          >
            <template #button>ms</template>
          </van-field>
        </van-cell-group>
        <van-button
          type="primary"
          block
          round
          @click="saveWearableData"
        >
          确认
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import TaskCard from '@/components/chat/TaskCard.vue'
import EfficacySlider from '@/components/chat/EfficacySlider.vue'
import type { WearableData } from '@/api/types'

const userStore = useUserStore()
const chatStore = useChatStore()

const inputText = ref('')
const showExpertPicker = ref(false)
const showWearablePopup = ref(false)
const messageListRef = ref<HTMLElement>()

const wearableForm = ref<WearableData>({
  hr: undefined,
  steps: undefined,
  sleep_hours: undefined,
  hrv: undefined
})

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

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  inputText.value = ''
  await chatStore.sendMessage(text)
  scrollToBottom()
}

function saveWearableData() {
  userStore.updateWearableData(wearableForm.value)
  showWearablePopup.value = false
}

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
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
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

.wearable-popup {
  padding: $spacing-md;

  h3 {
    text-align: center;
    margin-bottom: $spacing-md;
  }

  .van-button {
    margin-top: $spacing-md;
  }
}
</style>
