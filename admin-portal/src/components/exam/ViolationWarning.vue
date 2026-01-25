<template>
  <a-modal
    :open="visible"
    :closable="false"
    :maskClosable="false"
    :keyboard="false"
    centered
    width="450px"
  >
    <template #title>
      <div class="warning-title">
        <WarningOutlined class="warning-icon" />
        <span>考试警告</span>
      </div>
    </template>

    <div class="warning-content">
      <p class="warning-message">{{ message }}</p>

      <div class="violation-info">
        <div class="info-item">
          <span class="label">当前违规次数:</span>
          <span class="value danger">{{ violationCount }}</span>
        </div>
        <div class="info-item">
          <span class="label">剩余机会:</span>
          <span class="value" :class="{ danger: remainingChances <= 2 }">
            {{ remainingChances }}
          </span>
        </div>
        <div class="info-item">
          <span class="label">诚信分:</span>
          <a-progress
            :percent="integrityScore"
            :size="80"
            type="circle"
            :status="integrityScore >= 80 ? 'success' : integrityScore >= 60 ? 'normal' : 'exception'"
          />
        </div>
      </div>

      <a-alert
        type="warning"
        show-icon
        style="margin-top: 16px"
      >
        <template #message>
          请注意以下行为将被记录为违规:
        </template>
        <template #description>
          <ul class="warning-list">
            <li>切换浏览器标签页或窗口</li>
            <li>退出全屏模式</li>
            <li>使用其他应用程序</li>
            <li>摄像头未检测到人脸</li>
          </ul>
        </template>
      </a-alert>
    </div>

    <template #footer>
      <div class="warning-footer">
        <span class="countdown" v-if="autoCloseSeconds > 0">
          {{ autoCloseSeconds }} 秒后自动关闭
        </span>
        <a-button type="primary" @click="handleAcknowledge">
          我已了解，继续考试
        </a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue';
import { WarningOutlined } from '@ant-design/icons-vue';

const props = defineProps<{
  visible: boolean;
  message: string;
  violationCount: number;
  maxViolations: number;
  integrityScore: number;
}>();

const emit = defineEmits<{
  (e: 'acknowledge'): void;
}>();

// 剩余机会
const remainingChances = ref(0);
watch(
  () => [props.violationCount, props.maxViolations],
  ([count, max]) => {
    remainingChances.value = Math.max(0, max - count);
  },
  { immediate: true }
);

// 自动关闭倒计时
const autoCloseSeconds = ref(0);
let countdownTimer: number | null = null;

const startCountdown = () => {
  autoCloseSeconds.value = 10;
  countdownTimer = window.setInterval(() => {
    autoCloseSeconds.value--;
    if (autoCloseSeconds.value <= 0) {
      clearInterval(countdownTimer!);
      handleAcknowledge();
    }
  }, 1000);
};

const stopCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
  autoCloseSeconds.value = 0;
};

// 监听弹窗显示
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      startCountdown();
    } else {
      stopCountdown();
    }
  }
);

// 确认按钮
const handleAcknowledge = () => {
  stopCountdown();
  emit('acknowledge');
};

// 清理
onUnmounted(() => {
  stopCountdown();
});
</script>

<style scoped>
.warning-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fa8c16;
}

.warning-icon {
  font-size: 20px;
}

.warning-content {
  padding: 8px 0;
}

.warning-message {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
  line-height: 1.6;
}

.violation-info {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.info-item {
  text-align: center;
}

.info-item .label {
  display: block;
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.info-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.info-item .value.danger {
  color: #ff4d4f;
}

.warning-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.warning-list li {
  margin-bottom: 4px;
}

.warning-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.countdown {
  color: #999;
  font-size: 14px;
}
</style>
