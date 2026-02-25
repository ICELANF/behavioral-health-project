import { ref, onUnmounted } from 'vue';

/**
 * 抓拍快照
 */
export interface Snapshot {
  id: string;
  dataUrl: string;
  timestamp: string;
  trigger: 'interval' | 'violation' | 'manual';
  violationId?: string;
  uploaded: boolean;
  uploadUrl?: string;
}

/**
 * 抓拍配置
 */
export interface SnapshotConfig {
  enabled: boolean;
  intervalSeconds: number;       // 基础间隔（秒）
  randomVarianceSeconds: number; // 随机偏移（秒）
  captureOnViolation: boolean;   // 违规时抓拍
  maxSnapshots: number;          // 最大快照数
  quality: number;               // JPEG质量 (0-1)
}

const defaultConfig: SnapshotConfig = {
  enabled: true,
  intervalSeconds: 60,
  randomVarianceSeconds: 15,
  captureOnViolation: true,
  maxSnapshots: 50,
  quality: 0.7,
};

/**
 * 考中抓拍 Hook
 * 使用 WebRTC 获取摄像头并定时抓拍
 */
export function useProctorCamera(config: Partial<SnapshotConfig> = {}) {
  const mergedConfig = { ...defaultConfig, ...config };

  const isActive = ref(false);
  const hasPermission = ref(false);
  const errorMessage = ref('');
  const snapshots = ref<Snapshot[]>([]);
  const snapshotCount = ref(0);

  let videoElement: HTMLVideoElement | null = null;
  let canvasElement: HTMLCanvasElement | null = null;
  let stream: MediaStream | null = null;
  let intervalTimer: number | null = null;

  /**
   * 生成快照ID
   */
  const generateSnapshotId = () => {
    return `snap_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  /**
   * 计算下次抓拍间隔（带随机偏移）
   */
  const getNextInterval = (): number => {
    const base = mergedConfig.intervalSeconds * 1000;
    const variance = mergedConfig.randomVarianceSeconds * 1000;
    const random = Math.random() * variance * 2 - variance; // -variance ~ +variance
    return Math.max(base + random, 10000); // 至少10秒
  };

  /**
   * 请求摄像头权限
   */
  const requestPermission = async (): Promise<boolean> => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      });

      hasPermission.value = true;
      errorMessage.value = '';
      return true;
    } catch (error: any) {
      hasPermission.value = false;

      if (error.name === 'NotAllowedError') {
        errorMessage.value = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头';
      } else if (error.name === 'NotFoundError') {
        errorMessage.value = '未检测到摄像头设备';
      } else {
        errorMessage.value = `摄像头初始化失败: ${error.message}`;
      }

      console.error('[ProctorCamera] Permission error:', error);
      return false;
    }
  };

  /**
   * 初始化视频元素
   */
  const initVideoElement = (video: HTMLVideoElement) => {
    videoElement = video;

    if (stream) {
      videoElement.srcObject = stream;
      videoElement.play().catch(console.error);
    }

    // 创建canvas用于截图
    canvasElement = document.createElement('canvas');
  };

  /**
   * 抓拍一张图片
   */
  const capture = (trigger: Snapshot['trigger'] = 'manual', violationId?: string): Snapshot | null => {
    if (!videoElement || !canvasElement || !stream) {
      console.warn('[ProctorCamera] Not ready for capture');
      return null;
    }

    if (snapshots.value.length >= mergedConfig.maxSnapshots) {
      console.warn('[ProctorCamera] Max snapshots reached');
      return null;
    }

    try {
      // 设置canvas尺寸
      canvasElement.width = videoElement.videoWidth || 640;
      canvasElement.height = videoElement.videoHeight || 480;

      // 绘制当前帧
      const ctx = canvasElement.getContext('2d');
      if (!ctx) return null;

      ctx.drawImage(videoElement, 0, 0);

      // 转换为dataURL
      const dataUrl = canvasElement.toDataURL('image/jpeg', mergedConfig.quality);

      const snapshot: Snapshot = {
        id: generateSnapshotId(),
        dataUrl,
        timestamp: new Date().toISOString(),
        trigger,
        violationId,
        uploaded: false,
      };

      snapshots.value.push(snapshot);
      snapshotCount.value++;


      return snapshot;
    } catch (error) {
      console.error('[ProctorCamera] Capture error:', error);
      return null;
    }
  };

  /**
   * 违规时抓拍
   */
  const captureOnViolation = (violationId: string): Snapshot | null => {
    if (!mergedConfig.captureOnViolation) return null;
    return capture('violation', violationId);
  };

  /**
   * 定时抓拍
   */
  const scheduleNextCapture = () => {
    if (!isActive.value || !mergedConfig.enabled) return;

    const delay = getNextInterval();

    intervalTimer = window.setTimeout(() => {
      capture('interval');
      scheduleNextCapture();
    }, delay);
  };

  /**
   * 开始抓拍
   */
  const start = async (): Promise<boolean> => {
    if (isActive.value) return true;

    // 请求权限
    if (!hasPermission.value) {
      const granted = await requestPermission();
      if (!granted) return false;
    }

    isActive.value = true;

    // 开始定时抓拍
    if (mergedConfig.enabled) {
      scheduleNextCapture();
    }

    return true;
  };

  /**
   * 停止抓拍
   */
  const stop = () => {
    isActive.value = false;

    // 清除定时器
    if (intervalTimer) {
      clearTimeout(intervalTimer);
      intervalTimer = null;
    }

    // 停止视频流
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }

    if (videoElement) {
      videoElement.srcObject = null;
    }

  };

  /**
   * 获取未上传的快照
   */
  const getUnuploadedSnapshots = (): Snapshot[] => {
    return snapshots.value.filter((s) => !s.uploaded);
  };

  /**
   * 标记快照为已上传
   */
  const markAsUploaded = (snapshotId: string, uploadUrl: string) => {
    const snapshot = snapshots.value.find((s) => s.id === snapshotId);
    if (snapshot) {
      snapshot.uploaded = true;
      snapshot.uploadUrl = uploadUrl;
    }
  };

  /**
   * 清空快照
   */
  const clearSnapshots = () => {
    // 释放dataUrl内存
    snapshots.value.forEach((s) => {
      // dataUrl会自动垃圾回收
    });
    snapshots.value = [];
    snapshotCount.value = 0;
  };

  /**
   * 获取视频流
   */
  const getStream = (): MediaStream | null => stream;

  // 组件卸载时清理
  onUnmounted(() => {
    stop();
    clearSnapshots();
  });

  return {
    isActive,
    hasPermission,
    errorMessage,
    snapshots,
    snapshotCount,
    requestPermission,
    initVideoElement,
    capture,
    captureOnViolation,
    start,
    stop,
    getUnuploadedSnapshots,
    markAsUploaded,
    clearSnapshots,
    getStream,
  };
}
