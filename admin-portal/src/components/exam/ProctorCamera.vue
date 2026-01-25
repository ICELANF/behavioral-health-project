<template>
  <div class="proctor-camera" :class="{ minimized: isMinimized }">
    <!-- 摄像头预览 -->
    <div class="camera-preview" @click="toggleMinimize">
      <video
        ref="videoRef"
        autoplay
        playsinline
        muted
        class="camera-video"
      />

      <!-- 状态指示器 -->
      <div class="camera-status">
        <span class="status-dot" :class="statusClass"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>

      <!-- 最小化/展开按钮 -->
      <div class="camera-toggle">
        <ShrinkOutlined v-if="!isMinimized" />
        <ArrowsAltOutlined v-else />
      </div>

      <!-- 抓拍计数 -->
      <div v-if="snapshotCount > 0" class="snapshot-count">
        <CameraOutlined />
        <span>{{ snapshotCount }}</span>
      </div>
    </div>

    <!-- 权限错误提示 -->
    <div v-if="errorMessage" class="camera-error">
      <ExclamationCircleOutlined />
      <span>{{ errorMessage }}</span>
      <a-button size="small" type="link" @click="retry">重试</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import {
  ShrinkOutlined,
  ArrowsAltOutlined,
  CameraOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue';

const props = defineProps<{
  isActive: boolean;
  hasPermission: boolean;
  errorMessage: string;
  snapshotCount: number;
}>();

const emit = defineEmits<{
  (e: 'init', video: HTMLVideoElement): void;
  (e: 'retry'): void;
}>();

// 视频元素引用
const videoRef = ref<HTMLVideoElement | null>(null);

// 最小化状态
const isMinimized = ref(false);

// 状态
const statusClass = computed(() => {
  if (!props.isActive) return 'inactive';
  if (props.hasPermission) return 'active';
  return 'error';
});

const statusText = computed(() => {
  if (!props.isActive) return '未启动';
  if (props.errorMessage) return '错误';
  if (props.hasPermission) return '监控中';
  return '等待授权';
});

// 切换最小化
const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value;
};

// 重试
const retry = () => {
  emit('retry');
};

// 初始化视频元素
onMounted(() => {
  if (videoRef.value) {
    emit('init', videoRef.value);
  }
});

// 监听视频元素变化
watch(videoRef, (video) => {
  if (video) {
    emit('init', video);
  }
});
</script>

<style scoped>
.proctor-camera {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  transition: all 0.3s ease;
}

.proctor-camera.minimized .camera-preview {
  width: 60px;
  height: 60px;
  border-radius: 50%;
}

.proctor-camera.minimized .camera-video {
  border-radius: 50%;
}

.proctor-camera.minimized .camera-status,
.proctor-camera.minimized .snapshot-count {
  display: none;
}

.camera-preview {
  width: 200px;
  height: 150px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.camera-preview:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* 镜像显示 */
}

.camera-status {
  position: absolute;
  top: 8px;
  left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active {
  background: #52c41a;
  animation: pulse 2s infinite;
}

.status-dot.inactive {
  background: #999;
}

.status-dot.error {
  background: #ff4d4f;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.camera-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
}

.snapshot-count {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}

.camera-error {
  margin-top: 8px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  color: #ff4d4f;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
</style>
